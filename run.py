#!/usr/bin/env python3
"""
==============================================================================
run.py - RAID Multimedia Storage Performance Simulator (Main Application)
==============================================================================

Purpose:
--------
This is the main entry point for the RAID Storage Simulator application.
It provides a web-based Gradio interface that allows users to:
  1. Scan folders for multimedia files (images/videos)
  2. Configure RAID parameters (disk count, RAID level)
  3. Simulate RAID operations and performance
  4. Visualize results through charts and reports
  5. Generate virtual disk structures and downloadable reports

RAID Levels Supported:
---------------------
- RAID 0: Striping (high performance, no redundancy)
- RAID 1: Mirroring (high redundancy, lower capacity)
- RAID 5: Striping with parity (balanced performance and redundancy)

Authors: Team Project
Date: 2024
Version: 1.0 (Optimized)
==============================================================================
"""

# ==============================================================================
# IMPORTS - External Libraries and System Modules
# ==============================================================================

import sys          # System-specific parameters and functions
import os           # Operating system interface for file/directory operations
import shutil       # High-level file operations (copy, move, archive)
import random       # Random number generation (for simulations)
import time         # Time-related functions
from pathlib import Path              # Object-oriented filesystem paths
from datetime import datetime         # Date and time manipulation

import gradio as gr                   # Web UI framework for ML/data apps
import pandas as pd                   # Data manipulation and analysis
import matplotlib.pyplot as plt       # Plotting and visualization
from PIL import Image                 # Python Imaging Library for image processing

# ==============================================================================
# PATH SETUP - Configure Application Directories
# ==============================================================================

# Get the absolute path of the directory containing this script
APP_DIR = Path(__file__).parent

# Define reports directory where all simulation outputs will be saved
REPORTS_DIR = APP_DIR / "reports"

# Create reports directory if it doesn't exist
# exist_ok=True prevents errors if directory already exists
REPORTS_DIR.mkdir(exist_ok=True)

# Add Modules directory to Python path so we can import our custom modules
sys.path.insert(0, str(APP_DIR / "Modules"))

# ==============================================================================
# IMPORT CUSTOM MODULES - Our RAID Simulation Components
# ==============================================================================

# Data analysis functions for storing and analyzing simulation results
from Data_Analysis import (
    append_run,              # Appends simulation run data to DataFrame
    save_report_csv,         # Saves DataFrames to CSV files
    summary_statistics       # Calculates statistical summaries (mean, std, etc.)
)

# RAID calculation functions for capacity and efficiency metrics
from Raid_Calculation import (
    usable_capacity_percent,            # Calculate usable storage percentage
    redundancy_percent,                 # Calculate redundancy overhead percentage
    space_efficiency,                   # Calculate space efficiency ratio
    calculate_capacity_breakdown_dict   # Get breakdown of capacity distribution
)

# RAID simulation functions for performance testing
from Raid_Simulation import (
    simulate_raid_read,      # Simulate read operation time
    simulate_raid_write      # Simulate write operation time
)

# ==============================================================================
# GLOBAL CONSTANTS - Configuration Values
# ==============================================================================

# Set of supported file extensions for multimedia files
# Images: jpg, jpeg, png, bmp, gif
# Videos: mp4, mov, mkv, avi, webm
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", 
                 ".mp4", ".mov", ".mkv", ".avi", ".webm"}

# Dictionary to store the last folder scan results
# This prevents re-scanning the same folder multiple times
last_scan = {
    "folder": None,        # Path of last scanned folder
    "files": [],          # List of file paths found
    "total_bytes": 0      # Total size of all files in bytes
}

# ==============================================================================
# FUNCTION: scan_folder
# ==============================================================================

