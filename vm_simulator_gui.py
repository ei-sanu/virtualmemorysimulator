
from collections import deque
from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
import subprocess
import platform
import urllib.parse

# Import simulator components
from simulator import (
    simulate_algorithm,
    SimulationResult,
    WorkloadGenerator,
    compare_algorithms,
    SimulationStep,
    MemoryMetrics,
)

# Try to import matplotlib for graphs
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


BACKGROUND = "#07111f"
PANEL = "#0f1b2e"
PANEL_ALT = "#12233b"
CARD = "#16263f"
CARD_HOVER = "#1b2f4d"
TEXT = "#f3f7ff"
MUTED = "#93a4bf"
ACCENT = "#4cc9f0"
ACCENT_2 = "#7cde8d"
WARNING = "#ffb703"
ERROR = "#fb7185"
GRID = "#27405f"

# New colors for effects
GLOW_FAULT = "#ff4757"
GLOW_HIT = "#2ed573"
INTERNAL_FRAG_COLOR = "#ff6348"
EXTERNAL_FRAG_COLOR = "#ee5a6f"
USED_MEMORY_COLOR = "#4cc9f0"
FREE_MEMORY_COLOR = "#e74c3c"

SAMPLE_SEQUENCES = {
    "Classic": (3, "7 0 1 2 0 3 0 4 2 3 0 3 2"),
    "Cache Miss Burst": (4, "1 2 3 4 5 1 2 6 7 1 2 3 4 5 6 7"),
    "Balanced": (3, "1 4 2 1 5 2 1 6 2 3 2 1 4 5"),
}

ALGO_INFO = {
    "FIFO": "Replaces the oldest page in memory. Simple and predictable.",
    "LRU": "Replaces the page that has not been used for the longest time.",
    "OPTIMAL": "Replaces the page that will not be used for the longest future interval.",
}

SPEED_DELAYS = {
    "Slow": 900,
    "Normal": 520,
    "Fast": 220,
}


# ============ Helper Functions ============
def export_to_json(result: SimulationResult, workload_type: str = "Custom") -> dict:
    """Export simulation results to JSON-compatible dictionary"""
    return {
        "timestamp": datetime.now().isoformat(),
        "algorithm": result.algorithm,
        "frames": result.frames,
        "workload_type": workload_type,
        "total_requests": len(result.pages),
        "page_faults": result.faults,
        "hits": result.hits,
        "fault_rate": float(result.fault_rate),
        "page_sequence": result.pages,
        "fragmentation": {
            "internal_fragmentation_kb": float(result.steps[-1].internal_frag) if result.steps else 0,
            "external_fragmentation_kb": float(result.steps[-1].external_frag) if result.steps else 0,
            "holes_count": result.steps[-1].holes_count if result.steps else 0,
        },
        "steps": [
            {
                "index": step.index,
                "request": step.request,
                "frames": step.frames,
                "fault": step.fault,
                "action": step.action,
                "internal_frag": float(step.internal_frag),
                "external_frag": float(step.external_frag),
            }
            for step in result.steps
        ]
    }


def export_to_pdf(results_dict: dict, filename: str = "sim_report.pdf"):
    """Export results to PDF (requires reportlab)"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors

        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#4cc9f0"),
            spaceAfter=30,
        )
        elements.append(Paragraph("Virtual Memory Simulator Report", title_style))
        elements.append(Spacer(1, 0.2*inch))

        # Summary
        summary_data = [
            ["Parameter", "Value"],
            ["Algorithm", results_dict.get("algorithm", "N/A")],
            ["Frames", str(results_dict.get("frames", "N/A"))],
            ["Total Requests", str(results_dict.get("total_requests", "N/A"))],
            ["Page Faults", str(results_dict.get("page_faults", "N/A"))],
            ["Hits", str(results_dict.get("hits", "N/A"))],
            ["Fault Rate", f"{results_dict.get('fault_rate', 0):.3f}"],
        ]

        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f1b2e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#f3f7ff")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#16263f")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#27405f")),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))

        # Fragmentation
        frag_data = results_dict.get("fragmentation", {})
        frag_info = [
            ["Metric", "Value"],
            ["Internal Fragmentation (KB)", f"{frag_data.get('internal_fragmentation_kb', 0):.2f}"],
            ["External Fragmentation (KB)", f"{frag_data.get('external_fragmentation_kb', 0):.2f}"],
            ["Number of Holes", str(frag_data.get("holes_count", 0))],
        ]

        frag_table = Table(frag_info)
        frag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f1b2e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#f3f7ff")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#16263f")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#27405f")),
        ]))
        elements.append(Paragraph("Fragmentation Analysis", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(frag_table)

        doc.build(elements)
        return True
    except ImportError:
        return False


def open_file(filepath):
    """Open a file with the default application"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", filepath])
        elif platform.system() == "Windows":
            os.startfile(filepath)
        else:  # Linux
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        print(f"Could not open file: {e}")


