
"""
Data_Analysis.py - RAID Simulation Data Analysis Module
========================================================
This module provides data analysis utilities for the RAID Storage Simulator.
It handles collection, storage, and statistical analysis of simulation results.

Primary Functions:
- append_run: Adds simulation run data to a DataFrame
- save_report_csv: Exports DataFrames to CSV files in reports folder
- summary_statistics: Calculates statistical metrics across performance fields

Authors: Omar and Youssef
Deadline: Monday
Date: 2024
"""

# ============================================================================
# SECTION 1: IMPORT STATEMENTS
# ============================================================================

# Import pandas for data manipulation and analysis
# pandas provides DataFrame structures for tabular data
import pandas as pd

# Import os for operating system interface
# Used for file/directory operations (creating folders, checking paths)
import os


# ============================================================================
# SECTION 2: DATA COLLECTION FUNCTION
# ============================================================================

def append_run(df, run_info_dict):
    """
    Appends a new simulation run to the existing DataFrame.
    
    This function takes a dictionary containing metrics from a single RAID
    simulation run and adds it as a new row to the DataFrame. If no DataFrame
    exists yet (None or empty), it creates a new one with the first run.
    
    Parameters
    ----------
    df : pd.DataFrame or None
        Existing DataFrame containing previous simulation runs.
        Can be None (for first run) or empty DataFrame.
    run_info_dict : dict
        Dictionary containing simulation metrics for one run.
        Expected keys include: raid_level, disk_count, read_time_ms,
        write_time_ms, total_size_bytes, usable_%, efficiency_%, etc.
    
    Returns
    -------
    pd.DataFrame
        Updated DataFrame containing all previous runs plus the new run.
        If df was None/empty, returns DataFrame with single row.
    
    Notes
    -----
    - Each run is added as a new row (horizontal concatenation)
    - Index is reset to sequential integers (0, 1, 2, ...)
    - Dictionary keys become DataFrame column names
    - Safe to call with None as first argument for initialization
    
    Examples
    --------
    >>> df = None  # No data yet
    >>> run1 = {"raid_level": "RAID 5", "read_time_ms": 120}
    >>> df = append_run(df, run1)  # Create new DataFrame
    >>> run2 = {"raid_level": "RAID 1", "read_time_ms": 95}
    >>> df = append_run(df, run2)  # Append to existing
    >>> print(df)
      raid_level  read_time_ms
    0    RAID 5           120
    1    RAID 1            95
    """
    
    # Convert dictionary to single-row DataFrame
    # [run_info_dict] wraps dict in list to create one row
    # Without list, keys would become columns with scalar values
    row = pd.DataFrame([run_info_dict])
    
    # Check if DataFrame is None (first run) or empty (no rows)
    # df.empty checks if DataFrame has zero rows
    if df is None or df.empty:
        # Return the new row as the complete DataFrame
        # This initializes the DataFrame with first run's data
        return row
    else:
        # Concatenate existing DataFrame with new row
        # axis=0 means vertical stacking (adding row, not column)
        # ignore_index=True resets index to 0, 1, 2, ... sequence
        # Without ignore_index, would keep original indices causing gaps
        return pd.concat([df, row], ignore_index=True)


# ============================================================================
# SECTION 3: FILE EXPORT FUNCTION
# ============================================================================

