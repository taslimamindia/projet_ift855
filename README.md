# Project IFT855 | Université de Sherbrooke

This project, carried out as part of a research essay at the University of Sherbrooke, implements a complete MLOps approach. Its objective is to develop and deploy an artificial intelligence system capable of answering user questions by leveraging web crawling techniques to automatically extract and process relevant information.

I gratefully acknowledge the guidance and supervision of [Professor Pierre‑Marc Jodoin](https://jodoin.github.io/) throughout this project.

The project covers the full solution lifecycle, including:

- Data acquisition and preprocessing through web crawling.
- Implementation of a Retrieval-Augmented Generation (RAG) system.
- Automation of the MLOps pipeline for continuous integration and deployment.
- Deployment of an API enabling users to interact with the system.

This repository contains the code, documentation, and configuration required to reproduce and further develop the project.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
	- [Backend (API)](#backend-api)
	- [Frontend (Web UI)](#frontend-web-ui)
- [API & Endpoints](#api--endpoints)
- [Datasets and Artifacts](#datasets-and-artifacts)
- [Development Notes](#development-notes)
- [Contributing](#contributing)
- [License & Contact](#license--contact)


## Overview

This repository implements a Retrieval-Augmented Generation (RAG) system with an end-to-end MLOps workflow. The system crawls web pages, extracts and processes content, computes embeddings, stores a FAISS index for retrieval, and serves a FastAPI-based backend together with a React + Vite frontend.


## Repository Structure

Top-level layout (important folders):

- `backend/` — Python backend (FastAPI), data loaders, model wrappers, RAG agent and pipeline logic.
- `frontend/` — React + TypeScript UI powered by Vite.
- `requirements.txt` — Python dependencies for the backend.
- `README.md` — This file.


## Technology Stack

- Backend: Python, FastAPI, Uvicorn
- Search & embeddings: FAISS, custom embedding code (Fireworks), LangChain for RAG orchestration
- Web crawling and data processing: BeautifulSoup, trafilatura, tldextract, others from `requirements.txt`
- Frontend: React, TypeScript, Vite, Bootstrap
- Dev / infra: ClearML integrations and environment-driven configuration


## Quick Start

These instructions assume you have Python 3.10+ and Node.js (with npm) installed.

### Backend (API)

1. Create a Python virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables:

- Copy or edit the provided `backend/dev.env` (or `backend/prod.env`) and set required variables such as `ENV`, `FIREWORKS_API_KEY`, `MODEL_EMBEDDINGS_NAME`, `MODEL_LLM_NAME`, `DEPLOYMENT_TYPE`.

4. Run the API (development):

```powershell
# from repository root
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

Notes:
- The backend loads datasets from `backend/datasets/` (e.g., `crawled_data.json`, `crawled_chunks.json`, `embeddings.npy`). Ensure these artifacts are present or re-run the crawling/embedding pipeline to regenerate them.
- CORS in `backend/api.py` is configured to allow `http://localhost:5173` (the default Vite dev server). Adjust if needed.


### Frontend (Web UI)

1. Install dependencies and run the dev server:

```powershell
cd frontend
npm install
npm run dev
```

2. By default the Vite dev server runs on `http://localhost:5173`. The frontend calls the backend endpoints and uses WebSocket routes for the pipeline progress features.

3. Build for production:

```powershell
npm run build
# serve the built files or integrate with your preferred static server
npm run preview
```


## API & Endpoints

Key endpoints provided by the backend (see `backend/api.py`):

- WebSocket pipeline endpoints (used by the frontend pipeline UI):
	- `ws://<host>/api/pipeline/initializing` — initialize a domain-specific model (supply `url`).
	- `ws://<host>/api/pipeline/crawling` — trigger crawling for a URL (supply `url` and `max_depth`).
	- `ws://<host>/api/pipeline/embedding` — compute embeddings for crawled pages (supply `url`).
	- `ws://<host>/api/pipeline/indexing` — create/update FAISS index for the domain.

- REST endpoints:
	- `POST /api/chat/rag` — call RAG chat: JSON body contains fields like `query`, `url` (optional), `k` (number of retrieved docs).

Example request payload for RAG chat:

```json
{
	"query": "What is retrieval augmented generation?",
	"url": "https://example.com",
	"k": 5
}
```


## Datasets and Artifacts

- `backend/datasets/` contains project-specific artifacts used at runtime:
	- `crawled_data.json`, `crawled_chunks.json`, `crawled_sources.json` — textual data produced by crawling.
	- `embeddings.npy` — precomputed embeddings array (if present).
	- `questions_references.csv` — evaluation helpers.

If you need to re-run crawling or embeddings, use the pipeline exposed through the frontend (websocket endpoints) or run the scripts in `backend/outils/`.


## Development Notes

- Settings are driven by `backend/load_settings.py` and `backend/config.py` via environment variables. Edit `backend/dev.env` for local development values.
- The backend uses a `Settings` dataclass (Pydantic Settings) to load `FIREWORKS_API_KEY`, model names and deployment type.
- Default Vite port: `5173`. Default backend port (when running uvicorn): `8000`.
- CORS is limited to the frontend origin in `backend/api.py` to simplify local development.


## Contributing

Contributions are welcome. Suggested workflow:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Implement your changes and add tests where appropriate.
4. Open a pull request describing the change.

Please follow the repository coding style and add tests for new functionality when possible.


## License & Contact

Add your preferred license here (e.g., MIT). For questions or collaboration, contact the project maintainer.


---

## Windows PowerShell — Quick commands

Below are short, copy-paste-friendly PowerShell snippets for common local development tasks on Windows. They assume you are at the repository root (`d:\\Stage\\projet_ift855`). Adjust paths or ports if you customized them.

- Create and activate a Python virtual environment:

```powershell
python -m venv .venv
# PowerShell (activate)
.\\.venv\\Scripts\\Activate.ps1
```

- Install backend Python dependencies:

```powershell
pip install -r requirements.txt
```

- Run the FastAPI backend (development mode with auto-reload):

```powershell
# from repository root
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

- Start the frontend dev server (Vite):

```powershell
cd frontend
npm install
npm run dev
```

- Build the frontend for production and preview locally:

```powershell
cd frontend
npm run build
npm run preview
```

- Notes for environment variables:

1. Copy `backend/dev.env` to `.env` (or create one) and set the required variables: `ENV`, `FIREWORKS_API_KEY`, `MODEL_EMBEDDINGS_NAME`, `MODEL_LLM_NAME`, `DEPLOYMENT_TYPE`.
2. When using PowerShell, prefer `Activate.ps1` to the `activate` script used on Unix shells.


## Conclusion

This repository demonstrates a complete MLOps process for a Retrieval-Augmented Generation (RAG) system: it includes web crawling and preprocessing, embedding generation, FAISS-based retrieval, a LangChain-based RAG agent, a FastAPI backend, and a React + Vite frontend that orchestrates the pipeline. The project is set up for iterative development — you can re-run the crawling and embedding pipeline, add evaluation datasets, and adapt the LLM configuration via environment variables.

