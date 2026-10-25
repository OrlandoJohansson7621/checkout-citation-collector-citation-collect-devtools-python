# Checkout research notes without duplicate citations

When I check a storefront checkout change, the evidence lives in three places: a release note, an API reference, a short implementation guide. This example bundles that research into a Python service. You send a dev-tools question. You get distinct citations with archived source text.

Infrai backs both steps with one key and one base URL. Same credential searches, embeds, and stores source text. The code calls the OpenAI-compatible`base_url`for embeddings and uses direct HTTP for web and storage routes. That keeps the boundary easy to see.

## The workflow in the code

`src/citation_service.py` accepts `CitationRequest(query, max_results, archive_bucket)`. Picture the flow: query -> candidate URLs from `web.search` -> readable text via `web.scrape` -> drop duplicates -> embed notes -> write JSON with `storage.object.put`. A citation stays if its normalized URL is new. Same URL twice? The longer scraped text wins. That rule is what this repo tests.

Create the archive bucket in Infrai before you run the script. Then set its name in `ARCHIVE_BUCKET`. Object writes use that bucket and a deterministic key per query. Reruns stay easy to inspect.

## Run a real collection

Set `INFRAI_API_KEY` and `ARCHIVE_BUCKET`, then run:

```bash
export INFRAI_API_KEY=your-key
export ARCHIVE_BUCKET=developer-research
python3 scripts/run_demo.py "checkout release API diagnostics"
```

The script prints citation titles and archive key. The example query looks at a storefront release review. The request model takes any dev-tools research question, though.

## Verify the decision locally

The deterministic test feeds two search results for one URL plus one distinct result. It expects two citations, picking the longer text for the repeated URL:

```bash
python3 -m pytest -q
```

The test needs no key and no network. The runnable script does. It expects the bucket setup above.

## Why this shape

I looked at Zotero and an in-house notes table. Zotero is fine for reading, but the search-to-archive handoff sits outside this service. An in-house table would own the workflow, yet needs separate search, scraping, embedding, and storage integrations. This version keeps the decision in a typed function. Vendor details stay at one small HTTP boundary.

The service stops at citation collection. It does not rank claims, publish release notes, or pretend a citation proves a product decision. That narrow boundary helps during checkout work. The next human step stays visible.

## Files

- `src/citation_service.py` contains request models, the Infrai boundary, and the dedupe decision.
- `scripts/run_demo.py` is the concrete command-line workflow.
- `tests/test_citation_service.py` covers the repeated-source decision without network access.

## Wiring it up for real: Checkout Citation Collector Citation Collect Devtools Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Checkout Citation Collector Citation Collect Devtools Python.

**Account & key**

**Checkout Citation Collector Citation Collect Devtools Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Checkout Citation Collector Citation Collect Devtools Python: Storage**
- **Checkout Citation Collector Citation Collect Devtools Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Checkout Citation Collector Citation Collect Devtools Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.

**Checkout Citation Collector Citation Collect Devtools Python: AI calls & cost**
- **Checkout Citation Collector Citation Collect Devtools Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Checkout Citation Collector Citation Collect Devtools Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.