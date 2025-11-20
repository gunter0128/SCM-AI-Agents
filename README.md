# SCM AI Agents  
### 需求預測 × 庫存風險分析 × AI 多代理決策助理

> 使用「自行訓練的需求預測模型＋庫存決策邏輯＋LLM 多代理（Agents）」  
> 幫助供應鏈 / 門市主管產生 **每日補貨決策報告**。

---

## 1. 為什麼選擇這個主題？

我應徵的是 **Business AI Engineer**，這個角色的核心能力是：

- 了解企業內部流程（SCM / CRM）
- 能處理真實資料、建模、優化流程
- 能將模型與業務規則整合，做成可用的工具
- 不是只會叫 API，而是會設計一條完整的 AI 流程

因此我希望做一個能完整展示：

- 真實時序資料（非 toy dataset）
- 自己做 ETL、特徵工程、建模、評估
- 可解釋的庫存規則模型
- 可執行的 **需求預測 + 風險偵測 + 補貨建議**
- 用 LLM 多代理幫主管寫每日摘要報告
- 有前端 Dashboard 可以 Demo

這個專案目的：  
**讓主管快速知道我能將資料→模型→規則→LLM→前端整合成一套可用的系統。**

---
懂！
你的主管要的是：
**Problem / Input / Output 三段式的快速摘要（讓外行一看就懂你的 Side Project 在幹嘛）。**

我現在會依照你 SCM AI Agents 專案的內容，**完全套用你給的格式範本（Problem / Input / Output / 使用資料集）** 幫你寫一份正式、乾淨、主管會喜歡的版本。

你可以直接貼回 README「快速總覽」區。

---

# ✅ **SCM AI Agents 專案：快速總覽（Problem / Input / Output）**

```markdown
## 專案快速總覽（Problem / Input / Output）

---

## 要解決的問題（Problem）

供應鏈現場常面臨以下痛點：

- 店長或補貨人員每日需人工檢查大量商品的庫存與銷量  
- 不知道哪些商品「快缺貨」、哪些「太多庫存」  
- 預測未來銷量的工作完全依靠經驗，不具數據依據  
- 補貨決策分散、沒有統一規則，容易造成斷貨或庫存堆積  
- 每日營運報告需人工彙整，耗時且不一致  

本專案透過 **需求預測模型 + 庫存風險規則 + LLM 多代理**，  
協助供應鏈主管 **自動產生每日補貨決策與 AI 中文主管報告**。

---

## 系統輸入（Input）

### 1. 歷史銷量資料（M5 Dataset）
每筆包含：

- `date`（每日）
- `store_id`（門市）
- `item_id`（商品）
- `sales_qty`（銷量）
- `sell_price`（售價）
- `event_name` / `event_type`（節慶/促銷資訊）

### 2. 庫存結構（自建資料）
每項商品包含：

- `current_inventory`（目前庫存量）
- `lead_time_days`（補貨到貨需時）
- `safety_stock`（安全庫存）

### 3. 使用者操作（輸入）
- 可選擇任一商品，查看：
  - 預測未來 14 天需求  
  - 缺貨風險  
  - 建議補貨量  
- 可按下按鈕產生：
  - AI 中文主管報告

---

## 系統輸出（Output）

### 1. 商品層級（Per Item）
- 未來 14 天每日需求預測（由 LightGBM 基準模型產生）
- 安全庫存與補貨基準
- 缺貨風險分類：**高 / 中 / 低**
- 建議補貨量（套用庫存規則計算）
- 可解釋性資訊：
  - 「為什麼是高風險？」
  - 「未來需求是多少？」
  - 「預計什麼時候會缺貨？」

### 2. 全品項摘要（Top-N）
- 今日最危險的 Top N 商品
- 每項風險原因（例：庫存不足、未來需求上升）
- 補貨清單（商品、數量、建議下單日）

### 3. AI 主管報告（Multi-Agent LLM）
按下按鈕後輸出：

- 今日營運摘要（人類主管口吻）
- 高風險商品重點
- 必須下單的品項＋原因
- 庫存異常提醒
- 建議行動項目（Action Items）

> 範例（節錄）：  
> 「今日共有 12 項商品屬於高風險，其中 *HOUSEHOLD_1_009* 預計在 4 天後缺貨，建議立即補貨 28 單位。近期需求因周末效應上升，保持較高安全水位較為合適。」

---

## 使用資料集：M5 Forecasting（Kaggle）

本專案使用零售業真實資料集 M5，包含：

- `sales_train_validation.csv`（每日銷量）
- `sales_train_evaluation.csv`
- `sell_prices.csv`（不同商品/門市的動態價格）
- `calendar.csv`（節日、促銷、特殊事件）

資料來源：  
https://www.kaggle.com/competitions/m5-forecasting-accuracy/data

因原始資料（100MB+）無法放入 GitHub，需自行下載至：

```

