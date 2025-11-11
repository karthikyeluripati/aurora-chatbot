# Aurora QA System

Natural language question-answering API for luxury concierge member data, powered by GPT-4o-mini.

## 🚀 Live Demo

- **Backend API**: https://your-backend-url.onrender.com
- **Web Interface**: https://your-frontend-url.vercel.app

## API Endpoint

### POST /ask

**Request:**
```bash
curl -X POST https://your-backend-url.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

**Response:**
```json
{
  "answer": "Layla is planning to stay at Claridge's in London for five nights starting Monday. She also needs a car service upon arrival and requires a chauffeur-driven Bentley for her stay next month."
}
```

### Other Endpoints

- `GET /` - Health check
- `GET /stats` - Dataset statistics
- `GET /docs` - Interactive API documentation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run
python app.py
```

Backend runs on http://localhost:8000

## Example Usage

```bash
# Test the API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are Sophia Al-Farsi'\''s travel preferences?"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which restaurants has Fatima El-Tahir visited?"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are Vikram Desai'\''s recent bookings?"}'
```

## Web Interface (Bonus)

Interactive chat UI for easy testing:

```bash
cd frontend
python serve.py
# Open http://localhost:3000
```

**Features**: Member selector, suggested questions, category filters, real-time responses

## Architecture

```
User Question → /ask Endpoint → Fetch Messages (cached)
→ Filter by User → Build Context → GPT-4o-mini → Return Answer
```

**Key Features:**
- **Smart Filtering**: Extracts user names from questions, filters 3,349 messages to ~300-400 relevant
- **Context Optimization**: Groups messages by member for better LLM comprehension
- **Caching**: 5-minute TTL reduces external API calls
- **Fast Responses**: 1-3 seconds with filtering

**Tech Stack**: Python 3.11, FastAPI, OpenAI GPT-4o-mini, Docker

## Bonus 1: Design Approaches Considered

### Chosen: LLM with Filtered Context

**How it works:** Extract user names from questions, filter messages to relevant members, pass to GPT-4o-mini

**Pros:**
- ✅ Simple to implement
- ✅ Handles complex questions
- ✅ No training data needed
- ✅ Optimal for 3,349 messages

**Cons:**
- ~$0.001-0.002 per query
- 1-3 second response time

---

### Alternative 1: Vector Database + RAG

**Approach:** Embed messages → Store in Pinecone/Weaviate → Retrieve top-K → Pass to LLM

**Pros:** Scales to millions, lower token costs, fast retrieval

**Cons:** Additional infrastructure, embedding costs, overkill for 3K messages

**Best for:** 10K+ messages

---

### Alternative 2: Fine-tuned Small Model

**Approach:** Fine-tune BERT/T5 on domain Q&A pairs

**Pros:** Lower costs, runs locally, fast

**Cons:** Needs training data (100+ examples), limited to trained patterns

**Best for:** 10K+ queries/day with fixed patterns

---

### Alternative 3: Rule-Based NLP

**Approach:** SpaCy NER → Pattern matching → Direct queries

**Pros:** Deterministic, no LLM costs, fast (<100ms)

**Cons:** Manual pattern engineering, brittle, poor for ambiguous queries

**Best for:** Fixed query templates only

---

### Alternative 4: Hybrid Vector + LLM

**Approach:** Vector search (top 50-100) → LLM for final answer

**Pros:** Balances cost and accuracy, scales well

**Cons:** More complexity, additional dependencies

**Best for:** 10K-50K messages

---

### Recommendation by Scale

| Dataset Size | Best Approach |
|--------------|---------------|
| 0-5K messages | LLM with filtered context (our choice) |
| 5K-50K | Hybrid vector + LLM |
| 50K+ | Full vector DB + RAG |

**Our choice** is optimal for 3,349 messages: simple, accurate, maintainable.

## Bonus 2: Data Insights & Anomalies

### Dataset Overview

- **Total**: 3,349 messages
- **Members**: 10
- **Date Range**: Nov 8, 2024 - Nov 8, 2025
- **Avg Length**: 68 characters

### Distribution

Even distribution across members (8.6% - 10.9% each):
- Lily O'Sullivan: 365 (10.9%)
- Thiago Monteiro: 361 (10.8%)
- Fatima El-Tahir: 349 (10.4%)
- Others: 288-346 each

### Top Services & Destinations

**Services:** Bookings (309), Hotels (202), Tickets (201), Cars (157), Flights (137)

**Destinations:** Paris (81), Tokyo (60), Milan (52), New York (52), London (47)

### Identified Anomalies

#### 1. Name Mismatch
**Issue:** Example asks about "Amira's favorite restaurants"
**Finding:** No user "Amira" exists → Closest is "Amina Van Den Berg"
**Impact:** Returns "no information"
**Fix:** Use exact names from `/stats`

#### 2. PII Exposure
**Finding:** 33 phone numbers, 8 emails in messages
**Risk:** Privacy concern
**Recommendation:** Implement PII masking

#### 3. Conflicting Preferences
**Example:** Lily O'Sullivan says both "I prefer window seats" AND "I prefer aisle seats"
**Impact:** LLM may note conflict in response
**Fix:** Track preference changes with timestamps

#### 4. Short Messages
**Finding:** 2 messages < 10 characters
**Issue:** Likely incomplete/test data
**Fix:** Add minimum length validation

#### 5. Future Timestamps
**Finding:** Messages dated through Nov 2025
**Assessment:** Expected for advance bookings
**Not an anomaly**

### Data Quality Summary

**Strengths:**
- No duplicates
- Consistent user IDs
- Proper formatting
- Clean text

**Improvements:**
- Redact PII
- Fix name inconsistencies
- Add validation
- Version preferences

**Overall:** High-quality dataset, production-ready with minor PII handling

## Testing

```bash
# Run test suite
python test_api.py

# Analyze dataset
python analyze_data.py
```

## Deployment

**Docker:**
```bash
docker-compose up --build
```

**Render.com** (recommended):
1. Push to GitHub
2. render.com → New Web Service → Docker
3. Add `OPENAI_API_KEY` env var
4. Deploy

**Vercel** (frontend):
1. Update `frontend/app.js` with backend URL
2. `cd frontend && vercel --prod`

## Project Structure

```
aurora-chatbot/
├── app.py              # Main FastAPI application
├── requirements.txt    # Dependencies
├── Dockerfile          # Container config
├── test_api.py         # API tests
├── analyze_data.py     # Dataset analysis
├── frontend/           # Web UI (bonus)
│   ├── index.html
│   ├── app.js
│   └── serve.py
└── README.md           # This file
```

## Performance

- Response time: 1-3 seconds
- Cost per query: ~$0.001-0.002
- Cache TTL: 5 minutes

---

**Built for Aurora Chatbot Challenge** | MIT License
