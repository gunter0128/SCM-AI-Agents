# src/forecasting/train_baseline.py
from __future__ import annotations
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from lightgbm import LGBMRegressor
import joblib

from src.forecasting.features import build_feature_table

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")


def load_daily_sales() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "daily_sales.csv", parse_dates=["date"])
    return df


def select_subset(df: pd.DataFrame,
                  store_id: str = "CA_1") -> pd.DataFrame:
    """
    先只對單一 store 做模型，之後你可以擴展成多 store / 全局模型。
    """
    return df[df["store_id"] == store_id].copy()


def train_val_test_split(df: pd.DataFrame,
                         val_days: int = 28,
                         test_days: int = 28):
    """
    用時間切分資料。
    """
    df = df.sort_values("date")
    max_date = df["date"].max()

    test_start = max_date - pd.Timedelta(days=test_days - 1)
    val_start = test_start - pd.Timedelta(days=val_days)

    train = df[df["date"] < val_start]
    val = df[(df["date"] >= val_start) & (df["date"] < test_start)]
    test = df[df["date"] >= test_start]

    return train, val, test


def get_feature_target(df: pd.DataFrame):
    """
    把想當特徵的欄位挑出來。
    """
    target_col = "sales_qty"

    feature_cols = [
        "dow", "weekofyear", "month", "year",
        "sell_price",
        "lag_7", "lag_14",
        "rollmean_7", "rollmean_28",
        # 之後可以加 one-hot 的 item_id / dept_id 等
    ]

    X = df[feature_cols]
    y = df[target_col]
    return X, y


def train_baseline_model():
    df = load_daily_sales()
    df = select_subset(df)

    df_feat = build_feature_table(df)

    train, val, test = train_val_test_split(df_feat)

    X_train, y_train = get_feature_target(train)
    X_val, y_val = get_feature_target(val)
    X_test, y_test = get_feature_target(test)

    model = LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="rmse",
    )

    # 評估
    def eval_and_print(split_name, X, y):
        preds = model.predict(X)
        # 舊版 sklearn 沒有 squared 參數，就自己開根號
        mse = mean_squared_error(y, preds)
        rmse = mse ** 0.5
        mape = mean_absolute_percentage_error(y, preds)
        print(f"{split_name} - RMSE: {rmse:.3f}, MAPE: {mape:.3f}")


    eval_and_print("Train", X_train, y_train)
    eval_and_print("Val", X_val, y_val)
    eval_and_print("Test", X_test, y_test)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / "baseline_lgbm_ca1.pkl")


if __name__ == "__main__":
    train_baseline_model()
