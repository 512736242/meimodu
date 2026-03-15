# main.py
"""
美梦AI多账号签到工具
支持多个账号同时签到，自动保存账号
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

# ========== 字体设置 ==========
def setup_fonts():
    """设置中文字体"""
    font_paths = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/NotoSansSC-Regular.otf',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/Roboto-Regular.ttf',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                LabelBase.register(name='ChineseFont', fn_regular=font_path)
                print(f"找到字体: {font_path}")
                return 'ChineseFont'
            except:
                continue
    
    print("未找到中文字体，使用默认字体")
    return None

DEFAULT_FONT = setup_fonts()

# 颜色主题
COLORS = {
    'bg': get_color_from_hex('#1a1a2e'),
    'card': get_color_from_hex('#16213e'),
    'primary': get_color_from_hex('#e94560'),
    'secondary': get_color_from_hex('#0f3460'),
    'text': get_color_from_hex('#eaeaea'),
    'success': get_color_from_hex('#4ecca3'),
    'error': get_color_from_hex('#ff6b6b'),
}


class StyledTextInput(TextInput):
    """自定义输入框"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COLORS['card']
        self.foreground_color = COLORS['text']
        self.cursor_color = COLORS['primary']
        self.font_name = DEFAULT_FONT if DEFAULT_FONT else 'Roboto'
        self.font_size = dp(14)


class StyledButton(Button):
    """自定义按钮"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.font_name = DEFAULT_FONT if DEFAULT_FONT else 'Roboto'
        self.font_size = dp(14)


class StyledLabel(Label):
    """自定义标签"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = DEFAULT_FONT if DEFAULT_FONT else 'Roboto'
        self.font_size = dp(14)


