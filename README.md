## Website

Run the local preview with `python app.py`.

## Contact form delivery

The contact form forwards messages through SMTP. Configure these environment variables on the server; never commit the password:

- `SMTP_HOST`
- `SMTP_PORT` (587 for STARTTLS or 465 for SSL)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER` (optional; defaults to `SMTP_USERNAME`)
- `CONTACT_RECIPIENT` (optional; defaults to `contact@ace-racing.de`)

The form reports delivery as unavailable until SMTP is configured.
