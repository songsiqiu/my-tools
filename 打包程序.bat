@echo off
chcp 65001
echo 正在打包程序，请稍候...
echo.

echo 方法1: 使用build_exe.py
python build_exe.py
if %errorlevel% neq 0 (
    echo.
    echo 方法1失败，尝试方法2...
    echo.
    python 简单打包.py
)

echo.
echo 打包完成，请检查dist文件夹
pause
