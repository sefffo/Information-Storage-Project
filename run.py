"""
run.py - RAID Multimedia Storage Performance Simulator
=====================================================
Main application file that provides a Gradio-based web interface for simulating
RAID (Redundant Array of Independent Disks) storage configurations.

This application allows users to:
1. Scan folders for multimedia files (images and videos)
2. Configure RAID levels (RAID 0, RAID 1, RAID 5)
3. Simulate storage performance and capacity metrics
4. Visualize results through charts and reports
5. Generate virtual disk structures showing data distribution
6. Calculate disk requirements using proper formulas from course materials

Author: Information Storage Project Team
Date: 2025
Updated: December 2025 - Added disk performance calculations from sec-2-1.pdf
"""

# ============================================================================
# SECTION 1: IMPORT STATEMENTS
# ============================================================================

# Standard library imports for system operations
import sys          # System-specific parameters and functions
import os           # Operating system interface for file/directory operations
import shutil       # High-level file operations (copy, move, archive)
import math         # Mathematical functions
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
# Path handling and datetime
from pathlib import Path            # Object-oriented filesystem paths
from datetime import datetime       # Date and time manipulation

# Third-party libraries
import gradio as gr                 # Web UI framework for creating interactive interfaces
import pandas as pd                 # Data manipulation and analysis library
import matplotlib.pyplot as plt     # Plotting and visualization library
from PIL import Image              # Python Imaging Library for image processing


# ============================================================================
# SECTION 2: PATH CONFIGURATION
# ============================================================================

# Get the directory where this script is located
APP_DIR = Path(__file__).parent

# Define the reports directory where all output files will be saved
REPORTS_DIR = APP_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Add the Modules directory to Python's module search path
sys.path.insert(0, str(APP_DIR / "Modules"))


# ============================================================================
# SECTION 3: IMPORT CUSTOM MODULES
# ============================================================================

# Import data analysis functions
from Data_Analysis import (
    append_run,
    save_report_csv,
    summary_statistics
)

# Import RAID calculation functions
from Raid_Calculation import (
    usable_capacity_percent,
    redundancy_percent,
    space_efficiency,
    calculate_capacity_breakdown_dict,
    get_write_penalty,
    calculate_disk_load_iops
)

# Import RAID simulation functions
from Raid_Simulation import (
    simulate_raid_read,
    simulate_raid_write
)

# Import disk performance functions (NEW!)
try:
    from Disk_Performance import (
        calculate_service_time,
        calculate_iops,
        calculate_disk_capacity_required,
        calculate_disk_performance_required,
        calculate_total_disks_required
    )
    DISK_PERF_AVAILABLE = True
except ImportError:
    DISK_PERF_AVAILABLE = False
    print("⚠️  Disk_Performance module not available. Using simplified calculations.")


# ============================================================================
# SECTION 4: GLOBAL CONSTANTS AND STATE
# ============================================================================

# Supported multimedia file extensions
SUPPORTED_EXT = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif",  # Images
    ".mp4", ".mov", ".mkv", ".avi", ".webm"   # Videos
}

# Global state for folder scan results
last_scan = {
    "folder": None,
    "files": [],
    "total_bytes": 0
}

# Disk specifications (typical 15K RPM enterprise drive)
# These values are from sec-2-1.pdf examples
DISK_SPECS = {
    "seek_time_ms": 5.0,           # Average seek time
    "rpm": 15000,                   # Rotations per minute
    "transfer_rate_mbps": 40,      # MB/s transfer rate
    "capacity_gb": 100,             # Disk capacity
    "io_size_kb": 4                 # Typical I/O size
}


# ============================================================================
# SECTION 5: FOLDER SCANNING FUNCTION
# ============================================================================

