# Virtual Memory Optimization Simulator

A comprehensive, interactive educational tool for simulating and analyzing virtual memory management with advanced page replacement algorithms, fragmentation analysis, and performance visualization.

## ⚡ Quick Start

### Installation
```bash
# Clone or navigate to project directory
cd /Users/somesh/Projects/osfinal

# Install optional dependencies (recommended)
pip install matplotlib reportlab

# Run the simulator
python3 vm_simulator_gui.py
```

### First Simulation (30 seconds)
1. **Load a demo**: Click "Load Demo" button
2. **Run animated**: Click "Run Animated" to see step-by-step execution
3. **View results**: Watch metrics and timeline update in real-time

---

## 🎮 Main Features

### Core Algorithms
- **FIFO**: First-In-First-Out page replacement
- **LRU**: Least Recently Used (optimal for temporal locality)
- **OPTIMAL**: Belady's Algorithm (theoretical minimum)

### Advanced Analysis
- 📊 **Fragmentation Analysis**: Internal and external memory fragmentation
- 📈 **Performance Graphs**: Visual metrics over simulation time
- 🔄 **Algorithm Comparison**: Side-by-side performance metrics
- 💾 **Memory Utilization**: Real-time memory usage tracking
- 📋 **Workload Generator**: Create realistic access patterns

### Export Options
- 📥 **JSON Report**: Complete simulation data export
- 📄 **PDF Report**: Professional formatted report
- 📋 **Clipboard Copy**: Quick JSON to clipboard

---

## 🎯 Key Concepts

### Page Replacement Algorithms
When physical memory is full and a new page is needed, one existing page must be evicted. Different algorithms choose which page to remove:

- **FIFO**: Removes oldest (earliest) page
- **LRU**: Removes least recently used page
- **OPTIMAL**: Removes page used farthest in future (requires perfect knowledge)

### Fragmentation
- **Internal**: Wasted space within allocated frames
- **External**: Free memory split into non-contiguous holes

### Demand Paging
- Pages loaded only when needed (on-demand)
- Page fault: Page not in memory, must load from disk
- Page hit: Page already in memory, no load needed

---

## 📖 Usage Guide

### Basic Simulation

1. **Enter Frames**: Number of physical memory frames (e.g., 3-4)
2. **Enter Pages**: Space-separated page reference string (e.g., "7 0 1 2 0 3 0 4")
3. **Choose Algorithm**: Select from FIFO, LRU, or OPTIMAL
4. **Playback Speed**: Select Slow, Normal, or Fast
5. **Run**: Click "Run Animated" or "Instant View"

### Generate Workload Patterns

1. Select **Workload Type**:
   - Random: Uniform random access
   - Locality: 70% nearby, 30% random (realistic)
   - Looping: Cyclic pattern
   - Burst: Clustered accesses

2. Set parameters:
   - Max Page #: Highest page number (0-N)
   - # of Requests: Sequence length

3. Click **Generate** to auto-fill page string

### Compare All Algorithms

1. Configure input parameters
2. Click **Compare All** button
3. View results in comparison table
4. Best algorithm highlighted

### View Performance Graphs

1. Run any simulation
2. Scroll to "Performance Dashboard" section
3. Three graphs displayed:
   - Page Faults vs Time
   - Page Hits vs Time
   - Fault Rate Over Time

### Export Results

**JSON Export**:
```bash
Click "📥 JSON Report"
→ File saved as sim_report_YYYYMMDD_HHMMSS.json
→ Opens automatically in default application
```

**PDF Export**:
```bash
Click "📄 PDF Report"
→ File saved as sim_report_YYYYMMDD_HHMMSS.pdf
→ Contains summary and fragmentation analysis
```

**Clipboard**:
```bash
Click "📋 Copy JSON"
→ JSON data copied to clipboard
→ Paste anywhere with Ctrl+V
```

---

## 📊 Understanding Results

### Live Metrics
- **Requests**: Total page requests processed
- **Faults**: Number of page faults (page not in memory)
- **Hits**: Number of successful accesses (page in memory)
- **Fault Rate**: Faults / Total Requests (lower is better)

### Fragmentation Analysis
- **Internal Fragmentation**: Wasted space within frames (KB)
- **External Fragmentation**: Free fragmented memory (KB)
- **Memory Holes**: Count of separate free areas

### Timeline
Shows step-by-step execution:
- Step number
- Page requested
- Result (Fault/Hit)
- Current frame contents

---

## 💡 Example Scenarios

### Scenario 1: Temporal Locality Test
```
Pages: 1 2 3 1 2 3 1 2 3 1 2 3
Frames: 3
Expected: Low fault rate (algorithm keeps recent pages)
Best: All algorithms (perfect locality)
```

### Scenario 2: Working Set Mismatch
```
Pages: 1 2 3 4 5 6 7 8 9 1 2 3 4 5 6 7 8 9
Frames: 3
Expected: High fault rate (only 3 frames, 9 active pages)
Best: LRU or OPTIMAL (adapt to pattern)
```

