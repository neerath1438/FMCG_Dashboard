@echo off
REM Git Cleanup Script for Windows
REM This script removes sensitive files from Git tracking

echo ========================================
echo Git Security Cleanup Script
echo ========================================
echo.

echo Step 1: Removing .env files from Git cache...
git rm --cached .env 2>nul
if %errorlevel% equ 0 (
    echo   ✓ Removed .env from Git cache
) else (
    echo   ℹ .env not in Git cache or already removed
)

git rm --cached backend\.env 2>nul
if %errorlevel% equ 0 (
    echo   ✓ Removed backend\.env from Git cache
) else (
    echo   ℹ backend\.env not in Git cache or already removed
)

echo.
echo Step 2: Adding updated files to Git...
git add .gitignore
git add fix_env_draft.py
git add verify_azure_claude.py
git add verify_azure_gpt5.py

echo.
echo Step 3: Committing changes...
git commit -m "chore: remove sensitive files and API keys from git tracking"

echo.
echo Step 4: Attempting to push to GitHub...
git push origin main

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo If the push was blocked due to secrets in history, you'll need to:
echo 1. Install git-filter-repo: pip install git-filter-repo
echo 2. Run: git filter-repo --path .env --invert-paths --force
echo 3. Run: git filter-repo --path backend/.env --invert-paths --force
echo 4. Force push: git push origin main --force
echo.
echo WARNING: Force push will rewrite Git history!
echo.
pause