def scan_folder(folder_path, progress=gr.Progress()):
    """
    Scans a folder recursively for multimedia files and collects metadata.
    """
    folder_path = os.path.normpath(folder_path.strip('"').strip("'"))
    
    if not os.path.isdir(folder_path):
        return "❌ Invalid folder.", None, 0
    
    files = [
        os.path.join(r, f)
        for r, _, n in os.walk(folder_path)
        for f in n
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
    ]
    
    if not files:
        return "❌ No media files found.", None, 0

    rows = []
    total_bytes = 0
    
    for p in files:
        size = os.path.getsize(p)
        total_bytes += size
        res = "N/A"
        
        if p.lower().endswith(tuple({".jpg", ".png", ".bmp", ".gif"})):
            try:
                with Image.open(p) as im:
                    res = f"{im.width}x{im.height}"
            except:
                pass
        
        rows.append({
            "Filename": os.path.basename(p),
            "Extension": os.path.splitext(p)[1],
            "Size (KB)": round(size/1024, 2),
            "Resolution": res
        })

    last_scan.update({
        "folder": folder_path,
        "files": files,
        "total_bytes": total_bytes
    })
    
    ext_counts = pd.DataFrame(rows)["Extension"].value_counts().to_string()
    summary = f"## 📊 Scan Results\n- **Files:** {len(files)}\n- **Size:** {total_bytes/1024**2:.2f} MB\n\n### Types:\n{ext_counts}"
    
    return summary, pd.DataFrame(rows[:200]), total_bytes/1024**2


# ============================================================================
# SECTION 6: DISK PERFORMANCE CALCULATIONS (NEW!)
# ============================================================================

def calculate_disk_metrics(num_disks, raid_level, total_capacity_gb, app_iops_required):
    """
    Calculate disk performance metrics using formulas from sec-2-1.pdf.
    
    Returns dictionary with:
    - service_time_ms: Disk service time
    - iops_per_disk: IOPS each disk can handle (70% utilization)
    - disks_for_capacity: Disks needed for capacity (Dc)
    - disks_for_performance: Disks needed for performance (Dp)
    - total_disks_required: max(Dc, Dp)
    - is_capacity_bottleneck: True if capacity is limiting factor
    """
    if not DISK_PERF_AVAILABLE:
        # Fallback to simplified estimates
        return {
            "service_time_ms": 7.1,
            "iops_per_disk": 98,
            "disks_for_capacity": math.ceil(total_capacity_gb / DISK_SPECS["capacity_gb"]),
            "disks_for_performance": num_disks,
            "total_disks_required": num_disks,
            "is_capacity_bottleneck": False
        }
    
    # Calculate service time using formula from sec-2-1.pdf
    service_time = calculate_service_time(
        seek_time_ms=DISK_SPECS["seek_time_ms"],
        disk_rpm=DISK_SPECS["rpm"],
        data_block_size_kb=DISK_SPECS["io_size_kb"],
        transfer_rate_mbps=DISK_SPECS["transfer_rate_mbps"]
    )
    
    # Calculate IOPS per disk (70% utilization for acceptable response time)
    iops_per_disk = calculate_iops(service_time, utilization=0.7)
    
    # Calculate disk requirements
    disk_reqs = calculate_total_disks_required(
        total_capacity_gb=total_capacity_gb,
        disk_capacity_gb=DISK_SPECS["capacity_gb"],
        app_iops=app_iops_required,
        disk_iops=iops_per_disk
    )
    
    return {
        "service_time_ms": service_time,
        "iops_per_disk": iops_per_disk,
        "disks_for_capacity": disk_reqs["disks_for_capacity"],
        "disks_for_performance": disk_reqs["disks_for_performance"],
        "total_disks_required": disk_reqs["total_disks_required"],
        "is_capacity_bottleneck": disk_reqs["disks_for_capacity"] > disk_reqs["disks_for_performance"]
    }


def calculate_raid_iops_with_workload(num_disks, raid_level, iops_per_disk, read_percent=70, write_percent=30):
    """
    Calculate RAID array IOPS considering write penalty.
    Uses formula from sec-5-1.pdf slide 22.
    
    Returns dictionary with:
    - total_iops_capacity: Max IOPS the RAID array can handle
    - disk_load_iops: Actual disk load for a given workload
    - write_penalty: Write penalty for this RAID level
    """
    # Calculate maximum IOPS the array can provide
    # This is simplified - assumes even distribution
    if raid_level == "RAID 0":
        max_array_iops = iops_per_disk * num_disks
    elif raid_level == "RAID 1":
        # Writes are limited by mirroring
        max_array_iops = iops_per_disk * num_disks * 0.6
    elif raid_level == "RAID 5":
        # Limited by parity overhead
        max_array_iops = iops_per_disk * (num_disks - 1) * 0.7
    else:
        max_array_iops = iops_per_disk * num_disks
    
    # Calculate disk load for typical workload using write penalty formula
    # Assuming application generates max_array_iops at the workload ratio
    disk_load = calculate_disk_load_iops(
        total_iops=max_array_iops,
        read_percent=read_percent,
        write_percent=write_percent,
        raid_level=raid_level
    )
    
    return {
        "total_iops_capacity": int(max_array_iops),
        "disk_load_iops": int(disk_load),
        "write_penalty": get_write_penalty(raid_level)
    }


