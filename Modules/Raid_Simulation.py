# Azoz and Saif (Dead Line : Monday )
# This file simulates RAID performance (read/write)
# and stores the results for analysis.
import time

# Import RAID calculation functions
from Raid_Calculation import (
    usable_capacity_percent,      # Calculates usable storage percentage
    redundancy_percent,           # Calculates redundancy percentage
    space_efficiency,             # Calculates space efficiency
    get_write_penalty,            # Gets write penalty for RAID level
    calculate_disk_load_iops      # Calculates disk load with write penalty
)

# Import disk performance functions
try:
    from Disk_Performance import (
        calculate_service_time,   # Calculates disk service time
        calculate_iops            # Calculates IOPS from service time
    )
    DISK_PERF_AVAILABLE = True
except ImportError:
    DISK_PERF_AVAILABLE = False

# Import data analysis utilities
from Data_Analysis import (
    append_run,        # Adds a new simulation run to a DataFrame
    save_report_csv,   # Saves results to CSV file
    summary_statistics # Generates statistical summary
)


def simulate_raid_read(raid_level, num_disks=4):
    """
    Simulates RAID read operation time using proper formulas.
    Uses disk performance calculations from sec-2-1.pdf.
    
    Args:
        raid_level: RAID level string
        num_disks: Number of disks in array
    
    Returns:
        Read time in milliseconds
    """
    # Base disk specifications (typical 15K RPM enterprise drive)
    base_speed_mbps = 150  # Base read speed in MB/s
    
    # RAID 0: Perfect striping parallelism
    if raid_level == "RAID 0":
        # Read speed scales linearly with number of disks
        effective_speed = base_speed_mbps * num_disks
    
    # RAID 1: Can read from any mirror (parallel reads)
    elif raid_level == "RAID 1":
        # Can read from multiple mirrors simultaneously
        effective_speed = base_speed_mbps * num_disks * 0.8  # 80% efficiency
    
    # RAID 5: Striping across (n-1) data disks
    elif raid_level == "RAID 5":
        # Read from n-1 data disks (one disk has parity)
        data_disks = num_disks - 1
        effective_speed = base_speed_mbps * data_disks * 0.9  # 90% efficiency
    
    else:
        effective_speed = base_speed_mbps
    
    # Calculate read time for 500 MB
    file_size_mb = 500
    read_time_s = file_size_mb / effective_speed
    
    # Artificial delay to simulate real I/O
    time.sleep(read_time_s / 10)
    
    # Return time in milliseconds
    return read_time_s * 1000


def simulate_raid_write(raid_level, num_disks=4):
    """
    Simulates RAID write operation time using write penalty formula.
    Uses formulas from sec-5-1.pdf slides 21-22.
    
    Args:
        raid_level: RAID level string
        num_disks: Number of disks in array
    
    Returns:
        Write time in milliseconds
    """
    # Base disk specifications
    base_speed_mbps = 120  # Base write speed in MB/s
    
    # Get write penalty from proper formula (sec-5-1.pdf)
    write_penalty = get_write_penalty(raid_level)
    
    # RAID 0: Direct striping, no penalty
    if raid_level == "RAID 0":
        effective_speed = base_speed_mbps * num_disks
        penalty_factor = 1.0
    
    # RAID 1: Write to all mirrors (write penalty = 2)
    elif raid_level == "RAID 1":
        # Must write to all mirrors, but happens in parallel
        effective_speed = base_speed_mbps
        penalty_factor = write_penalty  # 2.0 from formula
    
    # RAID 5: Read-modify-write for parity (write penalty = 4)
    elif raid_level == "RAID 5":
        # Must read old data, read old parity, write new data, write new parity
        data_disks = num_disks - 1
        effective_speed = base_speed_mbps * data_disks
        penalty_factor = write_penalty / 4.0  # Normalize: 4/4 = 1.0 base overhead
    
    else:
        effective_speed = base_speed_mbps
        penalty_factor = 1.0
    
    # Calculate write time for 500 MB with penalty
    file_size_mb = 500
    write_time_s = (file_size_mb / effective_speed) * penalty_factor
    
    # Artificial delay to simulate disk writes
    time.sleep(write_time_s / 10)
    
    # Return time in milliseconds
    return write_time_s * 1000


