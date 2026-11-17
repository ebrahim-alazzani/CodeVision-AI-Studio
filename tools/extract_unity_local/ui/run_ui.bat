@echo off
cd /d "%~dp0.."
py -m streamlit run ui\streamlit_app.py
pause
