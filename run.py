#!/usr/bin/env python3
"""
================================================================================
run.py - RAID Multimedia Storage Performance Simulator - Main Application
================================================================================

Purpose:
    This is the main entry point for the RAID simulator application.
    It provides a Gradio-based web interface for:
    - Scanning folders for multimedia files (images and videos)
    - Configuring RAID arrays (RAID 0, 1, or 5)
    - Simulating RAID performance (read/write times)
    - Generating capacity distribution charts
    - Creating virtual disk structures
    - Exporting detailed performance reports

Authors: Team Project
Deadline: Monday
Last Updated: December 2024

Dependencies:
    - gradio: Web UI framework
    - pandas: Data manipulation and analysis
    - matplotlib: Chart generation
    - PIL (Pillow): Image processing
    - Custom modules: Data_Analysis, Raid_Calculation, Raid_Simulation

Usage:
    python run.py
    Then open the provided URL in your browser (usually http://localhost:7860)

================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library imports
import sys              # System-specific parameters and functions
import os               # Operating system interface for file operations
import shutil           # High-level file operations (copy, move, archive)
import random           # Random number generation (not currently used)
import time             # Time-related functions (not currently used)
from pathlib import Path        # Object-oriented filesystem paths
from datetime import datetime   # Date and time manipulation

# Third-party library imports
import gradio as gr             # Web UI framework for creating interactive interfaces
import pandas as pd             # Data manipulation and analysis library
import matplotlib.pyplot as plt # Plotting library for creating visualizations
from PIL import Image           # Python Imaging Library for image processing

# ============================================================================
# SETUP PATHS AND DIRECTORIES
# ============================================================================

# Get the directory where this script is located
APP_DIR = Path(__file__).parent

# Define the reports directory where all outputs will be saved
REPORTS_DIR = APP_DIR / "reports"

# Create the reports directory if it doesn't exist
# exist_ok=True prevents errors if directory already exists
REPORTS_DIR.mkdir(exist_ok=True)

# Add the Modules directory to Python's module search path
# This allows us to import our custom modules
sys.path.insert(0, str(APP_DIR / "Modules"))

# ============================================================================
# IMPORT CUSTOM MODULES
# ============================================================================

# Import data analysis functions
from Data_Analysis import (
    append_run,             # Adds a new simulation run to a DataFrame
    save_report_csv,        # Saves DataFrame to CSV file in reports folder
    summary_statistics      # Generates statistical summary of simulation runs
)

# Import RAID calculation functions
from Raid_Calculation import (
    usable_capacity_percent,            # Calculates usable storage percentage
    redundancy_percent,                 # Calculates redundancy overhead percentage
    space_efficiency,                   # Calculates space efficiency ratio
    calculate_capacity_breakdown_dict   # Returns capacity breakdown for visualization
)

# Import RAID simulation functions
from Raid_Simulation import (
    simulate_raid_read,     # Simulates RAID read operation and returns time
    simulate_raid_write     # Simulates RAID write operation and returns time
)

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Define supported file extensions for multimedia files
# This set contains both image and video formats
SUPPORTED_EXT = {
    # Image formats
    ".jpg", ".jpeg", ".png", ".bmp", ".gif",
    # Video formats
    ".mp4", ".mov", ".mkv", ".avi", ".webm"
}

# Global state dictionary to store the last folder scan results
# This avoids re-scanning the same folder multiple times
last_scan = {
    "folder": None,         # Path to the last scanned folder
    "files": [],            # List of file paths found
    "total_bytes": 0        # Total size of all files in bytes
}

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def scan_folder(folder_path, progress=gr.Progress()):
    """
    Scans a folder recursively for supported multimedia files.
    
    This function walks through all subdirectories, identifies media files
    by their extensions, extracts metadata (size, resolution for images),
    and stores the results in the global last_scan dictionary.
    
    Args:
        folder_path (str): Path to the folder to scan
        progress (gr.Progress): Gradio progress tracker (optional)
    
    Returns:
        tuple: (
            summary_markdown (str): Formatted summary of scan results,
            dataframe (pd.DataFrame): Table of file details (limited to 200 rows),
            total_size_mb (float): Total size of files in megabytes
        )
    
    Example:
        >>> scan_folder("/path/to/media")
        ("## 📊 Scan Results...", DataFrame(...), 150.5)
    """
    # Normalize the path by removing quotes and extra spaces
    # This handles cases where users paste paths with quotes
    folder_path = os.path.normpath(folder_path.strip('"').strip("'"))
    
    # Validate that the path exists and is a directory
    if not os.path.isdir(folder_path):
        return "❌ Invalid folder.", None, 0
    
    # Walk through the directory tree and collect supported media files
    files = [
        os.path.join(r, f)  # Join root path with filename
        for r, _, n in os.walk(folder_path)  # r=root, _=dirs (unused), n=files
        for f in n  # Iterate through each file in the directory
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT  # Check extension
    ]
    
    # Check if any media files were found
    if not files:
        return "❌ No media files found.", None, 0

    # Initialize variables for storing file information
    rows = []           # List to store file metadata dictionaries
    total_bytes = 0     # Counter for total size
    
    # Process each file and extract metadata
    for p in files:
        # Get file size in bytes
        size = os.path.getsize(p)
        total_bytes += size
        
        # Initialize resolution as "N/A" (for non-images)
        res = "N/A"
        
        # For image files, try to extract resolution
        if p.lower().endswith(tuple({".jpg", ".png", ".bmp", ".gif"})):
            try:
                # Open image and get dimensions
                with Image.open(p) as im:
                    res = f"{im.width}x{im.height}"
            except:
                # If image can't be opened, keep "N/A"
                pass
        
        # Add file information to rows list
        rows.append({
            "Filename": os.path.basename(p),        # Just the filename
            "Extension": os.path.splitext(p)[1],    # File extension
            "Size (KB)": round(size/1024, 2),       # Size in KB, rounded
            "Resolution": res                        # Resolution or "N/A"
        })

    # Update global state with scan results
    last_scan.update({
        "folder": folder_path,
        "files": files,
        "total_bytes": total_bytes
    })
    
    # Create summary statistics
    # Count occurrences of each file extension
    ext_counts = pd.DataFrame(rows)["Extension"].value_counts().to_string()
    
    # Format summary as Markdown
    summary = f"""## 📊 Scan Results
