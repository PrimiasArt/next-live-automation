@echo off
title HLC Cloud - OBS WebSocket Tunnel
color 0b
echo ========================================================
echo    HLC CLOUD - KET NOI OBS WEBSOCKET VOI STREAMLIT
echo ========================================================
echo.
echo [1] Hay dam bao ban da bat OBS Studio!
echo [2] OBS WebSocket phai dang bat o cong 4455 (Tools -> WebSocket Server Settings)
echo.
echo Dang khoi tao duong truyen Ngrok TCP 4455...
echo ========================================================
echo.
ngrok tcp 4455
pause
