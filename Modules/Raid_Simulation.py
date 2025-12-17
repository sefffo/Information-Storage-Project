# Azoz and Saif (Dead Line : Monday )
# This file simulates RAID performance (read/write)
# and stores the results for analysis.
import time
import random

# Import RAID calculation functions
from Raid_Calculation import (
    usable_capacity_percent,   # Calculates usable storage percentage
    redundancy_percent,        # Calculates redundancy percentage
    space_efficiency           # Calculates space efficiency
)

# Import data analysis utilities
from Data_Analysis import (
    append_run,        # Adds a new simulation run to a DataFrame
    save_report_csv,   # Saves results to CSV file
    summary_statistics # Generates statistical summary
)


def simulate_raid_read(raid_level):
    """
    Simulates RAID read operation time.
    Returns read time in milliseconds.
    """

    base_speed = 150  # Base read speed in MB/s

    # RAID 1 has faster reads due to mirroring
    if raid_level == "RAID 1":
        base_speed *= 1.2

    # RAID 5 has slightly improved read speed
    elif raid_level == "RAID 5":
        base_speed *= 1.1

    # Calculate read time for 500 MB
    read_time = 500 / base_speed

    # Artificial delay to simulate real I/O
    time.sleep(read_time / 10)

    # Return time in milliseconds
    return read_time * 1000


def simulate_raid_write(raid_level):
    """
    Simulates RAID write operation time.
    Returns write time in milliseconds.
    """

    base_speed = 120  # Base write speed in MB/s
    overhead = 1.0    # Write overhead factor

    # RAID 1 has high write overhead (mirroring)
    if raid_level == "RAID 1":
        overhead = 1.5

    # RAID 5 has parity calculation overhead
    elif raid_level == "RAID 5":
        overhead = 1.3

    # Calculate write time for 500 MB
    write_time = (500 / base_speed) * overhead

    # Artificial delay to simulate disk writes
    time.sleep(write_time / 10)

    # Return time in milliseconds
    return write_time * 1000


def run_raid_simulation():
    """
    Runs RAID simulation for RAID 0, RAID 1, and RAID 5
    Collects performance and storage metrics
    """

    df = None          # DataFrame to store simulation runs
    num_disks = 4      # Number of disks in the RAID array

    # Loop through RAID levels
    for raid_level in ["RAID 0", "RAID 1", "RAID 5"]:

        # Store simulation results in dictionary
        run_info = {
            "raid_level": raid_level,
            "read_time_ms": simulate_raid_read(raid_level),
            "write_time_ms": simulate_raid_write(raid_level),

            # Random IOPS values to simulate performance
            "read_iops": random.randint(800, 1500),
            "write_iops": random.randint(500, 1200),

            # Storage-related calculations
            "usable_%": usable_capacity_percent(num_disks, raid_level),
            "redundancy_%": redundancy_percent(num_disks, raid_level),
            "efficiency_%": space_efficiency(num_disks, raid_level)
        }

        # Append results to DataFrame
        df = append_run(df, run_info)

    # Save full simulation results
    save_report_csv(df, "raid_report.csv")

    # Generate and save statistical summary
    stats = summary_statistics(df)
    save_report_csv(stats, "raid_summary.csv")


# Entry point of the program
if __name__ == "__main__":
    run_raid_simulation()
    print("All RAID operations completed successfully!")