class AccountRow(BoxLayout):
    """单个账号行"""
    def __init__(self, username='', password='', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(5)
        
        # 账号输入
        self.username = StyledTextInput(
            hint_text='账号',
            text=username,
            multiline=False,
            size_hint_x=0.4
        )
        self.add_widget(self.username)
        
        # 密码输入
        self.password = StyledTextInput(
            hint_text='密码',
            text=password,
            multiline=False,
            password=True,
            size_hint_x=0.4
        )
        self.add_widget(self.password)
        
        # 删除按钮
        self.del_btn = StyledButton(
            text='删除',
            size_hint_x=0.15,
            background_color=COLORS['error']
        )
        self.add_widget(self.del_btn)
    
    def get_account(self):
        """获取账号密码"""
        return {
            'username': self.username.text.strip(),
            'password': self.password.text.strip()
        }


class SignApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = []
        # 获取应用私有目录，确保有写入权限
        self.data_dir = self.get_data_dir()
        self.accounts_file = os.path.join(self.data_dir, 'accounts.json')
        print(f"账号文件位置: {self.accounts_file}")
        
    def get_data_dir(self):
        """获取数据保存目录"""
        try:
            # Android 平台
            from android.storage import primary_external_storage_path
            sdcard = primary_external_storage_path()
            app_dir = os.path.join(sdcard, 'MeimoSign')
            os.makedirs(app_dir, exist_ok=True)
            return app_dir
        except:
            # 非 Android 平台
            return os.path.dirname(os.path.abspath(__file__))
        
    def build(self):
        self.title = '美梦AI签到'
        Window.clearcolor = COLORS['bg']
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = StyledLabel(
            text='美梦AI 多账号签到',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(22),
            bold=True,
            color=COLORS['primary']
        )
        main_layout.add_widget(title)
        
        # 账号列表区域
        scroll = ScrollView(size_hint_y=0.6)
        self.accounts_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.accounts_layout.bind(minimum_height=self.accounts_layout.setter('height'))
        scroll.add_widget(self.accounts_layout)
        main_layout.add_widget(scroll)
        
        # 按钮区域
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        
        # 添加账号按钮
        add_btn = StyledButton(
            text='+ 添加账号',
            background_color=COLORS['secondary']
        )
        add_btn.bind(on_press=self.add_account)
        btn_layout.add_widget(add_btn)
        
        # 保存账号按钮
        save_btn = StyledButton(
            text='保存账号',
            background_color=COLORS['secondary']
        )
        save_btn.bind(on_press=self.save_accounts)
        btn_layout.add_widget(save_btn)
        
        # 开始签到按钮
        self.sign_btn = StyledButton(
            text='开始签到',
            background_color=COLORS['primary']
        )
        self.sign_btn.bind(on_press=self.start_sign)
        btn_layout.add_widget(self.sign_btn)
        
        main_layout.add_widget(btn_layout)
        
        # 结果显示区域
        result_label = StyledLabel(
            text='签到结果',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        main_layout.add_widget(result_label)
        
        # 结果列表
        result_scroll = ScrollView(size_hint_y=0.25)
        self.result_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        result_scroll.add_widget(self.result_layout)
        main_layout.add_widget(result_scroll)
        
        # ===== 关键修复：先加载保存的账号 =====
        self.load_accounts()
        
        # 如果没加载到账号，添加一个默认的空账号行
        if len(self.accounts_layout.children) == 0:
            self.add_account()
        
        return main_layout
    
    def load_accounts(self):
        """从文件加载保存的账号"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    saved_accounts = json.load(f)
                    print(f"找到保存的账号文件，共 {len(saved_accounts)} 个账号")
                    
                    # 清空现有账号行
                    self.accounts_layout.clear_widgets()
                    
                    # 添加保存的账号
                    for acc in saved_accounts:
                        self.add_account(
                            username=acc.get('username', ''),
                            password=acc.get('password', '')
                        )
                    
                    self.show_result(f'✅ 已加载 {len(saved_accounts)} 个保存的账号')
            else:
                print("没有找到保存的账号文件")
        except Exception as e:
            print(f"加载账号失败: {e}")
            self.show_result(f'❌ 加载账号失败: {e}')
    
    def save_accounts(self, instance=None):
        """保存账号到文件"""
        try:
            # 收集所有账号
            accounts_to_save = []
            for row in self.accounts_layout.children:
                if isinstance(row, AccountRow):
                    acc = row.get_account()
                    if acc['username']:  # 只要有账号就保存，密码可以为空
                        accounts_to_save.append(acc)
            
            # 保存到文件
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_to_save, f, ensure_ascii=False, indent=2)
            
            self.show_result(f'✅ 已保存 {len(accounts_to_save)} 个账号')
            print(f"账号已保存到: {self.accounts_file}")
            
        except Exception as e:
            self.show_result(f'❌ 保存失败: {e}')
            print(f"保存失败: {e}")
    
    def add_account(self, instance=None, username='', password=''):
        """添加新的账号行"""
        row = AccountRow(username=username, password=password)
        row.del_btn.bind(on_press=lambda x: self.remove_account(row))
        self.accounts_layout.add_widget(row)
    
    def remove_account(self, row):
        """删除账号行"""
        self.accounts_layout.remove_widget(row)
        # 自动保存
        self.save_accounts()
    
    def start_sign(self, instance):
        """开始签到"""
        # 先保存当前账号
        self.save_accounts()
        
        # 禁用按钮
        self.sign_btn.disabled = True
        self.sign_btn.text = '签到中...'
        
        # 清空结果
        self.result_layout.clear_widgets()
        
        # 收集要签到的账号
        accounts_to_sign = []
        for row in self.accounts_layout.children:
            if isinstance(row, AccountRow):
                acc = row.get_account()
                if acc['username'] and acc['password']:
                    accounts_to_sign.append((acc['username'], acc['password']))
        
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
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if '✅' in text:
            color = COLORS['success']
        elif '❌' in text:
            color = COLORS['error']
        elif 'ℹ️' in text:
            color = [1, 1, 0, 1]  # 黄色
        else:
            color = COLORS['text']
        
        label = StyledLabel(
            text=f'[{timestamp}] {text}',
            size_hint_y=None,
            height=dp(25),
            color=color,
            halign='left',
            valign='middle',
            text_size=(Window.width - 40, dp(25))
        )
        self.result_layout.add_widget(label)


if __name__ == '__main__':
    SignApp().run()
