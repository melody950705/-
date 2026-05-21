from flask import render_template, jsonify
from . import bus_bp
from ..models.report import Report
from app.utils.tdx import TDXClient

tdx = TDXClient()

@bus_bp.route('/bus/<route_id>', methods=['GET'])
def bus_status(route_id):
    """
    特定路線動態頁面
    顯示包含路線資訊與到站時間列表的介面 (由 AJAX 取得即時資料)
    """
    return render_template('bus_status.html', route_id=route_id)

@bus_bp.route('/api/bus/<route_id>', methods=['GET'])
def api_bus_status(route_id):
    """
    取得動態 API (供前端 AJAX 呼叫)
    1. 呼叫 TDX API 取得公車即時資訊
    2. 呼叫 Report.get_by_route() 取得司機回報狀態
    3. 合併並回傳 JSON
    """
    try:
        # 1. 取得即時 ETA 資料
        eta_list = tdx.get_bus_eta(route_id)
        
        # 2. 取得近期司機回報 (例如過去 1 小時內)
        driver_reports = Report.get_by_route(route_id)
        
        return jsonify({
            "status": "success",
            "route_id": route_id,
            "eta": eta_list,
            "reports": driver_reports
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
