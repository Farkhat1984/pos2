[app]
# Название приложения
title = POS App

# Идентификатор пакета в формате "домен.название"
package.name = posapp
package.domain = com.yourcompany

# Исходный файл, содержащий класс App
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,json,ttf

# Версия приложения
version = 0.1

# Требования для сборки
requirements = python3==3.10.0,\
    kivy==2.3.1,\
    certifi==2025.1.31,\
    charset-normalizer==3.4.1,\
    docutils==0.21.2,\
    filetype==1.2.0,\
    idna==3.10,\
    Kivy-Garden==0.1.5,\
    kivymd==1.2.0,\
    numpy==2.2.3,\
    pillow==11.1.0,\
    Pygments==2.19.1,\
    pyzbar==0.1.9,\
    requests==2.32.3,\
    urllib3==2.3.0

# Тип ориентации экрана (portrait, landscape)
orientation = portrait

# Фуллскрин или нет
fullscreen = 0

# Иконка приложения
icon.filename = %(source.dir)s/assets/logo.png

# Сплэш-экран
presplash.filename = %(source.dir)s/assets/logo.png

# Устанавливаемые разрешения Android
android.permissions = CAMERA,INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android SDK/NDK настройки
android.api = 33
android.minapi = 21
android.ndk = 25

# Цель архитектуры (новый формат)
android.archs = arm64-v8a, armeabi-v7a

# Использовать ли p4a bootstrap
p4a.bootstrap = sdl2

# Gradle зависимость для OpenCV
android.gradle_dependencies = org.opencv:opencv-java:4.5.1

[buildozer]
# Логи Buildozer
log_level = 2

# Директория для билдов
build_dir = ./.buildozer

# Директория приложения (внутри build_dir)
app_dir = ./%(source.dir)s

# Где скачивать p4a / crystax
p4a.source_dir = ./.buildozer/android/platform/python-for-android

# Очистка перед сборкой
# Options: never (default), prebuild, always
build_mode = app