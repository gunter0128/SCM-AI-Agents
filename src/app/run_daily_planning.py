# src/app/run_daily_planning.py
from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from textwrap import indent

from src.agents.tools import PlanningTools


def build_markdown_report(date_str: str, rows: list[dict]) -> str:
    """
    把所有品項的風險結果組成一份簡單的 markdown 報告。
    之後你可以用 LLM 來幫忙美化 / 撰寫中文說明。
    """
    lines: list[str] = []
    lines.append(f"# Daily Supply Chain Planning Report - {date_str}")
    lines.append("")
    lines.append("## Summary")
    total_items = len(rows)
    high_risk = sum(1 for r in rows if r["risk_level"] == "HIGH")
    medium_risk = sum(1 for r in rows if r["risk_level"] == "MEDIUM")
    low_risk = sum(1 for r in rows if r["risk_level"] == "LOW")

    lines.append(f"- Total items analyzed: **{total_items}**")
    lines.append(f"- HIGH risk items: **{high_risk}**")
    lines.append(f"- MEDIUM risk items: **{medium_risk}**")
    lines.append(f"- LOW risk items: **{low_risk}**")
    lines.append("")

    lines.append("## Top Risk Items (sorted by risk, then projected remaining)")
    lines.append("")
    lines.append("| Item ID | Risk | Reorder Qty | Projected Remaining | Current Inv | Safety Stock |")
    lines.append("|--------|------|-------------|---------------------|-------------|--------------|")

    for r in rows:
        lines.append(
            f"| {r['item_id']} | {r['risk_level']} | {r['reorder_qty']} | "
            f"{r['projected_remaining']:.1f} | {r['current_inventory']} | {r['safety_stock']} |"
        )

    return "\n".join(lines)


def main(date_str: str | None = None, top_n: int = 20):
    if date_str is None:
        date_str = datetime.today().strftime("%Y-%m-%d")

    tools = PlanningTools()
    items = tools.get_all_items()

    risk_rows: list[dict] = []

    # ===== 這裡可以想成：Demand Analyst + Inventory Planner 兩個 Agent 在合作 =====
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
            }
        )

    # 風險排序：HIGH > MEDIUM > LOW；同一級裡按 projected_remaining 由小到大（越容易缺貨排越前）
    risk_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    risk_rows.sort(key=lambda r: (risk_priority[r["risk_level"]], r["projected_remaining"]))

    top_rows = risk_rows[:top_n]

    report_md = build_markdown_report(date_str, top_rows)

    print(report_md)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date (for display only), format YYYY-MM-DD.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=20,
        help="Number of top risk items to show.",
    )
    args = parser.parse_args()

    main(date_str=args.date, top_n=args.top_n)
