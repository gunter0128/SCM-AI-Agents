下面是你可以直接放在 repo 裡的 `README.md` 內容（整份複製貼上就行）：

---

````markdown
# SCM AI Agents – 需求預測 × 庫存風險分析 × AI 多代理決策助理

> 用「自己訓練的需求預測模型 + 庫存決策邏輯 + LLM 多代理」  
> 打造一個給供應鏈 / 門市主管用的 **每日補貨決策助理**。

---

## 1. 為什麼做這個主題？

我應徵的職位是 **Business AI Engineer / 企業內部 AI 應用工程師**。  
主管在面試時提到，他們的工作不只是「叫 OpenAI API」，而是：

- 能理解 **企業的營運流程**（像 SCM / CRM）
- 自己動手做 **資料清洗、建模與評估**
- 再把模型與 **業務邏輯 + LLM + 前端** 串起來，變成主管用得懂的工具

所以我希望有一個作品可以同時展示：

1. 我會從頭處理真實的時序銷量資料（不是玩 toy dataset）
2. 自己訓練一個需求預測模型（特徵工程、切資料、調參 / 評估）
3. 把預測轉成 **可解釋的庫存風險與補貨建議**
4. 再用 LLM 做成多個「角色分工清楚」的 AI Agents，負責：
   - 需求分析
   - 庫存規劃說明
   - 風險排序
   - 幫主管寫中文摘要報告
5. 最後用一個簡單的 Dashboard 視覺化整套流程

這個專案的目標，是讓主管看到：

> 我不只是會用 LLM，而是有能力  
> **把資料 → 模型 → 業務規則 → AI Agents → 產品 Demo** 串成一條完整的鏈。

---

## 2. 專案整體設計概觀

### 2.1 系統目標

每天早上讓「門市 / 供應鏈主管」可以得到一份：

- 哪些商品在補貨到貨前會有缺貨風險？
- 每個商品 **建議補貨量是多少？**
- 目前庫存相比安全庫存有多危險？
- AI 幫你用中文總結「今天最需要注意什麼」，避免逐筆看表格。

### 2.2 架構一覽

整體可以想成 4 層：

1. **資料處理層（Data Prep）**
   - 從 M5 原始資料 `sales_train_*.csv` + `sell_prices.csv` 整理成  
     `data/processed/daily_sales.csv`
   - 一筆代表：`date, store_id, item_id, sales_qty, price, ...`

2. **需求預測層（Forecasting）**
   - 做日期特徵（星期幾、月份、是否週末）
   - 做 lag / rolling 特徵（前 7/14 天平均銷量、波動）
   - 用 LightGBM 訓練 **每日銷量預測模型**
   - 封裝成一個服務函式：

     ```python
     forecast_service.forecast_item(item_id, horizon_days=14)
     ```

