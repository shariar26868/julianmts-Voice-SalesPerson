# 🚀 AI Sales Training Platform - Backend

A powerful **FastAPI-based backend** for an AI-powered sales training platform where salespeople can practice conversations with **multi-agent AI company representatives** using **OpenAI GPT-4** and **ElevenLabs Voice AI**.

---

## ✨ Features

### 🎯 Core Capabilities
- **Multi-Agent AI Conversations**: Practice with 1, 2, or 3 AI representatives simultaneously
- **Realistic Turn-Taking**: Precise conversation flow management with natural interruptions
- **Voice-Enabled**: Full text-to-speech and speech-to-text using ElevenLabs
- **Smart Context Sharing**: Both salesperson and AI have full access to all relevant data
- **Personality-Based Responses**: AI reps respond according to their personality traits (angry, arrogant, soft, analytical, etc.)
- **Auto-Generated Questions**: Top 5 strategic questions generated based on product and company data
- **Complete Audio Recording**: All conversations saved to AWS S3 with full transcripts in MongoDB
- **Web Scraping**: Automatically fetches company data from websites

### 📊 Meeting Modes
- **1-on-1**: Salesperson vs 1 Company Representative
- **1-on-2**: Salesperson vs 2 Company Representatives
- **1-on-3**: Salesperson vs 3 Company Representatives

---

## 🏗️ Architecture

```
Salesman (Voice Input) 
    ↓
OpenAI GPT-4 (Orchestrator)
    ├── Analyzes who should respond
    ├── Manages turn-taking
    └── Handles interruptions
    ↓
AI Representatives (1/2/3 agents)
    ├── Each with unique personality
    ├── Each with different voice
    └── Context-aware responses
    ↓
ElevenLabs TTS → Audio Output
    ↓
AWS S3 (Audio Storage)
MongoDB (Conversation Transcripts)
```

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.9+)
- **AI/ML**: OpenAI GPT-4 Turbo, ElevenLabs Voice AI
- **Database**: MongoDB (Motor async driver)
- **Storage**: AWS S3
- **Web Scraping**: BeautifulSoup4, httpx
- **Audio**: Pydub (for processing)

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- MongoDB (local or Atlas)
- AWS Account with S3 bucket
- OpenAI API Key
- ElevenLabs API Key

### Step 1: Clone & Setup

```bash
cd ai-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file:

```env
# API Keys
OPENAI_API_KEY=sk-your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=sales-training-audio

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sales_training_db

# Application
APP_ENV=development
DEBUG=True
```

### Step 3: Setup AWS S3 Bucket

1. Create an S3 bucket named `sales-training-audio` (or your choice)
2. Configure bucket permissions for your AWS credentials
3. Enable CORS if accessing from frontend

### Step 4: Run the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Salesperson Management

#### Create Salesperson Profile
```http
POST /api/salesperson/create
Content-Type: multipart/form-data

Fields:
- product_name: string
- description: string
- product_url: string (optional)
- materials: files[] (PDF, PPTX, DOC, Images)
```

#### Get Salesperson Data
```http
GET /api/salesperson/{salesperson_id}
```

---

### Company Management

#### Create Company Profile
```http
POST /api/company/create
Content-Type: application/json

{
  "company_url": "https://example.com",
  "auto_fetch": true
}
```

Auto-fetches:
- Company size
- Headquarters
- Revenue
- Industry
- Tech stack
- Open positions
- Latest news

#### Add Company Representative
```http
POST /api/company/{company_id}/representatives
Content-Type: application/json

{
  "name": "John Smith",
  "role": "ceo",
  "tenure_months": 24,
  "personality_traits": ["arrogant", "analytical"],
  "is_decision_maker": true,
  "linkedin_profile": "https://linkedin.com/in/johnsmith",
  "notes": "Very direct, asks tough questions",
  "voice_id": "voice_1"
}
```

#### Get Company Representatives
```http
GET /api/company/{company_id}/representatives
```

---

### Meeting Management

#### Create Meeting
```http
POST /api/meeting/create
Content-Type: application/json

{
  "salesperson_id": "uuid",
  "company_id": "uuid",
  "meeting_mode": "1-on-2",
  "representatives": ["rep_id_1", "rep_id_2"],
  "meeting_goal": "Close a $50k deal",
  "personality": "nice",
  "duration_minutes": 30,
  "difficulty": "intermediate"
}
```

Response includes auto-generated **Top 5 Questions**.

#### Start Meeting
```http
POST /api/meeting/{meeting_id}/start
```

#### End Meeting
```http
POST /api/meeting/{meeting_id}/end
```

---

### Conversation (Real-time AI)

#### Send Message & Get AI Response
```http
POST /api/conversation/send-message
Content-Type: application/json

{
  "meeting_id": "uuid",
  "speaker": "salesperson",
  "message": "Hi, I wanted to discuss our new product",
  "audio_data": null  // Optional: base64 audio
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ai_response": {
      "speaker_id": "rep_1",
      "speaker_name": "John Smith",
      "speaker_role": "ceo",
      "response_text": "We're quite busy. What makes your product different?",
      "audio_url": "https://s3.../audio.mp3",
      "duration_seconds": 6.2
    },
    "turn_number": 2,
    "reasoning": "CEO responds as decision maker"
  }
}
```

#### Get Conversation History
```http
GET /api/conversation/{meeting_id}/history
```

#### Get Analytics
```http
GET /api/conversation/{meeting_id}/analytics
```

Returns:
- Total turns
- Talk time ratio
- Questions asked
- Performance metrics

---

## 🎙️ How It Works

### 1. Setup Phase
```python
# Salesperson uploads product data
POST /api/salesperson/create
  → Uploads PDFs, presentations to S3
  → Stores in MongoDB

