from flask import render_template, request
from . import main_bp
from app.utils.tdx import TDXClient

tdx = TDXClient()

@main_bp.route('/', methods=['GET'])
def index():
    """
    首頁
    顯示搜尋特定路線與附近站牌功能的介面
    """
    # 預設提供熱門推薦路線
    popular_routes = ["300", "305", "310", "25", "35", "5"]
    return render_template('index.html', popular_routes=popular_routes)

@main_bp.route('/route-plan', methods=['GET'])
def route_plan():
    """
    路線與轉乘規劃 [F-02]
    如果有 start 與 end 參數，則呼叫 TDX API 計算並顯示結果
    否則顯示規劃表單
    """
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    
    results = None
    if start and end:
        results = tdx.get_route_plan(start, end)
        
    return render_template('route_plan.html', start=start, end=end, results=results)
