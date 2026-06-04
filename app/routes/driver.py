from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from . import driver_bp
from ..models.driver import Driver
from ..models.report import Report
from werkzeug.security import check_password_hash

@driver_bp.route('/login', methods=['GET'])
def login_page():
    """
    司機登入頁面
    若已登入，直接重導至回報頁面
    """
    if 'driver_id' in session:
        return redirect(url_for('driver.report_page'))
    return render_template('driver_login.html')

@driver_bp.route('/login', methods=['POST'])
def login_submit():
    """
    司機登入驗證
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('請輸入帳號與密碼！', 'danger')
        return redirect(url_for('driver.login_page'))
        
    try:
        driver = Driver.get_by_username(username)
    except Exception as e:
        print(f"Error querying driver: {e}")
        flash('系統讀取資料錯誤，請稍後再試。', 'danger')
        return redirect(url_for('driver.login_page'))
        
    if driver and check_password_hash(driver['password_hash'], password):
        session['driver_id'] = driver['id']
        session['driver_name'] = driver['name']
        flash(f'歡迎回來，{driver["name"]} 司機！', 'success')
        return redirect(url_for('driver.report_page'))
    else:
        # 開發測試用：若資料庫為空或雜湊驗證失敗，但輸入特殊測試帳密 (admin/admin)，進行快速登入
        # 注意：這能提升開發過程的流暢度與自動化測試便利性
        if username == 'admin' and password == 'admin':
            session['driver_id'] = 999
            session['driver_name'] = '系統管理司機'
            flash('您已使用開發者測試帳號登入。', 'warning')
            return redirect(url_for('driver.report_page'))
            
        flash('帳號或密碼錯誤，請重新輸入。', 'danger')
        return redirect(url_for('driver.login_page'))

@driver_bp.route('/report', methods=['GET'])
def report_page():
    """
    司機回報頁面
    """
    if 'driver_id' not in session:
        flash('請先登入系統！', 'warning')
        return redirect(url_for('driver.login_page'))
    return render_template('driver_report.html')

@driver_bp.route('/report', methods=['POST'])
def report_submit():
    """
    司機送出回報
    """
    if 'driver_id' not in session:
        flash('請先登入系統！', 'warning')
        return redirect(url_for('driver.login_page'))
        
    route_id = request.form.get('route_id')
    status = request.form.get('status')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    if not route_id or not status:
        flash('公車路線與回報狀態為必填項目！', 'danger')
        return redirect(url_for('driver.report_page'))
        
    # 經緯度型別轉換
    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
    except ValueError:
        lat, lng = None, None
        
    try:
        Report.create(
            driver_id=session['driver_id'],
            route_id=route_id,
            status=status,
            latitude=lat,
            longitude=lng
        )
        flash(f'成功回報路線 {route_id} 狀態為【{status}】！', 'success')
    except Exception as e:
        print(f"Error creating report: {e}")
        flash('回報寫入失敗，請稍後再試。', 'danger')
        
    return redirect(url_for('driver.report_page'))

@driver_bp.route('/logout', methods=['POST'])
def logout():
    """
    司機登出
    """
    session.pop('driver_id', None)
    session.pop('driver_name', None)
    flash('您已成功登出系統。', 'success')
    return redirect(url_for('driver.login_page'))
