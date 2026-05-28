import base64
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def _headers(payload):
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def _extract_body(payload):
    """Recursively extract plain text body."""
    if "parts" in payload:
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data", "")
    if data and mime == "text/plain":
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    if data and mime == "text/html":
        raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        # Strip tags simply
        return re.sub(r"<[^>]+>", " ", raw)
    return ""


class GmailClient:
    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials)

    def get_profile(self):
        return self.service.users().getProfile(userId="me").execute()

    def list_unread_emails(self, max_results=15):
        return self._list("is:unread", max_results)

    def search_by_query(self, query: str, max_results=10):
        return self._list(query, max_results)

    def _list(self, q: str, max_results: int):
        res = self.service.users().messages().list(
            userId="me", q=q, maxResults=max_results
        ).execute()
        msgs = res.get("messages", [])
        return [self._fetch(m["id"]) for m in msgs if m]

    def _fetch(self, msg_id: str):
        msg = self.service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
        hdrs = _headers(msg["payload"])
        body = _extract_body(msg["payload"]).strip()
        return {
            "id": msg_id,
            "thread_id": msg.get("threadId", ""),
            "message_id_header": hdrs.get("Message-ID", ""),
            "from": hdrs.get("From", ""),
            "to": hdrs.get("To", ""),
            "subject": hdrs.get("Subject", "(No Subject)"),
            "date": hdrs.get("Date", ""),
            "body": body[:3000],
            "snippet": msg.get("snippet", "")[:150],
            "unread": "UNREAD" in msg.get("labelIds", []),
        }

    def get_email_by_id(self, msg_id: str):
        return self._fetch(msg_id)

    def send_email(self, to: str, subject: str, body: str, thread_id: str = None, reply_message_id: str = None):
        msg = MIMEMultipart()
        msg["From"] = "me"
        msg["To"] = to
        msg["Subject"] = subject
        if reply_message_id:
            msg["In-Reply-To"] = reply_message_id
            msg["References"] = reply_message_id
        msg.attach(MIMEText(body, "plain"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body_payload = {"raw": raw}
        if thread_id:
            body_payload["threadId"] = thread_id
        result = self.service.users().messages().send(
            userId="me", body=body_payload
        ).execute()
        return {"status": "sent", "id": result.get("id")}

    def mark_as_read(self, msg_id: str):
        self.service.users().messages().modify(
            userId="me", id=msg_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()