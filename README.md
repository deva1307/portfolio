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

## Portfolio deployment

The portfolio is in `frontend/Index.html`. Its contact form only needs the
standalone service in `contact-api/`; the chatbot backend and MySQL database are
not used by this page.

1. Deploy `contact-api/` as a Railway service with that folder as its root.
   Install with `pip install -r requirements.txt` and start with
   `gunicorn app:app --bind 0.0.0.0:$PORT`.
2. Set these variables in the Railway service. Enter real values in Railway's
   private variable settings, never in this repository:

   ```text
   PORTFOLIO_ORIGIN=https://deva1307.github.io
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_SECURITY=starttls
   SMTP_USERNAME=your-sending-account@gmail.com
   SMTP_PASSWORD=your-provider-app-password
   SMTP_FROM_EMAIL=your-sending-account@gmail.com
   CONTACT_TO_EMAIL=your-inbox@example.com
   ```

3. Generate a public HTTPS domain for the Railway service and add a GitHub
   repository Actions secret named `CONTACT_API_URL`, set to the full contact
   endpoint URL ending in `/contact`.
4. In the GitHub repository, set **Settings > Pages > Build and deployment >
   Source** to **GitHub Actions**. Run the **Deploy portfolio to GitHub Pages**
   workflow from the Actions tab. It builds the published page with the secret
   endpoint; it does not put SMTP credentials into the site.

The contact API exposes `/health` for a basic availability check. Email
delivery still depends on valid SMTP settings and provider filtering.

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
