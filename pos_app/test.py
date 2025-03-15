import os
import sys
import pkgutil
import importlib


def generate_spec_data():
    """Генерирует данные для MyApp.spec файла."""

    # Определение базового пути проекта
    project_path = os.path.abspath(os.path.dirname(__file__))

    # Сбор основных данных о проекте
    app_name = "MyApp"
    main_script = "main.py"

    # Поиск всех kivy модулей для hiddenimports
    kivy_modules = []
    for importer, modname, ispkg in pkgutil.iter_modules():
        if modname.startswith('kivy'):
            kivy_modules.append(modname)

    # Добавление важных модулей Kivy, которые могут не обнаружиться автоматически
    essential_kivy_modules = [
        'kivy.core.window', 'kivy.core.text', 'kivy.core.image',
        'kivy.core.audio', 'kivy.core.video', 'kivy.core.clipboard',
        'kivy.factory', 'kivy.uix.textinput', 'kivy.uix.button',
        'kivy.uix.label', 'kivy.uix.boxlayout', 'kivy.graphics',
        'kivy.graphics.context_instructions', 'kivy.graphics.vertex_instructions',
        'kivy.properties', 'kivy.animation', 'kivy.metrics'
    ]
    for module in essential_kivy_modules:
        if module not in kivy_modules:
            kivy_modules.append(module)

    # Находим все ресурсы в проекте (изображения, звуки, шрифты, kv-файлы и т.д.)
    resources = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.wav', '.mp3', '.ttf', '.kv')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_path)
                dest_path = os.path.dirname(rel_path)
                # Если dest_path пустой, назначаем корневую директорию '.'
                if dest_path == "":
                    dest_path = "."
                resources.append((file_path, dest_path))

    # Проверяем наличие kivy_deps пакетов
    has_sdl2 = False
    has_glew = False
    try:
        import kivy_deps.sdl2
        has_sdl2 = True
    except ImportError:
        print("kivy_deps.sdl2 не найден. Билд может не содержать необходимые SDL2 зависимости.")

    try:
        import kivy_deps.glew
        has_glew = True
    except ImportError:
        print("kivy_deps.glew не найден. Билд может не содержать необходимые GLEW зависимости.")

    # Создаем базовое содержимое spec файла с корректно экранированными путями
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    [{repr(main_script)}],
    pathex=[{repr(project_path)}],
    binaries=[],
    datas={resources},
    hiddenimports={kivy_modules},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name={repr(app_name)},
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    # Добавляем специфическую часть для сборки с kivy_deps, если доступны
    if has_sdl2 or has_glew:
        spec_content += "\n# Импорт Kivy зависимостей\n"
        if has_sdl2:
            spec_content += "from kivy_deps import sdl2\n"
        if has_glew:
            spec_content += "from kivy_deps import glew\n"

        spec_content += "\ncoll = COLLECT(\n    exe,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n"

        if has_sdl2 and has_glew:
            spec_content += "    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],\n"
        elif has_sdl2:
            spec_content += "    *[Tree(p) for p in sdl2.dep_bins],\n"
        elif has_glew:
            spec_content += "    *[Tree(p) for p in glew.dep_bins],\n"

        spec_content += f"""    strip=False,
    upx=True,
    upx_exclude=[],
    name={repr(app_name)},
)"""
    else:
        spec_content += f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name={repr(app_name)},
)"""

    # Записываем spec файл
    with open(f"{app_name}.spec", "w", encoding="utf-8") as spec_file:
        spec_file.write(spec_content)

    print(f"Файл {app_name}.spec успешно создан!")
    print(f"Найдено {len(kivy_modules)} Kivy модулей для hiddenimports")
    print(f"Найдено {len(resources)} ресурсных файлов")
    print("Для сборки билда используйте команду:")
    print(f"pyinstaller {app_name}.spec")

    # Дополнительная информация для пользователя
    print("\nЕсли у вас возникают проблемы со сборкой, попробуйте следующее:")
    print("1. Установите необходимые зависимости:")
    print("   pip install kivy_deps.sdl2 kivy_deps.glew")
    print("2. Для современных версий Kivy может потребоваться другой подход к сборке.")
    print("   Проверьте официальную документацию Kivy 2025 года.")


if __name__ == "__main__":
    # Проверяем, установлен ли PyInstaller
    try:
        import PyInstaller

        print("PyInstaller установлен, версия:", PyInstaller.__version__)
    except ImportError:
        print("ВНИМАНИЕ: PyInstaller не установлен. Установите его с помощью pip install pyinstaller")

    # Проверяем, установлен ли Kivy
    try:
        import kivy

        print("Kivy установлен, версия:", kivy.__version__)
    except ImportError:
        print("ВНИМАНИЕ: Kivy не установлен. Установите его с помощью pip install kivy")

    # Генерируем данные для spec файла
    generate_spec_data()
