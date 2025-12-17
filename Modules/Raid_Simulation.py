# Azoz and Saif (Dead Line : Monday )
import os
import time
from concurrent.futures import ThreadPoolExecutor

from Raid_Calculation import (
    usable_capacity_percent,
    redundancy_percent,
    space_efficiency,
    calculate_storage_overhead,
    estimate_access_time
)


def simulate_io_copy(files, raid_level, num_disks):
    """
    Simulate parallel I/O access using threads.
    Returns total time taken.
    """
    start = time.time()

    def copy_file(file_size):
        # simulate access time for each file
        return estimate_access_time(
            file_size_bytes=file_size,
            num_disks=num_disks,
            raid_level=raid_level
        )

    with ThreadPoolExecutor(max_workers=num_disks) as executor:
        list(executor.map(copy_file, files))

    return time.time() - start


def simulate_raid(folder_path, raid_level, num_disks):
    """
    Main RAID simulation for a given folder.
    """
    files = []
    total_bytes = 0

    for root, _, filenames in os.walk(folder_path):
        for f in filenames:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            files.append(size)
            total_bytes += size

    usable_percent = usable_capacity_percent(num_disks, raid_level)
    redundancy = redundancy_percent(num_disks, raid_level)
    efficiency = space_efficiency(num_disks, raid_level)

    storage_info = calculate_storage_overhead(
        total_bytes,
        raid_level,
        num_disks
    )

    access_time = simulate_io_copy(files, raid_level, num_disks)

    return {
        "raid_level": raid_level,
        "num_disks": num_disks,
        "total_data_bytes": total_bytes,
        "usable_percent": usable_percent,
        "redundancy_percent": redundancy,
        "space_efficiency": efficiency,
        "storage_breakdown": storage_info,
        "access_time_seconds": access_time
    }


def simulate_all_raids(folder_path, num_disks=4):
    """
    Run RAID 0, RAID 1, RAID 5 simulations and compare results.
    """
    results = []

    for raid in ["RAID 0", "RAID 1", "RAID 5"]:
        results.append(
            simulate_raid(folder_path, raid, num_disks)
        )

    return results


def simulate_disk_failure_raid5(total_bytes, num_disks):
    """
    Extra feature: RAID 5 disk failure rebuild simulation (XOR concept).
    """
    if num_disks < 3:
        raise ValueError("RAID 5 requires at least 3 disks")

    # rebuild time penalty simulation
    rebuild_time = estimate_access_time(
        file_size_bytes=total_bytes,
        num_disks=num_disks - 1,
        raid_level="RAID 5"
    ) * 2

    return rebuild_time