# ============ GUI Application ============
        raise ValueError("Frames must be greater than zero")
    if not pages:
        raise ValueError("Page sequence cannot be empty")

    memory = []
    queue = deque()
    recent = {}
    faults = 0
    steps = []

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
        else:
            raise ValueError("Invalid algorithm")

        steps.append(SimulationStep(index + 1, page, memory.copy(), fault, action))

    hits = len(pages) - faults
    return SimulationResult(
        algorithm=algorithm,
        pages=pages,
        frames=frames,
        faults=faults,
        hits=hits,
        fault_rate=faults / len(pages),
        steps=steps,
    )


class VirtualMemorySimulatorApp:
    def __init__(self, root):
        self.root = root
        self.animation_job = None
        self.current_step_index = -1
        self.current_result = None
        self.comparison_results = {}  # Store algorithm comparison results
        self.workload_generator = WorkloadGenerator()
        self.show_comparison = False  # Toggle for comparison mode
        self.show_graphs = False  # Toggle for performance dashboard

        # Current workload settings
        self.current_workload_type = "Custom"
        self.current_max_page = 10
        self.current_num_requests = 20

        self._configure_root()
        self._build_styles()
        self._build_ui()
        self._bind_shortcuts()
        self.load_sample("Classic")

    def _configure_root(self):
        self.root.title("Virtual Memory Optimization Simulator")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        self.root.configure(bg=BACKGROUND)

    def _build_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Root.TFrame", background=BACKGROUND)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("PanelAlt.TFrame", background=PANEL_ALT)
        style.configure("Card.TFrame", background=CARD, relief="flat")
        style.configure("Title.TLabel", background=BACKGROUND, foreground=TEXT, font=("Avenir Next", 26, "bold"))
        style.configure("Subtitle.TLabel", background=BACKGROUND, foreground=MUTED, font=("Avenir Next", 11))
        style.configure("PanelTitle.TLabel", background=PANEL, foreground=TEXT, font=("Avenir Next", 13, "bold"))
        style.configure("CardTitle.TLabel", background=CARD, foreground=TEXT, font=("Avenir Next", 12, "bold"))
        style.configure("CardText.TLabel", background=CARD, foreground=MUTED, font=("Avenir Next", 10))
        style.configure("MetricValue.TLabel", background=CARD, foreground=TEXT, font=("Avenir Next", 20, "bold"))
        style.configure("MetricLabel.TLabel", background=CARD, foreground=MUTED, font=("Avenir Next", 10))
        style.configure("Accent.TButton", background=ACCENT, foreground="#04111d", padding=(16, 10), font=("Avenir Next", 11, "bold"))
        style.map("Accent.TButton", background=[("active", "#61d7f3")])
        style.configure("Ghost.TButton", background=PANEL_ALT, foreground=TEXT, padding=(14, 10), font=("Avenir Next", 11, "bold"))
        style.map("Ghost.TButton", background=[("active", CARD_HOVER)])
        style.configure("Tool.TButton", background=CARD, foreground=TEXT, padding=(12, 8), font=("Avenir Next", 10, "bold"))
        style.map("Tool.TButton", background=[("active", CARD_HOVER)])
        style.configure("Compact.TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT, foreground=TEXT, arrowcolor=TEXT, bordercolor=GRID, lightcolor=GRID, darkcolor=GRID)
        style.map("Compact.TCombobox", fieldbackground=[("readonly", PANEL_ALT)], foreground=[("readonly", TEXT)])
        style.configure("Dark.Treeview", background=PANEL_ALT, fieldbackground=PANEL_ALT, foreground=TEXT, bordercolor=GRID, rowheight=30, font=("Avenir Next", 10))
        style.configure("Dark.Treeview.Heading", background=CARD, foreground=TEXT, relief="flat", font=("Avenir Next", 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#07111f")])
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL_ALT, background=ACCENT, bordercolor=PANEL_ALT, lightcolor=ACCENT, darkcolor=ACCENT)

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Header
        self.header = tk.Frame(self.root, bg=BACKGROUND)
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 14))
        self.header.grid_columnconfigure(0, weight=1)

        title_area = tk.Frame(self.header, bg=BACKGROUND)
        title_area.grid(row=0, column=0, sticky="w")
        tk.Label(title_area, text="Virtual Memory Optimization Simulator", bg=BACKGROUND, fg=TEXT, font=("Avenir Next", 24, "bold")).pack(anchor="w")
        tk.Label(title_area, text="Advanced simulation with demand paging, fragmentation analysis, performance metrics, and algorithm comparison.", bg=BACKGROUND, fg=MUTED, font=("Avenir Next", 11)).pack(anchor="w", pady=(6, 0))

        status_wrap = tk.Frame(self.header, bg=BACKGROUND)
        status_wrap.grid(row=0, column=1, sticky="e")
        self.status_badge = tk.Label(status_wrap, text="Ready", bg=PANEL_ALT, fg=TEXT, font=("Avenir Next", 10, "bold"), padx=14, pady=8)
        self.status_badge.pack(anchor="e")

        # Main scrollable area
        self.main = tk.Frame(self.root, bg=BACKGROUND)
        self.main.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        # Create canvas and scrollbar for scrollable interface
        self.canvas = tk.Canvas(self.main, bg=BACKGROUND, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BACKGROUND)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Enable mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Build UI sections in scrollable area
        self._build_controls_card()
        self._build_workload_card()
        self._build_metrics_card()
        self._build_fragmentation_card()
        self._build_utilization_card()
        self._build_memory_card()
        self._build_comparison_card()
        self._build_timeline_card()
        self._build_summary_card()
        self._build_graphs_card()
        self._build_export_card()

        # Footer with progress
        self.footer = tk.Frame(self.root, bg=BACKGROUND)
        self.footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        self.footer.grid_columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(self.footer, style="Horizontal.TProgressbar", mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    def _build_controls_card(self):
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)
        tk.Label(card, text="Simulation Controls", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w", columnspan=4)
        tk.Label(card, text="Configure input parameters, select algorithm, and choose playback speed.", bg=CARD, fg=MUTED, font=("Avenir Next", 10), wraplength=760, justify="left").grid(row=1, column=0, sticky="w", columnspan=4, pady=(4, 14))

        # Row 2: Frames and Pages
        tk.Label(card, text="Frames", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.frame_entry = tk.Entry(card, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Avenir Next", 11), highlightthickness=1, highlightbackground=GRID, highlightcolor=ACCENT)
        self.frame_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14), padx=(0, 12))

        tk.Label(card, text="Page Reference String", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=1, sticky="w", pady=(0, 6))
        self.pages_entry = tk.Entry(card, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Avenir Next", 11), highlightthickness=1, highlightbackground=GRID, highlightcolor=ACCENT)
        self.pages_entry.grid(row=3, column=1, sticky="ew", pady=(0, 14), padx=(0, 12))

        tk.Label(card, text="Algorithm", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=2, sticky="w", pady=(0, 6))
        self.algo_var = tk.StringVar(value="FIFO")
        self.algo_box = ttk.Combobox(card, textvariable=self.algo_var, values=["FIFO", "LRU", "OPTIMAL"], state="readonly", style="Compact.TCombobox", font=("Avenir Next", 11))
        self.algo_box.grid(row=3, column=2, sticky="ew", pady=(0, 14), padx=(0, 12))
        self.algo_box.bind("<<ComboboxSelected>>", self.update_algorithm_copy)

        tk.Label(card, text="Playback Speed", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=3, sticky="w", pady=(0, 6))
        self.speed_var = tk.StringVar(value="Normal")
        self.speed_box = ttk.Combobox(card, textvariable=self.speed_var, values=list(SPEED_DELAYS.keys()), state="readonly", style="Compact.TCombobox", font=("Avenir Next", 11))
        self.speed_box.grid(row=3, column=3, sticky="ew", pady=(0, 14))

        button_row = tk.Frame(card, bg=CARD)
        button_row.grid(row=4, column=0, columnspan=4, sticky="ew")
        button_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ttk.Button(button_row, text="Run Animated", style="Accent.TButton", command=self.run_animated).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(button_row, text="Instant View", style="Ghost.TButton", command=self.run_instant).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(button_row, text="Compare All", style="Tool.TButton", command=self.run_comparison).grid(row=0, column=2, sticky="ew", padx=8)
        ttk.Button(button_row, text="Load Demo", style="Tool.TButton", command=self.cycle_sample).grid(row=0, column=3, sticky="ew", padx=8)
        ttk.Button(button_row, text="Clear", style="Tool.TButton", command=self.clear_all).grid(row=0, column=4, sticky="ew", padx=(8, 0))

        self.algorithm_copy = tk.Label(card, text="", bg=CARD, fg=ACCENT, font=("Avenir Next", 10), wraplength=760, justify="left")
        self.algorithm_copy.grid(row=5, column=0, columnspan=4, sticky="w", pady=(14, 0))

        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

    def _build_metrics_card(self):
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)
        tk.Label(card, text="Live Metrics", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w", columnspan=4)

        self.metric_values = {}
        metric_specs = [
            ("Requests", "requests", ACCENT),
            ("Faults", "faults", ERROR),
            ("Hits", "hits", ACCENT_2),
            ("Fault Rate", "fault_rate", WARNING),
        ]

        for column, (label, key, color) in enumerate(metric_specs):
            metric = tk.Frame(card, bg=PANEL_ALT, highlightbackground=GRID, highlightthickness=1, padx=12, pady=10)
            metric.grid(row=1, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(14, 0))
            tk.Label(metric, text=label, bg=PANEL_ALT, fg=MUTED, font=("Avenir Next", 9, "bold")).pack(anchor="w")
            value = tk.Label(metric, text="--", bg=PANEL_ALT, fg=color, font=("Avenir Next", 20, "bold"))
            value.pack(anchor="w", pady=(4, 0))
            self.metric_values[key] = value

    def _build_workload_card(self):
        """Add workload generator UI"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        tk.Label(card, text="Workload Generator", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w", columnspan=4)
        tk.Label(card, text="Auto-generate realistic page reference patterns.", bg=CARD, fg=MUTED, font=("Avenir Next", 10)).grid(row=1, column=0, sticky="w", columnspan=4, pady=(4, 14))

        tk.Label(card, text="Workload Type", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.workload_var = tk.StringVar(value="Custom")
        workload_box = ttk.Combobox(card, textvariable=self.workload_var, values=["Custom", "Random", "Locality", "Looping", "Burst"], state="readonly", style="Compact.TCombobox", font=("Avenir Next", 11))
        workload_box.grid(row=3, column=0, sticky="ew", pady=(0, 14), padx=(0, 12))
        workload_box.bind("<<ComboboxSelected>>", self.update_workload_ui)

        tk.Label(card, text="Max Page #", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=1, sticky="w", pady=(0, 6))
        self.max_page_entry = tk.Entry(card, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Avenir Next", 11), highlightthickness=1, highlightbackground=GRID, highlightcolor=ACCENT)
        self.max_page_entry.insert(0, "10")
        self.max_page_entry.grid(row=3, column=1, sticky="ew", pady=(0, 14), padx=(0, 12))

        tk.Label(card, text="# of Requests", bg=CARD, fg=TEXT, font=("Avenir Next", 10, "bold")).grid(row=2, column=2, sticky="w", pady=(0, 6))
        self.num_requests_entry = tk.Entry(card, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Avenir Next", 11), highlightthickness=1, highlightbackground=GRID, highlightcolor=ACCENT)
        self.num_requests_entry.insert(0, "20")
        self.num_requests_entry.grid(row=3, column=2, sticky="ew", pady=(0, 14), padx=(0, 12))

        ttk.Button(card, text="Generate", style="Tool.TButton", command=self.generate_workload).grid(row=3, column=3, sticky="ew", pady=(0, 14))

        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

    def _build_fragmentation_card(self):
        """Add fragmentation analysis panel"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure((0, 1, 2), weight=1)

        tk.Label(card, text="Fragmentation Analysis", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w", columnspan=3)
        tk.Label(card, text="Memory fragmentation metrics from live simulation.", bg=CARD, fg=MUTED, font=("Avenir Next", 10)).grid(row=1, column=0, sticky="w", columnspan=3, pady=(4, 14))

        self.frag_values = {}
        frag_specs = [
            ("Internal Frag (KB)", "internal_frag", INTERNAL_FRAG_COLOR),
            ("External Frag (KB)", "external_frag", EXTERNAL_FRAG_COLOR),
            ("Memory Holes", "holes", WARNING),
        ]

        for column, (label, key, color) in enumerate(frag_specs):
            metric = tk.Frame(card, bg=PANEL_ALT, highlightbackground=GRID, highlightthickness=1, padx=12, pady=10)
            metric.grid(row=2, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0, 0))
            tk.Label(metric, text=label, bg=PANEL_ALT, fg=MUTED, font=("Avenir Next", 9, "bold")).pack(anchor="w")
            value = tk.Label(metric, text="--", bg=PANEL_ALT, fg=color, font=("Avenir Next", 20, "bold"))
            value.pack(anchor="w", pady=(4, 0))
            self.frag_values[key] = value

    def _build_utilization_card(self):
        """Add memory utilization metrics"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text="Memory Utilization", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")

        # Progress bar for utilization
        self.util_label = tk.Label(card, text="0% utilized", bg=CARD, fg=ACCENT, font=("Avenir Next", 11, "bold"))
        self.util_label.grid(row=1, column=0, sticky="w", pady=(10, 6))

        self.util_progress = ttk.Progressbar(card, style="Horizontal.TProgressbar", mode="determinate", maximum=100)
        self.util_progress.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        # Memory breakdown
        breakdown_frame = tk.Frame(card, bg=CARD)
        breakdown_frame.grid(row=3, column=0, sticky="ew")
        breakdown_frame.grid_columnconfigure((0, 1), weight=1)

        self.memory_used_label = tk.Label(breakdown_frame, text="Used: -- KB", bg=CARD, fg=USED_MEMORY_COLOR, font=("Avenir Next", 10, "bold"))
        self.memory_used_label.grid(row=0, column=0, sticky="w")

        self.memory_free_label = tk.Label(breakdown_frame, text="Free: -- KB", bg=CARD, fg=FREE_MEMORY_COLOR, font=("Avenir Next", 10, "bold"))
        self.memory_free_label.grid(row=0, column=1, sticky="e")

    def _build_memory_card(self):
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        tk.Label(card, text="Frame Snapshot", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")

        self.memory_frame = tk.Frame(card, bg=CARD)
        self.memory_frame.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        self.memory_frame.grid_columnconfigure(0, weight=1)
        self.memory_slots = []

        self.memory_empty = tk.Label(self.memory_frame, text="Run a simulation to populate frames.", bg=CARD, fg=MUTED, font=("Avenir Next", 11))
        self.memory_empty.pack(fill="both", expand=True, pady=8)

        self.step_label = tk.Label(card, text="Step: --", bg=CARD, fg=ACCENT, font=("Avenir Next", 11, "bold"))
        self.step_label.grid(row=2, column=0, sticky="w", pady=(16, 0))

    def _build_comparison_card(self):
        """Add algorithm comparison panel"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        tk.Label(card, text="Algorithm Comparison", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")

        self.comparison_tree = ttk.Treeview(
            card,
            columns=("algo", "faults", "hits", "fault_rate"),
            show="headings",
            style="Dark.Treeview",
            height=4
        )
        self.comparison_tree.heading("algo", text="Algorithm")
        self.comparison_tree.heading("faults", text="Page Faults")
        self.comparison_tree.heading("hits", text="Hits")
        self.comparison_tree.heading("fault_rate", text="Fault Rate")

        self.comparison_tree.column("algo", width=150, anchor="center")
        self.comparison_tree.column("faults", width=150, anchor="center")
        self.comparison_tree.column("hits", width=150, anchor="center")
        self.comparison_tree.column("fault_rate", width=150, anchor="center")

        self.comparison_tree.grid(row=1, column=0, sticky="nsew", pady=(14, 0))

    def _build_timeline_card(self):
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        tk.Label(card, text="Simulation Timeline", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")

        tree_wrap = tk.Frame(card, bg=CARD)
        tree_wrap.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)

        columns = ("step", "request", "result", "frames")
        self.timeline = ttk.Treeview(tree_wrap, columns=columns, show="headings", style="Dark.Treeview", selectmode="browse", height=10)
        self.timeline.heading("step", text="Step")
        self.timeline.heading("request", text="Request")
        self.timeline.heading("result", text="Result")
        self.timeline.heading("frames", text="Frames")
        self.timeline.column("step", width=80, anchor="center")
        self.timeline.column("request", width=90, anchor="center")
        self.timeline.column("result", width=180, anchor="w")
        self.timeline.column("frames", width=320, anchor="w")

        timeline_scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.timeline.yview)
        self.timeline.configure(yscrollcommand=timeline_scroll.set)
        self.timeline.grid(row=0, column=0, sticky="nsew")
        timeline_scroll.grid(row=0, column=1, sticky="ns")

    def _build_summary_card(self):
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        tk.Label(card, text="Analysis & Insights", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")

        self.summary_text = tk.Text(card, height=8, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Avenir Next", 10), wrap="word", padx=14, pady=12)
        self.summary_text.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        self.summary_text.configure(state="disabled")

    def _build_graphs_card(self):
        """Add performance dashboard with graphs"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text="Performance Dashboard", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(card, text="Visualize performance metrics across simulation steps.", bg=CARD, fg=MUTED, font=("Avenir Next", 10)).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.graph_container = tk.Frame(card, bg=CARD)
        self.graph_container.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        self.graph_container.grid_columnconfigure(0, weight=1)

        if MATPLOTLIB_AVAILABLE:
            self.graph_canvas = None
        else:
            tk.Label(self.graph_container, text="⚠️ Matplotlib not installed. Install with: pip install matplotlib",
                    bg=CARD, fg=WARNING, font=("Avenir Next", 10)).pack(pady=(10, 0))

    def _build_export_card(self):
        """Add export/report feature"""
        card = tk.Frame(self.scrollable_frame, bg=CARD, highlightbackground=GRID, highlightthickness=1, padx=18, pady=18)
        card.pack(fill="x", pady=(0, 14))
        card.grid_columnconfigure((0, 1, 2), weight=1)

        tk.Label(card, text="Export & Reports", bg=CARD, fg=TEXT, font=("Avenir Next", 14, "bold")).grid(row=0, column=0, sticky="w", columnspan=3)
        tk.Label(card, text="Download simulation results in various formats.", bg=CARD, fg=MUTED, font=("Avenir Next", 10)).grid(row=1, column=0, sticky="w", columnspan=3, pady=(4, 14))

        ttk.Button(card, text="📥 JSON Report", style="Tool.TButton", command=self.export_json).grid(row=2, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(card, text="📄 PDF Report", style="Tool.TButton", command=self.export_pdf).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Button(card, text="📋 Copy JSON", style="Tool.TButton", command=self.copy_json_to_clipboard).grid(row=2, column=2, sticky="ew", padx=(8, 0))

    def _bind_shortcuts(self):
        self.root.bind("<Return>", lambda event: self.run_animated())
        self.root.bind("<Escape>", lambda event: self.clear_all())

    def update_workload_ui(self, event=None):
        """Update UI when workload type changes"""
        workload_type = self.workload_var.get()
        if workload_type == "Custom":
            self.max_page_entry.config(state="disabled")
            self.num_requests_entry.config(state="disabled")
        else:
            self.max_page_entry.config(state="normal")
            self.num_requests_entry.config(state="normal")

    def generate_workload(self):
        """Generate workload based on selected type"""
        try:
            workload_type = self.workload_var.get()
            if workload_type == "Custom":
                return

            max_page = int(self.max_page_entry.get())
            num_requests = int(self.num_requests_entry.get())

            if workload_type == "Random":
                workload = self.workload_generator.random_workload(num_requests, max_page)
            elif workload_type == "Locality":
                workload = self.workload_generator.locality_workload(num_requests, max_page)
            elif workload_type == "Looping":
                loop_seq = list(range(min(5, max_page + 1)))
                workload = self.workload_generator.looping_workload(num_requests, loop_seq)
            elif workload_type == "Burst":
                workload = self.workload_generator.burst_workload(num_requests, max_page)
            else:
                return

            self.pages_entry.delete(0, tk.END)
            self.pages_entry.insert(0, " ".join(str(p) for p in workload))
            self.set_status(f"Generated {workload_type} workload", ACCENT_2)
        except Exception as e:
            messagebox.showerror("Workload Generation Error", str(e))

    def run_comparison(self):
        """Run all algorithms and compare results"""
        try:
            frames, pages, _ = self._parse_inputs()
            self.comparison_results = compare_algorithms(pages, frames)

            # Clear and populate comparison table
            for item in self.comparison_tree.get_children():
                self.comparison_tree.delete(item)

            best_algo = None
            best_fault_rate = float('inf')

            for algo in ["FIFO", "LRU", "OPTIMAL"]:
                result = self.comparison_results[algo]
                if result.fault_rate < best_fault_rate:
                    best_fault_rate = result.fault_rate
                    best_algo = algo

                self.comparison_tree.insert("", tk.END, values=(
                    algo,
                    result.faults,
                    result.hits,
                    f"{result.fault_rate:.3f}"
                ))

            # Highlight best algorithm
            for item in self.comparison_tree.get_children():
                values = self.comparison_tree.item(item)['values']
                if values[0] == best_algo:
                    self.comparison_tree.item(item, tags=('best',))

            self.comparison_tree.tag_configure('best', foreground=ACCENT_2)
            self.set_status(f"Best: {best_algo} ({best_fault_rate:.3f})", ACCENT_2)
            self.show_comparison = True

        except Exception as e:
            messagebox.showerror("Comparison Error", str(e))

    def export_json(self):
        """Export results to JSON file"""
        if not self.current_result:
            messagebox.showwarning("Export Error", "Run a simulation first")
            return

        try:
            filename = f"sim_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            result_dict = export_to_json(self.current_result, self.current_workload_type)

            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2)

            messagebox.showinfo("Export Success", f"Report saved to {filename}")
            open_file(filename)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_pdf(self):
        """Export results to PDF file"""
        if not self.current_result:
            messagebox.showwarning("Export Error", "Run a simulation first")
            return

        try:
            filename = f"sim_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            result_dict = export_to_json(self.current_result, self.current_workload_type)
            success = export_to_pdf(result_dict, filename)

            if success:
                messagebox.showinfo("Export Success", f"Report saved to {filename}")
                open_file(filename)
            else:
                messagebox.showwarning("Export Warning", "reportlab not installed. Install with: pip install reportlab")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def copy_json_to_clipboard(self):
        """Copy JSON results to clipboard"""
        if not self.current_result:
            messagebox.showwarning("Error", "Run a simulation first")
            return

        try:
            result_dict = export_to_json(self.current_result, self.current_workload_type)
            json_str = json.dumps(result_dict, indent=2)
            self.root.clipboard_clear()
            self.root.clipboard_append(json_str)
            self.set_status("JSON copied to clipboard", ACCENT_2)
        except Exception as e:
            messagebox.showerror("Copy Error", str(e))

    def _plot_graphs(self):
        """Plot performance graphs"""
        if not MATPLOTLIB_AVAILABLE or not self.current_result:
            return

        try:
            # Clear previous canvas
            if self.graph_canvas:
                self.graph_canvas.get_tk_widget().destroy()

            fig = Figure(figsize=(12, 4), dpi=80, facecolor=CARD)
            ax1 = fig.add_subplot(131)
            ax2 = fig.add_subplot(132)
            ax3 = fig.add_subplot(133)

            # Set background
            for ax in [ax1, ax2, ax3]:
                ax.set_facecolor(PANEL_ALT)
                for spine in ax.spines.values():
                    spine.set_edgecolor(GRID)

            # Plot 1: Faults vs Time
            steps = list(range(1, len(self.current_result.steps) + 1))
            faults = [sum(1 for s in self.current_result.steps[:i+1] if s.fault) for i in range(len(self.current_result.steps))]
            ax1.plot(steps, faults, color=ERROR, linewidth=2, marker='o', markersize=4)
            ax1.set_title('Page Faults vs Time', color=TEXT)
            ax1.set_xlabel('Step', color=TEXT)
            ax1.set_ylabel('Cumulative Faults', color=TEXT)
            ax1.tick_params(colors=TEXT)
            ax1.grid(True, color=GRID, alpha=0.3)

            # Plot 2: Hits vs Time
            hits = [sum(1 for s in self.current_result.steps[:i+1] if not s.fault) for i in range(len(self.current_result.steps))]
            ax2.plot(steps, hits, color=ACCENT_2, linewidth=2, marker='o', markersize=4)
            ax2.set_title('Page Hits vs Time', color=TEXT)
            ax2.set_xlabel('Step', color=TEXT)
            ax2.set_ylabel('Cumulative Hits', color=TEXT)
            ax2.tick_params(colors=TEXT)
            ax2.grid(True, color=GRID, alpha=0.3)

            # Plot 3: Fault Rate
            fault_rates = [(s.index - sum(1 for st in self.current_result.steps[:s.index] if not st.fault)) / s.index * 100 for s in self.current_result.steps]
            ax3.plot(steps, fault_rates, color=WARNING, linewidth=2, marker='s', markersize=4)
            ax3.set_title('Fault Rate Over Time', color=TEXT)
            ax3.set_xlabel('Step', color=TEXT)
            ax3.set_ylabel('Fault Rate (%)', color=TEXT)
            ax3.tick_params(colors=TEXT)
            ax3.grid(True, color=GRID, alpha=0.3)

            fig.tight_layout()

            self.graph_canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
            self.graph_canvas.draw()
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print(f"Graph plotting error: {e}")

    def update_algorithm_copy(self, event=None):
        algo = self.algo_var.get()
        self.algorithm_copy.config(text=ALGO_INFO.get(algo, ""))

    def set_status(self, text, color=PANEL_ALT):
        self.status_badge.config(text=text, bg=color)

    def load_sample(self, sample_name):
        frames, pages = SAMPLE_SEQUENCES[sample_name]
        self.frame_entry.delete(0, tk.END)
        self.frame_entry.insert(0, str(frames))
        self.pages_entry.delete(0, tk.END)
        self.pages_entry.insert(0, pages)
        self.set_status(f"Loaded {sample_name} sample", ACCENT_2)
        self.update_algorithm_copy()

    def cycle_sample(self):
        current = self.pages_entry.get().strip()
        samples = list(SAMPLE_SEQUENCES.items())
        for index, (_, (_, pages)) in enumerate(samples):
            if current == pages:
                next_name = samples[(index + 1) % len(samples)][0]
                self.load_sample(next_name)
                return
        self.load_sample(samples[0][0])

    def clear_all(self):
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        self.current_result = None
        self.current_step_index = -1
        self.comparison_results = {}

        self.frame_entry.delete(0, tk.END)
        self.pages_entry.delete(0, tk.END)
        self.timeline.delete(*self.timeline.get_children())
        self.comparison_tree.delete(*self.comparison_tree.get_children())

        self._clear_memory_slots()
        self._reset_metrics()
        self._reset_fragmentation()

        # Reset utilization
        self.util_label.config(text="0% utilized")
        self.util_progress.config(value=0)
        self.memory_used_label.config(text="Used: -- KB")
        self.memory_free_label.config(text="Free: -- KB")

        self._update_summary("Enter a sequence and run a simulation to see the timeline, frame state, and fault statistics.")
        self.progress.configure(maximum=1, value=0)
        self.step_label.config(text="Step: --")
        self.set_status("Ready", PANEL_ALT)

    def _reset_metrics(self):
        for key, label in self.metric_values.items():
            label.config(text="--")

    def _reset_fragmentation(self):
        for key, label in self.frag_values.items():
            label.config(text="--")

    def _clear_memory_slots(self):
        for widget in self.memory_frame.winfo_children():
            widget.destroy()
        self.memory_slots = []
        self.memory_empty = tk.Label(self.memory_frame, text="Run a simulation to populate frames.", bg=CARD, fg=MUTED, font=("Avenir Next", 11))
        self.memory_empty.pack(fill="both", expand=True, pady=8)

    def _build_memory_slots(self, frames):
        for widget in self.memory_frame.winfo_children():
            widget.destroy()

        self.memory_slots = []
        for index in range(frames):
            slot = tk.Frame(self.memory_frame, bg=PANEL_ALT, highlightbackground=GRID, highlightthickness=1, padx=14, pady=12)
            slot.grid(row=index, column=0, sticky="ew", pady=6)
            slot.grid_columnconfigure(1, weight=1)
            tk.Label(slot, text=f"Frame {index + 1}", bg=PANEL_ALT, fg=MUTED, font=("Avenir Next", 9, "bold")).grid(row=0, column=0, sticky="w")
            value_label = tk.Label(slot, text="—", bg=PANEL_ALT, fg=TEXT, font=("Avenir Next", 18, "bold"))
            value_label.grid(row=0, column=1, sticky="e")
            self.memory_slots.append((slot, value_label))

    def _update_summary(self, text):
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, text)
        self.summary_text.configure(state="disabled")

    def _parse_inputs(self):
        frames = int(self.frame_entry.get().strip())
        pages = [int(value) for value in self.pages_entry.get().split()]
        algorithm = self.algo_var.get().strip().upper()
        if algorithm not in {"FIFO", "LRU", "OPTIMAL"}:
            raise ValueError("Choose a valid algorithm")
        return frames, pages, algorithm

    def _render_step(self, step_index):
        if not self.current_result or not self.current_result.steps:
            return

        step = self.current_result.steps[step_index]
        action_text = step.action
        if step.fault:
            action_text = f"🔴 {action_text}"
        else:
            action_text = f"✅ {action_text}"

        self.step_label.config(text=f"Step {step.index} of {len(self.current_result.steps)} | Request {step.request} | {action_text}")

        # Update fragmentation metrics
        self.frag_values["internal_frag"].config(text=f"{step.internal_frag:.2f}")
        self.frag_values["external_frag"].config(text=f"{step.external_frag:.2f}")
        self.frag_values["holes"].config(text=str(step.holes_count))

        # Add glow effect on fault
        for index, (slot, value_label) in enumerate(self.memory_slots):
            if index < len(step.frames):
                value = step.frames[index]
                if step.fault and value == step.request:
                    value_label.config(text=str(value), fg=GLOW_FAULT)
                    slot.config(highlightbackground=GLOW_FAULT, highlightthickness=2)
                else:
                    value_label.config(text=str(value), fg=TEXT)
                    slot.config(highlightbackground=GRID, highlightthickness=1)
            else:
                value_label.config(text="—", fg=MUTED)
                slot.config(highlightbackground=GRID, highlightthickness=1)

        for item in self.timeline.get_children():
            self.timeline.selection_remove(item)

        self.timeline.selection_set(str(step.index - 1))
        self.timeline.see(str(step.index - 1))
        self.progress.configure(value=step.index)

    def _final_summary(self, result):
        fault_rate = f"{result.fault_rate:.3f}"
        final_step = result.steps[-1] if result.steps else None
        internal_frag = f"{final_step.internal_frag:.2f}" if final_step else "0"
        external_frag = f"{final_step.external_frag:.2f}" if final_step else "0"
        holes = final_step.holes_count if final_step else 0

        summary = [
            f"Algorithm: {result.algorithm}\n",
            f"Frames: {result.frames}\n",
            f"Total requests: {len(result.pages)}\n",
            f"Page faults: {result.faults}\n",
            f"Hits: {result.hits}\n",
            f"Fault rate: {fault_rate}\n\n",
            f"Fragmentation:\n",
            f"- Internal: {internal_frag} KB\n",
            f"- External: {external_frag} KB\n",
            f"- Memory holes: {holes}\n\n",
            "Interpretation:\n",
            f"- {ALGO_INFO.get(result.algorithm, '')}\n",
            "- The frame snapshot updates step by step during playback.\n",
            "- Fragmentation increases as pages are replaced.\n",
        ]
        return "".join(summary)

    def _populate_timeline(self, result):
        self.timeline.delete(*self.timeline.get_children())
        for step in result.steps:
            frames_text = "[" + ", ".join(str(frame) for frame in step.frames) + "]"
            outcome = "Page fault" if step.fault else "Hit"
            self.timeline.insert("", tk.END, iid=str(step.index - 1), values=(step.index, step.request, outcome, frames_text))

    def _start_simulation(self, animated):
        try:
            frames, pages, algorithm = self._parse_inputs()
            result = simulate_algorithm(pages, frames, algorithm)
        except Exception as error:
            messagebox.showerror("Invalid input", str(error))
            self.set_status("Input error", ERROR)
            return

        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

        self.current_result = result
        self.current_step_index = -1
        self._build_memory_slots(frames)
        self._populate_timeline(result)
        self.progress.configure(maximum=max(len(result.steps), 1), value=0)

        self.metric_values["requests"].config(text=str(len(result.pages)))
        self.metric_values["faults"].config(text=str(result.faults))
        self.metric_values["hits"].config(text=str(result.hits))
        self.metric_values["fault_rate"].config(text=f"{result.fault_rate:.3f}")

        # Update memory utilization
        total_memory_kb = frames * 4  # 4 KB per frame
        used_memory_kb = len(set(result.steps[-1].frames)) * 4 if result.steps else 0
        util_percent = (used_memory_kb / total_memory_kb * 100) if total_memory_kb > 0 else 0

        self.util_label.config(text=f"{util_percent:.1f}% utilized")
        self.util_progress.config(value=util_percent)
        self.memory_used_label.config(text=f"Used: {used_memory_kb:.0f} KB")
        self.memory_free_label.config(text=f"Free: {total_memory_kb - used_memory_kb:.0f} KB")

        self._update_summary(self._final_summary(result))
        self.set_status(f"Running {algorithm}", ACCENT)

        # Plot graphs if available
        self._plot_graphs()

        if animated:
            self.animation_delay = SPEED_DELAYS[self.speed_var.get()]
            self._advance_animation()
        else:
            self.current_step_index = len(result.steps) - 1
            self._render_step(self.current_step_index)
            self.set_status("Completed", ACCENT_2)

    def _advance_animation(self):
        if not self.current_result:
            return

        self.current_step_index += 1
        if self.current_step_index >= len(self.current_result.steps):
            self.animation_job = None
            self.set_status("Completed", ACCENT_2)
            return

        self._render_step(self.current_step_index)
        self.animation_job = self.root.after(self.animation_delay, self._advance_animation)

    def run_animated(self):
        self._start_simulation(animated=True)

    def run_instant(self):
        self._start_simulation(animated=False)


def main():
    root = tk.Tk()
    VirtualMemorySimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
