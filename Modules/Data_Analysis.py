#!/usr/bin/env python3
"""
==============================================================================
Data_Analysis.py - RAID Simulation Data Collection and Statistical Analysis
==============================================================================

Purpose:
--------
This module provides functions for collecting, storing, and analyzing
RAID simulation results. It handles:
  1. Appending simulation run data to pandas DataFrames
  2. Saving reports to CSV files in the reports directory
  3. Calculating statistical summaries (mean, std, median, min, max, variance)

The module is designed to work with simulation data from RAID performance
tests, tracking metrics like read/write times and IOPS across multiple runs.

Key Functions:
-------------
- append_run(): Add a new simulation run to the dataset
- save_report_csv(): Save DataFrame to CSV file
- summary_statistics(): Calculate statistical measures for performance metrics

Authors: Omar and Youssef
Deadline: Monday
Version: 1.0
==============================================================================
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

import pandas as pd  # Data manipulation and analysis library
import os           # Operating system interface for file/directory operations

# ==============================================================================
# FUNCTION: append_run
# ==============================================================================

def append_run(df, run_info_dict):
    """
    Appends a new simulation run to the existing DataFrame.
    
    This function takes a dictionary containing simulation metrics and adds it
    as a new row to the DataFrame. If the DataFrame is None or empty, it creates
    a new DataFrame with the run data.
    
    Parameters:
    -----------
    df : pandas.DataFrame or None
        Existing DataFrame containing previous simulation runs.
        Can be None if this is the first run.
    
    run_info_dict : dict
        Dictionary containing simulation metrics. Expected keys may include:
        - run_id: Unique identifier for the run
        - raid_level: RAID configuration level (0, 1, 5, etc.)
        - disk_count: Number of disks in the array
        - read_time_ms: Read operation time in milliseconds
        - write_time_ms: Write operation time in milliseconds
        - read_iops: Read I/O operations per second
        - write_iops: Write I/O operations per second
        - total_files: Number of files processed
        - total_size_bytes: Total data size processed
        - usable_%: Percentage of usable capacity
        - efficiency_%: Storage efficiency percentage
    
    Returns:
    --------
    pandas.DataFrame
        Updated DataFrame containing all runs including the new one.
        If input df was None, returns a new DataFrame with just this run.
    
    Example:
    --------
    >>> run1 = {"run_id": 1, "raid_level": 5, "read_time_ms": 120}
    >>> df = append_run(None, run1)  # First run
    >>> run2 = {"run_id": 2, "raid_level": 1, "read_time_ms": 140}
    >>> df = append_run(df, run2)    # Second run appended
    >>> print(df)
       run_id  raid_level  read_time_ms
    0       1           5           120
    1       2           1           140
    
    Technical Notes:
    ---------------
    - Creates a new DataFrame from the dictionary with one row
    - Uses pd.concat() to append rows (more efficient than DataFrame.append())
    - ignore_index=True resets row indices to sequential integers
    - Safe to call with None df for initialization
    """
    
    # Convert the run information dictionary to a single-row DataFrame
    # The list wrapper [run_info_dict] ensures pandas creates one row
    row = pd.DataFrame([run_info_dict])
    
    # Check if this is the first run (df is None or empty)
    if df is None or df.empty:
        # Return the single row as the new DataFrame
        return row
    else:
        # Concatenate existing DataFrame with the new row
        # ignore_index=True renumbers rows sequentially (0, 1, 2, ...)
        return pd.concat([df, row], ignore_index=True)

# ==============================================================================
# FUNCTION: save_report_csv
# ==============================================================================

def save_report_csv(df, filename):
    """
    Saves a DataFrame to a CSV file in the reports directory.
    
    This function ensures the reports folder exists and saves the provided
    DataFrame to a CSV file within that folder. It provides console feedback
    about the save operation.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the data to save.
        Typically contains simulation runs or statistical summaries.
    
    filename : str
        Name of the CSV file (without path).
        Examples: "simulation_report.csv", "statistics_report.csv"
        The file will be saved in the "reports" subfolder.
    
    Returns:
    --------
    None
        Function performs file I/O and prints status messages.
    
    Side Effects:
    ------------
    - Creates "reports" directory if it doesn't exist
    - Writes CSV file to disk
    - Prints confirmation messages to console
    
    Example:
    --------
    >>> df = pd.DataFrame({"metric": ["read_time"], "value": [120]})
    >>> save_report_csv(df, "test_report.csv")
    The Report saved to reports/test_report.csv
    
    File Format:
    -----------
    - CSV format with comma separator
    - No row indices included (index=False)
    - Headers included as first row
    - UTF-8 encoding
    """
    
    # Define the name of the reports folder
    reports_folder = "reports"
    
    # Check if reports folder exists
    if not os.path.exists(reports_folder):
        # Create the folder if it doesn't exist
        os.makedirs(reports_folder)
        print(f"Created folder: {reports_folder}")
    
    # Construct the full file path by joining folder and filename
    # Example: "reports" + "simulation_report.csv" = "reports/simulation_report.csv"
    full_path = os.path.join(reports_folder, filename)
    
    # Save the DataFrame to CSV file
    # index=False: Don't include row numbers in the CSV
    df.to_csv(full_path, index=False)
    
    # Print confirmation message with the full path
    print(f"The Report saved to {full_path}")

# ==============================================================================
# PERFORMANCE METRICS CONFIGURATION
# ==============================================================================

# List of performance fields to calculate statistics for
# These are the key metrics tracked across simulation runs
fields = [
    "read_time_ms",   # Read operation time in milliseconds
    "write_time_ms",  # Write operation time in milliseconds
    "read_iops",      # Read I/O operations per second
    "write_iops"      # Write I/O operations per second
]

# ==============================================================================
# FUNCTION: summary_statistics
# ==============================================================================

def summary_statistics(df):
    """
    Calculates comprehensive statistical summaries for performance metrics.
    
    This function computes six key statistical measures for each performance
    metric in the fields list:
    - Mean (average value)
    - Standard Deviation (measure of spread)
    - Median (middle value)
    - Minimum (lowest value)
    - Maximum (highest value)
    - Variance (square of standard deviation)
    
    These statistics help analyze the consistency and range of RAID
    performance across multiple simulation runs.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing simulation run data.
        Should include columns matching the names in the 'fields' list.
        May have additional columns which will be ignored.
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with one row per metric containing:
        - metric: Name of the performance metric
        - mean: Average value across all runs
        - std: Standard deviation (measure of variability)
        - median: Middle value when sorted
        - min: Minimum value observed
        - max: Maximum value observed
        - variance: Square of standard deviation
    
    Example:
    --------
    >>> runs = pd.DataFrame({
    ...     "read_time_ms": [120, 130, 125],
    ...     "write_time_ms": [210, 220, 215]
    ... })
    >>> stats = summary_statistics(runs)
    >>> print(stats)
              metric   mean       std  median  min  max  variance
    0  read_time_ms  125.0  5.000000   125.0  120  130     25.00
    1 write_time_ms  215.0  5.000000   215.0  210  220     25.00
    
    Technical Notes:
    ---------------
    - If a metric is not in the DataFrame, all statistics will be None
    - Uses pandas built-in statistical functions for accuracy
    - Variance is calculated as std²
    - Returns None for metrics with insufficient data
    """
    
    # Initialize empty list to store statistics for each metric
    stats_rows = []
    
    # Iterate through each performance metric we want to analyze
    for field in fields:
        
        # Check if this metric exists as a column in the DataFrame
        if field in df.columns:
            # Calculate all statistics for this metric
            stats_rows.append({
                "metric": field,                    # Name of the metric
                "mean": df[field].mean(),          # Average value
                "std": df[field].std(),            # Standard deviation (spread)
                "median": df[field].median(),      # Middle value
                "min": df[field].min(),            # Minimum value
                "max": df[field].max(),            # Maximum value
                "variance": df[field].var()        # Variance (std squared)
            })
        else:
            # Metric not found in DataFrame - add row with None values
            # This ensures the output always has entries for all expected metrics
            stats_rows.append({
                "metric": field,
                "mean": None,
                "std": None,
                "median": None,
                "min": None,
                "max": None,
                "variance": None
            })
    
    # Convert list of dictionaries to DataFrame and return
    return pd.DataFrame(stats_rows)

# ==============================================================================
# EXAMPLE USAGE AND TESTING
# ==============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the module's functions.
    This code runs when the module is executed directly (not imported).
    """
    
    # Example Simulation Run 1: RAID 5 with 4 disks
    run1 = {
        "run_id": 1,              # Unique identifier for this run
        "raid_level": 5,          # RAID 5 configuration
        "disk_count": 4,          # 4 disks in the array
        "read_time_ms": 120,      # Read took 120 milliseconds
        "write_time_ms": 210,     # Write took 210 milliseconds
        "read_iops": 380,         # 380 read operations per second
        "write_iops": 220         # 220 write operations per second
    }

    # Example Simulation Run 2: RAID 10 with 8 disks
    run2 = {
        "run_id": 2,
        "raid_level": 10,         # RAID 10 configuration
        "disk_count": 8,          # 8 disks (more expensive but faster)
        "read_time_ms": 130,
        "write_time_ms": 220,
        "read_iops": 390,
        "write_iops": 230
    }
    
    # Example Simulation Run 3: RAID 3 with 6 disks
    run3 = {
        "run_id": 3,
        "raid_level": 3,
        "disk_count": 6,
        "read_time_ms": 175,
        "write_time_ms": 225,
        "read_iops": 380,
        "write_iops": 275
    }

    # Initialize empty DataFrame
    df = None

    # Add runs to DataFrame one by one
    df = append_run(df, run1)  # First run creates the DataFrame
    df = append_run(df, run2)  # Second run appends to existing DataFrame
    df = append_run(df, run3)  # Third run appends

    # Display the main DataFrame with all runs
    print("\n=== Main DataFrame ===")
    print(df)

    # Calculate statistical summary
    stats_df = summary_statistics(df)
    
    # Display the statistics DataFrame
    print("\n=== Statistics DataFrame ===")
    print(stats_df)

    # Save both DataFrames to CSV files
    save_report_csv(df, "simulation_report.csv")
    save_report_csv(stats_df, "statistics_report.csv")
    
    print("\n=== Files saved successfully ===")
    print("Check the 'reports' folder for:")
    print("  - simulation_report.csv (raw data)")
    print("  - statistics_report.csv (summary stats)")
