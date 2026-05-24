from flask import render_template, request, redirect, url_for, session, flash
from . import driver_bp
from ..models.driver import Driver
from ..models.report import Report
from werkzeug.security import check_password_hash

@driver_bp.route('/driver/login', methods=['GET'])
def login_page():
    """
    司機登入頁面
    若已登入，直接重導至回報頁面
    """
    if 'driver_id' in session:
        return redirect(url_for('driver.report_page'))
    return render_template('driver_login.html')

@driver_bp.route('/driver/login', methods=['POST'])
def login_submit():
    """
    司機登入驗證
    驗證帳號密碼，成功則建立 session 並重導向
    失敗則顯示錯誤訊息
    """
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash("請輸入帳號與密碼。")
        return redirect(url_for('driver.login_page'))

    driver = Driver.get_by_username(username)
    if driver and check_password_hash(driver['password_hash'], password):
        session['driver_id'] = driver['id']
        session['driver_name'] = driver['name']
        session['driver_username'] = driver['username']
        flash(f"登入成功，歡迎回來，{driver['name']} 司機！")
        return redirect(url_for('driver.report_page'))
    else:
        flash("帳號或密碼錯誤。")
        return redirect(url_for('driver.login_page'))

@driver_bp.route('/driver/report', methods=['GET'])
def report_page():
    """
    司機回報頁面
    檢查 session 權限，未登入則導向登入頁面
    """
    if 'driver_id' not in session:
        flash("請先登入系統。")
        return redirect(url_for('driver.login_page'))
    
    # 取得目前此司機送出的歷史回報
    driver_id = session['driver_id']
    all_reports = Report.get_all()
    driver_reports = [r for r in all_reports if r['driver_id'] == driver_id]
    
    # 定義可供回報的公車路線
    available_routes = ["300", "310", "326"]
    
    return render_template('driver_report.html', reports=driver_reports, routes=available_routes)

@driver_bp.route('/driver/report', methods=['POST'])
def report_submit():
    """
    司機送出回報
    接收路況、故障或滿載狀態，寫入資料庫
    """
    if 'driver_id' not in session:
        flash("請先登入系統。")
        return redirect(url_for('driver.login_page'))

    driver_id = session['driver_id']
    route_id = request.form.get('route_id', '').strip()
    status = request.form.get('status', '').strip()
    latitude = request.form.get('latitude', '').strip()
    longitude = request.form.get('longitude', '').strip()

    if not route_id or not status:
        flash("公車路線與回報狀態為必填欄位。")
        return redirect(url_for('driver.report_page'))

    # 處理經緯度轉換
    lat_val = float(latitude) if latitude else None
    lon_val = float(longitude) if longitude else None

    report_data = {
        "driver_id": driver_id,
        "route_id": route_id,
        "status": status,
        "latitude": lat_val,
        "longitude": lon_val
    }

    report_id = Report.create(report_data)
    if report_id:
        flash(f"路線 {route_id} 狀態回報成功！")
    else:
        flash("系統錯誤，回報失敗，請重試。")
        
    return redirect(url_for('driver.report_page'))

@driver_bp.route('/driver/logout', methods=['POST'])
def logout():
    """
    司機登出
    清除 session 並重導向至登入頁面
    """
    session.clear()
    flash("已成功登出。")
    return redirect(url_for('driver.login_page'))
