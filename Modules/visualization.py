#!/usr/bin/env python3
"""
================================================================================
visualization.py - RAID Performance Visualization Module
================================================================================

Purpose:
    This module creates visual representations of RAID array performance
    and capacity distribution. It generates:
    - Pie charts showing storage space allocation
    - Bar charts comparing RAID level performance
    - Automatic performance timing with simulated workloads

Authors: Youssef and Omar
Deadline: Monday
Last Updated: December 2024

Visualization Types:
    1. Pie Chart: Shows how storage is divided (usable/mirror/parity)
    2. Bar Chart: Compares performance times across RAID levels

Dependencies:
    - matplotlib.pyplot: For creating charts and graphs
    - time: For performance timing
    - random: For adding variability to simulations

Output:
    - Displays charts in matplotlib windows
    - Prints performance timing results to console

================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

import matplotlib.pyplot as plt  # Plotting library for charts and graphs
import time                      # For timing operations
import random                    # For generating random values (not used currently)

# ============================================================================
# RAID STORAGE CALCULATIONS
# ============================================================================

def raid_space_distribution(raid_level, num_disks=4):
    """
    Calculates how storage space is distributed in a RAID array.
    
    This function computes the percentage of total storage capacity
    allocated to different purposes:
    - Usable: Space available for actual user data
    - Mirrored: Space used for redundant copies (RAID 1)
    - Parity: Space used for parity information (RAID 5)
    
    Args:
        raid_level (int): RAID level as integer.
                         Supported values: 0, 1, 5
        num_disks (int): Number of disks in the array.
                        Default: 4 disks
    
    Returns:
        tuple: (usable_percent, mirrored_percent, parity_percent)
               All values are percentages (0-100)
    
    Examples:
        >>> raid_space_distribution(0, 4)
        (100, 0, 0)  # 100% usable, no redundancy
        
        >>> raid_space_distribution(1, 4)
        (50, 50, 0)  # 50% usable, 50% mirrored
        
        >>> raid_space_distribution(5, 4)
        (75.0, 0, 25.0)  # 75% usable, 25% parity
    
    RAID Level Details:
        RAID 0 (Striping):
            - All disks store unique data
            - No redundancy = 100% usable
            - Example: 4x 1TB = 4TB usable
        
        RAID 1 (Mirroring):
            - Data duplicated on all disks
            - 50% usable for typical 2-disk setup
            - Example: 4x 1TB = 2TB usable (2TB mirrored)
        
        RAID 5 (Striping with Parity):
            - One disk worth of space for parity
            - (n-1)/n * 100% usable
            - Example: 4x 1TB = 3TB usable, 1TB parity
    
    Notes:
        - Percentages always sum to 100
        - Mirrored and parity are mutually exclusive
        - RAID 0 has no redundancy (risky but fast)
    """
    # ========================================================================
    # RAID 0: STRIPING (NO REDUNDANCY)
    # ========================================================================
    if raid_level == 0:
        usable = 100      # All space is usable
        mirrored = 0      # No mirroring
        parity = 0        # No parity

    # ========================================================================
    # RAID 1: MIRRORING (FULL REDUNDANCY)
    # ========================================================================
    elif raid_level == 1:
        usable = 50       # Half the space is usable (simplified for 2-way mirror)
        mirrored = 50     # Half the space is mirrored
        parity = 0        # No parity in RAID 1

    # ========================================================================
    # RAID 5: STRIPING WITH PARITY (SINGLE DISK REDUNDANCY)
    # ========================================================================
    elif raid_level == 5:
        # Calculate usable percentage: (n-1)/n * 100
        # Example: 4 disks -> (4-1)/4 * 100 = 75%
        usable = ((num_disks - 1) / num_disks) * 100
        
        # Calculate parity percentage: 1/n * 100
        # Example: 4 disks -> 1/4 * 100 = 25%
        parity = (1 / num_disks) * 100
        
        mirrored = 0      # No mirroring in RAID 5

    # Return all three percentages as a tuple
    return usable, mirrored, parity


# ============================================================================
# RAID PERFORMANCE SIMULATION
# ============================================================================

def simulate_raid_time(raid_level):
    """
    Simulates I/O operation time for a RAID level.
    
    This function measures how long a simulated workload takes to complete,
    with different RAID levels having different performance characteristics.
    The simulation uses a CPU-intensive loop as a proxy for disk operations.
    
    Args:
        raid_level (int): RAID level to simulate (0, 1, or 5)
    
    Returns:
        float: Simulated operation time in seconds, rounded to 3 decimal places
    
    Performance Characteristics:
        - RAID 0: Fastest (1.0x multiplier)
        - RAID 1: Slower (1.6x multiplier, due to write duplication)
        - RAID 5: Slowest (2.2x multiplier, due to parity calculation)
    
    Example:
        >>> simulate_raid_time(0)
        0.052  # Base time (fastest)
        
        >>> simulate_raid_time(1)
        0.083  # 1.6x slower (mirroring overhead)
        
        >>> simulate_raid_time(5)
        0.114  # 2.2x slower (parity overhead)
    
    How It Works:
        1. Record start time
        2. Execute simulated workload (CPU-intensive loop)
        3. Record end time and calculate duration
        4. Apply RAID-specific multiplier
        5. Return adjusted time
    
    Simulation Notes:
        - Loop performs 5 million iterations (meaningless arithmetic)
        - Not real disk I/O, but proportional to actual overhead
        - Multipliers are simplified estimates of real-world performance
        - Actual performance varies by hardware, file size, etc.
    
    Real-World Factors Not Modeled:
        - Disk seek time and rotational latency (HDDs)
        - SSD erase/program cycles
        - Controller cache effects
        - Operating system buffer cache
        - File system overhead
    """
    # Record start time in seconds since epoch
    start = time.time()

    # ========================================================================
    # SIMULATED WORKLOAD
    # ========================================================================
    # Perform CPU-intensive work to simulate disk operations
    # This loop represents the base time for a storage operation
    for i in range(5000000):  # 5 million iterations
        x = i * 2  # Meaningless arithmetic (placeholder for actual disk I/O)

    # Calculate base time (how long the loop took)
    base_time = time.time() - start

    # ========================================================================
    # APPLY RAID-SPECIFIC MULTIPLIERS
    # ========================================================================
    
    if raid_level == 0:
        # RAID 0: Fastest performance
        # Parallel striping across disks with no overhead
        multiplier = 1.0
        
    elif raid_level == 1:
        # RAID 1: Moderate performance
        # Write penalty from duplicating data to all mirrors
        # Read benefit from parallel access not modeled here
        multiplier = 1.6
        
    elif raid_level == 5:
        # RAID 5: Slower performance
        # Parity calculation (XOR operations) adds overhead
        # Must read, calculate parity, and write parity block
        multiplier = 2.2

    # Calculate final time by applying RAID overhead
    # Example: 0.05s base * 1.6 = 0.08s for RAID 1
    final_time = base_time * multiplier
    
    # Round to 3 decimal places for cleaner output
    return round(final_time, 3)


# ============================================================================
# VISUALIZATION 1: PIE CHART (CAPACITY DISTRIBUTION)
# ============================================================================

# Calculate storage distribution for RAID 5 with 4 disks
usable, mirrored, parity = raid_space_distribution(5, num_disks=4)

# Labels for pie chart slices
labels = [
    'Usable Data',     # Space for actual user data
    'Mirrored Data',   # Space for redundant copies (RAID 1)
    'Parity'           # Space for parity information (RAID 5)
]

# Values for pie chart slices (percentages)
# For RAID 5 with 4 disks: [75, 0, 25]
sizes = [usable, mirrored, parity]

# Create new figure with 5x5 inch size
plt.figure(figsize=(5,5))

# Create pie chart
# autopct='%1.1f%%': Display percentages with 1 decimal place
# Example: 75.0%, 25.0%
plt.pie(
    sizes,              # Data values
    labels=labels,      # Slice labels
    autopct='%1.1f%%'   # Format for percentage labels
)

# Add title to the chart
plt.title('RAID 5 Storage Distribution')

# Display the chart in a window
plt.show()


# ============================================================================
# VISUALIZATION 2: BAR CHART (PERFORMANCE COMPARISON)
# ============================================================================

# List of RAID levels to compare
raid_levels = ['RAID 0', 'RAID 1', 'RAID 5']

# Simulate performance time for each RAID level
# This runs the simulate_raid_time() function for each level
times = [
    simulate_raid_time(0),  # RAID 0 time
    simulate_raid_time(1),  # RAID 1 time
    simulate_raid_time(5)   # RAID 5 time
]

# Create new figure with 7x5 inch size (wider for bar chart)
plt.figure(figsize=(7,5))

# Create bar chart
# x-axis: RAID levels (categorical)
# y-axis: Time in seconds (numerical)
plt.bar(raid_levels, times)

# Add y-axis label
plt.ylabel('Time (seconds)')

# Add title to the chart
plt.title('RAID Performance Comparison')

# Display the chart in a window
plt.show()

# ============================================================================
# CONSOLE OUTPUT
# ============================================================================

# Print the simulated times to console for reference
# Creates a dictionary mapping RAID levels to their times
print("Simulated Times:", dict(zip(raid_levels, times)))

# Example output:
# Simulated Times: {'RAID 0': 0.052, 'RAID 1': 0.083, 'RAID 5': 0.114}


# ============================================================================
# USAGE NOTES AND EXTENSIONS
# ============================================================================

"""
Running This Module:
    $ python visualization.py
    
    This will:
    1. Display a pie chart showing RAID 5 storage distribution
    2. Display a bar chart comparing RAID 0, 1, and 5 performance
    3. Print timing results to console

