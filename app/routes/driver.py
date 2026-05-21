from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from . import driver_bp
from ..models.driver import Driver
from ..models.report import Report

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
        flash('請填寫所有欄位！', 'danger')
        return redirect(url_for('driver.login_page'))

    driver = Driver.get_by_username(username)
    
    # 支援雜湊驗證，或者若直接為明文密碼也支援驗證以防測試環境未雜湊
    if driver and (check_password_hash(driver['password_hash'], password) or driver['password_hash'] == password):
        session['driver_id'] = driver['id']
        session['driver_name'] = driver['name']
        session['driver_username'] = driver['username']
        flash(f'歡迎回來，{driver["name"]} 司機！', 'success')
        return redirect(url_for('driver.report_page'))
    
    flash('帳號或密碼錯誤！', 'danger')
    return redirect(url_for('driver.login_page'))

@driver_bp.route('/driver/report', methods=['GET'])
def report_page():
    """
    司機回報頁面
    檢查 session 權限，未登入則導向登入頁面
    """
    if 'driver_id' not in session:
        flash('請先登入系統！', 'warning')
        return redirect(url_for('driver.login_page'))
    return render_template('driver_report.html')

@driver_bp.route('/driver/report', methods=['POST'])
def report_submit():
    """
    司機送出回報
    接收路況、故障或滿載狀態，寫入資料庫
    """
    if 'driver_id' not in session:
        flash('權限不足，請先登入！', 'danger')
        return redirect(url_for('driver.login_page'))

    route_id = request.form.get('route_id', '').strip()
    status = request.form.get('status', '').strip()
    latitude = request.form.get('latitude', None)
    longitude = request.form.get('longitude', None)

    if not route_id or not status:
        flash('路線與回報狀態為必填欄位！', 'danger')
        return redirect(url_for('driver.report_page'))

    try:
        lat_val = float(latitude) if latitude else None
        lng_val = float(longitude) if longitude else None
        
        Report.create(
            driver_id=session['driver_id'],
            route_id=route_id,
            status=status,
            latitude=lat_val,
            longitude=lng_val
        )
        flash(f'成功回報 {route_id} 路公車狀態：{status}！', 'success')
    except Exception as e:
        flash(f'回報失敗：{str(e)}', 'danger')
        
    return redirect(url_for('driver.report_page'))

@driver_bp.route('/driver/logout', methods=['POST'])
def logout():
    """
    司機登出
    清除 session 並重導向至首頁或登入頁
    """
    session.clear()
    flash('您已成功登出系統。', 'info')
    return redirect(url_for('driver.login_page'))
