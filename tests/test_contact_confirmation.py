import os
import re
import tempfile
import unittest
from unittest.mock import patch

import app


class ContactConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.environment = patch.dict(
            os.environ,
            {
                "CONTACT_DB_PATH": os.path.join(self.temp_directory.name, "contact.sqlite3"),
                "CONTACT_PUBLIC_URL": "https://ace-racing.de",
                "CONTACT_RECIPIENT": "team@example.test",
                "RESEND_API_KEY": "test-api-key",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        app.CONTACT_SUBMISSIONS.clear()
        self.client = app.app.test_client()

    def _submit_contact_form(self, language="en"):
        return self.client.post(
            f"/contact?lang={language}",
            data={
                "name": "Test Sender",
                "email": "sender@example.test",
                "organisation": "Example Org",
                "topic": "general",
                "message": "A test inquiry.",
                "privacy_consent": "yes",
            },
        )

    @patch("app._send_contact_email")
    def test_message_is_forwarded_only_after_confirmation_post(self, send_email):
        response = self._submit_contact_form()

        self.assertEqual(response.status_code, 202)
        send_email.assert_called_once()
        self.assertEqual(send_email.call_args.args[0], "sender@example.test")
        confirmation_body = send_email.call_args.args[2]
        token_match = re.search(r"/contact/confirm/([A-Za-z0-9_-]{43})\?lang=en", confirmation_body)
        self.assertIsNotNone(token_match)
        confirmation_path = f"/contact/confirm/{token_match.group(1)}?lang=en"

        link_response = self.client.get(confirmation_path)
        self.assertEqual(link_response.status_code, 200)
        self.assertIn(b"Confirm email and send message", link_response.data)
        send_email.assert_called_once()

        confirmed_response = self.client.post(confirmation_path)
        self.assertEqual(confirmed_response.status_code, 302)
        self.assertEqual(confirmed_response.location, "/contact?sent=1&lang=en")
        self.assertEqual(send_email.call_count, 2)
        self.assertEqual(send_email.call_args.args[0], "team@example.test")
        self.assertEqual(send_email.call_args.kwargs["reply_to"], "sender@example.test")

        replay_response = self.client.post(confirmation_path)
        self.assertEqual(replay_response.status_code, 400)
        self.assertEqual(send_email.call_count, 2)

    @patch("app._send_contact_email", side_effect=app.ContactDeliveryError("provider rejected recipient"))
    def test_confirmation_email_failure_is_reported_and_not_stored(self, send_email):
        response = self._submit_contact_form(language="de")

        self.assertEqual(response.status_code, 503)
        self.assertIn(b"Best\xc3\xa4tigungsmail konnte nicht verschickt werden", response.data)
        connection = app._connect_contact_db()
        try:
            pending_count = connection.execute(
                "SELECT COUNT(*) FROM pending_contact_messages"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(pending_count, 0)
        send_email.assert_called_once()

    @patch("app._send_contact_email")
    def test_invalid_email_shape_is_rejected_before_any_email_is_sent(self, send_email):
        response = self.client.post(
            "/contact",
            data={
                "name": "Test Sender",
                "email": "not-an-email",
                "topic": "general",
                "message": "A test inquiry.",
                "privacy_consent": "yes",
            },
        )

        self.assertEqual(response.status_code, 400)
        send_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