- **Files:** {len(files)}
- **Size:** {total_bytes/1024**2:.2f} MB

### Types:
{ext_counts}"""
    
    # Return summary, DataFrame (limited to first 200 rows), and size in MB
    return summary, pd.DataFrame(rows[:200]), total_bytes/1024**2


def build_virtual_disks(raid, num, files, ts):
    """
    Creates a virtual disk structure simulating RAID configuration.
    
    This function creates separate folders for each disk in the RAID array
    and distributes files according to RAID level logic:
    - RAID 0: Files striped across disks (load balanced)
    - RAID 1: Files mirrored to all disks
    - RAID 5: Files striped with parity information
    
    Args:
        raid (str): RAID level ("RAID 0", "RAID 1", or "RAID 5")
        num (int): Number of disks in the array
        files (list): List of file paths to distribute
        ts (str): Timestamp string for unique folder naming
    
    Returns:
        tuple: (
            disk_folder_path (str): Path to the disk folders,
            zip_file_path (str): Path to the created zip archive
        )
    
    Example:
        >>> build_virtual_disks("RAID 5", 4, file_list, "20241219_120530")
        ("/path/to/virtual_disks_20241219_120530/RAID_5", "/path/to/RAID_5.zip")
    """
    # Create base directory structure
    # Format: reports/virtual_disks_{timestamp}/RAID_X/disk_0, disk_1, ...
    base = REPORTS_DIR / f"virtual_disks_{ts}" / raid.replace(" ", "_")
    
    # Create a dictionary mapping disk number to its folder path
    disks = {i: base / f"disk_{i}" for i in range(num)}
    
    # Create all disk folders
    for d in disks.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # Track how much data is on each disk (for load balancing)
    disk_loads = {i: 0 for i in range(num)}
    
    # Distribute files to disks based on RAID level
    for idx, f in enumerate(files):
        # Get file size for load tracking
        size = os.path.getsize(f)
        
        # ==========================================
        # RAID-SPECIFIC FILE DISTRIBUTION LOGIC
        # ==========================================
        
        if raid == "RAID 1":
            # RAID 1: Mirror to ALL disks
            # Every file is copied to every disk for redundancy
            targets = list(disks.keys())
            
        else:
            # RAID 0 and RAID 5: Stripe data across disks
            
            if raid == "RAID 5":
                # RAID 5: Parity disk rotates (round-robin)
                # Parity for file i goes to disk (i % num_disks)
                # Data goes to other disks (excluding parity disk)
                candidates = [d for d in range(num) if d != (idx % num)]
            else:
                # RAID 0: All disks are candidates for data
                candidates = list(range(num))
            
            # Choose disk with minimum load for better balance
            target = min(candidates, key=lambda x: disk_loads[x])
            targets = [target]

        # ==========================================
        # COPY FILES TO TARGET DISKS
        # ==========================================
        
        # Copy file to all target disks
        for t in targets:
            shutil.copy2(f, disks[t])  # copy2 preserves metadata
            disk_loads[t] += size      # Update disk load
            
        # ==========================================
        # RAID 5: CREATE PARITY FILES
        # ==========================================
        
        if raid == "RAID 5":
            # Calculate which disk stores parity for this file
            p_disk = idx % num
            
            # Create a text file representing parity information
            parity_file = disks[p_disk] / f"{Path(f).stem}_PARITY.txt"
            parity_file.write_text(
                f"Parity for {Path(f).name}\nData on disk {targets[0]}"
            )

    # ==========================================
    # CREATE ZIP ARCHIVE
    # ==========================================
    
    # Create a zip file of all virtual disks for easy download
    zip_path = shutil.make_archive(
        str(base.parent / base.name),  # Archive name (without extension)
        "zip",                          # Archive format
        base                            # Directory to archive
    )
    
    return str(base), zip_path


def run_simulation(num_disks, raid_level, progress=gr.Progress()):
    """
    Runs a complete RAID simulation with performance testing and reporting.
    
    This is the main simulation function that:
    1. Validates that files have been scanned
    2. Simulates read/write operations
    3. Calculates capacity and efficiency metrics
    4. Generates visualization charts
    5. Creates virtual disk structures
    6. Saves detailed reports to CSV
    
    Args:
        num_disks (int): Number of disks in the RAID array (2-12)
        raid_level (str): RAID configuration ("RAID 0", "RAID 1", or "RAID 5")
        progress (gr.Progress): Gradio progress tracker (optional)
    
    Returns:
        tuple: (
            message (str): Markdown-formatted success message,
            results_df (pd.DataFrame): Detailed run data,
            stats_df (pd.DataFrame): Statistical summary,
            pie_figure (matplotlib.figure.Figure): Capacity distribution pie chart,
            bar_figure (matplotlib.figure.Figure): Performance bar chart,
            download_files (list): List of file paths for download
        )
    
    Example:
        >>> run_simulation(4, "RAID 5")
        ("## ✅ Done: RAID 5...", DataFrame(...), DataFrame(...), Figure, Figure, [...])
    """
    # ==========================================
    # VALIDATION
    # ==========================================
    
    # Check if user has scanned a folder first
    if not last_scan["files"]:
        return "❌ Scan folder first.", *([None]*5)
    
    # ==========================================
    # SIMULATE RAID OPERATIONS
    # ==========================================
    
    # Simulate read operation and get time in milliseconds
    r_ms = simulate_raid_read(raid_level)
    
    # Simulate write operation and get time in milliseconds
    w_ms = simulate_raid_write(raid_level)
    
    # ==========================================
    # COLLECT SIMULATION DATA
    # ==========================================
    
    # Create a dictionary with all simulation metrics
    run_data = {
        "raid_level": raid_level,                    # RAID configuration
        "disk_count": num_disks,                     # Number of disks
        "total_files": len(last_scan["files"]),      # Files processed
        "total_size_bytes": last_scan["total_bytes"], # Total data size
        "read_time_ms": r_ms,                        # Read time
        "write_time_ms": w_ms,                       # Write time
        "total_time_ms": r_ms + w_ms,                # Combined time
        "usable_%": usable_capacity_percent(num_disks, raid_level),  # Usable capacity %
        "efficiency_%": space_efficiency(num_disks, raid_level) * 100 # Efficiency %
    }
    
    # Add this run to a DataFrame (starts with None, creates new DataFrame)
    df = append_run(None, run_data)
    
    # Generate statistical summary (mean, std, median, min, max, variance)
    stats_df = summary_statistics(df)
    
    # ==========================================
    # GENERATE TIMESTAMP FOR FILES
    # ==========================================
    
    # Create unique timestamp for this simulation run
    # Format: YYYYMMDD_HHMMSS (e.g., 20241219_153045)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ==========================================
    # DEFINE OUTPUT FILE PATHS
    # ==========================================
    
    # Dictionary storing all output file paths
    files = {
        "report": REPORTS_DIR / f"report_{ts}.csv",      # Detailed run data
        "stats": REPORTS_DIR / f"summary_{ts}.csv",      # Statistical summary
        "pie": REPORTS_DIR / f"pie_{ts}.png",            # Pie chart image
        "bar": REPORTS_DIR / f"bar_{ts}.png"             # Bar chart image
    }
    
    # ==========================================
    # SAVE CSV REPORTS
    # ==========================================
    
    # Save detailed simulation data to CSV
    save_report_csv(df, files["report"].name)
    
    # Save statistical summary to CSV
    save_report_csv(stats_df, files["stats"].name)
    
    # ==========================================
    # CREATE PIE CHART (CAPACITY DISTRIBUTION)
    # ==========================================
    
    # Create new figure with 5x5 inch size
    fig1 = plt.figure(figsize=(5,5))
    
    # Get capacity breakdown (usable, parity, mirror)
    bd = calculate_capacity_breakdown_dict(num_disks, raid_level)
    
    # Create pie chart showing capacity distribution
    plt.pie(
        [bd["usable"], bd["parity"], bd["mirror"]],  # Values
        labels=["Usable", "Parity", "Mirror"],        # Labels
        autopct="%1.1f%%"                              # Show percentages
    )
    plt.title("Capacity Distribution")  # Chart title
    
    # Save figure to file
    fig1.savefig(files["pie"])
    
    # ==========================================
    # CREATE BAR CHART (PERFORMANCE)
    # ==========================================
    
    # Create new figure with 6x4 inch size
    fig2 = plt.figure(figsize=(6,4))
    
    # Create bar chart showing total operation time
    plt.bar([raid_level], [run_data["total_time_ms"]])
    plt.ylabel("Time (ms)")                 # Y-axis label
    plt.title("Total Performance Time")     # Chart title
    
    # Save figure to file
    fig2.savefig(files["bar"])

    # ==========================================
    # BUILD VIRTUAL DISK STRUCTURE
    # ==========================================
    
    # Create virtual disks and get folder path and zip file path
    v_folder, v_zip = build_virtual_disks(
        raid_level,             # RAID level
        num_disks,              # Number of disks
        last_scan["files"],     # Files to distribute
        ts                      # Timestamp for folder naming
    )
    
    # ==========================================
    # FORMAT SUCCESS MESSAGE
    # ==========================================
    
    # Create Markdown-formatted success message
    msg = f"""## ✅ Done: {raid_level}
