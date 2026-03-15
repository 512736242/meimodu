"""
MeiMoAI 每日签到 - 精简版
登录 + 签到按钮 + 日志 + 多账号
"""
import os
import threading
import requests
import json
import time
import random
import string
from datetime import datetime
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

# 中文字体设置
def init_chinese_font():
    fonts = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansFallback.ttf',
    ]
    for font in fonts:
        if os.path.exists(font):
            LabelBase.register(name='ChineseFont', fn_regular=font)
            return 'ChineseFont'
    return None

DEFAULT_FONT = init_chinese_font()

# 颜色
COLORS = {
    'bg': get_color_from_hex('#1a1a2e'),
    'card': get_color_from_hex('#16213e'),
    'primary': get_color_from_hex('#e94560'),
    'secondary': get_color_from_hex('#0f3460'),
    'text': get_color_from_hex('#eaeaea'),
    'success': get_color_from_hex('#4ecca3'),
    'error': get_color_from_hex('#ff6b6b'),
}


# ========== 签到核心 ==========
class SignCore:
    def __init__(self):
        self.base_url = "https://www.meimoai12.com/api"
    
    def _generate_id(self):
        return str(int(time.time() * 1000)) + ''.join(random.choices(string.digits, k=8))
    
    def login(self, username, password):
        url = f"{self.base_url}/user/login"
        headers = {
            "Lang": "ZH",
            "Idempotency-Key": self._generate_id(),
            "Content-Type": "application/json"
        }
        data = {
            "username": username,
            "password": password,
            "code": "",
            "inviteCode": "",
            "deviceId": self._generate_id()
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 200:
                    return {"success": True, "token": result["data"].get("token"), "data": result["data"]}
                return {"success": False, "msg": result.get("message")}
            return {"success": False, "msg": f"网络错误 {resp.status_code}"}
        except Exception as e:
            return {"success": False, "msg": str(e)}
    
    def get_info(self, token):
        url = f"{self.base_url}/user/info"
        headers = {"Lang": "ZH", "Authorization": token, "Content-Type": "application/json"}
        try:
            resp = requests.post(url, headers=headers, json={}, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 200:
                    return {"success": True, "data": result["data"]}
            return {"success": False}
        except:
            return {"success": False}
    
    def sign(self, token):
        url = f"{self.base_url}/user/sign-in"
        headers = {
            "Lang": "ZH",
            "Idempotency-Key": self._generate_id(),
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


# ========== 主界面 ==========
class SignScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.core = SignCore()
        self.accounts = []  # 账号列表 [{"user": "", "pwd": ""}]
        
        # 背景
        with self.canvas.before:
            Color(*COLORS['bg'])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 标题
        title = Label(
            text='MeiMoAI 每日签到',
            color=COLORS['text'],
            font_name=DEFAULT_FONT,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(50)
        )
        self.add_widget(title)
        
        # 输入区
        input_card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), padding=dp(10), spacing=dp(5))
        with input_card.canvas.before:
            Color(*COLORS['card'])
            Rectangle(pos=input_card.pos, size=input_card.size)
        input_card.bind(pos=self._update_rect, size=self._update_rect)
        
        self.user_input = TextInput(
            hint_text='账号',
            multiline=False,
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=dp(40)
        )
        self.pwd_input = TextInput(
            hint_text='密码',
            multiline=False,
            password=True,
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=dp(40)
        )
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        add_btn = Button(
            text='添加账号',
            background_normal='',
            background_color=COLORS['secondary'],
            color=COLORS['text'],
            font_name=DEFAULT_FONT
        )
        add_btn.bind(on_press=self.add_account)
        
        clear_btn = Button(
            text='清空',
            background_normal='',
            background_color=COLORS['error'],
            color=COLORS['text'],
            font_name=DEFAULT_FONT
        )
        clear_btn.bind(on_press=self.clear_input)
        
        btn_row.add_widget(add_btn)
        btn_row.add_widget(clear_btn)
        
        input_card.add_widget(self.user_input)
        input_card.add_widget(self.pwd_input)
        input_card.add_widget(btn_row)
        self.add_widget(input_card)
        
        # 账号列表
        list_label = Label(
            text='待签到账号',
            color=COLORS['text'],
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(list_label)
        
        self.list_scroll = ScrollView(size_hint_y=0.4)
        self.list_layout = GridLayout(cols=1, spacing=dp(3), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.list_scroll.add_widget(self.list_layout)
        self.add_widget(self.list_scroll)
        
        # 签到按钮
        self.sign_btn = Button(
            text='开始签到',
            background_normal='',
            background_color=COLORS['primary'],
            color=COLORS['text'],
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=dp(50),
            bold=True
        )
        self.sign_btn.bind(on_press=self.do_sign)
        self.add_widget(self.sign_btn)
        
        # 日志
        log_label = Label(
            text='执行日志',
            color=COLORS['text'],
            font_name=DEFAULT_FONT,
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(log_label)
        
        self.log_text = TextInput(
            text='[就绪]\n',
            readonly=True,
            font_name=DEFAULT_FONT,
            font_size=dp(12)
        )
        self.add_widget(self.log_text)
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def _update_rect(self, instance, *args):
        instance.canvas.before.children[1].pos = instance.pos
        instance.canvas.before.children[1].size = instance.size
    
    def add_account(self, btn):
        user = self.user_input.text.strip()
        pwd = self.pwd_input.text.strip()
        if not user or not pwd:
            self.log("❌ 账号密码不能为空")
            return
        
        # 去重
        for acc in self.accounts:
            if acc['user'] == user:
                self.log(f"⚠️ 账号 {user} 已存在")
                return
        
        self.accounts.append({'user': user, 'pwd': pwd})
        self.update_list()
        self.user_input.text = ''
        self.pwd_input.text = ''
        self.log(f"✅ 已添加账号: {user}")
    
    def clear_input(self, btn):
        self.user_input.text = ''
        self.pwd_input.text = ''
    
    def remove_account(self, user, btn):
        self.accounts = [a for a in self.accounts if a['user'] != user]
        self.update_list()
        self.log(f"🗑️ 已移除账号: {user}")
    
    def update_list(self):
        self.list_layout.clear_widgets()
        if not self.accounts:
            self.list_layout.add_widget(Label(
                text='暂无账号',
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        for acc in self.accounts:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            
            # 显示部分账号
            user = acc['user']
            display = user[:3] + '***' + user[-4:] if len(user) > 7 else user
            
            label = Label(
                text=display,
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                size_hint_x=0.7,
                halign='left'
            )
            label.bind(size=label.setter('text_size'))
            
            rm_btn = Button(
                text='移除',
                size_hint_x=0.3,
                background_normal='',
                background_color=COLORS['error'],
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                font_size=dp(11)
            )
            rm_btn.bind(on_press=partial(self.remove_account, acc['user']))
            
            row.add_widget(label)
            row.add_widget(rm_btn)
            self.list_layout.add_widget(row)
    
    def do_sign(self, btn):
        if not self.accounts:
            self.log("❌ 请先添加账号")
            return
        
        self.sign_btn.disabled = True
        self.sign_btn.text = '签到中...'
        self.log_text.text = '[开始签到]\n'
        
        def run():
            for i, acc in enumerate(self.accounts):
                self.log(f"\n===== 第 {i+1}/{len(self.accounts)} 个账号 =====")
                self.log(f"📱 账号: {acc['user'][:3]}***{acc['user'][-4:]}")
                
                # 登录
                self.log("📡 登录中...")
                login_res = self.core.login(acc['user'], acc['pwd'])
                if not login_res['success']:
                    self.log(f"❌ 登录失败: {login_res.get('msg', '未知错误')}")
                    continue
                
                token = login_res['token']
                nickname = login_res['data'].get('nickname', '未知')
                self.log(f"✅ 登录成功 - {nickname}")
                
                # 获取信息
                info = self.core.get_info(token)
                if info['success']:
                    data = info['data']
                    if data.get('todayIsSign'):
                        self.log(f"ℹ️ 今日已签到，余额: {data.get('balance')}")
                        continue
                
                # 签到
                self.log("🎯 签到中...")
                sign_res = self.core.sign(token)
                if sign_res['success']:
                    self.log("✅ 签到成功")
                    time.sleep(1)
                    # 确认结果
                    info2 = self.core.get_info(token)
                    if info2['success']:
                        self.log(f"💰 当前余额: {info2['data'].get('balance')}")
                else:
                    self.log(f"❌ 签到失败: {sign_res.get('msg', '未知错误')}")
                
                time.sleep(2)  # 间隔
            
            self.log("\n✨ 所有账号签到完成")
            self.enable_btn()
        
        threading.Thread(target=run, daemon=True).start()
    
    @mainthread
    def log(self, msg):
        self.log_text.text += msg + '\n'
        # 滚动到底部
        self.log_text.cursor = (0, len(self.log_text.text))
    
    @mainthread
    def enable_btn(self):
        self.sign_btn.disabled = False
        self.sign_btn.text = '开始签到'


# ========== 应用 ==========
class SignApp(App):
    def build(self):
        Window.clearcolor = COLORS['bg']
        return SignScreen()


if __name__ == '__main__':
    SignApp().run()
