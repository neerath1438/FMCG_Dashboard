@echo off
REM Complete Git History Cleanup - Remove all files with secrets
REM This removes the Python files from history, then re-adds the cleaned versions

echo ========================================
echo Complete Git History Cleanup
echo ========================================
echo.
echo This will remove files with hardcoded secrets from Git history
echo and re-add the cleaned versions.
echo.
pause

echo.
echo Step 1: Removing fix_env_draft.py from Git history...
git filter-repo --path fix_env_draft.py --invert-paths --force
if %errorlevel% equ 0 (
    echo   ✓ Removed fix_env_draft.py from Git history
) else (
    echo   ℹ File not found in history or already removed
)

echo.
echo Step 2: Removing verify_azure_claude.py from Git history...
git filter-repo --path verify_azure_claude.py --invert-paths --force
if %errorlevel% equ 0 (
    echo   ✓ Removed verify_azure_claude.py from Git history
) else (
    echo   ℹ File not found in history or already removed
)

echo.
echo Step 3: Removing verify_azure_gpt5.py from Git history...
git filter-repo --path verify_azure_gpt5.py --invert-paths --force
if %errorlevel% equ 0 (
    echo   ✓ Removed verify_azure_gpt5.py from Git history
) else (
    echo   ℹ File not found in history or already removed
)

echo.
echo Step 4: Re-adding remote origin...
git remote add origin https://github.com/neerath1438/FMCG_Dashboard.git
echo   ✓ Remote origin re-added

echo.
echo Step 5: Adding cleaned files back...
git add fix_env_draft.py verify_azure_claude.py verify_azure_gpt5.py
git commit -m "chore: re-add Python files with secrets removed"
echo   ✓ Cleaned files added

echo.
echo Step 6: Force pushing to GitHub...
echo This will overwrite the remote repository!
pause
git push origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS! Push completed!
    echo ========================================
    echo.
    echo Your repository is now clean of secrets!
) else (
    echo.
    echo ========================================
    echo ✗ Push failed. Check the error above.
    echo ========================================
)

echo.
pause
