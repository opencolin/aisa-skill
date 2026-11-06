# AIsa data APIs

Read this after connecting. `SKILL.md` covers the search, quote and run flow and the spending rules.

## Recipes

Pass these queries to `search`. Tool names change, so these are what search returned on November 6, 2026. Always use what it returns now.

| Goal | Query | Tools returned |
| --- | --- | --- |
| Public X profile | "look up a public X profile by handle" | `get_twitter_user_info` |
| Instagram profile | "instagram profile by handle" | `get_instagram_profile` |
| Page text from a URL | "extract clean text from a URL" | `post_tavily_extract`, `post_exa_contents` |
| Keyword metrics | "keyword search volume and difficulty" | `get_semrush_keyword_difficulty`, `post_dataforseo_ai_keyword_volume_live` |
| AI visibility | "how often is a brand mentioned in ChatGPT answers" | `post_dataforseo_ai_llm_mentions_aggregated_metrics_live` |
| Stock brief | "price, latest earnings and insider trades for a ticker" | `get_financial_prices_snapshot`, `get_financial_earnings`, `get_financial_insider_trades` |
| Prediction markets | "polymarket market prices" | `get_any_polymarket_clob_apis_v1_polymarket_prices` |
| Person by email | "enrich a person by email with title and company" | `post_apollo_people_match`, `post_apollo_people_bulk_match` |
| Company by domain | "company firmographics by domain" | `get_apollo_organizations_enrich`, `get_akta_company_enrichment` |

For a broad task such as a company brief, search the full goal first. Search can return a Plan. A Plan may cover only part of the task, so read its `next_steps_guidance`.

When a decision depends on a number, cross-check two providers. Domain authority and backlinks, for example, are available from several sources.

## Gotchas

- Parameter names differ between tools. X uses `userName` and Instagram uses `handle`, so read the schema.
- Search always returns something. "Verify whether an email is deliverable" returned Apollo and TikTok tools, and none of them verify email. The catalog lists email checks as "Soon".
- `post_apollo_organizations_bulk_enrich` takes up to 10 domains. For a company known only by name, use a search tool such as `post_apollo_mixed_companies_search`.
- Duffel search tools report `read_only: false`, so don't assume a tool is read-only from its name.

## Bulk jobs

Lists of hundreds or thousands of rows need more care than a single call, because small errors in an estimate multiply.

1. **Use cheaper sources first.** Send only the rows they miss to a paid lookup.
2. **Remove duplicates and cache results** by a stable key, so a rerun costs nothing.
3. **Get approval for a pilot budget, then run a pilot** of 100 to 200 rows from the real list. Measure settled cost, match rate and useful fields. Rows at the top of a sorted list can behave differently from the rest.
4. **Give the user the total** from the pilot, a stop condition and a time estimate. Wait for approval. Quote each batch as you run it, and stop if the running total would pass the budget.
5. **Batch where the tool allows it,** and pace requests.
6. **Check every paid dependency's balance before starting.** Stop on `402`, and stop if the balance falls to an agreed floor.
7. **Report actual cost against the estimate.**

### Apollo field notes

- `post_apollo_people_bulk_match` takes 10 people per call.
- A 6,945-person run in November 2026 matched 77% and cost about $0.018 per match.
- Search lists this tool at $1.78 per call as a metered reference. A real 10-person call settled near $0.15, so measure before estimating.

## CLI

The flow matches MCP. `quote` and `call` take the same `calls` JSON.

```sh
aisa search --input '{"query":"<user goal>"}' --json
aisa schema <tool>
aisa quote --input '{"calls":[{"call_id":"c1","tool":"<tool>","arguments":{}}]}' --json
aisa call --input '{"calls":[{"call_id":"c1","tool":"<tool>","arguments":{}}]}' --json
```

Run `aisa schema` when `has_full_schema` is false. `aisa balance` and `aisa usage` show the balance and usage. Full guide: https://aisa.one/docs/get-started/cli.md

## Direct HTTP

**Gate:** MCP and the CLI are both unavailable, HTTP works, and a valid key already exists in `AISA_API_KEY` or the client's secret store. Do not read `~/.aisa/tokens.json` or `~/.aisa/key`.

**Approval is stricter here.** A request to collect data is not approval. Before any paid call:

1. Read the endpoint's page in the [API reference](https://aisa.one/docs/api-reference) and its published pricing.
2. Tell the user the exact endpoint and scope, the rate, and the maximum USD exposure.
3. Wait for a separate message approving that scope and cap.
4. If there's no documented maximum, stop and say so.

Full rule: https://aisa.one/docs/get-started/cli.md#direct-http-fallback

| Item | Value |
| --- | --- |
| Data base URL | `https://api.aisa.one/apis/v1` |
| Auth | `Authorization: Bearer $AISA_API_KEY` |
| Free quote, where supported | Request header `X-AISA-Cost-Mode: quote` |
| Price limit, where supported | Request header `X-AISA-Max-Price-USD` |
| Safe retries, where supported | Request header `Idempotency-Key` |
| Settled cost | Response header `X-AISA-Customer-Cost-Micros-USD` |

Example, after approval:

```sh
curl -s https://api.aisa.one/apis/v1/apollo/people/bulk_match \
  -H "Authorization: Bearer $AISA_API_KEY" -H "Content-Type: application/json" \
  -d '{"details":[{"email":"person@example.com","first_name":"Pat","last_name":"Lee"}]}'
```

The response has a `matches` array in request order, with an empty entry when Apollo found no one.
