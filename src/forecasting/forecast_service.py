# src/forecasting/forecast_service.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import joblib

from src.forecasting.features import build_feature_table

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")


class DemandForecaster:
    def __init__(self, model_path: Path, store_id: str = "CA_1"):
        self.model = joblib.load(model_path)
        self.store_id = store_id
        self.hist_df = pd.read_csv(PROCESSED_DIR / "daily_sales.csv",
                                   parse_dates=["date"])
        self.hist_df = self.hist_df[self.hist_df["store_id"] == store_id]

    def forecast_demand(self, item_id: str, horizon_days: int = 14):
        """
        回傳未來 horizon_days 的預測銷量（簡單版）。
        之後你可以做更嚴謹的 roll-forward 預測。
        """
        # 先拿該 item 的歷史資料做最新一版特徵
        df_item = self.hist_df[self.hist_df["item_id"] == item_id].copy()
        df_feat = build_feature_table(df_item)

        # 這裡先簡化：用最後一列的特徵，代表「最近一天」的狀態
        last_row = df_feat.sort_values("date").iloc[-1:]
        X_last, _ = self._get_feature_target(last_row)

        # 暴力簡化：預測同樣的值當作未來 horizon_days 天（之後你可以改成真正的 multi-step）
        base_pred = float(self.model.predict(X_last)[0])
        preds = [max(base_pred, 0.0)] * horizon_days

        return preds

    def _get_feature_target(self, df: pd.DataFrame):
        # 和 train_baseline.py 的 get_feature_target 保持一致
        feature_cols = [
            "dow", "weekofyear", "month", "year",
            "sell_price",
            "lag_7", "lag_14",
            "rollmean_7", "rollmean_28",
        ]
        X = df[feature_cols]
        return X, None
