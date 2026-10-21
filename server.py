#!/usr/bin/env python3
"""A small, standard-library-only contact form for a local webinar."""

from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from urllib.parse import parse_qs


HOST = "127.0.0.1"
PORT = 8080
MAX_BODY = 64 * 1024
EMAIL_RE = re.compile(
    r"^([A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*)@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)

STYLE = """
:root { color-scheme:light; --ink:#17231f; --muted:#53645c; --paper:#f5f2eb; --card:#fffefa; --green:#176447; --line:#b7c5bb; --error:#a32121; --wash:#e6eee5; }
* { box-sizing:border-box; }
body { margin:0; background:radial-gradient(ellipse at 50% 0,#e4ece1 0,transparent 48%),var(--paper); color:var(--ink); font:17px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
main { width:min(100% - 32px,680px); margin:clamp(28px,7vh,76px) auto 48px; }
.skip-link { position:absolute; left:-9999px; top:10px; z-index:2; padding:10px 14px; background:#fff; color:var(--green); border-radius:8px; }
.skip-link:focus { left:10px; }
.eyebrow { display:flex; align-items:center; gap:9px; margin:0 0 12px; color:var(--green); font-size:.82rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }
.eyebrow:before { content:""; width:10px; height:10px; border-radius:50%; background:var(--green); box-shadow:0 0 0 4px #1764471a; }
h1 { max-width:18ch; margin:0 0 12px; font-size:clamp(2.15rem,6vw,3.15rem); line-height:1.08; letter-spacing:-.045em; }
.intro { max-width:58ch; margin:0 0 24px; color:var(--muted); }
.card { padding:clamp(22px,5vw,40px); background:var(--card); border:1px solid #d9ded8; border-radius:22px; box-shadow:0 18px 48px #17231f12; }
.form-meta { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px 20px; margin:0 0 24px; color:var(--muted); font-size:.9rem; }
.required-note { margin:0; }
.privacy-note { display:flex; gap:10px; padding:12px 14px; margin:0 0 24px; border:1px solid #cddbcc; border-radius:12px; background:var(--wash); color:#31473a; font-size:.92rem; }
.privacy-note p { margin:0; }
.field { margin:0 0 21px; }
label { display:block; margin-bottom:7px; font-weight:700; }
.required { color:var(--green); }
input,textarea { display:block; width:100%; min-height:52px; padding:13px 14px; border:1px solid var(--line); border-radius:11px; background:#fff; color:var(--ink); font:inherit; transition:border-color .15s,box-shadow .15s; }
textarea { min-height:160px; resize:vertical; }
input:focus,textarea:focus { outline:3px solid #1764472b; border-color:var(--green); box-shadow:0 0 0 1px var(--green); }
[aria-invalid="true"] { border-color:var(--error); }
.error { margin:7px 0 0; color:#8a1c1c; font-weight:650; }
.error-summary { padding:16px 18px; margin:0 0 22px; border:1px solid #e4b8b3; border-left:4px solid var(--error); border-radius:10px; background:#fff2f0; }
.error-summary p { margin:0 0 6px; }
.error-summary ul { margin:0; padding-left:20px; }
.error-summary a { color:#7c1919; font-weight:650; }
.notice p { margin:0 0 10px; }
.notice p:last-child { margin-bottom:0; }
button,.button { display:inline-flex; align-items:center; justify-content:center; gap:9px; min-height:52px; padding:13px 23px; border:0; border-radius:999px; background:var(--green); color:#fff; font:inherit; font-weight:750; text-decoration:none; cursor:pointer; transition:background .15s,transform .15s; }
button:hover,.button:hover { background:#104b35; transform:translateY(-1px); }
button:focus-visible,.button:focus-visible,.error-summary a:focus-visible { outline:3px solid #17644766; outline-offset:3px; }
.notice { padding:18px; border:1px solid #cddbcc; border-radius:14px; background:var(--wash); }
.notice strong { display:block; margin-bottom:4px; }
footer { display:flex; gap:8px; margin:17px 2px 0; color:var(--muted); font-size:.9rem; }
@media(max-width:480px) { main { margin:28px auto; } .card { border-radius:17px; } button { width:100%; } }
@media(prefers-reduced-motion:reduce) { *,*:before,*:after { scroll-behavior:auto!important; transition:none!important; } }
"""


def page(title: str, content: str) -> bytes:
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f5f2eb"><title>{escape(title)} · Local AI webinar</title><style>{STYLE}</style></head>
<body><a class="skip-link" href="#main">Skip to form</a><main id="main"><p class="eyebrow">Free webinar · Ireland</p>{content}</main></body></html>"""
    return document.encode("utf-8")


def error_markup(errors: dict[str, str], field: str) -> str:
    if field not in errors:
        return ""
    return f'<p class="error" id="{field}-error">{escape(errors[field])}</p>'


def form_page(values: dict[str, str] | None = None, errors: dict[str, str] | None = None, status: int = 200) -> tuple[int, bytes]:
    values = values or {"name": "", "email": "", "message": ""}
    errors = errors or {}
    if errors:
        links = "".join(
            f'<li><a href="#{key}">{escape(label)}: {escape(message)}</a></li>'
            for key, label in (("name", "Your name"), ("email", "Email address"), ("message", "Your message"))
            if (message := errors.get(key))
        )
        summary = f'<div class="error-summary" role="alert" tabindex="-1"><p>Please correct these fields:</p><ul>{links}</ul></div>'
    else:
        summary = ""
    first_error = next((key for key in ("name", "email", "message") if key in errors), None)
    fields = []
    for key, label, control in (
        ("name", "Your name", "input"),
        ("email", "Email address", "input"),
        ("message", "Your message", "textarea"),
    ):
        invalid = ' aria-invalid="true" aria-describedby="' + key + '-error"' if key in errors else ""
        focus = " autofocus" if key == first_error else ""
        common = f'id="{key}" name="{key}" required{invalid}{focus}'
        if control == "textarea":
            element = f"<textarea {common}>{escape(values[key])}</textarea>"
        else:
            extra = ' type="email" autocomplete="email"' if key == "email" else ' autocomplete="name"'
            element = f'<input {common}{extra} value="{escape(values[key], quote=True)}">'
        fields.append(
            f'<div class="field"><label for="{key}">{label} <span class="required" aria-hidden="true">*</span></label>'
            f"{element}{error_markup(errors, key)}</div>"
        )
    content = (
        '<h1 id="title">Get in touch</h1>'
        '<p class="intro">Questions about <strong>How to run a local AI model that protects your privacy</strong>? We’d be glad to hear from you.</p>'
        f'<section class="card" aria-labelledby="title">{summary}'
        '<div class="form-meta"><p class="required-note">Fields marked <span class="required" aria-hidden="true">*</span> are required</p></div>'
        '<div class="privacy-note"><span aria-hidden="true">🔒</span><p><strong>Your privacy:</strong> This demo does not save or send your message. Please don’t include anything you need a reply to.</p></div>'
        '<form method="post" action="/contact">'
        + "".join(fields)
        + '<button type="submit">Check my message <span aria-hidden="true">→</span></button></form></section>'
        '<footer><span aria-hidden="true">ⓘ</span><span>This is a local demo form for webinar participants in Ireland.</span></footer>'
    )
    return status, page("Get in touch", content)


class ContactHandler(BaseHTTPRequestHandler):
    server_version = "LocalAIContact/1.0"

    def send_html(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code == 404:
            title, description = "Page not found", "That page isn’t available. Use the button below to return to the contact form."
            action = '<a class="button" href="/contact">Back to contact form</a>'
        else:
            title, description = "We couldn’t check your message", "Your message was not saved or sent. Please return to the form and try again."
            action = '<a class="button" href="/contact">Try the form again</a>'
        content = f'<section class="card" aria-labelledby="title"><h1 id="title">{title}</h1><p>{description}</p>{action}</section>'
        self.send_html(code, page(title, content))

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_response(303)
            self.send_header("Location", "/contact")
            self.end_headers()
        elif self.path == "/contact":
            status, body = form_page()
            self.send_html(status, body)
        else:
            self.send_error(404, "Page not found")

    def do_POST(self) -> None:
        if self.path != "/contact":
            self.send_error(404, "Page not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid request")
            return
        if length < 0 or length > MAX_BODY:
            self.send_error(413, "Request is too large")
            return
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            self.send_error(415, "Unsupported form content type")
            return

        raw_body = self.rfile.read(length)
        try:
            raw_values = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True, max_num_fields=10)
        except (UnicodeDecodeError, ValueError):
            self.send_error(400, "Invalid form data")
            return
        values = {key: raw_values.get(key, [""])[0].strip() for key in ("name", "email", "message")}
        errors: dict[str, str] = {}
        if not values["name"]:
            errors["name"] = "Please enter your name."
        email = values["email"]
        if not email:
            errors["email"] = "Please enter your email address."
        else:
            email_match = EMAIL_RE.fullmatch(email)
            if not email_match or len(email_match.group(1)) > 64 or len(email.rsplit("@", 1)[1]) > 253:
                errors["email"] = "Enter a valid email address, for example name@example.com."
        if not values["message"]:
            errors["message"] = "Please enter a message."

        if errors:
            status, body = form_page(values, errors, 422)
            self.send_html(status, body)
            return

        # Valid values are deliberately discarded: this version stores and sends nothing.
        content = (
            '<section class="card" aria-labelledby="title"><h1 id="title">Thanks for getting in touch</h1>'
            '<div class="notice" role="status"><strong>Your message passed the form checks.</strong>'
            '<p>This demo does not save or send messages, so nobody can reply to it. Your details have now been discarded.</p></div>'
            '<p><a class="button" href="/contact">Back to contact form</a></p></section>'
        )
        self.send_html(200, page("Message checked", content))

    def log_message(self, _format: str, *_args: object) -> None:
        # Do not log request content or participant details.
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ContactHandler)
    print(f"Contact form running at http://{HOST}:{PORT}/contact")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping contact form.")
    finally:
        server.server_close()
