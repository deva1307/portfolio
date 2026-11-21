import os
import unittest
from unittest.mock import patch

import app as contact_service


class ContactEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = contact_service.app.test_client()
        self.payload = {
            "name": "Bala",
            "email": "visitor@example.com",
            "subject": "Office meeting",
            "message": "Hi Deva",
        }

    @patch("app.send_contact_email")
    def test_valid_contact_submission_is_sent(self, send_contact_email):
        response = self.client.post("/contact", json=self.payload)

        self.assertEqual(response.status_code, 200)
        send_contact_email.assert_called_once_with(
            "Bala", "visitor@example.com", "Office meeting", "Hi Deva"
        )

    @patch("app.send_contact_email")
    def test_honeypot_submission_is_rejected(self, send_contact_email):
        response = self.client.post(
            "/contact", json={**self.payload, "_honey": "bot text"}
        )

        self.assertEqual(response.status_code, 400)
        send_contact_email.assert_not_called()

    @patch("app.send_contact_email")
    def test_invalid_email_is_rejected(self, send_contact_email):
        response = self.client.post(
            "/contact", json={**self.payload, "email": "not-an-email"}
        )

        self.assertEqual(response.status_code, 400)
        send_contact_email.assert_not_called()

    def test_cors_allows_the_github_pages_origin(self):
        response = self.client.options(
            "/contact",
            headers={
                "Origin": "https://deva1307.github.io",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "https://deva1307.github.io")

    @patch.dict(os.environ, {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "sender@example.com",
        "SMTP_PASSWORD": "",
        "SMTP_FROM_EMAIL": "sender@example.com",
        "CONTACT_TO_EMAIL": "owner@example.com",
    })
    def test_missing_smtp_password_returns_configuration_error(self):
        response = self.client.post("/contact", json=self.payload)

        self.assertEqual(response.status_code, 503)
        self.assertIn("SMTP_PASSWORD", response.get_json()["error"])
        self.assertNotIn("SMTP_HOST", response.get_json()["error"])

    @patch("app.smtplib.SMTP")
    @patch.dict(os.environ, {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_SECURITY": "starttls",
        "SMTP_USERNAME": "sender@example.com",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM_EMAIL": "sender@example.com",
        "CONTACT_TO_EMAIL": "owner@example.com",
    })
    def test_smtp_uses_fixed_sender_and_reply_to(self, smtp):
        contact_service.send_contact_email(
            "Bala", "visitor@example.com", "Office meeting", "Hi Deva"
        )

        server = smtp.return_value.__enter__.return_value
        server.starttls.assert_called_once()
        sent_message = server.send_message.call_args.args[0]
        self.assertEqual(sent_message["From"], "sender@example.com")
        self.assertEqual(sent_message["To"], "owner@example.com")
        self.assertEqual(sent_message["Reply-To"], "visitor@example.com")


if __name__ == "__main__":
    unittest.main()
