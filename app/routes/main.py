from flask import render_template, request
from . import main_bp
from ..models.report import Report

@main_bp.route('/', methods=['GET'])
def index():
    """
    首頁
    顯示搜尋特定路線與附近站牌功能的介面，並列出熱門路線與最新司機回報
    """
    # 取得最新的 5 筆司機路況回報
    recent_reports = Report.get_all()[:5]
    popular_routes = [
        {"id": "300", "name": "300路 (臺中車站 - 靜宜大學)", "desc": "臺灣大道幹線公車，班次密集"},
        {"id": "310", "name": "310路 (臺中車站 - 台中港)", "desc": "行經秋紅谷、東海大學、沙鹿至台中港"},
        {"id": "326", "name": "326路 (新民高中 - 靜宜大學)", "desc": "臺灣大道深夜公車 (22:00 - 05:00)"}
    ]
    return render_template('index.html', recent_reports=recent_reports, popular_routes=popular_routes)

@main_bp.route('/route-plan', methods=['GET'])
def route_plan():
    """
    路線與轉乘規劃
    如果有 start 與 end 參數，則進行計算並顯示結果；否則顯示規劃表單
    """
    start = request.args.get('start', '').strip()
    end = request.args.get('end', '').strip()
    
    plans = []
    if start and end:
        # 進行模擬路線規劃，以提供開箱即用的良好體驗
        # 也可以未來串接外部轉乘規劃 API
        plans = [
            {
                "method": "直達幹線公車",
                "route": "300 路公車",
                "duration": "約 25 分鐘",
                "steps": [
                    f"於 【{start}】 站牌上車，搭乘 300 路公車（往靜宜大學方向）",
                    "行經 7 個站點，中途經過 市政府、秋紅谷",
                    f"於 【{end}】 下車，抵達目的地"
                ],
                "fare": "15 元 (持悠遊卡/一卡通前 10 公里免費/市民優惠)"
            },
            {
                "method": "捷運 + 公車轉乘",
                "route": "捷運綠線 + 310 路公車",
                "duration": "約 35 分鐘",
                "steps": [
                    f"自 【{start}】 步行至最近捷運站搭乘捷運綠線",
                    "至 捷運市政府站 下車並由 2 號出口出站",
                    "至 臺灣大道公車專用道【市政府】站 轉乘 310 路公車",
                    f"搭乘至 【{end}】 下車"
                ],
                "fare": "35 元"
            }
        ]
        
    return render_template('route_plan.html', start=start, end=end, plans=plans)
