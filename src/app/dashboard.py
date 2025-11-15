# src/app/dashboard.py
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# 確保可以從專案根目錄 import src.*
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.agents.tools import PlanningTools
from src.agents.domain_agents import (
    build_demand_analyst_agent,
    build_inventory_planner_agent,
    build_report_agent,
)


# ========= 資料計算相關 =========

def load_item_meta(processed_path: Path = Path("data/processed/daily_sales.csv")) -> pd.DataFrame:
    """
    從 daily_sales 抓出每個 item 的基本資訊：
    item_id, cat_id, dept_id, store_id
    用來在前端顯示「品項描述」。
    """
    df = pd.read_csv(processed_path)
    meta = (
        df.groupby("item_id")
        .agg(
            cat_id=("cat_id", "first"),
            dept_id=("dept_id", "first"),
            store_id=("store_id", "first"),
        )
        .reset_index()
    )
    # 簡單組一個「看得懂」的描述（之後你可以改成手動 mapping 成品名）
    meta["item_desc"] = meta["cat_id"].astype(str) + " / " + meta["dept_id"].astype(str)
    return meta


def compute_risk_rows(tools: PlanningTools, meta_df: pd.DataFrame) -> pd.DataFrame:
    """
    跑一輪預測 + 庫存規則，回傳一個 DataFrame：
    每列就是一個品項的風險資訊 + 商品描述。
    """
    items = tools.get_all_items()
    rows: list[dict] = []

    for item_id in items:
        demand, plan = tools.analyze_item(item_id)

        rows.append(
            {
                "item_id": item_id,
                "risk_level": plan.risk_level,
                "reorder_qty": plan.reorder_qty,
                "projected_remaining": plan.projected_remaining,
                "current_inventory": plan.current_inventory,
                "safety_stock": plan.safety_stock,
                "avg_daily_forecast": demand.avg_daily_forecast,
                "horizon_days": demand.horizon_days,
            }
        )

    df = pd.DataFrame(rows)
    df = df.merge(meta_df[["item_id", "item_desc", "store_id"]], on="item_id", how="left")

    # 風險排序：HIGH > MEDIUM > LOW；同一級按 projected_remaining 由小到大
    risk_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["risk_rank"] = df["risk_level"].map(risk_priority)
    df = df.sort_values(["risk_rank", "projected_remaining"])
    return df


def build_ai_report(date_str: str, top_rows: pd.DataFrame) -> str:
    """
    呼叫三個 Agents，產生一份中文報告。
    """
    import json

    demand_agent = build_demand_analyst_agent()
    inv_agent = build_inventory_planner_agent()
    report_agent = build_report_agent()

    enriched_rows: list[dict] = []

    for _, r in top_rows.iterrows():
        item_id = r["item_id"]

        demand_msg = [
            {
                "role": "user",
                "content": (
                    f"品項 ID：{item_id}\n"
                    f"品項描述：{r.get('item_desc', '')}\n"
                    f"預測天數：{int(r['horizon_days'])} 天\n"
                    f"未來 {int(r['horizon_days'])} 天平均每日預測需求：{r['avg_daily_forecast']:.2f}"
                ),
            }
        ]
        demand_explanation = demand_agent.run(demand_msg)

        inv_msg = [
            {
                "role": "user",
                "content": (
                    f"品項 ID：{item_id}\n"
                    f"品項描述：{r.get('item_desc', '')}\n"
                    f"風險等級：{r['risk_level']}\n"
                    f"目前庫存：{int(r['current_inventory'])}\n"
                    f"安全庫存：{int(r['safety_stock'])}\n"
                    f"預期在補貨前剩餘庫存：{r['projected_remaining']:.1f}\n"
                    f"建議補貨量：{int(r['reorder_qty'])}"
                ),
            }
        ]
        inv_explanation = inv_agent.run(inv_msg)

        enriched_rows.append(
            {
                **r.to_dict(),
                "demand_comment": demand_explanation,
                "inventory_comment": inv_explanation,
            }
        )

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
    return final_report


# ========= Streamlit UI =========

