# src/forecasting/features.py
from __future__ import annotations
import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    依據 date 欄位加入基本時間特徵。
    需要 df['date'] 已經是 datetime64。
    """
    df = df.copy()
    df["dow"] = df["date"].dt.weekday
    df["weekofyear"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    return df


def add_lag_features(df: pd.DataFrame,
                     group_cols=("store_id", "item_id"),
                     lag_days=(7, 14)) -> pd.DataFrame:
    """
    對每個 (store_id, item_id) 做 sales_qty 的 lag 特徵。
    """
    df = df.sort_values(["store_id", "item_id", "date"]).copy()
    for lag in lag_days:
        df[f"lag_{lag}"] = (
            df.groupby(list(group_cols))["sales_qty"]
              .shift(lag)
        )
    return df


def add_rolling_features(df: pd.DataFrame,
                         group_cols=("store_id", "item_id"),
                         windows=(7, 28)) -> pd.DataFrame:
    """
    rolling mean / std 特徵。
    """
    df = df.sort_values(["store_id", "item_id", "date"]).copy()
    for win in windows:
        grp = df.groupby(list(group_cols))["sales_qty"]
        df[f"rollmean_{win}"] = grp.shift(1).rolling(win).mean()
        df[f"rollstd_{win}"] = grp.shift(1).rolling(win).std()
    return df


def build_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    串起來：時間特徵 + lag + rolling。
    這個 df 就是你之後拿去丟進模型的訓練資料。
    """
    df = add_time_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df)
    # 也可以順便填掉一部分缺失值，或過濾前幾天沒有 lag 的列
    df = df.dropna(subset=[c for c in df.columns if c.startswith("lag_")])
    return df