def save_report_csv(df, filename):
    """
    Saves DataFrame to CSV file in the reports folder.
    
    This function exports simulation data to a CSV file, automatically creating
    the reports directory if it doesn't exist. Files are saved with the given
    filename in the 'reports/' subdirectory.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing data to export (run data or statistics).
        Can contain any columns; all will be saved to CSV.
    filename : str
        Name of the CSV file (e.g., "simulation_report.csv").
        Should include .csv extension.
    
    Returns
    -------
    None
        Function performs file I/O but returns nothing.
        Prints confirmation messages to console.
    
    Side Effects
    ------------
    - Creates 'reports/' directory if it doesn't exist
    - Writes CSV file to disk
    - Prints status messages to console
    
    Notes
    -----
    - CSV is saved without index column (index=False)
    - Overwrites existing file with same name
    - Uses UTF-8 encoding by default
    - Column names become CSV header row
    
    Examples
    --------
    >>> df = pd.DataFrame({"raid": ["RAID 5"], "time": [120]})
    >>> save_report_csv(df, "test_report.csv")
    Created folder: reports
    The Report saved to reports/test_report.csv
    """
    
    # Define the name of the reports folder
    # Using relative path (subfolder of current directory)
    reports_folder = "reports"
    
    # Check if reports directory exists
    # os.path.exists returns True if path exists (file or directory)
    if not os.path.exists(reports_folder):
        # Create the directory if it doesn't exist
        # os.makedirs creates all intermediate directories if needed
        # (though here we only create one level)
        os.makedirs(reports_folder)
        
        # Print confirmation message to console
        # Useful for debugging and user feedback
        print(f"Created folder: {reports_folder}")
    
    # Construct full file path by joining folder and filename
    # os.path.join handles OS-specific path separators (/ or \)
    # Result: "reports/simulation_report.csv"
    full_path = os.path.join(reports_folder, filename)
    
    # Export DataFrame to CSV file
    # index=False excludes the DataFrame index (row numbers) from CSV
    # This creates cleaner CSV with only actual data columns
    df.to_csv(full_path, index=False)
    
    # Print confirmation message showing save location
    # Provides feedback that operation completed successfully
    print(f"The Report saved to {full_path}")


# ============================================================================
# SECTION 4: STATISTICAL ANALYSIS CONFIGURATION
# ============================================================================

# Define list of performance metric fields to analyze
# These are the column names expected in simulation DataFrames
# Statistics will be calculated for each of these fields
fields = [
    "read_time_ms",   # Read operation time in milliseconds
    "write_time_ms",  # Write operation time in milliseconds
    "read_iops",      # Read I/O Operations Per Second
    "write_iops"      # Write I/O Operations Per Second
]


# ============================================================================
# SECTION 5: STATISTICAL ANALYSIS FUNCTION
# ============================================================================

def summary_statistics(df):
    """
    Calculates comprehensive statistical metrics for performance fields.
    
    This function computes descriptive statistics (mean, standard deviation,
    median, min, max, variance) for each performance metric field across all
    simulation runs. If a field doesn't exist in the DataFrame, it returns
    None values for that metric.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing simulation run data with performance metrics.
        Expected to have some or all of: read_time_ms, write_time_ms,
        read_iops, write_iops columns.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with one row per metric field containing:
        - metric: Field name (e.g., "read_time_ms")
        - mean: Arithmetic mean (average value)
        - std: Standard deviation (spread of values)
        - median: Middle value when sorted
        - min: Minimum value
        - max: Maximum value
        - variance: Square of standard deviation
    
    Notes
    -----
    - Handles missing columns gracefully (returns None for statistics)
    - Uses pandas built-in statistical methods for accuracy
    - Variance is calculated as std²
    - Useful for comparing performance across multiple runs
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     "read_time_ms": [100, 120, 110],
    ...     "write_time_ms": [200, 220, 210]
    ... })
    >>> stats = summary_statistics(df)
    >>> print(stats)
              metric   mean   std  median  min  max  variance
    0  read_time_ms  110.0  10.0   110.0  100  120     100.0
    1 write_time_ms  210.0  10.0   210.0  200  220     100.0
    2     read_iops   None  None    None None None      None
    3    write_iops   None  None    None None None      None
    """
    
    # Initialize empty list to store statistics for each field
    # Each element will be a dictionary with metric name and statistics
    stats_rows = []
    
    # Iterate through each performance metric field
    # fields is defined globally at module level
    for field in fields:
        # Check if current field exists as a column in DataFrame
        # df.columns returns list of column names
        # 'in' operator checks membership in that list
        if field in df.columns:
            # Field exists: Calculate all statistics
            
            # Append dictionary with field name and calculated statistics
            stats_rows.append({
                # Name of the metric being analyzed
                "metric": field,
                
                # Mean (average): Sum of values divided by count
                # df[field].mean() computes arithmetic mean of column
                "mean": df[field].mean(),
                
                # Standard deviation: Measure of value spread
                # df[field].std() uses sample std (N-1 denominator)
                "std": df[field].std(),
                
                # Median (middle value): 50th percentile
                # df[field].median() returns middle value when sorted
                "median": df[field].median(),
                
                # Minimum: Smallest value in the column
                # df[field].min() returns lowest value
                "min": df[field].min(),
                
                # Maximum: Largest value in the column
                # df[field].max() returns highest value
                "max": df[field].max(),
                
                # Variance: Square of standard deviation
                # df[field].var() measures average squared deviation from mean
                "variance": df[field].var()
            })
        else:
            # Field doesn't exist in DataFrame: Return None for all statistics
            # This prevents errors when DataFrame is missing expected columns
            
            # Append dictionary with field name but None for all stats
            stats_rows.append({
                "metric": field,      # Keep field name for reference
                "mean": None,         # No data to calculate mean
                "std": None,          # No data for standard deviation
                "median": None,       # No data for median
                "min": None,          # No data for minimum
                "max": None,          # No data for maximum
                "variance": None      # No data for variance
            })
    
    # Convert list of dictionaries to DataFrame
    # Each dictionary becomes a row, dictionary keys become columns
    # Result is DataFrame with one row per metric field
    return pd.DataFrame(stats_rows)