### Scenario 3: Sequential Access
```
Pages: 1 2 3 4 5 1 2 3 4 5
Frames: 4
Expected: FIFO poor, LRU/OPTIMAL good
Why: FIFO replaces oldest (1), but 1 needed again soon
```

---

## 🔧 Configuration

### Default Settings
- Frames: Variable (from demo or user input)
- Algorithm: FIFO
- Speed: Normal (520ms per step)
- Workload: Custom input

### Adjustable Parameters
- Number of frames (1-100)
- Page reference string
- Algorithm selection
- Playback speed
- Workload generation parameters

---

## 📋 Data Formats

### JSON Export Structure
```json
{
  "timestamp": "2026-04-21T10:54:16",
  "algorithm": "FIFO",
  "frames": 3,
  "workload_type": "Classic",
  "total_requests": 13,
  "page_faults": 10,
  "hits": 3,
  "fault_rate": 0.769,
  "fragmentation": {
    "internal_fragmentation_kb": 7.0,
    "external_fragmentation_kb": 8.0,
    "holes_count": 5
  },
  "steps": [...]
}
```

### Step Data
Each step includes:
- index: Step number
- request: Page number requested
- frames: Current frame contents
- fault: Boolean (true if page fault)
- action: Description of action
- internal_frag: Internal fragmentation at this step
- external_frag: External fragmentation at this step

---

## ✅ Checklist for Learning

- [ ] Understand FIFO, LRU, OPTIMAL differences
- [ ] Test with Classic sample (3 frames)
- [ ] Generate Random workload (high fault rate expected)
- [ ] Generate Locality workload (lower fault rate)
- [ ] Compare all algorithms on same input
- [ ] View graphs and analyze trends
- [ ] Export and review JSON data
- [ ] Experiment with different frame counts
- [ ] Understand fragmentation concepts
- [ ] Identify best algorithm for workload pattern

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Ensure you're in the correct directory
```bash
cd /Users/somesh/Projects/osfinal
python3 vm_simulator_gui.py
```

### Issue: Graphs not displaying
**Solution**: Install matplotlib
```bash
pip install matplotlib
```

### Issue: PDF export fails
**Solution**: Install reportlab
```bash
pip install reportlab
```

### Issue: Slow animation
**Solution**:
- Use "Instant View" instead of animated
- Reduce number of requests
- Change to "Fast" speed

---

## 📚 Learning Resources

### Concepts Covered
1. **Virtual Memory**: Demand paging and page replacement
2. **Page Replacement**: FIFO, LRU, OPTIMAL algorithms
3. **Performance Metrics**: Fault rate, hit rate
4. **Fragmentation**: Internal and external memory fragmentation
5. **Workload Patterns**: Locality of reference, working sets
6. **Performance Analysis**: Comparative algorithm analysis

### Related Topics
- Memory hierarchy
- Cache behavior
- Process scheduling
- Resource allocation
- OS performance tuning

---

## 📝 Requirements

### Minimum
- Python 3.7+
- tkinter (included with Python)
- OS: Windows, macOS, or Linux

### Recommended
- matplotlib: For graphs
- reportlab: For PDF reports

---

## 🎓 Academic Use

Perfect for:
- Operating Systems course projects
- Computer Architecture assignments
- Memory management studies
- Performance analysis labs
- Algorithm comparison research

---

## 🔄 Workflow

```
1. Configure Input
   ├─ Enter frames
   ├─ Enter pages (manual or generate)
   └─ Select algorithm

2. Run Simulation
   ├─ Choose animated or instant
   └─ Monitor metrics and timeline

3. Analyze Results
   ├─ View fragmentation stats
   ├─ Check graphs
   └─ Compare algorithms

4. Export Data
   ├─ JSON for data analysis
   ├─ PDF for reports
   └─ Copy for integration
```

---

## 🎯 Tips & Tricks

1. **Quick comparison**: Click "Compare All" to see all three algorithms instantly
2. **Pattern testing**: Use workload generator to test specific patterns
3. **Performance graphs**: Watch fault rate curve to understand algorithm behavior
4. **Export for analysis**: Use JSON export for spreadsheet analysis
5. **Batch testing**: Generate different workloads and compare results
6. **Frame optimization**: Try different frame counts to find optimal memory size

---

## 📞 Support

For issues, check:
1. Terminal error messages
2. Ensure Python 3.7+ is installed
3. Verify dependencies installed
4. Check file permissions
5. Review FEATURES.md for detailed documentation

---

## 📄 License

Educational tool for learning purposes.

---

**Quick Links**:
- 📖 Full Features: See `FEATURES.md`
- 📊 Sample Data: Use demo presets
- 🚀 Get Started: Click "Load Demo" then "Run Animated"

**Enjoy learning virtual memory concepts!** 🎓
