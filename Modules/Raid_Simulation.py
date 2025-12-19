#!/usr/bin/env python3
"""
================================================================================
Raid_Simulation.py - RAID Performance Simulation Module
================================================================================

Purpose:
    This module simulates RAID array performance by modeling read and write
    operations with realistic timing and overhead calculations. It provides:
    - Read operation simulation with RAID-specific optimizations
    - Write operation simulation with RAID-specific overhead
    - Complete simulation runner for multiple RAID configurations
    - Integration with data analysis and calculation modules

Authors: Azoz and Saif
Deadline: Monday
Last Updated: December 2024

Simulation Approach:
    - Base speeds represent typical HDD/SSD performance
    - RAID-specific multipliers account for parallelism and overhead
    - Artificial delays simulate real I/O wait times
    - Random IOPS values add variability to results

RAID Performance Characteristics:
    - RAID 0: Fastest (parallel striping, no overhead)
    - RAID 1: Fast reads (mirroring), slower writes (duplication)
    - RAID 5: Moderate speed (parity calculation overhead)

Dependencies:
    - time: For simulating I/O delays
    - random: For generating variable IOPS values
    - Raid_Calculation: For capacity and efficiency calculations
    - Data_Analysis: For storing and analyzing results

================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

import time     # For sleep() to simulate I/O delays
import random   # For generating random IOPS values

# Import RAID calculation functions from our custom module
from Raid_Calculation import (
    usable_capacity_percent,   # Calculates usable storage percentage
    redundancy_percent,        # Calculates redundancy overhead percentage
    space_efficiency           # Calculates space efficiency ratio
)

# Import data analysis utilities from our custom module
from Data_Analysis import (
    append_run,        # Adds a new simulation run to DataFrame
    save_report_csv,   # Saves results to CSV file in reports folder
    summary_statistics # Generates statistical summary (mean, std, etc.)
)

# ============================================================================
# SIMULATION CONSTANTS
# ============================================================================

# Base read speed in megabytes per second (MB/s)
# This represents a typical HDD/SSD read performance
BASE_READ_SPEED = 150  # MB/s

# Base write speed in megabytes per second (MB/s)
# Typically slower than read speed for most storage devices
BASE_WRITE_SPEED = 120  # MB/s

# Standard test file size for operations (in megabytes)
# We simulate reading/writing 500 MB of data
TEST_FILE_SIZE_MB = 500  # MB

# ============================================================================
# READ OPERATION SIMULATION
# ============================================================================

def simulate_raid_read(raid_level):
    """
    Simulates a RAID read operation and returns the time taken.
    
    This function models how different RAID configurations affect read
    performance. RAID levels with mirroring or striping can read from
    multiple disks simultaneously, improving performance.
    
    Args:
        raid_level (str): RAID configuration to simulate.
                         Valid values: "RAID 0", "RAID 1", "RAID 5"
    
    Returns:
        float: Simulated read time in milliseconds (ms)
    
    Performance Characteristics:
        - RAID 0: Fast (parallel striping across all disks)
        - RAID 1: Faster (can read from any mirror, 20% boost)
        - RAID 5: Fast (parallel striping, 10% boost)
    
    Examples:
        >>> simulate_raid_read("RAID 0")
        3333.33  # 500 MB / 150 MB/s = 3.33s = 3333ms
        
        >>> simulate_raid_read("RAID 1")
        2777.78  # 20% faster due to mirroring
        
        >>> simulate_raid_read("RAID 5")
        3030.30  # 10% faster due to striping
    
    How It Works:
        1. Start with base read speed (150 MB/s)
        2. Apply RAID-specific speed multiplier
        3. Calculate time = size / speed
        4. Add artificial delay to simulate real I/O
        5. Return time in milliseconds
    
    Notes:
        - Artificial delay is 1/10th of calculated time (for demo purposes)
        - Real-world performance depends on many factors:
          * Disk RPM (for HDDs)
          * Queue depth
          * Controller cache
          * File system overhead
    """
    # Start with base read speed (150 MB/s)
    base_speed = BASE_READ_SPEED

    # Apply RAID-specific optimizations
    if raid_level == "RAID 1":
        # RAID 1: Can read from any mirror disk in parallel
        # Multiple read heads working simultaneously = faster reads
        # 1.2x multiplier = 20% speed boost
        base_speed *= 1.2

    elif raid_level == "RAID 5":
        # RAID 5: Data striped across multiple disks
        # Can read from multiple disks in parallel
        # 1.1x multiplier = 10% speed boost (less than RAID 1 due to parity)
        base_speed *= 1.1

    # RAID 0 uses base speed (no multiplier needed, already fast from striping)
    
    # Calculate read time in seconds
    # Formula: time = size / speed
    # Example: 500 MB / 150 MB/s = 3.33 seconds
    read_time = TEST_FILE_SIZE_MB / base_speed

    # Simulate actual I/O delay
    # Use 1/10th of calculated time to keep demo responsive
    # In real simulation, this would be the full read_time
    time.sleep(read_time / 10)

    # Convert time from seconds to milliseconds
    # 1 second = 1000 milliseconds
    # Example: 3.33 seconds = 3330 milliseconds
    return read_time * 1000


# ============================================================================
# WRITE OPERATION SIMULATION
# ============================================================================

def simulate_raid_write(raid_level):
    """
    Simulates a RAID write operation and returns the time taken.
    
    This function models how different RAID configurations affect write
    performance. RAID levels with redundancy have additional overhead
    from copying data or calculating parity.
    
    Args:
        raid_level (str): RAID configuration to simulate.
                         Valid values: "RAID 0", "RAID 1", "RAID 5"
    
    Returns:
        float: Simulated write time in milliseconds (ms)
    
    Performance Characteristics:
        - RAID 0: Fast (no overhead, direct writing)
        - RAID 1: Slower (must write to all mirrors, 50% overhead)
        - RAID 5: Moderate (must calculate and write parity, 30% overhead)
    
    Examples:
        >>> simulate_raid_write("RAID 0")
        4166.67  # 500 MB / 120 MB/s = 4.17s = 4167ms
        
        >>> simulate_raid_write("RAID 1")
        6250.00  # 50% slower due to mirroring overhead
        
        >>> simulate_raid_write("RAID 5")
        5416.67  # 30% slower due to parity calculation
    
    How It Works:
        1. Start with base write speed (120 MB/s)
        2. Calculate overhead multiplier based on RAID level
        3. Calculate time = (size / speed) * overhead
        4. Add artificial delay to simulate real I/O
        5. Return time in milliseconds
    
    Overhead Explanation:
        - RAID 0: overhead = 1.0 (no extra work)
        - RAID 1: overhead = 1.5 (must duplicate data to all disks)
        - RAID 5: overhead = 1.3 (must calculate XOR parity)
    
    Notes:
        - Write operations are generally slower than reads
        - RAID 1 has highest write overhead (full duplication)
        - RAID 5 parity calculation is CPU-intensive
        - Modern RAID controllers have hardware parity acceleration
    """
    # Start with base write speed (120 MB/s)
    base_speed = BASE_WRITE_SPEED
    
    # Initialize overhead multiplier (1.0 = no overhead)
    overhead = 1.0

    # Apply RAID-specific overhead
    if raid_level == "RAID 1":
        # RAID 1: Must write data to ALL disks
        # Even though writes happen in parallel, controller is bottleneck
        # 1.5x overhead = 50% slower writes
        # Example: 2 disks means 2x data written, but parallel = 1.5x time
        overhead = 1.5

    elif raid_level == "RAID 5":
        # RAID 5: Must calculate parity (XOR operation) and write it
        # Parity calculation: P = D1 XOR D2 XOR D3 ...
        # 1.3x overhead = 30% slower writes
        # Less overhead than RAID 1 because only 1 parity disk, not n-1 mirrors
        overhead = 1.3

    # RAID 0 uses overhead = 1.0 (no redundancy = no overhead)
    
    # Calculate write time with overhead
    # Formula: time = (size / speed) * overhead
    # Example: (500 MB / 120 MB/s) * 1.5 = 6.25 seconds (RAID 1)
    write_time = (TEST_FILE_SIZE_MB / base_speed) * overhead

    # Simulate actual I/O delay
    # Use 1/10th of calculated time to keep demo responsive
    time.sleep(write_time / 10)

    # Convert time from seconds to milliseconds
    # Example: 6.25 seconds = 6250 milliseconds
    return write_time * 1000


# ============================================================================
# COMPLETE RAID SIMULATION RUNNER
# ============================================================================

def run_raid_simulation():
    """
    Runs a complete RAID simulation for multiple configurations.
    
    This function:
    1. Simulates RAID 0, RAID 1, and RAID 5 operations
    2. Measures read and write performance
    3. Generates random IOPS values
    4. Calculates storage efficiency metrics
    5. Stores results in a DataFrame
    6. Generates statistical summary
    7. Saves reports to CSV files
    
    Returns:
        None (saves results to CSV files in reports folder)
    
    Output Files:
        - raid_report.csv: Detailed simulation results for each RAID level
        - raid_summary.csv: Statistical summary (mean, std, median, etc.)
    
    Workflow:
        1. Initialize empty DataFrame
        2. Loop through each RAID level:
           a. Simulate read operation
           b. Simulate write operation
           c. Generate random IOPS values
           d. Calculate storage metrics
           e. Store results in DataFrame
        3. Generate statistical summary
        4. Save both reports to CSV
    
    Example Output (raid_report.csv):
        raid_level,read_time_ms,write_time_ms,read_iops,write_iops,usable_%,redundancy_%,efficiency_%
        RAID 0,3333.33,4166.67,1200,900,100.0,0.0,100.0
        RAID 1,2777.78,6250.00,1350,750,25.0,75.0,25.0
        RAID 5,3030.30,5416.67,1100,850,75.0,25.0,75.0
    
    Notes:
        - Uses 4 disks for all configurations
        - IOPS values are randomized for realistic variation
        - Can be called multiple times to generate different results
    """
    # Initialize DataFrame as None (will be created on first append)
    df = None
    
    # Number of disks in the RAID array (constant for this simulation)
    num_disks = 4

    # ========================================================================
    # MAIN SIMULATION LOOP
    # ========================================================================
    
    # Loop through each RAID level we want to test
    for raid_level in ["RAID 0", "RAID 1", "RAID 5"]:
        
        # ====================================================================
        # SIMULATE OPERATIONS
        # ====================================================================
        
        # Simulate read operation and get time in milliseconds
        read_ms = simulate_raid_read(raid_level)
        
        # Simulate write operation and get time in milliseconds
        write_ms = simulate_raid_write(raid_level)
        
        # ====================================================================
        # GENERATE RANDOM PERFORMANCE METRICS
        # ====================================================================
        
        # Generate random IOPS (Input/Output Operations Per Second)
        # Read IOPS: Random value between 800 and 1500
        # Higher IOPS = better performance
        read_iops = random.randint(800, 1500)
        
        # Write IOPS: Random value between 500 and 1200
        # Typically lower than read IOPS for most storage systems
        write_iops = random.randint(500, 1200)
        
        # ====================================================================
        # CALCULATE STORAGE METRICS
        # ====================================================================
        
        # Calculate usable capacity percentage
        # Example: RAID 5 with 4 disks = 75% usable
        usable_pct = usable_capacity_percent(num_disks, raid_level)
        
        # Calculate redundancy overhead percentage
        # Example: RAID 5 with 4 disks = 25% redundancy
        redundancy_pct = redundancy_percent(num_disks, raid_level)
        
        # Calculate space efficiency ratio and convert to percentage
        # Example: RAID 5 with 4 disks = 0.75 * 100 = 75%
        efficiency_pct = space_efficiency(num_disks, raid_level) * 100
        
        # ====================================================================
        # STORE RESULTS
        # ====================================================================
        
        # Create dictionary with all simulation results
        run_info = {
            "raid_level": raid_level,         # RAID configuration
            "read_time_ms": read_ms,          # Read time in milliseconds
            "write_time_ms": write_ms,        # Write time in milliseconds
            "read_iops": read_iops,           # Random read IOPS
            "write_iops": write_iops,         # Random write IOPS
            "usable_%": usable_pct,           # Usable capacity percentage
            "redundancy_%": redundancy_pct,   # Redundancy overhead percentage
            "efficiency_%": efficiency_pct    # Space efficiency percentage
        }

        # Append this run's results to the DataFrame
        # First iteration: df is None, creates new DataFrame
        # Subsequent iterations: appends to existing DataFrame
        df = append_run(df, run_info)

    # ========================================================================
    # GENERATE STATISTICAL SUMMARY
    # ========================================================================
    
    # Calculate summary statistics for all performance metrics
    # Computes: mean, std, median, min, max, variance
    stats = summary_statistics(df)
    
    # ========================================================================
    # SAVE RESULTS TO CSV FILES
    # ========================================================================
    
    # Save detailed simulation results
    # File: reports/raid_report.csv
    save_report_csv(df, "raid_report.csv")

    # Save statistical summary
    # File: reports/raid_summary.csv
    save_report_csv(stats, "raid_summary.csv")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Entry point when script is run directly.
    
    This block only executes when you run:
        python Raid_Simulation.py
    
    It does NOT execute when this module is imported by another script.
    
    Execution Flow:
        1. Run complete simulation for all RAID levels
        2. Generate and save reports
        3. Print success message
    
    Expected Output:
        Created folder: reports  (if folder doesn't exist)
        The Report saved to reports/raid_report.csv
        The Report saved to reports/raid_summary.csv
        All RAID operations completed successfully!
    """
    # Run the complete simulation
    run_raid_simulation()
    
    # Print success message
    print("All RAID operations completed successfully!")


