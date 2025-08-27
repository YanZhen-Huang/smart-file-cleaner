@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo           智能文档清理器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.6或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 运行Python脚本
python start_cleaner.py

REM 如果脚本执行失败，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo 程序执行出错，错误代码: %errorlevel%
    pause
)