def scan_folder(folder_path, progress=gr.Progress()):
    """
    Scans a directory for multimedia files and returns statistics.
    
    This function recursively walks through the specified directory and its
    subdirectories to find all supported multimedia files (images and videos).
    It collects file metadata and calculates summary statistics.
    
    Parameters:
    -----------
    folder_path : str
        Absolute or relative path to the folder to scan.
        Can include quotes which will be stripped.
    
    progress : gr.Progress
        Gradio progress indicator (optional, for UI feedback)
    
    Returns:
    --------
    tuple: (summary_markdown, dataframe, total_size_mb)
        - summary_markdown: Formatted string with scan statistics
        - dataframe: pandas DataFrame with file details (up to 200 files)
        - total_size_mb: Total size of all files in megabytes
    
    Example:
    --------
    >>> scan_folder("/path/to/media")
    ("## 📊 Scan Results...", DataFrame(...), 1234.56)
    """
    
    # Clean up the folder path by removing quotes and normalizing separators
    folder_path = os.path.normpath(folder_path.strip('"').strip("'"))
    
    # Validate that the path is actually a directory
    if not os.path.isdir(folder_path):
        return "❌ Invalid folder.", None, 0
    
    # Walk through directory tree and collect files with supported extensions
    # os.walk returns: (dirpath, dirnames, filenames) for each directory
    files = [
        os.path.join(r, f)  # Join directory path with filename
        for r, _, n in os.walk(folder_path)  # For each directory
        for f in n  # For each file in directory
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT  # Filter by extension
    ]
    
    # Check if any files were found
    if not files:
        return "❌ No media files found.", None, 0

    # Initialize lists for DataFrame construction
    rows = []           # List to store file information dictionaries
    total_bytes = 0     # Accumulator for total file size
    
    # Process each file to extract metadata
    for p in files:
        # Get file size in bytes
        size = os.path.getsize(p)
        total_bytes += size
        
        # Default resolution for non-images
        res = "N/A"
        
        # Try to get image resolution for image files
        if p.lower().endswith(tuple({".jpg", ".png", ".bmp", ".gif"})):
            try:
                # Open image and read dimensions
                with Image.open(p) as im:
                    res = f"{im.width}x{im.height}"
            except:
                # If image can't be opened, keep "N/A"
                pass
        
        # Append file information as dictionary
        rows.append({
            "Filename": os.path.basename(p),           # Just the filename, not full path
            "Extension": os.path.splitext(p)[1],       # File extension with dot
            "Size (KB)": round(size/1024, 2),          # Convert bytes to KB, 2 decimals
            "Resolution": res                           # Image resolution or "N/A"
        })

    # Update global last_scan dictionary for use in simulation
    last_scan.update({
        "folder": folder_path,
        "files": files,
        "total_bytes": total_bytes
    })
    
    # Create summary statistics
    # Count files by extension type
    ext_counts = pd.DataFrame(rows)["Extension"].value_counts().to_string()
    
    # Format summary in Markdown for nice UI display
    summary = f"""## 📊 Scan Results
- **Files:** {len(files)}
- **Size:** {total_bytes/1024**2:.2f} MB

### Types:
{ext_counts}"""
    
    # Return summary, first 200 files as DataFrame, and total size in MB
    return summary, pd.DataFrame(rows[:200]), total_bytes/1024**2

# ==============================================================================
# FUNCTION: build_virtual_disks
# ==============================================================================