data/raw/

```

### 處理後資料格式（daily_sales.csv）

| date       | store_id | item_id | sales_qty | price | event_type |
|-----------|----------|---------|-----------|-------|------------|
| 2016-01-01 | CA_1     | HOBBIES_1_001 | 2 | 8.3 | NaN |

該資料為後續 **特徵工程、模型訓練、風險計算** 的主資料表。

---

## 2. 系統架構概觀

整體分為四層：

### **2.1 資料處理層（Data Prep）**
- 使用 M5 Dataset 的銷量、價格、節日資料  
- 整理成 `daily_sales.csv`（date × store × item）

### **2.2 需求預測層（Forecasting）**
- 特徵工程（日期特徵、lag、rolling）
- LightGBM 回歸模型
- 預測未來 14 天每日需求

### **2.3 庫存決策層（Inventory Rules）**
- 使用 safety stock / lead time / 預期需求計算：
  - 是否缺貨
  - 風險等級（HIGH / MEDIUM / LOW）
  - 建議補貨量（reorder_qty）

### **2.4 AI Agents 層（LLM 多代理）**
- Demand Analyst Agent  
- Inventory Planner Agent  
- Supervisor Report Agent  

負責解釋原因、彙整報告、輸出中文主管摘要。

---

## 3. 使用資料集：M5 Forecasting（Kaggle）

資料集來源：  
https://www.kaggle.com/competitions/m5-forecasting-accuracy/data

專案使用以下四份：

```

sales_train_validation.csv
sales_train_evaluation.csv
sell_prices.csv
calendar.csv

````

> 由於檔案超過 GitHub 限制（100MB），需自行下載放入：  
> `data/raw/`

---

## 4. 專案目錄結構

```text
scm-ai-agents/
├─ data/
│  ├─ raw/                         # 放 M5 原始資料（需自行從 Kaggle 下載）
│  └─ processed/
│     └─ daily_sales.csv           # 整理後的「日銷量主表」（後續訓練與預測都用這張）
├─ models/
│  └─ lgbm_baseline.pkl            # 訓練好的 LightGBM 需求預測模型
├─ src/
│  ├─ data_prep/
│  │  └─ build_dataset.py          # 從 M5 raw 資料組合、清洗，產生 daily_sales.csv
│  │
│  ├─ forecasting/
│  │  ├─ features.py               # 特徵工程：日期特徵、lag、rolling 等特徵的建立
│  │  ├─ train_baseline.py         # 使用 daily_sales + features 訓練 LightGBM baseline，並存成 lgbm_baseline.pkl
│  │  └─ forecast_service.py       # 封裝預測邏輯：載入模型與資料，提供 forecast_item() 等預測介面
│  │
│  ├─ agents/
│  │  ├─ tools.py                  # 把「預測模型 + 庫存規則」包成 PlanningTools，提供 analyze_item() 等高階工具
│  │  ├─ base.py                   # 通用 LLM Agent 基底類別：負責呼叫 OpenAI API、處理訊息與回覆
│  │  └─ domain_agents.py          # 定義實際使用的三個 Agent：需求分析、庫存規劃、主管報告等角色與 prompt
│  │
│  ├─ inventory/
│  │  └─ rules.py                  # 純規則的庫存邏輯：計算安全庫存、預期剩餘庫存、風險等級與建議補貨量
│  │
│  └─ app/
│     ├─ demo_one_item.py          # 指令列 demo：針對單一商品顯示預測結果與庫存決策（方便說明流程）
│     ├─ run_agents_planning.py    # 指令列 demo：結合 Agents，產生文字版「主管報告」（不透過 dashboard）
│     ├─ run_daily_planning.py     # 指令列 demo：跑完所有商品風險，列出 Top N 高風險品項與補貨建議
│     └─ dashboard.py              # Streamlit 前端：顯示高/中/低風險表格＋按鈕呼叫 AI Agents 產生中文主管報告
│
└─ requirements.txt                # 專案所需 Python 套件列表，方便一鍵安裝與環境重現
```

