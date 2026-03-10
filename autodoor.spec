# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
project_root = os.path.abspath('.')

tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')

if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            
            if (file == 'tesseract' or file == 'tesseract.exe'):
                tesseract_files.append((file_path, dest_dir))
                continue
            if file.endswith('.exe') and file != 'tesseract.exe':
                continue
            if file.endswith('.html'):
                continue
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            
            tesseract_files.append((file_path, dest_dir))
    print(f"Collected {len(tesseract_files)} tesseract files")

data_files = [
    (os.path.join(project_root, 'voice/alarm.mp3'), 'voice'),
    (os.path.join(project_root, 'voice/temp_reversed.mp3'), 'voice'),
    (os.path.join(project_root, 'icon/autodoor.ico'), 'icon'),
    (os.path.join(project_root, 'icon/autodoor.png'), 'icon'),
] + tesseract_files

binaries = []

a = Analysis(
    ['autodoor.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=data_files,
    hiddenimports=[
        'core',
        'core.config',
        'core.controller',
        'core.events',
        'core.logging',
        'core.platform',
        'core.proxy',
        'core.threading',
        'core.utils',
        
        'ui',
        'ui.background_tab',
        'ui.basic_tab',
        'ui.home',
        'ui.image_tab',
        'ui.number_tab',
        'ui.ocr_tab',
        'ui.script_tab',
        'ui.theme',
        'ui.timed_tab',
        'ui.utils',
        'ui.widgets',
        
        'modules',
        'modules.alarm',
        'modules.background',
        'modules.color',
        'modules.image',
        'modules.input',
        'modules.number',
        'modules.ocr',
        'modules.recorder',
        'modules.script',
        'modules.timed',
        
        'input',
        'input.controller',
        'input.keyboard',
        'input.permissions',
        
        'utils',
        'utils.image',
        'utils.keyboard',
        'utils.region',
        'utils.tesseract',
        'utils.version',
        
        'pygame',
        'pygame.mixer',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'pytesseract',
        'screeninfo',
        'screeninfo.common',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pydub',
        'requests',
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'six',
        'imagehash',
        'cv2',
        
        'win32gui',
        'win32ui',
        'win32con',
        'win32api',
        'win32process',
        'pywintypes',
        'pythoncom',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'tensorflow', 'keras', 'scipy', 'pandas', 'matplotlib',
        'sklearn', 'xgboost', 'lightgbm', 'catboost', 'seaborn',
        'statsmodels', 'plotly', 'bokeh', 'networkx', 'nltk',
        'spacy', 'transformers', 'torchvision', 'torchaudio', 'onnx',
        'onnxruntime', 'jax', 'jaxlib', 'timm', 'diffusers', 'peft',
        'gradio', 'streamlit', 'dash',
        
        'flask', 'django', 'fastapi', 'uvicorn', 'gunicorn',
        'beautifulsoup4', 'selenium', 'webdriver_manager',
        
        'pyqt5', 'pyside6', 'wxpython', 'tkinterdnd2',
        
        'pillow_heif', 'PIL._tkinter_finder', 'PIL.ImageQt',
        
        'numpy.testing', 'numpy.f2py', 'numpy.distutils',
        
        'pkg_resources',
        'pycparser', 'cffi',
        'platformdirs', 'pyparsing', 'colorama', 'chardet'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='autodoor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon', 'autodoor.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='autodoor',
)