# ============================================================================
# SECTION 7: VIRTUAL DISK BUILDER FUNCTION
# ============================================================================

def build_virtual_disks(raid, num, files, ts, max_workers=4):
    """
    Creates virtual disk structure simulating RAID data distribution using multi-threading.
    
    Args:
        raid: RAID level string
        num: Number of disks
        files: List of file paths to distribute
        ts: Timestamp string
        max_workers: Number of threads for parallel file copying (default: 4)
    
    Returns:
        Tuple of (virtual_disks_folder_path, zip_archive_path)
    """
    base = REPORTS_DIR / f"virtual_disks_{ts}" / raid.replace(" ", "_")
    disks = {i: base / f"disk_{i}" for i in range(num)}
    
    # Create all disk directories
    for d in disks.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # Thread-safe disk load tracking
    disk_loads = {i: 0 for i in range(num)}
    disk_loads_lock = threading.Lock()
    
    # Determine file distribution (which file goes to which disk)
    file_distribution = []
    
    for idx, f in enumerate(files):
        size = os.path.getsize(f)
        
        if raid == "RAID 1":
            # RAID 1: Copy to all disks
            targets = list(disks.keys())
        else:
            # RAID 0 and RAID 5: Use load balancing
            candidates = [
                d for d in range(num)
                if (raid != "RAID 5" or d != (idx % num))
            ]
            target = min(candidates, key=lambda x: disk_loads[x])
            targets = [target]
        
        # Update disk loads for planning
        for t in targets:
            disk_loads[t] += size
        
        # Store file distribution info
        file_distribution.append({
            "file_path": f,
            "targets": targets,
            "idx": idx,
            "size": size
        })
    
    # ========================================================================
    # Multi-threaded file copying
    # ========================================================================
    
    def copy_file_to_disks(file_info):
        """Worker function to copy a single file to its target disk(s)."""
        f = file_info["file_path"]
        targets = file_info["targets"]
        idx = file_info["idx"]
        
        try:
            # Copy file to each target disk
            for t in targets:
                shutil.copy2(f, disks[t])
            
            # Create RAID 5 parity placeholder
            if raid == "RAID 5":
                p_disk = idx % num
                parity_file = disks[p_disk] / f"{Path(f).stem}_PARITY.txt"
                parity_file.write_text(
                    f"Parity for {Path(f).name}\nData on disk {targets[0]}"
                )
            
            return True, f
        except Exception as e:
            return False, f"Error copying {f}: {str(e)}"
    
    # Execute file copying in parallel using ThreadPoolExecutor
    print(f"Starting multi-threaded file distribution ({max_workers} workers)...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all copy tasks
        futures = {
            executor.submit(copy_file_to_disks, file_info): file_info 
            for file_info in file_distribution
        }
        
        # Track progress
        completed = 0
        total = len(futures)
        
        for future in as_completed(futures):
            success, result = future.result()
            completed += 1
            
            if not success:
                print(f"⚠️  {result}")
            
            # Progress indicator
            if completed % 10 == 0 or completed == total:
                print(f"Progress: {completed}/{total} files distributed")
    
    print(f"✅ All {total} files distributed successfully!")
    
    # ========================================================================
    # Create ZIP archive
    # ========================================================================
    
    print("Creating ZIP archive...")
    zip_path = shutil.make_archive(
        str(base.parent / base.name),
        "zip",
        base
    )
    print(f"✅ ZIP archive created: {os.path.basename(zip_path)}")
    
    return str(base), zip_path

# ============================================================================
# SECTION 8: MAIN SIMULATION RUNNER FUNCTION (ENHANCED!)
# ============================================================================

def run_simulation(num_disks, raid_level, progress=gr.Progress()):
    """
    Executes complete RAID simulation with disk performance calculations.
    Now includes proper IOPS, service time, and disk requirement formulas.
    """
    if not last_scan["files"]:
        return "❌ Scan folder first.", *([None]*5)
    
    # ========================================================================
    # Calculate Storage Requirements
    # ========================================================================
    
    total_capacity_gb = last_scan["total_bytes"] / (1024**3)  # Convert to GB
    
    # Estimate application IOPS (simplified: based on file count)
    # Assume 10 IOPS per 100 files as baseline
    estimated_app_iops = max(100, len(last_scan["files"]) * 0.1)
    
    # ========================================================================
    # Calculate Disk Performance Metrics (NEW!)
    # ========================================================================
    
    disk_metrics = calculate_disk_metrics(
        num_disks=num_disks,
        raid_level=raid_level,
        total_capacity_gb=total_capacity_gb,
        app_iops_required=estimated_app_iops
    )
    
    # ========================================================================
    # Calculate RAID IOPS with Workload (NEW!)
    # ========================================================================
    
    raid_iops = calculate_raid_iops_with_workload(
        num_disks=num_disks,
        raid_level=raid_level,
        iops_per_disk=disk_metrics["iops_per_disk"],
        read_percent=70,  # Typical read-heavy workload
        write_percent=30
    )
    
    # ========================================================================
    # Run Performance Simulations
    # ========================================================================
    
    r_ms = simulate_raid_read(raid_level, num_disks)
    w_ms = simulate_raid_write(raid_level, num_disks)
    
    # ========================================================================
    # Collect All Simulation Metrics (ENHANCED!)
    # ========================================================================
    
    run_data = {
        # RAID configuration
        "raid_level": raid_level,
        "disk_count": num_disks,
        
        # File statistics
        "total_files": len(last_scan["files"]),
        "total_size_gb": total_capacity_gb,
        
        # Performance metrics
        "read_time_ms": r_ms,
        "write_time_ms": w_ms,
        "total_time_ms": r_ms + w_ms,
        
        # Disk performance metrics (from sec-2-1.pdf formulas)
        "service_time_ms": disk_metrics["service_time_ms"],
        "iops_per_disk": int(disk_metrics["iops_per_disk"]),
        "disks_for_capacity_Dc": disk_metrics["disks_for_capacity"],
        "disks_for_performance_Dp": disk_metrics["disks_for_performance"],
        "total_disks_required": disk_metrics["total_disks_required"],
        "bottleneck": "Capacity" if disk_metrics["is_capacity_bottleneck"] else "Performance",
        
        # RAID IOPS with write penalty (from sec-5-1.pdf formulas)
        "array_iops_capacity": raid_iops["total_iops_capacity"],
        "disk_load_iops": raid_iops["disk_load_iops"],
        "write_penalty": raid_iops["write_penalty"],
        
        # Capacity metrics
        "usable_%": usable_capacity_percent(num_disks, raid_level),
        "efficiency_%": space_efficiency(num_disks, raid_level) * 100
    }
    
    df = append_run(None, run_data)
    stats_df = summary_statistics(df)
    
    # ========================================================================
    # Generate Timestamp and File Paths
    # ========================================================================
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files = {
        "report": REPORTS_DIR / f"report_{ts}.csv",
        "stats": REPORTS_DIR / f"summary_{ts}.csv",
        "pie": REPORTS_DIR / f"pie_{ts}.png",
        "bar": REPORTS_DIR / f"bar_{ts}.png"
    }
    
    # ========================================================================
    # Save CSV Reports
    # ========================================================================
    
    save_report_csv(df, files["report"].name)
    save_report_csv(stats_df, files["stats"].name)
    
    # ========================================================================
    # Create Capacity Distribution Pie Chart
    # ========================================================================
    
    fig1 = plt.figure(figsize=(5,5))
    bd = calculate_capacity_breakdown_dict(num_disks, raid_level)
    
    plt.pie(
        [bd["usable"], bd["parity"], bd["mirror"]],
        labels=["Usable", "Parity", "Mirror"],
        autopct="%1.1f%%"
    )
    plt.title("Capacity Distribution")
    fig1.savefig(files["pie"])
    
    # ========================================================================
    # Create Performance Bar Chart
    # ========================================================================
    
    fig2 = plt.figure(figsize=(6,4))
    plt.bar([raid_level], [run_data["total_time_ms"]])
    plt.ylabel("Time (ms)")
    plt.title("Total Performance Time")
    fig2.savefig(files["bar"])

    # ========================================================================
    # Build Virtual Disk Structure
    # ========================================================================
    
    v_folder, v_zip = build_virtual_disks(
        raid_level,
        num_disks,
        last_scan["files"],
        ts
    )
    
    # ========================================================================
    # Format Success Message (ENHANCED!)
    # ========================================================================
    
    msg = f"""## ✅ Done: {raid_level}

### 📊 Disk Performance Metrics
- **Service Time (Ts):** {disk_metrics['service_time_ms']:.2f} ms
- **IOPS per Disk:** {disk_metrics['iops_per_disk']:.0f} (70% utilization)
- **Array IOPS Capacity:** {raid_iops['total_iops_capacity']} IOPS
- **Write Penalty:** {raid_iops['write_penalty']}x

### 💾 Disk Requirements
- **For Capacity (Dc):** {disk_metrics['disks_for_capacity']} disks
- **For Performance (Dp):** {disk_metrics['disks_for_performance']} disks
- **Total Required:** {disk_metrics['total_disks_required']} disks
- **Bottleneck:** {'Capacity' if disk_metrics['is_capacity_bottleneck'] else 'Performance'}

### 📁 Output
Saved to `reports/`  
Zip: `{os.path.basename(v_zip)}`
"""
    
    return (
        msg,
        df,
        stats_df,
        fig1,
        fig2,
        [str(f) for f in files.values()] + [v_zip]
    )


# ============================================================================
# SECTION 9: GRADIO USER INTERFACE DEFINITION
# ============================================================================

with gr.Blocks(title="RAID Sim", theme=gr.themes.Soft()) as app:
    gr.HTML(
        "<h1 style='text-align:center; background:#667eea; color:white; "
        "padding:10px; border-radius:10px;'>💾 RAID Simulator with Disk Performance Analysis</h1>"
    )
    
    state_size = gr.State(0)
    
    with gr.Tabs():
        with gr.Tab("1. Load"):
            with gr.Row():
                inp = gr.Textbox(label="Path")
                btn = gr.Button("Scan", variant="primary")
            
            out_md = gr.Markdown()
            out_tbl = gr.DataFrame()
            
            btn.click(scan_folder, inp, [out_md, out_tbl, state_size])
        
        with gr.Tab("2. Config"):
            d_sld = gr.Slider(2, 12, value=4, step=1, label="Disks")
            r_rad = gr.Radio(["RAID 0", "RAID 1", "RAID 5"], value="RAID 5", label="Level")
            
            c_btn = gr.Button("Calc Metrics")
            c_out = gr.Markdown()
            
            c_btn.click(
                lambda n, r, s: f"**Usable:** {usable_capacity_percent(n,r):.1f}% | "
                                f"**Eff:** {space_efficiency(n,r):.2%} | "
                                f"**Write Penalty:** {get_write_penalty(r)}x",
                [d_sld, r_rad, state_size],
                c_out
            )

        with gr.Tab("3. Run"):
            s_btn = gr.Button("🚀 Simulate", variant="primary")
            s_out = gr.Markdown()
            
            with gr.Row():
                p1 = gr.Plot(label="Capacity Distribution")
                p2 = gr.Plot(label="Performance")
            
            with gr.Row():
                res_df = gr.DataFrame(label="Run Data")
                stats_tbl = gr.DataFrame(label="Summary Statistics")
            
            dl = gr.File(label="Download Reports & Virtual Disks", file_count="multiple")
            
            s_btn.click(
                run_simulation,
                [d_sld, r_rad],
                [s_out, res_df, stats_tbl, p1, p2, dl]
            )


if __name__ == "__main__":
    app.launch(inbrowser=True)
