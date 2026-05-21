from flask import render_template, request
from . import main_bp

@main_bp.route('/', methods=['GET'])
def index():
    """
    首頁
    顯示搜尋特定路線與附近站牌功能的介面
    """
    pass

@main_bp.route('/route-plan', methods=['GET'])
def route_plan():
    """
    路線與轉乘規劃
    如果有 start 與 end 參數，則呼叫 TDX API 計算並顯示結果
    否則顯示規劃表單
    """
    pass
