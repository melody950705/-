from flask import render_template, request, redirect, url_for, session, flash
from . import driver_bp
from ..models.driver import Driver
from ..models.report import Report

@driver_bp.route('/driver/login', methods=['GET'])
def login_page():
    """
    司機登入頁面
    若已登入，直接重導至回報頁面
    """
    pass

@driver_bp.route('/driver/login', methods=['POST'])
def login_submit():
    """
    司機登入驗證
    驗證帳號密碼，成功則建立 session 並重導向
    失敗則顯示錯誤訊息
    """
    pass

@driver_bp.route('/driver/report', methods=['GET'])
def report_page():
    """
    司機回報頁面
    檢查 session 權限，未登入則導向登入頁面
    """
    pass

@driver_bp.route('/driver/report', methods=['POST'])
def report_submit():
    """
    司機送出回報
    接收路況、故障或滿載狀態，寫入資料庫
    """
    pass

@driver_bp.route('/driver/logout', methods=['POST'])
def logout():
    """
    司機登出
    清除 session 並重導向至首頁或登入頁
    """
    pass
