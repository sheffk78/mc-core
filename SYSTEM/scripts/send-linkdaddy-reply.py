#!/usr/bin/env python3
"""Send reply to LinkDaddy with attachments via Gmail API."""
import sys, os, base64, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

sys.path.insert(0, "/Users/socializerender/.hermes/skills/productivity/google-workspace/scripts")
from google_api import get_credentials, build_service

# File paths
legal_dir = "/Users/socializerender/.openclaw/workspace/Kit/life/brands/AgenticTrust/legal/formation"
attachments = [
    ("certification_of_trust_Agentic-Trust-SIGNED.pdf", "Certificate of Trust.pdf"),
    ("AgenticTrust Opp Agreement.pdf", "Operating Agreement.pdf"),
    ("irs_confirmation_0464c4a0-7e38-4e7d-9518-e0f07d1bd436.pdf", "IRS EIN Confirmation.pdf"),
]

# Build the email
msg = MIMEMultipart()
msg["to"] = "fhul@linkdaddy.com"
msg["subject"] = "Re: Your LinkDaddy Premium Press Release Submission & Review! Press Release Service - Yahoo \u2013 Order #75951"
msg["from"] = "Jeff Kohler <jeff@socialize.video>"

body_text = (
    "Hi Fhul,\n\n"
    "Approved \u2014 the press release is good to go.\n\n"
    "Regarding the business registration certificate for Yahoo: TrustOffice operates under a trust structure, "
    "so we don't have a conventional state-filed business registration. I've attached what we currently have "
    "\u2014 our Certificate of Trust, Operating Agreement, and IRS EIN confirmation letter. "
    "Let me know if these satisfy Yahoo's requirement or if you need anything else.\n\n"
    "Thanks,\n"
    "Jeff"
)

msg.attach(MIMEText(body_text, "plain"))

for filename, display_name in attachments:
    filepath = os.path.join(legal_dir, filename)
    with open(filepath, "rb") as f:
        part = MIMEBase("application", "pdf")
        part.set_payload(f.read())
    part.add_header("Content-Disposition", f'attachment; filename="{display_name}"')
    msg.attach(part)

# Send via Gmail API
service = build_service("gmail", "v1")
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
result = service.users().messages().send(
    userId="me",
    body={"raw": raw}
).execute()

print(json.dumps({"status": "sent", "id": result["id"], "threadId": result.get("threadId", "")}, indent=2))