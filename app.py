import streamlit as st
import os
import json
import re
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()
# ─────────────────────────────────────────────────────────────────────────────
# ✅ YOUR CREDENTIALS — fill these in
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

st.set_page_config(
    page_title="MailMind — AI Email Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

:root {
    --bg: #f5f5f5;
    --surface: #ffffff;
    --surface2: #f9f9f9;
    --border: #e8e8e8;
    --ink: #111111;
    --ink2: #555555;
    --ink3: #999999;
    --accent: #f26419;
    --accent-light: #fff3ec;
    --accent-dark: #d4530e;
    --radius: 12px;
    --shadow: 0 1px 8px rgba(0,0,0,0.06);
    --shadow-lg: 0 4px 24px rgba(0,0,0,0.10);
}

body { background: var(--bg); }

/* ── Login ── */
.login-outer {
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: #ffffff;
}
.login-card {
    background: var(--surface);
    border-radius: 20px;
    padding: 3rem 2.75rem;
    width: 100%; max-width: 400px;
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--border);
    text-align: center;
}
.login-logo {
    font-size: 2rem; font-weight: 700;
    color: var(--ink); letter-spacing: -1px;
    margin-bottom: 0.35rem;
}
.login-logo span { color: var(--accent); }
.login-tagline { color: var(--ink3); font-size: 0.85rem; margin-bottom: 2.25rem; line-height: 1.5; }
.google-btn {
    display: inline-flex; align-items: center; gap: 10px;
    background: #fff; border: 1.5px solid #e0e0e0;
    border-radius: 10px; padding: 0.7rem 1.75rem;
    font-size: 0.875rem; font-weight: 600; color: #222;
    cursor: pointer; text-decoration: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    width: 100%; justify-content: center;
}
.google-btn:hover { border-color: var(--accent); box-shadow: 0 2px 10px rgba(242,100,25,0.12); }
.google-icon { width: 18px; height: 18px; }
.login-note { font-size: 0.7rem; color: var(--ink3); margin-top: 1.4rem; line-height: 1.6; }

/* ── Topbar ── */
.topbar {
    background: #111111; border-bottom: none;
    padding: 0 1.5rem; height: 54px;
    display: flex; align-items: center; gap: 1rem;
    position: sticky; top: 0; z-index: 200;
}
.topbar-logo { font-weight: 700; font-size: 1.1rem; letter-spacing: -0.3px; color: #ffffff; }
.topbar-logo span { color: var(--accent); }
.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 0.75rem; }
.user-chip {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.78rem; color: #aaaaaa;
    background: #222222; border: 1px solid #333333;
    border-radius: 20px; padding: 4px 12px 4px 6px;
}
.avatar {
    width: 24px; height: 24px; background: var(--accent);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 0.65rem;
}

/* ── Layout ── */
.app-body { display: flex; height: calc(100vh - 54px); overflow: hidden; }
.sidenav {
    width: 220px; flex-shrink: 0;
    background: #ffffff; border-right: 1px solid var(--border);
    padding: 1rem 0.6rem; display: flex; flex-direction: column; gap: 2px;
    overflow-y: auto;
}
.main { flex: 1; overflow-y: auto; padding: 1.75rem 2rem; background: var(--bg); }

/* ── Nav items ── */
.nav-lbl {
    font-size: 0.62rem; font-weight: 700; color: var(--ink3);
    text-transform: uppercase; letter-spacing: 0.8px;
    padding: 0.5rem 0.75rem 0.25rem;
}

/* ── Page headers ── */
.page-title { font-size: 1.3rem; font-weight: 700; color: var(--ink); letter-spacing: -0.4px; margin-bottom: 0.15rem; }
.page-sub { font-size: 0.8rem; color: var(--ink3); margin-bottom: 1.4rem; }

/* ── Chat ── */
.bubble-user {
    background: var(--ink); color: white;
    padding: 0.65rem 0.95rem; border-radius: 18px 18px 4px 18px;
    font-size: 0.85rem; line-height: 1.55; max-width: 76%;
    margin-left: auto;
}
.bubble-ai-wrap { display: flex; gap: 0.55rem; align-items: flex-start; margin-right: auto; max-width: 82%; }
.bubble-ai-icon {
    width: 24px; height: 24px; background: var(--accent); border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 0.6rem; flex-shrink: 0; margin-top: 2px;
}
.bubble-ai {
    background: var(--surface); border: 1px solid var(--border);
    padding: 0.75rem 1rem; border-radius: 4px 18px 18px 18px;
    font-size: 0.875rem; line-height: 1.68; color: var(--ink);
    box-shadow: var(--shadow);
}
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1.1rem; }
.chip {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--ink2); padding: 4px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 500;
}
.tool-log {
    font-family: 'JetBrains Mono', monospace; font-size: 0.71rem; color: var(--ink2);
    background: var(--surface2); border-left: 2px solid var(--accent);
    padding: 3px 9px; border-radius: 0 5px 5px 0; margin: 2px 0;
}
.empty { text-align: center; padding: 4rem 0; color: var(--ink3); }
.empty-icon { font-size: 2.2rem; margin-bottom: 0.5rem; }
.empty-text { font-size: 0.83rem; }