def calculate_raid_iops(raid_level, num_disks=4, utilization=0.7):
    """
    Calculate IOPS for RAID array using proper disk performance formulas.
    Uses formulas from sec-2-1.pdf and sec-5-1.pdf.
    
    Args:
        raid_level: RAID level string
        num_disks: Number of disks in array
        utilization: Disk utilization factor (0.7 for 70% recommended)
    
    Returns:
        Dictionary with read_iops and write_iops
    """
    if DISK_PERF_AVAILABLE:
        # Use actual disk performance calculations
        # Typical 15K RPM disk specs
        seek_time_ms = 4.0
        disk_rpm = 15000
        block_size_kb = 4
        transfer_rate_mbps = 40
        
        # Calculate service time
        service_time = calculate_service_time(
            seek_time_ms, disk_rpm, block_size_kb, transfer_rate_mbps
        )
        
        # Calculate base IOPS per disk
        base_iops = calculate_iops(service_time, utilization)
        
        # Adjust for RAID level parallelism
        if raid_level == "RAID 0":
            # Perfect parallelism for reads and writes
            read_iops = base_iops * num_disks
            write_iops = base_iops * num_disks
        
        elif raid_level == "RAID 1":
            # Reads can parallelize, writes limited by mirroring
            read_iops = base_iops * num_disks * 0.8
            write_iops = base_iops * num_disks / get_write_penalty(raid_level)
        
        elif raid_level == "RAID 5":
            # Striping across n-1 disks with parity overhead
            data_disks = num_disks - 1
            read_iops = base_iops * data_disks * 0.9
            write_iops = base_iops * data_disks / (get_write_penalty(raid_level) / 4.0)
        
        else:
            read_iops = base_iops
            write_iops = base_iops
    
    else:
        # Fallback: Use simplified estimates
        base_iops = 140  # Typical 15K RPM disk at 70% utilization
        
        if raid_level == "RAID 0":
            read_iops = base_iops * num_disks
            write_iops = base_iops * num_disks
        elif raid_level == "RAID 1":
            read_iops = base_iops * num_disks * 0.8
            write_iops = base_iops * num_disks * 0.5
        elif raid_level == "RAID 5":
            read_iops = base_iops * (num_disks - 1) * 0.9
            write_iops = base_iops * (num_disks - 1) * 0.4
        else:
            read_iops = base_iops
            write_iops = base_iops
    
    return {
        "read_iops": int(read_iops),
        "write_iops": int(write_iops)
    }


def calculate_disk_load_for_workload(total_iops, read_percent, write_percent, raid_level):
    """
    Calculate actual disk load using the formula from sec-5-1.pdf slide 22.
    
    This is the key formula:
    Disk Load = (Total IOPS × Read %) + (Total IOPS × Write % × Write Penalty)
    
    Args:
        total_iops: Total IOPS from application
        read_percent: Percentage of reads (0-100)
        write_percent: Percentage of writes (0-100)
        raid_level: RAID level string
    
    Returns:
        Actual disk load in IOPS
    """
    return calculate_disk_load_iops(total_iops, read_percent, write_percent, raid_level)


def run_raid_simulation():
    """
    Runs RAID simulation for RAID 0, RAID 1, and RAID 5
    Collects performance and storage metrics using proper formulas
    """
    df = None          # DataFrame to store simulation runs
    num_disks = 4      # Number of disks in the RAID array
    
    # Loop through RAID levels
    for raid_level in ["RAID 0", "RAID 1", "RAID 5"]:
        # Calculate IOPS using proper formulas
        iops_results = calculate_raid_iops(raid_level, num_disks)
        
        # Simulate read and write times
        read_time = simulate_raid_read(raid_level, num_disks)
        write_time = simulate_raid_write(raid_level, num_disks)
        
        # Calculate disk load for a typical workload (70% read, 30% write)
        typical_iops = 1000  # Assume 1000 IOPS workload
        disk_load = calculate_disk_load_for_workload(typical_iops, 70, 30, raid_level)
        
        # Store simulation results in dictionary
        run_info = {
            "raid_level": raid_level,
            "num_disks": num_disks,
            "read_time_ms": read_time,
            "write_time_ms": write_time,
            "total_time_ms": read_time + write_time,
            
            # IOPS calculated from formulas (not random!)
            "read_iops": iops_results["read_iops"],
            "write_iops": iops_results["write_iops"],
            "total_iops": iops_results["read_iops"] + iops_results["write_iops"],
            
            # Disk load with write penalty
            "disk_load_iops": disk_load,
            "write_penalty": get_write_penalty(raid_level),
            
            # Storage-related calculations
            "usable_%": usable_capacity_percent(num_disks, raid_level),
            "redundancy_%": redundancy_percent(num_disks, raid_level),
            "efficiency_%": space_efficiency(num_disks, raid_level) * 100
        }
        
        # Append results to DataFrame
        df = append_run(df, run_info)
    
    # Save full simulation results
    save_report_csv(df, "raid_report.csv")
    
    # Generate and save statistical summary
    stats = summary_statistics(df)
    save_report_csv(stats, "raid_summary.csv")
    
    # Print summary
    print("\n" + "=" * 60)
    print("RAID Simulation Results")
    print("=" * 60)
    print(df.to_string(index=False))
    print("\n" + "=" * 60)
    print("Statistical Summary")
    print("=" * 60)
    print(stats.to_string())


# Entry point of the program
if __name__ == "__main__":
    run_raid_simulation()
    print("\n✅ All RAID operations completed successfully!")
    print("📊 Reports saved to: raid_report.csv and raid_summary.csv")