Customizing the Pie Chart:
    # Show RAID 1 distribution instead
    usable, mirrored, parity = raid_space_distribution(1, num_disks=4)
    sizes = [usable, mirrored, parity]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title('RAID 1 Storage Distribution')
    plt.show()

Customizing the Bar Chart:
    # Add more RAID levels
    raid_levels = ['RAID 0', 'RAID 1', 'RAID 5', 'RAID 6', 'RAID 10']
    times = [simulate_raid_time(level) for level in [0, 1, 5, 6, 10]]
    plt.bar(raid_levels, times, color='skyblue')
    
    # Customize colors
    colors = ['green', 'yellow', 'orange', 'red', 'purple']
    plt.bar(raid_levels, times, color=colors)

Integration with Main Application:
    This module is currently standalone, but can be integrated:
    
    from visualization import raid_space_distribution, simulate_raid_time
    
    # Get distribution for UI display
    usable, mirror, parity = raid_space_distribution(5, 6)
    
    # Get performance estimate
    estimated_time = simulate_raid_time(5)

Improving the Simulation:
    Current simulation uses CPU time as proxy for disk I/O.
    
    Better approaches:
    1. Use actual disk I/O operations (read/write files)
    2. Integrate with Raid_Simulation module's more detailed model
    3. Add randomness to simulate real-world variability:
       
       import random
       noise = random.uniform(0.9, 1.1)  # ±10% variation
       return round(base_time * multiplier * noise, 3)
    
    4. Model different workloads (sequential vs random I/O)

Saving Charts to Files:
    Instead of plt.show(), save to files:
    
    # Save pie chart
    plt.savefig('raid5_distribution.png', dpi=300, bbox_inches='tight')
    
    # Save bar chart
    plt.savefig('raid_performance.png', dpi=300, bbox_inches='tight')
    
    # Save as PDF (vector graphics)
    plt.savefig('raid_comparison.pdf')

Advanced Visualizations:
    - Line graphs showing performance vs. disk count
    - Heatmaps showing performance across different file sizes
    - 3D surface plots for multi-variable analysis
    - Animated charts showing rebuild times
    - Stacked bar charts showing read vs write performance

Chart Styling:
    # Use seaborn for prettier charts
    import seaborn as sns
    sns.set_style('darkgrid')
    
    # Custom colors
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    plt.bar(raid_levels, times, color=colors)
    
    # Add grid
    plt.grid(axis='y', alpha=0.3)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
"""
