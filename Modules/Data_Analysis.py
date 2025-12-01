#omar and youssef (Dead Line : Monday )import pandas as pd

def append_run(df, run_info_dict):
    row = pd.DataFrame([run_info_dict])
    if df is None or df.empty:
        return row
    else:
        return pd.concat([df, row], ignore_index=True)


def save_report_csv(df, path):
    df.to_csv(path, index=False)
    print(f"The Report saved to {path}")


fields = ["read_time_ms", "write_time_ms", "read_iops", "write_iops"]


def summary_statistics(df):
    stats_rows = []

    for field in fields:
        if field in df.columns:
            stats_rows.append({
                "metric": field,
                "mean": df[field].mean(),
                "std": df[field].std(),
                "median": df[field].median(),
                "min": df[field].min(),
                "max": df[field].max(),
                "variance": df[field].var()
            })
        else:
            stats_rows.append({
                "metric": field,
                "mean": None,
                "std": None,
                "median": None,
                "min": None,
                "max": None,
                "variance": None
            })

    return pd.DataFrame(stats_rows)



# Example Runs
run1 = {
    "run_id": 1,
    "raid_level": 5,
    "disk_count": 4,
    "read_time_ms": 120,
    "write_time_ms": 210,
    "read_iops": 380,
    "write_iops": 220
}

run2 = {
    "run_id": 2,
    "raid_level": 10,
    "disk_count": 8,
    "read_time_ms": 130,
    "write_time_ms": 220,
    "read_iops": 390,
    "write_iops": 230
}
run3 = {
    "run_id": 3,
    "raid_level": 3,
    "disk_count": 6,
    "read_time_ms": 175,
    "write_time_ms": 225,
    "read_iops": 380,
    "write_iops": 275
}

df = None

df = append_run(df, run1)
df = append_run(df, run2)


print("\n=== Main DataFrame ===")
print(df)

print("\n=== Statistics DataFrame ===")
stats_df = summary_statistics(df)
print(stats_df)

save_report_csv(df, "simulation_report.csv")
save_report_csv(stats_df, "statistics_report.csv")