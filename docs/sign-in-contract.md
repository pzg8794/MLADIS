# MLADIS Sign-In Contract

This contract protects the working local social sign-in setup. Any change to
auth settings, allauth provider settings, login/signup templates, middleware,
or OAuth launch routes must keep these guarantees true.

## Source Of Truth

- `./run_mladis_live.command` is the only normal local startup path for MLADIS.
- The launcher starts Django at `http://127.0.0.1:8000` and, by default,
  starts a Cloudflare tunnel for browser testing.
- Use the printed `https://...trycloudflare.com` URL for browser testing when
  Facebook sign-in matters.
- Treat `http://127.0.0.1:8000` as the internal Django origin and the
  Google/GitHub local callback origin, not as the Facebook browser test URL.
- Do not use the Vite dev server at `http://127.0.0.1:5173` as the auth source
  of truth. It can preview frontend assets, but Django/allauth owns sign-in.
- Do not start extra app servers with ad hoc `python manage.py runserver`,
  `npm run dev`, `nohup`, background shell commands, or preview scripts during
  normal testing.
- Keep only one launcher-managed local app server active while testing auth.
- If the synced Google Drive path becomes slow or flaky, work from a fast clone
  such as `~/Documents/MLADIS-dev` and push changes through GitHub. Copy only
  `airbnb_agent/.env` from the Drive checkout when you need the same local
  secrets.

## Provider Contract

- Google local origin: `SOCIAL_AUTH_GOOGLE_ORIGIN=http://127.0.0.1:8000`.
- GitHub local origin: `SOCIAL_AUTH_GITHUB_ORIGIN=http://127.0.0.1:8000`.
- Facebook local origin: the launcher exports
  `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://<active-tunnel>.trycloudflare.com` for
  the current run after it captures the Cloudflare URL.
- Leave `SOCIAL_AUTH_CANONICAL_ORIGIN` empty for mixed local testing. It is only
  a fallback, not the main local callback setting.
- Keep `ACCOUNT_DEFAULT_HTTP_PROTOCOL=http` for plain local `127.0.0.1`.
- Keep `USE_X_FORWARDED_PROTO=True` so tunnel requests generate HTTPS callbacks.
- Hide Microsoft until credentials are ready with
  `SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=microsoft`.

## Account Picker Contract

- Google must use provider-native account selection with
  `SOCIALACCOUNT_PROVIDERS["google"]["AUTH_PARAMS"]["prompt"] = "select_account"`.
- GitHub must use provider-native account selection with
  `SOCIALACCOUNT_PROVIDERS["github"]["AUTH_PARAMS"]["prompt"] = "select_account"`.
- Do not add an MLADIS-side "confirm current GitHub account" interstitial. The
  identity provider should handle account choice.

## Callback URLs

Register these exact callbacks for local testing:

```txt
Google:   http://127.0.0.1:8000/oauth/google/login/callback/
GitHub:   http://127.0.0.1:8000/oauth/github/login/callback/
Facebook: https://<active-tunnel>.trycloudflare.com/oauth/facebook/login/callback/
```

The active Facebook tunnel host changes when the tunnel restarts. The launcher
exports the active URL for the Django process it starts, even if
`airbnb_agent/.env` still has an older quick-tunnel value. The Meta app callback
must still allow the exact active tunnel callback while the tunnel is running.
Use `MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN=https://stable-host.example` only when
testing through a stable named tunnel or domain.

## Local Test Command

Run this before committing or pushing any auth change:

```bash
bash airbnb_agent/scripts/test_signin_contracts.sh
```

The script runs:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test bookings.test_signin_contracts.SignInContractTests
```

The tests assert:

- Login page uses direct local POST forms for Google and GitHub.
- Login page sends Facebook through the HTTPS origin bridge.
- Microsoft stays hidden while unconfigured.
- Google OAuth uses the local callback and `prompt=select_account`.
- GitHub OAuth uses the local callback and `prompt=select_account`.
- Facebook OAuth uses the HTTPS tunnel callback.
- `/ops/oauth/` renders the staff OAuth diagnostics page with exact callbacks.
- The local launcher keeps the safer startup defaults and remains shell-valid.

## Launcher Contract

The launcher should be the one-file way to see normal code and UI changes:

- `MLADIS_PUBLIC_TUNNEL` defaults to `1`.
- The launcher captures the current Cloudflare URL before starting Django and
  exports it as `SOCIAL_AUTH_FACEBOOK_ORIGIN` for that process unless
  `MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN` or an explicit shell
  `SOCIAL_AUTH_FACEBOOK_ORIGIN` is provided.
- `MLADIS_BUILD_FRONTEND` defaults to `1`, so React text/UI changes are rebuilt
  before Django starts.
- `MLADIS_RESTART_EXISTING` defaults to `1`, so stale local Django/tunnel
  processes on the same port are stopped first.
- `MLADIS_TUNNEL_LOG` defaults to `/private/tmp/mladis-tunnel.log`; use this
  log to recover the current quick-tunnel URL if the Terminal scrollback moves.
- `MLADIS_STARTUP_TIMEOUT` defaults to `60` seconds.
- Dependency install is skipped when `requirements.txt` has not changed.
- `collectstatic` is skipped for local startup unless `MLADIS_COLLECTSTATIC=1`.
- Use `MLADIS_FORCE_INSTALL=1` when you intentionally want to reinstall Python
  dependencies.
- Use `MLADIS_FORCE_NPM_INSTALL=1` when you intentionally want to reinstall
  frontend dependencies.
- Use `MLADIS_STARTUP_TIMEOUT=120` or higher if the repo is on a slow synced
  Drive path and first startup is still slow.
- Use `MLADIS_PUBLIC_TUNNEL=0` only for emergency local-only debugging.
  Facebook sign-in is expected not to work in that mode.

## Troubleshooting

- Facebook says the connection is not secure: run `./run_mladis_live.command`,
  use the printed HTTPS tunnel URL, and save the exact HTTPS callback in Meta.
- Google says `redirect_uri_mismatch`: add
  `http://127.0.0.1:8000/oauth/google/login/callback/` to the Google OAuth app.
- GitHub says `redirect_uri` is not associated: add
  `http://127.0.0.1:8000/oauth/github/login/callback/` to the GitHub OAuth app.
- The page opens on `127.0.0.1:5173`: stop the Vite server for auth testing and
  run `./run_mladis_live.command`.
- The page opens on plain `127.0.0.1:8000` while testing Facebook: switch to the
  printed tunnel URL from the launcher.
