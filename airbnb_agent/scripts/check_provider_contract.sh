#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "FAIL: airbnb_agent/.env is missing."
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from dotenv import dotenv_values

values = dotenv_values(".env")
failures = []
warnings = []

stripe = (values.get("STRIPE_SECRET_KEY") or "").strip()
paypal_client = (values.get("PAYPAL_CLIENT_ID") or "").strip()
paypal_secret = (values.get("PAYPAL_CLIENT_SECRET") or "").strip()
paypal_environment = (values.get("PAYPAL_ENVIRONMENT") or "sandbox").strip().lower()
email_backend = (values.get("EMAIL_BACKEND") or "django.core.mail.backends.console.EmailBackend").strip()
email_host = (values.get("EMAIL_HOST") or "").strip()
email_user = (values.get("EMAIL_HOST_USER") or "").strip()
email_password = (values.get("EMAIL_HOST_PASSWORD") or "").strip()
admin_recipients = (values.get("BOOKING_INQUIRY_RECIPIENTS") or "").strip()

if not stripe:
    failures.append("STRIPE_SECRET_KEY is missing. Secure deposit Stripe checkout cannot open.")
elif not stripe.startswith(("sk_test_", "sk_live_")):
    failures.append("STRIPE_SECRET_KEY is present but does not look like sk_test_... or sk_live_...")
else:
    print("PASS: STRIPE_SECRET_KEY is configured.")
    print("INFO: Stripe key mode: " + ("test" if stripe.startswith("sk_test_") else "live"))

if paypal_client and paypal_secret:
    print("PASS: PayPal credentials are configured.")
    print("INFO: PayPal environment: " + paypal_environment)
elif paypal_client or paypal_secret:
    failures.append("PayPal is partially configured. Set both PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.")
else:
    warnings.append("PayPal credentials are not configured. PayPal deposit checkout will show a setup message.")

if not admin_recipients:
    failures.append("BOOKING_INQUIRY_RECIPIENTS is missing. Admin request/payment notifications cannot be sent.")
elif email_backend.endswith(".console.EmailBackend"):
    warnings.append("EMAIL_BACKEND is console. Emails print to the Django terminal and will not arrive in Gmail.")
elif email_backend.endswith(".locmem.EmailBackend"):
    warnings.append("EMAIL_BACKEND is locmem. Emails stay in Django memory and will not arrive in Gmail.")
elif email_backend.endswith(".smtp.EmailBackend"):
    if email_host and email_user and email_password:
        print("PASS: SMTP email delivery is configured.")
        print("INFO: Admin notification recipients are configured.")
    else:
        failures.append("EMAIL_BACKEND is SMTP but EMAIL_HOST, EMAIL_HOST_USER, or EMAIL_HOST_PASSWORD is missing.")
else:
    warnings.append(f"EMAIL_BACKEND is {email_backend}. Verify this backend sends real inbox email.")

for warning in warnings:
    print("WARN: " + warning)

if failures:
    for failure in failures:
        print("FAIL: " + failure)
    raise SystemExit(1)

print("Provider contract check passed.")
PY
