# 🧠 Virtual Memory Optimization Simulator

> **Demand Paging · Page Replacement Algorithms · Fragmentation Analysis · Performance Benchmarking**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=flat-square)](https://docs.python.org/3/library/tkinter.html)
[![Matplotlib](https://img.shields.io/badge/Graphs-Matplotlib-11557C?style=flat-square&logo=matplotlib)](https://matplotlib.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![OS Course](https://img.shields.io/badge/Domain-Operating%20Systems-blueviolet?style=flat-square)]()

---

## 📌 Overview

**Virtual Memory Optimization Simulator** is a Python-based desktop application that provides an interactive, visual deep-dive into the mechanics of virtual memory management. Built as an OS coursework educational tool, it simulates **demand paging**, benchmarks **page replacement algorithms**, and performs real-time **fragmentation analysis** — all through a polished, dark-themed Tkinter GUI.

Whether you're studying OS internals, comparing algorithm behavior under different workloads, or visualizing how memory fragmentation evolves over time — this simulator brings it to life step by step.

---

## 🏗️ Architecture

```
Virtual Memory Optimization Simulator
├── simulator.py                # Core simulation engine
│   ├── SimulationStep          # Per-step state snapshot
│   ├── FragmentationState      # Internal/external frag tracking
│   ├── MemoryMetrics           # Fault/hit counters, fault rate
│   ├── WorkloadGenerator       # 5 workload pattern modes
│   ├── FragmentationAnalyzer   # Hole-list based frag model
│   ├── PerformanceTracker      # Time-series metrics
│   └── SimulationResult        # Full run output bundle
│
└── vm_simulator_gui.py         # Tkinter GUI orchestration
    └── VirtualMemorySimulatorApp
        ├── Simulation Controls
        ├── Workload Generator
        ├── Live Metrics Panel
        ├── Frame Snapshot View
        ├── Fragmentation Panel
        ├── Algorithm Comparison Table
        ├── Performance Dashboard (matplotlib)
        ├── Simulation Timeline Table
        ├── Analysis & Insights Panel
        └── Export / Reporting Panel
```

---

## ⚙️ Core Concepts Implemented

### 🔄 Demand Paging

The simulator models **demand paging** strictly:
- Pages are **loaded only on access** (no pre-fetching)
- A **page fault** is triggered when the requested page is not in any frame
- When frames are full, a **replacement algorithm** selects the victim page
- After eviction, the new page occupies the freed frame

Each step records the full frame state, fault/hit status, and which page was replaced.

### 🗂️ Page & Frame Model

| Parameter | Value |
|-----------|-------|
| Page / Frame Size | **4 KB** (fixed) |
| Simulated Used Size per Page | **1–4 KB** (randomized) |
| Internal Fragmentation per Page | `frame_size - used_size` |
| Secondary Memory Hole Tracking | Hole list updated on every replacement |

---

## 🧮 Page Replacement Algorithms

### FIFO — First-In First-Out
Evicts the **oldest loaded page**. Maintained via insertion-order queue. Simple but suffers from **Bélády's anomaly** — fault count can increase with more frames.

### LRU — Least Recently Used
Evicts the page that was **accessed furthest back in time**. Requires access-time tracking per frame. Approximates optimal behavior without future knowledge.

### OPTIMAL (Bélády's Algorithm)
Uses **future reference knowledge** to evict the page that will not be used for the longest time. Serves as a **theoretical lower bound** for fault rate — used as the performance ceiling for comparison.

---

## 📊 Fragmentation Analysis

### Internal Fragmentation
```
Internal Waste = Σ (frame_size - used_size_per_page)
               = Σ (4 KB - rand(1..4) KB)  per loaded page
```
Tracked cumulatively across all simulation steps.

### External Fragmentation
- Models a **secondary memory hole list**
- A **new hole** is created in secondary memory each time a page is evicted
- Metrics tracked:
  - `Total External Fragmented Memory (KB)`
  - `Number of Holes`
- Illustrates how repeated replacements fragment free secondary memory over time

---

## 🔧 Workload Generator

Five workload modes auto-populate the page reference string:

| Mode | Behavior |
|------|----------|
| **Custom** | Manual input — user types the reference string |
| **Random** | Uniformly random pages from `[0, max_page]` |
| **Locality of Reference** | High reuse probability with occasional spatial jumps |
| **Looping Pattern** | Cycles through a fixed sequence repeatedly |
| **Burst Pattern** | Alternates between focused bursts on a subset of pages |

Inputs used: **Max Page** and **Number of Requests**.

---

## 📈 Performance Dashboard

Powered by **matplotlib** (graceful fallback if unavailable):

| Graph | X-Axis | Y-Axis |
|-------|--------|--------|
| Page Faults vs Time | Step | Cumulative Faults |
| Hits vs Time | Step | Cumulative Hits |
| Fault Rate Over Time | Step | Fault Rate (%) |

Charts render inline in the dashboard panel. If matplotlib is not installed, a descriptive fallback message is shown — simulation still runs fully.

---

## 🏆 Algorithm Comparison Mode

Runs **FIFO, LRU, and OPTIMAL** on the identical input sequence simultaneously:

```
┌────────────┬────────┬──────┬────────────┐
│ Algorithm  │ Faults │ Hits │ Fault Rate │
├────────────┼────────┼──────┼────────────┤
│ FIFO       │   12   │   8  │  60.00%    │
│ LRU        │   9    │  11  │  45.00%    │
│ OPTIMAL ★  │   7    │  13  │  35.00%    │  ← Best highlighted
└────────────┴────────┴──────┴────────────┘
```

**Best algorithm** (lowest fault rate) is highlighted automatically.

---

## 📡 Live Metrics Panel

Updated in real-time during animated or step-wise simulation:

```
Requests    Faults    Hits    Fault Rate
   20          9        11      45.00%
```

Additional panels:
- **Memory Utilization**: Progress bar + `used / free` memory values
- **Frame Snapshot**: Current frame contents with fault/hit color cues
- **Fragmentation Summary**: Internal (KB), External (KB), Hole Count
- **Analysis & Insights**: Auto-generated textual interpretation of run

---

## 💾 Export & Reporting

### JSON Export
Timestamped file — e.g., `vm_simulation_20250420_143215.json`

```json
{
  "metadata": {
    "algorithm": "LRU",
    "frames": 3,
    "page_reference_string": [1, 2, 3, 4, 1, 2, 5],
    "workload_mode": "Locality",
    "timestamp": "2025-04-20T14:32:15"
  },
  "metrics": {
    "total_requests": 7,
    "page_faults": 5,
    "page_hits": 2,
    "fault_rate": 0.714
  },
  "fragmentation": {
    "internal_kb": 6.2,
    "external_kb": 12.0,
    "hole_count": 3
  },
  "timeline": [
    {
      "step": 1,
      "page": 1,
      "frames": [1, null, null],
      "fault": true,
      "replaced": null
    }
  ]
}
```

### PDF Export
Generated via **reportlab** (graceful fallback if unavailable). Contains full simulation summary, metrics table, and fragmentation stats.

### Clipboard
Copy the full JSON payload to clipboard with one click.

---

## 🖥️ Installation

### Prerequisites

```bash
python3 --version   # Requires Python 3.x
```

Tkinter is included with standard Python. Verify:
```bash
python3 -c "import tkinter; print('tkinter OK')"
```

### Clone & Run

```bash
git clone https://github.com/your-username/vm-simulator.git
cd vm-simulator
python3 vm_simulator_gui.py
```

### Optional Dependencies

```bash
pip install matplotlib   # For performance dashboard graphs
pip install reportlab    # For PDF export
```

Both are optional — the simulator runs fully without them, showing graceful fallback messages in their respective panels.

---

## 🚀 Usage

### Step-by-Step Workflow

```
1. Set number of frames (e.g., 3)
2. Choose page replacement algorithm: FIFO / LRU / OPTIMAL
3. Select workload mode or enter custom reference string
4. Set Max Page and Number of Requests if using generator
5. Click [Run Animated] OR press Enter
6. Watch the Frame Snapshot, Timeline, and Metrics update live
7. Switch to Algorithm Comparison tab for side-by-side benchmarking
8. View Performance Dashboard for matplotlib graphs
9. Export results via JSON / PDF / Clipboard
10. Press Escape to clear and reset
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Run animated simulation |
| `Escape` | Clear / reset all |

### Playback Speed

| Speed | Behavior |
|-------|----------|
| Slow | Best for step-by-step learning |
| Normal | Default |
| Fast | Rapid batch analysis |

---

## 🧪 Sample Scenarios

### Classic (Textbook)
```
Reference String: 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1
Frames: 3
Algorithm: FIFO / LRU / OPTIMAL
```
Classic OS textbook example — great for comparing all three algorithms.

### Cache Miss Burst
```
Workload: Burst Pattern
Max Page: 10, Requests: 30, Frames: 2
```
Stresses the replacement algorithm with repeated thrashing.

### Balanced
```
Workload: Locality of Reference
Max Page: 8, Requests: 25, Frames: 4
```
Simulates realistic process behavior with working-set locality.

---

## 🔍 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: matplotlib` | `pip install matplotlib` |
| `ModuleNotFoundError: reportlab` | `pip install reportlab` |
| Tkinter not found | Reinstall Python with Tk support or `sudo apt install python3-tk` |
| Graphs not rendering | Ensure matplotlib ≥ 3.x; check `matplotlib.use('TkAgg')` backend |
| PDF export fails silently | Install reportlab and re-run |

---

## 🔭 Future Improvements

- [ ] Add **Clock / Second-Chance** algorithm
- [ ] Add **NRU (Not Recently Used)** policy
- [ ] **Working Set Model** simulation
- [ ] Thrashing detection and visualization
- [ ] Multi-process simulation with shared frames
- [ ] Web-based port (Flask + React or Streamlit)
- [ ] Configurable frame/page sizes (beyond 4 KB fixed)
- [ ] Side-by-side animated comparison view
- [ ] Save/load simulation sessions

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first to discuss scope.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

> *Built for OS coursework. Designed to make virtual memory tangible.*
