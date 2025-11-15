# src/data_prep/build_dataset.py
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def load_raw_m5(raw_dir: Path = RAW_DIR):
    """讀取 M5 的三個主要 raw 檔案。"""
    sales = pd.read_csv(raw_dir / "sales_train_validation.csv")
    calendar = pd.read_csv(raw_dir / "calendar.csv")
    prices = pd.read_csv(raw_dir / "sell_prices.csv")
    return sales, calendar, prices


def filter_subset(
    sales: pd.DataFrame,
    state_ids=("CA",),          # 只拿 CA 州
    store_ids=("CA_1",),        # 只拿 CA_1 這間店
    max_items_per_store: int = 50,  # 每個 store 最多 50 個 item
) -> pd.DataFrame:
    """
    真的縮小資料量：
    - 只取指定州 (state_id)
    - 只取指定 store_id
    - 每個 store 最多取 N 個 item
    """
    subset = sales[
        sales["state_id"].isin(state_ids)
        & sales["store_id"].isin(store_ids)
    ].copy()

    # 每個 store 取前 N 個 item（就算亂選，對我們 demo 也夠用）
    subset = subset.groupby("store_id").head(max_items_per_store).copy()

    return subset



def melt_sales_to_long(sales_subset: pd.DataFrame) -> pd.DataFrame:
    """
    把 d_1 ~ d_1913 這種 wide format 轉成長表：
    一列 = store_id, item_id, d_xx, sales_qty
    """
    id_cols = ["id", "item_id", "dept_id", "cat_id",
               "store_id", "state_id"]
    value_cols = [c for c in sales_subset.columns if c.startswith("d_")]

    long_df = sales_subset.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name="d",
        value_name="sales_qty"
    )
    return long_df


def add_calendar_features(long_df: pd.DataFrame,
                          calendar: pd.DataFrame) -> pd.DataFrame:
    """
    把 d_xx join 到 calendar，拿到真的日期、weekday、month、event 等。
    """
    merged = long_df.merge(calendar, how="left", left_on="d", right_on="d")
    # 重點欄位先整理一下
    merged["date"] = pd.to_datetime(merged["date"])
    merged["weekday"] = merged["wday"]
    merged["month"] = merged["month"]

    # 做一個簡單的 event flag
    merged["is_event"] = merged["event_name_1"].notna().astype(int)
    return merged


def add_price(long_df: pd.DataFrame,
              prices: pd.DataFrame) -> pd.DataFrame:
    """
    把 sell_prices.csv merge 進來，補上價格資訊。
    """
    out = long_df.merge(
        prices,
        how="left",
        on=["store_id", "item_id", "wm_yr_wk"]
    )
    return out


def build_and_save_daily_table():
    sales, calendar, prices = load_raw_m5()
    subset = filter_subset(sales)
    long_df = melt_sales_to_long(subset)
    with_cal = add_calendar_features(long_df, calendar)
    full = add_price(with_cal, prices)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    full.to_csv(PROCESSED_DIR / "daily_sales.csv", index=False)


if __name__ == "__main__":
    build_and_save_daily_table()
