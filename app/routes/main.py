from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首頁
    顯示搜尋特定路線與附近站牌功能的介面，同時將 session 中已收藏的站牌清單傳至前端。
    """
    favorites = session.get('favorites', [])
    return render_template('index.html', favorites=favorites)

@main_bp.route('/route-plan')
def route_plan():
    """
    路線與轉乘規劃
    如果有 start 與 end 參數，則進行規劃並顯示結果；否則顯示空白規劃表單。
    """
    start = request.args.get('start')
    end = request.args.get('end')
    results = None
    
    if start and end:
        from app.utils.tdx import TDXClient
        tdx = TDXClient()
        raw_plans = tdx.get_route_plan(start, end)
        
        results = []
        for plan in raw_plans:
            steps = []
            for leg in plan.get('legs', []):
                leg_type = leg.get('type')
                leg_name = leg.get('name', '')
                leg_from = leg.get('from', '')
                leg_to = leg.get('to', '')
                leg_dur = leg.get('duration', 0)
                leg_note = leg.get('note', '')
                
                note_str = f"（{leg_note}）" if leg_note else ""
                
                if leg_type == 'walk':
                    steps.append(f"從 {leg_from} 步行至 {leg_to}，預估 {leg_dur} 分鐘{note_str}")
                else:
                    steps.append(f"搭乘 {leg_name}（從 {leg_from} 到 {leg_to}），預估 {leg_dur} 分鐘{note_str}")
            
            results.append({
                'summary': plan.get('title'),
                'duration': f"{plan.get('total_time')} 分鐘",
                'steps': steps
            })
        
    return render_template('route_plan.html', start=start, end=end, results=results)

@main_bp.route('/favorites/add', methods=['POST'])
def add_favorite():
    """
    將特定公車路線/站牌加入收藏清單（存於 session 中）。
    支援一般 Form 表單與 AJAX JSON 請求。
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    route_id = data.get('route_id')
    stop_name = data.get('stop_name')
    direction = data.get('direction', '0')
    
    if not route_id or not stop_name:
        error_msg = '路線代號與站牌名稱為必填欄位！'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(request.referrer or url_for('main.index'))
        
    favorites = session.get('favorites', [])
    
    # 檢查是否已收藏
    exists = any(f['route_id'] == route_id and f['stop_name'] == stop_name and f.get('direction') == direction for f in favorites)
    
    if not exists:
        favorites.append({
            'route_id': route_id,
            'stop_name': stop_name,
            'direction': direction
        })
        session['favorites'] = favorites
        session.modified = True
        success_msg = f'已成功收藏：{route_id}路公車 - {stop_name}！'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg, 'favorites': favorites})
        flash(success_msg, 'success')
    else:
        info_msg = '此站牌已在您的收藏名單中。'
        if request.is_json:
            return jsonify({'success': True, 'message': info_msg, 'favorites': favorites})
        flash(info_msg, 'info')
        
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/favorites/delete', methods=['POST'])
def delete_favorite():
    """
    將特定公車路線/站牌從收藏清單中移除。
    支援一般 Form 表單與 AJAX JSON 請求。
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    route_id = data.get('route_id')
    stop_name = data.get('stop_name')
    direction = data.get('direction', '0')
    
    favorites = session.get('favorites', [])
    initial_len = len(favorites)
    
    # 過濾掉要刪除的項目
    favorites = [f for f in favorites if not (f['route_id'] == route_id and f['stop_name'] == stop_name and f.get('direction') == direction)]
    
    if len(favorites) < initial_len:
        session['favorites'] = favorites
        session.modified = True
        success_msg = '已成功移除該收藏站牌。'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg, 'favorites': favorites})
        flash(success_msg, 'success')
    else:
        error_msg = '找不到該收藏項目。'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 404
        flash(error_msg, 'warning')
        
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/api/stops/nearby', methods=['GET'])
def get_nearby_stops():
    """
    附近站牌 API
    計算當前 GPS 位置 1 公里內最近的 5 個公車站牌
    """
    import math
    import os
    import json
    
    lat_str = request.args.get('lat')
    lng_str = request.args.get('lng')
    
    if not lat_str or not lng_str:
        return jsonify({'status': 'error', 'message': '請提供經緯度參數！'}), 400
        
    try:
        user_lat = float(lat_str)
        user_lng = float(lng_str)
    except ValueError:
        return jsonify({'status': 'error', 'message': '經緯度格式不正確！'}), 400

    def haversine(lat1, lon1, lat2, lon2):
        # Haversine formula to calculate distance in meters
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2.0)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    # 載入本地的 stops.json 檔案
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stops_file = os.path.join(base_dir, 'static', 'data', 'stops.json')
    
    if not os.path.exists(stops_file):
        return jsonify({'status': 'error', 'message': '伺服器缺少站牌快取檔案！'}), 500
        
    try:
        with open(stops_file, 'r', encoding='utf-8') as f:
            all_stops_data = json.load(f)
    except Exception as e:
        print(f"Error reading stops.json: {e}")
        return jsonify({'status': 'error', 'message': '無法載入站牌資料！'}), 500
        
    # 提取所有不重複的站牌與行經路線
    unique_stops = {}
    for route_data in all_stops_data:
        route_id = route_data.get('RouteID', '')
        route_name = route_data.get('RouteName', {}).get('Zh_tw', route_id)
        if not route_name.endswith('路') and not '路' in route_name:
            route_name = f"{route_name}路"
            
        for stop in route_data.get('Stops', []):
            stop_name = stop.get('StopName', {}).get('Zh_tw', '')
            
            # 修復 stops.json 中的亂碼站牌名稱（如果是 300 號線的亂碼，我們用正確名稱匹配，或者正常過濾）
            # 因為 300 號線中文名稱在 stops.json 中已毀，我們用 StopUID 來還原
            uid = stop.get('StopUID', '')
            if uid:
                uid_map = {
                    'TXG13567': '靜宜大學', 'TXG13568': '弘光科技大學', 'TXG13569': '正英路',
                    'TXG13570': '坪頂', 'TXG13571': '東海別墅', 'TXG13572': '榮總/東海大學',
                    'TXG13573': '福安', 'TXG13574': '秋紅谷', 'TXG13575': '新光/遠百',
                    'TXG13576': '市政府', 'TXG13577': '頂何厝', 'TXG13578': '忠明國小',
                    'TXG13579': '科博館', 'TXG13580': '中正國小', 'TXG13581': '茄苳腳',
                    'TXG13582': '原子街口', 'TXG13583': '中華路口', 'TXG13584': '第二市場',
                    'TXG13585': '台中車站'
                }
                if uid in uid_map:
                    stop_name = uid_map[uid]
            
            # 如果還是亂碼字元，或是長度包含無效替換字元，用英文名清理作為後備
            if '' in stop_name:
                en_name = stop.get('StopName', {}).get('En', '')
                if en_name:
                    stop_name = en_name.split('(')[0].strip()
            
            pos = stop.get('StopPosition', {})
            stop_lat = pos.get('PositionLat')
            stop_lng = pos.get('PositionLon')
            
            if not stop_name or stop_lat is None or stop_lng is None:
                continue
                
            # 站名和經緯度作為 Key，以防有些站名相同但位置不同
            key = (stop_name, round(stop_lat, 4), round(stop_lng, 4))
            
            if key not in unique_stops:
                unique_stops[key] = {
                    'name': stop_name,
                    'lat': stop_lat,
                    'lng': stop_lng,
                    'routes': set()
                }
            unique_stops[key]['routes'].add(route_name)

    # 計算距離並篩選
    nearby_list = []
    is_mocked_location = False
    
    # 計算所有站牌的距離
    for key, s in unique_stops.items():
        dist = haversine(user_lat, user_lng, s['lat'], s['lng'])
        s['distance'] = dist
        nearby_list.append(s)
        
    # 篩選 1000m 內
    filtered_list = [s for s in nearby_list if s['distance'] <= 1000]

    if not filtered_list:
        return jsonify({
            'status': 'success',
            'out_of_service': True,
            'lat': user_lat,
            'lng': user_lng,
            'stops': []
        })


    # 按距離排序並取前 5 筆
    filtered_list.sort(key=lambda x: x['distance'])
    results = filtered_list[:5]
    
    return jsonify({
        'status': 'success',
        'out_of_service': False,
        'stops': [
            {
                'stop_name': s['name'],
                'lat': s['lat'],
                'lng': s['lng'],
                'distance': int(s['distance']),
                'routes': sorted(list(s['routes']))
            } for s in results
        ]
    })


