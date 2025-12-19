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

Author: Information Storage Project Team
Date: 2025
"""

# ============================================================================
# SECTION 1: IMPORT STATEMENTS
# ============================================================================

# Standard library imports for system operations
import sys          # System-specific parameters and functions
import os           # Operating system interface for file/directory operations
import shutil       # High-level file operations (copy, move, archive)
import random       # Random number generation (unused in current version)
import time         # Time-related functions (unused in current version)

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
# __file__ is the path to the current Python file
# .parent gets the parent directory of the file
APP_DIR = Path(__file__).parent

# Define the reports directory where all output files will be saved
# Uses the / operator for path joining (pathlib feature)
REPORTS_DIR = APP_DIR / "reports"

# Create the reports directory if it doesn't exist
# exist_ok=True prevents errors if directory already exists
REPORTS_DIR.mkdir(exist_ok=True)

# Add the Modules directory to Python's module search path
# This allows importing custom modules from the Modules folder
# str() converts Path object to string for sys.path
# insert(0, ...) adds to beginning of path list for priority
sys.path.insert(0, str(APP_DIR / "Modules"))


# ============================================================================
# SECTION 3: IMPORT CUSTOM MODULES
# ============================================================================

# Import data analysis functions for storing and analyzing simulation results
from Data_Analysis import (
    append_run,              # Adds a new simulation run to DataFrame
    save_report_csv,         # Saves DataFrame to CSV file in reports folder
    summary_statistics       # Calculates statistical metrics (mean, std, etc.)
)

# Import RAID calculation functions for capacity and efficiency metrics
from Raid_Calculation import (
    usable_capacity_percent,           # Calculates usable storage percentage
    redundancy_percent,                # Calculates redundancy overhead percentage
    space_efficiency,                  # Calculates efficiency ratio (0.0-1.0)
    calculate_capacity_breakdown_dict  # Returns breakdown of usable/parity/mirror
)

# Import RAID simulation functions for performance testing
from Raid_Simulation import (
    simulate_raid_read,      # Simulates read operation time in milliseconds
    simulate_raid_write      # Simulates write operation time in milliseconds
)


# ============================================================================
# SECTION 4: GLOBAL CONSTANTS AND STATE
# ============================================================================

# Define supported multimedia file extensions
# Using a set for O(1) lookup performance
SUPPORTED_EXT = {
    # Image formats
    ".jpg", ".jpeg", ".png", ".bmp", ".gif",
    # Video formats
    ".mp4", ".mov", ".mkv", ".avi", ".webm"
}

# Global state dictionary to store the last folder scan results
# This persists data between function calls in the Gradio interface
last_scan = {
    "folder": None,        # Path to the scanned folder
    "files": [],          # List of file paths found
    "total_bytes": 0      # Total size of all files in bytes
}


# ============================================================================
# SECTION 5: FOLDER SCANNING FUNCTION
# ============================================================================

def scan_folder(folder_path, progress=gr.Progress()):
    """
    Scans a folder recursively for multimedia files and collects metadata.
    
    This function walks through the entire directory tree, identifies supported
    media files, extracts their metadata (size, resolution for images), and
    returns a summary with a detailed file listing.
    
    Parameters
    ----------
    folder_path : str
        Path to the folder to scan. Can include quotes which will be stripped.
    progress : gr.Progress
        Gradio progress indicator (unused but required for UI integration).
    
    Returns
    -------
    tuple : (summary_markdown, dataframe, total_size_mb)
        summary_markdown : str
            Markdown-formatted summary with file count, total size, and type breakdown
        dataframe : pd.DataFrame or None
            DataFrame containing up to 200 files with their metadata
        total_size_mb : float
            Total size of all files in megabytes
    
    Examples
    --------
    >>> summary, df, size = scan_folder("/path/to/media")
    >>> print(summary)
    ## 📊 Scan Results
    - **Files:** 150
    - **Size:** 2500.50 MB
    """
    
    # Normalize the path and remove surrounding quotes
    # os.path.normpath converts path to OS-appropriate format (/ or \)
    # .strip() removes leading/trailing whitespace and quote characters
    folder_path = os.path.normpath(folder_path.strip('"').strip("'"))
    
    # Validate that the path is a directory
    # Return error message if path is invalid or doesn't exist
    if not os.path.isdir(folder_path):
        return "❌ Invalid folder.", None, 0
    
    # Walk through directory tree and collect all supported media files
    # List comprehension iterates through all files in all subdirectories
    # os.walk(folder_path) yields (root_dir, subdirs, files) for each directory
    # r = root directory path, _ = subdirectories (unused), n = files list
    # f = individual filename, os.path.splitext splits filename into name and extension
    # Filter: only include files whose extension is in SUPPORTED_EXT set
    files = [
        os.path.join(r, f)                              # Create full file path
        for r, _, n in os.walk(folder_path)            # Walk directory tree
        for f in n                                      # Iterate through files
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT  # Check extension
    ]
    
    # Check if any files were found
    # Return error message if no media files exist
    if not files:
        return "❌ No media files found.", None, 0

    # Initialize empty lists and counters for file metadata
    rows = []              # List to store file information dictionaries
    total_bytes = 0        # Accumulator for total file size
    
    # Iterate through each found file to extract metadata
    for p in files:
        # Get file size in bytes using os.path.getsize
        size = os.path.getsize(p)
        
        # Add to running total of all file sizes
        total_bytes += size
        
        # Initialize resolution as "N/A" (not applicable for videos)
        res = "N/A"
        
        # Check if file is an image format to extract resolution
        # Convert path to lowercase for case-insensitive comparison
        if p.lower().endswith(tuple({".jpg", ".png", ".bmp", ".gif"})):
            try:
                # Open image using PIL and extract dimensions
                # Using context manager (with) ensures file is properly closed
                with Image.open(p) as im:
                    # Format resolution as "WIDTHxHEIGHT"
                    res = f"{im.width}x{im.height}"
            except:
                # If image is corrupted or unreadable, keep res as "N/A"
                # Silent failure to prevent scan from stopping
                pass
        
        # Create dictionary with file metadata and append to rows list
        rows.append({
            "Filename": os.path.basename(p),              # Extract filename without path
            "Extension": os.path.splitext(p)[1],          # Extract file extension
            "Size (KB)": round(size/1024, 2),            # Convert bytes to KB, round to 2 decimals
            "Resolution": res                             # Image resolution or "N/A"
        })

    # Update global state with scan results for use by other functions
    # This allows run_simulation to access the scanned files
    last_scan.update({
        "folder": folder_path,    # Store original folder path
        "files": files,           # Store list of file paths
        "total_bytes": total_bytes # Store total size in bytes
    })
    
    # ========================================================================
    # Generate Summary Statistics
    # ========================================================================
    
    # Create DataFrame from rows and count files by extension
    # .value_counts() returns Series with extension frequencies
    # .to_string() converts to human-readable string format
    ext_counts = pd.DataFrame(rows)["Extension"].value_counts().to_string()
    
    # Format summary as Markdown with file count, total size, and type breakdown
    # Uses f-string for variable interpolation
    # total_bytes/1024**2 converts bytes to megabytes (divide by 1,048,576)
    summary = f"## 📊 Scan Results\n- **Files:** {len(files)}\n- **Size:** {total_bytes/1024**2:.2f} MB\n\n### Types:\n{ext_counts}"
    
    # Return tuple of summary text, DataFrame (limited to first 200 rows), and size in MB
    # Limiting to 200 rows prevents UI slowdown with large datasets
    return summary, pd.DataFrame(rows[:200]), total_bytes/1024**2


# ============================================================================
# SECTION 6: VIRTUAL DISK BUILDER FUNCTION
# ============================================================================

def build_virtual_disks(raid, num, files, ts):
    """
    Creates virtual disk structure simulating RAID data distribution.
    
    This function simulates how files would be distributed across physical disks
    in a RAID array. It creates separate folders for each disk and copies files
    according to RAID level rules:
    - RAID 0: Stripes data across disks (load balancing)
    - RAID 1: Mirrors data to all disks (full redundancy)
    - RAID 5: Stripes data with distributed parity
    
    Parameters
    ----------
    raid : str
        RAID level as string ("RAID 0", "RAID 1", or "RAID 5")
    num : int
        Number of disks in the array
    files : list
        List of file paths to distribute
    ts : str
        Timestamp string for unique folder naming (format: YYYYMMDD_HHMMSS)
    
    Returns
    -------
    tuple : (virtual_disks_folder, zip_archive_path)
        virtual_disks_folder : str
            Path to the folder containing all virtual disk folders
        zip_archive_path : str
            Path to the ZIP archive of the virtual disks
    
    Notes
    -----
    - RAID 1 copies each file to ALL disks (mirroring)
    - RAID 0/5 use load balancing to distribute files evenly
    - RAID 5 creates parity placeholder files using modulo distribution
    - All operations create actual file copies (not symbolic links)
    
    Examples
    --------
    >>> folder, zip_path = build_virtual_disks("RAID 5", 4, file_list, "20241219_153000")
    >>> print(f"Virtual disks saved to: {folder}")
    >>> print(f"Archive available at: {zip_path}")
    """
    
    # ========================================================================
    # Setup Directory Structure
    # ========================================================================
    
    # Create base path for virtual disks with RAID level and timestamp
    # Replace spaces in RAID level string with underscores for filesystem compatibility
    # Example: reports/virtual_disks_20241219_153000/RAID_5/
    base = REPORTS_DIR / f"virtual_disks_{ts}" / raid.replace(" ", "_")
    
    # Create dictionary mapping disk index to its folder path
    # Keys: 0, 1, 2, ..., num-1
    # Values: Path objects pointing to disk_0, disk_1, disk_2, etc.
    disks = {i: base / f"disk_{i}" for i in range(num)}
    
    # Create all disk directories (including parent directories)
    # parents=True creates intermediate directories if needed
    # exist_ok=True prevents errors if directories already exist
    for d in disks.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # Initialize load tracking dictionary to balance file distribution
    # Stores cumulative bytes written to each disk for load balancing
    # Keys: disk index (0, 1, 2, ...)
    # Values: total bytes stored on that disk
    disk_loads = {i: 0 for i in range(num)}
    
    # ========================================================================
    # Distribute Files Across Disks
    # ========================================================================
    
    # Iterate through all files with index for parity calculation
    # idx is used for RAID 5 parity disk selection (round-robin)
    for idx, f in enumerate(files):
        # Get file size in bytes for load balancing
        size = os.path.getsize(f)
        
        # ====================================================================
        # Determine Target Disk(s) Based on RAID Level
        # ====================================================================
        
        if raid == "RAID 1":
            # RAID 1 (Mirroring): Copy to ALL disks for redundancy
            # Every file exists on every disk
            targets = list(disks.keys())  # [0, 1, 2, ..., num-1]
        else:
            # RAID 0 and RAID 5: Use load balancing with striping
            
            # For RAID 5, exclude the parity disk from data candidates
            # Parity disk rotates using modulo: file 0→disk 0, file 1→disk 1, etc.
            # For RAID 0, all disks are candidates (condition always false)
            candidates = [
                d for d in range(num)                        # All disk indices
                if (raid != "RAID 5" or d != (idx % num))   # Exclude parity disk for RAID 5
            ]
            
            # Select disk with minimum current load for balancing
            # min() with key function finds disk with smallest disk_loads value
            # This ensures even distribution of data across disks
            target = min(candidates, key=lambda x: disk_loads[x])
            
            # Wrap single target in list for consistent handling
            targets = [target]

        # ====================================================================
        # Copy File(s) to Target Disk(s)
        # ====================================================================
        
        # Copy file to each target disk
        for t in targets:
            # shutil.copy2 copies file with metadata (timestamps, permissions)
            # Destination: disks[t] is the Path object for disk folder
            shutil.copy2(f, disks[t])
            
            # Update load tracker for this disk
            # Add file size to cumulative bytes for load balancing
            disk_loads[t] += size
        
        # ====================================================================
        # Create RAID 5 Parity Placeholder
        # ====================================================================
        
        if raid == "RAID 5":
            # Calculate which disk holds parity for this file
            # Uses modulo to rotate parity across disks
            # File 0→disk 0, file 1→disk 1, ..., file n→disk (n % num_disks)
            p_disk = idx % num
            
            # Create parity placeholder text file on the parity disk
            # Filename: original_filename_PARITY.txt
            # Path(f).stem extracts filename without extension
            # Content: Indicates which file and which disk has the data
            (disks[p_disk] / f"{Path(f).stem}_PARITY.txt").write_text(
                f"Parity for {Path(f).name}\nData on disk {targets[0]}"
            )

    # ========================================================================
    # Create ZIP Archive
    # ========================================================================
    
    # Create ZIP archive of all virtual disks for easy download
    # shutil.make_archive creates archive from directory
    # Format: reports/virtual_disks_20241219_153000/RAID_5.zip
    # Arguments: (archive_name_without_extension, format, directory_to_archive)
    zip_path = shutil.make_archive(
        str(base.parent / base.name),  # Output path: parent/folder_name
        "zip",                          # Archive format
        base                            # Directory to compress
    )
    
    # Return both the folder path and zip path
    # Convert Path objects to strings for Gradio compatibility
    return str(base), zip_path


# ============================================================================
# SECTION 7: MAIN SIMULATION RUNNER FUNCTION
# ============================================================================

def run_simulation(num_disks, raid_level, progress=gr.Progress()):
    """
    Executes complete RAID simulation including performance tests and visualizations.
    
    This is the main orchestration function that:
    1. Validates that files have been scanned
    2. Runs read/write performance simulations
    3. Calculates capacity and efficiency metrics
    4. Generates CSV reports with run data and statistics
    5. Creates visualization charts (pie and bar charts)
    6. Builds virtual disk structure
    7. Returns all results for display in UI
    
    Parameters
    ----------
    num_disks : int
        Number of disks in the RAID array (2-12)
    raid_level : str
        RAID configuration ("RAID 0", "RAID 1", or "RAID 5")
    progress : gr.Progress
        Gradio progress indicator for UI updates
    
    Returns
    -------
    tuple : (message, run_df, stats_df, pie_chart, bar_chart, download_files)
        message : str
            Markdown-formatted success message with save location
        run_df : pd.DataFrame
            DataFrame containing single row with all simulation metrics
        stats_df : pd.DataFrame
            DataFrame with statistical summary (mean, std, median, etc.)
        pie_chart : matplotlib.figure.Figure
            Pie chart showing capacity distribution (usable/parity/mirror)
        bar_chart : matplotlib.figure.Figure
            Bar chart showing total performance time
        download_files : list of str
            Paths to all generated files (CSVs, PNGs, ZIP) for download
    
    Raises
    ------
    Returns error tuple if no files have been scanned yet
    
    Notes
    -----
    - Requires scan_folder() to be called first to populate last_scan
    - All files are timestamped to prevent overwriting previous results
    - Charts are returned as Figure objects for direct display in Gradio
    - Virtual disks simulate actual RAID data distribution patterns
    
    Examples
    --------
    >>> msg, df, stats, fig1, fig2, files = run_simulation(4, "RAID 5")
    >>> print(msg)
    ## ✅ Done: RAID 5
    Saved to `reports/`
    Zip: `virtual_disks_20241219_153000.zip`
    """
    
    # ========================================================================
    # Validate Pre-Scan Requirement
    # ========================================================================
    
    # Check if files have been scanned (last_scan populated)
    # If no files exist, return error message and None values for all outputs
    # *([None]*5) creates tuple of 5 None values unpacked with *
    if not last_scan["files"]:
        return "❌ Scan folder first.", *([None]*5)
    
    # ========================================================================
    # Run Performance Simulations
    # ========================================================================
    
    # Simulate read operation and get time in milliseconds
    # simulate_raid_read returns float representing read time
    r_ms = simulate_raid_read(raid_level)
    
    # Simulate write operation and get time in milliseconds
    # simulate_raid_write returns float representing write time
    w_ms = simulate_raid_write(raid_level)
    
    # ========================================================================
    # Collect All Simulation Metrics
    # ========================================================================
    
    # Create dictionary containing all metrics for this simulation run
    run_data = {
        # RAID configuration parameters
        "raid_level": raid_level,                          # RAID type string
        "disk_count": num_disks,                           # Number of disks
        
        # File statistics from last scan
        "total_files": len(last_scan["files"]),           # Count of media files
        "total_size_bytes": last_scan["total_bytes"],     # Total size in bytes
        
        # Performance metrics from simulation
        "read_time_ms": r_ms,                             # Read time in milliseconds
        "write_time_ms": w_ms,                            # Write time in milliseconds
        "total_time_ms": r_ms + w_ms,                     # Combined read+write time
        
        # Capacity metrics from RAID calculations
        "usable_%": usable_capacity_percent(num_disks, raid_level),  # Usable capacity percentage
        "efficiency_%": space_efficiency(num_disks, raid_level) * 100  # Efficiency ratio as percentage
    }
    
    # Create DataFrame from single run (None creates new DataFrame)
    # append_run handles adding row to existing or creating new DataFrame
    df = append_run(None, run_data)
    
    # Calculate statistical summary of the run data
    # Returns DataFrame with mean, std, median, min, max, variance
    stats_df = summary_statistics(df)
    
    # ========================================================================
    # Generate Timestamp and File Paths
    # ========================================================================
    
    # Create timestamp string for unique file naming
    # Format: YYYYMMDD_HHMMSS (e.g., 20241219_153045)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define dictionary of all output file paths with timestamp
    files = {
        "report": REPORTS_DIR / f"report_{ts}.csv",     # Main simulation data
        "stats": REPORTS_DIR / f"summary_{ts}.csv",     # Statistical summary
        "pie": REPORTS_DIR / f"pie_{ts}.png",           # Capacity pie chart
        "bar": REPORTS_DIR / f"bar_{ts}.png"            # Performance bar chart
    }
    
    # ========================================================================
    # Save CSV Reports
    # ========================================================================
    
    # Save main simulation data to CSV
    # files["report"].name extracts just the filename (not full path)
    save_report_csv(df, files["report"].name)
    
    # Save statistical summary to CSV
    save_report_csv(stats_df, files["stats"].name)
    
    # ========================================================================
    # Create Capacity Distribution Pie Chart
    # ========================================================================
    
    # Create new matplotlib figure with 5x5 inch size
    # Returns Figure object (not displayed yet)
    fig1 = plt.figure(figsize=(5,5))
    
    # Get capacity breakdown dictionary (usable, parity, mirror disk counts)
    # Returns dict like: {"usable": 3, "parity": 1, "mirror": 0}
    bd = calculate_capacity_breakdown_dict(num_disks, raid_level)
    
    # Create pie chart showing capacity distribution
    # First arg: data values as list [usable_count, parity_count, mirror_count]
    # labels: text labels for each slice
    # autopct: format string for percentage labels (1 decimal place)
    plt.pie(
        [bd["usable"], bd["parity"], bd["mirror"]],  # Slice sizes
        labels=["Usable", "Parity", "Mirror"],        # Slice labels
        autopct="%1.1f%%"                              # Percentage format
    )
    
    # Add title to the chart
    plt.title("Capacity Distribution")
    
    # Save figure to PNG file
    # files["pie"] is Path object pointing to output file
    fig1.savefig(files["pie"])
    
    # ========================================================================
    # Create Performance Bar Chart
    # ========================================================================
    
    # Create new matplotlib figure with 6x4 inch size
    fig2 = plt.figure(figsize=(6,4))
    
    # Create bar chart with single bar showing total time
    # X-axis: RAID level name
    # Y-axis: Total time in milliseconds
    plt.bar(
        [raid_level],                      # X-axis category (single bar)
        [run_data["total_time_ms"]]       # Y-axis value (height)
    )
    
    # Set Y-axis label
    plt.ylabel("Time (ms)")
    
    # Add title to the chart
    plt.title("Total Performance Time")
    
    # Save figure to PNG file
    fig2.savefig(files["bar"])

    # ========================================================================
    # Build Virtual Disk Structure
    # ========================================================================
    
    # Create virtual disk folders and ZIP archive
    # v_folder: path to virtual_disks folder
    # v_zip: path to ZIP archive file
    v_folder, v_zip = build_virtual_disks(
        raid_level,              # RAID level string
        num_disks,               # Number of disks
        last_scan["files"],      # List of file paths to distribute
        ts                       # Timestamp for unique naming
    )
    
    # ========================================================================
    # Format Success Message
    # ========================================================================
    
    # Create Markdown-formatted success message
    # Shows RAID level, save location, and ZIP filename
    # os.path.basename extracts just filename from full path
    msg = f"## ✅ Done: {raid_level}\nSaved to `reports/`\nZip: `{os.path.basename(v_zip)}`"
    
    # ========================================================================
    # Return All Results
    # ========================================================================
    
    # Return tuple with all outputs for Gradio display
    # Note: Returning matplotlib Figure objects (fig1, fig2), NOT file paths
    # This allows Gradio to display charts directly in the interface
    return (
        msg,                                              # Success message (Markdown)
        df,                                               # Run data (DataFrame)
        stats_df,                                         # Statistics (DataFrame)
        fig1,                                             # Pie chart (Figure)
        fig2,                                             # Bar chart (Figure)
        [str(f) for f in files.values()] + [v_zip]       # All file paths for download
    )


# ============================================================================
# SECTION 8: GRADIO USER INTERFACE DEFINITION
# ============================================================================

# Create Gradio Blocks app (advanced layout container)
# Blocks allows custom layouts with tabs, rows, columns, etc.
# title: Browser tab/window title
# theme: Visual theme (Soft provides pleasant color scheme)
with gr.Blocks(title="RAID Sim", theme=gr.themes.Soft()) as app:
    
    # ========================================================================
    # Application Header
    # ========================================================================
    
    # Add HTML header with custom styling
    # Creates centered title with gradient background and white text
    gr.HTML(
        "<h1 style='text-align:center; background:#667eea; color:white; "
        "padding:10px; border-radius:10px;'>💾 RAID Simulator</h1>"
    )
    
    # Create hidden state variable to store scanned folder size
    # State persists between UI interactions but isn't displayed
    # Initial value: 0 (megabytes)
    state_size = gr.State(0)
    
    # ========================================================================
    # Tab Container (3 Tabs for Workflow)
    # ========================================================================
    
    with gr.Tabs():
        
        # ====================================================================
        # TAB 1: Load Media Files
        # ====================================================================
        
        with gr.Tab("1. Load"):
            # Row container for horizontal layout
            with gr.Row():
                # Text input for folder path
                # User types or pastes path to media folder
                inp = gr.Textbox(label="Path")
                
                # Button to trigger folder scan
                # variant="primary" makes it blue/prominent
                btn = gr.Button("Scan", variant="primary")
            
            # Markdown output area for scan summary
            # Displays file count, size, and type breakdown
            out_md = gr.Markdown()
            
            # DataFrame display for file details table
            # Shows first 200 files with metadata
            out_tbl = gr.DataFrame()
            
            # Connect button click to scan_folder function
            # Inputs: inp (folder path textbox)
            # Outputs: out_md (summary), out_tbl (table), state_size (hidden state)
            btn.click(
                scan_folder,                      # Function to call
                inp,                              # Input component(s)
                [out_md, out_tbl, state_size]    # Output component(s)
            )
        
        # ====================================================================
        # TAB 2: Configure RAID Parameters
        # ====================================================================
        
        with gr.Tab("2. Config"):
            # Slider for selecting number of disks
            # Range: 2-12 disks, default: 4, step: 1 (integers only)
            d_sld = gr.Slider(
                2, 12,              # Min, max values
                value=4,            # Default value
                step=1,             # Increment step
                label="Disks"       # Display label
            )
            
            # Radio buttons for RAID level selection
            # Options: RAID 0 (striping), RAID 1 (mirroring), RAID 5 (parity)
            # Default: RAID 5 (balanced performance and redundancy)
            r_rad = gr.Radio(
                ["RAID 0", "RAID 1", "RAID 5"],  # Available options
                value="RAID 5",                   # Default selection
                label="Level"                     # Display label
            )
            
            # Button to calculate metrics preview
            c_btn = gr.Button("Calc Metrics")
            
            # Markdown output for displaying calculated metrics
            c_out = gr.Markdown()
            
            # Connect button to lambda function for quick calculation
            # Lambda creates inline anonymous function
            # Inputs: n (num_disks), r (raid_level), s (size - unused)
            # Output: formatted string with usable % and efficiency %
            # :.1f formats float with 1 decimal place
            # :.2% formats float as percentage with 2 decimal places
            c_btn.click(
                lambda n, r, s: f"**Usable:** {usable_capacity_percent(n,r):.1f}% | "
                                f"**Eff:** {space_efficiency(n,r):.2%}",
                [d_sld, r_rad, state_size],      # Input components
                c_out                             # Output component
            )

        # ====================================================================
        # TAB 3: Run Simulation and View Results
        # ====================================================================
        
        with gr.Tab("3. Run"):
            # Main simulation button
            # Emoji adds visual appeal, variant="primary" emphasizes importance
            s_btn = gr.Button("🚀 Simulate", variant="primary")
            
            # Markdown output for simulation status message
            s_out = gr.Markdown()
            
            # Row container for side-by-side chart display
            with gr.Row():
                # Plot component for capacity distribution pie chart
                # Displays matplotlib Figure object directly
                p1 = gr.Plot(label="Capacity Distribution")
                
                # Plot component for performance bar chart
                p2 = gr.Plot(label="Performance")
            
            # Row container for data tables
            with gr.Row():
                # DataFrame for displaying simulation run data
                # Shows RAID level, disk count, times, capacity metrics
                res_df = gr.DataFrame(label="Run Data")
                
                # DataFrame for displaying statistical summary
                # Shows mean, std, median, min, max, variance
                stats_tbl = gr.DataFrame(label="Summary Statistics")
            
            # File download component allowing multiple file downloads
            # Users can download CSV reports, PNG charts, and ZIP archive
            dl = gr.File(
                label="Download Reports & Virtual Disks",
                file_count="multiple"
            )
            
            # Connect simulation button to run_simulation function
            # Inputs: d_sld (num_disks), r_rad (raid_level)
            # Outputs: message, run data, stats, pie chart, bar chart, files
            s_btn.click(
                run_simulation,                          # Function to execute
                [d_sld, r_rad],                         # Input components
                [s_out, res_df, stats_tbl, p1, p2, dl] # Output components
            )


# ============================================================================
# SECTION 9: APPLICATION ENTRY POINT
# ============================================================================

# Standard Python idiom to check if script is run directly (not imported)
# __name__ is "__main__" only when script is executed directly
if __name__ == "__main__":
    # Launch the Gradio application
    # inbrowser=True automatically opens default web browser to the app
    # Server will run on localhost (usually http://127.0.0.1:7860)
    app.launch(inbrowser=True)
