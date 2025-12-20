# Azoz and Saif (Dead Line : Monday )

# This file simulates RAID performance (read/write)
# and stores the results for analysis.
# 
# Dependencies: Requires Disk_Performance.py for service time and IOPS calculations
import time

# Import disk performance functions (REQUIRED - from sec-2-1.pdf)
from Disk_Performance import (
    calculate_service_time,   # Calculates disk service time (Ts)
    calculate_iops            # Calculates IOPS from service time
)

# Import RAID calculation functions (from sec-5-1.pdf)
from Raid_Calculation import (
    usable_capacity_percent,      # Calculates usable storage percentage
    redundancy_percent,           # Calculates redundancy percentage
    space_efficiency,             # Calculates space efficiency
    get_write_penalty,            # Gets write penalty for RAID level
    calculate_disk_load_iops      # Calculates disk load with write penalty
)

# Import data analysis utilities
from Data_Analysis import (
    append_run,        # Adds a new simulation run to a DataFrame
    save_report_csv,   # Saves results to CSV file
    summary_statistics # Generates statistical summary
)


# ============================================================================
# DISK SPECIFICATIONS
# ============================================================================

def get_disk_specs():
    """
    Returns standard disk specifications used throughout the simulation.
    These values match the examples in sec-2-1.pdf (slides 13-16).
    
    Returns:
        Dictionary with disk specifications
    """
    return {
        "seek_time_ms": 5.0,           # Average seek time (milliseconds)
        "rpm": 15000,                   # Disk rotation speed (15K RPM enterprise)
        "transfer_rate_mbps": 40,      # Data transfer rate (MB/s)
        "capacity_gb": 100,             # Disk capacity (GB)
        "io_size_kb": 4,                # Typical I/O block size (KB)
        "base_read_speed_mbps": 150,   # Base sequential read speed (MB/s)
        "base_write_speed_mbps": 120   # Base sequential write speed (MB/s)
    }


def calculate_base_iops(utilization=0.7):
    """
    Calculate base IOPS per disk using formulas from sec-2-1.pdf.
    
    This function calculates the actual IOPS a single disk can handle
    based on its service time, using the proper formulas.
    
    Args:
        utilization: Disk utilization factor (0.7 = 70% recommended)
    
    Returns:
        IOPS that a single disk can service
    
    Formula:
        1. Ts = seek_time + (0.5 / (rpm/60)) + (block_size / transfer_rate)
        2. IOPS = utilization × (1 / (Ts × 0.001))
    """
    specs = get_disk_specs()
    
    # Calculate service time using formula from sec-2-1.pdf slide 5
    service_time = calculate_service_time(
        seek_time_ms=specs["seek_time_ms"],
        disk_rpm=specs["rpm"],
        data_block_size_kb=specs["io_size_kb"],
        transfer_rate_mbps=specs["transfer_rate_mbps"]
    )
    
    # Calculate IOPS using formula from sec-2-1.pdf slide 6
    iops = calculate_iops(service_time, utilization=utilization)
    
    return iops


# ============================================================================
# RAID PERFORMANCE SIMULATION
# ============================================================================

def simulate_raid_read(raid_level, num_disks=4):
    """
    Simulates RAID read operation time.
    
    Uses disk specifications and RAID parallelism to estimate read time.
    Read operations can often parallelize across multiple disks.
    
    Args:
        raid_level: RAID level string ("RAID 0", "RAID 1", "RAID 5")
        num_disks: Number of disks in array
    
    Returns:
        Read time in milliseconds for 500 MB
    """
    specs = get_disk_specs()
    base_speed_mbps = specs["base_read_speed_mbps"]
    
    # RAID 0: Perfect striping parallelism
    if raid_level == "RAID 0":
        # Read speed scales linearly with number of disks
        effective_speed = base_speed_mbps * num_disks
    
    # RAID 1: Can read from any mirror (parallel reads possible)
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
    Simulates RAID write operation time using write penalty.
    
    Uses write penalty formula from sec-5-1.pdf slides 21-22.
    Write operations have overhead due to mirroring or parity calculations.
    
    Args:
        raid_level: RAID level string
        num_disks: Number of disks in array
    
    Returns:
        Write time in milliseconds for 500 MB
    """
    specs = get_disk_specs()
    base_speed_mbps = specs["base_write_speed_mbps"]
    
    # Get write penalty from formula (sec-5-1.pdf slide 21)
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
        # Must: read old data, read old parity, write new data, write new parity
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
    Calculate IOPS for RAID array using formulas from sec-2-1.pdf and sec-5-1.pdf.
    
    This function combines:
    1. Base disk IOPS (from service time formula - sec-2-1.pdf)
    2. RAID parallelism factors
    3. Write penalty overhead (sec-5-1.pdf)
    
    Args:
        raid_level: RAID level string
        num_disks: Number of disks in array
        utilization: Disk utilization factor (0.7 = 70% recommended)
    
    Returns:
        Dictionary with:
        - read_iops: Total read IOPS capacity
        - write_iops: Total write IOPS capacity
        - base_iops_per_disk: IOPS per single disk (from formula)
    """
    # Calculate base IOPS per disk using service time formula
    base_iops = calculate_base_iops(utilization)
    
    # Adjust for RAID level parallelism and write penalty
    if raid_level == "RAID 0":
        # Perfect parallelism for reads and writes
        read_iops = base_iops * num_disks
        write_iops = base_iops * num_disks
    
    elif raid_level == "RAID 1":
        # Reads can parallelize, writes limited by mirroring
        # Write penalty = 2 means each logical write = 2 physical writes
        read_iops = base_iops * num_disks * 0.8  # 80% read efficiency
        write_iops = (base_iops * num_disks) / get_write_penalty(raid_level)
    
    elif raid_level == "RAID 5":
        # Striping across n-1 disks with parity overhead
        # Write penalty = 4 (read data, read parity, write data, write parity)
        data_disks = num_disks - 1
        read_iops = base_iops * data_disks * 0.9  # 90% read efficiency
        # Write IOPS reduced by penalty factor
        write_iops = (base_iops * data_disks) / (get_write_penalty(raid_level) / 4.0)
    
    else:
        read_iops = base_iops
        write_iops = base_iops
    
    return {
        "read_iops": int(read_iops),
        "write_iops": int(write_iops),
        "base_iops_per_disk": int(base_iops)
    }


