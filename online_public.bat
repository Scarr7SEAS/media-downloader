@echo off
title Online Public Link (Pinggy Tunnel)
echo ========================================================
echo   Membuka Akses Publik Online ke Seluruh Dunia...
echo ========================================================
echo.
echo Pastikan start.bat sudah dijalankan terlebih dahulu!
echo Tunggu beberapa detik, tautan HTTPS dan QR Code akan muncul di bawah:
echo.
ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:8000 a.pinggy.io
pause
