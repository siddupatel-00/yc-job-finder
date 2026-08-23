# AI Job Hunter - Autonomous Startup Intelligence Platform

AI Job Hunter is a specialized data ingestion, intelligence, and candidate-matching platform designed for startup opportunities. The system orchestrates automated web data collection via Bright Data Web Scraper Studio, processes and standardizes unstructured job postings, runs multi-factor heuristic matching against target technical profiles, generates tailored outreach pitches, and surfaces real-time compensation and market intelligence.

---

## Architecture and Data Flow

```
+-------------------------------------------------------------------------+
|                        Bright Data Cloud Engine                         |
|                                                                         |
|  +---------------------------+       Trigger        +----------------+  |
|  | Target Job Board:         | <------------------- | DCA Collector: |  |
|  | ycombinator.com/jobs      |                      | c_mt5wl2m71... |  |
|  +---------------------------+                      +----------------+  |
|               |                                              |          |
|               | Extraction & Parsing                         | Job ID   |
|               v                                              v          |
|  +-------------------------------------------------------------------+  |
|  |                     Dataset Endpoint Delivery                     |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
                                    |
                                    | Async Polling (GET /dca/dataset)
                                    v
+-------------------------------------------------------------------------+
|                         Local Processing Layer                          |
|                                                                         |
|  +--------------------+    Raw NDJSON/JSON    +----------------------+  |
|  | bright_data.py     | --------------------> | Normalization Engine |  |
|  +--------------------+                       +----------------------+  |
|                                                          |              |
|                                                          | Clean Dicts  |
|                                                          v              |
|  +--------------------+   Candidate Profile   +----------------------+  |
|  | matcher.py         | <-------------------- | Weighted Match Engine|  |
|  | - Skill Overlap    |                       +----------------------+  |
|  | - Title Relevance  |                                  |              |
|  | - Location Fit     |                                  | Scored Jobs  |
|  +--------------------+                                  v              |
|                                               +----------------------+  |
|                                               | generator.py         |  |
|                                               | - Cold Email Pitch   |  |
|                                               +----------------------+  |
|                                                          |              |
|                                                          v              |
|  +--------------------+                       +----------------------+  |
|  | analytics.py       | <-------------------- | Streamlit Interface  |  |
|  | - Stack Frequency  |                       | (app.py)             |  |
|  | - Stage Comp Dist  |                       +----------------------+  |
|  +--------------------+                                                 |
+-------------------------------------------------------------------------+
```

---

## Core Modules

The codebase is organized into discrete, modular components:

- **`app.py`**: Main application entry point and user interface built with Streamlit. Implements dynamic query-parameter routing (`?tab=...`), state management, real-time filtering, responsive layout rendering, and visual display cards.
- **`bright_data.py`**: Client module managing communication with the Bright Data Data Collector API (DCA). Handles crawl execution triggers, asynchronous dataset polling with exponential backoff, payload normalization, and API connection diagnostics.
- **`matcher.py`**: Multi-factor scoring and ranking engine. Computes fit percentages based on direct skill overlap (45%), title alignment (30%), description context (15%), and location/remote preferences (10%). Generates matched vs. missing skill matrices.
- **`generator.py`**: Pitch generation engine that constructs structured, contextual cold email templates targeting company domain requirements, tech stack alignment, and candidate background.
- **`analytics.py`**: Statistical aggregation service computing compensation percentiles across funding stages (Seed, Series A, Series B) and technology stack frequency distributions.
- **`sample_data.py`**: High-fidelity fallback dataset containing validated startup job listings across modern batch cohorts, used for instant caching, development, and offline execution.

---

## Bright Data Integration Specifications

The application directly communicates with Bright Data Scraper Studio through REST endpoints:

### Configuration Parameters
- **Collector ID**: `c_mt5wl2m71k9t9f0bwj`
- **Target URL**: `https://www.ycombinator.com/jobs`
- **Authentication**: Bearer Token via HTTP Header (`Authorization: Bearer <TOKEN>`)

### 1. Trigger Crawl (`trigger_crawl`)
Initiates the data collection job on Bright Data's cloud infrastructure.

- **Method**: `POST`
- **Endpoint**: `https://api.brightdata.com/dca/trigger?collector=c_mt5wl2m71k9t9f0bwj&queue_next=1`
- **Headers**:
  ```http
  Authorization: Bearer <BRIGHT_DATA_API_TOKEN>
  Content-Type: application/json
  ```
- **Payload**:
  ```json
  [
    {
      "url": "https://www.ycombinator.com/jobs"
    }
  ]
  ```
- **Response**: Returns a JSON object containing `collection_id` (or `response_id`).

### 2. Dataset Polling (`poll_dataset`)
Retrieves the extracted dataset once the crawler finishes execution.

- **Method**: `GET`
- **Endpoint**: `https://api.brightdata.com/dca/dataset?id={COLLECTION_ID}`
- **Headers**:
  ```http
  Authorization: Bearer <BRIGHT_DATA_API_TOKEN>
  ```
- **Execution Strategy**: Polling loop executed with interval delays (`poll_interval_seconds=3`) up to a maximum retry threshold (`max_retries=6`). Returns HTTP 200 with JSON/NDJSON records upon completion.

---

## Setup and Execution

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git
- Valid Bright Data API Token (optional for live crawling; offline cache works out-of-the-box)

### Step 1: Clone Repository
```bash
git clone https://github.com/siddupatel-00/yc-job-finder.git
cd yc-job-finder
```

### Step 2: Configure Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# .\venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example environment file and insert your API credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
BRIGHT_DATA_API_TOKEN=your_bright_data_api_token_here
BRIGHT_DATA_COLLECTOR_ID=c_mt5wl2m71k9t9f0bwj
```

### Step 5: Launch Application
```bash
streamlit run app.py
```

The application will initialize and become available locally at `http://localhost:8501`.

---

## Routing & Deep Links

The interface supports direct deep linking via query parameters:
- `http://localhost:8501/?tab=opportunities`: Active job opportunities and filter panel.
- `http://localhost:8501/?tab=pitch-generator`: Cold outreach email generator.
- `http://localhost:8501/?tab=analytics`: Compensation distributions and tech stack intelligence.
- `http://localhost:8501/?tab=terminal`: Bright Data DCA API configuration and diagnostics.
