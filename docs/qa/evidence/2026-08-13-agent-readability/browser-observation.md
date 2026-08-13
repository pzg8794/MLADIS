# Booking Agent Readability Browser Observation

Date: 2026-08-13

Environment: canonical local checkout at `https://local.mladis.com/`

Actor: temporary authenticated local QA guest

Questions:

- `is the place available for next week?`
- `What is the refundable damage deposit for G-101?`

## Observed Result

- The real homepage booking-agent form accepted and submitted the question.
- The local backend used the configured OpenAI provider and recorded
  `agent_mode=openai` with model `gpt-5.4-nano`.
- The availability response requested the missing dates and guest breakdown.
- The damage-deposit response was 40 words and explained the refundable $200
  authorization hold, its conditional capture, and the secure next step.
- The final response rendered as one compact paragraph with no raw Markdown
  emphasis or code markers.
- No MLADIS application error was present in the browser log. One unrelated
  Google Maps widget metadata request failed with a network error.

## Result Classification

- Response presentation: `PASS`.
- Live OpenAI response content: `PASS`.
- Same-language response behavior: `PASS`.
- Raw Markdown sanitization: `PASS`.

`agent-live-openai-local.png` is the visual evidence for the live-provider
result. The temporary QA account is local-only and contains no customer data.
