#!/usr/bin/env python3
"""
================================================================================
Raid_Calculation.py - RAID Capacity and Performance Calculations
================================================================================

Purpose:
    This module implements mathematical calculations for RAID arrays including:
    - Usable capacity calculations
    - Redundancy overhead analysis
    - Space efficiency ratios
    - Storage overhead breakdown
    - Access time estimation
    - Parallel speedup factors
    - Fault tolerance levels

Authors: Saif and Azoz
Deadline: Monday
Last Updated: December 2024

Supported RAID Levels:
    - RAID 0: Striping (no redundancy, maximum performance)
    - RAID 1: Mirroring (full redundancy, read performance boost)
    - RAID 5: Striping with parity (single disk redundancy)

Key Concepts:
    - Usable Capacity: Amount of actual data that can be stored
    - Redundancy: Extra space used for data protection
    - Efficiency: Ratio of usable space to total raw space
    - IOPS: Input/Output Operations Per Second
    - Parity: Calculated data for error recovery

================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

import math  # Mathematical functions (not currently used but available)

# ============================================================================
# CAPACITY CALCULATION FUNCTIONS
# ============================================================================

def usable_capacity_percent(num_disks, raid_level):
    """
    Calculates the percentage of raw storage capacity that is usable for data.
    
    Different RAID levels have different usable capacity ratios:
    - RAID 0: 100% usable (no redundancy)
    - RAID 1: 1/n usable (mirrored across all disks)
    - RAID 5: (n-1)/n usable (one disk worth for parity)
    
    Args:
        num_disks (int): Number of physical disks in the array.
                        Must be >= 2 for all RAID levels.
                        Must be >= 3 for RAID 5.
        raid_level (str): RAID configuration.
                         Valid values: "RAID 0", "RAID 1", "RAID 5"
    
    Returns:
        float: Percentage of usable capacity (0.0 to 100.0)
    
    Raises:
        ValueError: If num_disks < 2
        ValueError: If RAID 5 and num_disks < 3
        ValueError: If raid_level is not supported
    
    Examples:
        >>> usable_capacity_percent(4, "RAID 0")
        100.0  # All 4 disks usable
        
        >>> usable_capacity_percent(4, "RAID 1")
        25.0  # Only 1 out of 4 disks usable (others are mirrors)
        
        >>> usable_capacity_percent(4, "RAID 5")
        75.0  # 3 out of 4 disks usable (1 for parity)
    
    Real-World Example:
        With 4x 1TB disks (4TB raw):
        - RAID 0: 4TB usable (100%)
        - RAID 1: 1TB usable (25%)
        - RAID 5: 3TB usable (75%)
    """
    # Validate minimum number of disks
    if num_disks < 2:
        raise ValueError("Number of disks must be at least 2")
    
    # Calculate based on RAID level
    if raid_level == "RAID 0":
        # RAID 0: All disks used for data (striping, no redundancy)
        return 100.0
        
    elif raid_level == "RAID 1":
        # RAID 1: Data mirrored across all disks
        # Only 1 disk worth of unique data, rest are copies
        # Formula: (1 / number_of_disks) * 100
        return 100.0 / num_disks
        
    elif raid_level == "RAID 5":
        # RAID 5 requires at least 3 disks
        if num_disks < 3:
            raise ValueError("RAID 5 requires at least 3 disks")
        
        # RAID 5: One disk equivalent used for parity
        # Formula: ((n-1) / n) * 100
        # Example: 4 disks -> (3/4) * 100 = 75%
        return ((num_disks - 1) / num_disks) * 100.0
        
    else:
        # Unsupported RAID level
        raise ValueError(f"Unsupported RAID level: {raid_level}")


def redundancy_percent(num_disks, raid_level):
    """
    Calculates the percentage of capacity used for redundancy/overhead.
    
    This is simply the complement of usable capacity:
    redundancy% = 100% - usable%
    
    Args:
        num_disks (int): Number of disks in the array
        raid_level (str): RAID configuration ("RAID 0", "RAID 1", "RAID 5")
    
    Returns:
        float: Percentage of capacity used for redundancy (0.0 to 100.0)
    
    Examples:
        >>> redundancy_percent(4, "RAID 0")
        0.0  # No redundancy in RAID 0
        
        >>> redundancy_percent(4, "RAID 1")
        75.0  # 75% used for mirroring
        
        >>> redundancy_percent(4, "RAID 5")
        25.0  # 25% used for parity
    
    Use Cases:
        - Cost analysis: How much extra storage do we need?
        - Capacity planning: What's the overhead of data protection?
        - RAID comparison: Which level has lowest overhead?
    """
    # Simply subtract usable capacity from 100%
    return 100.0 - usable_capacity_percent(num_disks, raid_level)


def space_efficiency(num_disks, raid_level):
    """
    Calculates space efficiency as a ratio (usable / total).
    
    This is the same as usable_capacity_percent but returned as a
    decimal ratio (0.0 to 1.0) instead of a percentage.
    
    Args:
        num_disks (int): Number of disks
        raid_level (str): RAID configuration
    
    Returns:
        float: Efficiency ratio (0.0 to 1.0)
               1.0 = 100% efficient (RAID 0)
               0.5 = 50% efficient
               0.25 = 25% efficient
    
    Examples:
        >>> space_efficiency(4, "RAID 0")
        1.0  # 100% efficient
        
        >>> space_efficiency(4, "RAID 1")
        0.25  # 25% efficient
        
        >>> space_efficiency(4, "RAID 5")
        0.75  # 75% efficient
    
    Use in Formulas:
        total_required = data_size / space_efficiency(n, raid)
        
        Example: Store 3TB with RAID 5 (4 disks):
        total_required = 3TB / 0.75 = 4TB raw storage needed
    """
    # Convert percentage to ratio by dividing by 100
    return usable_capacity_percent(num_disks, raid_level) / 100.0


def calculate_storage_overhead(total_bytes, raid_level, num_disks):
    """
    Calculates detailed storage breakdown for a given data size.
    
    This function shows exactly how storage is distributed across
    usable data, parity data, and mirrored copies.
    
    Args:
        total_bytes (int): Size of actual data to store (in bytes)
        raid_level (str): RAID configuration
        num_disks (int): Number of disks in array
    
    Returns:
        dict: Detailed breakdown with keys:
            - usable_bytes (int): Amount of actual data stored
            - parity_bytes (int): Space used for parity information
            - mirror_bytes (int): Space used for mirrored copies
            - total_required_bytes (int): Total raw storage needed
            - efficiency_ratio (float): Usable/total ratio (0.0-1.0)
    
    Examples:
        >>> calculate_storage_overhead(1000, "RAID 0", 4)
        {
            'usable_bytes': 1000,
            'parity_bytes': 0,
            'mirror_bytes': 0,
            'total_required_bytes': 1000,
            'efficiency_ratio': 1.0
        }
        
        >>> calculate_storage_overhead(1000, "RAID 1", 4)
        {
            'usable_bytes': 1000,
            'parity_bytes': 0,
            'mirror_bytes': 3000,  # 3 copies
            'total_required_bytes': 4000,
            'efficiency_ratio': 0.25
        }
        
        >>> calculate_storage_overhead(1000, "RAID 5", 4)
        {
            'usable_bytes': 1000,
            'parity_bytes': 333.33,  # 1/3 of data
            'mirror_bytes': 0,
            'total_required_bytes': 1333.33,
            'efficiency_ratio': 0.75
        }
    
    Real-World Application:
        Use this to calculate disk requirements:
        - Input: 5TB of video files
        - RAID 5 with 6 disks
        - Output: Need 6TB raw storage (5TB data + 1TB parity)
    """
    # Get efficiency ratio for this RAID configuration
    efficiency = space_efficiency(num_disks, raid_level)
    
    if raid_level == "RAID 0":
        # RAID 0: No overhead, all storage is usable
        return {
            "usable_bytes": total_bytes,        # All bytes are usable
            "parity_bytes": 0,                  # No parity in RAID 0
            "mirror_bytes": 0,                  # No mirroring in RAID 0
            "total_required_bytes": total_bytes, # No extra storage needed
            "efficiency_ratio": 1.0             # 100% efficient
        }
        
    elif raid_level == "RAID 1":
        # RAID 1: Data mirrored (num_disks - 1) times
        # If we have 4 disks, data is copied 3 additional times
        mirror_bytes = total_bytes * (num_disks - 1)
        
        return {
            "usable_bytes": total_bytes,              # Original data
            "parity_bytes": 0,                        # No parity in RAID 1
            "mirror_bytes": mirror_bytes,             # Extra copies
            "total_required_bytes": total_bytes * num_disks,  # Total storage
            "efficiency_ratio": efficiency
        }
        
    elif raid_level == "RAID 5":
        # RAID 5: Parity takes 1/(n-1) of data size
        # Formula: parity = data_size / (num_disks - 1)
        # Example: 3TB data, 4 disks -> parity = 3TB / 3 = 1TB
        parity_bytes = total_bytes / (num_disks - 1)
        
        return {
            "usable_bytes": total_bytes,                    # Original data
            "parity_bytes": parity_bytes,                   # Parity overhead
            "mirror_bytes": 0,                              # No mirroring in RAID 5
            "total_required_bytes": total_bytes + parity_bytes,  # Data + parity
            "efficiency_ratio": efficiency
        }
        
    else:
        raise ValueError(f"Unsupported RAID level: {raid_level}")


# ============================================================================
# PERFORMANCE CALCULATION FUNCTIONS
# ============================================================================

def estimate_access_time(file_size_bytes, num_disks, raid_level, 
                        base_transfer_rate_mbps=100):
    """
    Estimates file access time based on RAID configuration.
    
    This is a simplified model that considers:
    - Parallel reading/writing across multiple disks
    - RAID-specific overhead (parity calculation, mirroring)
    - Base transfer rate per disk
    
    Args:
        file_size_bytes (int): Size of file to read/write (bytes)
        num_disks (int): Number of disks in array
        raid_level (str): RAID configuration
        base_transfer_rate_mbps (int): Transfer rate per disk (MB/s)
                                       Default: 100 MB/s
    
    Returns:
        float: Estimated access time in seconds
    
    Performance Characteristics:
        - RAID 0: Fastest (parallel striping)
        - RAID 1: Moderate (parallel reads, sequential writes)
        - RAID 5: Slower (parity calculation overhead)
    
    Examples:
        >>> # 500MB file on RAID 0 with 4 disks
        >>> estimate_access_time(500*1024*1024, 4, "RAID 0")
        1.25  # seconds (500MB / (100MB/s * 4) = 1.25s)
        
        >>> # Same file on RAID 5 with 4 disks
        >>> estimate_access_time(500*1024*1024, 4, "RAID 5")
        1.96  # seconds (slower due to parity overhead)
    
    Notes:
        - This is a theoretical estimate, not real-world measurement
        - Actual times depend on disk speed, controller, cache, etc.
        - Does not account for seek time, latency, or queue depth
    """
    # Convert file size from bytes to megabytes
    # 1 MB = 1024 * 1024 bytes = 1,048,576 bytes
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if raid_level == "RAID 0":
        # RAID 0: Perfect parallel striping across all disks
        # Effective rate = base_rate * number_of_disks
        # Example: 100 MB/s per disk * 4 disks = 400 MB/s total
        effective_rate = base_transfer_rate_mbps * num_disks
        return file_size_mb / effective_rate
    
    elif raid_level == "RAID 1":
        # RAID 1: 
        # - Writes: Must write to all disks (sequential, limited by slowest)
        # - Reads: Can read from any disk (parallel)
        # We average write and read times for this estimate
        
        # Write time: Limited to single disk speed (all disks write in parallel)
        write_time = file_size_mb / base_transfer_rate_mbps
        
        # Read time: Can read from multiple disks simultaneously
        read_time = file_size_mb / (base_transfer_rate_mbps * num_disks)
        
        # Return average of read and write
        return (write_time + read_time) / 2
    
    elif raid_level == "RAID 5":
        # RAID 5: Striping across (n-1) data disks
        # Parity calculation adds ~15% overhead
        data_disks = num_disks - 1
        
        # Effective rate considers parallelism and parity overhead
        # 0.85 = 85% efficiency (15% lost to parity calculation)
        effective_rate = base_transfer_rate_mbps * data_disks * 0.85
        return file_size_mb / effective_rate
    
    else:
        # Fallback: Use single disk speed
        return file_size_mb / base_transfer_rate_mbps


def calculate_parallel_speedup(num_disks, raid_level):
    """
    Calculates theoretical speedup factor from parallel disk operations.
    
    This represents how many times faster the RAID array is compared
    to a single disk, considering the parallelism benefits of each
    RAID level.
    
    Args:
        num_disks (int): Number of disks in array
        raid_level (str): RAID configuration
    
    Returns:
        float: Speedup multiplier relative to single disk
               Example: 4.0 means 4x faster than single disk
    
    Speedup by RAID Level:
        - RAID 0: Perfect speedup (n disks = n times faster)
        - RAID 1: Partial speedup (n disks = n/2 times faster)
        - RAID 5: Good speedup (n disks = (n-1) * 0.85 times faster)
    
    Examples:
        >>> calculate_parallel_speedup(4, "RAID 0")
        4.0  # 4x speedup with 4 disks
        
        >>> calculate_parallel_speedup(4, "RAID 1")
        2.0  # 2x speedup (reads parallel, writes sequential)
        
        >>> calculate_parallel_speedup(4, "RAID 5")
        2.55  # (4-1) * 0.85 = 2.55x speedup
    
    Use Cases:
        - Performance comparison between RAID levels
        - Estimating performance gains from adding disks
        - Capacity vs. performance trade-off analysis
    """
    if raid_level == "RAID 0":
        # RAID 0: Perfect parallelism, all disks contribute to speed
        return num_disks
        
    elif raid_level == "RAID 1":
        # RAID 1: Can parallelize reads, not writes
        # Average speedup is approximately half the disk count
        return num_disks * 0.5
        
    elif raid_level == "RAID 5":
        # RAID 5: (n-1) data disks with 15% parity overhead
        # Formula: (num_disks - 1) * 0.85
        return (num_disks - 1) * 0.85
        
    else:
        # Unknown RAID level: Assume no speedup
        return 1.0


# ============================================================================
# FAULT TOLERANCE AND RELIABILITY
# ============================================================================

def fault_tolerance_level(raid_level, num_disks=None):
    """
    Returns the number of disk failures that can be tolerated.
    
    This indicates how many disks can fail simultaneously before
    data is lost.
    
    Args:
        raid_level (str): RAID configuration
        num_disks (int, optional): Number of disks (needed for RAID 1)
    
    Returns:
        int: Number of disk failures survivable
             0 = No fault tolerance (data loss on any failure)
             1 = Can survive 1 disk failure
             n-1 = Can survive all but one disk failing
    
    Fault Tolerance by RAID Level:
        - RAID 0: 0 (no redundancy, any failure = data loss)
        - RAID 1: n-1 (can lose all but one disk)
        - RAID 5: 1 (can lose exactly one disk)
    
    Examples:
        >>> fault_tolerance_level("RAID 0")
        0  # No fault tolerance
        
        >>> fault_tolerance_level("RAID 1", num_disks=4)
        3  # Can lose 3 out of 4 disks
        
        >>> fault_tolerance_level("RAID 5")
        1  # Can lose 1 disk
    
    Important Notes:
        - RAID 0: High performance, but dangerous (no redundancy)
        - RAID 1: Excellent fault tolerance, but expensive
        - RAID 5: Good balance of performance, capacity, and protection
    """
    if raid_level == "RAID 0":
        # RAID 0: No redundancy at all
        # Any single disk failure = complete data loss
        return 0
        
    elif raid_level == "RAID 1":
        # RAID 1: Full mirroring
        # Can lose all disks except one
        # Example: 4 disks -> can lose 3 and still have data
        return num_disks - 1 if num_disks else 1
        
    elif raid_level == "RAID 5":
        # RAID 5: Single parity
        # Can tolerate exactly one disk failure
        # Second failure = data loss
        return 1
        
    else:
        # Unknown RAID level: Assume no fault tolerance
        return 0


# ============================================================================
# VISUALIZATION HELPER FUNCTIONS
# ============================================================================

def calculate_capacity_breakdown_dict(num_disks, raid_level):
    """
    Calculates capacity breakdown for pie chart visualization.
    
    This function returns the number of disks dedicated to each purpose:
    - Usable: Disks storing actual user data
    - Parity: Disks storing parity information
    - Mirror: Disks storing redundant copies
    
    Args:
        num_disks (int): Total number of disks
        raid_level (str): RAID configuration
    
    Returns:
        dict: Breakdown with keys:
            - usable (int): Number of disks for data
            - parity (int): Number of disks for parity
            - mirror (int): Number of disks for mirroring
    
    Examples:
        >>> calculate_capacity_breakdown_dict(4, "RAID 0")
        {'usable': 4, 'parity': 0, 'mirror': 0}
        # All 4 disks for data
        
        >>> calculate_capacity_breakdown_dict(4, "RAID 1")
        {'usable': 1, 'parity': 0, 'mirror': 3}
        # 1 disk for unique data, 3 for mirrors
        
        >>> calculate_capacity_breakdown_dict(4, "RAID 5")
        {'usable': 3, 'parity': 1, 'mirror': 0}
        # 3 disks for data, 1 for parity
    
    Use in Visualization:
        breakdown = calculate_capacity_breakdown_dict(4, "RAID 5")
        plt.pie([breakdown['usable'], breakdown['parity'], breakdown['mirror']],
                labels=['Usable', 'Parity', 'Mirror'])
    """
    if raid_level == "RAID 0":
        # All disks store data, no redundancy
        return {"usable": num_disks, "parity": 0, "mirror": 0}
        
    elif raid_level == "RAID 1":
        # 1 disk for unique data, rest are mirrors
        return {"usable": 1, "parity": 0, "mirror": num_disks - 1}
        
    elif raid_level == "RAID 5":
        # (n-1) disks for data, 1 equivalent for parity
        return {"usable": num_disks - 1, "parity": 1, "mirror": 0}
        
    else:
        # Default: Assume all usable (unknown RAID)
        return {"usable": num_disks, "parity": 0, "mirror": 0}


# ============================================================================
# COMPARISON AND ANALYSIS FUNCTIONS
# ============================================================================

def compare_raid_efficiency(num_disks, raid_levels=None):
    """
    Compares efficiency metrics across multiple RAID levels.
    
    This function generates a comprehensive comparison table showing
    all key metrics for different RAID configurations side by side.
    
    Args:
        num_disks (int): Number of disks to compare
        raid_levels (list, optional): List of RAID levels to compare.
                                     Default: ["RAID 0", "RAID 1", "RAID 5"]
    
    Returns:
        dict: Nested dictionary mapping RAID level to metrics:
            {
                "RAID X": {
                    "usable_percent": float,
                    "redundancy_percent": float,
                    "efficiency_ratio": float,
                    "speedup_factor": float,
                    "fault_tolerance": int
                },
                ...
            }
    
    Example:
        >>> comparison = compare_raid_efficiency(4)
        >>> for raid, metrics in comparison.items():
        ...     print(f"{raid}: {metrics['usable_percent']:.1f}% usable")
        RAID 0: 100.0% usable
        RAID 1: 25.0% usable
        RAID 5: 75.0% usable
    
    Use Cases:
        - Decision making: Which RAID level fits requirements?
        - Cost analysis: Compare storage efficiency
        - Performance analysis: Compare speedup factors
        - Risk assessment: Compare fault tolerance
    """
    # Use default RAID levels if none specified
    if raid_levels is None:
        raid_levels = ["RAID 0", "RAID 1", "RAID 5"]
    
    # Initialize comparison dictionary
    comparison = {}
    
    # Calculate metrics for each RAID level
    for raid in raid_levels:
        try:
            # Attempt to calculate all metrics
            comparison[raid] = {
                "usable_percent": usable_capacity_percent(num_disks, raid),
                "redundancy_percent": redundancy_percent(num_disks, raid),
                "efficiency_ratio": space_efficiency(num_disks, raid),
                "speedup_factor": calculate_parallel_speedup(num_disks, raid),
                "fault_tolerance": fault_tolerance_level(raid, num_disks)
            }
        except ValueError as e:
            # If calculation fails (e.g., RAID 5 with 2 disks), store error
            comparison[raid] = {"error": str(e)}
    
    return comparison


# ============================================================================
# MODULE DOCUMENTATION
# ============================================================================

"""
Quick Reference Guide:

RAID 0 - Striping:
    - Usable: 100%
    - Fault Tolerance: 0 disks
    - Performance: Excellent (n disks = n times faster)
    - Use Case: High-speed temporary storage, scratch disks

RAID 1 - Mirroring:
    - Usable: 100/n %
    - Fault Tolerance: n-1 disks
    - Performance: Good reads, standard writes
    - Use Case: Critical data, high availability systems

RAID 5 - Striping with Parity:
    - Usable: (n-1)/n * 100%
    - Fault Tolerance: 1 disk
    - Performance: Good (85% of RAID 0)
    - Use Case: General purpose, best balance

Formulas at a Glance:
    - Usable (RAID 0) = n disks
    - Usable (RAID 1) = 1 disk
    - Usable (RAID 5) = n - 1 disks
    - Total Required = Data Size / Efficiency
    - Speedup (RAID 0) = n
    - Speedup (RAID 1) = n / 2
    - Speedup (RAID 5) = (n - 1) * 0.85
"""
