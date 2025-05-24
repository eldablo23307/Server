[app]
title = File Manager
package.name = filemanager
package.domain = org.mottu.filemanager

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy,requests

orientation = portrait
fullscreen = 0

# Android settings
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.archs = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Release settings
android.release_artifact = apk
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 0