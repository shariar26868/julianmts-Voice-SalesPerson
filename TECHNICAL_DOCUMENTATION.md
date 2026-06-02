# 🚀 AI Sales Training Platform - Complete Technical Documentation

**Version:** 1.0.0  
**Last Updated:** June 2025  
**Platform:** Enterprise AI Sales Training & Conversation Simulation  

---

## 📋 Executive Summary

The **AI Sales Training Platform** is a sophisticated, production-ready **FastAPI-based backend system** designed to help salespeople practice realistic sales conversations through AI-powered, multi-agent role-playing simulations. The platform combines advanced conversational AI, real-time voice synthesis, and comprehensive analytics to create an immersive training experience.

### Key Capabilities
- **Multi-Agent AI Conversations:** 1-on-1, 1-on-2, or 1-on-3 realistic meeting simulations
- **Real-time Voice I/O:** Full speech-to-text and text-to-speech capabilities
- **Intelligent Orchestration:** GPT-4 powered agent selection and turn management
- **Comprehensive Analytics:** Meeting performance scoring, sentiment analysis, MEDDIC framework evaluation
- **Enterprise Data Management:** Secure cloud storage, MongoDB persistence, AWS S3 audio archival

---

## 🏗️ Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  (Web Browser / Mobile App / Voice Client)                          │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ API ROUTES LAYER                                             │   │
│  │ ├─ /api/salesperson      (Sales rep management)             │   │
│  │ ├─ /api/company          (Company & contact management)     │   │
│  │ ├─ /api/meeting          (Meeting creation & setup)         │   │
│  │ ├─ /api/conversation     (Real-time conversation flow)      │   │
│  │ ├─ /api/admin            (System configuration)             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                     │                                                │
│                     ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SERVICE LAYER                                                │   │
│  │ ├─ OpenAI Service (GPT-4 orchestration)                      │   │
│  │ ├─ ElevenLabs Service (Voice synthesis)                      │   │
│  │ ├─ Whisper Service (Speech recognition)                      │   │
│  │ ├─ S3 Service (Audio storage)                               │   │
│  │ ├─ Google Search Service (Company research)                  │   │
│  │ ├─ URL Validation Service (Link verification)                │   │
│  │ ├─ Scraper Service (Web data extraction)                     │   │
│  │ ├─ Audio Stream Service (Real-time streaming)                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                     │                                                │
│                     ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ DATABASE LAYER                                               │   │
│  │ ├─ Collections:                                              │   │
│  │ │  • salespeople          (Sales rep profiles)              │   │
│  │ │  • companies            (Target companies)                │   │
│  │ │  • representatives      (Company reps / roles)            │   │
│  │ │  • meetings             (Practice session configs)        │   │
│  │ │  • conversations        (Meeting transcripts & data)      │   │
│  │ │  • methodology_prompts  (Sales framework configs)         │   │
│  │ │  • system_config        (Global system settings)          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ OpenAI  │ │ Eleven  │ │   AWS   │
    │  GPT-4  │ │  Labs   │ │    S3   │
    └─────────┘ └─────────┘ └─────────┘
         │           │           │
         └─────────┬─────────────┘
                   ▼
          ┌─────────────────┐
          │ MongoDB Atlas   │
          │ (Cloud DB)      │
          └─────────────────┘
