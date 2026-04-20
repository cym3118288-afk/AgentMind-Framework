#!/bin/bash
# AgentMind 文件结构优化脚本
# 执行前请确保已提交所有更改

set -e  # 遇到错误立即退出

echo "=== AgentMind 文件结构优化 ==="
echo ""

# 1. 创建目录结构
echo "步骤 1: 创建目录结构..."
mkdir -p docs/guides
mkdir -p docs/api
mkdir -p docs/deployment
mkdir -p docs/archive
mkdir -p examples/tutorials
mkdir -p examples/use_cases
mkdir -p examples/integrations
mkdir -p examples/advanced

# 2. 移动指南类文档到 docs/guides/
echo "步骤 2: 移动指南类文档..."
git mv QUICKSTART.md docs/guides/ 2>/dev/null || true
git mv TROUBLESHOOTING.md docs/guides/ 2>/dev/null || true
git mv QUICK_REFERENCE.md docs/guides/ 2>/dev/null || true
git mv FAQ.md docs/guides/ 2>/dev/null || true
git mv MIGRATION.md docs/guides/ 2>/dev/null || true
git mv CHAT_README.md docs/guides/ 2>/dev/null || true
git mv DEVELOPER_TOOLS.md docs/guides/ 2>/dev/null || true
git mv ADVANCED_FEATURES.md docs/guides/ 2>/dev/null || true
git mv COMPARISON.md docs/guides/ 2>/dev/null || true
git mv SCALING.md docs/guides/ 2>/dev/null || true
git mv PERFORMANCE.md docs/guides/ 2>/dev/null || true
git mv PERFORMANCE_IMPLEMENTATION.md docs/guides/ 2>/dev/null || true

# 3. 移动 API 文档到 docs/api/
echo "步骤 3: 移动 API 文档..."
git mv API.md docs/api/ 2>/dev/null || true
git mv ARCHITECTURE.md docs/api/ 2>/dev/null || true

# 4. 移动部署文档到 docs/deployment/
echo "步骤 4: 移动部署文档..."
git mv DEPLOYMENT.md docs/deployment/ 2>/dev/null || true
git mv DOCKER.md docs/deployment/ 2>/dev/null || true
git mv RELEASING.md docs/deployment/ 2>/dev/null || true
git mv WAVE3_PRODUCTION_READINESS.md docs/deployment/ 2>/dev/null || true

# 5. 移动示例文档到 docs/guides/
echo "步骤 5: 移动示例文档..."
git mv EXAMPLES.md docs/guides/ 2>/dev/null || true
git mv EXAMPLES_INDEX.md docs/guides/ 2>/dev/null || true

# 6. 移动发布说明到 docs/
echo "步骤 6: 移动发布说明..."
git mv RELEASE_NOTES_v0.3.0.md docs/ 2>/dev/null || true
git mv RELEASE_NOTES_v0.4.0.md docs/ 2>/dev/null || true

# 7. 移动贡献者文档到 docs/
echo "步骤 7: 移动贡献者文档..."
git mv CONTRIBUTORS.md docs/ 2>/dev/null || true

# 8. 删除所有临时报告文件
echo "步骤 8: 删除临时报告文件..."
git rm -f *_REPORT.md 2>/dev/null || true
git rm -f *_SUMMARY.md 2>/dev/null || true
git rm -f *_COMPLETE.md 2>/dev/null || true
git rm -f PHASE*.md 2>/dev/null || true
git rm -f WAVE*.md 2>/dev/null || true

# 9. 删除 .agentmind_checkpoints 目录
echo "步骤 9: 删除临时 checkpoints..."
rm -rf .agentmind_checkpoints

# 10. 更新 .gitignore
echo "步骤 10: 更新 .gitignore..."
if ! grep -q ".agentmind_checkpoints" .gitignore; then
    echo "" >> .gitignore
    echo "# AgentMind temporary files" >> .gitignore
    echo ".agentmind_checkpoints/" >> .gitignore
    echo "*_REPORT.md" >> .gitignore
    echo "*_SUMMARY.md" >> .gitignore
    echo "*_COMPLETE.md" >> .gitignore
fi

# 11. 检查状态
echo ""
echo "步骤 11: 检查更改..."
git status

echo ""
echo "=== 文件重组完成 ==="
echo ""
echo "根目录保留的核心文档："
ls -1 *.md 2>/dev/null || echo "  (所有文档已移动)"
echo ""
echo "docs/ 目录结构："
tree docs/ -L 2 2>/dev/null || find docs/ -type d
echo ""
echo "下一步："
echo "1. 检查 git status 确认更改正确"
echo "2. 更新 README.md 中的文档链接"
echo "3. 运行: git add -A"
echo "4. 运行: git commit -m 'refactor: reorganize project documentation structure'"
echo "5. 运行: git push"
