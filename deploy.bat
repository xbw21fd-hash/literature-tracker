@echo off
REM 文献追踪系统 V5.1 快速部署脚本 (Windows)
REM 使用方法: deploy.bat [github|vercel|netlify]

setlocal enabledelayedexpansion

echo.
echo ========================================
echo 🚀 文献追踪系统 V5.1 部署脚本
echo ========================================
echo.

REM 获取部署方式参数
set DEPLOY_METHOD=%1
if "%DEPLOY_METHOD%"=="" set DEPLOY_METHOD=github

echo 部署方式: %DEPLOY_METHOD%
echo.

REM 检查必需文件
echo [INFO] 检查必需文件...
set FILES_OK=1

if not exist "docs\index.html" (
    echo [ERROR] docs\index.html 不存在
    set FILES_OK=0
)
if not exist "docs\app.js" (
    echo [ERROR] docs\app.js 不存在
    set FILES_OK=0
)
if not exist "docs\style.css" (
    echo [ERROR] docs\style.css 不存在
    set FILES_OK=0
)
if not exist "docs\performance-optimization.js" (
    echo [ERROR] docs\performance-optimization.js 不存在
    set FILES_OK=0
)
if not exist "docs\sw.js" (
    echo [ERROR] docs\sw.js 不存在
    set FILES_OK=0
)
if not exist "docs\manifest.json" (
    echo [ERROR] docs\manifest.json 不存在
    set FILES_OK=0
)

if %FILES_OK%==0 (
    echo.
    echo [ERROR] 缺少必需文件，请检查！
    exit /b 1
)

echo [SUCCESS] 所有必需文件检查通过
echo.

REM 根据部署方式执行
if "%DEPLOY_METHOD%"=="github" goto deploy_github
if "%DEPLOY_METHOD%"=="vercel" goto deploy_vercel
if "%DEPLOY_METHOD%"=="netlify" goto deploy_netlify

echo [ERROR] 未知的部署方式: %DEPLOY_METHOD%
echo.
echo 使用方法: deploy.bat [github^|vercel^|netlify]
echo.
echo 支持的部署方式:
echo   github  - GitHub Pages (推荐)
echo   vercel  - Vercel
echo   netlify - Netlify
exit /b 1

:deploy_github
echo [INFO] 开始 GitHub Pages 部署...
echo.

REM 检查Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git 未安装，请先安装 Git
    echo 下载地址: https://git-scm.com/download/win
    exit /b 1
)

REM 检查是否是Git仓库
if not exist ".git" (
    echo [WARNING] 当前目录不是Git仓库，正在初始化...
    git init
    echo [SUCCESS] Git仓库初始化完成
)

REM 添加文件
echo [INFO] 添加文件到Git...
git add .

REM 提交
echo [INFO] 提交更改...
git commit -m "V5.1 性能优化完成，部署上线"
if %errorlevel% neq 0 (
    echo [WARNING] 没有新的更改需要提交
)

REM 检查远程仓库
git remote | findstr "origin" >nul
if %errorlevel% neq 0 (
    echo [WARNING] 未配置远程仓库
    echo.
    echo 请手动添加远程仓库：
    echo   git remote add origin https://github.com/YOUR_USERNAME/literature-tracker.git
    echo   git push -u origin main
    echo.
    echo 然后在GitHub仓库设置中：
    echo   1. 进入 Settings -^> Pages
    echo   2. Source 选择 main 分支
    echo   3. Folder 选择 /docs
    echo   4. 点击 Save
    goto end
)

REM 推送
echo [INFO] 推送到GitHub...
git push origin main
if %errorlevel% neq 0 (
    git push origin master
)

echo.
echo [SUCCESS] 部署完成！
echo.
echo 请在GitHub仓库设置中配置GitHub Pages：
echo   1. 进入 Settings -^> Pages
echo   2. Source 选择 main 分支
echo   3. Folder 选择 /docs
echo   4. 点击 Save
echo.
echo 几分钟后，您的网站将在以下地址可用：
echo   https://YOUR_USERNAME.github.io/literature-tracker/
goto end

:deploy_vercel
echo [INFO] 开始 Vercel 部署...
echo.

REM 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js
    echo 下载地址: https://nodejs.org/
    exit /b 1
)

REM 检查Vercel CLI
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Vercel CLI 未安装
    echo [INFO] 正在安装 Vercel CLI...
    npm install -g vercel
)

REM 创建vercel.json配置
if not exist "vercel.json" (
    echo [INFO] 创建 vercel.json 配置...
    (
        echo {
        echo   "version": 2,
        echo   "public": true,
        echo   "github": {
        echo     "silent": true
        echo   },
        echo   "routes": [
        echo     {
        echo       "src": "/sw.js",
        echo       "headers": {
        echo         "cache-control": "public, max-age=0, must-revalidate",
        echo         "service-worker-allowed": "/"
        echo       }
        echo     },
        echo     {
        echo       "src": "/(.*)",
        echo       "headers": {
        echo         "cache-control": "public, max-age=31536000, immutable"
        echo       }
        echo     }
        echo   ]
        echo }
    ) > vercel.json
    echo [SUCCESS] vercel.json 创建完成
)

REM 部署
echo [INFO] 开始部署到 Vercel...
cd docs
vercel --prod
cd ..

echo.
echo [SUCCESS] 部署完成！
goto end

:deploy_netlify
echo [INFO] 开始 Netlify 部署...
echo.

REM 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js
    echo 下载地址: https://nodejs.org/
    exit /b 1
)

REM 检查Netlify CLI
where netlify >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Netlify CLI 未安装
    echo [INFO] 正在安装 Netlify CLI...
    npm install -g netlify-cli
)

REM 创建netlify.toml配置
if not exist "netlify.toml" (
    echo [INFO] 创建 netlify.toml 配置...
    (
        echo [build]
        echo   publish = "docs"
        echo.
        echo [[headers]]
        echo   for = "/sw.js"
        echo   [headers.values]
        echo     Cache-Control = "public, max-age=0, must-revalidate"
        echo     Service-Worker-Allowed = "/"
        echo.
        echo [[headers]]
        echo   for = "/*"
        echo   [headers.values]
        echo     X-Frame-Options = "DENY"
        echo     X-XSS-Protection = "1; mode=block"
        echo     X-Content-Type-Options = "nosniff"
    ) > netlify.toml
    echo [SUCCESS] netlify.toml 创建完成
)

REM 部署
echo [INFO] 开始部署到 Netlify...
netlify deploy --prod --dir=docs

echo.
echo [SUCCESS] 部署完成！
goto end

:end
echo.
echo ========================================
echo 🎉 部署流程完成！
echo ========================================
echo.
echo [INFO] 下一步：
echo   1. 访问您的网站验证部署
echo   2. 检查 PWA 功能是否正常
echo   3. 运行 Lighthouse 测试
echo   4. 查看 DEPLOYMENT_GUIDE.md 了解更多
echo.
pause
