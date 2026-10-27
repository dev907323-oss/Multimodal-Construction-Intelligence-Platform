@echo off
cd /d "%~dp0"
py -m pip install -r requirements-streamlit.txt
py -m streamlit run app.py
pause
