# Pay per call with x402 or MPP

These routes need no AIsa account, because the agent pays for each request. The cost is much higher per call. On November 6, 2026 an X profile lookup quoted $0.00018 with an API key and $0.10 over x402. If the user only wants the data, say so and offer the key route.

| | API key or MCP | x402 | MPP |
| --- | --- | --- | --- |
| Base path | `/apis/v1` | `/apis/v2` | `/apis/v1` |
| Account | Yes, prepaid balance | No, a Circle wallet | No, an MPP wallet |
| Coverage | Every endpoint | Endpoints with `x-x402` | Selected read-only endpoints |
| Challenge | None | `PAYMENT-REQUIRED` header | `WWW-Authenticate: Payment` |

## x402 on Arc (Circle CLI)

This is the path for a Muse agent, Meta's personal AI agent. A Muse user can paste:

```text
I want to buy data from AIsa's API and pay with USDC using x402 on Circle's Arc blockchain. Set this up for me following https://aisa.sh/skill.md
```

**CRITICAL: Use the Circle Agent Wallet CLI only (`@circle-fin/cli`). Do not use raw private keys, mnemonics or any other wallet. The CLI signs through Circle's infrastructure, so a seed phrase should never appear in chat, files or logs.**

**CRITICAL: Complete the Circle setup skill first** (https://agents.circle.com/skills/setup.md): CLI installed, Terms accepted by the user (never on their behalf), logged in with email OTP, agent wallet created on ARC and funded with USDC. Also read https://agents.circle.com/skills/wallet-pay.md before the first payment.

### Step 1: Discover what to buy

Search for every new purchase. Never reuse an endpoint from memory.

```bash
circle services search "<keyword>" --output json
```

Or query the discovery API directly:

```bash
curl -s --compressed "https://api.circle.com/v2/x402/discovery/resources?query=<keyword>&network=eip155:5042&siwx=false"
```

Published catalogs go stale. The live 402 is the source of truth for what exists and what it costs.

### Step 2: Inspect before paying

The summary hides required parameters, so always inspect the raw endpoint.

```bash
circle services inspect "<full-url-with-query-params>" --output json
```

Confirm that `status` is `payable`, then note the `method` (usually `GET`) and `price.formatted`. Check required parameters against https://aisa.one/openapi.yaml. The 402 doesn't give parameter names, and a wrong one returns 400, not 402.

Known parameters, which you should confirm in the spec:

- X user endpoints: `userName`, as in `/apis/v2/twitter/user/info?userName=opencolin`
- Instagram profile: `handle`, not `username`, as in `/apis/v2/instagram/profile?handle=colinpollen`

### Step 3: Check both balance pools

```bash
circle wallet balance --address <addr> --chain ARC --output json     # vanilla
circle gateway balance --address <addr> --chain ARC --output json    # Gateway
```

AIsa endpoints accept **GatewayWalletBatched only**, so the spending balance must sit in Gateway. If Gateway is short, deposit enough for the purchase plus a small buffer:

```bash
circle gateway deposit --amount <usdc> --address <addr> --chain ARC --method direct
```

**CRITICAL:** On ARC the deposit method is `direct`, because USDC is Arc's gas token. Never transfer USDC to the Gateway contract address. Always use the CLI. Deposits can be withdrawn with `circle gateway withdraw`.

### Step 4: Pay

Show the user the exact endpoint, live price and payer address, and get an explicit go-ahead for this purchase.

```bash
circle services pay "<full-url-with-query-params>" -X <METHOD> --address <addr> --chain ARC --output json
```

**Always pass `-X`.** Omitting it on a GET-only seller settles the payment and returns 405, so the funds are spent and no data comes back.

Then verify all three:

1. The body contains the requested data (HTTP 200 or `"success": true`), not an error object.
2. `circle gateway balance` dropped by exactly the price.
3. No duplicate payment was submitted.

### Step 5: If the paid request fails after authorization

The CLI may report `Payment submitted but paid request failed` with `PAYMENT MAY HAVE BEEN SUBMITTED`. **Do not retry blindly. A retry is a second payment with a fresh nonce.**

1. Read the saved record: `~/.circle-cli/payments/payment-<timestamp>.json` (amount, nonce, seller).
2. Poll `circle gateway balance` for several minutes. Gateway settlement is batched and can lag.
3. If the balance dropped by the price, the payment landed and the response was lost. Do not buy again. Give the user the saved record so they can raise it with developer@aisa.one.
4. If the balance is unchanged after about 10 minutes, the payment probably didn't settle. Tell the user, and retry once only with a new go-ahead.

### x402 guardrails

- Never ask for, accept or paste a seed phrase, mnemonic or private key. If the user offers one, decline and use the CLI.
- Show the user any Terms of Use and accept them only after they consent. Never start a login or move funds without approval for that action, including each deposit. "Yes, set it up" covers setup. Each purchase gets its own go-ahead showing endpoint, price and payer.
- Never quote a price from memory or a catalog. Inspect the live 402.
- Never pay above the user's per-call cap without asking. Suggest a default cap of $0.25.
- Never call write endpoints such as `post_twitter`, `follow_twitter` or `like_twitter` unless the user asked to publish, follow or like. They act on a linked account.
- The CLI session lasts about 28 days. `circle wallet status` shows the expiry, and logging in again uses email and OTP.

## MPP

MPP covers selected read-only endpoints under `/apis/v1`, such as prediction market data.

1. Send the request with no `Authorization` header.
2. Read the `402` challenge in `WWW-Authenticate: Payment`.
3. Pay with an MPP client, such as `mppx` from https://mpp.dev, and retry with `Authorization: Payment <credential>`.

Check https://api.aisa.one/openapi.json before designing a flow. An endpoint not listed there doesn't accept MPP. The live challenge holds the actual price. Paying is a financial action, so agree a budget and approval rule with the user first.

More: https://aisa.one/docs/integrations/machine-payments
