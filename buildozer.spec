[app]

# 应用名称
title = 美墨签到工具

# 包名
package.name = meimodu
package.domain = com.meimodu

# 源代码目录
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf

# 版本号
version = 1.0.0

# 依赖
requirements = python3,kivy,requests

# Android 配置
# 只需要网络权限
android.permissions = android.permission.INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# 屏幕方向
orientation = portrait

# 不需要全屏
fullscreen = 0

# Android 特定
android.accept_sdk_license = True
android.encoding = utf-8
android.locale = zh_CN

# 生成 APK
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
