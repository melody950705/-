import os
import time
import requests
from config import Config

# Simple token cache
_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_tdx_token():
    """
    獲取 TDX API 的 Access Token，支援快取。
    """
    global _token_cache
    client_id = Config.TDX_CLIENT_ID
    client_secret = Config.TDX_CLIENT_SECRET

    if not client_id or not client_secret:
        return None

    # Check if cached token is still valid (with 60-second buffer)
    current_time = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > current_time + 60:
        return _token_cache["access_token"]

    url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    headers = {
        "content-type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            _token_cache["access_token"] = res_data.get("access_token")
            expires_in = res_data.get("expires_in", 3600)
            _token_cache["expires_at"] = current_time + expires_in
            return _token_cache["access_token"]
        else:
            print(f"Failed to get TDX token: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Error requesting TDX token: {e}")
        return None

def get_live_route_status(route_id):
    """
    取得特定路線的即時到站狀態與站牌清單。
    如果未配置 TDX 金鑰或呼叫失敗，將自動回傳高品質動態模擬數據。
    
    Args:
        route_id (str): 路線名稱 (例如 '300', '310')
        
    Returns:
        dict: 包含 'route_id', 'direction' 與 'stops' 清單的字典
    """
    token = get_tdx_token()
    if not token:
        return get_mock_route_data(route_id)

    # 1. 取得路線站牌順序 (StopOfRoute)
    # 2. 取得預估到站時間 (EstimatedOfArrival)
    # 3. 合併回傳
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    city = "Taichung"
    
    try:
        # Get stop sequences
        stop_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/StopOfRoute/City/{city}/{route_id}?$format=JSON"
        stop_res = requests.get(stop_url, headers=headers, timeout=5)
        
        # Get estimated arrival times
        estimate_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedOfArrival/City/{city}/{route_id}?$format=JSON"
        estimate_res = requests.get(estimate_url, headers=headers, timeout=5)
        
        if stop_res.status_code == 200 and estimate_res.status_code == 200:
            stops_data = stop_res.json()
            estimate_data = estimate_res.json()
            
            if not stops_data:
                return get_mock_route_data(route_id)
                
            # Filter for outbound direction (Direction=0) as default
            target_route = None
            for r in stops_data:
                if r.get("Direction") == 0:
                    target_route = r
                    break
            if not target_route:
                target_route = stops_data[0]
                
            direction = target_route.get("Direction", 0)
            stops_list = target_route.get("Stops", [])
            
            # Map estimates by StopUID
            estimates_map = {}
            for est in estimate_data:
                if est.get("Direction") == direction:
                    estimates_map[est.get("StopUID")] = est
            
            formatted_stops = []
            for stop in stops_list:
                stop_uid = stop.get("StopUID")
                stop_name = stop.get("StopName", {}).get("Zh_tw", "")
                est_info = estimates_map.get(stop_uid, {})
                
                estimate_time = est_info.get("EstimateTime") # in seconds
                stop_status = est_info.get("StopStatus", 0) # 0: Normal
                plate_nbr = est_info.get("PlateNbr", "")
                
                # Format estimated time to display format
                display_time = "未發車"
                if stop_status == 1:
                    display_time = "尚未起飛/未營運"
                elif stop_status == 2:
                    display_time = "交管不停靠"
                elif stop_status == 3:
                    display_time = "末班車已過"
                elif stop_status == 4:
                    display_time = "今日未營運"
                elif estimate_time is not None:
                    mins = estimate_time // 60
                    if mins == 0:
                        display_time = "即將到站"
                    elif mins == 1:
                        display_time = "將到站 (1分)"
                    else:
                        display_time = f"{mins} 分"
                        
                formatted_stops.append({
                    "stop_uid": stop_uid,
                    "stop_name": stop_name,
                    "sequence": stop.get("StopSequence", 0),
                    "estimate_time": estimate_time,
                    "display_time": display_time,
                    "plate_nbr": plate_nbr
                })
                
            return {
                "route_id": route_id,
                "direction": direction,
                "stops": formatted_stops
            }
        else:
            return get_mock_route_data(route_id)
    except Exception as e:
        print(f"Error fetching TDX data: {e}")
        return get_mock_route_data(route_id)

def get_mock_route_data(route_id):
    """
    針對常用路線 (300, 310, 326) 回傳高品質的模擬即時數據。
    使用時間戳記動態計算到站時間，模擬公車移動效果。
    """
    # 預設路線站牌
    stops_db = {
        "300": [
            "臺中車站", "第二市場(三民路)", "中華路口", "原子街口", "茄苳腳",
            "臺灣大道民權路口", "科博館", "忠明國小", "頂何厝", "市政府",
            "新光/遠百", "秋紅谷", "榮總/東海大學", "東海別墅", "坪頂", "靜宜大學"
        ],
        "310": [
            "臺中車站", "第二市場(三民路)", "科博館", "市政府", "秋紅谷", 
            "榮總/東海大學", "靜宜大學", "弘光科技大學", "沙鹿高工", "梧棲國小", 
            "頂魚寮公園", "台中港旅客服務中心"
        ],
        "326": [
            "新民高中", "臺中車站", "中華路口", "科博館", "市政府", "秋紅谷",
            "榮總/東海大學", "東海別墅", "坪頂", "靜宜大學", "沙鹿車站"
        ]
    }
    
    # 預設若不是這三條，就以 300 作為基底
    stops_names = stops_db.get(route_id, stops_db["300"])
    
    # 利用當前時間做動態模擬
    current_sec = int(time.time())
    
    formatted_stops = []
    num_stops = len(stops_names)
    
    for i, name in enumerate(stops_names):
        # 模擬公車在站點間移動
        # 假設每 3 站有一班公車，每班公車行駛速度不同
        # 我們用數學公式根據時間計算到站剩餘秒數
        stop_offset = i * 180 # 假設每站差 3 分鐘 (180秒)
        cycle = 1200 # 每 20 分鐘一班車循環
        
        # 剩餘秒數 = (站點偏移 - 當前秒數) % 循環
        rem_sec = (stop_offset - current_sec) % cycle
        
        # 判斷是否即將到站或已過站
        plate_nbr = f"EAA-{300 + (current_sec // cycle) % 50:03d}"
        
        if rem_sec < 45:
            display_time = "即將到站"
            estimate_time = 0
        elif rem_sec < 90:
            display_time = "將到站 (1分)"
            estimate_time = 60
        else:
            mins = rem_sec // 60
            display_time = f"{mins} 分"
            estimate_time = rem_sec
            plate_nbr = "" # 還太遠不顯示車牌
            
        formatted_stops.append({
            "stop_uid": f"TXG_{route_id}_{i+1:03d}",
            "stop_name": name,
            "sequence": i + 1,
            "estimate_time": estimate_time,
            "display_time": display_time,
            "plate_nbr": plate_nbr
        })
        
    return {
        "route_id": route_id,
        "direction": 0,
        "stops": formatted_stops
    }