def main():
    st.set_page_config(
        page_title="SCM AI Agents Dashboard",
        layout="wide",
    )

    # ---- Header ----
    st.markdown(
        """
        <h1 style="margin-bottom:0.2rem;">📦 SCM AI Agents Dashboard</h1>
        <p style="color:#666;margin-top:0;">
        Demo：用需求預測 + 庫存規則 + AI Agents，幫門市主管每天看哪些商品有缺貨風險、該補多少貨。
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ---- Sidebar ----
    st.sidebar.header("⚙️ 報告設定")

    date = st.sidebar.date_input(
        "報告日期（可選擇）",
        value=datetime.today(),
    )
    date_str = date.strftime("%Y-%m-%d")

    top_n = st.sidebar.slider("AI 報告要重點說明的品項數（Top N）", min_value=5, max_value=50, value=10, step=5)

    # ---- Data & Tools ----
    tools = PlanningTools()
    meta_df = load_item_meta()
    risk_df = compute_risk_rows(tools, meta_df)

    total_items = len(risk_df)
    high_risk = (risk_df["risk_level"] == "HIGH").sum()
    medium_risk = (risk_df["risk_level"] == "MEDIUM").sum()
    low_risk = (risk_df["risk_level"] == "LOW").sum()
    store_ids = sorted(risk_df["store_id"].dropna().unique())

    # ---- Summary Section ----
    st.subheader(f" 今日庫存風險總覽 - {date_str}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("監控品項數量", int(total_items))
    col2.metric("高風險品項", int(high_risk))
    col3.metric("中風險品項", int(medium_risk))
    col4.metric("低風險品項", int(low_risk))

    store_text = "、".join(store_ids) if store_ids else "N/A"
    st.caption(
        f"目前 Demo 是以「{store_text}」這間門市為例，"
        f"大約監控 {total_items} 個商品。歷史銷量來自公開零售資料（可以想成一間大賣場的日銷量紀錄）。"
    )

    # ---- 可解釋性：風險 + 指標說明 ----
    with st.expander("🧾 風險等級怎麼算？（白話版本）", expanded=False):
        st.markdown(
            """
- **我們關心的時間窗**：先看「補貨到貨前」這幾天（lead time）。
- **預期剩餘庫存** = 目前庫存 −「lead time 期間的預測需求總和」。

在這個前提下：

- `HIGH`：預期剩餘庫存 **會掉到 0 以下** → 很可能會缺貨  
- `MEDIUM`：預期剩餘庫存 **還大於 0，但已經低於安全庫存** → 還不會立刻缺貨，但偏危險  
- `LOW`：預期剩餘庫存 **高於安全庫存** → 相對安全  
            """
        )

    with st.expander("🧮 表格裡幾個指標是怎麼算的？", expanded=False):
        st.markdown(
            """
- **未來平均每日需求**：  
  - 用需求預測模型算出未來 14 天（可調整）的每日需求，再取平均。  
  - 直覺可以理解成：這個品項最近「大概一天會賣掉多少」。

- **預期剩餘庫存** `projected_remaining`：  
  - = 目前庫存 −「補貨到貨前幾天的預測需求總和」。  
  - 如果這個數字變成負的，代表照目前走勢會「賣得比庫存還多」，有缺貨風險。

- **安全庫存** `safety_stock`：  
  - 為了 Demo，我是用「最近一段時間的平均每日銷量 × 3 天」來當作安全庫存。  
  - 你可以把它想像成：就算需求稍微超標 2～3 天，還不會馬上缺貨的緩衝量。

- **建議補貨量** `建議補貨量`：  
  - 先把目標庫存設在：「安全庫存 + lead time 期間的預測需求」。  
  - 建議補貨量 = 目標庫存 − 目前庫存（如果算出來是負的，就當 0）。  
  - 白話：補到「先把預測中的需求補滿，再留一點安全緩衝」。
            """
        )

    st.markdown("---")

    # ---- 風險等級表格：用 Tabs 分開 ----
    st.subheader("🔥 各風險等級品項一覽")

    tab_high, tab_medium, tab_low = st.tabs(["🔴 高風險", "🟠 中風險", "🟢 低風險"])

    def show_table(df: pd.DataFrame):
        if df.empty:
            st.info("目前沒有此風險等級的品項。")
            return

        display = df[
            [
                "item_id",
                "item_desc",
                "risk_level",
                "reorder_qty",
                "projected_remaining",
                "current_inventory",
                "safety_stock",
                "avg_daily_forecast",
            ]
        ].rename(
            columns={
                "item_id": "品項 ID",
                "item_desc": "品項描述",
                "risk_level": "風險等級",
                "reorder_qty": "建議補貨量",
                "projected_remaining": "預期剩餘庫存",
                "current_inventory": "目前庫存",
                "safety_stock": "安全庫存",
                "avg_daily_forecast": "未來平均每日需求",
            }
        )

        st.dataframe(
            display,
            use_container_width=True,
            height=350,
        )

    with tab_high:
        show_table(risk_df[risk_df["risk_level"] == "HIGH"])

    with tab_medium:
        show_table(risk_df[risk_df["risk_level"] == "MEDIUM"])

    with tab_low:
        show_table(risk_df[risk_df["risk_level"] == "LOW"])

    # ---- AI Agents 報告（純按鈕，不再勾勾） ----
    st.markdown("---")
    st.subheader("🤖 AI Agents 產生的「主管報告」")

    st.caption(
        "系統會從所有品項中挑出風險最高的前 N 個，由需求分析 Agent + 庫存規劃 Agent 解釋後，"
        "再交給報告 Agent 整理成一份給主管看的中文摘要。"
    )

    if st.button("產生今日 AI 報告"):
        with st.spinner("AI Agents 正在分析今日風險與補貨建議..."):
            try:
                top_rows = risk_df.head(top_n)
                report_text = build_ai_report(date_str, top_rows)
                st.markdown(report_text)
            except Exception as e:
                st.error(f"產生 AI 報告時發生錯誤：{e}")
                st.info("請確認已設定 OPENAI_API_KEY，且模型名稱與網路連線正常。")
    else:
        st.info("按下按鈕，即可產生一份供應鏈主管閱讀的中文報告。")


if __name__ == "__main__":
    main()
