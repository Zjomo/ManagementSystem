@echo off
echo ========================================
echo   竞赛信息管理系统 - 启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查虚拟环境...
if not exist "venv\Scripts\python.exe" (
    echo 虚拟环境不存在，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo 创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功！
)

echo [2/3] 安装依赖...
call venv\Scripts\activate.bat
pip install -q -r requirements.txt 2>nul

echo [3/3] 启动服务...
echo.

start /min "CompetitionServer" "venv\Scripts\python.exe" "backend\app.py"
if errorlevel 1 (
    echo 服务启动失败！
    pause
    exit /b 1
)

echo 服务正在启动，请稍候...
timeout /t 3 /nobreak >nul

echo 正在打开浏览器...
start http://localhost:5000

echo.
echo ========================================
echo   系统已启动！
echo   访问地址: http://localhost:5000
echo   停止服务: 关闭后台服务窗口
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause >nul
