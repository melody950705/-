from flask import Blueprint, render_template, jsonify, current_app
import requests
import random
from ..models.report import Report
from app.utils.tdx import TDXClient

tdx = TDXClient()

bus_bp = Blueprint('bus', __name__)

def get_tdx_token():
    """
    取得 TDX API 的 Access Token
    """
    client_id = current_app.config.get('TDX_CLIENT_ID')
    client_secret = current_app.config.get('TDX_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None
    try:
        url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        res = requests.post(url, headers=headers, data=data, timeout=5)
        if res.status_code == 200:
            return res.json().get('access_token')
    except Exception as e:
        print(f"Error getting TDX token: {e}")
    return None

def fetch_tdx_bus_data(route_id, token):
    """
    從 TDX API 取得即時公車動態資料
    """
    if not token:
        return None
    try:
        # 取得台中市指定路線的預估到站時間
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedOfArrival/City/Taichung/{route_id}?$format=JSON"
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error fetching TDX bus data: {e}")
    return None

def fetch_tdx_stops_of_route(route_id, token):
    """
    從 TDX API 取得指定路線的所有停靠站序 (StopOfRoute)
    """
    if not token:
        return None
    try:
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/StopOfRoute/City/Taichung/{route_id}?$format=JSON"
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error fetching TDX stop of route: {e}")
    return None


def get_mock_bus_data(route_id):
    """
    產生模擬的公車路線與站牌動態資料，以利在無 TDX 金鑰時正常展示系統功能。
    """
    # 尋找是否在本地 routes.json 中
    all_routes = tdx.get_mock_all_routes()
    route_info = next((r for r in all_routes if str(r["id"]) == str(route_id)), None)

    # 根據常見台中公車路線給予不同的站牌
    if route_id == '300':
        stops = ["台中車站", "第二市場", "仁愛醫院", "中華路口", "原子街口", "茄苳腳", "中教大", "科博館", "廣三SOGO", "市政府", "新光/遠百", "秋紅谷", "東海大學", "靜宜大學"]
    elif route_id == '301':
        stops = ["新民高中", "台中科技大學", "台中車站", "第三市場", "忠孝夜市", "國立公共資訊圖書館", "中興大學"]
    elif route_id == '黃25':
        stops = ["捷運九德站(興華街)", "九德國小(興祥街)", "明道中學", "光德國中(信義街)", "永興宮", "福泰社區", "東園里", "東園國小", "東園社區活動中心", "南興宮", "溪心壩", "溪南國中", "北螺潭", "石螺潭", "南螺潭", "集會所(太明路)", "喀哩", "溪南派出所", "溪尾里活動中心", "芬園花卉生產休憩園區", "後溪仔(CFT照顧學校)", "溪尾國小"]
    elif route_id == '525':
        stops = ["臺中刑務所演武場（國漫館）", "地方法院", "臺中女中", "民權繼光街口", "臺中車站（臺灣大道）", "第一廣場", "第二市場（臺灣大道）", "中央市場", "中國醫藥大學", "曉明女中（中清路）", "捷運文心中清站（文心路）", "臺中流行影音中心", "經貿黎明路口", "大雅交流道", "大華國中", "大雅", "上楓國小（楓樹腳）", "三采幼稚園", "頂牛埔", "社口活動中心"]
    elif route_id == '153':
        stops = ["高鐵台中站", "朝馬(臺灣大道)", "秋紅谷", "石岡水壩", "東勢轉運站", "和平區公所", "白冷", "谷關"]
    elif route_info and route_info.get("departure") and route_info.get("destination"):
        dep = route_info["departure"]
        dest = route_info["destination"]
        # 為了讓特定路線的站牌順序固定，使用 hash(route_id) 作為隨機種子
        random.seed(hash(route_id))
        middle_pool = [
            "台中車站", "第二市場", "中華路口", "原子街口", "茄苳腳", "中正國小", "科博館", "忠明國小", "頂何厝", 
            "市政府", "新光/遠百", "秋紅谷", "福安", "榮總/東海大學", "東海別墅", "坪頂", "正英路", "弘光科技大學", 
            "靜宜大學", "中友百貨", "一中商圈", "臺中公園", "中國醫藥大學", "水湳市場", "逢甲大學", "文華高中", 
            "捷運市政府站", "秀泰影城", "大墩路口", "公益路口", "五權南路口", "國家歌劇院", "朝馬轉運站", "大慶火車站", 
            "太原火車站", "豐原轉運中心", "大甲火車站", "沙鹿火車站", "清水火車站", "烏日高鐵站"
        ]
        selected_middle = random.sample(middle_pool, min(12, len(middle_pool)))
        stops = [dep] + selected_middle + [dest]
    else:
        stops = [f"模擬站牌 {i}" for i in range(1, 11)]
        
    random.seed(None)

        
    mock_data = []
    # 去程 (Direction 0)
    for i, stop in enumerate(stops):
        estimate_time = random.randint(30, 1800) if i > 0 else None
        stop_status = 0
        if estimate_time is None:
            stop_status = 1  # 尚未起飛
            
        mock_data.append({
            'StopName': {'Zh_tw': stop},
            'EstimateTime': estimate_time,
            'StopStatus': stop_status,
            'StopSequence': i + 1,
            'Direction': 0
        })
        
    # 返程 (Direction 1)
    reversed_stops = list(reversed(stops))
    for i, stop in enumerate(reversed_stops):
        estimate_time = random.randint(30, 1800) if i > 0 else None
        stop_status = 0
        if estimate_time is None:
            stop_status = 1  # 尚未起飛
            
        mock_data.append({
            'StopName': {'Zh_tw': stop},
            'EstimateTime': estimate_time,
            'StopStatus': stop_status,
            'StopSequence': i + 1,
            'Direction': 1
        })
    return mock_data

@bus_bp.route('/<route_id>', methods=['GET'])
def bus_status(route_id):
    """
    特定公車路線動態頁面
    """
    return render_template('bus_status.html', route_id=route_id)

@bus_bp.route('/api/status/<route_id>', methods=['GET'])
def api_bus_status(route_id):
    """
    取得即時動態 API
    結合 TDX API 預估到站時間與 SQLite 中司機的回報資料。
    """
    # 1. 取得 TDX 資料 (若無金鑰則使用模擬資料)
    token = get_tdx_token()
    stops_data = fetch_tdx_stops_of_route(route_id, token)
    eta_data = fetch_tdx_bus_data(route_id, token)
    
    if stops_data:
        # 建立 ETA 查表對照 Dict
        eta_dict = {}
        if eta_data:
            for item in eta_data:
                stop_uid = item.get('StopUID')
                direction = item.get('Direction', 0)
                if stop_uid is not None:
                    eta_dict[(stop_uid, direction)] = {
                        'EstimateTime': item.get('EstimateTime'),
                        'StopStatus': item.get('StopStatus', 0)
                    }
        
        bus_stops = []
        for route_dir in stops_data:
            direction = route_dir.get('Direction', 0)
            stops_list = route_dir.get('Stops', [])
            for stop in stops_list:
                stop_uid = stop.get('StopUID')
                stop_name = stop.get('StopName', {})
                seq = stop.get('StopSequence', 0)
                
                # 從 ETA 資料中比對
                eta_info = eta_dict.get((stop_uid, direction), {})
                est_time = eta_info.get('EstimateTime')
                stop_status = eta_info.get('StopStatus', 0)
                
                # 如果沒有找到對應的即時 ETA，預設狀態為「1: 尚未開車/未發車」
                if est_time is None and stop_status == 0:
                    stop_status = 1
                
                bus_stops.append({
                    'StopName': stop_name,
                    'EstimateTime': est_time,
                    'StopStatus': stop_status,
                    'StopSequence': seq,
                    'Direction': direction
                })
        # 依去返程與站序排序
        bus_stops.sort(key=lambda x: (x['Direction'], x['StopSequence']))
    else:
        # 如果無法取得 StopOfRoute，但能取得 EstimatedOfArrival，以此作為備份
        if eta_data:
            bus_stops = []
            for item in eta_data:
                bus_stops.append({
                    'StopName': item.get('StopName', {}),
                    'EstimateTime': item.get('EstimateTime'),
                    'StopStatus': item.get('StopStatus', 0),
                    'StopSequence': item.get('StopSequence', 0),
                    'Direction': item.get('Direction', 0)
                })
            bus_stops.sort(key=lambda x: (x['Direction'], x['StopSequence']))
        else:
            # 採用模擬資料
            bus_stops = get_mock_bus_data(route_id)
        
    # 2. 獲取司機近期回報狀態
    try:
        reports = Report.get_by_route(route_id)
    except Exception as e:
        print(f"Error reading reports in route: {e}")
        reports = []
        
    # 合併回傳
    return jsonify({
        'route_id': route_id,
        'stops': bus_stops,
        'reports': reports
    })

@bus_bp.route('/api/routes', methods=['GET'])
def get_routes():
    """
    取得所有公車路線清單
    """
    routes = tdx.get_all_routes()
    return jsonify(routes)

