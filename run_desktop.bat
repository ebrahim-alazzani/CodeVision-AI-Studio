@echo off
cd /d "%~dp0"
echo ========================================================
echo       CodeVision Studio - استوديو استخراج الشيفرة
echo ========================================================
echo.

set "PYTHONPATH=%~dp0;%PYTHONPATH%"
if exist "C:\Users\ibral\anaconda3\python.exe" (
    set "CODEVISION_PYTHON=C:\Users\ibral\anaconda3\python.exe"
)

echo Starting CodeVision Studio Desktop (WinUI 3)...
dotnet run --project "%~dp0desktop\CodeVision.Desktop.csproj" -p:Platform=x64 --no-restore
if %errorlevel% neq 0 (
    echo.
    echo Application exited with code %errorlevel%.
    pause
)
