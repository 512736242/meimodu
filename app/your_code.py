# app/your_code.py - 无文件操作版
import requests
import time
import random
import string

def generate_id():
    return str(int(time.time() * 1000)) + ''.join(random.choices(string.digits, k=8))

def login(username, password):
    url = "https://www.meimoai12.com/api/user/login"
    headers = {
        "Lang": "ZH",
        "Idempotency-Key": generate_id(),
        "Content-Type": "application/json"
    }
    data = {
        "username": username,
        "password": password,
        "code": "",
        "inviteCode": "",
        "deviceId": generate_id()
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 200:
                return {"success": True, "token": result["data"].get("token")}
        return {"success": False}
    except:
        return {"success": False}

def do_sign(token):
    url = "https://www.meimoai12.com/api/user/sign-in"
    headers = {
        "Lang": "ZH",
        "Idempotency-Key": generate_id(),
        "Authorization": token,
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, json={}, timeout=10)
        return resp.status_code == 200
    except:
        return False

def run(args=None):
    """极简版 - 无文件操作"""
    if not args or len(args) < 2:
        return "用法: 账号 密码"
    
    username, password = args[0], args[1]
    
    result = f"开始签到: {username[:3]}***\n"
    
    # 登录
    login_res = login(username, password)
    if not login_res['success']:
        return result + "❌ 登录失败"
    
    token = login_res['token']
    result += "✅ 登录成功\n"
    
    # 签到
    if do_sign(token):
        result += "✅ 签到成功"
    else:
        result += "❌ 签到失败"
    
    return result
