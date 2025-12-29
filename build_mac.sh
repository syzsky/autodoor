#!/bin/bash

echo "开始打包 AutoDoor OCR 识别系统（macOS版本）..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：Python 3未安装或未添加到环境变量"
    exit 1
fi

# 检查pip是否可用
if ! command -v pip3 &> /dev/null; then
    echo "错误：pip3不可用"
    exit 1
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
    pip3 install --upgrade pip
fi

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt pyinstaller
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
echo "请将整个dist/autodoor目录复制到目标机器上运行"

echo
echo "按任意键继续..."
read -n 1 -s
