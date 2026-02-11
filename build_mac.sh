#!/bin/bash

echo "开始打包 AutoDoor OCR 识别系统（macOS版本）..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：Python 3未安装或未添加到环境变量"
    exit 1
fi

# 检查pip是否可用，优先使用pip3，如果不可用则尝试使用pip
PIP_CMD="pip3"
if ! command -v $PIP_CMD &> /dev/null; then
    PIP_CMD="pip"
    if ! command -v $PIP_CMD &> /dev/null; then
        echo "错误：pip不可用"
        exit 1
    fi
fi

# 创建虚拟环境（可选）
echo "创建虚拟环境..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "警告：创建虚拟环境失败，将使用当前Python环境"
else
    echo "激活虚拟环境..."
    source venv/bin/activate
    echo "更新pip..."
    $PIP_CMD install --upgrade pip
fi

# 安装依赖
echo "安装依赖..."
$PIP_CMD install -r requirements.txt pyinstaller
if [ $? -ne 0 ]; then
    echo "错误：安装依赖失败"
    exit 1
fi

# 使用PyInstaller打包
echo "使用PyInstaller打包..."
pyinstaller autodoor.spec --noconfirm
if [ $? -ne 0 ]; then
    echo "错误：打包失败"
    exit 1
fi

echo
echo "打包成功！"
echo "可执行文件位置：dist/autodoor/autodoor"
echo "应用程序包位置：dist/AutoDoor.app"
echo "请将AutoDoor.app复制到目标机器上运行"
echo "注意：首次运行时，macOS可能会显示安全警告，需要在系统偏好设置中允许运行"

echo
echo "按任意键继续..."
read -n 1 -s
