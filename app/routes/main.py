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
        # 這裡未來可整合 TDX 轉乘規劃 API，目前回傳模擬規劃結果
        results = [
            {
                'summary': '搭乘 300 路公車（預估 25 分鐘）',
                'duration': '25 mins',
                'steps': [
                    f'從 {start} 步行至最近捷運站/公車站牌',
                    '搭乘 300 路公車（方向：台中車站 -> 靜宜大學）',
                    f'於目的地站牌下車，步行至 {end}'
                ]
            },
            {
                'summary': '搭乘 301 路公車（預估 30 分鐘，步行較少）',
                'duration': '30 mins',
                'steps': [
                    f'從 {start} 步行至公車站牌',
                    '搭乘 301 路公車',
                    f'到達目的地 {end}'
                ]
            }
        ]
        
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

@main_bp.route('/api/nearby-stops', methods=['GET'])
def get_nearby_stops():
    """
    [F-05] 附近站牌與公車搜尋 API
    根據使用者傳入的經緯度 (lat, lng)，計算距離並回傳最接近的公車站點。
    """
    try:
        lat_val = request.args.get('lat')
        lng_val = request.args.get('lng')
        
        # 預設位置（台中市政府附近）
        lat = float(lat_val) if lat_val else 24.1625
        lng = float(lng_val) if lng_val else 120.6472
    except ValueError:
        return jsonify({'status': 'error', 'message': '經緯度格式錯誤'}), 400

    mock_stations = [
        {"name": "科博館 (Botanical Garden)", "lat": 24.1558, "lng": 120.6653, "routes": ["300", "301", "303", "304"]},
        {"name": "廣三SOGO (Kuang San SOGO)", "lat": 24.1556, "lng": 120.6616, "routes": ["300", "302", "305", "310"]},
        {"name": "市政府 (Taichung City Hall)", "lat": 24.1625, "lng": 120.6472, "routes": ["300", "301", "305"]},
        {"name": "新光/遠百 (Shin Kong/Top City)", "lat": 24.1645, "lng": 120.6425, "routes": ["300", "302", "310"]},
        {"name": "秋紅谷 (Maple Garden)", "lat": 24.1668, "lng": 120.6384, "routes": ["300", "303", "304", "305"]},
        {"name": "台中車站 (Taichung Station)", "lat": 24.1373, "lng": 120.6868, "routes": ["300", "301", "302", "305", "310"]},
        {"name": "逢甲大學 (Tunghai Univ. / Fengjia)", "lat": 24.1798, "lng": 120.6462, "routes": ["5", "25", "35"]},
        {"name": "靜宜大學 (Providence Univ.)", "lat": 24.2268, "lng": 120.5791, "routes": ["300", "301", "305", "310"]}
    ]
    
    import math
    results = []
    for station in mock_stations:
        # 使用簡易經緯度歐氏距離換算 (北緯 24 度下，緯度 1 度約 111 公里，經度 1 度約 101 公里)
        d_lat = (station["lat"] - lat) * 111000
        d_lng = (station["lng"] - lng) * 101000
        distance = int(math.sqrt(d_lat**2 + d_lng**2))
        
        results.append({
            "name": station["name"],
            "distance": distance,
            "routes": station["routes"]
        })
        
    # 依距離由近到遠排序，取前 4 個
    results.sort(key=lambda x: x["distance"])
    
    return jsonify({
        "status": "success",
        "stops": results[:4]
    })

