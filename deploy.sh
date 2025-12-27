#!/bin/bash

# 文献追踪系统 V5.1 快速部署脚本
# 使用方法: ./deploy.sh [github|vercel|netlify]

set -e

echo "🚀 文献追踪系统 V5.1 部署脚本"
echo "================================"
echo ""

# 检查部署方式参数
DEPLOY_METHOD=${1:-github}

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印函数
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查必需文件
check_files() {
    print_info "检查必需文件..."
    
    required_files=(
        "docs/index.html"
        "docs/app.js"
        "docs/style.css"
        "docs/performance-optimization.js"
        "docs/sw.js"
        "docs/manifest.json"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file 存在"
        else
            print_error "$file 不存在"
            exit 1
        fi
    done
    
    echo ""
}

# GitHub Pages 部署
deploy_github() {
    print_info "开始 GitHub Pages 部署..."
    echo ""
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        print_error "Git 未安装，请先安装 Git"
        exit 1
    fi
    
    # 检查是否是Git仓库
    if [ ! -d ".git" ]; then
        print_warning "当前目录不是Git仓库，正在初始化..."
        git init
        print_success "Git仓库初始化完成"
    fi
    
    # 添加文件
    print_info "添加文件到Git..."
    git add .
    
    # 提交
    print_info "提交更改..."
    git commit -m "V5.1 性能优化完成，部署上线" || print_warning "没有新的更改需要提交"
    
    # 检查远程仓库
    if ! git remote | grep -q "origin"; then
        print_warning "未配置远程仓库"
        echo ""
        echo "请手动添加远程仓库："
        echo "  git remote add origin https://github.com/YOUR_USERNAME/literature-tracker.git"
        echo "  git push -u origin main"
        echo ""
        echo "然后在GitHub仓库设置中："
        echo "  1. 进入 Settings → Pages"
        echo "  2. Source 选择 main 分支"
        echo "  3. Folder 选择 /docs"
        echo "  4. 点击 Save"
        exit 0
    fi
    
    # 推送
    print_info "推送到GitHub..."
    git push origin main || git push origin master
    
    print_success "部署完成！"
    echo ""
    echo "请在GitHub仓库设置中配置GitHub Pages："
    echo "  1. 进入 Settings → Pages"
    echo "  2. Source 选择 main 分支"
    echo "  3. Folder 选择 /docs"
    echo "  4. 点击 Save"
    echo ""
    echo "几分钟后，您的网站将在以下地址可用："
    echo "  https://YOUR_USERNAME.github.io/literature-tracker/"
}

# Vercel 部署
deploy_vercel() {
    print_info "开始 Vercel 部署..."
    echo ""
    
    # 检查Vercel CLI
    if ! command -v vercel &> /dev/null; then
        print_warning "Vercel CLI 未安装"
        print_info "正在安装 Vercel CLI..."
        npm install -g vercel
    fi
    
    # 创建vercel.json配置
    if [ ! -f "vercel.json" ]; then
        print_info "创建 vercel.json 配置..."
        cat > vercel.json << 'EOF'
{
  "version": 2,
  "public": true,
  "github": {
    "silent": true
  },
  "routes": [
    {
      "src": "/sw.js",
      "headers": {
        "cache-control": "public, max-age=0, must-revalidate",
        "service-worker-allowed": "/"
      }
    },
    {
      "src": "/(.*)",
      "headers": {
        "cache-control": "public, max-age=31536000, immutable"
      }
    }
  ]
}
EOF
        print_success "vercel.json 创建完成"
    fi
    
    # 部署
    print_info "开始部署到 Vercel..."
    cd docs && vercel --prod
    
    print_success "部署完成！"
}

# Netlify 部署
deploy_netlify() {
    print_info "开始 Netlify 部署..."
    echo ""
    
    # 检查Netlify CLI
    if ! command -v netlify &> /dev/null; then
        print_warning "Netlify CLI 未安装"
        print_info "正在安装 Netlify CLI..."
        npm install -g netlify-cli
    fi
    
    # 创建netlify.toml配置
    if [ ! -f "netlify.toml" ]; then
        print_info "创建 netlify.toml 配置..."
        cat > netlify.toml << 'EOF'
[build]
  publish = "docs"
  
[[headers]]
  for = "/sw.js"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
    Service-Worker-Allowed = "/"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
EOF
        print_success "netlify.toml 创建完成"
    fi
    
    # 部署
    print_info "开始部署到 Netlify..."
    netlify deploy --prod --dir=docs
    
    print_success "部署完成！"
}

# 主流程
main() {
    echo "部署方式: $DEPLOY_METHOD"
    echo ""
    
    # 检查文件
    check_files
    
    # 根据部署方式执行
    case $DEPLOY_METHOD in
        github)
            deploy_github
            ;;
        vercel)
            deploy_vercel
            ;;
        netlify)
            deploy_netlify
            ;;
        *)
            print_error "未知的部署方式: $DEPLOY_METHOD"
            echo ""
            echo "使用方法: ./deploy.sh [github|vercel|netlify]"
            echo ""
            echo "支持的部署方式:"
            echo "  github  - GitHub Pages (推荐)"
            echo "  vercel  - Vercel"
            echo "  netlify - Netlify"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "🎉 部署流程完成！"
    echo ""
    print_info "下一步："
    echo "  1. 访问您的网站验证部署"
    echo "  2. 检查 PWA 功能是否正常"
    echo "  3. 运行 Lighthouse 测试"
    echo "  4. 查看 DEPLOYMENT_GUIDE.md 了解更多"
}

# 运行主流程
main