Saved to `reports/`
Zip: `{os.path.basename(v_zip)}`"""
    
    # ==========================================
    # RETURN ALL RESULTS
    # ==========================================
    
    # Return matplotlib Figure objects (not file paths) for Gradio plotting
    # Also return list of all generated files for download
    return (
        msg,                                              # Success message
        df,                                               # Results DataFrame
        stats_df,                                         # Statistics DataFrame
        fig1,                                             # Pie chart figure
        fig2,                                             # Bar chart figure
        [str(f) for f in files.values()] + [v_zip]       # All file paths
    )

# ============================================================================
# GRADIO USER INTERFACE
# ============================================================================

# Create Gradio Blocks interface (allows custom layout)
with gr.Blocks(title="RAID Sim", theme=gr.themes.Soft()) as app:
    
    # ==========================================
    # HEADER
    # ==========================================
    
    # HTML header with custom styling
    gr.HTML(
        "<h1 style='text-align:center; background:#667eea; color:white; "
        "padding:10px; border-radius:10px;'>💾 RAID Simulator</h1>"
    )
    
    # ==========================================
    # STATE VARIABLES
    # ==========================================
    
    # Gradio State to store total size (persists between interactions)
    state_size = gr.State(0)
    
    # ==========================================
    # TAB 1: LOAD DATA
    # ==========================================
    
    with gr.Tabs():
        with gr.Tab("1. Load"):
            # Row for input and button
            with gr.Row():
                # Text input for folder path
                inp = gr.Textbox(label="Path")
                
                # Scan button (primary style = blue/prominent)
                btn = gr.Button("Scan", variant="primary")
            
            # Output area for scan results
            out_md = gr.Markdown()      # Markdown-formatted summary
            out_tbl = gr.DataFrame()    # Table of files
            
            # Connect button click to scan_folder function
            # Inputs: folder path from textbox
            # Outputs: markdown summary, dataframe, size (stored in state)
            btn.click(scan_folder, inp, [out_md, out_tbl, state_size])
        
        # ==========================================
        # TAB 2: CONFIGURE RAID
        # ==========================================
        
        with gr.Tab("2. Config"):
            # Slider for selecting number of disks (2-12)
            d_sld = gr.Slider(
                minimum=2,
                maximum=12,
                value=4,              # Default value
                step=1,               # Integer steps
                label="Disks"
            )
            
            # Radio buttons for RAID level selection
            r_rad = gr.Radio(
                ["RAID 0", "RAID 1", "RAID 5"],
                value="RAID 5",       # Default selection
                label="Level"
            )
            
            # Button to calculate metrics
            c_btn = gr.Button("Calc Metrics")
            
            # Output area for calculated metrics
            c_out = gr.Markdown()
            
            # Connect button to lambda function that calculates metrics
            # Lambda creates formatted string with usable capacity and efficiency
            c_btn.click(
                lambda n,r,s: f"**Usable:** {usable_capacity_percent(n,r):.1f}% | "
                              f"**Eff:** {space_efficiency(n,r):.2%}",
                [d_sld, r_rad, state_size],  # Inputs
                c_out                          # Output
            )

        # ==========================================
        # TAB 3: RUN SIMULATION
        # ==========================================
        
        with gr.Tab("3. Run"):
            # Simulate button (primary style)
            s_btn = gr.Button("🚀 Simulate", variant="primary")
            
            # Output message
            s_out = gr.Markdown()
            
            # Row for charts (side by side)
            with gr.Row():
                p1 = gr.Plot(label="Capacity Distribution")  # Pie chart
                p2 = gr.Plot(label="Performance")            # Bar chart
            
            # Row for data tables (side by side)
            with gr.Row():
                res_df = gr.DataFrame(label="Run Data")              # Detailed data
                stats_tbl = gr.DataFrame(label="Summary Statistics") # Stats summary
            
            # File download component (allows multiple files)
            dl = gr.File(
                label="Download Reports & Virtual Disks",
                file_count="multiple"
            )
            
            # Connect simulate button to run_simulation function
            # Inputs: number of disks, RAID level
            # Outputs: message, dataframes, plots, download files
            s_btn.click(
                run_simulation,
                [d_sld, r_rad],                            # Inputs
                [s_out, res_df, stats_tbl, p1, p2, dl]    # Outputs
            )

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Main entry point when script is run directly.
    
    Launches the Gradio web interface with:
    - inbrowser=True: Automatically opens browser window
    - Default port: 7860
    - Access via: http://localhost:7860
    """
    app.launch(inbrowser=True)