def calculate_disk_load_for_workload(total_iops, read_percent, write_percent, raid_level):
    """
    Calculate actual disk load using formula from sec-5-1.pdf slide 22.
    
    Formula:
    Disk Load (IOPS) = (Total IOPS × Read %) + (Total IOPS × Write % × Write Penalty)
    
    Args:
        total_iops: Total IOPS from application
        read_percent: Percentage of reads (0-100)
        write_percent: Percentage of writes (0-100)
        raid_level: RAID level string
    
    Returns:
        Actual disk load in IOPS (accounts for write penalty)
    
    Example from sec-5-1.pdf slide 25:
        - 400 IOPS total, 75% read, 25% write, RAID 5
        - Disk Load = 400 × 0.75 + 400 × 0.25 × 4 = 300 + 400 = 700 IOPS
    """
    return calculate_disk_load_iops(total_iops, read_percent, write_percent, raid_level)


# ============================================================================
# MAIN SIMULATION RUNNER
# ============================================================================

def run_raid_simulation(num_disks=4, workload_iops=1000, read_percent=70, write_percent=30):
    """
    Runs comprehensive RAID simulation for multiple RAID levels.
    
    All calculations use proper formulas from course materials:
    - Service time and IOPS from sec-2-1.pdf
    - RAID capacity and write penalty from sec-5-1.pdf
    
    Args:
        num_disks: Number of disks in RAID array
        workload_iops: Application IOPS workload
        read_percent: Percentage of read operations (0-100)
        write_percent: Percentage of write operations (0-100)
    
    Returns:
        DataFrame with simulation results
    """
    df = None  # DataFrame to store simulation runs
    
    print(f"\n{'='*60}")
    print("RAID Performance Simulation")
    print(f"{'='*60}")
    print(f"Configuration: {num_disks} disks")
    print(f"Workload: {workload_iops} IOPS ({read_percent}% read, {write_percent}% write)")
    print(f"{'='*60}\n")
    
    # Loop through RAID levels
    for raid_level in ["RAID 0", "RAID 1", "RAID 5"]:
        print(f"Simulating {raid_level}...")
        
        # Calculate IOPS using formulas (not random!)
        iops_results = calculate_raid_iops(raid_level, num_disks)
        
        # Simulate read and write times
        read_time = simulate_raid_read(raid_level, num_disks)
        write_time = simulate_raid_write(raid_level, num_disks)
        
        # Calculate disk load with write penalty
        disk_load = calculate_disk_load_for_workload(
            workload_iops, read_percent, write_percent, raid_level
        )
        
        # Store simulation results
        run_info = {
            "raid_level": raid_level,
            "num_disks": num_disks,
            
            # Performance times
            "read_time_ms": round(read_time, 2),
            "write_time_ms": round(write_time, 2),
            "total_time_ms": round(read_time + write_time, 2),
            
            # IOPS from formulas (sec-2-1.pdf)
            "base_iops_per_disk": iops_results["base_iops_per_disk"],
            "read_iops": iops_results["read_iops"],
            "write_iops": iops_results["write_iops"],
            "total_iops": iops_results["read_iops"] + iops_results["write_iops"],
            
            # Write penalty and disk load (sec-5-1.pdf)
            "write_penalty": get_write_penalty(raid_level),
            "disk_load_iops": int(disk_load),
            
            # Storage capacity metrics
            "usable_%": round(usable_capacity_percent(num_disks, raid_level), 1),
            "redundancy_%": round(redundancy_percent(num_disks, raid_level), 1),
            "efficiency_%": round(space_efficiency(num_disks, raid_level) * 100, 1)
        }
        
        # Append results to DataFrame
        df = append_run(df, run_info)
    
    # Save reports
    save_report_csv(df, "raid_report.csv")
    
    stats = summary_statistics(df)
    save_report_csv(stats, "raid_summary.csv")
    
    # Print results
    print(f"\n{'='*60}")
    print("Simulation Results")
    print(f"{'='*60}")
    print(df.to_string(index=False))
    print(f"\n{'='*60}")
    print("Statistical Summary")
    print(f"{'='*60}")
    print(stats.to_string())
    print(f"\n✅ Reports saved to: raid_report.csv and raid_summary.csv")
    
    return df


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run simulation with default parameters
    run_raid_simulation(
        num_disks=4,
        workload_iops=1000,
        read_percent=70,
        write_percent=30
    )
    print("\n✅ All RAID operations completed successfully!")
