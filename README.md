# ⚡ AI Job Hunter — Powered by Bright Data

> **Hackathon Project**: Autonomous Y Combinator job discovery & AI-driven skill matching engine powered by **Bright Data Web Scraper Studio**.

---

## 🌟 Overview

**AI Job Hunter** turns the tedious process of finding relevant startup jobs into a seamless, real-time experience. It orchestrates automated web crawling via **Bright Data Scraper Studio**, standardizes job postings from Y Combinator, and runs a multi-factor AI matching and ranking algorithm tailored to your skills, tech stack, and location preferences.

---

## 🕷️ Bright Data Scraper Studio Integration

The application integrates directly with Bright Data's Data Collector API (DCA):

| Parameter | Value |
| :--- | :--- |
| **Collector ID** | `c_mt5wl2m71k9t9f0bwj` |
| **Target Job Board** | `https://www.ycombinator.com/jobs` |
| **Collector Studio** | Bright Data Scraper Studio |
| **Auth Header** | `Authorization: Bearer <BRIGHT_DATA_API_TOKEN>` |

### 1. Trigger Crawl (Function 1)
Initiates the data collection job on Bright Data's cloud infrastructure:
```http
POST https://api.brightdata.com/dca/trigger?collector=c_mt5wl2m71k9t9f0bwj&queue_next=1
Headers:
  Authorization: Bearer <BRIGHT_DATA_API_TOKEN>
  Content-Type: application/json

Payload:
[
  { "url": "https://www.ycombinator.com/jobs" }
]
```
The response returns a unique `collection_id` (or `response_id`).

### 2. Poll Dataset (Function 2)
Polls the dataset endpoint until Bright Data completes scraping:
```http
GET https://api.brightdata.com/dca/dataset?id={COLLECTION_ID}
Headers:
  Authorization: Bearer <BRIGHT_DATA_API_TOKEN>
```
Returns structured JSON / NDJSON job records containing job titles, companies, locations, compensation, skills, and descriptions.

---

## 🧠 Job Matching & Ranking Engine

The matcher calculates a weighted relevance score (0% – 100%) for each job:

- **Skills & Tech Stack Overlap (45%)**: Matches user keywords against the job's tags and tech stack.
- **Title Relevance (30%)**: Matches keywords against job titles (e.g. Senior AI Engineer vs "AI").
- **Description Deep Scan (15%)**: Scans job descriptions for specific tools and methodologies.
- **Location Preference (10%)**: Boosts jobs matching preferred locations or Remote status.

---

## 🎨 Minimalist Monochrome Design

- **Black & White Simple Color Palette**: High contrast, distraction-free aesthetic with crisp typography and clean card layouts.
- **Dark Mode & Light Mode**: Live toggle switch to seamlessly shift between high-contrast dark theme and crisp light theme.

---

## 🚀 Quickstart Guide

### 1. Clone & Navigate to Project
```bash
cd /Users/siddu/.gemini/antigravity/scratch/ai-job-hunter
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your API token:
```bash
cp .env.example .env
```
Inside `.env`:
```env
BRIGHT_DATA_API_TOKEN=your_bright_data_api_token_here
BRIGHT_DATA_COLLECTOR_ID=c_mt5wl2m71k9t9f0bwj
TARGET_JOB_URL=https://www.ycombinator.com/jobs
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
ai-job-hunter/
├── app.py              # Main Streamlit web application & monochrome UI
├── bright_data.py      # Bright Data DCA client (trigger & polling logic)
├── matcher.py          # Relevance scoring & ranking engine
├── sample_data.py      # High-fidelity Y Combinator dataset for demos & offline testing
├── requirements.txt    # Python dependencies (streamlit, requests, python-dotenv, pandas)
├── .env.example        # Environment variables template
├── .env                # Local environment configuration
└── README.md           # Project documentation
```

---

## ⚡ Key Features

- **⚡ Bright Data DCA Trigger & Poller**: Live integration with Collector `c_mt5wl2m71k9t9f0bwj`.
- **🎯 Smart Skill Filters**: Quick-select keyword pills (`Python`, `AI`, `Remote`, `LLMs`, `React`, `FastAPI`, `Go`, `Rust`).
- **📊 Real-time Dashboard**: Live metrics for Total Crawled, Matching Jobs, Top Score, and Active Filters.
- **📩 Automated Email Alert Mockup**: Simulated instant/digest email notification generator.
- **💾 Export Capabilities**: Instant CSV and JSON downloads of ranked matches.
- **🌗 Dark & Light Theme**: Pure black-and-white minimalist design.
