@echo off
echo ==========================================
echo   Pushing cortexchain v1.0.0 to GitHub
echo   PRODUCTION RELEASE
echo ==========================================
echo.

cd /d "%~dp0"

:: Initialize git if not already done
if not exist ".git" (
    echo [1/6] Initializing git repository...
    git init
    git branch -M main
) else (
    echo [1/6] Git repo already exists.
)

:: Add remote if not set
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [2/6] Adding remote origin...
    git remote add origin https://github.com/prince-network-lilly/langchain_cortextai.git
) else (
    echo [2/6] Remote already configured.
)

:: Stage all files
echo [3/6] Staging all files...
git add .

:: Show what's being committed
echo.
echo --- Files to be committed ---
git status --short
echo ---
echo.

:: Commit
echo [4/6] Creating commit...
git commit -m "feat: cortexchain v1.0.0 - production release (connection pool, profiling, full docs)"

:: Push
echo [5/6] Pushing to GitHub...
git push -u origin main

:: Tag
echo [6/6] Creating version tag...
git tag v1.0.0
git push origin v1.0.0

echo.
echo ==========================================
echo   PRODUCTION RELEASE COMPLETE!
echo.
echo   Repository:
echo   https://github.com/prince-network-lilly/langchain_cortextai
echo.
echo   Install:
echo   pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git
echo.
echo   Install specific version:
echo   pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git@v1.0.0
echo.
echo   Install with dev tools:
echo   pip install "cortexchain[dev] @ git+https://github.com/prince-network-lilly/langchain_cortextai.git"
echo ==========================================
pause
