# src/app/demo_one_item.py
from __future__ import annotations
from pathlib import Path

from src.forecasting.forecast_service import DemandForecaster
from src.inventory.rules import InventoryPlanner


def main(item_id: str = None):
    model_path = Path("models/baseline_lgbm_ca1.pkl")
    forecaster = DemandForecaster(model_path, store_id="CA_1")
    planner = InventoryPlanner("data/processed/inventory.csv")

    # 如果沒指定 item_id，就拿 inventory.csv 第一個
    if item_id is None:
        item_id = planner.inv["item_id"].iloc[0]

    forecast_horizon = 14
    forecast = forecaster.forecast_demand(item_id=item_id, horizon_days=forecast_horizon)

    plan = planner.compute_inventory_plan(item_id, forecast)

    print(f"=== Item: {item_id} ===")
    print(f"Forecast next {forecast_horizon} days: {forecast}")
    print(f"Current inventory   : {plan.current_inventory}")
    print(f"Safety stock        : {plan.safety_stock}")
    print(f"Lead time (days)    : {plan.lead_time_days}")
    print(f"Projected remaining : {plan.projected_remaining:.1f}")
    print(f"Risk level          : {plan.risk_level}")
    print(f"Suggested reorder   : {plan.reorder_qty} units")


if __name__ == "__main__":
    main()
