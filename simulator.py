from collections import deque
from dataclasses import dataclass, field
import random
from typing import Dict, List, Tuple


PAGE_SIZE_KB = 4


@dataclass
class SimulationStep:
    index: int
    request: int
    frames: list
    fault: bool
    action: str
    internal_frag: float = 0.0
    external_frag: float = 0.0
    holes_count: int = 0


@dataclass
class MemoryMetrics:
    total_memory: int
    used_memory: int
    free_memory: int
    utilization_percent: float


@dataclass
class SimulationResult:
    algorithm: str
    pages: list
    frames: int
    faults: int
    hits: int
    fault_rate: float
    steps: list
    performance_tracker: object = None
    fragmentation: object = None


class WorkloadGenerator:
    @staticmethod
    def random_workload(num_requests: int, max_page: int) -> List[int]:
        return [random.randint(0, max_page) for _ in range(num_requests)]

    @staticmethod
    def locality_workload(num_requests: int, max_page: int, window_size: int = 5) -> List[int]:
        workload = []
        current_page = random.randint(0, max_page)
        for _ in range(num_requests):
            workload.append(current_page)
            if random.random() < 0.3:
                current_page = random.randint(0, max_page)
            else:
                current_page = (current_page + random.randint(-window_size, window_size)) % (max_page + 1)
        return workload

    @staticmethod
    def looping_workload(num_requests: int, loop_sequence: List[int]) -> List[int]:
        return [loop_sequence[i % len(loop_sequence)] for i in range(num_requests)]

    @staticmethod
    def burst_workload(num_requests: int, max_page: int, burst_size: int = 4) -> List[int]:
        workload = []
        while len(workload) < num_requests:
            base_page = random.randint(0, max_page)
            for j in range(burst_size):
                if len(workload) >= num_requests:
                    break
                workload.append((base_page + j) % (max_page + 1))
        return workload


class FragmentationAnalyzer:
    def __init__(self, total_frames: int):
        self.total_frames = total_frames
        self.page_usage: Dict[int, int] = {}
        self.holes: List[Dict[str, int]] = []

    def calculate_internal_fragmentation(self, frames_state: List[int]) -> Tuple[float, Dict[int, int]]:
        internal_frag = 0.0
        usage = {}
        for page in frames_state:
            if page not in self.page_usage:
                self.page_usage[page] = random.randint(1, PAGE_SIZE_KB)
            usage[page] = self.page_usage[page]
            internal_frag += PAGE_SIZE_KB - self.page_usage[page]
        return internal_frag, usage

    def calculate_external_fragmentation(self) -> Tuple[float, int]:
        total_fragmented = sum(hole["size"] for hole in self.holes)
        return float(total_fragmented), len(self.holes)

    def add_hole(self, position: int, size: int):
        self.holes.append({"position": position, "size": size})

    def remove_hole(self, size: int) -> bool:
        for hole in self.holes:
            if hole["size"] >= size:
                hole["size"] -= size
                if hole["size"] == 0:
                    self.holes.remove(hole)
                return True
        return False


class PerformanceTracker:
    def __init__(self):
        self.fault_over_time = []
        self.hits_over_time = []
        self.fault_rate_over_time = []

    def record_step(self, faults: int, hits: int, total: int):
        self.fault_over_time.append(faults)
        self.hits_over_time.append(hits)
        rate = (faults / total * 100) if total > 0 else 0
        self.fault_rate_over_time.append(rate)


