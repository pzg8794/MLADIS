# MLADIS Sign-In Contract

This contract protects the working local social sign-in setup. Any change to
auth settings, allauth provider settings, login/signup templates, middleware,
or OAuth launch routes must keep these guarantees true.

## Source Of Truth

- `./run_mladis_live.command` is the only normal local startup path for MLADIS.
- The launcher starts Django at `http://127.0.0.1:8000` and, by default,
  starts the stable Cloudflare named tunnel for `https://local.mladis.com`.
- Use `https://local.mladis.com` for browser testing when Facebook sign-in
  matters.
- Treat `http://127.0.0.1:8000` as the internal Django origin and the
  Google/GitHub local callback origin, not as the Facebook browser test URL.
- Do not use the Vite dev server at `http://127.0.0.1:5173` as the auth source
  of truth. It can preview frontend assets, but Django/allauth owns sign-in.
- Do not start extra app servers with ad hoc `python manage.py runserver`,
  `npm run dev`, `nohup`, background shell commands, or preview scripts during
  normal testing.
- Keep only one launcher-managed local app server active while testing auth.
- During active MLADIS UI/app work, keep that launcher-managed local server
  live for the owner. If an agent stops or restarts it to apply changes, the
  agent must bring it back through `./run_mladis_live.command` and verify
  `/healthz` before reporting that the work is ready.
- If the synced Google Drive path becomes slow or flaky, work from a fast clone
  such as `~/Documents/MLADIS-dev` and push changes through GitHub. Copy only
  `airbnb_agent/.env` from the Drive checkout when you need the same local
  secrets.
- On this Mac, the active fast checkout is
  `/Users/pitergarcia/Desktop/MLADIS-deploy-rebrand`. Do not run auth tests from
  older duplicate checkouts unless the owner explicitly tells you to switch.

## Provider Contract

- OAuth credentials are sourced from the canonical `airbnb_agent/.env` and synced
  into Django with `python manage.py sync_socialapps`.
- If provider buttons disappear or show setup/fallback states, verify `.env`
  presence first with boolean/length-only checks, run `sync_socialapps`, restart
  the launcher, and rerun this contract before touching templates.
- If `.env` is missing values, recover them only from an approved provider
  dashboard/secret manager or a prior known-working local database. Never print
  secrets and never create a second runtime as a workaround.
- `SOCIAL_AUTH_HIDDEN_PROVIDERS=microsoft` keeps Microsoft out of the login UI
  even if legacy credentials are present. Remove it only when Microsoft sign-in
  is intentionally part of the tested product surface.
- Google local origin: `SOCIAL_AUTH_GOOGLE_ORIGIN=http://127.0.0.1:8000`.
- GitHub local origin: `SOCIAL_AUTH_GITHUB_ORIGIN=http://127.0.0.1:8000`.
- Facebook local origin:
  `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com`.
- Production origin: `https://mladis.com`.
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

## Social Signup Completion Contract

- Provider emails that the provider marks as verified must remain verified in
  the allauth `SocialLogin.email_addresses` object. Do not downgrade trusted
  Google/GitHub/Microsoft email claims to `verified=False`; that breaks safe
  email authentication and forces existing users into the raw
  `/oauth/3rdparty/signup/` completion form.
- Existing MLADIS users with a verified matching email must be allowed to
  connect/login through the verified provider email path.
- If allauth still needs a final social-signup form, it must render the modern
  `socialaccount/signup.html` template, not the package default unstyled page.
- Social signup usernames must be generated from account data, not left as
  placeholders such as `User` or `Usuario`.

## Callback URLs

Register these exact callbacks for local testing:

```txt
Google:   http://127.0.0.1:8000/oauth/google/login/callback/
GitHub:   http://127.0.0.1:8000/oauth/github/login/callback/
Facebook: https://local.mladis.com/oauth/facebook/login/callback/
```

Register these exact callbacks for production:

```txt
Google:   https://mladis.com/oauth/google/login/callback/
GitHub:   https://mladis.com/oauth/github/login/callback/
Facebook: https://mladis.com/oauth/facebook/login/callback/
```

