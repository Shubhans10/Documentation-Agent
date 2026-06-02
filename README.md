# 🔥 DocuForge — AI Documentation Agent

> Transform raw content into beautifully structured HTML documentation, powered by Google Antigravity SDK & Gemini.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/typescript-5+-3178C6.svg)

---

## ✨ Features

- **Multi-format Input** — Upload TXT, PDF, Markdown files and images
- **AI-Powered Structuring** — Gemini analyzes and organizes your content into logical documentation
- **Diagram Generation** — Auto-generates Mermaid.js diagrams (flowcharts, sequences, ER, etc.) with a toggle control
- **Smart Image Handling** — Detects uploaded images and prompts for placement in the documentation
- **Live Preview** — Watch your documentation build in real-time via server-sent events
- **Multiple Themes** — Modern Dark, Clean Light, and Technical Blueprint
- **Self-Contained Export** — Download a single HTML file with all styles and assets embedded
- **Interactive Chat** — Send additional instructions to the agent mid-generation

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              React TypeScript Frontend                │
│   Upload Panel · Settings · Live Preview · Export     │
└──────────────────────┬───────────────────────────────┘
                       │ REST + SSE
┌──────────────────────┼───────────────────────────────┐
│           FastAPI Python Backend                      │
│  ┌───────────────────▼──────────────────────────┐    │
│  │       Orchestrator Agent (Antigravity SDK)     │    │
│  │  tools: diagram · table · code · structure    │    │
│  └───────────────────────────────────────────────┘    │
│  File Processor (PDF · TXT · MD · Images)             │
│  HTML Renderer (Jinja2 + Mermaid.js + Prism.js)       │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Gemini API Key](https://aistudio.google.com/app/api-keys)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/documentation-agent.git
cd documentation-agent
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

---

## 🎮 Usage

1. **Upload Files** — Drag & drop your TXT, PDF, MD files or images into the upload zone
2. **Configure Settings** — Toggle diagram generation, choose a theme, enable/disable features
3. **Generate** — Click "Generate Documentation" and watch it build in real-time
4. **Place Images** — When images are detected, a modal prompts you to choose placement
5. **Export** — Download your self-contained HTML documentation

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ | — | Your Gemini API key |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Maximum upload file size in MB |
| `OUTPUT_DIR` | ❌ | `./output` | Directory for generated HTML files |

---

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings & env loading
│   │   ├── agents/
│   │   │   ├── orchestrator.py  # Main AI orchestrator
│   │   │   └── tools/           # Agent tools (diagram, table, code, structure)
│   │   ├── services/            # File processing & HTML rendering
│   │   ├── models/              # Pydantic schemas
│   │   └── templates/           # HTML templates
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── api/                 # API client
│   │   └── types/               # TypeScript types
│   └── package.json
└── README.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
