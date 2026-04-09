#!/usr/bin/env python3
"""
GitHub Actions 配置检查和测试
"""

import os
import sys
import yaml
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOWS_DIR = os.path.join(BASE_DIR, ".github", "workflows")

def check_workflow_syntax(filepath):
    """检查workflow文件语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析YAML - 处理 'on' 关键字问题
        try:
            workflow = yaml.safe_load(content)
        except yaml.YAMLError:
            # 如果解析失败，尝试替换 'on:' 为 '"on":'
            content_fixed = re.sub(r'^on:', '"on":', content, flags=re.MULTILINE)
            workflow = yaml.safe_load(content_fixed)
        
        issues = []
        warnings = []
        
        # 检查必需字段
        if 'name' not in workflow:
            issues.append("缺少 'name' 字段")
        
        # 处理 'on' 字段（可能是True/False的字面量）
        on_field = workflow.get('on') or workflow.get(True)
        if not on_field:
            issues.append("缺少触发器定义")
        
        if 'jobs' not in workflow:
            issues.append("缺少 'jobs' 定义")
        
        # 检查每个job
        for job_name, job_def in workflow.get('jobs', {}).items():
            if 'runs-on' not in job_def:
                issues.append(f"Job '{job_name}' 缺少 'runs-on'")
            
            if 'steps' not in job_def:
                issues.append(f"Job '{job_name}' 缺少 'steps'")
            else:
                for i, step in enumerate(job_def['steps']):
                    if 'uses' not in step and 'run' not in step:
                        issues.append(f"Job '{job_name}' Step {i+1} 缺少 'uses' 或 'run'")
        
        return issues, warnings
    except yaml.YAMLError as e:
        return [f"YAML解析错误: {e}"], []
    except Exception as e:
        return [f"检查失败: {e}"], []

def check_python_syntax(filepath):
    """检查Python文件语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        import ast
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"检查失败: {e}"

def check_duplicate_imports(filepath):
    """检查重复导入（仅在模块级别）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到模块级别的导入语句（不在函数/类内部的）
        lines = content.split('\n')
        imports = []
        in_function = False
        in_class = False
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # 检测缩进级别变化
            if stripped and not stripped.startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent == 0:
                    in_function = False
                    in_class = False
            
            # 检测函数/类定义
            if stripped.startswith('def ') or stripped.startswith('async def '):
                in_function = True
                continue
            if stripped.startswith('class '):
                in_class = True
                continue
            
            # 只在模块级别检查导入
            if not in_function and not in_class:
                import_pattern = r'^(?:from\s+(\S+)\s+import\s+(\S+)|import\s+(\S+))'
                match = re.match(import_pattern, stripped)
                if match:
                    if match.group(1) and match.group(2):
                        imports.append(f"from {match.group(1)} import {match.group(2)}")
                    elif match.group(3):
                        imports.append(f"import {match.group(3)}")
        
        # 检查重复
        seen = set()
        duplicates = []
        for imp in imports:
            if imp in seen:
                duplicates.append(imp)
            seen.add(imp)
        
        return duplicates
    except Exception as e:
        return [f"检查失败: {e}"]

def main():
    print("=" * 60)
    print("GitHub Actions 配置检查和测试")
    print("=" * 60)
    
    # 1. 检查所有workflow文件
    print("\n📋 检查 Workflow 文件...")
    if os.path.exists(WORKFLOWS_DIR):
        for filename in os.listdir(WORKFLOWS_DIR):
            if filename.endswith(('.yml', '.yaml')):
                filepath = os.path.join(WORKFLOWS_DIR, filename)
                issues, warnings = check_workflow_syntax(filepath)
                
                if issues:
                    print(f"❌ {filename}:")
                    for issue in issues:
                        print(f"   - {issue}")
                elif warnings:
                    print(f"⚠️  {filename}:")
                    for warning in warnings:
                        print(f"   - {warning}")
                else:
                    print(f"✅ {filename}")
    else:
        print("⚠️  未找到 workflows 目录")
    
    # 2. 检查关键Python文件语法
    print("\n🐍 检查 Python 文件语法...")
    key_files = [
        'ai_summarizer.py',
        'generate_daily_pages.py',
        'run_optimized_sync.py',
        'weekly_summary.py',
        'rss_fetcher.py',
    ]
    
    for filename in key_files:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            ok, error = check_python_syntax(filepath)
            if ok:
                print(f"✅ {filename}")
            else:
                print(f"❌ {filename}: {error}")
        else:
            print(f"⚠️  {filename} 不存在")
    
    # 3. 检查重复导入
    print("\n📦 检查重复导入...")
    for filename in key_files:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            duplicates = check_duplicate_imports(filepath)
            if duplicates and not isinstance(duplicates[0], str) or (duplicates and not duplicates[0].startswith("检查失败")):
                if duplicates:
                    print(f"⚠️  {filename} 有重复导入:")
                    for dup in duplicates:
                        print(f"   - {dup}")
                else:
                    print(f"✅ {filename}")
            elif duplicates and duplicates[0].startswith("检查失败"):
                print(f"❌ {filename}: {duplicates[0]}")
            else:
                print(f"✅ {filename}")
    
    # 4. 测试导入关键模块
    print("\n📥 测试模块导入...")
    test_modules = [
        'ai_summarizer',
        'generate_daily_pages',
        'run_optimized_sync',
        'weekly_summary',
    ]
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
