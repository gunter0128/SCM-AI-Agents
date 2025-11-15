# src/inventory/rules.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class InventoryPlan:
    """單一品項的庫存決策結果。"""
    item_id: str
    risk_level: str
    reorder_qty: int
    projected_remaining: float
    lead_time_days: int
    safety_stock: int
    current_inventory: int


class InventoryPlanner:
    def __init__(self, inventory_path: Path | str = "data/processed/inventory.csv"):
        """
        讀取事先準備好的庫存表：
        - item_id
        - current_inventory
        - safety_stock
        - lead_time_days
        - store_id
        """
        self.inventory_path = Path(inventory_path)
        self.inv = pd.read_csv(self.inventory_path)

    def compute_inventory_plan(self, item_id: str, forecast: list[float]) -> InventoryPlan:
        """
        根據預測需求 + 庫存設定，計算：
        - 缺貨風險等級
        - 建議補貨量
        - 預期剩餘庫存

        forecast: 未來 N 天的預測需求 list（例如 horizon=14）
        """

        row = self.inv[self.inv["item_id"] == item_id]
        if row.empty:
            raise ValueError(f"Item {item_id} not found in inventory table.")

        row = row.iloc[0]

        current_inv = int(row["current_inventory"])
        safety_stock = int(row["safety_stock"])
        lead_time = int(row["lead_time_days"])

        # lead time 期間的總預測需求
        demand_lt = sum(forecast[:lead_time])

        # 預期在 lead time 結束時剩餘的庫存
        projected_remaining = current_inv - demand_lt

        # 風險等級（門檻可以之後再調整）
        if projected_remaining >= safety_stock:
            risk = "LOW"
        elif projected_remaining >= 0:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        # 建議補貨量：目標庫存 = safety_stock + demand_lt
        target_level = safety_stock + demand_lt
        reorder_qty = max(0, int(round(target_level - current_inv)))

        return InventoryPlan(
            item_id=item_id,
            risk_level=risk,
            reorder_qty=reorder_qty,
            projected_remaining=float(projected_remaining),
            lead_time_days=lead_time,
            safety_stock=safety_stock,
            current_inventory=current_inv,
        )
