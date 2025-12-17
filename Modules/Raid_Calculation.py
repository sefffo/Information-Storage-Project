#Saif and azoz  (Dead Line : Monday )
"""
raid_calculations.py
Implements RAID calculation functions for performance metrics and capacity analysis.
Functions for Idea 5 (Multimedia Storage Performance Simulator):
- usable_capacity_percent(num_disks, raid_level) -> float
- redundancy_percent(num_disks, raid_level) -> float
- space_efficiency(num_disks, raid_level) -> float
- calculate_storage_overhead(total_bytes, raid_level, num_disks) -> dict
- estimate_access_time(file_size_bytes, num_disks, raid_level, base_transfer_rate_mbps=100) -> float
"""
import math
def usable_capacity_percent(num_disks, raid_level):
    """
    Calculate usable capacity as percentage of raw capacity.
    
    Args:
        num_disks: Number of disks in array
        raid_level: RAID level string ("RAID 0", "RAID 1", "RAID 5")
    
    Returns:
        Percentage of usable capacity (0-100)
    """
    if num_disks < 2:
        raise ValueError("Number of disks must be at least 2")
    
    if raid_level == "RAID 0":
        return 100.0  # All capacity is usable
    elif raid_level == "RAID 1":
        return 100.0 / num_disks  # Only 1/n is usable (mirroring)
    elif raid_level == "RAID 5":
        if num_disks < 3:
            raise ValueError("RAID 5 requires at least 3 disks")
        return ((num_disks - 1) / num_disks) * 100.0  # One disk worth for parity
    else:
        raise ValueError(f"Unsupported RAID level: {raid_level}")


def redundancy_percent(num_disks, raid_level):
    """
    Calculate redundancy overhead as percentage of total capacity.
    to get the redundancy percent, we just subtract usable from 100.
    Args:
        num_disks: Number of disks in array
        raid_level: RAID level string ("RAID 0", "RAID 1", "RAID 5")
    Returns:
        Percentage of capacity used for redundancy (0-100)
    """
    return 100.0 - usable_capacity_percent(num_disks, raid_level)


def space_efficiency(num_disks, raid_level):
    """
    Calculate space efficiency ratio (usable / raw).
    tshl 3lina fe el calcs di 3ashan n3rf el efficiency bta3t el storage.
    Returns:
        Efficiency ratio (0.0-1.0)
    """
    return usable_capacity_percent(num_disks, raid_level) / 100.0


def calculate_storage_overhead(total_bytes, raid_level, num_disks):
    """
    Calculate detailed storage breakdown for given data size.
    
    Args:
        total_bytes: Total size of data to store
        raid_level: RAID level string
        num_disks: Number of disks
    
    Returns:
        Dictionary with:
        - usable_bytes: Data that can be stored
        - parity_bytes: Space used for parity
        - mirror_bytes: Space used for mirroring
        - total_required_bytes: Total raw storage needed
        - efficiency_ratio: Usable/total ratio
    """
    efficiency = space_efficiency(num_disks, raid_level)
    
    if raid_level == "RAID 0":
        return {
            "usable_bytes": total_bytes,
            "parity_bytes": 0,
            "mirror_bytes": 0,
            "total_required_bytes": total_bytes,
            "efficiency_ratio": 1.0
        }
    elif raid_level == "RAID 1":
        mirror_bytes = total_bytes * (num_disks - 1)
        return {
            "usable_bytes": total_bytes,
            "parity_bytes": 0,
            "mirror_bytes": mirror_bytes,
            "total_required_bytes": total_bytes * num_disks,
            "efficiency_ratio": efficiency
        }
    elif raid_level == "RAID 5":
        parity_bytes = total_bytes / (num_disks - 1)
        return {
            "usable_bytes": total_bytes,
            "parity_bytes": parity_bytes,
            "mirror_bytes": 0,
            "total_required_bytes": total_bytes + parity_bytes,
            "efficiency_ratio": efficiency
        }
    else:
        raise ValueError(f"Unsupported RAID level: {raid_level}")


