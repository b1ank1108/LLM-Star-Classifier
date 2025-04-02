# 🌟 GitHub Star Repository Classifier

English | [中文](README_zh.md)

<div align="center">
  <img src="https://registry.npmmirror.com/@lobehub/icons-static-svg/1.44.0/files/icons/cursor.svg" alt="Cursor" width="32" height="32" />
  <p>Developed with Cursor</p>
</div>

A tool that uses 🤖 AI to classify and summarize GitHub Star repositories.

## ✨ Features

- 🔄 Automatically fetch GitHub Star repository information
- 🤖 AI-powered repository classification and summarization
- 📁 Multi-category management
- 📝 Automatic documentation generation
- ⚡ Concurrent processing support
- 🔑 Multiple API Key rotation support

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-star-classifier.git
cd llm-star-classifier
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configuration:
   - Copy `config.yaml.example` to `config.yaml`
   - Fill in your GitHub Token and OpenAI API Key in `config.yaml`

## 📖 Usage

### 📥 Fetch Repository Information
```bash
python main.py fetch
```

### 🏷️ Classify Repositories
```bash
python main.py classify
```

### 🔄 Process Unclassified Repositories Only
```bash
python main.py classify -u
```

### 📝 Generate Classification Documentation
```bash
python main.py gen-readme
```

## ⚙️ Configuration

Configure the following information in `config.yaml`:

- 🔑 GitHub Token: For accessing GitHub API
- 🤖 OpenAI API Key: For AI classification
- 💾 Database Path: Location to store repository information
- 📁 Categories: Predefined classification list

## 🤝 Contributing

Issues and Pull Requests are welcome to help improve this project.

## 📄 License

MIT License
