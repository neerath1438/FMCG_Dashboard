# Git Cleanup Commands

Since Git is not recognized in PowerShell, please run these commands in **Git Bash** or add Git to your PATH.

## Step 1: Remove files from Git cache (but keep them locally)

```bash
git rm --cached .env
git rm --cached backend/.env
git rm --cached fix_env_draft.py
git rm --cached verify_azure_claude.py
git rm --cached verify_azure_gpt5.py
```

## Step 2: Commit the changes

```bash
git add .gitignore
git add fix_env_draft.py
git add verify_azure_claude.py
git add verify_azure_gpt5.py
git commit -m "chore: remove sensitive files and API keys from git tracking"
```

## Step 3: Push to GitHub

```bash
git push origin main
```

## Alternative: If you still get errors about secrets in history

If GitHub still blocks the push because secrets exist in previous commits, you'll need to clean the Git history:

```bash
# Install git-filter-repo (if not already installed)
# pip install git-filter-repo

# Remove .env files from entire history
git filter-repo --path .env --invert-paths --force
git filter-repo --path backend/.env --invert-paths --force

# Force push (WARNING: This rewrites history)
git push origin main --force
```

## Notes:
- The hardcoded API keys have been removed from the Python files
- `.gitignore` is now configured to prevent future commits of sensitive files
- Make sure to keep your `.env` files locally - they won't be deleted, just removed from Git tracking
