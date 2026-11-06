# AIsa skill

One installable agent skill for connecting to AIsa and using its data APIs, LLMs and pay-per-call routes.
Plan: https://claude.ai/artifact/GtumdbwjW3i6ErNBsT8HXA

## Publish at aisa.sh

Publish these together, because `skill.md` links to the reference files by relative path:

| Source | URL |
| --- | --- |
| `aisa/SKILL.md` | `https://aisa.sh/skill.md` |
| `aisa/references/data-apis.md` | `https://aisa.sh/references/data-apis.md` |
| `aisa/references/llms.md` | `https://aisa.sh/references/llms.md` |
| `aisa/references/x402-arc.md` | `https://aisa.sh/references/x402-arc.md` |
| `aisa/references/flights.md` | `https://aisa.sh/references/flights.md` |

Existing Muse prompts point at `aisa.sh/skill.md` and now reach the x402 steps through `references/x402-arc.md`, so that file must be live when `skill.md` changes.

The target home is `aisa.one/skill.md`. The same files work there unchanged. Ellie and Haoyang review on the AIsa side.

## Check before publishing

```bash
AISA_API_KEY=... python3 check_skill.py
```

It makes free calls only. Without the key it skips the live MCP tool check.

## Moving into AIsa-team/agent-skills

The folder goes to `platform/aisa/`. That repo also requires:

- the generated `aisa-rules` block from `_shared/aisa-rules.md` in `SKILL.md`
- an updated `skill.json`
- a new digest in `.well-known/agent-skills/index.json`

## Issues for the AIsa team

Found while building this on November 6, 2026:

1. **Official skill tool names:** `platform/aisa/SKILL.md` lists `AISA_SEARCH_TOOL` and similar. The server exposes `search`, `batch_get_schema`, `batch_quote` and `batch_use`.
2. **Auth check drift:** `_shared/aisa-rules.md` verifies HTTP with `/v1/models`. `llms.txt` says to use `/v1/credits/balance`.
3. **Pinned manual install:** the docs pin a 3.7 KB `SKILL.md`. The current file is 9.9 KB.
4. **Agent mail:** `llms.txt` suggests "Give this agent its own inbox", but `list_categories` shows the `mail` module with 0 tools and search finds no AgentMail tools.
5. **Stale tool name:** the quickstart and doc headers still say `get_details`. The server lists `batch_get_schema`.
6. **Metered prices in search:** `post_apollo_people_bulk_match` lists $1.78 per call, while a real 10-person call settled near $0.15.
