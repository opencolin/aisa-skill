# Book a flight through AIsa

AIsa proxies Duffel for flight search, booking, holds, seat maps, changes and cancellations. A booking charges the whole fare, so this is real money. Get explicit approval at every paid step.

The x402 flow below was tested live on October 5, 2026. Duffel tools also appear in MCP `search`, such as `post_duffel_offer_requests_create` and `post_duffel_orders_create`, but booking through them hasn't been tested. Both report `read_only: false` and "do not retry automatically". If you use MCP, quote every call and keep the same review steps.

Complete the setup and wallet steps in `x402-arc.md` first.

## Endpoints

Base URL `https://api.aisa.one`. Inspect the live 402 for every price, because spec prices were wrong in testing.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/apis/v2/duffel/flights/offer-requests/create` | POST | Flight search |
| `/apis/v2/duffel/flights/offer-requests/{id}` | GET | Retrieve a search and its offers |
| `/apis/v2/duffel/flights/offers/{id}` | GET | Refresh one offer, with the authoritative price and expiry |
| `/apis/v2/duffel/flights/orders/create` | POST | Book. Pays the fare and returns the PNR and e-ticket |
| `/apis/v2/duffel/flights/orders/hold-create` | POST | Hold without immediate payment |
| `/apis/v2/duffel/flights/seat-maps` | GET | Seat maps for an offer |
| `/apis/v2/duffel/flights/order-change-requests/create`, `/apis/v2/duffel/flights/order-changes/create` | POST | Changes |
| `/apis/v2/duffel/flights/order-cancellations/create`, `/order-cancellations/{id}`, `/order-cancellations/{id}/confirm` | POST, GET | Cancellations |

Search body:

```json
{"data":{"slices":[{"origin":"SFO","destination":"LGA","departure_date":"2026-12-06"}],
"passengers":[{"type":"adult"}]}}
```

`SliceInput` needs `origin`, `destination` (IATA) and `departure_date` (YYYY-MM-DD). `PassengerInput` takes `type: "adult"`, or `age` for under-18s.

## Booking flow

1. **Search.** `pay` the search with `-X POST -d '<body>'` and a `--max-amount` above the live price. Save the full response. The offers array is large, so parse it rather than buying it again.
2. **Shortlist 3 to 6 offers** with airline, times, stops, duration and total. Inventory is whatever the proxy returns.
3. **Refresh the chosen offer** through `offers/{id}` right before ordering. The returned price and `expires_at` are authoritative.
4. **Fund it.** The `orders/create` payment equals the entire fare (`BalancePayment`: `type: "balance"`, `amount` is the refreshed `total_amount`, `currency` is the offer currency). The settled charge is the fare plus a small service fee. The Gateway balance must cover all of it, so get explicit approval for the deposit amount.
5. **Collect passenger details.** `BookingPassenger` needs `id` (from the offer request response), `title` (mr, ms, mrs, dr), `gender` (m, f, x), `given_name`, `family_name`, `born_on` (YYYY-MM-DD), `email` and `phone_number`.
6. **Show the full purchase review** and get explicit approval: itinerary with times and airports, airline and flight numbers, fare breakdown, passenger names, total with service fee, and payer address.
7. **Book.** `pay` `orders/create` with `-X POST` and the booking body. Verify HTTP 201, `booking_reference` (PNR) and `electronic_ticket` documents.

## Gotchas

- A 422 means validation failed, the offer expired or the amount didn't match. You weren't charged. Refresh and review again, and never retry blindly.
- A mismatch of even $0.01 returns 422, so always use the refreshed total.
- `payment_required_by` and `expires_at` are real deadlines, so don't let a review sit.
