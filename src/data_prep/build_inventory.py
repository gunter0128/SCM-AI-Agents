# src/data_prep/build_inventory.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

PROCESSED_DIR = Path("data/processed")


def build_inventory_from_sales(
    store_id: str = "CA_1",
    output_path: Path = PROCESSED_DIR / "inventory.csv",
):
    """
    從 daily_sales 抓出某個 store 的 item 列表，
    幫每個 item 生一份「假的但合理」的庫存設定：
    - current_inventory：最近 28 天平均銷量 * 10
    - safety_stock：最近 28 天平均銷量 * 3
    - lead_time_days：在 [3, 7, 14] 之間隨機
    """
    df = pd.read_csv(PROCESSED_DIR / "daily_sales.csv", parse_dates=["date"])

    df_store = df[df["store_id"] == store_id].copy()

    # 算每個 item 最近 28 天平均銷量
    max_date = df_store["date"].max()
    recent_start = max_date - pd.Timedelta(days=27)
    recent = df_store[df_store["date"] >= recent_start]

    avg_daily = (
        recent.groupby("item_id")["sales_qty"]
        .mean()
        .rename("avg_daily_sales")
        .reset_index()
    )

    rng = np.random.default_rng(42)

    inventory_rows = []
    for _, row in avg_daily.iterrows():
        item_id = row["item_id"]
        avg = row["avg_daily_sales"]

        # 避免有些 item 平均是 0
        base = max(avg, 1.0)

        current_inventory = int(base * 10 + rng.integers(0, 10))
        safety_stock = int(base * 3)
        lead_time_days = int(rng.choice([3, 7, 14]))

        inventory_rows.append(
            {
                "item_id": item_id,
                "current_inventory": current_inventory,
                "safety_stock": safety_stock,
                "lead_time_days": lead_time_days,
                "store_id": store_id,
            }
        )

    inv_df = pd.DataFrame(inventory_rows)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    inv_df.to_csv(output_path, index=False)
    print(f"Saved inventory table to {output_path} with {len(inv_df)} items.")


if __name__ == "__main__":
    build_inventory_from_sales()