# ============================================================================
# USAGE EXAMPLES AND NOTES
# ============================================================================

"""
Standalone Usage:
    $ python Raid_Simulation.py
    
    This will:
    - Simulate RAID 0, 1, and 5
    - Create reports folder
    - Generate two CSV files with results

Integration Usage:
    from Raid_Simulation import simulate_raid_read, simulate_raid_write
    
    # Simulate specific operations
    read_time = simulate_raid_read("RAID 5")
    write_time = simulate_raid_write("RAID 5")
    total_time = read_time + write_time

Customization:
    To change simulation parameters, modify the constants:
    - BASE_READ_SPEED: Adjust for faster/slower disks
    - BASE_WRITE_SPEED: Adjust for faster/slower disks
    - TEST_FILE_SIZE_MB: Simulate larger/smaller files
    - num_disks in run_raid_simulation(): Test with more/fewer disks

Performance Notes:
    - Actual times include artificial delays (sleep)
    - Remove sleep() calls for instant results
    - IOPS values are randomized for variability
    - Real-world performance varies based on:
      * Hardware (HDD vs SSD vs NVMe)
      * RAID controller quality
      * File system and OS caching
      * Network overhead (for NAS/SAN)

Statistical Analysis:
    The summary statistics file shows:
    - mean: Average performance across all RAID levels
    - std: How much performance varies
    - median: Middle value (less affected by outliers)
    - min/max: Best and worst case performance
    - variance: Squared standard deviation

Extensions:
    This module can be extended to:
    - Support RAID 6, RAID 10, RAID 50, etc.
    - Simulate disk failures and rebuild times
    - Model degraded array performance
    - Add network latency for NAS simulations
    - Simulate different file sizes and patterns
    - Add caching effects
"""
