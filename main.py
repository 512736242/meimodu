# main.py
"""
美梦AI多账号签到工具
支持多个账号同时签到
"""
import os
import threading
import json
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
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

# 导入你的签到脚本
from app.your_code import MeimoAutoSign

# 颜色主题
COLORS = {
    'bg': get_color_from_hex('#1a1a2e'),
    'card': get_color_from_hex('#16213e'),
    'primary': get_color_from_hex('#e94560'),
    'text': get_color_from_hex('#eaeaea'),
    'success': get_color_from_hex('#4ecca3'),
    'error': get_color_from_hex('#ff6b6b'),
}


class AccountRow(BoxLayout):
    """单个账号行"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(5)
        
        # 账号输入
        self.username = TextInput(
            hint_text='账号',
            multiline=False,
            size_hint_x=0.35,
            background_color=COLORS['card'],
            foreground_color=COLORS['text'],
            cursor_color=COLORS['primary']
        )
        self.add_widget(self.username)
        
        # 密码输入
        self.password = TextInput(
            hint_text='密码',
            multiline=False,
            password=True,
            size_hint_x=0.35,
            background_color=COLORS['card'],
            foreground_color=COLORS['text'],
            cursor_color=COLORS['primary']
        )
        self.add_widget(self.password)
        
        # 删除按钮
        self.del_btn = Button(
            text='✕',
            size_hint_x=0.1,
            background_color=COLORS['error'],
            color=COLORS['text']
        )
        self.add_widget(self.del_btn)


class SignApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = []  # 账号列表
        self.results = []   # 结果列表
        
    def build(self):
        self.title = '美梦AI签到'
        Window.clearcolor = COLORS['bg']
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(
            text='美梦AI 多账号签到',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(20),
            color=COLORS['text'],
            bold=True
        )
        main_layout.add_widget(title)
        
        # 账号列表区域（可滚动）
        scroll = ScrollView(size_hint_y=0.7)
        self.accounts_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.accounts_layout.bind(minimum_height=self.accounts_layout.setter('height'))
        scroll.add_widget(self.accounts_layout)
        main_layout.add_widget(scroll)
        
        # 按钮区域
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        
        # 添加账号按钮
        add_btn = Button(
            text='+ 添加账号',
            background_color=COLORS['card'],
            color=COLORS['text']
        )
        add_btn.bind(on_press=self.add_account)
        btn_layout.add_widget(add_btn)
        
        # 开始签到按钮
        self.sign_btn = Button(
            text='开始签到',
            background_color=COLORS['primary'],
            color=COLORS['text']
        )
        self.sign_btn.bind(on_press=self.start_sign)
        btn_layout.add_widget(self.sign_btn)
        
        main_layout.add_widget(btn_layout)
        
        # 结果显示区域
        result_label = Label(
            text='签到结果',
            size_hint_y=None,
            height=dp(30),
            color=COLORS['text']
        )
        main_layout.add_widget(result_label)
        
        # 结果列表
        result_scroll = ScrollView(size_hint_y=0.2)
        self.result_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        result_scroll.add_widget(self.result_layout)
        main_layout.add_widget(result_scroll)
        
        # 先添加一个默认的账号行
        self.add_account()
        
        return main_layout
    
    def add_account(self, instance=None):
        """添加新的账号行"""
        row = AccountRow()
        row.del_btn.bind(on_press=lambda x: self.remove_account(row))
        self.accounts_layout.add_widget(row)
        self.accounts.append(row)
    
    def remove_account(self, row):
        """删除账号行"""
        if row in self.accounts:
            self.accounts.remove(row)
            self.accounts_layout.remove_widget(row)
    
    def start_sign(self, instance):
        """开始签到"""
        # 禁用按钮
        self.sign_btn.disabled = True
        self.sign_btn.text = '签到中...'
        
        # 清空结果
        self.result_layout.clear_widgets()
        
        # 收集要签到的账号
        accounts_to_sign = []
        for row in self.accounts:
            username = row.username.text.strip()
            password = row.password.text.strip()
            if username and password:
                accounts_to_sign.append((username, password))
        
        if not accounts_to_sign:
            self.show_result('没有输入任何账号密码')
            self.sign_btn.disabled = False
            self.sign_btn.text = '开始签到'
            return
        
        self.show_result(f'开始为 {len(accounts_to_sign)} 个账号签到...')
        
        # 在新线程中执行签到
        threading.Thread(target=self.do_sign_all, args=(accounts_to_sign,), daemon=True).start()
    
    def do_sign_all(self, accounts):
        """为所有账号签到"""
        for i, (username, password) in enumerate(accounts, 1):
            try:
                # 显示进度
                self.show_result(f'[{i}/{len(accounts)}] 账号 {username} 签到中...')
                
                # 执行签到
                signer = MeimoAutoSign(username, password)
                result = signer.run()
                
                # 提取关键信息
                if '✅ 登录成功' in result and '签到成功' in result:
                    self.show_result(f'✅ 账号 {username} 签到成功')
                elif '今日已经签到过了' in result:
                    self.show_result(f'ℹ️ 账号 {username} 今日已签到')
                else:
                    # 显示错误信息的第一行
                    error_line = result.split('\n')[0]
                    self.show_result(f'❌ 账号 {username} 失败: {error_line[:30]}')
                    
            except Exception as e:
                self.show_result(f'❌ 账号 {username} 异常: {str(e)}')
        
        # 签到完成
        self.show_result('=' * 30)
        self.show_result(f'✅ 全部签到完成！')
        
        # 恢复按钮
        Clock.schedule_once(self.enable_button, 0)
    
    def enable_button(self, dt):
        """恢复按钮状态"""
        self.sign_btn.disabled = False
        self.sign_btn.text = '开始签到'
    
    @mainthread
    def show_result(self, text):
        """显示结果"""
        # 添加时间戳
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 根据结果类型设置颜色
        if '✅' in text:
            color = COLORS['success']
        elif '❌' in text:
            color = COLORS['error']
        elif 'ℹ️' in text:
            color = [1, 1, 0, 1]  # 黄色
        else:
            color = COLORS['text']
        
        # 创建结果标签
        label = Label(
            text=f'[{timestamp}] {text}',
            size_hint_y=None,
            height=dp(25),
            color=color,
            halign='left',
            valign='middle',
            text_size=(Window.width - 40, dp(25))
        )
        self.result_layout.add_widget(label)
        
        # 自动滚动到底部（简单实现）
        Clock.schedule_once(lambda dt: setattr(self.result_layout.parent, 'scroll_y', 0), 0.1)


if __name__ == '__main__':
    SignApp().run()
