# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 获取项目根目录 - 修复PyInstaller执行时__file__未定义的问题
import os
import sys
project_root = os.path.abspath('.')

# 收集tesseract目录下的必要文件（排除训练工具和文档）
tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')
if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        # 排除训练工具（.exe文件，除了tesseract.exe）和文档
        for file in files:
            if file.endswith('.exe') and file != 'tesseract.exe':
                continue
            # 排除HTML文档
            if file.endswith('.html'):
                continue
            # 排除不必要的配置文件
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            tesseract_files.append((file_path, dest_dir))

# 配置文件
data_files = [
    (os.path.join(project_root, 'autodoor_config.json'), '.'),
] + tesseract_files

a = Analysis(
    ['autodoor.py'],
    pathex=[project_root],
    binaries=[],
    datas=data_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={
        'cv2': {
            'excludes': ['opencv_videoio_ffmpeg*', 'opencv_ffmpeg*']
        }
    },
    runtime_hooks=[],
    excludes=[
        # 大型深度学习框架
        'torch', 'tensorflow', 'keras', 'scipy', 'pandas', 'matplotlib',
        'sklearn', 'xgboost', 'lightgbm', 'catboost', 'seaborn',
        'statsmodels', 'plotly', 'bokeh', 'networkx', 'nltk',
        'spacy', 'transformers', 'torchvision', 'torchaudio', 'onnx',
        'onnxruntime', 'jax', 'jaxlib', 'timm', 'diffusers', 'peft',
        'gradio', 'streamlit', 'dash',
        
        # Web框架和网络库
        'flask', 'django', 'fastapi', 'uvicorn', 'gunicorn',
        'requests', 'urllib3', 'beautifulsoup4', 'selenium', 'webdriver_manager',
        
        # GUI库
        'pyqt5', 'pyside6', 'wxpython', 'tkinterdnd2',
        
        # PIL扩展
        'pillow_heif', 'PIL._imagingtk', 'PIL._tkinter_finder', 'PIL.ImageQt',
        
        # OpenCV不必要的组件
        'cv2.data', 'cv2.gapi', 'cv2.misc', 'cv2.typing',
        'cv2.aruco', 'cv2.bgsegm', 'cv2.bioinspired', 'cv2.calib3d',
        'cv2.datasets', 'cv2.dnn', 'cv2.dnn_objdetect', 'cv2.dnn_superres',
        'cv2.dpm', 'cv2.face', 'cv2.freetype', 'cv2.fuzzy', 'cv2.hfs',
        'cv2.img_hash', 'cv2.line_descriptor', 'cv2.mcc', 'cv2.optflow',
        'cv2.phase_unwrapping', 'cv2.plot', 'cv2.quality', 'cv2.rapid',
        'cv2.reg', 'cv2.rgbd', 'cv2.saliency', 'cv2.shape', 'cv2.stitching',
        'cv2.superres', 'cv2.surface_matching', 'cv2.text', 'cv2.tracking',
        'cv2.video', 'cv2.videoio', 'cv2.videostab', 'cv2.xfeatures2d',
        'cv2.ximgproc', 'cv2.xobjdetect', 'cv2.xphoto',
        
        # NumPy扩展
        'numpy.testing', 'numpy.f2py', 'numpy.distutils',
        
        # 其他不必要的库
        'pkg_resources',
        'pycparser', 'cffi', 'six',
        'platformdirs', 'pyparsing', 'colorama', 'chardet',
        'idna', 'certifi', 'charset_normalizer'
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
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='',  # 如果有图标文件，可以在这里设置
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='autodoor',
)
