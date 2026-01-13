@echo off
REM Simple Git Push Script - Just commit current state and use git-filter-repo

echo ========================================
echo Git Cleanup and Push
echo ========================================
echo.

echo Step 1: Staging all changes...
git add -A
echo   ✓ Done

echo.
echo Step 2: Committing changes...
git commit -m "chore: remove files with secrets and fix Docker build" --allow-empty
echo   ✓ Done

echo.
echo Step 3: Removing files with secrets from Git history...
echo This will take a moment...
git filter-repo --path fix_env_draft.py --invert-paths --force
git filter-repo --path verify_azure_claude.py --invert-paths --force
git filter-repo --path verify_azure_gpt5.py --invert-paths --force
echo   ✓ History cleaned

echo.
echo Step 4: Re-adding remote...
git remote add origin https://github.com/neerath1438/FMCG_Dashboard.git
echo   ✓ Remote added

echo.
echo Step 5: Force pushing to GitHub...
echo WARNING: This will rewrite Git history!
pause
git push origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS! Repository is clean!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ Push failed. See error above.
    echo ========================================
)

echo.
pause
