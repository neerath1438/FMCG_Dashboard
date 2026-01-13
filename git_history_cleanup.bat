@echo off
REM Advanced Git History Cleanup Script
REM This script removes sensitive files from entire Git history

echo ========================================
echo Git History Cleanup Script
echo ========================================
echo.
echo WARNING: This will rewrite Git history!
echo Make sure you have a backup if needed.
echo.
pause

echo.
echo Step 1: Installing git-filter-repo...
pip install git-filter-repo
if %errorlevel% neq 0 (
    echo   ✗ Failed to install git-filter-repo
    echo   Please install Python and pip first
    pause
    exit /b 1
)
echo   ✓ git-filter-repo installed

echo.
echo Step 2: Removing .env from entire Git history...
git filter-repo --path .env --invert-paths --force
if %errorlevel% equ 0 (
    echo   ✓ Removed .env from Git history
) else (
    echo   ℹ .env not found in history or already removed
)

echo.
echo Step 3: Removing backend/.env from entire Git history...
git filter-repo --path backend/.env --invert-paths --force
if %errorlevel% equ 0 (
    echo   ✓ Removed backend/.env from Git history
) else (
    echo   ℹ backend/.env not found in history or already removed
)

echo.
echo Step 4: Re-adding remote origin...
REM git-filter-repo removes the remote, so we need to add it back
git remote add origin https://github.com/neerath1438/FMCG_Dashboard.git
echo   ✓ Remote origin re-added

echo.
echo Step 5: Force pushing to GitHub...
echo This will overwrite the remote repository!
pause
git push origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS! Push completed!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ Push failed. Check the error above.
    echo ========================================
)

echo.
pause
