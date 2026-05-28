# 路由設計文件：台中等公車2.0

本文件基於 PRD、架構設計與流程圖，規劃 Flask 應用程式的路由、HTTP 方法與對應的 Jinja2 模板，並提供每個路由的詳細邏輯說明。

## 1. 路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| --- | --- | --- | --- | --- |
| **首頁** | GET | `/` | `templates/index.html` | 顯示搜尋路線與附近站牌功能 |
| **路線與轉乘規劃** | GET | `/route-plan` | `templates/route_plan.html` | 顯示起迄點輸入表單與規劃結果 |
| **特定路線動態** | GET | `/bus/<route_id>` | `templates/bus_status.html` | 顯示特定公車的預估到站時間 |
| **取得動態 API** | GET | `/api/bus/<route_id>` | — (回傳 JSON) | 前端 AJAX 用，整合 TDX 與回報資料 |
| **司機登入頁面** | GET | `/driver/login` | `templates/driver_login.html` | 顯示司機登入表單 |
| **司機登入驗證** | POST | `/driver/login` | — | 驗證帳號密碼並建立 Session |
| **司機回報頁面** | GET | `/driver/report` | `templates/driver_report.html` | 顯示司機專屬的回報按鈕介面 |
| **司機送出回報** | POST | `/driver/report` | — | 接收回報狀態，寫入資料庫並重新導向 |
| **司機登出** | POST | `/driver/logout` | — | 清除 Session 並導回首頁或登入頁 |

## 2. 每個路由的詳細說明

### 2.1 Main 路由 (`app/routes/main.py`)

- **GET `/` (首頁)**
  - 輸入：無
  - 處理邏輯：準備必要的初始資料（如熱門路線），供前端渲染。
  - 輸出：渲染 `index.html`
  - 錯誤處理：無特殊錯誤，正常回傳 200。

- **GET `/route-plan` (路線與轉乘規劃)**
  - 輸入：URL Query 參數 `start` (起點), `end` (迄點)
  - 處理邏輯：若有起迄點，則呼叫 TDX 規劃 API 計算轉乘方案；若無則顯示空白表單。
  - 輸出：渲染 `route_plan.html`，帶入規劃結果。
  - 錯誤處理：起迄點無效時提示使用者重新輸入。

### 2.2 Bus 路由 (`app/routes/bus.py`)

- **GET `/bus/<route_id>` (特定路線動態)**
  - 輸入：`route_id` (如 '300')
  - 處理邏輯：確認路線是否存在。
  - 輸出：渲染 `bus_status.html`，帶入路線基本資訊。
  - 錯誤處理：若路線不存在回傳 404，並導向自訂 404 頁面。

- **GET `/api/bus/<route_id>` (取得動態 API)**
  - 輸入：`route_id`
  - 處理邏輯：
    1. 呼叫 TDX API 取得即時動態與預估到站時間。
    2. 呼叫 `Report.get_by_route(route_id)` 取得近期司機回報的狀況（例如延誤、滿載）。
    3. 合併資料。
  - 輸出：回傳 JSON 格式的公車資料。
  - 錯誤處理：TDX API 失敗時回傳預設錯誤 JSON 且 HTTP Status 500。

### 2.3 Driver 路由 (`app/routes/driver.py`)

- **GET `/driver/login` (司機登入頁面)**
  - 輸入：無
  - 處理邏輯：檢查若已登入，直接重導至 `/driver/report`。
  - 輸出：渲染 `driver_login.html`。

- **POST `/driver/login` (司機登入驗證)**
  - 輸入：表單欄位 `username`, `password`
  - 處理邏輯：使用 `Driver.get_by_username()` 查詢，驗證密碼雜湊。成功則寫入 session。
  - 輸出：成功重導至 `/driver/report`；失敗回傳登入頁面並顯示錯誤訊息。

- **GET `/driver/report` (司機回報頁面)**
  - 輸入：無
  - 處理邏輯：檢查 session 是否已登入，未登入重導至登入頁。
  - 輸出：渲染 `driver_report.html`。

- **POST `/driver/report` (司機送出回報)**
  - 輸入：表單欄位 `route_id`, `status`, `latitude` (可選), `longitude` (可選)
  - 處理邏輯：檢查權限後，呼叫 `Report.create()` 寫入 SQLite。
  - 輸出：重導向至 `/driver/report` (並可帶有成功提示的 flash 訊息)。

- **POST `/driver/logout` (司機登出)**
  - 處理邏輯：清除 session 中的 driver 資訊。
  - 輸出：重導向至首頁或 `/driver/login`。

## 3. Jinja2 模板清單

所有的模板將存放在 `app/templates/` 中。

- `base.html`：共用版型（包含全站的導覽列、頁尾與基礎 CSS 資源，支援黑夜模式）
- `index.html`：首頁（繼承 `base.html`）
- `route_plan.html`：轉乘規劃頁面（繼承 `base.html`）
- `bus_status.html`：公車即時動態頁面（繼承 `base.html`）
- `driver_login.html`：司機專屬登入頁（繼承 `base.html`，但可能採用更簡潔的排版）
- `driver_report.html`：司機專屬回報介面（繼承 `base.html`，按鈕放大，適合快速點擊）