def build_virtual_disks(raid, num, files, ts):
    """
    Creates virtual disk directory structure simulating RAID array.
    
    This function simulates how files would be distributed across physical
    disks in a RAID array. It creates separate directories for each disk
    and distributes files according to RAID level rules:
    - RAID 0: Files distributed round-robin for load balancing
    - RAID 1: All files copied to all disks (mirroring)
    - RAID 5: Files distributed with parity information
    
    Parameters:
    -----------
    raid : str
        RAID level ("RAID 0", "RAID 1", or "RAID 5")
    
    num : int
        Number of disks in the array
    
    files : list
        List of file paths to distribute
    
    ts : str
        Timestamp string for unique folder naming
    
    Returns:
    --------
    tuple: (virtual_disk_path, zip_archive_path)
        - virtual_disk_path: Path to the virtual disk directory
        - zip_archive_path: Path to the created ZIP archive
    
    File Distribution Logic:
    -----------------------
    RAID 0: Each file goes to least loaded disk (load balancing)
    RAID 1: Each file copied to ALL disks (complete mirroring)
    RAID 5: Each file goes to least loaded disk (excluding parity disk),
            parity information stored on rotating disk
    """
    
    # Create base directory structure: reports/virtual_disks_{timestamp}/RAID_X/
    base = REPORTS_DIR / f"virtual_disks_{ts}" / raid.replace(" ", "_")
    
    # Create dictionary mapping disk numbers to their directory paths
    # Example: {0: Path('reports/virtual_disks_20240101_120000/RAID_5/disk_0'), ...}
    disks = {i: base / f"disk_{i}" for i in range(num)}
    
    # Create all disk directories (including parent directories)
    for d in disks.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to track how much data is stored on each disk (for load balancing)
    # Key: disk number, Value: total bytes stored
    disk_loads = {i: 0 for i in range(num)}
    
    # Distribute files across disks according to RAID level
    for idx, f in enumerate(files):
        # Get file size for load balancing
        size = os.path.getsize(f)
        
        # === RAID-SPECIFIC FILE DISTRIBUTION LOGIC ===
        
        if raid == "RAID 1":
            # RAID 1: MIRRORING - Copy to ALL disks
            targets = list(disks.keys())
            
        else:
            # RAID 0 or RAID 5: Distribute files with load balancing
            
            if raid == "RAID 5":
                # RAID 5: Exclude parity disk from data storage
                # Parity disk rotates: file 0 -> disk 0, file 1 -> disk 1, etc.
                parity_disk = idx % num
                # Candidates are all disks EXCEPT the parity disk for this file
                candidates = [d for d in range(num) if d != parity_disk]
            else:
                # RAID 0: All disks are candidates for data storage
                candidates = list(range(num))
            
            # Choose the disk with minimum current load (greedy load balancing)
            target = min(candidates, key=lambda x: disk_loads[x])
            targets = [target]

        # === COPY FILES TO TARGET DISKS ===
        
        for t in targets:
            # Copy file to the target disk directory
            # shutil.copy2 preserves metadata (timestamps, permissions)
            shutil.copy2(f, disks[t])
            
            # Update load tracking for this disk
            disk_loads[t] += size
            
        # === CREATE PARITY PLACEHOLDER FOR RAID 5 ===
        
        if raid == "RAID 5":
            # Calculate which disk holds parity for this file
            p_disk = idx % num
            
            # Create a text file indicating parity information
            # In real RAID 5, this would be XOR of data blocks
            parity_file = disks[p_disk] / f"{Path(f).stem}_PARITY.txt"
            parity_file.write_text(
                f"Parity for {Path(f).name}\n"
                f"Data on disk {targets[0]}"
            )

    # === CREATE ZIP ARCHIVE ===
    
    # Create a ZIP archive of all virtual disks for easy download
    # shutil.make_archive returns the full path to the created archive
    zip_path = shutil.make_archive(
        str(base.parent / base.name),  # Archive name (without extension)
        "zip",                          # Archive format
        base                            # Directory to archive
    )
    
    return str(base), zip_path

# ==============================================================================
# FUNCTION: run_simulation
# ==============================================================================

