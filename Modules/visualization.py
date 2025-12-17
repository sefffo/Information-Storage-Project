#youssef and omar (Dead Line : Monday )
import matplotlib.pyplot as plt
import time
import random

# -------------------------------
# 1) RAID SPACE CALCULATIONS
# -------------------------------

def raid_space_distribution(raid_level, num_disks=4):
    """
    Returns usable %, mirrored %, parity % for RAID 0,1,5
    """
    if raid_level == 0:
        usable = 100
        mirrored = 0
        parity = 0

    elif raid_level == 1:
        usable = 50
        mirrored = 50
        parity = 0

    elif raid_level == 5:
        usable = ((num_disks - 1) / num_disks) * 100
        parity = (1 / num_disks) * 100
        mirrored = 0

    return usable, mirrored, parity


# ---------------------------------
# 2) SIMULATED RAID PERFORMANCE
# ---------------------------------

def simulate_raid_time(raid_level):
    """
    Simulates I/O time for each RAID level
    by adding artificial delays.
    """
    start = time.time()

    # Fake "processing" (simulated workload)
    for i in range(5000000):
        x = i * 2  # meaningless work

    base_time = time.time() - start

    # RAID penalties
    if raid_level == 0:
        multiplier = 1.0   # fastest
    elif raid_level == 1:
        multiplier = 1.6   # slower due to mirroring
    elif raid_level == 5:
        multiplier = 2.2   # slowest (parity calculation)

    return round(base_time * multiplier, 3)


# -------------------------------
# 3) PIE CHART (RAID 5 example)
# -------------------------------

usable, mirrored, parity = raid_space_distribution(5, num_disks=4)

labels = ['Usable Data', 'Mirrored Data', 'Parity']
sizes = [usable, mirrored, parity]

plt.figure(figsize=(5,5))
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.title('RAID 5 Storage Distribution')
plt.show()


# -------------------------------
# 4) BAR CHART (automatic times)
# -------------------------------

raid_levels = ['RAID 0', 'RAID 1', 'RAID 5']
times = [
    simulate_raid_time(0),
    simulate_raid_time(1),
    simulate_raid_time(5)
]

plt.figure(figsize=(7,5))
plt.bar(raid_levels, times)
plt.ylabel('Time (seconds)')
plt.title('RAID Performance Comparison')
plt.show()

print("Simulated Times:", dict(zip(raid_levels, times)))