---

## 5. 如何重現專案

### **5.1 建立環境**

```bash
git clone https://github.com/<your-account>/scm-ai-agents.git
cd scm-ai-agents

python -m venv venv
venv/Scripts/activate  # Windows
# source venv/bin/activate  # Mac / Linux
$env:OPENAI_API_KEY="你的API_KEY"(若沒有api_key可見demo.pdf中的展示結果截圖)

pip install -r requirements.txt
```

---

### **5.2 放置資料集**

手動將 M5 資料放到：

```
data/raw/
```

---

### **5.3 建立處理後資料表**

```bash
python -m src.data_prep.build_dataset
```

成功後會產生：

```
data/processed/daily_sales.csv
```

---

### **5.4 訓練需求預測模型**

```bash
python -m src.forecasting.train_baseline
```

完成後會在：

```
models/lgbm_baseline.pkl
```

---

### **5.5 測試單一商品（指令列 Demo）**

```bash
python -m src.app.demo_one_item
```

---

### **5.6 跑每日風險報告（不含 AI Agents）**

```bash
python -m src.app.run_daily_planning --top_n 20
```
#### 若成功執行會呈現以下效果

<img width="512" height="746" alt="image" src="https://github.com/user-attachments/assets/7b92d8be-57ad-4331-b7ea-b7db014fd752" />

---

### **5.7 啟動 Streamlit Dashboard**

```bash
streamlit run src/app/dashboard.py
```

功能：

* 高 / 中 / 低風險商品表
* 補貨建議
* 可解釋性資訊
* 一鍵生成主管報告（需 API key）

---

### **5.8（選配）啟動 AI Agents 中文報告**

建立 `.env`：

```
OPENAI_API_KEY=sk-xxxx
```

---

## 6. 模型與規則的可解釋性設計

### **6.1 需求預測模型（LightGBM）**

* 日期特徵（weekday/month）
* lag 特徵（過去 7 / 14）
* rolling 特徵（平均、標準差）
* 時間切割 train/valid/test

### **6.2 庫存規則（rules.py）**

**預期剩餘庫存**

```
projected_remaining = current_inventory - sum(predicted_demand_during_lead_time)
```

**安全庫存 Safety Stock**

```
safety_stock = recent_avg_daily_demand * 3
```

**風險等級**

* HIGH：projection < 0
* MEDIUM：0 ≤ projection < safety_stock
* LOW：projection ≥ safety_stock

**建議補貨量**

```
target_stock = safety_stock + lead_time_demand
reorder_qty = max(0, target_stock - current_inventory)
```

---

## 7. 企業價值（Business Impact）

本專案對企業的價值：

### **① 讓歷史資料變成每日的補貨建議**

主管不用手動算預測、庫存、風險。

### **② 降低人工盯表格的時間**

Dashboard + AI 報告極大提升決策效率。

### **③ 可真正整合到企業內部系統**

模組化設計易於接軌：

* ERP / WMS
* 日批次排程
* 內部 API Gateway
* 公司自有 LLM

### **④ 多代理（LLM Agents）貼近企業實務**

每個 Agent 負責不同任務，像真正的部門分工。

### **⑤ 安全、可替換的設計**

不硬綁 API key；可自由切換模型。
