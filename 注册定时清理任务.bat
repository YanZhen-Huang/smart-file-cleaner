@echo off
chcp 65001 >nul
REM ============================================================
REM 智能文档清理器 - 定时任务一键注册脚本（Windows 任务计划）
REM 用法: 右键"以管理员身份运行" 本脚本
REM 会注册一个每日 02:00 的自动清理任务
REM ============================================================

setlocal
set PROJECT_DIR=%~dp0
set TASK_NAME=SmartFileCleaner

echo ============================================
echo  智能文档清理器 - 定时清理任务注册
echo ============================================
echo.

REM 检测 python 命令
set PY_CMD=python
where python >nul 2>nul
if errorlevel 1 (
    set PY_CMD=py
    where py >nul 2>nul
    if errorlevel 1 (
        echo [错误] 未找到 Python，请先安装 Python 并加入 PATH
        pause
        exit /b 1
    )
)

echo 使用 Python: %PY_CMD%
echo 项目目录:   %PROJECT_DIR%

REM 组装完整命令：切换到项目目录后运行无人值守清理
set RUN_CMD=cmd /c "cd /d "%PROJECT_DIR%" && %PY_CMD% main.py --auto"

echo.
echo [1/2] 创建计划任务 %TASK_NAME% （每日 02:00）...
schtasks /Create /F /TN "%TASK_NAME%" ^
    /SC DAILY /ST 02:00 ^
    /TR "%RUN_CMD%" ^
    /RL LIMITED

if errorlevel 1 (
    echo [错误] 创建任务失败，请确认已以管理员身份运行
    pause
    exit /b 1
)

echo.
echo [2/2] 验证任务...
schtasks /Query /TN "%TASK_NAME%"

echo.
echo 完成！任务已注册。
echo   - 每日 02:00 自动清理过期文件
echo   - 清理规则见 src\config\operation-config.json
echo   - 删除前会移入回收站（可恢复）
echo.
echo 如需立即运行一次，执行:
echo   schtasks /Run /TN "%TASK_NAME%"
echo 如需卸载任务，执行:
echo   schtasks /Delete /F /TN "%TASK_NAME%"
echo.
pause
endlocal