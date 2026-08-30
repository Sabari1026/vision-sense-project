@echo off
echo ===================================================
echo  VisionSense Automated GitHub Repository Push
echo ===================================================
echo.
"C:\Users\sabari kumar\.gemini\antigravity\brain\c697823c-e067-4613-96d5-23026496a6b9\scratch\git\cmd\git.exe" push -u origin main --force
echo.
if %ERRORLEVEL% EQU 0 (
    echo ===================================================
    echo  SUCCESS! Code pushed to GitHub successfully.
    echo  Repository: https://github.com/Sabari1026/vision-sense-project
    echo ===================================================
) else (
    echo ===================================================
    echo  If GitHub login popup appears, complete sign-in.
    echo  If using Personal Access Token, paste your token as password.
    echo ===================================================
)
pause