def estimate_access_time(file_size_bytes, num_disks, raid_level, base_transfer_rate_mbps=100):
    """
    Estimate access time for reading/writing files based on RAID level.
    Simplified model considering parallelism and overhead.
    
    Args:
        file_size_bytes: Size of file
        num_disks: Number of disks
        raid_level: RAID level string
        base_transfer_rate_mbps: Base transfer rate per disk (MB/s)
    
    Returns:
        Estimated time in seconds
    """
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if raid_level == "RAID 0":
        # Parallel striping across all disks
        effective_rate = base_transfer_rate_mbps * num_disks
        return file_size_mb / effective_rate
    
    elif raid_level == "RAID 1":
        # Write to all disks (parallel), but limited by slowest
        # Read can be parallel from any disk
        # Use average: (write_time + read_time) / 2
        write_time = file_size_mb / base_transfer_rate_mbps  # All writes happen in parallel
        read_time = file_size_mb / (base_transfer_rate_mbps * num_disks)  # Can read from any
        return (write_time + read_time) / 2
    
    elif raid_level == "RAID 5":
        # Striping across (n-1) data disks with parity overhead
        data_disks = num_disks - 1
        effective_rate = base_transfer_rate_mbps * data_disks * 0.85  # 15% parity overhead
        return file_size_mb / effective_rate
    
    else:
        # Fallback: single disk speed
        return file_size_mb / base_transfer_rate_mbps


def calculate_parallel_speedup(num_disks, raid_level):
    """
    Calculate theoretical speedup factor from parallelism.
    
    Returns:
        Speedup multiplier compared to single disk
    """
    if raid_level == "RAID 0":
        return num_disks  # Perfect parallelism
    elif raid_level == "RAID 1":
        return num_disks * 0.5  # Can parallelize reads, not writes
    elif raid_level == "RAID 5":
        return (num_disks - 1) * 0.85  # (n-1) data disks with parity overhead
    else:
        return 1.0


def fault_tolerance_level(raid_level, num_disks=None):
    """
    Return number of disk failures that can be tolerated.
    
    Returns:
        Integer number of disk failures survivable
    """
    if raid_level == "RAID 0":
        return 0  # No fault tolerance
    elif raid_level == "RAID 1":
        return num_disks - 1 if num_disks else 1  # Can lose all but one
    elif raid_level == "RAID 5":
        return 1  # Can lose one disk
    else:
        return 0


def calculate_capacity_breakdown_dict(num_disks, raid_level):
    """
    Calculate capacity breakdown for visualization.
    
    Returns:
        Dictionary with 'usable', 'parity', 'mirror' disk counts
    """
    if raid_level == "RAID 0":
        return {"usable": num_disks, "parity": 0, "mirror": 0}
    elif raid_level == "RAID 1":
        return {"usable": 1, "parity": 0, "mirror": num_disks - 1}
    elif raid_level == "RAID 5":
        return {"usable": num_disks - 1, "parity": 1, "mirror": 0}
    else:
        return {"usable": num_disks, "parity": 0, "mirror": 0}


def compare_raid_efficiency(num_disks, raid_levels=None):
    """
    Compare efficiency metrics across multiple RAID levels.
    
    Args:
        num_disks: Number of disks
        raid_levels: List of RAID level strings (default: ["RAID 0", "RAID 1", "RAID 5"])
    
    Returns:
        Dictionary mapping RAID level to efficiency metrics
    """
    if raid_levels is None:
        raid_levels = ["RAID 0", "RAID 1", "RAID 5"]
    
    comparison = {}
    for raid in raid_levels:
        try:
            comparison[raid] = {
                "usable_percent": usable_capacity_percent(num_disks, raid),
                "redundancy_percent": redundancy_percent(num_disks, raid),
                "efficiency_ratio": space_efficiency(num_disks, raid),
                "speedup_factor": calculate_parallel_speedup(num_disks, raid),
                "fault_tolerance": fault_tolerance_level(raid, num_disks)
            }
        except ValueError as e:
            comparison[raid] = {"error": str(e)}
    
    return comparison
