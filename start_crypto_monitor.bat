@echo off
title Crypto Market Monitor
color 0A
mode con: cols=80 lines=25
cls

echo.
echo.
echo    ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗     ██╗     ██╗██╗   ██╗███████╗
echo   ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██║     ██║██║   ██║██╔════╝
echo   ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ██║     ██║██║   ██║█████╗  
echo   ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██║     ██║╚██╗ ██╔╝██╔══╝  
echo   ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ███████╗██║ ╚████╔╝ ███████╗
echo    ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝     ╚══════╝╚═╝  ╚═══╝  ╚══════╝
echo.
echo                              Market Monitor v1.0
echo                        Real-time Cryptocurrency Tracking
echo.
echo                     [BTC] [ETH] [BNB] [SOL] [ADA] and more...
echo.
echo.

:: Animação de loading
set load=0
:loading
set /a load+=1
set "loading="
for /l %%i in (1,1,%load%) do set "loading=!loading!█"
echo     Initializing... !loading!
if %load% leq 20 (
    timeout /t 1 >nul
    cls
    echo.
    echo.
    echo    ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗     ██╗     ██╗██╗   ██╗███████╗
    echo   ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██║     ██║██║   ██║██╔════╝
    echo   ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ██║     ██║██║   ██║█████╗  
    echo   ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██║     ██║╚██╗ ██╔╝██╔══╝  
    echo   ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ███████╗██║ ╚████╔╝ ███████╗
    echo    ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝     ╚══════╝╚═╝  ╚═══╝  ╚══════╝
    echo.
    echo                              Market Monitor v1.0
    echo                        Real-time Cryptocurrency Tracking
    echo.
    echo                     [BTC] [ETH] [BNB] [SOL] [ADA] and more...
    echo.
    echo.
    goto loading
)

cls
echo Iniciando o monitor de criptomoedas...
timeout /t 1 >nul

python crypto_monitor.py

if errorlevel 1 (
    color 0C
    echo.
    echo Programa finalizado com erro.
    echo Verifique se todas as dependências estão instaladas:
    echo - python-binance
    echo - pandas
    echo - numpy
    echo - matplotlib
    echo.
    echo Para instalar, use: pip install python-binance pandas numpy matplotlib
    pause
) else (
    color 0A
    echo.
    echo Programa finalizado com sucesso.
    pause
)