"""
run.py - Optimized
Gradio UI for RAID Multimedia Storage Performance Simulator
"""
import sys, os, shutil, random, time
from pathlib import Path
from datetime import datetime
import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# Setup Paths
APP_DIR = Path(__file__).parent
REPORTS_DIR = APP_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(APP_DIR / "Modules"))

# Import Modules
from Data_Analysis import append_run, save_report_csv, summary_statistics
from Raid_Calculation import usable_capacity_percent, redundancy_percent, space_efficiency, calculate_capacity_breakdown_dict
from Raid_Simulation import simulate_raid_read, simulate_raid_write

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".mp4", ".mov", ".mkv", ".avi", ".webm"}
last_scan = {"folder": None, "files": [], "total_bytes": 0}

def scan_folder(folder_path, progress=gr.Progress()):
    folder_path = os.path.normpath(folder_path.strip('"').strip("'"))
    if not os.path.isdir(folder_path): return "❌ Invalid folder.", None, 0
    
    files = [os.path.join(r, f) for r, _, n in os.walk(folder_path) for f in n if os.path.splitext(f)[1].lower() in SUPPORTED_EXT]
    if not files: return "❌ No media files found.", None, 0

    rows, total_bytes = [], 0
    for p in files:
        size = os.path.getsize(p)
        total_bytes += size
        res = "N/A"
        if p.lower().endswith(tuple({".jpg", ".png", ".bmp", ".gif"})):
            try:
                with Image.open(p) as im: res = f"{im.width}x{im.height}"
            except: pass
        rows.append({"Filename": os.path.basename(p), "Extension": os.path.splitext(p)[1], "Size (KB)": round(size/1024, 2), "Resolution": res})

    last_scan.update({"folder": folder_path, "files": files, "total_bytes": total_bytes})
    
    # Summary
    ext_counts = pd.DataFrame(rows)["Extension"].value_counts().to_string()
    summary = f"## 📊 Scan Results\n- **Files:** {len(files)}\n- **Size:** {total_bytes/1024**2:.2f} MB\n\n### Types:\n{ext_counts}"
    return summary, pd.DataFrame(rows[:200]), total_bytes/1024**2

def build_virtual_disks(raid, num, files, ts):
    base = REPORTS_DIR / f"virtual_disks_{ts}" / raid.replace(" ", "_")
    disks = {i: base / f"disk_{i}" for i in range(num)}
    for d in disks.values(): d.mkdir(parents=True, exist_ok=True)
    
    disk_loads = {i: 0 for i in range(num)}
    
    for idx, f in enumerate(files):
        size = os.path.getsize(f)
        
        # Target Logic
        if raid == "RAID 1":
            targets = list(disks.keys()) # All disks
        else:
            # RAID 5: Parity is (idx % num), data goes to balancing logic excluding parity
            candidates = [d for d in range(num) if (raid != "RAID 5" or d != (idx % num))]
            target = min(candidates, key=lambda x: disk_loads[x])
            targets = [target]

        # Copy Files
        for t in targets:
            shutil.copy2(f, disks[t])
            disk_loads[t] += size
            
        # RAID 5 Parity Placeholder
        if raid == "RAID 5":
            p_disk = idx % num
            (disks[p_disk] / f"{Path(f).stem}_PARITY.txt").write_text(f"Parity for {Path(f).name}\nData on disk {targets[0]}")

    zip_path = shutil.make_archive(str(base.parent / base.name), "zip", base)
    return str(base), zip_path

def run_simulation(num_disks, raid_level, progress=gr.Progress()):
    if not last_scan["files"]: return "❌ Scan folder first.", *([None]*5)
    
    # Sim
    r_ms, w_ms = simulate_raid_read(raid_level), simulate_raid_write(raid_level)
    run_data = {
        "raid_level": raid_level, "disk_count": num_disks, "total_files": len(last_scan["files"]),
        "total_size_bytes": last_scan["total_bytes"], "read_time_ms": r_ms, "write_time_ms": w_ms,
        "total_time_ms": r_ms + w_ms, "usable_%": usable_capacity_percent(num_disks, raid_level),
        "efficiency_%": space_efficiency(num_disks, raid_level) * 100
    }
    df = append_run(None, run_data)
    stats_df = summary_statistics(df)
    
    # Save & Plots
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = {
        "report": REPORTS_DIR / f"report_{ts}.csv", "stats": REPORTS_DIR / f"summary_{ts}.csv",
        "pie": REPORTS_DIR / f"pie_{ts}.png", "bar": REPORTS_DIR / f"bar_{ts}.png"
    }
    save_report_csv(df, files["report"].name); save_report_csv(stats_df, files["stats"].name)
    
    # Plotting - Create figures
    fig1 = plt.figure(figsize=(5,5))
    bd = calculate_capacity_breakdown_dict(num_disks, raid_level)
    plt.pie([bd["usable"], bd["parity"], bd["mirror"]], labels=["Usable", "Parity", "Mirror"], autopct="%1.1f%%")
    plt.title("Capacity Distribution")
    fig1.savefig(files["pie"])
    
    fig2 = plt.figure(figsize=(6,4))
    plt.bar([raid_level], [run_data["total_time_ms"]])
    plt.ylabel("Time (ms)")
    plt.title("Total Performance Time")
    fig2.savefig(files["bar"])

    # Virtual Disks
    v_folder, v_zip = build_virtual_disks(raid_level, num_disks, last_scan["files"], ts)
    
    msg = f"## ✅ Done: {raid_level}\nSaved to `reports/`\nZip: `{os.path.basename(v_zip)}`"
    
    # Return matplotlib Figure objects (fig1, fig2), not file paths
    return msg, df, stats_df, fig1, fig2, [str(f) for f in files.values()] + [v_zip]

# UI
with gr.Blocks(title="RAID Sim", theme=gr.themes.Soft()) as app:
    gr.HTML("<h1 style='text-align:center; background:#667eea; color:white; padding:10px; border-radius:10px;'>💾 RAID Simulator</h1>")
    state_size = gr.State(0)
    
    with gr.Tabs():
        with gr.Tab("1. Load"):
            with gr.Row():
                inp = gr.Textbox(label="Path")
                btn = gr.Button("Scan", variant="primary")
            out_md = gr.Markdown()
            out_tbl = gr.DataFrame()
            btn.click(scan_folder, inp, [out_md, out_tbl, state_size])
            
        with gr.Tab("2. Config"):
            d_sld = gr.Slider(2, 12, value=4, step=1, label="Disks")
            r_rad = gr.Radio(["RAID 0", "RAID 1", "RAID 5"], value="RAID 5", label="Level")
            c_btn = gr.Button("Calc Metrics")
            c_out = gr.Markdown()
            c_btn.click(lambda n,r,s: f"**Usable:** {usable_capacity_percent(n,r):.1f}% | **Eff:** {space_efficiency(n,r):.2%}", [d_sld, r_rad, state_size], c_out)

        with gr.Tab("3. Run"):
            s_btn = gr.Button("🚀 Simulate", variant="primary")
            s_out = gr.Markdown()
            
            with gr.Row():
                p1 = gr.Plot(label="Capacity Distribution")
                p2 = gr.Plot(label="Performance")
            
            with gr.Row():
                res_df = gr.DataFrame(label="Run Data")
                stats_tbl = gr.DataFrame(label="Summary Statistics")
            
            dl = gr.File(label="Download Reports & Virtual Disks", file_count="multiple")
            
            s_btn.click(run_simulation, [d_sld, r_rad], [s_out, res_df, stats_tbl, p1, p2, dl])

if __name__ == "__main__":
    app.launch(inbrowser=True)
