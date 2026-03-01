# The LLM Search - Project Documentation

*A living document to track project architecture, changes, and setup instructions.*

## Overview
The LLM Search is a local web application that allows users to query selected websites using conversational AI directly from their browser. It features a React frontend and a Python backend utilizing local Large Language Models (LLMs) via Ollama for privacy-preserving, fast chat-based querying.

## Architecture & Technology Stack

### Frontend (`/thellmsearch`)
- **Framework:** React (bootstrapped with Create React App)
- **Routing:** React Router
- **UI:** Material-UI (MUI)
- **Features:** Dark mode, responsive design, website selection, chat interface, search history.

### Backend (`/backend`)
- **Language:** Python
- **API Server:** FastAPI + Uvicorn (Provides the REST endpoint `POST /api/chat` on port 8000)
- **Core Dependencies:**
  - `fastapi`, `uvicorn` (for the API)
  - `ollama` (for connecting to local LLMs)
  - `requests`, `beautifulsoup4`, `lxml` (for web scraping)
- **Current Model:** `qwen3:4b-instruct`
- **Main Scripts:**
  - `api.py`: The FastAPI server linking the frontend React app to the search agent.
  - `local_search_llm_v2.py`: Advanced multi-source AI search agent that selects multiple URLs for comprehensive context.

## How to Run the Project

To run the project, you need to start both the backend and the frontend in separate terminals.

### 1. Start the Backend API
The backend runs the Ollama integration wrapped in a FastAPI server on `localhost:8000`.

```bash
cd backend
python -m uvicorn api:app --reload
```
*Note: Make sure Ollama is running and the `qwen3:4b-instruct` model is downloaded.*

### 2. Start the Frontend
The frontend provides the graphical user interface.

```bash
cd thellmsearch
npm start
```
*This will open the application in your browser at `http://localhost:3001`.*

---

## Recent Changes & Changelog

### February 2026
- **Model Migration:** Updated backend scripts (`local_search_agent.py`, `local_search_llm_v2.py`) to use `qwen3:4b-instruct` instead of `gemma3:12b`.
- **Bug Fix:** Fixed a variable scoping bug (`UnboundLocalError`) in `local_search_llm_v2.py` where `ctx` was referenced outside of the extraction loop.
- **Prompt Engineering:** Reworked `SYNTHESIS_PROMPT` in both backend files. Injected a dynamic `current_date` and added strict instructions preventing the model from citing its knowledge cutoff, forcing it to treat the scraped context as real-time updates. This prevents the "As of now, I can't provide real-time updates" error message when querying latest news.
- **Full-Stack Integration:** Completely disconnected the frontend's hardcoded "lorem ipsum" mock data. Created `api.py` using FastAPI in the backend, and installed `axios` in the React frontend. `Chat.js` now sends exact configurations and prompts to `api.py`, which dynamically triggers the Ollama model and returns real responses to the browser.
