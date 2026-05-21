# 流程圖與系統行為文件：台中等公車2.0

本文件基於 PRD 與系統架構設計，使用 Mermaid 語法繪製「使用者流程圖」與「系統序列圖」，並提供對應的功能與 API 路由清單，協助開發團隊釐清系統操作路徑與資料流向。

## 1. 使用者流程圖 (User Flow)

此流程圖描述一般乘客與公車司機進入系統後的完整操作路徑。

```mermaid
flowchart LR
  Start([使用者進入首頁]) --> Role{您是哪種身份？}
  
  %% 乘客流程
  Role -->|一般乘客| Home[乘客首頁]
  Home --> A1[搜尋特定公車路線]
  Home --> A2[一鍵搜尋附近站牌]
  Home --> A3[路線與轉乘規劃]
  
  A1 --> B1[查看各站預估到站時間]
  A2 --> B1
  A3 --> B2[查看建議乘車方案與轉乘指示]
  
  B1 --> C1{是否需要提醒？}
  C1 -->|是| D1[設定智慧下車提醒]
  C1 -->|否| E1([等待公車到來])
  D1 --> E1
  B2 --> E1
  
  %% 司機流程
  Role -->|公車司機| Login[司機登入頁面]
  Login -->|驗證成功| ReportUI[司機專屬回報介面]
  ReportUI --> F1[點選回報項目: 延誤/滿載/故障]
  F1 --> F2[確認並送出回報]
  F2 -->|系統提示成功| ReportUI
```

## 2. 系統序列圖 (Sequence Diagram)

### 2.1 司機即時回報流程 (寫入資料庫)
描述公車司機透過介面回報車輛狀態，資料經過 Flask 驗證並存入 SQLite 資料庫的完整流程。

```mermaid
sequenceDiagram
    actor Driver as 公車司機
    participant Browser as 司機瀏覽器
    participant Flask as Flask Route
    participant Model as Report Model
    participant DB as SQLite 資料庫

    Driver->>Browser: 點選「車輛滿載」並送出回報
    Browser->>Flask: POST /driver/report (攜帶回報狀態與座標)
    Flask->>Flask: 驗證司機 Session 權限
    Flask->>Model: 呼叫 create_report() 建立紀錄
    Model->>DB: INSERT INTO reports (driver_id, status, timestamp)
    DB-->>Model: 資料寫入成功
    Model-->>Flask: 回傳處理結果
    Flask-->>Browser: 回傳成功訊息 (重導向或 JSON)
    Browser-->>Driver: 畫面顯示「回報成功」提示
```

### 2.2 乘客查詢即時動態流程 (讀取外部 API)
描述乘客查詢特定路線時，系統向外部 TDX 開放資料平台取得即時資訊的過程。

```mermaid
sequenceDiagram
    actor User as 一般乘客
    participant Browser as 乘客瀏覽器
    participant Flask as Flask Route
    participant TDX as TDX 開放資料 API
    
    User->>Browser: 輸入「300路」並搜尋
    Browser->>Flask: GET /api/bus/300
    Flask->>TDX: 發送 API 請求取得 300 路公車最新動態
    TDX-->>Flask: 回傳 JSON 預估到站時間與 GPS 資料
    Flask->>Flask: 解析、過濾並結合司機回報狀態
    Flask-->>Browser: 回傳整理後的動態資訊
    Browser-->>User: 畫面更新顯示各站牌到站時間
```

## 3. 功能清單與路由對照表

以下為系統核心功能對應的 URL 路徑與 HTTP 方法：

| 功能名稱 | URL 路徑 | HTTP 方法 | 說明 |
| --- | --- | --- | --- |
| **乘客首頁** | `/` | GET | 顯示首頁搜尋框與附近站牌按鈕 |
| **路線與轉乘規劃** | `/route-plan` | GET | 提供起迄點輸入與規劃結果呈現 |
| **查詢公車動態頁面** | `/bus/<route_id>` | GET | 顯示特定路線的各站牌預估到站時間與介面 |
| **取得即時動態 API** | `/api/bus/<route_id>` | GET | 前端 AJAX 呼叫，由後端向 TDX 取得最新公車資料 |
| **司機登入頁面** | `/driver/login` | GET | 顯示司機專屬的登入表單 |
| **司機登入驗證** | `/driver/login` | POST | 驗證司機帳號密碼並建立登入 Session |
| **司機回報介面** | `/driver/report` | GET | 顯示適合司機快速操作（大按鈕）的專屬介面 |
| **送出狀態回報** | `/driver/report` | POST | 接收前端送出的回報資料並寫入 SQLite 資料庫 |