def simulate_algorithm(pages, frames, algorithm):
    if frames <= 0:
        raise ValueError("Frames must be greater than zero")
    if not pages:
        raise ValueError("Page sequence cannot be empty")

    memory = []
    queue = deque()
    recent = {}
    faults = 0
    hits = 0
    steps = []

    frag_analyzer = FragmentationAnalyzer(frames)
    performance = PerformanceTracker()

    for index, page in enumerate(pages):
        fault = page not in memory
        action = "Hit"

        if algorithm == "FIFO":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    queue.append(page)
                    action = f"Loaded {page}"
                else:
                    removed = queue.popleft()
                    memory[memory.index(removed)] = page
                    queue.append(page)
                    action = f"Replaced {removed}"
                    frag_analyzer.add_hole(position=removed * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1

        elif algorithm == "LRU":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    action = f"Loaded {page}"
                else:
                    lru_page = min(memory, key=lambda value: recent.get(value, -1))
                    memory[memory.index(lru_page)] = page
                    action = f"Replaced {lru_page}"
                    frag_analyzer.add_hole(position=lru_page * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1
            recent[page] = index

        elif algorithm == "OPTIMAL":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    action = f"Loaded {page}"
                else:
                    future = pages[index + 1 :]
                    replace = None
                    farthest = -1
                    for candidate in memory:
                        if candidate not in future:
                            replace = candidate
                            break
                        future_index = future.index(candidate)
                        if future_index > farthest:
                            farthest = future_index
                            replace = candidate
                    memory[memory.index(replace)] = page
                    action = f"Replaced {replace}"
                    frag_analyzer.add_hole(position=replace * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1

        else:
            raise ValueError("Invalid algorithm")

        internal_frag, _ = frag_analyzer.calculate_internal_fragmentation(memory)
        external_frag, holes_count = frag_analyzer.calculate_external_fragmentation()
        performance.record_step(faults, hits, index + 1)

        steps.append(
            SimulationStep(
                index=index + 1,
                request=page,
                frames=memory.copy(),
                fault=fault,
                action=action,
                internal_frag=internal_frag,
                external_frag=external_frag,
                holes_count=holes_count,
            )
        )

    return SimulationResult(
        algorithm=algorithm,
        pages=pages,
        frames=frames,
        faults=faults,
        hits=hits,
        fault_rate=faults / len(pages) if pages else 0,
        steps=steps,
        performance_tracker=performance,
        fragmentation=frag_analyzer,
    )


def compare_algorithms(pages: List[int], frames: int) -> Dict[str, SimulationResult]:
    results = {}
    for algo in ["FIFO", "LRU", "OPTIMAL"]:
        results[algo] = simulate_algorithm(pages, frames, algo)
    return results

from collections import deque
from dataclasses import dataclass, field
import random
from typing import List, Dict, Tuple


# ============ Constants ============
PAGE_SIZE_KB = 4  # Page/Frame size in KB


# ============ Data Classes ============
@dataclass
class SimulationStep:
    index: int
    request: int
    frames: list
    fault: bool
    action: str
    internal_frag: float = 0.0  # KB
    external_frag: float = 0.0  # KB
    holes_count: int = 0


@dataclass
class FragmentationState:
    """Track memory fragmentation metrics"""
    internal_fragmentation: float = 0.0  # KB
    external_fragmentation: float = 0.0  # KB
    holes: List[Dict] = field(default_factory=list)  # List of free holes
    page_usage: Dict = field(default_factory=dict)  # Page -> actual usage size


@dataclass
class MemoryMetrics:
    """Track memory utilization"""
    total_memory: int  # KB
    used_memory: int  # KB
    free_memory: int  # KB
    utilization_percent: float


class WorkloadGenerator:
    """Generate realistic page reference workloads"""

    @staticmethod
    def random_workload(num_requests: int, max_page: int) -> List[int]:
        """Generate random page requests"""
        return [random.randint(0, max_page) for _ in range(num_requests)]

    @staticmethod
    def locality_workload(num_requests: int, max_page: int, window_size: int = 5) -> List[int]:
        """Generate workload with locality of reference"""
        workload = []
        current_page = random.randint(0, max_page)
        for _ in range(num_requests):
            workload.append(current_page)
            if random.random() < 0.3:  # 30% chance to jump to new area
                current_page = random.randint(0, max_page)
            else:  # 70% stay in nearby area
                current_page = (current_page + random.randint(-window_size, window_size)) % (max_page + 1)
        return workload

    @staticmethod
    def looping_workload(num_requests: int, loop_sequence: List[int]) -> List[int]:
        """Generate looping pattern workload"""
        workload = []
        for i in range(num_requests):
            workload.append(loop_sequence[i % len(loop_sequence)])
        return workload

    @staticmethod
    def burst_workload(num_requests: int, max_page: int, burst_size: int = 4) -> List[int]:
        """Generate workload with burst patterns"""
        workload = []
        for _ in range(num_requests // burst_size + 1):
            base_page = random.randint(0, max_page)
            for j in range(burst_size):
                if len(workload) < num_requests:
                    workload.append((base_page + j) % (max_page + 1))
        return workload[:num_requests]


class FragmentationAnalyzer:
    """Analyze and track memory fragmentation"""

    def __init__(self, total_frames: int):
        self.total_frames = total_frames
        self.page_usage = {}  # page -> actual usage in KB
        self.holes = []  # External fragmentation holes

    def calculate_internal_fragmentation(self, frames_state: List[int]) -> Tuple[float, Dict]:
        """
        Calculate internal fragmentation for loaded pages.
        Assumes each page uses random size between 1-PAGE_SIZE_KB
        """
        internal_frag = 0.0
        usage = {}

        for page in frames_state:
            if page not in self.page_usage:
                # Simulate page size: random between 1 and PAGE_SIZE_KB
                actual_size = random.randint(1, PAGE_SIZE_KB)
                self.page_usage[page] = actual_size

            usage[page] = self.page_usage[page]
            unused = PAGE_SIZE_KB - self.page_usage[page]
            internal_frag += unused

        return internal_frag, usage

    def calculate_external_fragmentation(self) -> Tuple[float, int]:
        """Calculate external fragmentation from holes"""
        # Simplified: holes are fragments in secondary memory
        total_fragmented = sum(hole["size"] for hole in self.holes)
        return float(total_fragmented), len(self.holes)

    def add_hole(self, position: int, size: int):
        """Add a free hole (for external fragmentation tracking)"""
        self.holes.append({"position": position, "size": size})

    def remove_hole(self, size: int):
        """Remove/merge holes when memory is allocated"""
        for hole in self.holes:
            if hole["size"] >= size:
                hole["size"] -= size
                if hole["size"] == 0:
                    self.holes.remove(hole)
                return True
        return False


class PerformanceTracker:
    """Track performance metrics for graphs"""

    def __init__(self):
        self.fault_over_time = []  # Cumulative faults
        self.hits_over_time = []   # Cumulative hits
        self.fault_rate_over_time = []  # Instantaneous fault rate

    def record_step(self, faults: int, hits: int, total: int):
        """Record metrics at each step"""
        self.fault_over_time.append(faults)
        self.hits_over_time.append(hits)
        fault_rate = (faults / total * 100) if total > 0 else 0
        self.fault_rate_over_time.append(fault_rate)


def simulate_algorithm(pages, frames, algorithm):
    if frames <= 0:
        raise ValueError("Frames must be greater than zero")
    if not pages:
        raise ValueError("Page sequence cannot be empty")

    memory = []
    queue = deque()
    recent = {}
    faults = 0
    hits = 0
    steps = []

    # Initialize fragmentation analyzer
    frag_analyzer = FragmentationAnalyzer(frames)
    performance = PerformanceTracker()

    for index, page in enumerate(pages):
        fault = page not in memory
        action = "Hit"

        if algorithm == "FIFO":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    queue.append(page)
                    action = f"Loaded {page}"
                else:
                    removed = queue.popleft()
                    memory[memory.index(removed)] = page
                    queue.append(page)
                    action = f"Replaced {removed}"
                    # Simulate hole creation in secondary memory
                    frag_analyzer.add_hole(position=removed * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1

        elif algorithm == "LRU":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    action = f"Loaded {page}"
                else:
                    lru_page = min(memory, key=lambda value: recent.get(value, -1))
                    memory[memory.index(lru_page)] = page
                    action = f"Replaced {lru_page}"
                    frag_analyzer.add_hole(position=lru_page * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1
            recent[page] = index

        elif algorithm == "OPTIMAL":
            if fault:
                faults += 1
                if len(memory) < frames:
                    memory.append(page)
                    action = f"Loaded {page}"
                else:
                    future = pages[index + 1 :]
                    replace = None
                    farthest = -1
                    for candidate in memory:
                        if candidate not in future:
                            replace = candidate
                            break
                        future_index = future.index(candidate)
                        if future_index > farthest:
                            farthest = future_index
                            replace = candidate
                    memory[memory.index(replace)] = page
                    action = f"Replaced {replace}"
                    frag_analyzer.add_hole(position=replace * 100, size=PAGE_SIZE_KB)
            else:
                hits += 1
        else:
            raise ValueError("Invalid algorithm")

        # Calculate fragmentation
        internal_frag, _ = frag_analyzer.calculate_internal_fragmentation(memory)
        external_frag, holes_count = frag_analyzer.calculate_external_fragmentation()

        # Record performance
        performance.record_step(faults, hits, index + 1)

        step = SimulationStep(
            index + 1,
            page,
            memory.copy(),
            fault,
            action,
            internal_frag=internal_frag,
            external_frag=external_frag,
            holes_count=holes_count
        )
        steps.append(step)

    return SimulationResult(
        algorithm=algorithm,
        pages=pages,
        frames=frames,
        faults=faults,
        hits=hits,
        fault_rate=faults / len(pages) if pages else 0,
        steps=steps,
        performance_tracker=performance,
        fragmentation=frag_analyzer
    )


@dataclass
class SimulationResult:
    algorithm: str
    pages: list
    frames: int
    faults: int
    hits: int
    fault_rate: float
    steps: list
    performance_tracker: PerformanceTracker = field(default_factory=PerformanceTracker)
    fragmentation: FragmentationAnalyzer = None


def compare_algorithms(pages: List[int], frames: int) -> Dict[str, SimulationResult]:
    """Run all three algorithms on the same input and return results"""
    results = {}
    for algo in ["FIFO", "LRU", "OPTIMAL"]:
        results[algo] = simulate_algorithm(pages, frames, algo)
    return results


def format_frames(frames_state):
    return "[" + ", ".join(str(frame) for frame in frames_state) + "]"


def print_steps(steps):
    print("\nStep-by-step timeline:\n")
    print(f"{'Step':>4}  {'Request':>7}  {'Result':<11}  Frames")
    print("-" * 52)
    for step in steps:
        result = "Fault" if step.fault else "Hit"
        print(f"{step.index:>4}  {step.request:>7}  {result:<11}  {format_frames(step.frames)}")


def main():
    print("\nVirtual Memory Optimization Simulator\n")

    try:
        frames = int(input("Enter number of frames: ").strip())
        seq = input("Enter page reference string (space separated): ").strip()
        algo = input("Algorithm (FIFO / LRU / OPTIMAL): ").strip().upper()

        pages = [int(value) for value in seq.split()]
        result = simulate_algorithm(pages, frames, algo)
    except Exception as error:
        print(f"\nError: {error}\n")
        return

    print_steps(result.steps)

    print("\nResults\n")
    print(f"Algorithm: {result.algorithm}")
    print(f"Frames: {result.frames}")
    print(f"Total Requests: {len(result.pages)}")
    print(f"Page Faults: {result.faults}")
    print(f"Hits: {result.hits}")
    print(f"Fault Rate: {result.fault_rate:.3f}")


if __name__ == "__main__":
    main()
