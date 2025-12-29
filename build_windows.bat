@echo off
chcp 65001 >nul

echo 开始打包 AutoDoor OCR 识别系统（Windows版本）...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：Python未安装或未添加到环境变量
    pause
    exit /b 1
)

REM 检查pip是否可用
pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：pip不可用
    pause
    exit /b 1
)

REM 创建虚拟环境（可选）
echo 创建虚拟环境...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo 警告：创建虚拟环境失败，将使用当前Python环境
) else (
    echo 激活虚拟环境...
    call venv\Scripts\activate
    echo 更新pip...
    pip install --upgrade pip
)

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt pyinstaller
if %ERRORLEVEL% neq 0 (
    echo 错误：安装依赖失败
    pause
    exit /b 1
)

REM 使用PyInstaller打包
echo 使用PyInstaller打包...
pyinstaller autodoor.spec --noconfirm
if %ERRORLEVEL% neq 0 (
    echo 错误：打包失败
    pause
    exit /b 1
)

echo.
echo 打包成功！
echo 可执行文件位置：dist\autodoor\autodoor.exe
echo 请将整个dist\autodoor目录复制到目标机器上运行

echo.
pause
