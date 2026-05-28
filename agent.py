import json
import os
import re
from datetime import datetime
from groq import Groq


# ---------------------------------------------------------------------------
# Persistent Memory Store
# ---------------------------------------------------------------------------

class MemoryStore:
    """
    Persists agent memory to a local JSON file across sessions.

    Stores three kinds of memory:
      - sender_profiles : what the agent knows about each contact
                          (tone used, topics discussed, last interaction)
      - user_preferences: reply style, signature, things the user has
                          explicitly told the agent to remember
      - interaction_log : lightweight log of past actions the agent took
                          (last 50 entries kept to avoid unbounded growth)
    """

    DEFAULT = {
        "sender_profiles": {},
        "user_preferences": {},
        "interaction_log": []
    }

    def __init__(self, path: str = "agent_memory.json"):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                for k, v in self.DEFAULT.items():
                    data.setdefault(k, v)
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return json.loads(json.dumps(self.DEFAULT))

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    # ---- sender profiles ---------------------------------------------------

    def update_sender(self, email_address: str, updates: dict):
        email_address = email_address.lower().strip()
        profile = self._data["sender_profiles"].setdefault(email_address, {})
        profile.update(updates)
        profile["last_seen"] = datetime.now().isoformat()
        self.save()

    def get_sender(self, email_address: str) -> dict:
        return self._data["sender_profiles"].get(email_address.lower().strip(), {})

    def get_all_senders(self) -> dict:
        return self._data["sender_profiles"]

    # ---- user preferences --------------------------------------------------

    def set_preference(self, key: str, value):
        self._data["user_preferences"][key] = value
        self.save()

    def get_preference(self, key: str, default=None):
        return self._data["user_preferences"].get(key, default)

    def get_all_preferences(self) -> dict:
        return self._data["user_preferences"]

    # ---- interaction log ---------------------------------------------------

    def log_action(self, action: str, detail: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "detail": detail
        }
        self._data["interaction_log"].append(entry)
        self._data["interaction_log"] = self._data["interaction_log"][-50:]
        self.save()

    def get_recent_log(self, n: int = 10) -> list:
        return self._data["interaction_log"][-n:]

    # ---- serialise for prompt injection ------------------------------------

    def as_context_string(self) -> str:
        """Compact memory summary injected into the system prompt each session."""
        lines = ["### Agent Memory (persisted across sessions)"]

        prefs = self._data["user_preferences"]
        if prefs:
            lines.append("\n**User preferences:**")
            for k, v in prefs.items():
                lines.append(f"  - {k}: {v}")

        profiles = self._data["sender_profiles"]
        if profiles:
            lines.append("\n**Known senders:**")
            for addr, p in list(profiles.items())[:15]:
                parts = [addr]
                if p.get("name"):
                    parts.append(f"({p['name']})")
                if p.get("relationship"):
                    parts.append(f"— {p['relationship']}")
                if p.get("tone"):
                    parts.append(f"[reply tone: {p['tone']}]")
                if p.get("last_seen"):
                    parts.append(f"[last seen: {p['last_seen'][:10]}]")
                lines.append("  - " + " ".join(parts))

        recent = self._data["interaction_log"][-5:]
        if recent:
            lines.append("\n**Recent actions:**")
            for e in recent:
                lines.append(f"  - [{e['timestamp'][:16]}] {e['action']}: {e['detail']}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Email Agent
# ---------------------------------------------------------------------------

class EmailAgent:
    MODEL = "llama-3.1-8b-instant"

    def __init__(self, groq_api_key: str, gmail_client, memory_path: str = "agent_memory.json"):
        self.client = Groq(api_key=groq_api_key)
        self.gmail = gmail_client
        self.memory = MemoryStore(memory_path)
        self.action_log = []

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_unread_emails",
                    "description": "Fetch the latest unread emails from Gmail inbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_results": {"type": "integer", "default": 5}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Search emails. Supports Gmail query syntax: from:, subject:, is:unread, after:, before:, or free-text keywords.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_email",
                    "description": "Fetch the full content of a specific email by its ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_id": {"type": "string"}
                        },
                        "required": ["email_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "draft_reply",
                    "description": "Generate a draft reply for a specific email without sending.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_id": {"type": "string"},
                            "instructions": {"type": "string"}
                        },
                        "required": ["email_id", "instructions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send a new email or reply to an existing one.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"},
                            "thread_id": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "description": "Thread ID for replies. Omit or pass null for new emails."
                            },
                            "reply_message_id": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "description": "Message-ID header for threading. Omit or pass null for new emails."
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mark_as_read",
                    "description": "Mark an email as read.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_id": {"type": "string"}
                        },
                        "required": ["email_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_email",
                    "description": (
                        "Classify whether an email requires any reply or follow-up action. "
                        "Use this before drafting replies or suggesting actions. "
                        "Emails that NEVER need replies include: bank statements, transaction "
                        "alerts, debit/credit notifications, OTP/verification codes, social "
                        "network notifications (LinkedIn follow requests, likes, connection "
                        "requests), newsletters, automated receipts, shipping/delivery "
                        "notifications, subscription confirmations, and any no-reply sender."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "ID of the email to classify."
                            }
                        },
                        "required": ["email_id"]
                    }
                }
            },
            # -----------------------------------------------------------------
            # Memory tools
            # -----------------------------------------------------------------
            {
                "type": "function",
                "function": {
                    "name": "remember_preference",
                    "description": (
                        "Save a user preference or instruction for future sessions. "
                        "Use whenever the user tells you how they want things done: "
                        "reply tone, signature, topics to ignore, trusted senders, etc."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key":   {"type": "string", "description": "Short name, e.g. 'reply_tone'"},
                            "value": {"type": "string", "description": "The value to remember"}
                        },
                        "required": ["key", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_sender",
                    "description": (
                        "Update what the agent knows about an email sender. "
                        "Call after reading or replying to an email to record "
                        "relationship, preferred tone, or any useful context."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_address": {"type": "string"},
                            "name":         {"type": "string"},
                            "relationship": {"type": "string", "description": "e.g. manager, client, recruiter, friend"},
                            "tone":         {"type": "string", "description": "tone for replies, e.g. formal, casual"},
                            "notes":        {"type": "string", "description": "any other useful context"}
                        },
                        "required": ["email_address"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_memory",
                    "description": (
                        "Read everything the agent remembers about a specific sender, "
                        "or retrieve all stored preferences. Pass null address for preferences."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_address": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "description": "Address to look up, or null for all preferences."
                            }
                        },
                        "required": ["email_address"]
                    }
                }
            }
        ]

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _slim_email(email: dict) -> dict:
        return {
            "id":        email.get("id"),
            "thread_id": email.get("thread_id"),
            "from":      email.get("from"),
            "subject":   email.get("subject"),
            "date":      email.get("date"),
            "snippet":   email.get("snippet", "")[:150],
            "unread":    email.get("unread"),
        }

    @staticmethod
    def _extract_address(raw: str) -> str:
        m = re.search(r"<([^>]+)>", raw)
        return m.group(1).strip().lower() if m else raw.strip().lower()

    # -----------------------------------------------------------------------
    # Tool execution
    # -----------------------------------------------------------------------

    def _run_tool(self, name: str, args: dict) -> str:
        self.action_log.append(f"🔧 **{name}** `{json.dumps(args)}`")
        try:

            if name == "list_unread_emails":
                emails = self.gmail.list_unread_emails(args.get("max_results", 5))
                self.action_log.append(f"   ↳ fetched {len(emails)} unread emails")
                for e in emails:
                    addr = self._extract_address(e.get("from", ""))
                    if addr:
                        self.memory.update_sender(addr, {})
                return json.dumps([self._slim_email(e) for e in emails])

            elif name == "search_emails":
                emails = self.gmail.search_by_query(args["query"], args.get("max_results", 5))
                self.action_log.append(f"   ↳ found {len(emails)} results for '{args['query']}'")
                return json.dumps([self._slim_email(e) for e in emails])

            elif name == "get_email":
                email = self.gmail.get_email_by_id(args["email_id"])
                if email and email.get("body"):
                    email["body"] = email["body"][:1500]
                # Attach known sender profile so the model sees it in context
                if email:
                    addr = self._extract_address(email.get("from", ""))
                    profile = self.memory.get_sender(addr)
                    if profile:
                        email["_known_sender"] = profile
                return json.dumps(email)

            elif name == "draft_reply":
                em = self.gmail.get_email_by_id(args["email_id"])
                if not em:
                    return json.dumps({"error": "Email not found"})

                addr    = self._extract_address(em.get("from", ""))
                profile = self.memory.get_sender(addr)
                prefs   = self.memory.get_all_preferences()

                # Build memory hint to steer the draft
                hints = []
                if profile.get("tone"):
                    hints.append(f"Use a {profile['tone']} tone for this sender.")
                if profile.get("relationship"):
                    hints.append(f"This person is your {profile['relationship']}.")
                if profile.get("notes"):
                    hints.append(f"Context about sender: {profile['notes']}")
                if prefs.get("signature"):
                    hints.append(f"End with this signature:\n{prefs['signature']}")
                if prefs.get("reply_tone") and not profile.get("tone"):
                    hints.append(f"Default reply tone: {prefs['reply_tone']}.")

                memory_hint = " ".join(hints)

                prompt = (
                    f"Write a professional email reply.\n"
                    f"From: {em['from']}\nSubject: {em['subject']}\n"
                    f"Body:\n{em['body'][:1500]}\n\n"
                    f"Instructions: {args['instructions']}\n"
                    + (f"Memory context: {memory_hint}\n" if memory_hint else "")
                    + "Return ONLY the reply body. No subject line."
                )
                r = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
                draft = r.choices[0].message.content
                self.action_log.append(f"   ↳ draft created for email from {em['from']}")
                self.memory.log_action("draft_reply", f"to {addr} re: {em['subject'][:60]}")
                return json.dumps({
                    "draft": draft,
                    "to": em["from"],
                    "subject": f"Re: {em['subject']}",
                    "thread_id": em.get("thread_id", ""),
                    "reply_message_id": em.get("message_id_header", "")
                })

            elif name == "send_email":
                thread_id        = args.get("thread_id") or None
                reply_message_id = args.get("reply_message_id") or None
                result = self.gmail.send_email(
                    to=args["to"], subject=args["subject"], body=args["body"],
                    thread_id=thread_id, reply_message_id=reply_message_id
                )
                self.action_log.append(f"   ↳ 📤 sent to {args['to']}")
                addr = self._extract_address(args["to"])
                self.memory.log_action("sent_email", f"to {addr} — {args['subject'][:60]}")
                self.memory.update_sender(addr, {"last_replied": datetime.now().isoformat()})
                return json.dumps(result)

            elif name == "mark_as_read":
                self.gmail.mark_as_read(args["email_id"])
                self.action_log.append(f"   ↳ marked as read")
                return json.dumps({"status": "ok"})

            elif name == "classify_email":
                em = self.gmail.get_email_by_id(args["email_id"])
                if not em:
                    return json.dumps({"error": "Email not found"})

                prompt = (
                    "Classify this email and decide whether any reply or follow-up is needed.\n\n"
                    "Emails that NEVER need a reply include (but are not limited to):\n"
                    "  - Bank statements, transaction alerts, debit/credit/UPI notifications\n"
                    "  - OTP, verification codes, password reset emails\n"
                    "  - LinkedIn follow requests, connection suggestions, likes, endorsements\n"
                    "  - Social media notifications (Twitter, Instagram, Facebook, etc.)\n"
                    "  - Automated receipts, invoices with no action required\n"
                    "  - Shipping / delivery status updates\n"
                    "  - Newsletter or promotional emails\n"
                    "  - Subscription confirmations / welcome emails\n"
                    "  - Any email from a no-reply@ or donotreply@ address\n\n"
                    f"From: {em['from']}\n"
                    f"Subject: {em['subject']}\n"
                    f"Snippet: {em['snippet']}\n"
                    f"Body (first 600 chars):\n{(em.get('body') or '')[:600]}\n\n"
                    "Respond ONLY with valid JSON — no markdown, no explanation:\n"
                    '{"needs_reply": true/false, "category": "one of: transactional | notification | social | newsletter | reply_needed | follow_up_needed", "reason": "one short sentence"}'
                )
                r = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=120
                )
                raw = r.choices[0].message.content.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()
                try:
                    result = json.loads(raw)
                except Exception:
                    result = {"needs_reply": True, "category": "unknown", "reason": "Could not classify."}
                self.action_log.append(
                    f"   ↳ classified as {'needs reply' if result.get('needs_reply') else 'no reply needed'} ({result.get('category', '')})"
                )
                return json.dumps(result)

            # ---- memory tools ----------------------------------------------

            elif name == "remember_preference":
                self.memory.set_preference(args["key"], args["value"])
                self.action_log.append(f"   ↳ 🧠 remembered: {args['key']} = {args['value']}")
                return json.dumps({"status": "saved", "key": args["key"], "value": args["value"]})

            elif name == "remember_sender":
                addr = self._extract_address(args["email_address"])
                updates = {k: v for k, v in args.items()
                           if k != "email_address" and v is not None}
                self.memory.update_sender(addr, updates)
                self.action_log.append(f"   ↳ 🧠 updated sender profile: {addr}")
                return json.dumps({"status": "saved", "address": addr, "updates": updates})

            elif name == "recall_memory":
                addr = args.get("email_address")
                if addr:
                    return json.dumps({"sender": addr, "profile": self.memory.get_sender(addr)})
                else:
                    return json.dumps({
                        "preferences": self.memory.get_all_preferences(),
                        "recent_log":  self.memory.get_recent_log(10)
                    })

        except Exception as e:
            err = f"Error in {name}: {e}"
            self.action_log.append(f"   ↳ ❌ {err}")
            return json.dumps({"error": err})

        return json.dumps({"error": "Unknown tool"})

    # -----------------------------------------------------------------------
    # Public: classify a single email (used by app.py for inbox UI)
    # -----------------------------------------------------------------------

    def classify_email(self, email_id: str) -> dict:
        """
        Classify whether an email needs a reply.
        Returns: {"needs_reply": bool, "category": str, "reason": str}
        """
        result = json.loads(self._run_tool("classify_email", {"email_id": email_id}))
        return result

    # -----------------------------------------------------------------------
    # Main run loop
    # -----------------------------------------------------------------------

    def run(self, instruction: str):
        self.action_log = []

        # Inject persistent memory into the system prompt so every session
        # automatically starts with accumulated context.
        memory_context = self.memory.as_context_string()

        system_prompt = (
            "You are an intelligent personal email assistant with access to the user's Gmail.\n"
            "You can read, search, draft, and send emails.\n"
            "Be concise. Summarize emails by highlighting sender, subject, and key action items.\n"
            "Always fetch email content before drafting replies.\n"
            "Never make up email content.\n\n"
            "IMPORTANT — Before drafting a reply or suggesting any follow-up action, ALWAYS call\n"
            "`classify_email` first. If it returns needs_reply=false, inform the user that this\n"
            "email does not require a reply (e.g. bank alert, LinkedIn notification, OTP, newsletter)\n"
            "and do NOT draft a reply unless the user explicitly insists.\n\n"
            "You have PERSISTENT MEMORY across sessions. Use it proactively:\n"
            "  - Call `remember_sender` after reading or replying to an email to record "
            "the relationship and preferred reply tone for that contact.\n"
            "  - Call `remember_preference` when the user tells you how they want things done.\n"
            "  - Call `recall_memory` when you need to check what you know about someone.\n"
            "  - Your memory is automatically used in draft_reply — no need to fetch it manually.\n\n"
            + memory_context
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": instruction}
        ]

        for _ in range(12):
            resp = None
            for attempt in range(3):
                try:
                    resp = self.client.chat.completions.create(
                        model=self.MODEL, messages=messages,
                        tools=self.tools, tool_choice="auto", max_tokens=2048
                    )
                    break
                except Exception as e:
                    err_str = str(e)
                    if "tool_use_failed" in err_str and attempt < 2:
                        self.action_log.append(
                            f"   ⚠️ Empty tool generation, retrying (attempt {attempt + 2}/3)..."
                        )
                        messages.append({
                            "role": "user",
                            "content": (
                                "Your last response was empty. Please try again and "
                                "use one of the available tools to complete the task."
                            )
                        })
                        continue
                    self.action_log.append(f"   ❌ API error: {e}")
                    return f"Error communicating with model: {e}", self.action_log

            if resp is None:
                return "Model failed to respond after retries.", self.action_log

            msg        = resp.choices[0].message
            finish     = resp.choices[0].finish_reason
            tool_calls = msg.tool_calls or []

            messages.append({
                "role":       "assistant",
                "content":    msg.content,
                "tool_calls": tool_calls or None
            })

            if finish == "stop" or not tool_calls:
                return msg.content, self.action_log

            for tc in tool_calls:
                result = self._run_tool(tc.function.name, json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return "Agent reached max iterations.", self.action_log