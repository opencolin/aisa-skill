# AIsa as an LLM provider

One AIsa key reaches every model in the catalog. Connecting data tools does not need any of this, and changing a client's model provider affects all of its work, so do it only when the user asks.

## Endpoints

| SDK | Base URL | Paths | Auth |
| --- | --- | --- | --- |
| OpenAI | `https://api.aisa.one/v1` | `/chat/completions`, `/responses`, `/embeddings`, `/images/generations` | `Authorization: Bearer $AISA_API_KEY` |
| Anthropic | `https://api.aisa.one` | `/v1/messages` | `x-api-key: $AISA_API_KEY` |
| Google Gen AI | `https://api.aisa.one` | `/v1beta/models/{model}:generateContent` | `x-api-key: $AISA_API_KEY` as an extra header |

The Anthropic SDK adds `/v1/messages` itself, so its base URL has no `/v1`. AIsa does not read Google's `x-goog-api-key` header.

## Pick a model

`GET https://api.aisa.one/v1/models` is free. Use only IDs it returns, and do not reuse IDs from memory.

- Check `aisa.model_type` and `aisa.capabilities`. Do not assume a model supports something because its family does.
- Use the route in `aisa.preferred_route` when present. Otherwise choose from `aisa.routes`.
- Do not pick an image, video, embedding, Whisper or TTS model as the main chat model.
- Prices are at https://aisa.one/models.

A successful `/v1/models` call doesn't prove account access. Verify with `GET /v1/credits/balance`.

## Code

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["AISA_API_KEY"], base_url="https://api.aisa.one/v1")
reply = client.chat.completions.create(
    model="<id from /v1/models>",
    messages=[{"role": "user", "content": "Hello"}],
)
```

```python
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["AISA_API_KEY"], base_url="https://api.aisa.one")
```

## Claude Code

Set these in the shell or under `env` in `~/.claude/settings.json`. Choose the API-key option when Claude Code asks you to log in.

```bash
export ANTHROPIC_BASE_URL="https://api.aisa.one"
export ANTHROPIC_AUTH_TOKEN="$AISA_API_KEY"
export ANTHROPIC_MODEL="<claude id from /v1/models>"
export ANTHROPIC_SMALL_FAST_MODEL="<claude id from /v1/models>"
```

Claude Code doesn't load Claude connectors with an auth token, so add AIsa tools with `claude mcp add`.

## Codex

Add this to `~/.codex/config.toml`, with `AISA_API_KEY` exported. Codex reads the key at runtime, so it never lands in the file.

```toml
model = "<id from /v1/models>"
model_provider = "aisa"

[model_providers.aisa]
name = "AIsa"
base_url = "https://api.aisa.one/v1"
env_key = "AISA_API_KEY"
wire_api = "responses"
```

## Limits and billing

- Some models cap successful calls per rolling window. The response is `429` with `model_success_rate_limit_exceeded` and a `Retry-After` header.
- Failed calls don't count toward that cap.
- LLM calls bill per token from the same balance as data calls, and there is no quote step for them.

More: https://aisa.one/docs/get-started/sdk-compatibility and https://aisa.one/docs/guides/models.md
