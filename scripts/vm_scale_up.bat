@echo off
REM Scale Up Google VM for Heavy Backtesting (Windows version)

setlocal enabledelayedexpansion

REM Configuration - UPDATE THESE VALUES
set VM_NAME=aicryptobot
set ZONE=us-central1-a
set PROJECT=intense-base-456414-u5

echo 🚀 VM Scale-Up Script for Heavy Backtesting
echo =============================================
echo VM Name: %VM_NAME%
echo Zone: %ZONE%
echo Project: %PROJECT%
echo.

echo 📋 Checking current VM status...
gcloud compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="value(status)" > temp_status.txt 2>nul
if errorlevel 1 (
    echo ❌ VM '%VM_NAME%' not found in zone '%ZONE%'
    echo Please check your VM name and zone settings.
    del temp_status.txt 2>nul
    pause
    exit /b 1
)

set /p CURRENT_STATUS=<temp_status.txt
del temp_status.txt

gcloud compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="value(machineType)" > temp_machine.txt
set /p MACHINE_TYPE_FULL=<temp_machine.txt
for %%i in (%MACHINE_TYPE_FULL%) do set CURRENT_MACHINE_TYPE=%%~nxi
del temp_machine.txt

echo Current machine type: %CURRENT_MACHINE_TYPE%
echo Current status: %CURRENT_STATUS%

REM Check if already high-performance
echo %CURRENT_MACHINE_TYPE% | findstr /C:"c2-standard-" >nul
if not errorlevel 1 (
    echo ✅ VM is already using high-performance machine type: %CURRENT_MACHINE_TYPE%
    echo No scaling needed.
    pause
    exit /b 0
)

echo.
echo 🎯 Choose scaling option:
echo 1) c2-standard-4 (4 vCPUs, ~$0.20/hour) - Recommended for most backtests
echo 2) c2-standard-8 (8 vCPUs, ~$0.40/hour) - For fastest processing
echo 3) Cancel
echo.
set /p choice=Enter choice (1-3): 

if "%choice%"=="1" (
    set TARGET_MACHINE_TYPE=c2-standard-4
    set COST_PER_HOUR=~$0.20
) else if "%choice%"=="2" (
    set TARGET_MACHINE_TYPE=c2-standard-8
    set COST_PER_HOUR=~$0.40
) else if "%choice%"=="3" (
    echo Cancelled.
    pause
    exit /b 0
) else (
    echo Invalid choice. Exiting.
    pause
    exit /b 1
)

echo.
echo 🔧 Scaling VM to: %TARGET_MACHINE_TYPE% (%COST_PER_HOUR% per hour)
echo.

REM Stop VM if running
if "%CURRENT_STATUS%"=="RUNNING" (
    echo ⏹️ Stopping VM...
    gcloud compute instances stop %VM_NAME% --zone=%ZONE% --project=%PROJECT% --quiet
    
    echo ⏳ Waiting for VM to stop...
    :wait_stop
    gcloud compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="value(status)" > temp_status.txt
    set /p STATUS=<temp_status.txt
    del temp_status.txt
    if not "%STATUS%"=="TERMINATED" (
        echo    Status: %STATUS% (waiting...)
        timeout /t 5 /nobreak >nul
        goto wait_stop
    )
    echo ✅ VM stopped successfully
)

REM Change machine type
echo 🔄 Changing machine type to %TARGET_MACHINE_TYPE%...
gcloud compute instances set-machine-type %VM_NAME% --machine-type=%TARGET_MACHINE_TYPE% --zone=%ZONE% --project=%PROJECT%

echo ✅ Machine type changed successfully

REM Start VM
echo ▶️ Starting VM with new machine type...
gcloud compute instances start %VM_NAME% --zone=%ZONE% --project=%PROJECT% --quiet

echo ⏳ Waiting for VM to start...
:wait_start
gcloud compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="value(status)" > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt
if not "%STATUS%"=="RUNNING" (
    echo    Status: %STATUS% (waiting...)
    timeout /t 5 /nobreak >nul
    goto wait_start
)

REM Get external IP
gcloud compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="value(networkInterfaces[0].accessConfigs[0].natIP)" > temp_ip.txt
set /p EXTERNAL_IP=<temp_ip.txt
del temp_ip.txt

echo.
echo 🎉 VM Successfully Scaled Up!
echo ==============================
echo VM Name: %VM_NAME%
echo New Machine Type: %TARGET_MACHINE_TYPE%
echo Status: RUNNING
echo External IP: %EXTERNAL_IP%
echo Estimated Cost: %COST_PER_HOUR% per hour
echo.
echo 🔗 Connect to your VM:
echo ssh markus@%EXTERNAL_IP%
echo.
echo ⚠️ IMPORTANT: Remember to scale down when done!
echo Run: scripts\vm_scale_down.bat
echo.
echo 💡 Recommended next steps:
echo 1. SSH into your VM
echo 2. cd ~/AI-crypto-bot
echo 3. source venv/bin/activate
echo 4. Run your backtests (they should be 4-8x faster now)
echo 5. Scale down when complete to save costs

pause