def run_simulation(num_disks, raid_level, progress=gr.Progress()):
    """
    Executes complete RAID simulation including performance and capacity analysis.
    
    This is the main simulation function that:
    1. Validates that files have been scanned
    2. Simulates read/write operations
    3. Calculates capacity and efficiency metrics
    4. Generates visualization charts
    5. Creates virtual disk structures
    6. Saves all reports to CSV files
    
    Parameters:
    -----------
    num_disks : int
        Number of disks in the RAID array (2-12)
    
    raid_level : str
        RAID level to simulate ("RAID 0", "RAID 1", or "RAID 5")
    
    progress : gr.Progress
        Gradio progress indicator (optional)
    
    Returns:
    --------
    tuple: (message, run_dataframe, stats_dataframe, pie_chart, bar_chart, download_files)
        - message: Markdown-formatted success/error message
        - run_dataframe: DataFrame with simulation run data
        - stats_dataframe: DataFrame with statistical summary
        - pie_chart: Matplotlib Figure object with capacity distribution
        - bar_chart: Matplotlib Figure object with performance time
        - download_files: List of file paths for download
    
    Workflow:
    ---------
    1. Validate input (check if folder was scanned)
    2. Run performance simulation (read/write times)
    3. Calculate capacity metrics (usable %, efficiency, etc.)
    4. Store results in DataFrame
    5. Generate statistical summary
    6. Create visualizations (pie chart, bar chart)
    7. Build virtual disk structure
    8. Save all outputs and return results
    """
    
    # === VALIDATION ===
    
    # Check if user has scanned a folder before running simulation
    if not last_scan["files"]:
        return "❌ Scan folder first.", *([None]*5)
    
    # === PERFORMANCE SIMULATION ===
    
    # Simulate read operation and get time in milliseconds
    r_ms = simulate_raid_read(raid_level)
    
    # Simulate write operation and get time in milliseconds
    w_ms = simulate_raid_write(raid_level)
    
    # === BUILD SIMULATION DATA DICTIONARY ===
    
    run_data = {
        # RAID configuration
        "raid_level": raid_level,
        "disk_count": num_disks,
        
        # File information
        "total_files": len(last_scan["files"]),
        "total_size_bytes": last_scan["total_bytes"],
        
        # Performance metrics (time in milliseconds)
        "read_time_ms": r_ms,
        "write_time_ms": w_ms,
        "total_time_ms": r_ms + w_ms,
        
        # Capacity metrics (percentages)
        "usable_%": usable_capacity_percent(num_disks, raid_level),
        "efficiency_%": space_efficiency(num_disks, raid_level) * 100
    }
    
    # === DATA ANALYSIS ===
    
    # Append this run to the results DataFrame
    # First run creates new DataFrame, subsequent runs append
    df = append_run(None, run_data)
    
    # Calculate statistical summary (mean, std, median, min, max, variance)
    stats_df = summary_statistics(df)
    
    # === FILE GENERATION SETUP ===
    
    # Generate timestamp for unique filenames
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define paths for all output files
    files = {
        "report": REPORTS_DIR / f"report_{ts}.csv",        # Main simulation data
        "stats": REPORTS_DIR / f"summary_{ts}.csv",        # Statistical summary
        "pie": REPORTS_DIR / f"pie_{ts}.png",              # Capacity pie chart
        "bar": REPORTS_DIR / f"bar_{ts}.png"               # Performance bar chart
    }
    
    # === SAVE CSV REPORTS ===
    
    # Save main simulation results to CSV
    save_report_csv(df, files["report"].name)
    
    # Save statistical summary to CSV
    save_report_csv(stats_df, files["stats"].name)
    
    # === GENERATE VISUALIZATIONS ===
    
    # --- PIE CHART: Capacity Distribution ---
    
    # Create new figure for pie chart
    fig1 = plt.figure(figsize=(5, 5))
    
    # Get capacity breakdown (usable, parity, mirror)
    bd = calculate_capacity_breakdown_dict(num_disks, raid_level)
    
    # Create pie chart showing how capacity is distributed
    plt.pie(
        [bd["usable"], bd["parity"], bd["mirror"]],  # Sizes of pie slices
        labels=["Usable", "Parity", "Mirror"],        # Labels for each slice
        autopct="%1.1f%%"                             # Show percentage with 1 decimal
    )
    plt.title("Capacity Distribution")
    
    # Save figure to file
    fig1.savefig(files["pie"])
    
    # --- BAR CHART: Total Performance Time ---
    
    # Create new figure for bar chart
    fig2 = plt.figure(figsize=(6, 4))
    
    # Create bar chart showing total operation time
    plt.bar(
        [raid_level],                        # X-axis: RAID level
        [run_data["total_time_ms"]]         # Y-axis: Total time
    )
    plt.ylabel("Time (ms)")
    plt.title("Total Performance Time")
    
    # Save figure to file
    fig2.savefig(files["bar"])

    # === BUILD VIRTUAL DISK STRUCTURE ===
    
    # Create virtual disk directories and ZIP archive
    v_folder, v_zip = build_virtual_disks(
        raid_level,
        num_disks,
        last_scan["files"],
        ts
    )
    
    # === PREPARE SUCCESS MESSAGE ===
    
    msg = f"""## ✅ Done: {raid_level}
Saved to `reports/`
Zip: `{os.path.basename(v_zip)}`"""
    
    # === RETURN ALL RESULTS ===
    
    # Return tuple with:
    # 1. Success message (Markdown)
    # 2. Main results DataFrame
    # 3. Statistics DataFrame
    # 4. Pie chart Figure object (Gradio will render it)
    # 5. Bar chart Figure object
    # 6. List of downloadable files (CSVs, PNGs, ZIP)
    return (
        msg,
        df,
        stats_df,
        fig1,  # Return Figure object, not file path
        fig2,  # Return Figure object, not file path
        [str(f) for f in files.values()] + [v_zip]
    )

# ==============================================================================
# GRADIO USER INTERFACE
# ==============================================================================