# ============================================================================
# SECTION 6: EXAMPLE USAGE AND TESTING CODE
# ============================================================================

# The following code demonstrates module functionality when run directly
# This section is for testing/demonstration and won't execute when imported

# Example usage comments (for reference only - code is commented out)
# save_report_csv(df, "simulation_report.csv")
# save_report_csv(stats_df, "statistics_report.csv")


# ----------------------------------------------------------------------------
# Example Simulation Run Data (Test Data)
# ----------------------------------------------------------------------------

# Define first example RAID simulation run
# Dictionary contains metrics from a hypothetical RAID 5 test
run1 = {
    "run_id": 1,              # Unique identifier for this run
    "raid_level": 5,          # RAID 5 (striping with distributed parity)
    "disk_count": 4,          # 4 disks in the array
    "read_time_ms": 120,      # Read operation took 120 milliseconds
    "write_time_ms": 210,     # Write operation took 210 milliseconds
    "read_iops": 380,         # 380 read operations per second
    "write_iops": 220         # 220 write operations per second
}

# Define second example RAID simulation run
# Different RAID level (10) with more disks
run2 = {
    "run_id": 2,              # Second run identifier
    "raid_level": 10,         # RAID 10 (mirrored stripes)
    "disk_count": 8,          # 8 disks (more than run1)
    "read_time_ms": 130,      # Slightly slower read than run1
    "write_time_ms": 220,     # Slightly slower write than run1
    "read_iops": 390,         # Better IOPS than run1 (more disks)
    "write_iops": 230         # Better write IOPS than run1
}

# Define third example RAID simulation run (currently unused)
# RAID 3 with medium disk count
run3 = {
    "run_id": 3,              # Third run identifier
    "raid_level": 3,          # RAID 3 (byte-level striping with parity)
    "disk_count": 6,          # 6 disks in the array
    "read_time_ms": 175,      # Slower than run1 and run2
    "write_time_ms": 225,     # Slowest write of all three
    "read_iops": 380,         # Same as run1
    "write_iops": 275         # Better than run1, worse than run2
}


# ----------------------------------------------------------------------------
# Build Example DataFrame
# ----------------------------------------------------------------------------

# Initialize DataFrame as None (empty state)
# Will be populated by append_run calls
df = None

# Add first run to DataFrame
# Since df is None, this creates new DataFrame with one row
df = append_run(df, run1)

