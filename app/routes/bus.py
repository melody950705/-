from flask import Blueprint, render_template, jsonify, current_app
import requests
import random
from ..models.report import Report

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

def get_mock_bus_data(route_id):
    """
    產生模擬的公車路線與站牌動態資料，以利在無 TDX 金鑰時正常展示系統功能。
    """
    # 根據常見台中公車路線給予不同的站牌
    if route_id == '300':
        stops = ["台中車站", "第二市場", "仁愛醫院", "中華路口", "原子街口", "茄苳腳", "中教大", "科博館", "廣三SOGO", "市政府", "新光/遠百", "秋紅谷", "東海大學", "靜宜大學"]
    elif route_id == '301':
        stops = ["新民高中", "台中科技大學", "台中車站", "第三市場", "忠孝夜市", "國立公共資訊圖書館", "中興大學"]
    else:
        stops = [f"模擬站牌 {i}" for i in range(1, 11)]
        
    mock_data = []
    for i, stop in enumerate(stops):
        # 模擬預估到站秒數。i=0 代表已過站或起點，其餘時間遞增
        estimate_time = random.randint(30, 1800) if i > 0 else None
        
        # 狀態：0: 正常, 1: 尚未起飛, 2: 交管, 3: 故障, 4: 停駛
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
    tdx_data = fetch_tdx_bus_data(route_id, token)
    
    if tdx_data:
        # 解析並格式化 TDX 資料
        bus_stops = []
        for item in tdx_data:
            bus_stops.append({
                'StopName': item.get('StopName', {}),
                'EstimateTime': item.get('EstimateTime'),
                'StopStatus': item.get('StopStatus', 0),
                'StopSequence': item.get('StopSequence', 0),
                'Direction': item.get('Direction', 0)
            })
        # 依站牌順序排序
        bus_stops.sort(key=lambda x: x['StopSequence'])
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
