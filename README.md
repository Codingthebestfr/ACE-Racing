## Website

Run the local preview with `python app.py`.

## Contact form delivery

The contact form sends messages through Resend. Configure these environment variables on the server; never commit the API key:

- `RESEND_API_KEY` (required)
- `CONTACT_RECIPIENT` (optional; defaults to `contact@ace-racing.de`)
- `CONTACT_PUBLIC_URL` (optional; canonical HTTPS website origin used in confirmation links; defaults to `https://ace-racing.de`)
- `CONTACT_DB_PATH` (optional; defaults to `instance/contact_submissions.sqlite3`)

Verify `ace-racing.de` in Resend and use a sender address on that verified domain. A contact message is held temporarily and is not sent to the team until the sender opens the emailed confirmation link and explicitly confirms. Links expire after 30 minutes. The database path must point to persistent storage on deployments where the application filesystem is ephemeral; protect it because it temporarily contains unconfirmed contact details. Confirmation email or message delivery failures are reported to the visitor.
