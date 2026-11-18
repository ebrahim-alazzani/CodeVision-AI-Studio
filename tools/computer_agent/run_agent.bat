@echo off
chcp 65001 >nul 2>&1
echo.
echo ══════════════════════════════════════════
echo   🤖  CodeVision Computer Agent  v1.0
echo ══════════════════════════════════════════
echo.

cd /d "%~dp0"

REM تحقق من وجود مفتاح API
if "%GEMINI_API_KEY%"=="" (
    echo ⚠️  مفتاح Gemini API غير مُعيَّن!
    echo    احصل على مفتاح مجاني من:
    echo    https://aistudio.google.com/apikey
    echo.
    set /p GEMINI_API_KEY="🔑 أدخل المفتاح: "
)

if "%1"=="" (
    echo 💡 الوضع التفاعلي - أدخل المهام واحدة تلو الأخرى
    echo.
    python agent.py
) else (
    python agent.py %*
)

pause
