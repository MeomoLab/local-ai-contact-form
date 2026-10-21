# Local AI webinar contact form

A small server-rendered contact form for individual participants in the free webinar **How to run a local AI model that protects your privacy**. It uses Python's standard library only.

## Run locally

Requires Python 3.10 or newer. From this folder, run:

```sh
python3 server.py
```

Then open [http://127.0.0.1:8080/contact](http://127.0.0.1:8080/contact). Press `Ctrl+C` in the terminal to stop the server.

## Behavior

- `GET /contact` renders the form. `/` redirects to `/contact`.
- `POST /contact` checks name, email, and message on the server. All are required; email must match a conventional email address with a domain.
- Invalid fields produce visible errors and retain other submitted values.
- Validation errors link to the affected fields and focus the first invalid field. Request-processing errors show a friendly retry page.
- A valid submission displays a confirmation page, then discards the values.
- The app does not store, log, or email participant details. The confirmation explains that a reply is not possible yet.
- Request bodies are limited to 64 KiB. No third-party packages are used.

The server listens on `127.0.0.1`, so it is available only on this computer. For access from other devices, a public deployment, or an internet-facing server, configure a separate HTTPS-enabled web server and bind it appropriately.
