import requests
import json
import time
import random
import string
from datetime import datetime

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
                return {"success": True, "token": result["data"].get("token"), "nickname": result["data"].get("nickname")}
            return {"success": False, "msg": result.get("message")}
        return {"success": False, "msg": f"网络错误 {resp.status_code}"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def get_user_info(token):
    url = "https://www.meimoai12.com/api/user/info"
    headers = {
        "Lang": "ZH",
        "Authorization": token,
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, json={}, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 200:
                return {"success": True, "data": result["data"]}
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
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 200 and result.get("data") is True:
                return {"success": True}
            return {"success": False, "msg": result.get("message")}
        return {"success": False, "msg": f"网络错误 {resp.status_code}"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

# 账号管理
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.load()
    
    def load(self):
        try:
            with open('accounts.json', 'r') as f:
                self.accounts = json.load(f)
        except:
            self.accounts = []
    
    def save(self):
        try:
            with open('accounts.json', 'w') as f:
                json.dump(self.accounts, f)
        except:
            pass
    
    def add(self, user, pwd):
        for acc in self.accounts:
            if acc['user'] == user:
                return False, "账号已存在"
        self.accounts.append({'user': user, 'pwd': pwd})
        self.save()
        return True, "添加成功"
    
    def remove(self, user):
        self.accounts = [a for a in self.accounts if a['user'] != user]
        self.save()
    
    def list(self):
        result = []
        for acc in self.accounts:
            display = acc['user'][:3] + '***' + acc['user'][-4:] if len(acc['user']) > 7 else acc['user']
            result.append(f"账号: {display}")
        return result

# 全局账号管理器
_account_manager = AccountManager()

# 必须保留的入口函数
def run(args: list = None):
    """
    入口函数 - APP会调用这个函数
    用法:
      add 账号 密码     - 添加账号
      list              - 查看所有账号
      del 账号           - 删除账号
      sign all          - 签到所有账号
      sign 账号 密码     - 为指定账号签到
    """
    if not args or len(args) == 0:
        return """美墨签到工具 v1.0

可用命令:
  add 账号 密码     - 添加账号
  list              - 查看所有账号
  del 账号           - 删除账号
  sign all          - 签到所有账号
  sign 账号 密码     - 为指定账号签到

示例:
  add 13800138000 123456
  list
  sign all
  sign 13800138000 123456
"""

    cmd = args[0].lower()
    
    if cmd == "add" and len(args) >= 3:
        user, pwd = args[1], args[2]
        ok, msg = _account_manager.add(user, pwd)
        return f"{'✅' if ok else '❌'} {msg}\n当前共有 {len(_account_manager.accounts)} 个账号"
    
    elif cmd == "list":
        accounts = _account_manager.list()
        if not accounts:
            return "📭 暂无保存的账号"
        return f"📋 已保存账号 ({len(_account_manager.accounts)}个):\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(accounts))
    
    elif cmd == "del" and len(args) >= 2:
        _account_manager.remove(args[1])
        return f"🗑️ 已删除账号: {args[1]}"
    
    elif cmd == "sign":
        return handle_sign(args[1:])
    
    else:
        return f"❌ 未知命令: {cmd}\n输入 help 查看帮助"

def handle_sign(args):
    if not args:
        return "❌ 用法: sign all 或 sign 账号 密码"
    
    results = []
    
    if args[0].lower() == "all":
        accounts = _account_manager.accounts
        if not accounts:
            return "❌ 没有保存的账号，请先用 add 添加"
        
        results.append(f"🚀 开始批量签到，共 {len(accounts)} 个账号")
        for i, acc in enumerate(accounts, 1):
            results.append(f"\n===== 第 {i}/{len(accounts)} 个账号 =====")
            results.extend(do_sign_for_account(acc['user'], acc['pwd']))
            if i < len(accounts):
                time.sleep(2)
        results.append("\n✨ 批量签到完成")
    
    elif len(args) >= 2:
        user, pwd = args[0], args[1]
        results.append(f"🚀 开始为账号 {user[:3]}*** 签到")
        results.extend(do_sign_for_account(user, pwd))
    
    else:
        return "❌ 用法: sign all 或 sign 账号 密码"
    
    return "\n".join(results)

def do_sign_for_account(username, password):
    logs = []
    
    logs.append("📡 登录中...")
    login_res = login(username, password)
    if not login_res['success']:
        logs.append(f"❌ 登录失败: {login_res.get('msg', '未知错误')}")
        return logs
    
    token = login_res['token']
    nickname = login_res.get('nickname', '未知')
    logs.append(f"✅ 登录成功 - {nickname}")
    
    info = get_user_info(token)
    if info['success']:
        data = info['data']
        if data.get('todayIsSign'):
            logs.append(f"ℹ️ 今日已签到，余额: {data.get('balance')}")
            return logs
    
    logs.append("🎯 签到中...")
    sign_res = do_sign(token)
    if sign_res['success']:
        logs.append("✅ 签到成功")
        time.sleep(1)
        info2 = get_user_info(token)
        if info2['success']:
            logs.append(f"💰 当前余额: {info2['data'].get('balance')}")
    else:
        logs.append(f"❌ 签到失败: {sign_res.get('msg', '未知错误')}")
    
    return logs


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(run(sys.argv[1:]))
    else:
        print(run([]))
