# MailMind — AI Email Assistant

MailMind is an autonomous AI-powered Gmail assistant built using Python, Streamlit, Groq LLMs, and the Gmail API.

It can intelligently read, classify, summarize, search, draft, and send emails using natural language instructions while maintaining persistent memory across sessions.

---

# Features

* Gmail OAuth Authentication
* AI-powered inbox triage
* Autonomous email classification
* Smart reply drafting
* Persistent memory system
* Natural language email search
* Proactive urgent-email draft generation
* Human approval before sending emails
* Gmail thread-aware replies
* Modern Streamlit UI

---

# Tech Stack

* Python
* Streamlit
* Groq API
* Gmail API
* OAuth 2.0
* Google Cloud Console
* python-dotenv

---

# Project Structure

```bash
MailMind/
│
├── app.py
├── agent.py
├── gmail_client.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/mailmind.git
cd mailmind
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the root directory.

```env
GROQ_API_KEY=your_groq_api_key

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret

REDIRECT_URI=http://localhost:8501
```

---

# Google OAuth Setup

## 1. Open Google Cloud Console

Create a new project.

Enable:

* Gmail API

---

## 2. Configure OAuth Consent Screen

Add scopes:

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/userinfo.email
openid
```

---

## 3. Create OAuth Credentials

Create:

* OAuth Client ID
* Application Type: Web Application

Add Authorized Redirect URI:

### Local Development

```text
http://localhost:8501
```

### Streamlit Cloud Deployment

```text
https://your-app-name.streamlit.app
```

---

# Running the Application

```bash
streamlit run app.py
```

---

# AI Capabilities

## Inbox Triage

MailMind automatically categorizes emails into:

* Urgent
* Follow-up
* FYI / Notifications

---

## Autonomous Draft Generation

The assistant proactively drafts replies for urgent emails and waits for user approval before sending.

---

## Persistent Memory

The system remembers:

* sender relationships
* reply tones
* user preferences
* previous interactions

---

# Security

* Secrets are stored using environment variables
* OAuth authentication is used for Gmail access
* Sensitive files are excluded using `.gitignore`

Recommended `.gitignore`:

```gitignore
.env
agent_memory.json
__pycache__/
*.pyc
.streamlit/
```

---

# Deployment

The application can be deployed easily on:

* Streamlit Community Cloud

For deployment:

* Push project to GitHub
* Add secrets in Streamlit Cloud
* Deploy directly from repository

---

# Future Improvements

* Email summarization dashboard
* Calendar integration
* Voice assistant support
* Multi-account Gmail support
* RAG-powered email memory search
* Attachment analysis
* Mobile responsive UI

---

# Screenshots

Add screenshots here after deployment.

---

# License

MIT License

---

# Author

Ajinkya Patil

Built as an AI-powered autonomous email assistant project using LLMs and Gmail APIs.