/* ── Email cards ── */
.ecard {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.8rem 1rem;
    transition: border-color 0.12s, box-shadow 0.12s;
    margin-bottom: 0.4rem;
}
.ecard:hover { box-shadow: var(--shadow); border-color: #cccccc; }
.ecard.sel { border-color: var(--accent); background: var(--accent-light); }
.ec-from { font-size: 0.82rem; font-weight: 600; color: var(--ink); }
.ec-subj { font-size: 0.77rem; color: var(--ink2); margin-top: 2px; }
.ec-snip { font-size: 0.71rem; color: var(--ink3); margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.udot { display:inline-block; width:6px; height:6px; background:var(--accent); border-radius:50%; margin-right:5px; vertical-align:middle; }

/* ── Detail ── */
.detail {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.35rem; box-shadow: var(--shadow);
}
.detail-subj { font-size: 1rem; font-weight: 700; color: var(--ink); margin-bottom: 0.5rem; }
.detail-meta { font-size: 0.75rem; color: var(--ink3); line-height: 1.85; }
.detail-body {
    font-size: 0.82rem; color: var(--ink); line-height: 1.75;
    border-top: 1px solid var(--border); margin-top: 1rem; padding-top: 1rem;
    white-space: pre-wrap; max-height: 360px; overflow-y: auto;
}

/* ── Compose ── */
.ai-panel {
    background: var(--ink); border-radius: var(--radius); padding: 1.25rem; color: #cccccc;
}
.ai-panel-title { font-size: 0.85rem; font-weight: 600; color: white; margin-bottom: 0.3rem; }
.ai-panel-sub { font-size: 0.73rem; color: #888888; margin-bottom: 1rem; }

/* ── Triage panel ── */
.triage-wrap {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.25rem 1.4rem;
    box-shadow: var(--shadow); margin-bottom: 1.4rem;
}
.triage-header {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.75rem; font-weight: 700; color: var(--ink);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.85rem;
}
.triage-header-dot {
    width: 8px; height: 8px; background: var(--accent); border-radius: 50%; display: inline-block;
}
.triage-briefing {
    font-size: 0.85rem; color: var(--ink); line-height: 1.65;
    background: var(--accent-light); border-radius: 8px;
    padding: 0.7rem 0.95rem; margin-bottom: 1rem;
    border-left: 3px solid var(--accent);
}
.triage-bucket { margin-bottom: 0.85rem; }
.triage-bucket-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; margin-bottom: 0.4rem;
}
.triage-row {
    display: flex; align-items: flex-start; gap: 0.55rem;
    font-size: 0.78rem; padding: 0.4rem 0.55rem;
    border-radius: 7px; margin-bottom: 3px;
    background: var(--surface2); border: 1px solid var(--border);
}
.triage-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.triage-dot.urgent   { background: #e63946; }
.triage-dot.followup { background: #f4a261; }
.triage-dot.fyi      { background: #aaaaaa; }
.triage-from { font-weight: 600; color: var(--ink); white-space: nowrap; }
.triage-subj { color: var(--ink2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.triage-reason { font-size: 0.7rem; color: var(--ink3); flex-shrink: 0; max-width: 200px; text-align: right; }

/* ── Proactive draft approval cards ── */
.drafts-section { margin-bottom: 1.6rem; }
.drafts-section-header {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.75rem; font-weight: 700; color: var(--ink);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 0.85rem;
}
.draft-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1rem 1.15rem;
    box-shadow: var(--shadow);
    margin-bottom: 0.75rem;
    border-left: 3px solid var(--accent);
}
.draft-card-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 0.6rem; gap: 1rem;
}
.draft-card-meta { flex: 1; }
.draft-card-from { font-size: 0.83rem; font-weight: 700; color: var(--ink); }
.draft-card-subj { font-size: 0.75rem; color: var(--ink2); margin-top: 2px; }
.draft-card-reason {
    font-size: 0.7rem; color: var(--accent); font-weight: 600;
    background: var(--accent-light); border-radius: 20px;
    padding: 2px 9px; white-space: nowrap; align-self: flex-start;
}
.draft-card-body {
    font-size: 0.8rem; color: var(--ink); line-height: 1.65;
    background: var(--surface2); border-radius: 7px;
    padding: 0.7rem 0.85rem; white-space: pre-wrap;
    border: 1px solid var(--border); max-height: 150px; overflow-y: auto;
    margin-bottom: 0.7rem;
}
.draft-sent   { border-left-color: #aaaaaa; opacity: 0.55; }
.draft-reject { border-left-color: #cccccc; opacity: 0.45; }

/* ── No-reply badge ── */
.no-reply-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f5f5f5; border: 1px solid #dddddd;
    color: #444444; border-radius: 20px;
    padding: 4px 13px; font-size: 0.75rem; font-weight: 600;
    margin-bottom: 0.85rem;
}
.no-reply-reason {
    font-size: 0.72rem; color: var(--ink3); margin-bottom: 0.75rem;
    font-style: italic;
}

/* ── Input overrides ── */
.stTextInput input, .stTextArea textarea {
    background: #ffffff !important; border: 1.5px solid var(--border) !important;
    border-radius: 9px !important; font-family: 'Inter', sans-serif !important;
    color: var(--ink) !important; font-size: 0.85rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(242,100,25,0.08) !important;
}
.stButton > button {
    background: var(--ink) !important; color: white !important; border: none !important;
    border-radius: 9px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    padding: 0.5rem 1.25rem !important; transition: background 0.14s !important;
}
.stButton > button:hover { background: #333333 !important; }
div[data-testid="stExpander"] {
    background: var(--surface2) !important; border: 1px solid var(--border) !important; border-radius: 9px !important;
}

/* ── Landing hero ── */
.landing-greeting {
    font-size: 1.35rem; font-weight: 700; color: var(--ink); letter-spacing: -0.4px;
    margin-bottom: 0.2rem;
}
.landing-greeting span { color: var(--accent); }
.landing-sub { font-size: 0.8rem; color: var(--ink3); margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def build_google_auth_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_code_for_tokens(code: str):
    import urllib.request
    data = urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def build_credentials(token_data: dict):
    from google.oauth2.credentials import Credentials
    return Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )


def get_query_params():
    try:
        params = st.query_params
        return dict(params)
    except Exception:
        return {}


# ── Autonomous Triage ────────────────────────────────────────────────────────
def run_triage(agent, emails):
    """
    Agentic feature: automatically classify unread emails into urgency buckets
    the moment the user logs in — no instruction needed.

    Returns a dict:
      {
        "urgency":    [ {email_id, from, subject, reason}, ... ],
        "follow_up":  [ ... ],
        "fyi":        [ ... ],
        "briefing":   "one-paragraph plain-English summary"
      }
    """
    if not emails:
        return None

    # Build a minimal list — only IDs + short subjects to reduce token load
    # and minimise special characters in the JSON the model must produce.
    slim_prompt = [
        {
            "id":      e["id"],
            "from":    e["from"].split("<")[0].strip()[:40],
            "subject": e["subject"][:60],
            "snippet": e["snippet"][:80],
        }
        for e in emails[:10]   # 10 is safer for 1200-token budget
    ]

    prompt = (
        "Triage the inbox emails below into three buckets.\n\n"
        "Rules:\n"
        "  URGENT   — needs a reply or action TODAY\n"
        "  FOLLOW_UP — worth reading, can wait\n"
        "  FYI      — notifications, alerts, newsletters, social, bank statements — NO reply needed\n\n"
        "Emails (JSON):\n" + json.dumps(slim_prompt) + "\n\n"
        "Return ONLY a JSON object with this exact structure. "
        "Use the email's id field exactly as given. "
        "Keep every string value under 80 characters. "
        "Do NOT include newlines or special characters inside string values. "
        "Do NOT add markdown fences or any text outside the JSON.\n\n"
        "{\n"
        '  "urgency":   [{"email_id":"<id>","from":"<sender>","subject":"<subj>","reason":"<why>"}],\n'
        '  "follow_up": [{"email_id":"<id>","from":"<sender>","subject":"<subj>","reason":"<why>"}],\n'
        '  "fyi":       [{"email_id":"<id>","from":"<sender>","subject":"<subj>","reason":"<why>"}],\n'
        '  "briefing":  "<2 sentences about inbox state>"\n'
        "}"
    )

    def _safe_parse(raw: str) -> dict | None:
        """
        Try several increasingly lenient strategies to extract valid JSON
        from a string that may have markdown fences, trailing commas,
        truncated content, or unescaped quotes in values.
        """
        import re as _re

        # 1. Strip markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()

        # 2. Direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 3. Extract the outermost {...} block and try again
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        if m:
            candidate = m.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

            # 4. Remove trailing commas before ] or } (common LLM mistake)
            fixed = _re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

            # 5. Truncated JSON — find the last complete top-level key and
            #    close the object manually so we keep whatever was parsed.
            try:
                # Keep only complete "key": [...] pairs
                partial = _re.sub(
                    r',?\s*"(urgency|follow_up|fyi|briefing)"\s*:(?![^"]*"(?:urgency|follow_up|fyi|briefing)")',
                    lambda mo: mo.group(0),
                    fixed
                )
                # Find all complete array/string values per key
                result: dict = {"urgency": [], "follow_up": [], "fyi": [], "briefing": ""}
                for key in ("urgency", "follow_up", "fyi"):
                    km = _re.search(
                        rf'"{key}"\s*:\s*(\[.*?\])',
                        fixed, _re.DOTALL
                    )
                    if km:
                        try:
                            result[key] = json.loads(
                                _re.sub(r",\s*([}\]])", r"\1", km.group(1))
                            )
                        except Exception:
                            pass
                bm = _re.search(r'"briefing"\s*:\s*"([^"]*)"', fixed)
                if bm:
                    result["briefing"] = bm.group(1)
                # Return partial result if we got at least something
                if any(result[k] for k in ("urgency", "follow_up", "fyi")):
                    return result
            except Exception:
                pass

        return None

    try:
        from groq import Groq
        client = Groq(api_key=agent.client.api_key)
        r = client.chat.completions.create(
            model=agent.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1400,          # slightly more headroom
            temperature=0,            # deterministic → less creative punctuation
        )
        raw = r.choices[0].message.content.strip()
        parsed = _safe_parse(raw)
        if parsed:
            # Ensure all expected keys exist
            parsed.setdefault("urgency",   [])
            parsed.setdefault("follow_up", [])
            parsed.setdefault("fyi",       [])
            parsed.setdefault("briefing",  "Inbox triaged.")
            return parsed
        # All strategies failed — return graceful empty triage
        return {"urgency": [], "follow_up": [], "fyi": [], "briefing": "Triage completed (some emails could not be classified)."}
    except Exception as e:
        return {"urgency": [], "follow_up": [], "fyi": [], "briefing": f"Triage unavailable: {e}"}


def generate_proactive_drafts(agent, gmail, urgent_items, all_emails):
    """
    Agentic feature: for each urgent email, autonomously write a draft reply
    and queue it for user approval — without being asked.

    Returns a list of draft dicts ready to display in the approval UI.
    """
    drafts = []
    # Build a quick lookup: email_id -> full slim email from inbox fetch
    email_map = {e["id"]: e for e in all_emails}

    for item in urgent_items[:3]:   # cap at 3 to respect TPM
        email_id = item.get("email_id")
        if not email_id:
            continue
        try:
            # Fetch full email body for drafting
            em = gmail.get_email_by_id(email_id)
            if not em:
                continue

            # ── Skip emails that don't need a reply ──────────────────────────
            try:
                classification = agent.classify_email(email_id)
                if not classification.get("needs_reply", True):
                    continue   # silently skip — no draft for bank alerts, etc.
            except Exception:
                pass  # classification failed; proceed to draft anyway

            # Pull sender memory to personalise the draft
            import re as _re
            raw_from = em.get("from", "")
            m = _re.search(r"<([^>]+)>", raw_from)
            addr = m.group(1).lower() if m else raw_from.lower().strip()
            profile = agent.memory.get_sender(addr)
            prefs   = agent.memory.get_all_preferences()

            hints = []
            if profile.get("tone"):
                hints.append(f"Use a {profile['tone']} tone.")
            if profile.get("relationship"):
                hints.append(f"This person is your {profile['relationship']}.")
            if prefs.get("signature"):
                hints.append(f"End with: {prefs['signature']}")
            if prefs.get("reply_tone") and not profile.get("tone"):
                hints.append(f"Default tone: {prefs['reply_tone']}.")
            memory_hint = " ".join(hints)

            reason = item.get("reason", "urgent email requiring a reply")
            prompt = (
                f"Write a professional, concise reply to this email.\n"
                f"From: {em['from']}\nSubject: {em['subject']}\n"
                f"Body:\n{(em.get('body') or '')[:1200]}\n\n"
                f"Context: This email was flagged as urgent because: {reason}.\n"
                + (f"Memory: {memory_hint}\n" if memory_hint else "")
                + "Return ONLY the reply body text. No subject line, no preamble."
            )

            from groq import Groq
            client = Groq(api_key=agent.client.api_key)
            r = client.chat.completions.create(
                model=agent.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            draft_body = r.choices[0].message.content.strip()

            drafts.append({
                "email_id":         email_id,
                "from":             em.get("from", ""),
                "subject":          em.get("subject", ""),
                "to":               em.get("from", ""),
                "reply_subject":    f"Re: {em.get('subject', '')}",
                "draft":            draft_body,
                "thread_id":        em.get("thread_id", ""),
                "reply_message_id": em.get("message_id_header", ""),
                "reason":           reason,
                "status":           "pending",
            })

        except Exception as e:
            # Non-fatal — skip this email if drafting fails
            drafts.append({
                "email_id": email_id,
                "from":     item.get("from", ""),
                "subject":  item.get("subject", ""),
                "draft":    f"[Draft failed: {e}]",
                "status":   "error",
            })

    return drafts


# ── Session defaults ──────────────────────────────────────────────────────────
def init():
    defaults = {
        "logged_in": False,
        "user_email": "",
        "gmail_client": None,
        "agent": None,
        "tab": "home",
        "chat_history": [],
        "inbox_emails": [],
        "selected_email": None,
        "compose_to": "",
        "compose_subject": "",
        "compose_body": "",
        # Autonomous triage — runs once on login, persists for the session
        "triage_done": False,
        "triage_result": None,   # {"urgency":[], "follow_up":[], "fyi":[], "briefing":""}
        # Proactive drafts — agent auto-writes replies for urgent emails
        # Each entry: {email_id, from, subject, to, reply_subject, draft, thread_id, reply_message_id, status}
        # status: "pending" | "sent" | "rejected"
        "pending_drafts": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ── Handle OAuth callback ─────────────────────────────────────────────────────
if not st.session_state.logged_in:
    params = get_query_params()
    code = params.get("code")
    if isinstance(code, list):
        code = code[0]

    if code:
        with st.spinner("Completing sign-in…"):
            try:
                token_data = exchange_code_for_tokens(code)
                creds = build_credentials(token_data)

                from gmail_client import GmailClient
                from agent import EmailAgent

                gmail = GmailClient(creds)
                profile = gmail.get_profile()
                agent = EmailAgent(groq_api_key=GROQ_API_KEY, gmail_client=gmail)

                st.session_state.logged_in = True
                st.session_state.user_email = profile.get("emailAddress", "")
                st.session_state.gmail_client = gmail
                st.session_state.agent = agent
                emails = gmail.list_unread_emails(15)
                st.session_state.inbox_emails = emails

                # Autonomous triage — classify inbox immediately on login
                triage = run_triage(agent, emails)
                st.session_state.triage_result = triage
                st.session_state.triage_done = True

                # Proactive drafts — agent writes replies for urgent emails automatically
                urgent_items = triage.get("urgency", []) if triage else []
                if urgent_items:
                    st.session_state.pending_drafts = generate_proactive_drafts(
                        agent, gmail, urgent_items, emails
                    )

                # Clear the code from URL
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Sign-in failed: {e}")
                st.query_params.clear()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    auth_url = build_google_auth_url()

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='height:20vh'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="login-card">
            <div class="login-logo">Mail<span>Mind</span></div>
            <div class="login-tagline">Your AI-powered Gmail assistant.<br>Read, summarize, draft, and send emails.</div>
            <a href="{auth_url}" class="google-btn">
                <svg class="google-icon" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google
            </a>
            <div class="login-note">
                We only request access to your Gmail.<br>
                Your data is never stored on our servers.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

# ── Topbar ────────────────────────────────────────────────────────────────────
initials = st.session_state.user_email[:2].upper()
st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">Mail<span>Mind</span></div>
    <div style="flex:1"></div>
    <div class="topbar-right">
        <div class="user-chip">
            <div class="avatar">{initials}</div>
            {st.session_state.user_email}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Body ──────────────────────────────────────────────────────────────────────
col_nav, col_main = st.columns([0.75, 4])

with col_nav:
    st.markdown("<div style='padding-top:0.75rem'>", unsafe_allow_html=True)
    st.markdown('<div class="nav-lbl">Navigation</div>', unsafe_allow_html=True)

    for key, icon, label in [("home","✦","Home"), ("chat","💬","Chat"), ("inbox","📬","Inbox"), ("compose","✍️","Compose")]:
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.tab = key
            st.rerun()

    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-lbl">Actions</div>', unsafe_allow_html=True)

    if st.button("🔄  Refresh", use_container_width=True):
        with st.spinner("Fetching & triaging…"):
            emails = st.session_state.gmail_client.list_unread_emails(15)
            st.session_state.inbox_emails = emails
            # Re-run autonomous triage on refresh
            triage = run_triage(st.session_state.agent, emails)
            st.session_state.triage_result = triage
            st.session_state.triage_done = True
            # Re-generate proactive drafts for new urgent items
            urgent_items = triage.get("urgency", []) if triage else []
            if urgent_items:
                st.session_state.pending_drafts = generate_proactive_drafts(
                    st.session_state.agent, st.session_state.gmail_client, urgent_items, emails
                )
        st.rerun()

    if st.button("🚪  Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# CHAT TAB
# ══════════════════════════════════════════════════
with col_main:
    if st.session_state.tab == "home":
        st.markdown('<div class="page-title">Home</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Your inbox, triaged and ready.</div>', unsafe_allow_html=True)

        # ── AI Inbox Briefing ────────────────────────────────────────────────
        if st.session_state.triage_done and st.session_state.triage_result:
            tr = st.session_state.triage_result
            urgent   = tr.get("urgency", [])
            followup = tr.get("follow_up", [])
            fyi      = tr.get("fyi", [])
            briefing = tr.get("briefing", "")

            rows_html = ""

            if urgent:
                rows_html += '<div class="triage-bucket"><div class="triage-bucket-label" style="color:#d94f3d">🔴 Urgent — needs action today</div>'
                for item in urgent[:4]:
                    sender = (item.get("from","") or "").split("<")[0].strip()[:24]
                    subj   = (item.get("subject","") or "")[:48]
                    reason = (item.get("reason","") or "")[:50]
                    rows_html += f'<div class="triage-row"><div class="triage-dot urgent"></div><div class="triage-from">{sender}</div><div class="triage-subj">{subj}</div><div class="triage-reason">{reason}</div></div>'
                rows_html += "</div>"

            if followup:
                rows_html += '<div class="triage-bucket"><div class="triage-bucket-label" style="color:#e09c2f">🟡 Follow-up — review soon</div>'
                for item in followup[:3]:
                    sender = (item.get("from","") or "").split("<")[0].strip()[:24]
                    subj   = (item.get("subject","") or "")[:48]
                    reason = (item.get("reason","") or "")[:50]
                    rows_html += f'<div class="triage-row"><div class="triage-dot followup"></div><div class="triage-from">{sender}</div><div class="triage-subj">{subj}</div><div class="triage-reason">{reason}</div></div>'
                rows_html += "</div>"

            if fyi:
                rows_html += '<div class="triage-bucket"><div class="triage-bucket-label" style="color:#6baa6b">🟢 FYI — low priority</div>'
                for item in fyi[:3]:
                    sender = (item.get("from","") or "").split("<")[0].strip()[:24]
                    subj   = (item.get("subject","") or "")[:48]
                    rows_html += f'<div class="triage-row"><div class="triage-dot fyi"></div><div class="triage-from">{sender}</div><div class="triage-subj">{subj}</div></div>'
                rows_html += "</div>"

            st.markdown(f"""
            <div class="triage-wrap">
                <div class="triage-header"><span class="triage-header-dot"></span> AI Inbox Briefing</div>
                <div class="triage-briefing">{briefing}</div>
                {rows_html}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="triage-wrap">
                <div class="triage-header"><span class="triage-header-dot"></span> AI Inbox Briefing</div>
                <div class="triage-briefing" style="color:var(--ink3)">No triage data yet — click Refresh to analyse your inbox.</div>
            </div>""", unsafe_allow_html=True)

        # ── AI Drafted Mails ─────────────────────────────────────────────────
        st.markdown('<div style="height:0.25rem"></div>', unsafe_allow_html=True)

        pending_home = [d for d in st.session_state.pending_drafts if d.get("status") == "pending"]
        done_home    = [d for d in st.session_state.pending_drafts if d.get("status") in ("sent", "rejected")]

        if st.session_state.pending_drafts:
            st.markdown('<div class="drafts-section">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="drafts-section-header"><span style="display:inline-block;width:8px;height:8px;background:var(--accent);border-radius:50%;margin-right:6px"></span>AI Drafted Mails &nbsp;·&nbsp; {len(pending_home)} pending</div>',
                unsafe_allow_html=True
            )

            for idx, draft in enumerate(st.session_state.pending_drafts):
                status = draft.get("status", "pending")
                card_cls = {"sent": "draft-sent", "rejected": "draft-reject"}.get(status, "")
                sender = (draft.get("from") or "").split("<")[0].strip()
                subj   = draft.get("subject", "")
                reason = draft.get("reason", "urgent")
                body   = draft.get("draft", "")

                if status == "error":
                    st.markdown(
                        f'<div class="draft-card {card_cls}"><div class="draft-card-from">⚠️ {sender}</div>'
                        f'<div class="draft-card-subj">{subj}</div>'
                        f'<div style="font-size:0.78rem;color:#d94f3d;margin-top:0.5rem">{body}</div></div>',
                        unsafe_allow_html=True
                    )
                    continue

                badge = {"sent": "✅ Sent", "rejected": "✕ Rejected"}.get(status, "")

                st.markdown(f"""
                <div class="draft-card {card_cls}">
                    <div class="draft-card-header">
                        <div class="draft-card-meta">
                            <div class="draft-card-from">{sender} {badge}</div>
                            <div class="draft-card-subj">Re: {subj}</div>
                        </div>
                        <div class="draft-card-reason">🔴 {reason[:55]}</div>
                    </div>
                    <div class="draft-card-body">{body}</div>
                </div>""", unsafe_allow_html=True)

                if status == "pending":
                    col_edit, col_send, col_reject = st.columns([2, 1, 1])

                    with col_edit:
                        edited = st.text_area(
                            "Edit draft", value=body, height=100,
                            key=f"home_edit_{idx}", label_visibility="collapsed"
                        )

                    with col_send:
                        if st.button("📤 Send", key=f"home_send_{idx}", use_container_width=True):
                            try:
                                thread_id = draft.get("thread_id") or None
                                reply_mid = draft.get("reply_message_id") or None
                                st.session_state.gmail_client.send_email(
                                    to=draft["to"],
                                    subject=draft["reply_subject"],
                                    body=edited,
                                    thread_id=thread_id,
                                    reply_message_id=reply_mid,
                                )
                                st.session_state.pending_drafts[idx]["status"] = "sent"
                                st.session_state.pending_drafts[idx]["draft"]  = edited
                                st.session_state.agent.memory.log_action(
                                    "proactive_send", f"to {draft['to']} — {subj[:50]}"
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Send failed: {e}")

                    with col_reject:
                        if st.button("✕ Reject", key=f"home_reject_{idx}", use_container_width=True):
                            st.session_state.pending_drafts[idx]["status"] = "rejected"
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="drafts-section">
                <div class="drafts-section-header"><span style="display:inline-block;width:8px;height:8px;background:var(--accent);border-radius:50%;margin-right:6px"></span>AI Drafted Mails</div>
                <div class="triage-wrap" style="margin-bottom:0">
                    <div class="triage-briefing" style="color:var(--ink3);margin:0">No AI-drafted mails yet. Refresh to check for urgent emails.</div>
                </div>
            </div>""", unsafe_allow_html=True)

    elif st.session_state.tab == "chat":
        st.markdown('<div class="page-title">Chat</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Ask anything about your emails in plain English.</div>', unsafe_allow_html=True)

        # History
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="empty">
                <div class="empty-icon">✦</div>
                <div class="empty-text">Ask me anything about your emails</div>
            </div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div style="display:flex;justify-content:flex-end;margin:0.5rem 0"><div class="bubble-user">{msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="bubble-ai-wrap" style="margin:0.5rem 0">
                    <div class="bubble-ai-icon">AI</div>
                    <div class="bubble-ai">{msg["content"] or ""}</div>
                </div>""", unsafe_allow_html=True)
                if msg.get("logs"):
                    with st.expander("🔧 Agent steps"):
                        for log in msg["logs"]:
                            st.markdown(f'<div class="tool-log">{log}</div>', unsafe_allow_html=True)

        # Input
        prefill = st.session_state.pop("_prefill", "")
        user_input = st.text_area("Message", value=prefill, placeholder="e.g. Summarize my unread emails…", height=80, label_visibility="collapsed")
        c1, c2 = st.columns([1, 6])
        with c1:
            send = st.button("Send →", use_container_width=True)
        with c2:
            if st.session_state.chat_history:
                if st.button("Clear", use_container_width=False):
                    st.session_state.chat_history = []
                    st.rerun()

        if send and user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Thinking…"):
                try:
                    result, logs = st.session_state.agent.run(user_input.strip())
                    st.session_state.chat_history.append({"role": "ai", "content": result, "logs": logs})
                except Exception as e:
                    st.session_state.chat_history.append({"role": "ai", "content": f"❌ {e}", "logs": []})
            st.rerun()

    # ══════════════════════════════════════════════════
    # INBOX TAB
    # ══════════════════════════════════════════════════
    elif st.session_state.tab == "inbox":
        unread = sum(1 for e in st.session_state.inbox_emails if e.get("unread"))
        st.markdown('<div class="page-title">Inbox</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="page-sub">{unread} unread · {len(st.session_state.inbox_emails)} shown</div>', unsafe_allow_html=True)

        if not st.session_state.inbox_emails:
            st.markdown('<div class="empty"><div class="empty-icon">📭</div><div class="empty-text">No emails. Click Refresh.</div></div>', unsafe_allow_html=True)
        else:
            left, right = st.columns([1, 1.45])
            with left:
                for i, em in enumerate(st.session_state.inbox_emails):
                    sender = (em["from"].split("<")[0].strip() or em["from"])[:28]
                    subj   = (em["subject"] or "(No Subject)")[:40]
                    snip   = (em["snippet"] or "")[:65]
                    is_sel = (st.session_state.selected_email or {}).get("id") == em["id"]
                    dot = '<span class="udot"></span>' if em.get("unread") else ""
                    sel_cls = "sel" if is_sel else ""

                    st.markdown(f"""
                    <div class="ecard {sel_cls}">
                        <div class="ec-from">{dot}{sender}</div>
                        <div class="ec-subj">{subj}</div>
                        <div class="ec-snip">{snip}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("Open", key=f"open_{i}"):
                        st.session_state.selected_email = em
                        st.rerun()

            with right:
                em = st.session_state.selected_email
                if em:
                    st.markdown(f"""
                    <div class="detail">
                        <div class="detail-subj">{em['subject']}</div>
                        <div class="detail-meta">
                            From: {em['from']}<br>To: {em['to']}<br>Date: {em['date']}
                        </div>
                        <div class="detail-body">{em['body'] or '(No body)'}</div>
                    </div>""", unsafe_allow_html=True)

                    # ── Classify the email (cached per email id) ──────────────
                    cache_key = f"_classify_{em['id']}"
                    if cache_key not in st.session_state:
                        with st.spinner("Checking if reply is needed…"):
                            try:
                                st.session_state[cache_key] = st.session_state.agent.classify_email(em["id"])
                            except Exception:
                                st.session_state[cache_key] = {"needs_reply": True, "category": "unknown", "reason": ""}

                    classification = st.session_state[cache_key]
                    needs_reply    = classification.get("needs_reply", True)
                    cls_reason     = classification.get("reason", "")
                    cls_category   = classification.get("category", "")

                    st.markdown("<br>", unsafe_allow_html=True)

                    if not needs_reply:
                        # Show no-reply badge with reason
                        st.markdown(
                            f'<div class="no-reply-badge">✅ No Reply Needed &nbsp;·&nbsp; {cls_category}</div>'
                            f'<div class="no-reply-reason">{cls_reason}</div>',
                            unsafe_allow_html=True
                        )
                        bb_col, bc_col = st.columns(2)
                        with bb_col:
                            if st.button("✅ Mark Read"):
                                st.session_state.gmail_client.mark_as_read(em['id'])
                                st.session_state.inbox_emails = [x for x in st.session_state.inbox_emails if x['id'] != em['id']]
                                st.session_state.selected_email = None
                                st.session_state.pop(cache_key, None)
                                st.rerun()
                        with bc_col:
                            if st.button("✕ Close"):
                                st.session_state.selected_email = None
                                st.rerun()
                        # Override option — user can still force a draft
                        with st.expander("✍️ Reply anyway"):
                            st.caption("This email was classified as not needing a reply. You can still draft one manually.")
                            if st.button("Draft Reply Anyway", key="force_draft"):
                                with st.spinner("Drafting…"):
                                    result, _ = st.session_state.agent.run(
                                        f"Draft a professional reply to email ID {em['id']} from {em['from']} about '{em['subject']}'. The user has explicitly requested a reply despite this being a {cls_category} email."
                                    )
                                    try:
                                        parsed = json.loads(result)
                                        body = parsed.get("draft", result)
                                        to   = parsed.get("to", em["from"])
                                        subj = parsed.get("subject", f"Re: {em['subject']}")
                                    except Exception:
                                        body = result
                                        to_list = re.findall(r'[\w.+\-]+@[\w\-]+\.[a-z]+', em['from'])
                                        to   = to_list[0] if to_list else em['from']
                                        subj = f"Re: {em['subject']}"
                                    st.session_state.compose_to      = to
                                    st.session_state.compose_subject = subj
                                    st.session_state.compose_body    = body
                                    st.session_state.tab             = "compose"
                                st.rerun()
                    else:
                        ba, bb, bc = st.columns(3)
                        with ba:
                            if st.button("✍️ AI Draft Reply"):
                                with st.spinner("Drafting…"):
                                    result, _ = st.session_state.agent.run(
                                        f"Draft a professional reply to email ID {em['id']} from {em['from']} about '{em['subject']}'."
                                    )
                                    try:
                                        parsed = json.loads(result)
                                        body = parsed.get("draft", result)
                                        to = parsed.get("to", em["from"])
                                        subj = parsed.get("subject", f"Re: {em['subject']}")
                                    except Exception:
                                        body = result
                                        to_list = re.findall(r'[\w.+\-]+@[\w\-]+\.[a-z]+', em['from'])
                                        to = to_list[0] if to_list else em['from']
                                        subj = f"Re: {em['subject']}"
                                    st.session_state.compose_to = to
                                    st.session_state.compose_subject = subj
                                    st.session_state.compose_body = body
                                    st.session_state.tab = "compose"
                                st.rerun()
                        with bb:
                            if st.button("✅ Mark Read"):
                                st.session_state.gmail_client.mark_as_read(em['id'])
                                st.session_state.inbox_emails = [x for x in st.session_state.inbox_emails if x['id'] != em['id']]
                                st.session_state.selected_email = None
                                st.session_state.pop(cache_key, None)
                                st.rerun()
                        with bc:
                            if st.button("✕ Close"):
                                st.session_state.selected_email = None
                                st.rerun()
                else:
                    st.markdown('<div class="empty"><div class="empty-icon">👈</div><div class="empty-text">Select an email to read it</div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # COMPOSE TAB
    # ══════════════════════════════════════════════════
    elif st.session_state.tab == "compose":
        st.markdown('<div class="page-title">Compose</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Write manually or let AI draft it.</div>', unsafe_allow_html=True)

        cf, ca = st.columns([1.2, 1])
        with cf:
            to_v   = st.text_input("To",      value=st.session_state.compose_to,      placeholder="recipient@example.com")
            sub_v  = st.text_input("Subject", value=st.session_state.compose_subject,  placeholder="Subject line")
            body_v = st.text_area("Body",     value=st.session_state.compose_body,     height=260, placeholder="Your message…")
            s1, s2 = st.columns(2)
            with s1:
                if st.button("📤 Send", use_container_width=True):
                    if not to_v or not sub_v or not body_v:
                        st.error("Fill in all fields.")
                    else:
                        with st.spinner("Sending…"):
                            try:
                                st.session_state.gmail_client.send_email(to_v, sub_v, body_v)
                                st.success(f"✅ Sent to {to_v}")
                                st.session_state.compose_to = st.session_state.compose_subject = st.session_state.compose_body = ""
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
            with s2:
                if st.button("🗑 Clear", use_container_width=True):
                    st.session_state.compose_to = st.session_state.compose_subject = st.session_state.compose_body = ""
                    st.rerun()

        with ca:
            st.markdown("""
            <div class="ai-panel">
                <div class="ai-panel-title">✦ AI Writing Assistant</div>
                <div class="ai-panel-sub">Describe what you want to write — AI drafts it instantly.</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            ai_p = st.text_area("Describe", placeholder="e.g. Write a follow-up to sarah@company.com asking for the Q3 report status", height=130, label_visibility="collapsed")
            if st.button("✨ Generate", use_container_width=True):
                if ai_p.strip():
                    with st.spinner("Generating…"):
                        result, _ = st.session_state.agent.run(
                            f"Help compose an email: {ai_p}. Return ONLY the email body. No subject line."
                        )
                        st.session_state.compose_body = result
                        found = re.findall(r'[\w.+\-]+@[\w\-]+\.[a-z]+', ai_p)
                        if found and not st.session_state.compose_to:
                            st.session_state.compose_to = found[0]
                    st.rerun()
                else:
                    st.warning("Describe the email first.")
            st.markdown('<div style="font-size:0.73rem;color:var(--ink3);margin-top:0.75rem;">💡 Or use Chat: "Send an email to john@co.com about tomorrow\'s meeting"</div>', unsafe_allow_html=True)