# Company data scraped automatically
POST /api/company/create
  → Web scraping fetches company info
  → Stores in MongoDB

# Add AI representatives
POST /api/company/{id}/representatives
  → Configure personalities, roles
  → Assign voices
```

### 2. Meeting Creation
```python
POST /api/meeting/create
  → Validates salesperson, company, reps
  → Generates Top 5 Questions using GPT-4
  → Returns meeting ID
```

### 3. Real-time Conversation
```python
# Salesperson speaks
POST /api/conversation/send-message
  → Stores message + audio in S3/MongoDB
  
  → OpenAI Orchestrator analyzes:
      • Conversation context
      • Representative personalities
      • Who should respond
      • Detect directed questions
  
  → Selected AI Rep generates response
  
  → ElevenLabs TTS creates voice
  
  → Audio uploaded to S3
  
  → Response returned to salesperson
```

### 4. Turn-Taking Logic

**Scenario 1: General Question**
```
Salesman: "What's your biggest challenge right now?"
→ Orchestrator: CFO responds (handles financial concerns)
```

**Scenario 2: Directed Question**
```
Salesman: "John, what do you think about this?"
→ Orchestrator: John (CEO) MUST respond
```

**Scenario 3: Multiple Reps**
```
Salesman asks about budget
→ CFO responds first
→ CEO might interrupt to add strategic perspective
```

---

## 🗄️ Database Schema

### MongoDB Collections

#### `salespeople`
```json
{
  "_id": "uuid",
  "product_name": "CloudSync Pro",
  "product_url": "https://cloudsync.io",
  "description": "Enterprise cloud storage solution",
  "materials": [
    {
      "file_name": "product_deck.pptx",
      "file_url": "s3://bucket/...",
      "file_type": "pptx"
    }
  ],
  "created_at": "2024-02-05T10:00:00Z"
}
```

#### `companies`
```json
{
  "_id": "uuid",
  "company_url": "https://acme.com",
  "company_data": {
    "company_size": "500-1000",
    "headquarters": "San Francisco, CA",
    "revenue": "$50M",
    "industry": "Technology",
    "tech_stack": ["React", "AWS", "MongoDB"],
    "open_positions": 25
  },
  "created_at": "2024-02-05T10:00:00Z"
}
```

#### `representatives`
```json
{
  "_id": "uuid",
  "company_id": "company_uuid",
  "name": "John Smith",
  "role": "ceo",
  "tenure_months": 24,
  "personality_traits": ["arrogant", "analytical"],
  "is_decision_maker": true,
  "voice_id": "voice_1"
}
```

#### `meetings`
```json
{
  "_id": "uuid",
  "salesperson_id": "uuid",
  "company_id": "uuid",
  "meeting_mode": "1-on-2",
  "representative_ids": ["rep1", "rep2"],
  "top_5_questions": ["...", "...", "..."],
  "status": "active",
  "created_at": "2024-02-05T10:00:00Z"
}
```

#### `conversations`
```json
{
  "_id": "uuid",
  "meeting_id": "uuid",
  "turns": [
    {
      "turn_number": 1,
      "speaker": "salesperson",
      "speaker_name": "Alex",
      "text": "Hello, I wanted to discuss...",
      "audio_url": "s3://bucket/meetings/uuid/turn_001.mp3",
      "timestamp": "00:00:15",
      "duration_seconds": 5.2
    }
  ],
  "total_turns": 45,
  "salesperson_talk_time": 900,
  "representatives_talk_time": 900
}
```

---

## 🎨 Personality Types

Representatives can have these personality traits:

- **angry**: Aggressive, challenging tone
- **arrogant**: Dismissive, superiority complex
- **soft**: Encouraging, helpful, patient
- **cold_hearted**: Brief, factual, emotionless
- **nice**: Friendly, warm, supportive
- **analytical**: Data-driven, logical, precise
- **cool**: Relaxed, confident, casual

Voices adjust automatically based on personality!

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use IAM roles** for AWS in production
3. **Enable S3 bucket encryption**
4. **Use presigned URLs** for audio access
5. **Implement rate limiting** on API endpoints
6. **Add authentication** (JWT recommended)

---

## 🧪 Testing

```bash
# Run health check
curl http://localhost:8000/health

# Test salesperson creation
curl -X POST http://localhost:8000/api/salesperson/create \
  -F "product_name=Test Product" \
  -F "description=A test product"
```

---

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app /app/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS EC2 / DigitalOcean

1. Setup server with Python 3.9+
2. Install dependencies
3. Setup MongoDB Atlas (cloud)
4. Configure S3 bucket
5. Run with systemd or PM2

---

## 📈 Performance

- **GPT-4 Response Time**: ~2-3 seconds
- **ElevenLabs TTS**: ~1-2 seconds
- **S3 Upload**: <1 second
- **Total Latency**: ~3-5 seconds per turn

---

## 🤝 Contributing

This is a production-ready backend. Extend it with:
- Authentication (JWT, OAuth)
- Payment integration
- Advanced analytics
- Mobile app support
- Video calling

---

## 📞 Support

For issues or questions, contact the development team.

---

## 📄 License

Proprietary - All rights reserved

---

## 🎉 Quick Start Summary

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env  # Edit with your keys

# 3. Run
uvicorn app.main:app --reload

# 4. Test
curl http://localhost:8000/health
```

**🚀 You're ready to build AI-powered sales training!**