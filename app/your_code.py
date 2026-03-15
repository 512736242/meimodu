import requests
import json
import time
import random
import string
from datetime import datetime

class MeimoAutoSign:
    def __init__(self, username, password):
        """
        初始化签到类，需要用户提供账号密码
        """
        self.base_url = "https://www.meimoai12.com/api"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authorization = None
        self.device_id = self._generate_device_id()
        
    def _generate_device_id(self):
        """生成设备ID"""
        timestamp = str(int(time.time() * 1000))
        random_num = ''.join(random.choices(string.digits, k=8))
        return f"{timestamp}{random_num}"
    
    def _generate_idempotency_key(self):
        """生成幂等键"""
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        timestamp = str(int(time.time() * 1000))[-6:]
        return f"{random_str}{timestamp}"
    
    def _get_headers(self):
        """生成请求头"""
        headers = {
            "Lang": "ZH",
            "Idempotency-Key": self._generate_idempotency_key(),
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if self.authorization:
            headers["Authorization"] = self.authorization
        return headers
    
    def login(self):
        """
        登录获取token
        :return: (是否成功, 消息)
        """
        try:
            url = f"{self.base_url}/user/login"
            login_data = {
                "username": self.username,
                "code": "",
                "password": self.password,
                "inviteCode": "",
                "deviceId": self.device_id
            }
            
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    data = result.get("data", {})
                    token = data.get("token")
                    if token:
                        self.authorization = token
                        return True, "登录成功", data
                return False, result.get("message", "登录失败")
            return False, f"网络错误: {response.status_code}"
        except Exception as e:
            return False, f"登录异常: {str(e)}"
    
    def get_user_info(self):
        """
        获取用户信息
        :return: (是否成功, 消息, 数据)
        """
        try:
            url = f"{self.base_url}/user/info"
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json={},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    return True, "获取成功", result.get("data", {})
                elif result.get("code") == 401:
                    return False, "登录已过期，请重新登录", None
                return False, result.get("message", "获取失败"), None
            return False, f"网络错误: {response.status_code}", None
        except Exception as e:
            return False, f"获取异常: {str(e)}", None
    
    def sign_in(self):
        """
        执行签到
        :return: (是否成功, 消息)
        """
        try:
            url = f"{self.base_url}/user/sign-in"
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json={},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200 and result.get("data") is True:
                    return True, "签到成功"
                elif result.get("code") == 401:
                    return False, "登录已过期，请重新登录"
                return False, result.get("message", "签到失败")
            return False, f"网络错误: {response.status_code}"
        except Exception as e:
            return False, f"签到异常: {str(e)}"
    
    def run(self):
        """
        执行完整的签到流程，返回结果字符串
        """
        result_messages = []
        result_messages.append(f"开始执行签到任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 登录
        login_success, login_msg, user_data = self.login()
        if not login_success:
            result_messages.append(f"❌ 登录失败: {login_msg}")
            return "\n".join(result_messages)
        
        result_messages.append(f"✅ 登录成功，用户: {user_data.get('nickname')}")
        
        # 2. 获取用户信息，检查签到状态
        info_success, info_msg, user_info = self.get_user_info()
        if not info_success:
            result_messages.append(f"❌ 获取用户信息失败: {info_msg}")
            return "\n".join(result_messages)
        
        today_is_sign = user_info.get('todayIsSign', False)
        result_messages.append(f"今日签到状态: {'✅ 已签到' if today_is_sign else '❌ 未签到'}")
        result_messages.append(f"当前余额: {user_info.get('balance')}")
        
        if today_is_sign:
            result_messages.append("ℹ️ 今日已经签到过了")
            return "\n".join(result_messages)
        
        # 3. 执行签到
        result_messages.append("开始签到...")
        sign_success, sign_msg = self.sign_in()
        if not sign_success:
            result_messages.append(f"❌ 签到失败: {sign_msg}")
            return "\n".join(result_messages)
        
        result_messages.append(f"✅ {sign_msg}")
        
        # 4. 确认签到结果
        time.sleep(2)
        _, _, user_info = self.get_user_info()
        if user_info and user_info.get('todayIsSign'):
            result_messages.append(f"🎉 签到确认成功！当前余额: {user_info.get('balance')}")
        else:
            result_messages.append("⚠️ 签到可能成功，但无法确认")
        
        result_messages.append(f"签到任务执行完毕 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(result_messages)


# 用于单独测试
if __name__ == "__main__":
    # 测试时手动输入账号密码
    u = input("请输入账号: ")
    p = input("请输入密码: ")
    sign = MeimoAutoSign(u, p)
    print(sign.run())
