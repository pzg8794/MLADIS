# Booking Agent Readability Browser Observation

Date: 2026-08-13

Environment: canonical local checkout at `https://local.mladis.com/`

Actor: temporary authenticated local QA guest

Question: `is the place available for next week?`

## Observed Result

- The real homepage booking-agent form accepted and submitted the question.
- The local backend returned setup mode because the approved local `.env` has
  no `OPENAI_API_KEY`.
- The response rendered as one heading, one paragraph, and three numbered steps.
- Response word count: 63.
- Computed font size: 13.12px.
- Computed font weight: 620.
- Computed line height: 19.4176px.
- Maximum response height: 360px with vertical overflow enabled.
- No application error was present in the browser log. The only log entries
  were Google Maps embed debug messages.

## Result Classification

- Response presentation: `PASS`.
- Setup-mode response behavior: `PASS`.
- Live OpenAI response content: `BLOCKED` because the approved local
  environment has no configured key.

The screenshot in this directory is the visual evidence for the presentation
result. This observation does not claim that the live-provider response works
locally.
