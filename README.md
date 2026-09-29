## Website

Run the local preview with `python app.py`.

## Contact form delivery

The contact form sends messages through Resend. Configure these environment variables on the server; never commit the API key:

- `RESEND_API_KEY` (required)
- `CONTACT_RECIPIENT` (optional; defaults to `contact@ace-racing.de`)

Verify `ace-racing.de` in Resend and use a sender address on that verified domain. The form reports delivery as unavailable when Resend is not configured or rejects the request.