# Add second run to DataFrame
# Now df exists, so this appends to existing DataFrame
df = append_run(df, run2)

# Note: run3 is defined but not added to demonstrate selective inclusion


# ----------------------------------------------------------------------------
# Display Results
# ----------------------------------------------------------------------------

# Print separator and header for main DataFrame output
# Triple quotes allow multi-line strings, \n adds blank line
print("\n=== Main DataFrame ===")

# Print the DataFrame containing both runs
# pandas automatically formats as ASCII table
print(df)

# Print separator and header for statistics DataFrame output
print("\n=== Statistics DataFrame ===")

# Calculate statistics across all runs in DataFrame
# Computes mean, std, median, min, max, variance for each metric
stats_df = summary_statistics(df)

# Print the statistics DataFrame
# Shows one row per metric field with calculated statistics
print(stats_df)


# ----------------------------------------------------------------------------
# Save Results to CSV Files
# ----------------------------------------------------------------------------

# Export main simulation data to CSV file
# Creates/overwrites reports/simulation_report.csv
save_report_csv(df, "simulation_report.csv")

# Export statistical summary to CSV file
# Creates/overwrites reports/statistics_report.csv
save_report_csv(stats_df, "statistics_report.csv")






























































# #omar and youssef (Dead Line : Monday )
# import pandas as pd
# import os

# def append_run(df, run_info_dict):
#     row = pd.DataFrame([run_info_dict])
#     if df is None or df.empty:
#         return row
#     else:
#         return pd.concat([df, row], ignore_index=True)

# def save_report_csv(df, filename):
#     # Create reports folder if it doesn't exist
#     reports_folder = "reports"
#     if not os.path.exists(reports_folder):
#         os.makedirs(reports_folder)
#         print(f"Created folder: {reports_folder}")
    
#     # Create full path
#     full_path = os.path.join(reports_folder, filename)
    
#     # Save the CSV
#     df.to_csv(full_path, index=False)
#     print(f"The Report saved to {full_path}")

# fields = ["read_time_ms", "write_time_ms", "read_iops", "write_iops"]

# def summary_statistics(df):
#     stats_rows = []
#     for field in fields:
#         if field in df.columns:
#             stats_rows.append({
#                 "metric": field,
#                 "mean": df[field].mean(),
#                 "std": df[field].std(),
#                 "median": df[field].median(),
#                 "min": df[field].min(),
#                 "max": df[field].max(),
#                 "variance": df[field].var()
#             })
#         else:
#             stats_rows.append({
#                 "metric": field,
#                 "mean": None,
#                 "std": None,
#                 "median": None,
#                 "min": None,
#                 "max": None,
#                 "variance": None
#             })
#     return pd.DataFrame(stats_rows)

# # Example usage (uncomment to test):
# # save_report_csv(df, "simulation_report.csv")
# # save_report_csv(stats_df, "statistics_report.csv")


# # Example Runs
# run1 = {
#     "run_id": 1,
#     "raid_level": 5,
#     "disk_count": 4,
#     "read_time_ms": 120,
#     "write_time_ms": 210,
#     "read_iops": 380,
#     "write_iops": 220
# }

# run2 = {
#     "run_id": 2,
#     "raid_level": 10,
#     "disk_count": 8,
#     "read_time_ms": 130,
#     "write_time_ms": 220,
#     "read_iops": 390,
#     "write_iops": 230
# }
# run3 = {
#     "run_id": 3,
#     "raid_level": 3,
#     "disk_count": 6,
#     "read_time_ms": 175,
#     "write_time_ms": 225,
#     "read_iops": 380,
#     "write_iops": 275
# }

# df = None

# df = append_run(df, run1)
# df = append_run(df, run2)


# print("\n=== Main DataFrame ===")
# print(df)

# print("\n=== Statistics DataFrame ===")
# stats_df = summary_statistics(df)
# print(stats_df)

# save_report_csv(df, "simulation_report.csv")
# save_report_csv(stats_df, "statistics_report.csv")