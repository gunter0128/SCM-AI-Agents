# src/app/run_agents_planning.py
from __future__ import annotations

import json
from argparse import ArgumentParser
from datetime import datetime

from src.agents.tools import PlanningTools
from src.agents.domain_agents import (
    build_demand_analyst_agent,
    build_inventory_planner_agent,
    build_report_agent,
)


def main(date_str: str | None = None, top_n: int = 10):
    if date_str is None:
        date_str = datetime.today().strftime("%Y-%m-%d")

    tools = PlanningTools()
    items = tools.get_all_items()

    demand_agent = build_demand_analyst_agent()
    inv_agent = build_inventory_planner_agent()
    report_agent = build_report_agent()

    # 先做跟 run_daily_planning 類似的風險計算
    risk_rows: list[dict] = []
    for item_id in items:
        demand, plan = tools.analyze_item(item_id)

        risk_rows.append(
            {
                "item_id": item_id,
                "risk_level": plan.risk_level,
                "reorder_qty": plan.reorder_qty,
                "projected_remaining": plan.projected_remaining,
                "current_inventory": plan.current_inventory,
                "safety_stock": plan.safety_stock,
                "avg_daily_forecast": demand.avg_daily_forecast,
                "horizon_days": demand.horizon_days,
                "daily_forecast": demand.daily_forecast,
            }
        )

    # 風險排序：HIGH > MEDIUM > LOW，越容易缺貨排越前
    risk_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    risk_rows.sort(key=lambda r: (risk_priority[r["risk_level"]], r["projected_remaining"]))
    top_rows = risk_rows[:top_n]

    # 對每個 top item 呼叫兩個 Agent：需求分析 + 庫存規劃說明
    enriched_rows: list[dict] = []
    for r in top_rows:
        item_id = r["item_id"]

        # Demand Analyst Agent
        demand_msg = [
            {
                "role": "user",
                "content": (
                    f"品項 ID：{item_id}\n"
                    f"預測天數：{r['horizon_days']} 天\n"
                    f"未來 {r['horizon_days']} 天預測需求（每日）：{r['daily_forecast']}\n"
                    f"平均每日預測需求：{r['avg_daily_forecast']:.2f}"
                ),
            }
        ]
        demand_explanation = demand_agent.run(demand_msg)

        # Inventory Planner Agent
        inv_msg = [
            {
                "role": "user",
                "content": (
                    f"品項 ID：{item_id}\n"
                    f"風險等級：{r['risk_level']}\n"
                    f"目前庫存：{r['current_inventory']}\n"
                    f"安全庫存：{r['safety_stock']}\n"
                    f"預期在補貨前剩餘庫存：{r['projected_remaining']:.1f}\n"
                    f"建議補貨量：{r['reorder_qty']}"
                ),
            }
        ]
        inv_explanation = inv_agent.run(inv_msg)

        enriched = {
            **r,
            "demand_comment": demand_explanation,
            "inventory_comment": inv_explanation,
        }
        enriched_rows.append(enriched)

    # 最後交給 ReportAgent：產生給主管的中文報告
    report_input = {
        "date": date_str,
        "items": enriched_rows,
    }

    report_msg = [
        {
            "role": "user",
            "content": (
                "以下是一份今日高風險/中風險品項的分析結果（JSON 格式）：\n"
                + json.dumps(report_input, ensure_ascii=False, indent=2)
                + "\n\n請根據這些資料，產出一份給供應鏈主管看的中文報告。"
            ),
        }
    ]

    final_report = report_agent.run(report_msg)

    print("========== AI Agents Daily SCM Report ==========")
    print(final_report)
    print("================================================")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date (for description only), format YYYY-MM-DD.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Number of top risk items to analyze with agents.",
    )
    args = parser.parse_args()

    main(date_str=args.date, top_n=args.top_n)