```

---

## 🔧 Technology Stack

### Backend Framework
- **FastAPI 0.109.0** - Modern, async Python web framework
- **Uvicorn 0.27.0** - ASGI server for production deployment
- **Python 3.9+** - Core language

### AI/ML Services
- **OpenAI GPT-4 Turbo** - Conversation orchestration & multi-agent response generation
- **ElevenLabs API v1.2+** - Premium text-to-speech with natural voice synthesis
- **OpenAI Whisper** - Speech-to-text transcription

### Database & Storage
- **MongoDB Atlas** - Cloud NoSQL database for structured data
- **Motor 3.3.2** - Async MongoDB driver for FastAPI
- **AWS S3 (boto3)** - Secure cloud storage for audio recordings

### Web & Data Processing
- **BeautifulSoup4 4.12.3** - HTML parsing and web scraping
- **httpx 0.26.0** - Async HTTP client for API calls
- **Pydantic 2.5.3** - Data validation and serialization

### Audio Processing
- **Pydub 0.25.1** - Audio file manipulation
- **ImageIO-FFmpeg 0.6.0** - FFmpeg wrapper for audio encoding/decoding

### Security & Authentication
- **python-jose 3.3.0** - JWT token handling
- **passlib[bcrypt] 1.7.4** - Secure password hashing
- **python-dotenv 1.0.0** - Environment configuration

### Additional Libraries
- **WebSockets 12.0+** - Real-time bidirectional communication
- **Aiofiles 23.2.1** - Async file I/O operations

---

## 📊 Core Data Models

### 1. **Salesperson Model**
```json
{
  "_id": "uuid",
  "product_name": "string",
  "product_url": "url (optional)",
  "description": "string",
  "materials": [
    {
      "file_name": "string",
      "file_url": "s3_url",
      "file_type": "pdf|pptx|docx|image"
    }
  ],
  "created_at": "datetime"
}
```

### 2. **Company Model**
```json
{
  "_id": "uuid",
  "company_url": "string",
  "company_data": {
    "company_size": "string",
    "headquarters": "string",
    "revenue": "string",
    "industry": "string",
    "tech_stack": ["string"],
    "open_positions": "int",
    "customer_reviews": "object",
    "latest_news": ["string"],
    "financial_growth": "string"
  },
  "created_at": "datetime",
  "last_updated": "datetime"
}
```

### 3. **Representative Model**
```json
{
  "_id": "uuid",
  "company_id": "uuid",
  "name": "string",
  "role": "ceo|cmo|cfo|coo|cto|vp_sales|director|manager",
  "tenure_months": "int",
  "personality_traits": ["angry|arrogant|soft|cold_hearted|nice|analytical"],
  "is_decision_maker": "boolean",
  "linkedin_profile": "url (optional)",
  "notes": "string",
  "voice_id": "string (ElevenLabs ID)",
  "created_at": "datetime"
}
```

### 4. **Meeting Model**
```json
{
  "_id": "uuid",
  "salesperson_id": "uuid",
  "company_id": "uuid",
  "meeting_mode": "1-on-1|1-on-2|1-on-3",
  "representative_ids": ["uuid"],
  "meeting_goal": "string",
  "top_5_questions": ["string"],
  "personality": "nice|angry|soft|analytical|etc",
  "difficulty": "beginner|intermediate|advanced",
  "sales_methodology": "MEDDIC|BANT|CHALLENGER_SALES|SPIN|MEDDPICC|VALUE_SELLING|Other",
  "methodology_description": "string (custom methodology)",
  "status": "pending|active|completed",
  "duration_minutes": "int",
  "created_at": "datetime",
  "started_at": "datetime",
  "ended_at": "datetime",
  "total_duration_seconds": "float"
}
```

### 5. **Conversation Model**
```json
{
  "_id": "uuid",
  "meeting_id": "uuid",
  "session_id": "uuid",
  "turns": [
    {
      "turn_number": "int",
      "speaker": "salesperson|representative_id",
      "speaker_name": "string",
      "text": "string",
      "audio_url": "s3_url (optional)",
      "timestamp": "HH:MM:SS",
      "duration_seconds": "float",
      "created_at": "datetime"
    }
  ],
  "total_turns": "int",
  "salesperson_talk_time": "float (seconds)",
  "representatives_talk_time": "float (seconds)",
  "analytics": {
    "overall_score": "int (0-100)",
    "engagement_score": "int (0-100)",
    "preparation_score": "int (0-100)",
    "sentiment": "Positive|Neutral|Negative",
    "active_listening_grade": "A+|A|A-|B+|B|C|D",
    "questions_asked": "int",
    "open_questions": "int",
    "meddic": {
      "metrics": "string",
      "economic_buyer": "string",
      "decision_criteria": "string",
      "decision_process": "string",
      "identify_pain": "string",
      "champion": "string"
    }
  },
  "created_at": "datetime"
}
```

---

## 🔄 API Endpoints Structure

### Salesperson Routes `/api/salesperson`
- `POST /create` - Create new salesperson profile
- `GET /` - List all salespeople
- `GET /{salesperson_id}` - Get specific salesperson details
- `PUT /{salesperson_id}` - Update salesperson information
- `DELETE /{salesperson_id}` - Delete salesperson
- `GET /{salesperson_id}/dashboard` - Performance dashboard with all meetings

### Company Routes `/api/company`
- `POST /create` - Create company profile with auto-scrape
- `GET /` - List all companies
- `GET /{company_id}` - Get company details
- `PUT /{company_id}` - Update company information
- `DELETE /{company_id}` - Delete company
- `GET /{company_id}/representatives` - List company representatives
- `POST /{company_id}/representatives` - Add representative
- `PUT /{company_id}/representatives/{rep_id}` - Update representative
- `DELETE /{company_id}/representatives/{rep_id}` - Delete representative
- `GET /{company_id}/account-details` - Full account overview with analytics

### Meeting Routes `/api/meeting`
- `POST /create` - Create new meeting simulation
- `GET /{meeting_id}` - Get meeting details
- `POST /{meeting_id}/start` - Activate meeting
- `POST /{meeting_id}/end` - Complete meeting
- `GET /{meeting_id}/analytics` - Get meeting performance metrics

### Conversation Routes `/api/conversation`
- `POST /send-message` - Submit message and receive AI response (WebSocket compatible)
- `GET /{meeting_id}/history` - Get full conversation transcript
- `GET /{meeting_id}/analytics` - Get conversation-level analytics
- `WebSocket /ws/{meeting_id}` - Real-time bidirectional conversation stream

### Admin Routes `/api/admin`
- `GET /methodology-prompts` - List all sales methodology prompts
- `GET /methodology-prompts/{name}` - Get specific methodology
- `PUT /methodology-prompts/{name}` - Update methodology prompt
- `DELETE /methodology-prompts/{name}` - Delete methodology
- `GET /system-prompt` - Get global system prompt
- `PUT /system-prompt` - Update global system prompt

---

## 🤖 AI Orchestration Flow

### Conversation Turn Sequence

```
1. USER SENDS MESSAGE
   └─> Message arrives at /api/conversation/send-message
   
