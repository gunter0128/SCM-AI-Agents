```markdown
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
│  ├─ raw/                 # 放 M5 原始資料 (需自行下載)
│  └─ processed/
│     └─ daily_sales.csv   # 處理後的主資料表
├─ models/
│  └─ lgbm_baseline.pkl    # 訓練後需求預測模型
├─ src/
│  ├─ data_prep/
│  │  └─ build_dataset.py
│  ├─ forecasting/
│  │  ├─ features.py
│  │  ├─ train_baseline.py
│  │  └─ forecast_service.py
│  ├─ agents/
│  │  ├─ rules.py
│  │  ├─ tools.py
│  │  ├─ base.py
│  │  └─ domain_agents.py
│  └─ app/
│     ├─ demo_one_item.py
│     ├─ run_daily_planning.py
│     └─ dashboard.py
└─ requirements.txt
````

---

## 5. 如何重現專案

### **5.1 建立環境**

```bash
git clone https://github.com/<your-account>/scm-ai-agents.git
cd scm-ai-agents

python -m venv venv
venv/Scripts/activate  # Windows
# source venv/bin/activate  # Mac / Linux

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