If `www.mladis.com` is allowed to start provider login before redirecting to the
apex domain, register matching `https://www.mladis.com/oauth/.../callback/`
URLs too. Random `trycloudflare.com` callbacks are not part of the normal
contract and should not be added to provider dashboards for routine testing.

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
- Facebook OAuth uses the stable HTTPS local callback.
- Production diagnostics use `https://mladis.com` callbacks.
- `/ops/oauth/` renders the staff OAuth diagnostics page with exact callbacks.
- The local launcher keeps the safer startup defaults and remains shell-valid.

## Launcher Contract

The launcher should be the one-file way to see normal code and UI changes:

- Code/UI changes are not ready for owner testing unless the local site is live
  at `http://127.0.0.1:8000` and, when the named tunnel is available,
  `https://local.mladis.com`.
- `MLADIS_PUBLIC_TUNNEL` defaults to `1`.
- `MLADIS_TUNNEL_MODE` defaults to `named`.
- `MLADIS_TUNNEL_NAME` defaults to `mladis-local`.
- `MLADIS_LOCAL_PUBLIC_HOSTNAME` defaults to `local.mladis.com`.
- `MLADIS_LOCAL_PUBLIC_ORIGIN` defaults to `https://local.mladis.com`.
- The launcher exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com`
  for that process unless `MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN` or an explicit
  shell `SOCIAL_AUTH_FACEBOOK_ORIGIN` is provided.
- `MLADIS_BUILD_FRONTEND` defaults to `1`, so React text/UI changes are rebuilt
  before Django starts.
- `MLADIS_RESTART_EXISTING` defaults to `1`, so stale local Django/tunnel
  processes on the same port are stopped first.
- The named Cloudflare tunnel routes `local.mladis.com` to
  `http://127.0.0.1:8000`, so normal UI/Django restarts do not rotate the
  Facebook callback URL.
- `MLADIS_TUNNEL_LOG` defaults to `/private/tmp/mladis-tunnel.log`; use this log
  to inspect named-tunnel startup if the Terminal scrollback moves.
- With default settings, the launcher stops stale Django listeners on the local
  port and stale `mladis-local` tunnel processes before starting the clean run.
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
- Use `MLADIS_TUNNEL_MODE=quick` only for emergency debugging when the named
  tunnel is unavailable. Quick-tunnel callbacks rotate and must not become the
  documented local Facebook process.

One-time Cloudflare setup for stable local Facebook testing:

```bash
cloudflared tunnel login
cloudflared tunnel create mladis-local
cloudflared tunnel route dns mladis-local local.mladis.com
```

This requires the Cloudflare account to manage the `mladis.com` DNS zone.
For this zone, Cloudflare assigned:

```txt
olof.ns.cloudflare.com
ophelia.ns.cloudflare.com
```

Replace the current Google nameservers with those Cloudflare nameservers at the
domain registrar/DNS provider before expecting `local.mladis.com` to resolve
from normal browsers.

## Troubleshooting

- Facebook says the connection is not secure: run `./run_mladis_live.command`
  and open `https://local.mladis.com`, not plain `http://127.0.0.1:8000`.
- Facebook says `URL blocked`: confirm Meta has
  `https://local.mladis.com/oauth/facebook/login/callback/` and
  `https://mladis.com/oauth/facebook/login/callback/` in Facebook Login ->
  Settings -> Valid OAuth Redirect URIs.
- Google says `redirect_uri_mismatch`: add
  `http://127.0.0.1:8000/oauth/google/login/callback/` to the Google OAuth app.
- GitHub says `redirect_uri` is not associated: add
  `http://127.0.0.1:8000/oauth/github/login/callback/` to the GitHub OAuth app.
- The page opens on `127.0.0.1:5173`: stop the Vite server for auth testing and
  run `./run_mladis_live.command`.
- The page opens on plain `127.0.0.1:8000` while testing Facebook: switch to
  `https://local.mladis.com`.
- `dig local.mladis.com` returns Cloudflare public IPs but browsers or Python
  still resolve `fd10:aec2:5dae::`: flush the Mac resolver cache with
  `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`, then retry
  `https://local.mladis.com`.