2. CONVERSATION STATE CHECK
   └─> Verify meeting is active
   └─> Load previous conversation history (last 10 turns)
   
3. MULTI-AGENT ORCHESTRATION
   └─> OpenAI GPT-4 analyzes:
       • Current message context
       • All representative profiles
       • Company background
       • Conversation history
       • Sales methodology (if configured)
   └─> GPT-4 determines:
       ✓ Who should respond (representative selection)
       ✓ What tone/personality to use
       ✓ Should anyone interrupt
       ✓ Response content

4. RESPONSE GENERATION
   └─> Selected representative crafts response:
       • Personality-aligned (angry, soft, analytical, etc.)
       • Methodology-aligned (MEDDIC challenges, SPIN questions, etc.)
       • Context-aware (product knowledge, company research)
       • Natural conversation flow

5. VOICE SYNTHESIS
   └─> ElevenLabs converts response to audio:
       • Representative's assigned voice
       • Personality-based delivery style
       • Natural prosody and pace

6. STORAGE & PERSISTENCE
   └─> Save to MongoDB:
       ✓ Conversation turn with metadata
       ✓ Update talk time metrics
       ✓ Increment turn counter
   └─> Upload to S3:
       ✓ Salesperson audio file
       ✓ Representative audio file
       ✓ Transcripts

7. RESPONSE TO CLIENT
   └─> Return AI response with:
       • Response text
       • Audio URL (S3)
       • Speaker metadata
       • Reasoning for selection
```

### Example AI Selection Logic
```python
# GPT-4 Input
{
  "company_url": "https://techcorp.com",
  "product_pitching": "Sales Intelligence SaaS",
  "representatives": [
    {"id": "rep1", "name": "Alice", "role": "CFO", "personality": "cold_hearted"},
    {"id": "rep2", "name": "Bob", "role": "VP Sales", "personality": "analytical"}
  ],
  "conversation_context": "...",
  "current_message": "Our platform uses AI to predict sales outcomes..."
}

