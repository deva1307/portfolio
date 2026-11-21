# Student AI Chatbot Backend

Flask backend that serves:

- `POST /ai/ask` for chatbot answers
- `GET /health` for quick configuration status
- `POST /ai/pdf/upload` to upload/index a PDF
- `GET /ai/pdf/status` to check uploaded PDF status

## Setup

1. Create `.env` from `.env.example` and fill keys.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run server:

```powershell
python main.py
```

Backend default URL: `http://127.0.0.1:5000`
Auth user data is stored locally in SQLite: `auth_users.db`.

## GitHub Pages deployment

The portfolio source is `frontend/Index.html`. In the repository, set
**Settings > Pages > Build and deployment > Source** to **GitHub Actions**.
The **Deploy portfolio to GitHub Pages** workflow publishes the site on pushes
to `main` and can also be started manually from the Actions tab.

GitHub Pages is static hosting and cannot run the Flask email service. The
published build therefore disables the contact form and displays a notice;
the email link remains available in the portfolio. The standalone service in
`contact-api/` is source code only and is not deployed by this workflow.

## Contact Form Email

`POST /contact` sends a JSON message through authenticated SMTP to `CONTACT_TO_EMAIL`.
Configure these values in `.env` (do not commit real credentials):

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USERNAME=your-sending-account@gmail.com
SMTP_PASSWORD=your-provider-app-password
SMTP_FROM_EMAIL=your-sending-account@gmail.com
CONTACT_TO_EMAIL=your-inbox@example.com
```

Use the sender address authenticated with the SMTP provider (or a verified sender
alias), and set the visitor's address as `Reply-To`; the endpoint does this
automatically. For Gmail, use an app password when required by your account.
The contact form should send `name`, `email`, `subject`, and `message` as JSON
to `/contact`; an optional `_honey` field is used as a bot honeypot.

No application can guarantee that a message will appear in the inbox rather than
spam. Configure SPF and DKIM for the sending domain, publish an appropriate
DMARC policy, and verify inbox placement with the SMTP provider.

## PDF-First Flow

1. Upload PDF:

```powershell
curl -X POST http://127.0.0.1:5000/ai/pdf/upload -F "file=@C:/path/to/file.pdf"
```

2. Ask question:

```powershell
curl -X POST http://127.0.0.1:5000/ai/ask -H "Content-Type: application/json" -d "{\"question\":\"What is photosynthesis?\",\"preferred_lang\":\"en\"}"
```

Answer priority is:
- uploaded PDF
- grade2 knowledge base
- Gemini/Groq fallback

Notes:
- Frontend does not show PDF upload controls.
- Backend auto-loads the latest file from `uploaded_pdfs/` on startup.
- Optional: set `DEFAULT_PDF_PATH` in `.env` to preload a specific PDF.
