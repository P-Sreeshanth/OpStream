# 🚀 Opstream

An AI-powered platform that helps developers discover and contribute to open source projects. The platform uses RAG (Retrieval Augmented Generation) to analyze GitHub repositories and provide intelligent insights, contribution suggestions, and mentorship.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-19.x-61DAFB.svg)

## ✨ Features

### 🔍 **Issue Discovery**
- Search for beginner-friendly issues across GitHub
- Filter by domain (React, Python, ML, Rust, Go, etc.)
- Sort by recent activity or popularity

### 🧠 **Repository Analysis**
- **RAG-powered Q&A**: Ask questions about any indexed repository
- **Tech Stack Detection**: Automatically identify languages, frameworks, and tools
- **Contribution Suggestions**: Get AI-curated lists of beginner-friendly tasks, bugs, and features
- **Warmth Score**: Evaluate maintainer friendliness (0-100)

### 💬 **AI Mentorship**
- Interactive chat with context about the repository
- Code review simulation
- Setup instructions extraction
- Skill requirements analysis for issues

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Qdrant** - Vector database for embeddings
- **Sentence Transformers** - MiniLM-L6-v2 for embeddings (384 dims)
- **Groq (Llama 3.3 70B)** - LLM for analysis and chat
- **PyGithub** - GitHub API integration

### Frontend
- **React 19** + **Vite** - Modern build tooling
- **Three.js** + **React Three Fiber** - 3D visualizations
- **Vanilla CSS** - Premium dark theme design

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Qdrant** (cloud or local)
- API Keys:
  - GitHub Personal Access Token
  - Groq API Key
  - HuggingFace API Token (optional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/open-source-intelligence.git
cd open-source-intelligence
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
# Required
GITHUB_TOKEN=ghp_your_github_token_here
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
# Or for Qdrant Cloud:
# QDRANT_URL=https://your-cluster.qdrant.io
# QDRANT_API_KEY=your_qdrant_api_key
```

### 4. Start Qdrant (Local)

Using Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Or use [Qdrant Cloud](https://cloud.qdrant.io/) for free managed hosting.

### 5. Run the Backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
open-source-intelligence/
├── backend/
│   ├── main.py           # FastAPI app & endpoints
│   ├── rag/
│   │   ├── engine.py     # RAG engine (Qdrant integration)
│   │   ├── fetcher.py    # GitHub data fetcher
│   │   └── analyzer.py   # LLM-powered analysis
│   ├── tools/
│   │   └── github_engine.py  # Issue search engine
│   └── memory/           # Conversation memory
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main app component
│   │   ├── components/   # React components
│   │   └── index.css     # Styling
│   └── package.json
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 🌐 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/domains` | GET | List available domains |
| `/api/issues` | POST | Search beginner-friendly issues |
| `/api/index-repo` | POST | Index a repository |
| `/api/analyze` | POST | Ask questions about a repo |
| `/api/suggest` | POST | Get contribution suggestions |
| `/api/tech-stack` | POST | Detect technology stack |
| `/api/warmth-score` | POST | Calculate maintainer warmth |
| `/api/setup` | POST | Extract setup instructions |
| `/api/difficulty` | POST | Calculate issue difficulty |

---

# 🚢 Deployment Guide

## Option 1: Vercel (Frontend) + Railway (Backend)

### Deploy Backend to Railway

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Create a new project** and select "Deploy from GitHub repo"

3. **Add environment variables** in Railway dashboard:
   ```
   GITHUB_TOKEN=ghp_xxx
   GROQ_API_KEY=gsk_xxx
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_qdrant_key
   ```

4. Railway will auto-detect the `Dockerfile` and deploy

5. **Note your backend URL** (e.g., `https://your-app.up.railway.app`)

### Deploy Frontend to Vercel

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

2. **Import your GitHub repository**

3. **Configure build settings**:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Add environment variable**:
   ```
   VITE_API_URL=https://your-app.up.railway.app
   ```

5. **Deploy!**

### Update Frontend API URL

Before deploying, update the API base URL in your frontend. Create `frontend/.env.production`:

```env
VITE_API_URL=https://your-backend.up.railway.app
```

Then update API calls to use the environment variable:

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

---

## Option 2: Render (Full Stack)

### Backend on Render

1. Go to [render.com](https://render.com) and create a Web Service

2. Connect your GitHub repo

3. Configure:
   - **Environment**: Docker
   - **Docker Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

4. Add environment variables (same as Railway)

5. Deploy and note the URL

### Frontend on Render (Static Site)

1. Create a **Static Site** on Render

2. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

3. Add `VITE_API_URL` environment variable

---

## Qdrant Cloud Setup (Required)

Since Railway/Render don't support persistent local storage well, use **Qdrant Cloud**:

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io) (free tier available)

2. Create a cluster

3. Get your **URL** and **API Key**

4. Update environment variables:
   ```
   QDRANT_URL=https://xxx.qdrant.io
   QDRANT_API_KEY=your_api_key
   ```

---

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -t open-source-intelligence .

# Run with environment variables
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=ghp_xxx \
  -e GROQ_API_KEY=gsk_xxx \
  -e QDRANT_URL=https://xxx.qdrant.io \
  -e QDRANT_API_KEY=xxx \
  open-source-intelligence
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - QDRANT_URL=${QDRANT_URL}
      - QDRANT_API_KEY=${QDRANT_API_KEY}
    
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  qdrant_storage:
```

---

## 📝 Post-Deployment Checklist

- [ ] Backend health check returns `{"status": "ok"}`
- [ ] Frontend loads and displays the domain filters
- [ ] Issue search works (tests GitHub API)
- [ ] Repository indexing works (tests Qdrant + GitHub)
- [ ] Chat/Analysis works (tests Groq LLM)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for blazing fast LLM inference
- [Qdrant](https://qdrant.tech/) for vector database
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- The open source community 💜
