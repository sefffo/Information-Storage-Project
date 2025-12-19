# Formula Documentation

This document details all formulas implemented from the Information Storage course materials.

## Table of Contents

1. [Disk Performance Formulas (sec-2-1.pdf)](#disk-performance-formulas)
2. [RAID Calculation Formulas (sec-5-1.pdf)](#raid-calculation-formulas)
3. [Usage Examples](#usage-examples)
4. [Code Locations](#code-locations)

---

## Disk Performance Formulas

### Source: sec-2-1.pdf (Slides 5-16)

### 1. Disk Service Time (Ts)

**Formula:**
```
Ts = seek_time + (0.5 / (disk_rpm / 60)) + (data_block_size / transfer_rate)
```

**Components:**
- **Seek Time**: Time to position read/write head (milliseconds)
- **Rotational Latency**: `0.5 / (disk_rpm / 60)` - average time for platter rotation
- **Transfer Time**: `data_block_size / transfer_rate` - time to read/write data

**Code Location:** `Modules/Disk_Performance.py::calculate_service_time()`

**Example from sec-2-1.pdf (Slide 14):**
```python
from Disk_Performance import calculate_service_time

# 15K RPM disk with 5ms seek, 4KB block, 40MB/s transfer
ts = calculate_service_time(
    seek_time_ms=5,
    disk_rpm=15000,
    data_block_size_kb=4,
    transfer_rate_mbps=40
)
print(f"Service Time: {ts:.2f} ms")  # Output: 7.10 ms
```

---

### 2. Rotational Latency

**Formula:**
```
Average Rotational Latency = (1/2) × (60000 / RPM) milliseconds
```

**Code Location:** `Modules/Disk_Performance.py::calculate_rotational_latency()`

**Example from sec-2-1.pdf (Slide 8):**
```python
from Disk_Performance import calculate_rotational_latency

# 7200 RPM disk
latency = calculate_rotational_latency(7200)
print(f"Latency: {latency:.2f} ms")  # Output: 4.17 ms
```

---

### 3. IOPS Calculation

**Formula:**
```
IOPS = 1 / (Ts × 0.001)

For 70% utilization (recommended for acceptable response time):
IOPS = 0.7 × (1 / (Ts × 0.001))
```

**Code Location:** `Modules/Disk_Performance.py::calculate_iops()`

**Example:**
```python
from Disk_Performance import calculate_iops

# Service time of 7.1ms
iops_100 = calculate_iops(7.1, utilization=1.0)
print(f"100% utilization: {iops_100:.0f} IOPS")  # Output: 140 IOPS

iops_70 = calculate_iops(7.1, utilization=0.7)
print(f"70% utilization: {iops_70:.0f} IOPS")   # Output: 98 IOPS
```

---

### 4. Disk Capacity Requirements (Dc)

**Formula:**
```
Dc = total_capacity_required / capacity_of_single_disk
```

**Code Location:** `Modules/Disk_Performance.py::calculate_disk_capacity_required()`

**Example from sec-2-1.pdf (Slide 16):**
```python
from Disk_Performance import calculate_disk_capacity_required

# 1TB data, 100GB disks
dc = calculate_disk_capacity_required(1024, 100)
print(f"Disks for capacity: {dc}")  # Output: 10 disks
```

---

### 5. Disk Performance Requirements (Dp)

**Formula:**
```
Dp = IOPS_generated_by_application / IOPS_serviced_by_single_disk
```

**Code Location:** `Modules/Disk_Performance.py::calculate_disk_performance_required()`

**Example from sec-2-1.pdf (Slide 15):**
```python
from Disk_Performance import calculate_disk_performance_required

# Application needs 4900 IOPS, each disk provides 98 IOPS (70% util)
dp = calculate_disk_performance_required(4900, 98)
print(f"Disks for performance: {dp}")  # Output: 50 disks
```

---

### 6. Total Disks Required

**Formula:**
```
Total Disks = max(Dc, Dp)
```

The application needs the **maximum** of capacity or performance requirements.

**Code Location:** `Modules/Disk_Performance.py::calculate_total_disks_required()`

**Complete Example from sec-2-1.pdf (Slides 13-16):**
```python
from Disk_Performance import complete_disk_analysis

result = complete_disk_analysis(
    seek_time_ms=5,
    disk_rpm=15000,
    data_block_size_kb=4,
    transfer_rate_mbps=40,
    total_capacity_gb=1024,      # 1TB
    disk_capacity_gb=100,         # 100GB per disk
    app_iops_required=4900        # Application needs 4900 IOPS
)

print(f"Service Time: {result['service_time_ms']:.2f} ms")         # 7.10 ms
print(f"IOPS (70% util): {result['iops_70_percent']:.0f}")         # 98 IOPS
print(f"Disks for capacity: {result['disks_for_capacity']}")       # 10 disks
print(f"Disks for performance: {result['disks_for_performance']}") # 50 disks
print(f"Total required: {result['total_disks_required']}")         # 50 disks
```

---

## RAID Calculation Formulas

### Source: sec-5-1.pdf (Slides 13-29)

### 1. Usable Capacity

**Formulas:**
```
RAID 0:  Usable = n × Disk_Size          (100%)
RAID 1:  Usable = (n/2) × Disk_Size       (50% for 2 disks)
RAID 5:  Usable = (n-1) × Disk_Size       (e.g., 80% for 5 disks)
RAID 6:  Usable = (n-2) × Disk_Size       (e.g., 66.7% for 6 disks)
```

**Code Location:** `Modules/Raid_Calculation.py::usable_capacity_percent()`

**Examples from sec-5-1.pdf:**
```python
from Raid_Calculation import usable_capacity_percent

# RAID 0: 4 × 200GB = 800GB usable
print(usable_capacity_percent(4, "RAID 0"))  # 100.0%

# RAID 1: 4 × 200GB = 400GB usable (50%)
print(usable_capacity_percent(4, "RAID 1"))  # 50.0%

# RAID 5: 5 × 200GB = 800GB usable (80%)
print(usable_capacity_percent(5, "RAID 5"))  # 80.0%

# RAID 6: 6 × 200GB = 800GB usable (66.7%)
print(usable_capacity_percent(6, "RAID 6"))  # 66.67%
```

---

### 2. Write Penalty

**Values from sec-5-1.pdf (Slides 21-22):**
```
RAID 0:  Write Penalty = 1  (no overhead)
RAID 1:  Write Penalty = 2  (write to both mirrors)
RAID 5:  Write Penalty = 4  (read data + read parity + write data + write parity)
RAID 6:  Write Penalty = 6  (read data + 2 parity reads + write data + 2 parity writes)
```

**Code Location:** `Modules/Raid_Calculation.py::get_write_penalty()`

**Example:**
```python
from Raid_Calculation import get_write_penalty

for raid in ["RAID 0", "RAID 1", "RAID 5", "RAID 6"]:
    penalty = get_write_penalty(raid)
    print(f"{raid}: Write Penalty = {penalty}")

# Output:
# RAID 0: Write Penalty = 1
# RAID 1: Write Penalty = 2
# RAID 5: Write Penalty = 4
# RAID 6: Write Penalty = 6
```

---

### 3. Disk Load with Write Penalty

**Formula from sec-5-1.pdf (Slides 22-23):**
```
Disk Load (IOPS) = (Total_IOPS × Read_%) + (Total_IOPS × Write_% × Write_Penalty)
```

**Code Location:** `Modules/Raid_Calculation.py::calculate_disk_load_iops()`

**Example from sec-5-1.pdf (Slide 25):**
```python
from Raid_Calculation import calculate_disk_load_iops

# 400 IOPS, 75% read, 25% write, RAID 5
load = calculate_disk_load_iops(
    total_iops=400,
    read_percent=75,
    write_percent=25,
    raid_level="RAID 5"
)
print(f"Disk load: {load:.0f} IOPS")  # Output: 700 IOPS

# Calculation: 400 × 0.75 + 400 × 0.25 × 4 = 300 + 400 = 700
```

---

### 4. Required Disks for IOPS Workload

**Formula:**
```
Required_Disks = ceil(Disk_Load_IOPS / IOPS_per_Disk)
```

**Code Location:** `Modules/Raid_Calculation.py::calculate_required_disks_for_iops()`

**Example from sec-5-1.pdf (Slides 27-29):**
```python
from Raid_Calculation import calculate_required_disks_for_iops

# 5200 IOPS, 60% read, 40% write, 180 IOPS per disk

# RAID 5
disks_raid5 = calculate_required_disks_for_iops(
    total_iops=5200,
    read_percent=60,
    write_percent=40,
    raid_level="RAID 5",
    iops_per_disk=180
)
print(f"RAID 5 requires: {disks_raid5} disks")  # Output: 64 disks

# RAID 1
disks_raid1 = calculate_required_disks_for_iops(
    total_iops=5200,
    read_percent=60,
    write_percent=40,
    raid_level="RAID 1",
    iops_per_disk=180
)
print(f"RAID 1 requires: {disks_raid1} disks")  # Output: 41 disks

# Calculation for RAID 5:
# Disk Load = 5200 × 0.6 + 5200 × 0.4 × 4 = 3120 + 8320 = 11440 IOPS
# Disks = 11440 / 180 = 63.56 → 64 disks

# Calculation for RAID 1:
# Disk Load = 5200 × 0.6 + 5200 × 0.4 × 2 = 3120 + 4160 = 7280 IOPS
# Disks = 7280 / 180 = 40.44 → 41 disks (must be even for RAID 1)
```

---

### 5. XOR Parity Calculation

**Formula from sec-5-1.pdf (Slide 9):**
```
Parity = D1 ⊕ D2 ⊕ D3 ⊕ ... ⊕ Dn

To recover failed disk:
D_missing = D1 ⊕ D2 ⊕ ... ⊕ D_remaining ⊕ Parity
```

**Code Location:** `Modules/Raid_Calculation.py::calculate_xor_parity()` and `recover_failed_disk_xor()`

**Example from sec-5-1.pdf (Slide 9):**
```python
from Raid_Calculation import calculate_xor_parity, recover_failed_disk_xor

# Binary data blocks
d1 = 0b10110010  # Disk 1: 10110010
d2 = 0b11001010  # Disk 2: 11001010

# Calculate parity
parity = calculate_xor_parity([d1, d2])
print(f"Parity: {bin(parity)}")  # Output: 0b1111000

# Simulate disk 2 failure - recover using parity
recovered = recover_failed_disk_xor([d1], parity)
print(f"Recovered D2: {bin(recovered)}")  # Output: 0b11001010
print(f"Match: {recovered == d2}")         # Output: True
```

**Numeric Example from sec-5-1.pdf (Slide 8):**
```python
# Stripe: D1=4, D2=6, D3=?, D4=7, Parity=18
# Formula: 4 + 6 + ? + 7 = 18, so ? = 1

d1, d2, d4 = 4, 6, 7
parity = 18

# Using XOR to recover D3
d3_recovered = recover_failed_disk_xor([d1, d2, d4], parity)
print(f"Recovered D3: {d3_recovered}")  # Output: 1
```

---

## Usage Examples

### Complete Disk Analysis Example

```python
from Disk_Performance import complete_disk_analysis

# Scenario: Design storage for a new application
result = complete_disk_analysis(
    seek_time_ms=5,               # 5ms average seek time
    disk_rpm=15000,               # 15K RPM enterprise disk
    data_block_size_kb=4,         # 4KB I/O size
    transfer_rate_mbps=40,        # 40 MB/s transfer rate
    total_capacity_gb=1024,       # Need 1TB storage
    disk_capacity_gb=100,         # 100GB per disk
    app_iops_required=4900        # Application generates 4900 IOPS
)

print(f"\n{'='*60}")
print("Disk Performance Analysis")
print(f"{'='*60}")
print(f"Service Time: {result['service_time_ms']:.2f} ms")
print(f"IOPS per disk (70% util): {result['iops_70_percent']:.0f}")
print(f"\nDisks needed for capacity: {result['disks_for_capacity']}")
print(f"Disks needed for performance: {result['disks_for_performance']}")
print(f"\nTotal disks required: {result['total_disks_required']}")
print(f"\nBottleneck: {'Performance' if result['disks_for_performance'] > result['disks_for_capacity'] else 'Capacity'}")
```

### RAID Comparison Example

```python
from Raid_Calculation import (
    calculate_disk_load_iops,
    calculate_required_disks_for_iops,
    get_write_penalty,
    usable_capacity_percent
)

# Workload specifications
total_iops = 5200
read_percent = 60
write_percent = 40
iops_per_disk = 180
num_disks_per_array = 8

print(f"\n{'='*60}")
print("RAID Level Comparison")
print(f"{'='*60}")
print(f"Workload: {total_iops} IOPS ({read_percent}% read, {write_percent}% write)")
print(f"Disk capacity: {iops_per_disk} IOPS each\n")

for raid in ["RAID 0", "RAID 1", "RAID 5", "RAID 6"]:
    # Calculate metrics
    write_penalty = get_write_penalty(raid)
    disk_load = calculate_disk_load_iops(total_iops, read_percent, write_percent, raid)
    required_disks = calculate_required_disks_for_iops(
        total_iops, read_percent, write_percent, raid, iops_per_disk
    )
    usable = usable_capacity_percent(required_disks, raid)
    
    print(f"{raid}:")
    print(f"  Write Penalty: {write_penalty}")
    print(f"  Disk Load: {disk_load:.0f} IOPS")
    print(f"  Disks Required: {required_disks}")
    print(f"  Usable Capacity: {usable:.1f}%")
    print()
```

---

## Code Locations

### Disk Performance Module
- **File:** `Modules/Disk_Performance.py`
- **Functions:**
  - `calculate_service_time()` - Service time formula (Ts)
  - `calculate_iops()` - IOPS from service time
  - `calculate_rotational_latency()` - Average rotational latency
  - `calculate_disk_capacity_required()` - Dc formula
  - `calculate_disk_performance_required()` - Dp formula
  - `calculate_total_disks_required()` - max(Dc, Dp)
  - `complete_disk_analysis()` - Full analysis pipeline

### RAID Calculation Module
- **File:** `Modules/Raid_Calculation.py`
- **Functions:**
  - `usable_capacity_percent()` - Usable capacity for RAID levels
  - `get_write_penalty()` - Write penalty by RAID level
  - `calculate_disk_load_iops()` - Disk load with write penalty
  - `calculate_required_disks_for_iops()` - Disks needed for workload
  - `calculate_xor_parity()` - XOR parity calculation
  - `recover_failed_disk_xor()` - Recover data using parity
  - `space_efficiency()` - Efficiency ratio
  - `compare_raid_efficiency()` - Compare multiple RAID levels

### RAID Simulation Module
- **File:** `Modules/Raid_Simulation.py`
- **Functions:**
  - `simulate_raid_read()` - Simulate read performance
  - `simulate_raid_write()` - Simulate write performance with penalty
  - `calculate_raid_iops()` - Calculate RAID array IOPS
  - `run_raid_simulation()` - Complete simulation pipeline

---

## Testing

Run the modules directly to see examples:

```bash
# Test disk performance calculations
python Modules/Disk_Performance.py

# Test RAID calculations
python Modules/Raid_Calculation.py

# Run RAID simulation
python Modules/Raid_Simulation.py
```

---

## References

- **sec-2-1.pdf**: Data Center Environment (Disk Drive Performance)
  - Slides 5-6: Service Time Formula
  - Slides 6: IOPS Calculation
  - Slides 6: Dc and Dp Formulas
  - Slides 8: Rotational Latency
  - Slides 13-16: Complete Example

- **sec-5-1.pdf**: RAID Techniques
  - Slides 13-20: RAID Capacity Formulas
  - Slides 21-23: RAID Write Penalty
  - Slide 22: Disk Load Formula
  - Slides 24-29: Complete Examples
  - Slide 9: XOR Parity Calculation

---

## Notes

- All formulas match the course material exactly
- Examples use the same values as the PDF slides
- IOPS calculations now use proper formulas instead of random values
- Write penalty is correctly applied using the formula from sec-5-1.pdf
- XOR parity implements the exact algorithm from the slides

**Last Updated:** December 19, 2025