# Create Gradio Blocks interface (allows custom layout)
# Blocks is more flexible than Interface for complex multi-step workflows
with gr.Blocks(title="RAID Sim", theme=gr.themes.Soft()) as app:
    
    # === HEADER ===
    
    # Add styled header with HTML
    gr.HTML(
        "<h1 style='text-align:center; background:#667eea; color:white; "
        "padding:10px; border-radius:10px;'>💾 RAID Simulator</h1>"
    )
    
    # === STATE VARIABLE ===
    
    # Gradio State to persist data between interactions
    # Stores total size of scanned files in MB
    state_size = gr.State(0)
    
    # === TABS INTERFACE ===
    
    with gr.Tabs():
        
        # ======================================================================
        # TAB 1: LOAD - Scan Folder for Multimedia Files
        # ======================================================================
        
        with gr.Tab("1. Load"):
            
            # --- Input Row ---
            with gr.Row():
                # Text input for folder path
                inp = gr.Textbox(
                    label="Path",
                    placeholder="Enter folder path (e.g., C:\\Users\\...\\Media)"
                )
                
                # Button to trigger scan
                btn = gr.Button("Scan", variant="primary")
            
            # --- Output Components ---
            
            # Markdown output for scan summary
            out_md = gr.Markdown()
            
            # DataFrame output for file list (first 200 files)
            out_tbl = gr.DataFrame()
            
            # --- Connect Button to Function ---
            
            # When button is clicked:
            # - Call scan_folder with input path
            # - Update Markdown, DataFrame, and state_size with results
            btn.click(
                fn=scan_folder,                           # Function to call
                inputs=inp,                               # Input: folder path
                outputs=[out_md, out_tbl, state_size]    # Outputs: summary, table, size
            )
            
        # ======================================================================
        # TAB 2: CONFIG - Configure RAID Parameters
        # ======================================================================
        
        with gr.Tab("2. Config"):
            
            # --- RAID Configuration Inputs ---
            
            # Slider for number of disks (2-12)
            d_sld = gr.Slider(
                minimum=2,
                maximum=12,
                value=4,              # Default value
                step=1,
                label="Disks",
                info="Number of disks in RAID array"
            )
            
            # Radio buttons for RAID level selection
            r_rad = gr.Radio(
                choices=["RAID 0", "RAID 1", "RAID 5"],
                value="RAID 5",       # Default selection
                label="Level",
                info="Select RAID configuration"
            )
            
            # Button to calculate metrics preview
            c_btn = gr.Button("Calc Metrics")
            
            # Markdown output for metrics preview
            c_out = gr.Markdown()
            
            # --- Connect Button to Metrics Calculation ---
            
            # Lambda function to format usable capacity and efficiency
            c_btn.click(
                fn=lambda n, r, s: (
                    f"**Usable:** {usable_capacity_percent(n, r):.1f}% | "
                    f"**Eff:** {space_efficiency(n, r):.2%}"
                ),
                inputs=[d_sld, r_rad, state_size],
                outputs=c_out
            )

        # ======================================================================
        # TAB 3: RUN - Execute Simulation
        # ======================================================================
        
        with gr.Tab("3. Run"):
            
            # --- Simulation Button ---
            s_btn = gr.Button("🚀 Simulate", variant="primary")
            
            # --- Status Message ---
            s_out = gr.Markdown()
            
            # --- Visualization Charts Row ---
            with gr.Row():
                # Plot component for pie chart (capacity distribution)
                p1 = gr.Plot(label="Capacity Distribution")
                
                # Plot component for bar chart (performance)
                p2 = gr.Plot(label="Performance")
            
            # --- Data Tables Row ---
            with gr.Row():
                # DataFrame for simulation run data
                res_df = gr.DataFrame(label="Run Data")
                
                # DataFrame for statistical summary
                stats_tbl = gr.DataFrame(label="Summary Statistics")
            
            # --- Download Files Component ---
            dl = gr.File(
                label="Download Reports & Virtual Disks",
                file_count="multiple"  # Allow multiple file downloads
            )
            
            # --- Connect Button to Simulation Function ---
            
            # When simulate button is clicked:
            # - Call run_simulation with disk count and RAID level
            # - Update all output components with results
            s_btn.click(
                fn=run_simulation,
                inputs=[d_sld, r_rad],
                outputs=[s_out, res_df, stats_tbl, p1, p2, dl]
            )

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    """
    Application entry point.
    
    Launches the Gradio web interface with the following settings:
    - inbrowser=True: Automatically opens in default web browser
    - Server will run on localhost (default port 7860)
    - Access URL will be printed to console
    
    To run:
    -------
    python run.py
    
    Then navigate to the provided URL (typically http://localhost:7860)
    """
    app.launch(inbrowser=True)
