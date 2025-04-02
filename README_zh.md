# 🌟 GitHub Star 仓库分类工具

[English](README.md) | 中文

<div align="center">
  <img src="https://registry.npmmirror.com/@lobehub/icons-static-svg/1.44.0/files/icons/cursor.svg" alt="Cursor" width="32" height="32" />
  <p>使用 Cursor 开发</p>
</div>

这是一个使用 🤖 AI 对 GitHub Star 的仓库进行分类和总结的工具。

## ✨ 功能特点

- 🔄 自动获取 GitHub Star 的仓库信息
- 🤖 使用 AI 对仓库进行分类和总结
- 📁 支持多分类管理
- 📝 自动生成分类文档
- ⚡ 支持并发处理
- 🔑 支持多个 API Key 轮询

## 🚀 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/llm-star-classifier.git
cd llm-star-classifier
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置：
   - 复制 `config.yaml.example` 到 `config.yaml`
   - 在 `config.yaml` 中填入你的 GitHub Token 和 OpenAI API Key

## 📖 使用方法

### 📥 获取仓库信息
```bash
python main.py fetch
```

### 🏷️ 对仓库进行分类
```bash
python main.py classify
```

### 🔄 仅处理未分类的仓库
```bash
python main.py classify -u
```

### 📝 生成分类文档
```bash
python main.py gen-readme
```

## ⚙️ 配置说明

在 `config.yaml` 中配置以下信息：

- 🔑 GitHub Token：用于访问 GitHub API
- 🤖 OpenAI API Key：用于 AI 分类
- 💾 数据库路径：存储仓库信息的位置
- 📁 分类类别：预定义的分类列表

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 📄 许可证

MIT License 