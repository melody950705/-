from flask import render_template, jsonify
from . import bus_bp
from ..models.report import Report
from ..utils.tdx import get_live_route_status

@bus_bp.route('/bus/<route_id>', methods=['GET'])
def bus_status(route_id):
    """
    特定路線即時動態頁面
    渲染網頁架構，之後由 JavaScript AJAX 定期呼叫 /api/bus/<route_id> 更新
    """
    # 這裡先帶入基本資訊，避免畫面全白
    return render_template('bus_status.html', route_id=route_id)

@bus_bp.route('/api/bus/<route_id>', methods=['GET'])
def api_bus_status(route_id):
    """
    取得動態 API (供前端 AJAX 呼叫)
    1. 呼叫 TDX 模組取得即時公車與到站預估時間
    2. 呼叫 Report 取得司機近期回報狀態 (如延誤、滿載)
    3. 合併為 JSON 回傳
    """
    try:
        # 1. 取得即時動態
        bus_data = get_live_route_status(route_id)
        
        # 2. 取得此公車路線之司機回報
        reports = Report.get_by_route(route_id)
        
        # 3. 回傳整合數據
        return jsonify({
            "status": "success",
            "route_id": route_id,
            "direction": bus_data.get("direction", 0),
            "stops": bus_data.get("stops", []),
            "reports": reports
        })
    except Exception as e:
        print(f"Error in api_bus_status for route {route_id}: {e}")
        return jsonify({
            "status": "error",
            "message": "無法取得即時動態資料，請稍後再試。"
        }), 500
