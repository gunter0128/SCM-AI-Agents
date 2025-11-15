# src/agents/tools.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from src.forecasting.forecast_service import DemandForecaster
from src.inventory.rules import InventoryPlanner, InventoryPlan


@dataclass
class DemandInsight:
    """需求分析結果（給 Demand Analyst Agent 用）。"""
    item_id: str
    horizon_days: int
    daily_forecast: List[float]
    avg_daily_forecast: float


class PlanningTools:
    """
    把「需求預測 + 庫存規劃」包在一起的工具集合，
    之後 Agents 只要呼叫這裡的 method 就好。
    """

    def __init__(
        self,
        model_path: Path | str = Path("models/baseline_lgbm_ca1.pkl"),
        inventory_path: Path | str = Path("data/processed/inventory.csv"),
        store_id: str = "CA_1",
        default_horizon_days: int = 14,
    ):
        self.store_id = store_id
        self.default_horizon_days = default_horizon_days

        self.forecaster = DemandForecaster(Path(model_path), store_id=store_id)
        self.planner = InventoryPlanner(Path(inventory_path))

    # ====== 這幾個就是給 Agents 用的「工具」 ======

    def get_all_items(self) -> list[str]:
        """取得目前這個 store 庫存表裡所有 item_id。"""
        return list(self.planner.inv["item_id"].unique())

    def forecast_demand(
        self,
        item_id: str,
        horizon_days: int | None = None,
    ) -> DemandInsight:
        """Demand Analyst Agent 用：預測未來幾天銷量。"""
        if horizon_days is None:
            horizon_days = self.default_horizon_days

        forecast = self.forecaster.forecast_demand(
            item_id=item_id,
            horizon_days=horizon_days,
        )
        avg_daily = float(sum(forecast) / len(forecast))
        return DemandInsight(
            item_id=item_id,
            horizon_days=horizon_days,
            daily_forecast=forecast,
            avg_daily_forecast=avg_daily,
        )

    def compute_inventory_plan(
        self,
        item_id: str,
        forecast: List[float],
    ) -> InventoryPlan:
        """Inventory Planner Agent 用：根據預測計算缺貨風險與補貨建議。"""
        return self.planner.compute_inventory_plan(item_id, forecast)

    def analyze_item(
        self,
        item_id: str,
        horizon_days: int | None = None,
    ) -> Tuple[DemandInsight, InventoryPlan]:
        """
        整合一個品項的完整分析：
        - 預測未來需求
        - 計算缺貨風險與補貨建議
        """
        demand = self.forecast_demand(item_id, horizon_days=horizon_days)
        plan = self.compute_inventory_plan(item_id, demand.daily_forecast)
        return demand, plan
