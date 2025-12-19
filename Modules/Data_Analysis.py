#!/usr/bin/env python3
"""
================================================================================
Data_Analysis.py - Data Collection and Statistical Analysis Module
================================================================================

Purpose:
    This module handles data collection, storage, and statistical analysis
    for RAID simulation results. It provides functions to:
    - Append new simulation runs to a DataFrame
    - Save reports to CSV files
    - Calculate summary statistics (mean, std, median, min, max, variance)

Authors: Omar and Youssef
Deadline: Monday
Last Updated: December 2024

Dependencies:
    - pandas: For DataFrame operations and CSV file handling
    - os: For file system operations

Key Functions:
    - append_run(): Adds a new simulation run to existing data
    - save_report_csv(): Saves DataFrame to CSV in reports folder
    - summary_statistics(): Generates statistical summary of performance metrics

================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

import pandas as pd  # Data manipulation and analysis library
import os           # Operating system interface for file operations

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def append_run(df, run_info_dict):
    """
    Appends a new simulation run to the existing DataFrame.
    
    This function takes simulation results as a dictionary and adds them
    as a new row to the DataFrame. If the DataFrame doesn't exist (None),
    it creates a new one.
    
    Args:
        df (pd.DataFrame or None): Existing DataFrame with simulation data.
                                   Can be None for the first run.
        run_info_dict (dict): Dictionary containing simulation metrics.
                             Common keys include:
                             - raid_level: RAID configuration (str)
                             - disk_count: Number of disks (int)
                             - read_time_ms: Read operation time (float)
                             - write_time_ms: Write operation time (float)
                             - read_iops: Read IOPS (int)
                             - write_iops: Write IOPS (int)
                             - usable_%: Usable capacity percentage (float)
                             - efficiency_%: Space efficiency percentage (float)
    
    Returns:
        pd.DataFrame: Updated DataFrame containing all simulation runs
                     including the newly added run.
    
    Example:
        >>> df = None  # First run
        >>> run_data = {"raid_level": "RAID 5", "read_time_ms": 120}
        >>> df = append_run(df, run_data)
        >>> # df now contains 1 row
        >>> run_data2 = {"raid_level": "RAID 0", "read_time_ms": 80}
        >>> df = append_run(df, run_data2)
        >>> # df now contains 2 rows
    
    Notes:
        - This function does NOT modify the original DataFrame
        - Always reassign the result: df = append_run(df, new_run)
        - If df is None or empty, returns a new DataFrame with just the new row
    """
    # Create a new DataFrame with a single row from the dictionary
    # The list wrapper [run_info_dict] creates a DataFrame with one row
    row = pd.DataFrame([run_info_dict])
    
    # Check if the existing DataFrame is None or empty
    if df is None or df.empty:
        # Return the new row as the complete DataFrame
        return row
    else:
        # Concatenate existing DataFrame with new row
        # ignore_index=True resets the index to 0, 1, 2, ...
        return pd.concat([df, row], ignore_index=True)


def save_report_csv(df, filename):
    """
    Saves a DataFrame to a CSV file in the 'reports' folder.
    
    This function ensures the reports folder exists and saves the
    provided DataFrame to a CSV file with the specified filename.
    It prints confirmation messages for debugging.
    
    Args:
        df (pd.DataFrame): DataFrame to save to CSV
        filename (str): Name of the CSV file (just the filename, not full path)
                       Example: "simulation_report.csv"
    
    Returns:
        None (saves file to disk)
    
    Side Effects:
        - Creates 'reports' folder if it doesn't exist
        - Writes CSV file to reports/{filename}
        - Prints status messages to console
    
    Example:
        >>> df = pd.DataFrame({"raid_level": ["RAID 0", "RAID 5"]})
        >>> save_report_csv(df, "my_simulation.csv")
        Created folder: reports  # (only if folder didn't exist)
        The Report saved to reports/my_simulation.csv
    
    Notes:
        - CSV is saved without the DataFrame index (index=False)
        - Existing files with the same name will be overwritten
        - File encoding is UTF-8 by default
    """
    # Define the reports folder name
    reports_folder = "reports"
    
    # Check if the reports folder exists
    if not os.path.exists(reports_folder):
        # Create the folder if it doesn't exist
        os.makedirs(reports_folder)
        print(f"Created folder: {reports_folder}")
    
    # Construct the full file path by joining folder and filename
    # Example: "reports" + "/" + "simulation_report.csv" = "reports/simulation_report.csv"
    full_path = os.path.join(reports_folder, filename)
    
    # Save the DataFrame to CSV
    # index=False: Don't save the row numbers as a column
    df.to_csv(full_path, index=False)
    
    # Print confirmation message
    print(f"The Report saved to {full_path}")


# ============================================================================
# STATISTICAL ANALYSIS
# ============================================================================

# List of performance metrics to analyze
# These fields are expected in the simulation results DataFrame
fields = [
    "read_time_ms",   # Read operation time in milliseconds
    "write_time_ms",  # Write operation time in milliseconds
    "read_iops",      # Read Input/Output Operations Per Second
    "write_iops"      # Write Input/Output Operations Per Second
]

def summary_statistics(df):
    """
    Calculates comprehensive summary statistics for performance metrics.
    
    This function computes statistical measures (mean, standard deviation,
    median, min, max, variance) for each performance metric in the DataFrame.
    If a metric doesn't exist in the DataFrame, it returns None values.
    
    Args:
        df (pd.DataFrame): DataFrame containing simulation results.
                          Should have columns matching the 'fields' list.
    
    Returns:
        pd.DataFrame: Summary statistics DataFrame with columns:
                     - metric: Name of the performance metric (str)
                     - mean: Average value (float)
                     - std: Standard deviation (float)
                     - median: Middle value (float)
                     - min: Minimum value (float)
                     - max: Maximum value (float)
                     - variance: Statistical variance (float)
    
    Example:
        >>> df = pd.DataFrame({
        ...     "read_time_ms": [100, 120, 110],
        ...     "write_time_ms": [200, 210, 205]
        ... })
        >>> stats = summary_statistics(df)
        >>> print(stats)
               metric   mean   std  median  min  max  variance
        0  read_time_ms  110.0  10.0   110.0  100  120     100.0
        1 write_time_ms  205.0   5.0   205.0  200  210      25.0
        2    read_iops   None  None    None None None      None
        3   write_iops   None  None    None None None      None
    
    Statistical Measures Explained:
        - mean: Average of all values
        - std: How spread out the values are from the mean
        - median: Middle value when sorted
        - min: Smallest value
        - max: Largest value
        - variance: Square of standard deviation (measure of spread)
    
    Notes:
        - Returns None for metrics not present in the DataFrame
        - Uses pandas built-in statistical functions
        - All calculations handle NaN values appropriately
    """
    # Initialize empty list to store statistics for each metric
    stats_rows = []
    
    # Iterate through each performance metric
    for field in fields:
        # Check if this metric exists as a column in the DataFrame
        if field in df.columns:
            # Calculate all statistics for this metric and store in dictionary
            stats_rows.append({
                "metric": field,                # Name of the metric
                "mean": df[field].mean(),       # Calculate average
                "std": df[field].std(),         # Calculate standard deviation
                "median": df[field].median(),   # Calculate median (middle value)
                "min": df[field].min(),         # Find minimum value
                "max": df[field].max(),         # Find maximum value
                "variance": df[field].var()     # Calculate variance
            })
        else:
            # Metric doesn't exist in DataFrame, return None for all statistics
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


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

# Example simulation runs for testing
# These demonstrate the expected data structure

# Run 1: RAID 5 with 4 disks
run1 = {
    "run_id": 1,              # Unique identifier for this run
    "raid_level": 5,          # RAID 5 configuration
    "disk_count": 4,          # 4 disks in the array
    "read_time_ms": 120,      # Read operation took 120ms
    "write_time_ms": 210,     # Write operation took 210ms
    "read_iops": 380,         # 380 read operations per second
    "write_iops": 220         # 220 write operations per second
}

# Run 2: RAID 10 with 8 disks
run2 = {
    "run_id": 2,              # Unique identifier
    "raid_level": 10,         # RAID 10 configuration (RAID 1+0)
    "disk_count": 8,          # 8 disks in the array
    "read_time_ms": 130,      # Slightly slower read
    "write_time_ms": 220,     # Slightly slower write
    "read_iops": 390,         # Higher read IOPS
    "write_iops": 230         # Higher write IOPS
}

# Run 3: RAID 3 with 6 disks
run3 = {
    "run_id": 3,              # Unique identifier
    "raid_level": 3,          # RAID 3 configuration
    "disk_count": 6,          # 6 disks in the array
    "read_time_ms": 175,      # Slower read time
    "write_time_ms": 225,     # Slower write time
    "read_iops": 380,         # Standard read IOPS
    "write_iops": 275         # Higher write IOPS
}

# Initialize DataFrame as None (empty)
df = None

# Add first run to DataFrame (creates new DataFrame)
df = append_run(df, run1)

# Add second run to DataFrame (appends to existing)
df = append_run(df, run2)

# Display the main DataFrame with all runs
print("\n=== Main DataFrame ===")
print(df)

# Generate and display statistical summary
print("\n=== Statistics DataFrame ===")
stats_df = summary_statistics(df)
print(stats_df)

# Save both DataFrames to CSV files in the reports folder
save_report_csv(df, "simulation_report.csv")
save_report_csv(stats_df, "statistics_report.csv")

# ============================================================================
# NOTES FOR DEVELOPERS
# ============================================================================
"""
Usage in Main Application:
    1. Create empty DataFrame: df = None
    2. For each simulation:
       - Collect metrics in a dictionary
       - Append to DataFrame: df = append_run(df, metrics)
    3. Generate statistics: stats = summary_statistics(df)
    4. Save results: save_report_csv(df, "report.csv")

Best Practices:
    - Always reassign the result of append_run()
    - Use consistent key names in run dictionaries
    - Check for None/empty DataFrame before processing
    - Create reports folder at application startup

Error Handling:
    - pandas handles missing columns gracefully (returns None)
    - File operations may raise IOError if disk is full
    - Consider adding try-except blocks in production code
"""
