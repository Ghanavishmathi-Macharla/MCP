from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.message import EmailMessage


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_gmail_service():
    credentials = None

    # Load previously saved credentials
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # If credentials don't exist or have expired
    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            credentials = flow.run_local_server(
                port=0
            )

        # Save credentials for future runs
        TOKEN_FILE.write_text(
            credentials.to_json()
        )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )

def send_email(to: str, subject: str, body: str) -> dict:
    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = to
    message["Subject"] = subject

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    request_body = {
        "raw": encoded_message
    }

    result = service.users().messages().send(
        userId="me",
        body=request_body
    ).execute()

    return {
        "success": True,
        "message_id": result["id"],
        "to": to,
        "subject": subject
    }

if __name__ == "__main__":
    result = send_email(
        to="ghanavishmathi.macharla91@gmail.com",
        subject="MCP Gmail Test",
        body="Hello! This email was sent using the Gmail API."
    )

    print(result)