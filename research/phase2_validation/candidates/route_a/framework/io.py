# FRAMEWORK - DO NOT EDIT (identical across all teams; the organizers use their own copy)
import os
import pandas as pd

OUTPUT_COLUMNS = ["checkup", "date", "SOH_est"]


def write_output(rows, output_dir):
    """rows: list of dicts with checkup, date, SOH_est. Appends to output.csv."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "output.csv")
    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    if os.path.exists(path):
        old = pd.read_csv(path)
        df = pd.concat([old[~old["checkup"].isin(df["checkup"])], df], ignore_index=True)
    df.sort_values("date").to_csv(path, index=False)
    return path
