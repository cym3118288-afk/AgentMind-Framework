# README.md 文档链接更新指南

执行完 `reorganize_files.bat` 后，需要更新 README.md 中的文档链接。

## 需要更新的链接

### 1. 快速开始部分 (第 14 行附近)
```markdown
# 旧链接
[Quick Start](#quick-start) • [Documentation](docs/) • [Examples](examples/)

# 保持不变（这些链接仍然有效）
```

### 2. 文档部分 (第 236-249 行)

**需要更新的链接：**

```markdown
# 旧链接 → 新链接

### Getting Started
- [Quick Start Guide](docs/getting-started/quickstart.md) → [Quick Start Guide](docs/guides/QUICKSTART.md)
- [Basic Concepts](docs/getting-started/concepts.md) → 保持不变（如果存在）
- [Installation Guide](docs/getting-started/installation.md) → 保持不变（如果存在）

### Core Documentation
- [API Reference](API.md) → [API Reference](docs/api/API.md)
- [Architecture](ARCHITECTURE.md) → [Architecture](docs/api/ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md) → [Troubleshooting](docs/guides/TROUBLESHOOTING.md)
- [FAQ](FAQ.md) → [FAQ](docs/guides/FAQ.md)

### Advanced Topics
- [Advanced Features](ADVANCED_FEATURES.md) → [Advanced Features](docs/guides/ADVANCED_FEATURES.md)
- [Performance](PERFORMANCE.md) → [Performance](docs/guides/PERFORMANCE.md)
- [Scaling](SCALING.md) → [Scaling](docs/guides/SCALING.md)
- [Migration Guide](MIGRATION.md) → [Migration Guide](docs/guides/MIGRATION.md)

### Deployment
- [Deployment Guide](DEPLOYMENT.md) → [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [Docker Guide](DOCKER.md) → [Docker Guide](docs/deployment/DOCKER.md)
- [Production Readiness](WAVE3_PRODUCTION_READINESS.md) → [Production Readiness](docs/deployment/WAVE3_PRODUCTION_READINESS.md)

### Development
- [Developer Tools](DEVELOPER_TOOLS.md) → [Developer Tools](docs/guides/DEVELOPER_TOOLS.md)
- [Contributing](CONTRIBUTING.md) → 保持不变（根目录）
- [Security](SECURITY.md) → 保持不变（根目录）
```

## 自动更新脚本

创建一个 Python 脚本来自动更新链接：

```python
# update_readme_links.py
import re

def update_readme_links():
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义替换规则
    replacements = {
        r'\(API\.md\)': '(docs/api/API.md)',
        r'\(ARCHITECTURE\.md\)': '(docs/api/ARCHITECTURE.md)',
        r'\(TROUBLESHOOTING\.md\)': '(docs/guides/TROUBLESHOOTING.md)',
        r'\(FAQ\.md\)': '(docs/guides/FAQ.md)',
        r'\(QUICKSTART\.md\)': '(docs/guides/QUICKSTART.md)',
        r'\(QUICK_REFERENCE\.md\)': '(docs/guides/QUICK_REFERENCE.md)',
        r'\(ADVANCED_FEATURES\.md\)': '(docs/guides/ADVANCED_FEATURES.md)',
        r'\(PERFORMANCE\.md\)': '(docs/guides/PERFORMANCE.md)',
        r'\(SCALING\.md\)': '(docs/guides/SCALING.md)',
        r'\(MIGRATION\.md\)': '(docs/guides/MIGRATION.md)',
        r'\(DEPLOYMENT\.md\)': '(docs/deployment/DEPLOYMENT.md)',
        r'\(DOCKER\.md\)': '(docs/deployment/DOCKER.md)',
        r'\(DEVELOPER_TOOLS\.md\)': '(docs/guides/DEVELOPER_TOOLS.md)',
        r'\(COMPARISON\.md\)': '(docs/guides/COMPARISON.md)',
        r'\(EXAMPLES\.md\)': '(docs/guides/EXAMPLES.md)',
        r'\(CHAT_README\.md\)': '(docs/guides/CHAT_README.md)',
    }
    
    # 执行替换
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # 写回文件
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ README.md 链接已更新")

if __name__ == '__main__':
    update_readme_links()
```

## 手动更新步骤

如果不想用脚本，可以手动更新：

1. 打开 README.md
2. 使用查找替换功能（Ctrl+H）
3. 逐个替换上述链接
4. 保存文件

## 验证链接

更新后运行以下命令验证所有链接：

```bash
# 检查所有 markdown 文件中的链接
python -c "
import re
import os

def check_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有 markdown 链接
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    
    broken = []
    for text, link in links:
        if link.startswith('http'):
            continue  # 跳过外部链接
        if link.startswith('#'):
            continue  # 跳过锚点
        
        # 检查文件是否存在
        if not os.path.exists(link):
            broken.append((text, link))
    
    return broken

broken = check_links('README.md')
if broken:
    print('❌ 发现损坏的链接：')
    for text, link in broken:
        print(f'  - [{text}]({link})')
else:
    print('✅ 所有链接都有效')
"
```

## 提交更改

```bash
git add README.md
git commit -m "docs: update documentation links after reorganization"
```
