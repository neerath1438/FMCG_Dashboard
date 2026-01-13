@echo off
REM Final Git Cleanup - Remove files with secrets from history
REM Since files are already deleted locally, just clean history

echo ========================================
echo Final Git History Cleanup
echo ========================================
echo.

echo Step 1: Removing fix_env_draft.py from Git history...
git filter-repo --path fix_env_draft.py --invert-paths --force
echo   ✓ Done

echo.
echo Step 2: Removing verify_azure_claude.py from Git history...
git filter-repo --path verify_azure_claude.py --invert-paths --force
echo   ✓ Done

echo.
echo Step 3: Removing verify_azure_gpt5.py from Git history...
git filter-repo --path verify_azure_gpt5.py --invert-paths --force
echo   ✓ Done

echo.
echo Step 4: Re-adding remote origin...
git remote add origin https://github.com/neerath1438/FMCG_Dashboard.git
echo   ✓ Remote origin re-added

echo.
echo Step 5: Committing current state...
git add -A
git commit -m "chore: remove files with hardcoded secrets" --allow-empty
echo   ✓ Committed

echo.
echo Step 6: Force pushing to GitHub...
echo This will overwrite the remote repository!
pause
git push origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS! Repository is now clean!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ Push failed. Check the error above.
    echo ========================================
)

echo.
pause