3. **庫存決策層（Inventory Logic）**
   - 假設每個商品有：
     - 目前庫存 `current_inventory`
     - 補貨前的 lead time（幾天後到貨）
     - 安全庫存 `safety_stock`
   - 根據預測 + 庫存規則，計算：
     - 補貨前「預期剩餘庫存」 `projected_remaining`
     - 風險等級（HIGH / MEDIUM / LOW）
     - 建議補貨量 `reorder_qty`

   並提供統一介面：

   ```python
   tools = PlanningTools()
   demand, plan = tools.analyze_item(item_id)
````

4. **AI Agents + Dashboard 層（Decision & Presentation）**

   * 多個 LLM-based agents：

     * DemandAnalystAgent：解釋需求變化、是否異常
     * InventoryPlannerAgent：解釋為何需要/不需要補貨
     * ReportAgent：幫主管寫出「今日重點摘要」
   * Streamlit Dashboard：

     * 顯示高 / 中 / 低風險商品列表
     * 一鍵產生「主管報告」中文摘要（需自行提供 API key）

---

## 3. 使用的資料集：M5 Forecasting

本專案使用公開的 **M5 Forecasting - Accuracy** 資料集（Walmart 銷量資料）。

由於單檔檔案超過 GitHub 100MB 限制，**原始資料不直接放在 repo 裡**。
如需重現，請自行從 Kaggle 下載（需登入帳號）：

* `sales_train_evaluation.csv`
* `sales_train_validation.csv`
* `sell_prices.csv`
* `calendar.csv`

> 資料集概念上可以想成「美國某連鎖賣場在不同門市、不同商品的每日銷量與價格記錄」。

---

## 4. 專案結構說明

```text
scm-ai-agents/
├─ data/
│  ├─ raw/                 # 放 M5 原始資料（不在 GitHub 上）
│  └─ processed/
│     └─ daily_sales.csv   # 經過整理與聚合後的日銷量表
├─ models/
│  └─ lgbm_baseline.pkl    # 訓練好的 LightGBM 需求預測模型
├─ src/
│  ├─ data_prep/
│  │  └─ build_dataset.py  # 將 M5 raw 資料轉成 daily_sales
│  ├─ forecasting/
│  │  ├─ features.py       # 特徵工程（日期、lag、rolling）
│  │  ├─ train_baseline.py # 訓練 LightGBM baseline
│  │  └─ forecast_service.py # 用訓練好的模型做預測
│  ├─ agents/
│  │  ├─ rules.py          # 庫存規則邏輯（安全庫存、風險、補貨量）
│  │  ├─ tools.py          # 包成 PlanningTools，可供其他程式呼叫
│  │  ├─ base.py           # 通用 LLM Agent 基底（用 OpenAI API）
│  │  └─ domain_agents.py  # Demand / Inventory / Report 三種 Agent 定義
│  └─ app/
│     ├─ demo_one_item.py      # 指令列 demo：單一商品的預測與補貨建議
│     ├─ run_daily_planning.py # 指令列 demo：全商品風險報告（不含 LLM）
│     └─ dashboard.py          # Streamlit 前端 Dashboard
└─ requirements.txt
```

---

## 5. 如何重現實驗與操作

### 5.1 環境需求

* Python 3.10+（建議 3.10 或 3.11）
* pip / virtualenv 或 conda
* Git
* （選配）OpenAI API Key，如果要體驗 AI Agents 中文報告

---

### 5.2 安裝步驟

```bash
# 1. 取得專案
git clone https://github.com/<your-account>/scm-ai-agents.git
cd scm-ai-agents

# 2. 建立虛擬環境（以 venv 為例）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

# 3. 安裝套件
pip install -r requirements.txt
```

---

### 5.3 下載 M5 資料並放到正確位置

1. 前往 Kaggle 的 **M5 Forecasting - Accuracy** 頁面
2. 下載以下檔案並放到專案的：

   ```
   data/raw/
   ├─ sales_train_evaluation.csv
   ├─ sales_train_validation.csv
   ├─ sell_prices.csv
   └─ calendar.csv
   ```

**注意：`data/raw/` 不在 GitHub 上，需由使用者自行建立。**

---

### 5.4 建立處理後的日銷量資料表

```bash
python -m src.data_prep.build_dataset
```

成功後會產生：

* `data/processed/daily_sales.csv`

這是一張乾淨的主表：

`date, store_id, item_id, sales_qty, price, ...`
之後所有模型訓練與 dashboard 都用這張表。

---

### 5.5 訓練需求預測模型（LightGBM baseline）

```bash
python -m src.forecasting.train_baseline
```

這一步會：

* 讀取 `data/processed/daily_sales.csv`
* 做特徵工程（日期 / lag / rolling）
* 切 train / valid / test（依時間）
* 訓練 LightGBM 回歸模型
* 輸出模型到 `models/lgbm_baseline.pkl`
* 在終端機印出 RMSE / MAPE 等指標

---

### 5.6 測試單一商品的預測 + 補貨建議（指令列）

```bash
python -m src.app.demo_one_item
```

會在終端機顯示類似：

```text
=== Item: HOBBIES_1_001 ===
Forecast next 14 days: [1.2, 1.3, ...]
Current inventory   : 30
Safety stock        : 8
Projected remaining : -5.2
Risk level          : HIGH
Suggested reorder   : 20
Reason              : ...
```

---

### 5.7 對所有商品產生「每日風險報告」（不含 LLM）

```bash
python -m src.app.run_daily_planning --top_n 20
```

會依風險排序列出 Top N 高風險商品及建議補貨量，可直接貼進 Excel 或報告。

---

### 5.8 啟動 Dashboard（含高/中/低風險視覺化）

```bash
streamlit run src/app/dashboard.py
```

打開瀏覽器（預設 `http://localhost:8501`），可以看到：

* 今日總覽：監控品項數、高 / 中 / 低風險數量
* 分頁 Tabs：

  * 🔴 高風險商品表
  * 🟠 中風險商品表
  * 🟢 低風險商品表