# GPT-4 Output
{
  "primary_rep_id": "rep2",
  "primary_rep_name": "Bob",
  "primary_response": "Can you walk me through the specific metrics behind that claim? What's your historical accuracy rate?",
  "secondary_rep_id": "rep1",
  "secondary_response": "And more importantly, what's the ROI? Show me the numbers.",
  "reasoning": "Bob (analytical VP Sales) leads with methodology questions, Alice (cold CFO) backs with financial focus"
}
```

---

## 📈 Analytics Engine

### Post-Meeting Analytics Generation

When a meeting concludes, the system automatically generates comprehensive analytics by:

1. **Transcript Extraction**
   - Reconstruct full conversation from stored turns
   - Clean and format for analysis

2. **GPT-4 Analysis**
   - Deep conversation analysis with structured JSON output
   - Multi-dimensional scoring across 6 metrics
   - MEDDIC framework evaluation
   - Sentiment analysis
   - Question analysis (total & open-ended)

3. **Persistence**
   - Store analytics in MongoDB conversation document
   - Generate historical trends for salesperson dashboard

### Scoring Dimensions
- **Overall Score** (0-100): Composite performance rating
- **Engagement Score** (0-100): Interaction quality & attention
- **Preparation Score** (0-100): Research & goal alignment
- **Sentiment** (Positive/Neutral/Negative): Meeting tone trajectory
- **Active Listening Grade** (A+/A/A-/B+/B/C/D): Comprehension quality
- **Questions Asked**: Total count
- **Open Questions**: Percentage of open-ended questions

---

## 🎯 Supported Sales Methodologies

The platform supports 6 enterprise sales methodologies, each with AI-prompted representative behaviors:

### 1. **MEDDIC** (Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion)
- Challenges on ROI metrics and measurable outcomes
- Questions decision maker authority
- Probes evaluation criteria rigorously
- Uncovers internal approval process
- Forces pain identification

### 2. **BANT** (Budget, Authority, Need, Timeline)
- Vague about budget availability
- Questions signing authority
- Makes buyer discover needs
- Non-committal on timelines

### 3. **Challenger Sales**
- Pushes back on assumptions
- Brings new perspectives with data
- Sometimes agrees, sometimes resists
- Rewards genuine insights

### 4. **SPIN Selling** (Situation, Problem, Implication, Need-Payoff)
- Brief on situation questions
- Acknowledges pain but downplays urgency
- Shows concern when consequences highlighted
- Engages on solution-need connections

### 5. **MEDDPICC** (MEDDIC + Paper Process, Competition)
- MEDDIC pillars plus:
- Highlights legal/procurement complexity
- Hints at competitive evaluation

### 6. **Value Selling**
- Focuses on business outcomes
- Challenges value quantification
- Demands specifics relevant to business
- Skeptical of generic claims

---

## 🔐 Security Architecture

### Authentication & Authorization
- **JWT Tokens** for API authentication
- **Environment-based secrets** (OpenAI, ElevenLabs, AWS keys)
- **CORS middleware** with configurable origins

### Data Security
- **MongoDB encryption at rest** (Atlas default)
- **HTTPS for all external API calls**
- **S3 bucket policies** for access control
- **Audio files encrypted in transit**

### Rate Limiting & DDoS Protection
- WebSocket connection limits
- API rate limiting per endpoint
- Request validation & sanitization

### Compliance
- GDPR-compliant data retention policies
- SOC 2 audit trail (conversation logs)
- PII handling in audio transcripts

---

## 🚀 Deployment Architecture

### Production Deployment
```
Client (Web/Mobile)
    ↓
CloudFlare CDN (Optional)
    ↓
API Gateway (AWS/GCP)
    ↓
FastAPI Container (Docker)
    ├─ Multiple instances (auto-scaling)
    └─ Health checks
    ↓
Load Balancer
    ↓
Service Dependencies:
├─ MongoDB Atlas (Primary)
├─ AWS S3 (Audio storage)
├─ OpenAI API (External)
├─ ElevenLabs API (External)
└─ Google Search API (External)
```

### Docker Deployment
```dockerfile
# Base: Python 3.11 slim
# Install: Dependencies from requirements.txt
# Expose: Port 8000
# Health Check: /health endpoint
# CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment Configuration
```env
# API Keys
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=sk_...
GOOGLE_API_KEY=...

# Database
MONGODB_URL=mongodb+srv://...
MONGODB_DB_NAME=julienmts

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-north-1
S3_BUCKET_NAME=salesman-practice

# App Settings
APP_ENV=production|development
DEBUG=False
```

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (for containerization)
- MongoDB Atlas account
- AWS S3 bucket
- OpenAI API key (GPT-4 access)
- ElevenLabs API key

