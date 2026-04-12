@echo off
chcp 65001 >nul
title Alpha Signal - 5-Dimension Stock Analysis
echo.
echo  ============================================
echo    ALPHA SIGNAL - FULL STOCK ANALYSIS
echo    Analyzing Xiaomi (1810.HK) across 5 dims
echo    + AI pair stock selection
echo  ============================================
echo.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python full_analysis.py
echo.
echo  Analysis complete! Check the JSON output file.
pause