* 每一列顯示：

  * 品項 ID
  * 品項描述
  * 風險等級
  * 目前庫存
  * 安全庫存
  * 預期剩餘庫存
  * 建議補貨量
  * 未來平均每日需求

同時在底下有兩個「可解釋性」說明：

* 風險等級怎麼算（HIGH / MEDIUM / LOW）
* 預期剩餘庫存 / 安全庫存 / 建議補貨量 是如何計算

---

### 5.9（選配）啟用 AI Agents 中文主管報告

如果你有 OpenAI API key，可以啟用多代理解釋層。

1. 在專案根目錄建立 `.env`：

   ```bash
   OPENAI_API_KEY=sk-xxxxxx
   ```

2. 程式啟動時會自動讀取環境變數

3. 重新執行 Dashboard：

   ```bash
   streamlit run src/app/dashboard.py
   ```

4. 在頁面底部按下：

   > 「產生今日 AI 報告」

系統會：

* 對 Top N 高風險商品呼叫：

  * DemandAnalystAgent（解釋需求變化）
  * InventoryPlannerAgent（解釋庫存與補貨理由）
* 再交給 ReportAgent 整理成一份**給主管閱讀的中文摘要報告**

> 若沒有設定 API key，除了這段 AI 報告，其餘流程仍然可完全重現。

---

## 6. 模型與指標的可解釋性設計

在面對企業內部主管時，解釋清楚「模型怎麼來、指標怎麼算」很重要。
這個專案刻意設計成：

### 6.1 需求預測模型

* **模型類型**：LightGBM Regression
* **特徵**：

  * 日期特徵：星期幾、月份、是否週末
  * Lag 特徵：過去 7 / 14 天平均銷量
  * Rolling 統計：近幾天的平均 / 標準差
* **資料切分**：用時間切（train / valid / test），避免洩漏未來
* **評估指標**：RMSE / MAPE

這樣的選擇方便向主管說明：「不是黑盒 NN，而是較易控制、可快速迭代的樹模型。」

### 6.2 庫存與風險邏輯（從預測到決策）

* **預期剩餘庫存**
  `projected_remaining = current_inventory − 預測的 lead time 需求總和`

* **安全庫存（Safety Stock）**
  Demo 中設計為「近期平均每日銷量 × 3 天」，
  代表就算需求多出兩三天，仍有緩衝。

* **風險等級**：

  * HIGH：預期剩餘庫存 < 0（在補貨到貨前可能缺貨）
  * MEDIUM：0 ≤ 預期剩餘庫存 < 安全庫存
  * LOW：預期剩餘庫存 ≥ 安全庫存

* **建議補貨量**：
  目標庫存 = 安全庫存 + lead time 需求
  建議補貨量 = max(0, 目標庫存 − 目前庫存)

這些規則完全實作在 `src/agents/rules.py`，可讀性高，也易於日後與企業內部的 SCM 團隊一起修改。

---

## 7. 對企業 / 供應鏈部門的可能價值

從 Business AI Engineer 的角度來看，這個專案的價值主要有幾點：

1. **把歷史資料變成每日可用的「補貨建議」**

   * 不只是做一個 forecasting model，而是延伸到
     「缺貨風險判斷」與「補貨量計算」。

2. **降低主管盯表格的時間，提高決策效率**

   * 傳統上主管需要自己看數據、估預測、算庫存。
   * 這套系統每天自動跑完一次，主管只需看：

     * 今日高風險商品清單
     * 建議補貨量
     * AI 整理的中文摘要說明

3. **可被 IT 團隊接手擴充 / 上線**

   * 已經拆成清楚模組：data prep / model / rules / agents / app
   * 可以很容易：

     * 替換成公司自己的銷售 / 庫存資料表
     * 改成放到內部 API / Batch job / BI 報表

4. **多代理架構展示了 LLM 在企業場景中的應用方式**

   * 而不是一個單一 Chatbot，而是：

     * 專門看需求的 Agent
     * 專門看庫存的 Agent
     * 專門寫報告的 Agent
   * 這樣更貼近實際「把 LLM 嵌入業務流程」的樣貌。

5. **安全性與可替換性**

   * LLM 部分只依賴 `OPENAI_API_KEY` 環境變數，不寫死在程式碼，符合企業安全實務。
   * 將來可以直接替換為：

     * 公司自架模型
     * 其他 vendor 的 LLM API
     * 甚至內部的多語言 NLG 模型
