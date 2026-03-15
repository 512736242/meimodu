# main.py
import requests
import os
import sys
import threading
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
from kivy.utils import get_color_from_hex, platform

# ========== 错误处理 ==========
def safe_get_data_dir():
    """安全获取数据目录"""
    try:
        if platform == 'android':
            # 尝试多个外部存储路径
            possible_dirs = [
                "/sdcard/美墨签到",
                "/storage/emulated/0/美墨签到",
            ]
            
            for dir_path in possible_dirs:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    # 测试写入
                    test_file = os.path.join(dir_path, ".test")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    print(f"使用目录: {dir_path}")
                    return dir_path
                except:
                    continue
            
            # 备选：应用私有目录
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            return '.'
    except:
        return '.'

DATA_DIR = safe_get_data_dir()
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts.json')

# ========== 中文字体 ==========
def init_chinese_font():
    """初始化中文字体（借鉴你的代码）"""
    try:
        # 尝试项目内字体
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
        font_path = os.path.join(font_dir, 'NotoSansSC-Regular.ttf')
        if os.path.exists(font_path):
            LabelBase.register(name='ChineseFont', fn_regular=font_path)
            return 'ChineseFont'
        
        # 尝试系统字体
        android_fonts = [
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/DroidSansFallback.ttf',
        ]
        for font in android_fonts:
            if os.path.exists(font):
                LabelBase.register(name='ChineseFont', fn_regular=font)
                return 'ChineseFont'
    except:
        pass
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
        try:
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
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 200:
                    return {"success": True, "token": result["data"].get("token"), "nickname": result["data"].get("nickname")}
            return {"success": False, "msg": "登录失败"}
        except Exception as e:
            return {"success": False, "msg": str(e)}
    
    def get_info(self, token):
        try:
            url = f"{self.base_url}/user/info"
            headers = {
                "Lang": "ZH",
                "Authorization": token,
                "Content-Type": "application/json"
            }
            resp = requests.post(url, headers=headers, json={}, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 200:
                    return {"success": True, "data": result["data"]}
            return {"success": False}
        except:
            return {"success": False}
    
    def sign(self, token):
        try:
            url = f"{self.base_url}/user/sign-in"
            headers = {
                "Lang": "ZH",
                "Idempotency-Key": self._generate_id(),
                "Authorization": token,
                "Content-Type": "application/json"
            }
            resp = requests.post(url, headers=headers, json={}, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 200 and result.get("data") is True:
                    return {"success": True}
            return {"success": False}
        except:
            return {"success": False}


# ========== 账号管理 ==========
class AccountManager:
    def __init__(self):
        self.accounts = []
        self.load()
    
    def load(self):
        try:
            if os.path.exists(ACCOUNTS_FILE):
                with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
        except:
            self.accounts = []
    
    def save(self):
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
            with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add(self, user, pwd):
        for acc in self.accounts:
            if acc['user'] == user:
                return False
        self.accounts.append({'user': user, 'pwd': pwd})
        self.save()
        return True
    
    def remove(self, user):
        self.accounts = [a for a in self.accounts if a['user'] != user]
        self.save()
    
    def get_all(self):
        return self.accounts


# ========== 主界面 ==========
class SignScreen(BoxLayout):
    def __init__(self, **kwargs):
        try:
            super().__init__(orientation='vertical', **kwargs)
            self.core = SignCore()
            self.accounts = AccountManager()
            
            # 背景
            with self.canvas.before:
                Color(*COLORS['bg'])
                self.bg = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)
            
            # 标题
            title = Label(
                text='美墨签到',
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                font_size=dp(24),
                size_hint_y=None,
                height=dp(60)
            )
            self.add_widget(title)
            
            # 输入区
            input_box = BoxLayout(size_hint_y=None, height=dp(100), padding=dp(10), spacing=dp(5))
            with input_box.canvas.before:
                Color(*COLORS['card'])
                input_box.rect = Rectangle(pos=input_box.pos, size=input_box.size)
            input_box.bind(pos=self._update_rect, size=self._update_rect)
            
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
            
            input_box.add_widget(self.user_input)
            input_box.add_widget(self.pwd_input)
            input_box.add_widget(btn_row)
            self.add_widget(input_box)
            
            # 账号列表
            list_title = Label(
                text='待签到账号',
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                size_hint_y=None,
                height=dp(30)
            )
            self.add_widget(list_title)
            
            self.list_scroll = ScrollView(size_hint_y=0.3)
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
            log_title = Label(
                text='执行日志',
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                size_hint_y=None,
                height=dp(30)
            )
            self.add_widget(log_title)
            
            self.log_text = TextInput(
                text='[就绪]\n',
                readonly=True,
                font_name=DEFAULT_FONT,
                font_size=dp(12)
            )
            self.add_widget(self.log_text)
            
            # 刷新列表
            self.refresh_list()
            
        except Exception as e:
            print(f"初始化错误: {e}")
            # 如果初始化失败，显示错误界面
            self.add_widget(Label(
                text=f"启动失败: {e}",
                color=COLORS['error'],
                font_name=DEFAULT_FONT
            ))
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def _update_rect(self, instance, *args):
        if hasattr(instance, 'rect'):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
    
    def refresh_list(self):
        try:
            self.list_layout.clear_widgets()
            accounts = self.accounts.get_all()
            
            if not accounts:
                self.list_layout.add_widget(Label(
                    text='暂无账号',
                    color=COLORS['text'],
                    font_name=DEFAULT_FONT,
                    size_hint_y=None,
                    height=dp(40)
                ))
                return
            
            for acc in accounts:
                row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
                
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
        except Exception as e:
            self.log(f"刷新列表错误: {e}")
    
    def add_account(self, btn):
        try:
            user = self.user_input.text.strip()
            pwd = self.pwd_input.text.strip()
            
            if not user or not pwd:
                self.log("❌ 账号密码不能为空")
                return
            
            if self.accounts.add(user, pwd):
                self.log(f"✅ 已添加账号: {user[:3]}***")
                self.user_input.text = ''
                self.pwd_input.text = ''
                self.refresh_list()
            else:
                self.log(f"⚠️ 账号 {user[:3]}*** 已存在")
        except Exception as e:
            self.log(f"添加账号错误: {e}")
    
    def clear_input(self, btn):
        self.user_input.text = ''
        self.pwd_input.text = ''
    
    def remove_account(self, user, btn):
        try:
            self.accounts.remove(user)
            self.log(f"🗑️ 已移除账号: {user[:3]}***")
            self.refresh_list()
        except Exception as e:
            self.log(f"移除账号错误: {e}")
    
    def do_sign(self, btn):
        try:
            accounts = self.accounts.get_all()
            if not accounts:
                self.log("❌ 请先添加账号")
                return
            
            self.sign_btn.disabled = True
            self.sign_btn.text = '签到中...'
            self.log_text.text = '[开始签到]\n'
            
            def run():
                try:
                    for i, acc in enumerate(accounts, 1):
                        self.log(f"\n===== 第 {i}/{len(accounts)} 个账号 =====")
                        self.log(f"📱 账号: {acc['user'][:3]}***")
                        
                        # 登录
                        self.log("📡 登录中...")
                        login_res = self.core.login(acc['user'], acc['pwd'])
                        if not login_res['success']:
                            self.log(f"❌ 登录失败: {login_res.get('msg', '未知错误')}")
                            continue
                        
                        token = login_res['token']
                        nickname = login_res.get('nickname', '未知')
                        self.log(f"✅ 登录成功 - {nickname}")
                        
                        # 检查是否已签到
                        info = self.core.get_info(token)
                        if info['success'] and info['data'].get('todayIsSign'):
                            self.log(f"ℹ️ 今日已签到，余额: {info['data'].get('balance')}")
                            continue
                        
                        # 签到
                        self.log("🎯 签到中...")
                        sign_res = self.core.sign(token)
                        if sign_res['success']:
                            self.log("✅ 签到成功")
                            time.sleep(1)
                            info2 = self.core.get_info(token)
                            if info2['success']:
                                self.log(f"💰 当前余额: {info2['data'].get('balance')}")
                        else:
                            self.log("❌ 签到失败")
                        
                        time.sleep(2)
                    
                    self.log("\n✨ 所有账号签到完成")
                except Exception as e:
                    self.log(f"签到过程错误: {e}")
                finally:
                    self.enable_btn()
            
            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            self.log(f"开始签到错误: {e}")
            self.enable_btn()
    
    @mainthread
    def log(self, msg):
        try:
            self.log_text.text += msg + '\n'
            self.log_text.cursor = (0, len(self.log_text.text))
        except:
            pass
    
    @mainthread
    def enable_btn(self):
        try:
            self.sign_btn.disabled = False
            self.sign_btn.text = '开始签到'
        except:
            pass


# ========== 应用 ==========
class SignApp(App):
    def build(self):
        try:
            Window.clearcolor = COLORS['bg']
            # 延迟加载，给系统准备时间
            Clock.schedule_once(lambda dt: self.show_main(), 0.1)
            
            # 先显示加载界面
            loading = BoxLayout()
            with loading.canvas.before:
                Color(*COLORS['bg'])
                Rectangle(pos=(0, 0), size=Window.size)
            loading.add_widget(Label(
                text='加载中...',
                color=COLORS['text'],
                font_name=DEFAULT_FONT,
                font_size=dp(20)
            ))
            return loading
        except Exception as e:
            print(f"build错误: {e}")
            return Label(text=f"启动失败: {e}")
    
    def show_main(self, dt=None):
        try:
            self.root.clear_widgets()
            self.root.add_widget(SignScreen())
        except Exception as e:
            print(f"显示主界面错误: {e}")
            self.root.clear_widgets()
            self.root.add_widget(Label(
                text=f"界面加载失败: {e}",
                color=COLORS['error']
            ))


if __name__ == '__main__':
    try:
        SignApp().run()
    except Exception as e:
        print(f"应用崩溃: {e}")
        # 尝试写崩溃日志
        try:
            with open('/sdcard/crash.txt', 'w') as f:
                f.write(str(e))
        except:
            pass         color=COLORS['text'],
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
