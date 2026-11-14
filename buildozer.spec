[app]
title = Ultimate Calculator
package.name = calculator
package.domain = org.myapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 33
android.ndk = 25b
android.minapi = 21
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