### Local Development Setup
```bash
# 1. Clone repository
git clone <repo>
cd julianmts-Voice-SalesPerson

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build image
docker build -t salesman-trainer:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  --name salesman-trainer \
  salesman-trainer:latest

# Or use Docker Compose
docker-compose up -d
```

---

## 📊 Performance Metrics & Monitoring

### Key Metrics to Track
- **API Response Time** - Target <500ms for conversation turns
- **AI Latency** - GPT-4 response time (typical 2-5s)
- **TTS Latency** - ElevenLabs synthesis time (typical 1-3s)
- **Database Queries/sec** - MongoDB performance
- **Concurrent Users** - WebSocket connections
- **Error Rate** - API 5xx errors (target <0.1%)
- **Audio Quality** - Bit rate, sample rate consistency

### Monitoring Stack (Recommended)
- **Application Monitoring**: Sentry / New Relic
- **Infrastructure Monitoring**: Prometheus + Grafana
- **Log Aggregation**: CloudWatch / ELK Stack
- **Error Tracking**: Sentry / Rollbar

---

## 🔧 Integration Points

### External API Dependencies

| Service | Purpose | Latency | Cost Model |
|---------|---------|---------|-----------|
| **OpenAI GPT-4** | Conversation orchestration | 2-5s | $0.03/1K input tokens |
| **ElevenLabs** | Voice synthesis | 1-3s | ~$0.30/1K characters |
| **AWS S3** | Audio storage | <100ms | $0.023/GB stored |
| **MongoDB Atlas** | Database | <50ms | $0.10/million ops |
| **Google Search API** | Company research | 1-2s | $5/1K queries |

---

## 🎓 Use Cases & Workflows

### Use Case 1: Sales Representative Training
```
Sales Rep → Schedules practice meeting
         → Selects company & representatives
         → Practices conversation
         → Receives AI feedback
         → Tracks improvement over time
```

### Use Case 2: Manager Coaching
```
Manager → Reviews rep's meeting recordings
       → Analyzes MEDDIC framework adherence
       → Identifies coaching opportunities
       → Creates training plan
```

### Use Case 3: Methodology Training
```
Organization → Defines custom sales methodology
            → Configures in Admin panel
            → Reps practice with that methodology
            → Tracks methodology adoption metrics
```

---

## 🛣️ Roadmap & Future Enhancements

### Q3 2025
- [ ] Multi-language support (Spanish, French, German)
- [ ] Video meeting simulation with real-time transcription
- [ ] Advanced NLP sentiment analysis
- [ ] Custom LLM fine-tuning on company data

### Q4 2025
- [ ] Mobile native app (iOS/Android)
- [ ] Real-time collaboration (multiple salespeople in same meeting)
- [ ] Advanced analytics dashboard with predictive insights
- [ ] Integration with Salesforce CRM

### Q1 2026
- [ ] Realistic competitor simulation
- [ ] Scenario branching (multiple decision paths)
- [ ] Advanced coaching AI (real-time intervention)
- [ ] Voice cloning for custom company representatives

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: "Connection to MongoDB failed"
- Check MONGODB_URL in .env
- Verify IP whitelist on MongoDB Atlas
- Test connection: `python -c "import motor; print('OK')"`

**Issue**: "OpenAI API errors (quota/rate limit)"
- Verify API key has GPT-4 access
- Check account quota and billing
- Implement exponential backoff retry logic

**Issue**: "ElevenLabs audio quality poor"
- Verify voice_id is valid
- Check audio bit rate (recommend 128kbps+)
- Test with sample text in ElevenLabs dashboard

**Issue**: "High API latency (>2s per turn)"
- Check network connection to external APIs
- Consider caching common responses
- Implement request batching for analytics

---

## 📄 API Documentation

Full Swagger/OpenAPI documentation available at:
```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

---

**Document Version**: 1.0  
**Last Updated**: June 2025  
**Maintained By**: CTO / Technical Team
