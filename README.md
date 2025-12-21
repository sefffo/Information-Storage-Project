# 💾 RAID Multimedia Storage Performance Simulator

A Python-based RAID storage simulator with an interactive Gradio UI for analyzing multimedia file storage performance across different RAID configurations.

## 📋 Overview

This project simulates RAID (Redundant Array of Independent Disks) storage systems to analyze how multimedia files (images and videos) are distributed and stored across different RAID levels. The simulator provides performance metrics, capacity calculations, and creates virtual disk representations of the storage configuration.

## ✨ Features

- **Multi-RAID Support**: Simulate RAID 0, RAID 1, and RAID 5 configurations
- **Multimedia File Analysis**: Scan and analyze image (.jpg, .png, .bmp, .gif) and video (.mp4, .mov, .mkv, .avi, .webm) files
- **Interactive Web UI**: Built with Gradio for easy configuration and visualization
- **Performance Metrics**: 
  - Read/Write time simulation
  - Usable capacity calculation
  - Storage efficiency analysis
  - Redundancy percentage
- **Visual Reports**: 
  - Capacity distribution pie charts
  - Performance bar charts
  - Statistical summaries
- **Virtual Disk Creation**: Generates physical file distributions showing how files are stored across disks
- **Export Capabilities**: Download reports as CSV and virtual disks as ZIP archives

## 🏗️ Project Structure

```
Information-Storage-Project/
├── run.py                      # Main application entry point
├── Modules/
│   ├── Data_Analysis.py        # Data logging and statistical analysis
│   ├── Raid_Calculation.py     # RAID capacity and efficiency calculations
│   ├── Raid_Simulation.py      # Read/Write performance simulation
│   └── visualization.py        # Chart generation utilities
└── reports/                    # Generated reports and virtual disks
```

## 🚀 Getting Started

### Prerequisites

```bash
pip install gradio pandas matplotlib pillow
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sefffo/Information-Storage-Project.git
cd Information-Storage-Project
```

2. Run the application:
```bash
python run.py
```

The application will launch in your default web browser.

## 💻 Usage

### 1. Load Media Files
- Enter the path to a folder containing multimedia files
- Click **Scan** to analyze the folder
- Review the file summary and preview table

### 2. Configure RAID Settings
- Select number of disks (2-12)
- Choose RAID level (RAID 0, RAID 1, or RAID 5)
- Click **Calc Metrics** to preview usable capacity and efficiency

### 3. Run Simulation
- Click **🚀 Simulate** to execute the RAID simulation
- View performance charts and statistics
- Download generated reports and virtual disk structures

## 📊 RAID Configurations

### RAID 0 (Striping)
- **Usable Capacity**: 100%
- **Redundancy**: None
- **Performance**: High read/write speeds
- **Risk**: No fault tolerance

### RAID 1 (Mirroring)
- **Usable Capacity**: 50%
- **Redundancy**: Full mirror on all disks
- **Performance**: Fast reads, moderate writes
- **Risk**: Can survive disk failures

### RAID 5 (Striping with Parity)
- **Usable Capacity**: (n-1)/n × 100%
- **Redundancy**: Distributed parity
- **Performance**: Balanced read/write
- **Risk**: Can survive single disk failure

## 📈 Output Files

Each simulation generates:
- `report_[timestamp].csv` - Detailed run data
- `summary_[timestamp].csv` - Statistical summary
- `pie_[timestamp].png` - Capacity distribution chart
- `bar_[timestamp].png` - Performance chart
- `virtual_disks_[timestamp].zip` - Simulated disk file distribution

## 🛠️ Technical Details

### Modules

**Data_Analysis.py**
- Logs simulation runs to pandas DataFrames
- Calculates summary statistics (mean, median, std, min, max)
- Exports data to CSV format

**Raid_Calculation.py**
- Computes usable capacity percentages
- Calculates redundancy and space efficiency
- Provides capacity breakdown (usable/parity/mirror)

**Raid_Simulation.py**
- Simulates read/write operations with random timing
- Models RAID-specific performance characteristics
- Generates realistic performance metrics

**visualization.py**
- Creates matplotlib visualizations
- Generates pie and bar charts
- Handles chart styling and formatting

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is available for educational and research purposes.

## 👤 Author

**sefffo**
- GitHub: [@sefffo](https://github.com/sefffo)

## 🙏 Acknowledgments

- Built with [Gradio](https://gradio.app/) for the web interface
- Uses [Pandas](https://pandas.pydata.org/) for data analysis
- Visualizations powered by [Matplotlib](https://matplotlib.org/)

---

**Note**: This is a simulation tool for educational purposes. Performance metrics are simulated and may not reflect real-world hardware performance.