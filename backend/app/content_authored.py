"""Hand-authored comprehensive learning content — same rich shape as
content_generated.py, but written by hand (Opus) rather than via the Anthropic
API. This is a COMMITTED source of truth.

The seeder treats these topics as AUTHORITATIVE (their points are the canonical
set — curated/older points on the same topic are pruned) and `_enrich.py` never
regenerates them (their titles are in its skip set).

Format
------
AUTHORED: dict[topic_title, {
    "points": [ {"title", "notes", "explanation", "resources": [
                  {"title", "url", "kind", "query"} ]} , ... ],
    "example": [str, ...],   # concrete practice prompts
    "common":  [str, ...],   # conceptual interview questions
}]
AUTHORED_ORDER: dict[domain_name, [ {"title", "level"} , ... ]]
    # list order → path_order (1-based); level ∈ foundational|intermediate|advanced

`explanation` is markdown: headings, lists, `code`, KaTeX ($…$ / $$…$$), and
```mermaid``` diagrams render in the UI. Only include a resource `url` when it is
a real, stable link; otherwise leave it empty and give a `query` (the UI links to
a YouTube/Google search so it can never be dead).
"""

AUTHORED: dict[str, dict] = {
    # ------------------------------------------------------------------ SD ---
    "System design interview framework + capacity estimation": {
        "points": [
            {
                "title": "A repeatable framework: requirements → estimate → API → data → design → deep-dive",
                "notes": "Drive every design through the same 7 steps so you never freeze or ramble.",
                "explanation": (
                    "### Why a framework\n"
                    "A 45-minute design interview rewards a *structured* approach far more than clever tricks. "
                    "Walk the same path every time so you spend thought on the problem, not on what to do next:\n\n"
                    "1. **Clarify requirements** — functional (what it does) + non-functional (scale, latency, consistency).\n"
                    "2. **Back-of-envelope estimates** — QPS, storage, bandwidth, memory. Sets the scale you must design for.\n"
                    "3. **API design** — the handful of endpoints; nail the contract before internals.\n"
                    "4. **Data model** — entities, access patterns, SQL vs NoSQL, what to index.\n"
                    "5. **High-level design** — boxes and arrows: clients → LB → services → storage/cache/queue.\n"
                    "6. **Deep dives** — go deep where it matters (the bottleneck, the interesting tradeoff).\n"
                    "7. **Bottlenecks & wrap-up** — single points of failure, scaling the hot path, what you'd do with more time.\n\n"
                    "```mermaid\nflowchart LR\n  A[Requirements] --> B[Estimates]\n  B --> C[API]\n  C --> D[Data model]\n  D --> E[High-level design]\n  E --> F[Deep dives]\n  F --> G[Bottlenecks]\n```\n\n"
                    "Spend ~5 min on steps 1–2, ~10 on 3–5, and the bulk on deep dives — that's where senior signal lives."
                ),
                "resources": [
                    {"title": "system-design-primer (donnemartin)", "url": "https://github.com/donnemartin/system-design-primer", "kind": "docs", "query": "system design primer github"},
                    {"title": "System Design Interview — Alex Xu (book)", "url": "", "kind": "book", "query": "System Design Interview Alex Xu volume 1"},
                ],
            },
            {
                "title": "Clarify functional vs non-functional requirements first",
                "notes": "Pin down what to build and at what scale/SLA before drawing anything.",
                "explanation": (
                    "### Two kinds of requirements\n"
                    "- **Functional** — the features: 'shorten a URL and redirect', 'post a tweet, read a timeline'. Keep the scope small and explicit; ask what's *out* of scope.\n"
                    "- **Non-functional** — the qualities that drive architecture: expected **scale** (users, QPS), **latency** target (e.g. p99 < 200 ms), **availability** (99.9% vs 99.99%), **consistency** (strong vs eventual), durability, read/write ratio.\n\n"
                    "The non-functional answers *decide the design*: a read-heavy 100:1 system leans on caching and replicas; a strongly-consistent one rules out async replication on the write path. "
                    "Always ask: how many users, what's the read:write ratio, and is stale data acceptable?"
                ),
                "resources": [
                    {"title": "Functional vs non-functional requirements", "url": "", "kind": "article", "query": "functional vs non-functional requirements system design"},
                ],
            },
            {
                "title": "Back-of-envelope: estimating QPS (read & write)",
                "notes": "Convert DAU + per-user actions into average and peak requests/second.",
                "explanation": (
                    "### From users to QPS\n"
                    "Start with **daily active users (DAU)** and actions per user per day:\n\n"
                    "$$\\text{avg QPS} = \\frac{\\text{DAU} \\times \\text{actions/user/day}}{86{,}400}$$\n\n"
                    "Then apply a **peak factor** (typically 2–10×) for bursty traffic:\n\n"
                    "$$\\text{peak QPS} \\approx \\text{avg QPS} \\times 3 \\text{–} 10$$\n\n"
                    "Worked example: 100 M DAU each making 10 reads/day → $10^9$ reads/day $\\div 86{,}400 \\approx 11{,}600$ avg read QPS, so design for ~**50–100k peak read QPS**. "
                    "Split reads vs writes (often 100:1 for social feeds) — they scale differently. Round aggressively; the goal is the *order of magnitude*, not precision."
                ),
                "resources": [
                    {"title": "Back-of-the-envelope estimation", "url": "", "kind": "article", "query": "back of the envelope estimation system design qps"},
                ],
            },
            {
                "title": "Estimating storage",
                "notes": "Bytes per record × records/day × retention → total storage (and growth/yr).",
                "explanation": (
                    "### Storage math\n"
                    "$$\\text{storage} = \\text{writes/day} \\times \\text{bytes/write} \\times \\text{retention (days)}$$\n\n"
                    "Example: 5 M tweets/day × 300 bytes (text + metadata) = 1.5 GB/day of text → ~**0.5 TB/year**. "
                    "Media dominates: 1 M photos/day × 1 MB = 1 TB/**day**. Always separate small structured records (DB) from large blobs (object store/CDN). "
                    "Add a **replication factor** (×3 is common) and headroom for indexes. State your assumptions out loud — interviewers grade the reasoning, not the digits."
                ),
                "resources": [
                    {"title": "Powers of two & data sizes", "url": "", "kind": "article", "query": "data storage estimation system design powers of two"},
                ],
            },
            {
                "title": "Estimating bandwidth and memory (the 80/20 cache rule)",
                "notes": "Bandwidth = QPS × payload; cache the hot 20% that serves 80% of reads.",
                "explanation": (
                    "### Bandwidth\n"
                    "$$\\text{bandwidth} = \\text{QPS} \\times \\text{avg response size}$$\n"
                    "50k read QPS × 2 KB = 100 MB/s ≈ 800 Mbps — fine for a few servers; 50k × 1 MB (media) = 50 GB/s needs a CDN.\n\n"
                    "### Cache memory\n"
                    "Use the **80/20 rule**: ~20% of data drives ~80% of reads. To cache that hot set:\n\n"
                    "$$\\text{cache} \\approx 0.2 \\times \\text{daily read volume in bytes}$$\n\n"
                    "If you read 2 TB/day, a ~400 GB cache (a few Redis nodes) covers the hot set. This justifies *why* you add a cache, with numbers."
                ),
                "resources": [
                    {"title": "Caching at scale (overview)", "url": "", "kind": "article", "query": "cache hit ratio 80 20 rule system design"},
                ],
            },
            {
                "title": "Latency numbers every engineer should know",
                "notes": "Memory ~100 ns, SSD ~100 µs, network RT within DC ~0.5 ms, cross-region ~50–150 ms.",
                "explanation": (
                    "### Order-of-magnitude latencies (Jeff Dean's numbers)\n"
                    "| Operation | ~Latency |\n|---|---|\n"
                    "| L1 cache reference | 1 ns |\n"
                    "| Main memory reference | 100 ns |\n"
                    "| Read 1 MB sequentially from memory | ~10 µs |\n"
                    "| SSD random read | ~100 µs |\n"
                    "| Round trip within a datacenter | ~500 µs |\n"
                    "| Read 1 MB from SSD | ~1 ms |\n"
                    "| Disk (HDD) seek | ~10 ms |\n"
                    "| Round trip CA ⇄ Netherlands | ~150 ms |\n\n"
                    "Takeaways: **memory is ~1000× faster than SSD**, **SSD ~100× faster than HDD seek**, and **cross-region is ~100× a same-DC hop**. "
                    "These explain why we cache in RAM, keep replicas in-region, and avoid chatty cross-service calls on the hot path."
                ),
                "resources": [
                    {"title": "Latency Numbers Every Programmer Should Know", "url": "", "kind": "article", "query": "latency numbers every programmer should know"},
                ],
            },
            {
                "title": "Powers of two and the units cheat sheet",
                "notes": "2^10≈1K, 2^20≈1M, 2^30≈1B; map to KB/MB/GB/TB instantly.",
                "explanation": (
                    "### Know your powers of two\n"
                    "| Power | ≈ Value | Name |\n|---|---|---|\n"
                    "| $2^{10}$ | 1 thousand | 1 KB |\n"
                    "| $2^{20}$ | 1 million | 1 MB |\n"
                    "| $2^{30}$ | 1 billion | 1 GB |\n"
                    "| $2^{40}$ | 1 trillion | 1 TB |\n"
                    "| $2^{32}$ | ~4 billion | (max unsigned 32-bit) |\n"
                    "| $2^{63}$ | ~9.2 × 10¹⁸ | (max signed 64-bit) |\n\n"
                    "Handy facts: a day ≈ **86,400 s ≈ $10^5$**; a year ≈ **$3.15 \\times 10^7$ s**. "
                    "A 64-bit ID space is effectively infinite for record counts; a 32-bit one (~4 B) can overflow at internet scale — which is why ID sizing comes up in URL-shortener and ID-generator designs."
                ),
                "resources": [],
            },
            {
                "title": "Sizing the fleet: servers, shards, replicas",
                "notes": "fleet = peak QPS ÷ per-node capacity, then add replicas & headroom.",
                "explanation": (
                    "### From QPS to machine count\n"
                    "$$\\text{servers} = \\left\\lceil \\frac{\\text{peak QPS}}{\\text{QPS per node}} \\right\\rceil \\times \\text{headroom}$$\n\n"
                    "If a node serves ~5k QPS and peak is 80k, you need ~16 nodes — call it **~24 with headroom** for failover and spikes. "
                    "**Shards** are sized by data/throughput per shard ($\\text{data} \\div \\text{per-shard capacity}$); **replicas** (×3 typical) give availability and read scaling. "
                    "Tie it back: 'N shards × 3 replicas = 3N nodes' makes capacity, cost, and fault tolerance concrete in one sentence."
                ),
                "resources": [],
            },
            {
                "title": "Driving the conversation and managing the clock",
                "notes": "Lead the structure, narrate tradeoffs, and time-box; treat the interviewer as a teammate.",
                "explanation": (
                    "### It's a collaboration, not a quiz\n"
                    "- **Lead the structure** — announce each step ('let me start with requirements'). Silence reads as being stuck.\n"
                    "- **Think out loud** — verbalize options and *why* you pick one; the reasoning is the signal.\n"
                    "- **Time-box** — don't over-engineer the easy parts. Get a working end-to-end design fast, then deepen.\n"
                    "- **Check in** — 'Does it make sense to deep-dive on the feed fan-out?' invites steering.\n"
                    "- **Handle hints** — interviewers nudge toward the part they want explored; follow it.\n\n"
                    "A clear, well-paced 'good' design beats a brilliant but rushed/rambling one."
                ),
                "resources": [],
            },
            {
                "title": "Articulating tradeoffs — the senior signal",
                "notes": "Every choice has a cost; name the alternative and why you rejected it.",
                "explanation": (
                    "### Show the tradeoff, not just the answer\n"
                    "Seniority shows in *comparisons*, not facts. For each major decision, state the alternative and the cost:\n\n"
                    "- **SQL vs NoSQL** — relations/transactions vs horizontal scale + flexible schema.\n"
                    "- **Strong vs eventual consistency** — correctness vs availability/latency (CAP/PACELC).\n"
                    "- **Sync vs async (queue)** — simplicity vs throughput + decoupling at the cost of complexity.\n"
                    "- **Normalization vs denormalization** — write simplicity vs read speed.\n"
                    "- **Push vs pull (fan-out)** — read latency vs write amplification for celebrity accounts.\n\n"
                    "Phrase it as: 'I'd choose X because we're read-heavy and can tolerate stale data; the cost is Y, which we mitigate with Z.'"
                ),
                "resources": [
                    {"title": "CAP theorem & PACELC", "url": "", "kind": "article", "query": "CAP theorem PACELC explained"},
                ],
            },
            {
                "title": "Common mistakes that sink the interview",
                "notes": "Jumping to internals, ignoring scale, no tradeoffs, over-engineering, going silent.",
                "explanation": (
                    "### Avoid these\n"
                    "- **Designing before clarifying** — you build the wrong thing.\n"
                    "- **Skipping estimates** — your design has no scale to justify caches/shards/queues.\n"
                    "- **One 'right' answer with no tradeoffs** — reads as junior.\n"
                    "- **Over-engineering** — adding Kafka/microservices to a problem that doesn't need them.\n"
                    "- **Ignoring the bottleneck** — missing the single point of failure or the hot shard.\n"
                    "- **Going silent** — the interviewer can't grade what you don't say.\n"
                    "- **Hand-waving the deep dive** — 'we'll just cache it' without how/where/eviction.\n\n"
                    "Fix: clarify → estimate → simple working design → deepen the bottleneck → name tradeoffs, narrating throughout."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Estimate the QPS, storage, and server count for Twitter (300 M MAU, 50% daily, 2 posts + 100 reads per active user/day).",
            "Estimate storage for a photo service: 10 M uploads/day at 2 MB average, 3× replication, kept for 5 years.",
            "How many cache nodes (16 GB each) to hold the hot 20% of a 5 TB/day read workload?",
            "Size the fleet for 200k peak QPS if one app server handles ~8k QPS, including failover headroom.",
            "Walk through your framework end-to-end for 'Design a pastebin' in 10 minutes.",
        ],
        "common": [
            "What's your structured approach to an open-ended system design question?",
            "How do you estimate peak QPS from a DAU number, and what peak factor do you use?",
            "Give the rough latency of a memory reference, an SSD read, a same-DC round trip, and a cross-region round trip.",
            "When would you choose eventual consistency over strong consistency, and what's the cost?",
            "How do you decide how many shards and replicas a datastore needs?",
            "What signals separate a senior from a junior answer in a design interview?",
        ],
    },

    "Search, typeahead & autocomplete": {
        "points": [
            {
                "title": "Autocomplete vs full-text search: two different problems",
                "notes": "Typeahead = fast top-k prefix suggestions; search = rank documents by relevance to a query.",
                "explanation": (
                    "### Don't conflate them\n"
                    "- **Autocomplete / typeahead** — as the user types a *prefix*, return the top-k most likely completions in **< ~100 ms**. Optimizes for prefix lookup + popularity ranking over a relatively small phrase set.\n"
                    "- **Full-text search** — given a *complete query*, find and **rank** matching documents from a large corpus by relevance. Optimizes for an inverted index + scoring (BM25) over millions of docs.\n\n"
                    "They share ideas (indexing, ranking, sharding) but differ in data structures (trie vs inverted index), latency budget, and ranking signals. Clarify which one (often both) the interviewer wants."
                ),
                "resources": [
                    {"title": "Elasticsearch — search basics", "url": "https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html", "kind": "docs", "query": "elasticsearch search your data"},
                ],
            },
            {
                "title": "Trie (prefix tree) for autocomplete",
                "notes": "A tree keyed by characters; every prefix is a path, so lookups are O(prefix length).",
                "explanation": (
                    "### The core structure\n"
                    "A **trie** stores strings as a tree of characters. Each node represents a prefix; descending follows the typed characters, so finding all completions of a prefix is $O(p)$ to reach the node plus the cost of gathering its subtree.\n\n"
                    "```mermaid\nflowchart TD\n  root((·)) --> c[c]\n  c --> ca[ca]\n  ca --> cat[cat ✓]\n  ca --> car[car ✓]\n  car --> card[card ✓]\n```\n\n"
                    "Naively gathering the subtree on every keystroke is too slow for popular prefixes, which motivates **precomputing top-k at each node** (next point). Tries can be memory-heavy; compress with a **radix/PATRICIA trie** (merge single-child chains) or store as a ternary search tree."
                ),
                "resources": [
                    {"title": "Trie data structure", "url": "", "kind": "article", "query": "trie prefix tree autocomplete data structure"},
                ],
            },
            {
                "title": "Precomputing top-k completions per node",
                "notes": "Cache the k best completions on each trie node so a keystroke is an O(1) lookup, not a subtree scan.",
                "explanation": (
                    "### Make each keystroke cheap\n"
                    "Scanning a prefix's whole subtree per keystroke is too slow for hot prefixes ('a…'). Instead, **store the top-k completions (by score) directly on each node**. A request becomes: walk to the prefix node, return its cached list — $O(p + k)$.\n\n"
                    "- Build offline from query logs; recompute periodically (hourly/daily) as popularity shifts.\n"
                    "- Trades memory and write-time work for read latency — the right trade for a read-dominated, latency-critical feature.\n"
                    "- Serve the trie from memory (sharded by prefix). The whole structure for, say, a few million phrases fits comfortably in RAM."
                ),
                "resources": [],
            },
            {
                "title": "Ranking suggestions: frequency, recency, personalization",
                "notes": "Score = popularity + recency boost (+ user/context signals); precompute into the trie.",
                "explanation": (
                    "### What 'top' means\n"
                    "Completions are ranked by a score combining:\n\n"
                    "- **Frequency** — how often the phrase has been queried (the dominant signal).\n"
                    "- **Recency** — time-decay so trending terms surface; e.g. $\\text{score} = \\text{freq} \\times e^{-\\lambda \\, \\Delta t}$.\n"
                    "- **Personalization / context** — user history, location, language, current trends.\n\n"
                    "For an interview, start with frequency from query logs, add a recency decay, and mention personalization as an extension. Scores are computed in the offline build job and baked into each node's top-k list."
                ),
                "resources": [],
            },
            {
                "title": "Inverted index for full-text search",
                "notes": "Map each term → list (postings) of documents containing it; intersect postings to answer queries.",
                "explanation": (
                    "### The workhorse of search\n"
                    "An **inverted index** maps every term to a **postings list** of documents (and positions) containing it:\n\n"
                    "```\ndatabase -> [doc1, doc7, doc42, ...]\nsystem   -> [doc7, doc9, doc42, ...]\n```\n\n"
                    "A query like `database system` intersects the two postings lists (AND) to find docs containing both, then ranks them. Postings are stored sorted and **compressed** (delta + variable-byte encoding) for fast intersection and small size. "
                    "This is what Lucene/Elasticsearch build under the hood; positions in the postings also enable phrase queries."
                ),
                "resources": [
                    {"title": "Introduction to Information Retrieval (Manning) — inverted index", "url": "", "kind": "book", "query": "introduction to information retrieval inverted index Manning"},
                ],
            },
            {
                "title": "Text analysis: tokenization, normalization, stemming",
                "notes": "Both index and query go through the same pipeline so they match.",
                "explanation": (
                    "### Make text comparable\n"
                    "Before indexing (and at query time, identically), text is **analyzed**:\n\n"
                    "1. **Tokenization** — split into terms ('Running fast!' → ['Running', 'fast']).\n"
                    "2. **Normalization** — lowercase, strip punctuation/accents.\n"
                    "3. **Stop-word handling** — optionally drop very common words ('the', 'a').\n"
                    "4. **Stemming / lemmatization** — reduce to a root so 'running', 'ran', 'runs' all match 'run'.\n\n"
                    "**Crucial rule:** the query must pass through the *same* analyzer as the documents, or terms won't match. Different languages need different analyzers."
                ),
                "resources": [],
            },
            {
                "title": "Relevance scoring: TF-IDF and BM25",
                "notes": "Rank by term frequency × inverse document frequency; BM25 adds saturation + length normalization.",
                "explanation": (
                    "### Why some matches rank higher\n"
                    "**TF-IDF** weights a term by how often it appears in the doc (**TF**) times how *rare* it is across the corpus (**IDF**) — rare words are more discriminating:\n\n"
                    "$$\\text{idf}(t) = \\log\\frac{N}{df(t)}$$\n\n"
                    "**BM25** is the modern default. It adds **saturation** (the 10th occurrence of a word matters less than the 2nd) and **length normalization** (don't let long docs win just by size):\n\n"
                    "$$\\text{score} = \\sum_t \\text{idf}(t)\\cdot\\frac{f(t,d)\\,(k_1+1)}{f(t,d)+k_1\\,(1-b+b\\,\\frac{|d|}{\\text{avgdl}})}$$\n\n"
                    "with typical $k_1\\approx1.2$–2.0, $b\\approx0.75$. Mention you'd later add semantic/embedding ranking for meaning-based relevance."
                ),
                "resources": [
                    {"title": "BM25 explained", "url": "", "kind": "article", "query": "BM25 ranking function explained"},
                ],
            },
            {
                "title": "Sharding the index: by document vs by term",
                "notes": "Document-partitioning (scatter-gather) scales and is common; term-partitioning concentrates a term's postings.",
                "explanation": (
                    "### Two ways to split a big index\n"
                    "- **Document partitioning (local index)** — each shard holds a subset of documents and its own full inverted index. A query is **scatter-gathered** to all shards, each returns its top-k, results are merged. Scales writes well, balances load; the default (Elasticsearch works this way).\n"
                    "- **Term partitioning (global index)** — each shard owns a subset of *terms* (all postings for those terms). A query only hits the shards for its terms, but postings lists can be huge and create hotspots for popular terms.\n\n"
                    "Document partitioning is usually the answer; mention term partitioning to show you know the tradeoff (less query fan-out vs hotspots and harder updates)."
                ),
                "resources": [],
            },
            {
                "title": "The typeahead latency budget (client + server)",
                "notes": "Debounce keystrokes, cap results, serve from in-memory shards; target < 100 ms perceived.",
                "explanation": (
                    "### Spend the ~100 ms wisely\n"
                    "Typeahead must feel instant, so optimize end-to-end:\n\n"
                    "- **Client** — **debounce** (~50–150 ms after the last keystroke) so you don't fire a request per character; cancel in-flight requests; cache results for prefixes already seen this session.\n"
                    "- **Network** — keep connections warm (HTTP/2), return small payloads (just k strings).\n"
                    "- **Server** — in-memory trie sharded by prefix; precomputed top-k → O(1) lookup; no DB hit on the hot path.\n\n"
                    "Also cap suggestions (k≈5–10) and prefix length. The combination keeps p99 well under the budget."
                ),
                "resources": [],
            },
            {
                "title": "Keeping suggestions fresh (real-time updates)",
                "notes": "Batch-rebuild the trie/index periodically; layer a small real-time path for trending terms.",
                "explanation": (
                    "### Balancing freshness vs cost\n"
                    "Rebuilding the top-k trie or the full index is expensive, so most systems run a **batch pipeline** (stream query logs → aggregate counts → rebuild top-k → ship new trie) on an hourly/daily cadence. "
                    "For **trending/real-time** needs, layer a smaller online counter (e.g. count-min sketch over a recent window) and merge its hot terms into results. "
                    "For full-text search, new documents go into small **segments** that are searchable quickly and later merged into larger ones (Lucene's near-real-time model). State the freshness SLA you're targeting."
                ),
                "resources": [],
            },
            {
                "title": "Typo tolerance & fuzzy matching",
                "notes": "Allow small edit distances (≤1–2) via specialized indexes; correct or expand the query.",
                "explanation": (
                    "### Handling 'recieve' → 'receive'\n"
                    "Users misspell, so support **fuzzy matching** within a small **edit (Levenshtein) distance** (usually ≤ 2). Brute-force comparison is too slow at scale; instead use:\n\n"
                    "- **n-gram indexes** — index character trigrams so similar strings share many grams.\n"
                    "- **BK-trees** or **Levenshtein automata** — efficiently enumerate terms within distance k (what Lucene uses for fuzzy queries).\n"
                    "- **'Did you mean'** — detect a likely misspelling and suggest/auto-correct using a dictionary + query frequencies.\n\n"
                    "Cap the allowed distance (longer words tolerate more) to keep latency and false matches in check."
                ),
                "resources": [
                    {"title": "Levenshtein distance & fuzzy search", "url": "", "kind": "article", "query": "levenshtein automaton fuzzy search lucene"},
                ],
            },
            {
                "title": "Caching and the long tail",
                "notes": "Cache hot prefixes/queries at the edge; the long tail still hits the index.",
                "explanation": (
                    "### Most traffic, few queries\n"
                    "Query popularity is heavily skewed — a small set of prefixes/queries drives most traffic. Cache those aggressively:\n\n"
                    "- **Edge/CDN or app-tier cache** for the hottest prefixes and full queries (short TTL to stay fresh).\n"
                    "- The **long tail** (rare queries) falls through to the trie/inverted index — that's fine, it's a small fraction of volume.\n\n"
                    "Cache results *after* ranking so you serve the final list. This is the same 80/20 reasoning as general caching: a modest cache absorbs the bulk of reads and protects the index from spikes."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Design the autocomplete/typeahead for a search bar serving 100k QPS with < 100 ms latency.",
            "Design a full-text search service over 1 B documents (index structure, ranking, sharding).",
            "How would you precompute and serve the top-5 completions for every prefix?",
            "Add typo tolerance so 'databse' still suggests 'database' — what index and distance?",
            "How do you keep trending queries surfacing within minutes without rebuilding the whole index?",
        ],
        "common": [
            "What data structure powers autocomplete, and how do you make each keystroke O(1)?",
            "How does an inverted index work, and how is a multi-term query evaluated?",
            "Explain TF-IDF vs BM25 and what BM25 adds.",
            "Document partitioning vs term partitioning for a distributed index — tradeoffs?",
            "How do you rank autocomplete suggestions (frequency, recency, personalization)?",
            "How do you support fuzzy/typo-tolerant matching efficiently at scale?",
        ],
    },

    # ------------------------------------------------------------- AI Infra ---
    "NCCL collectives & communication patterns": {
        "points": [
            {
                "title": "What NCCL is and why collective communication dominates at scale",
                "notes": "NCCL is NVIDIA's library for fast multi-GPU/multi-node collectives; comm is often the scaling bottleneck.",
                "explanation": (
                    "### The library behind every distributed run\n"
                    "**NCCL** (NVIDIA Collective Communications Library) implements the group communication primitives that parallel training/inference depend on, tuned for GPU interconnects (NVLink, PCIe, InfiniBand). "
                    "A **collective** is an operation involving *all* GPUs in a group — e.g. summing every GPU's gradients. As you add GPUs, computation per GPU stays roughly fixed but communication grows, so **collectives become the scaling bottleneck**. "
                    "Understanding which collective each parallelism strategy uses — and how fast the interconnect runs it — is the key to predicting and improving throughput. Frameworks (PyTorch DDP/FSDP, Megatron) call NCCL under the hood."
                ),
                "resources": [
                    {"title": "NVIDIA NCCL user guide", "url": "https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html", "kind": "docs", "query": "NVIDIA NCCL user guide collectives"},
                ],
            },
            {
                "title": "All-Reduce — the workhorse of data-parallel training",
                "notes": "Every GPU ends with the summed (then averaged) gradient: reduce + broadcast in one op.",
                "explanation": (
                    "### The operation you'll see most\n"
                    "In data-parallel training each GPU computes gradients on its own minibatch; they must be **averaged across all GPUs** before the optimizer step. **All-Reduce** does exactly that: it sums each GPU's tensor element-wise and leaves the result on *every* GPU.\n\n"
                    "$$g_{\\text{final}} = \\frac{1}{N}\\sum_{i=1}^{N} g_i \\quad\\text{on every GPU}$$\n\n"
                    "It's logically a **Reduce** (combine) followed by a **Broadcast** (distribute), but NCCL fuses them into one bandwidth-efficient pass. Because it runs every step on the full gradient, its speed largely determines data-parallel scaling efficiency."
                ),
                "resources": [
                    {"title": "Ring All-Reduce explained (Uber Horovod)", "url": "", "kind": "article", "query": "ring allreduce horovod bringing distributed training"},
                ],
            },
            {
                "title": "Ring All-Reduce and bandwidth optimality",
                "notes": "Arranged in a ring, each GPU sends 2(N−1)/N × data — independent of N, so it scales.",
                "explanation": (
                    "### Why the ring algorithm scales\n"
                    "A naive all-reduce (everyone sends to one root) makes the root a bottleneck. **Ring All-Reduce** arranges GPUs in a logical ring and runs two phases — **reduce-scatter** then **all-gather** — each in N−1 steps where a GPU only talks to its neighbour.\n\n"
                    "Total data each GPU sends is $\\approx 2\\frac{N-1}{N}\\times$ the tensor size — which **approaches a constant (2×) as N grows**, so per-GPU bandwidth cost is independent of the number of GPUs. That bandwidth-optimality is why ring (and tree/hierarchical variants for multi-node) is the default. NCCL auto-selects ring vs tree based on size and topology."
                ),
                "resources": [],
            },
            {
                "title": "The collective zoo: Broadcast, Reduce, All-Gather, Reduce-Scatter, All-to-All",
                "notes": "Each primitive moves data a different way; know which op each parallelism needs.",
                "explanation": (
                    "### The primitives\n"
                    "- **Broadcast** — one GPU's data copied to all (e.g. distribute initial weights).\n"
                    "- **Reduce** — combine all GPUs' data to one GPU.\n"
                    "- **All-Reduce** — reduce, result on all GPUs.\n"
                    "- **All-Gather** — each GPU contributes a shard; everyone ends with the full concatenation (FSDP gathers sharded weights before a layer).\n"
                    "- **Reduce-Scatter** — reduce, but each GPU keeps only its shard of the result (FSDP scatters gradients).\n"
                    "- **All-to-All** — every GPU sends a distinct chunk to every other GPU (MoE token routing to experts).\n\n"
                    "All-Reduce = Reduce-Scatter + All-Gather, which is why those two appear together in sharded training."
                ),
                "resources": [],
            },
            {
                "title": "Mapping collectives to parallelism strategies",
                "notes": "DP→all-reduce, FSDP→all-gather+reduce-scatter, TP→all-reduce, MoE→all-to-all, PP→point-to-point.",
                "explanation": (
                    "### Which strategy triggers which op\n"
                    "| Parallelism | Communication |\n|---|---|\n"
                    "| **Data parallel (DDP)** | All-Reduce of gradients each step |\n"
                    "| **FSDP / ZeRO-3** | All-Gather weights (fwd/bwd) + Reduce-Scatter gradients |\n"
                    "| **Tensor parallel (TP)** | All-Reduce of partial activations within each layer |\n"
                    "| **Pipeline parallel (PP)** | Point-to-point send/recv of activations between stages |\n"
                    "| **Expert parallel (MoE)** | All-to-All to route tokens to expert GPUs |\n\n"
                    "TP is the most communication-intensive (all-reduce *inside* every layer), which is why it's kept within a high-bandwidth NVLink node, while DP can span nodes over slower InfiniBand."
                ),
                "resources": [],
            },
            {
                "title": "Interconnects & transports: NVLink, NVSwitch, PCIe, InfiniBand, GPUDirect RDMA",
                "notes": "Intra-node NVLink (~100s GB/s) ≫ PCIe; inter-node InfiniBand/RoCE; RDMA skips the CPU.",
                "explanation": (
                    "### The physical layer sets the ceiling\n"
                    "- **NVLink / NVSwitch** — high-bandwidth GPU-to-GPU links *within* a node (hundreds of GB/s, e.g. ~900 GB/s on H100 NVSwitch). Far faster than PCIe.\n"
                    "- **PCIe** — host/GPU bus, ~32–64 GB/s; a fallback when no NVLink.\n"
                    "- **InfiniBand / RoCE** — the *inter-node* fabric (e.g. 400 Gb/s NDR), used to scale beyond one box.\n"
                    "- **GPUDirect RDMA** — lets the NIC read/write GPU memory directly, bypassing the CPU and extra copies.\n\n"
                    "NCCL discovers this topology and routes collectives accordingly. Placement matters: keep the chattiest parallelism (TP) on NVLink, span the cheaper one (DP/PP) across the slower inter-node fabric."
                ),
                "resources": [
                    {"title": "NVLink / NVSwitch overview", "url": "", "kind": "article", "query": "NVLink NVSwitch bandwidth H100 explained"},
                ],
            },
            {
                "title": "Bus bandwidth, message size, and latency",
                "notes": "Small messages are latency-bound; fuse into large buffers to hit peak 'busbw'.",
                "explanation": (
                    "### Big messages win\n"
                    "Every collective pays a fixed **latency** plus a per-byte **bandwidth** cost. Tiny messages are dominated by latency and kernel-launch overhead, so effective bandwidth is poor; large messages amortize the fixed cost and approach peak. "
                    "NCCL reports **bus bandwidth (busbw)** — a topology-normalized number you can compare against the hardware peak with `nccl-tests`. The practical lever: **fuse many small tensors into few large buffers** before communicating (see gradient bucketing). The roofline intuition applies to comm too — you want to be bandwidth-bound, not latency-bound."
                ),
                "resources": [
                    {"title": "nccl-tests (benchmarking)", "url": "https://github.com/NVIDIA/nccl-tests", "kind": "docs", "query": "nccl-tests github bus bandwidth"},
                ],
            },
            {
                "title": "Overlapping communication with computation",
                "notes": "Run collectives on a separate CUDA stream during backprop so comm hides under compute.",
                "explanation": (
                    "### Hide the comm under the math\n"
                    "If a GPU computes, then stops to communicate, then computes, the comm time is pure overhead. The fix is **overlap**: launch collectives on a separate CUDA stream so they run *concurrently* with computation. "
                    "In backprop, gradients for early layers become available while later layers are still computing — DDP kicks off the all-reduce for a gradient bucket the moment it's ready, overlapping it with the rest of the backward pass. "
                    "Effective overlap can hide most communication, which is what keeps data-parallel scaling efficiency high. It requires enough compute per step to hide behind; tiny models/batches can't overlap and become comm-bound."
                ),
                "resources": [],
            },
            {
                "title": "Gradient bucketing and fusion",
                "notes": "Group many small gradient tensors into fixed-size buckets so each all-reduce is large and overlappable.",
                "explanation": (
                    "### Why DDP buckets gradients\n"
                    "A model has hundreds of parameter tensors; all-reducing each separately means hundreds of tiny, latency-bound collectives. **Bucketing** groups gradients into fixed-size buffers (e.g. 25 MB) and all-reduces a full bucket at once. "
                    "Benefits: (1) each collective is large → near-peak bandwidth; (2) a bucket fires as soon as its gradients are ready during backprop → maximal overlap with computation. "
                    "Bucket size is a tunable tradeoff — too small loses bandwidth and overlap; too large delays the first launch. This is a standard knob in DDP/FSDP performance tuning."
                ),
                "resources": [],
            },
            {
                "title": "Debugging hangs, mismatches, and stragglers",
                "notes": "Collectives are barriers — one slow/misordered rank stalls all; use NCCL_DEBUG and watch for stragglers.",
                "explanation": (
                    "### When the whole job freezes\n"
                    "Because every rank must participate, collectives act as **barriers** — the cluster runs at the speed of its slowest GPU. Common failure modes:\n\n"
                    "- **Mismatched collectives** — ranks call ops in different order / with different sizes → deadlock or corruption.\n"
                    "- **A dead or hung rank** → everyone waits forever (watch for NCCL timeout errors).\n"
                    "- **Stragglers** — one slow GPU (thermal throttling, bad NIC, noisy neighbour) drags down every step.\n\n"
                    "Tools: set `NCCL_DEBUG=INFO` to see topology/algorithm choices, `nccl-tests` to validate raw bandwidth, and per-rank step-time monitoring to catch stragglers. Many large-run incidents are network/straggler issues, not model bugs."
                ),
                "resources": [
                    {"title": "NCCL troubleshooting & env vars", "url": "https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting.html", "kind": "docs", "query": "NCCL_DEBUG troubleshooting environment variables"},
                ],
            },
            {
                "title": "Communication as the scaling bottleneck (compute vs comm)",
                "notes": "Scaling efficiency = compute / (compute + exposed comm); grow batch or overlap to stay compute-bound.",
                "explanation": (
                    "### The number that decides whether more GPUs help\n"
                    "Adding GPUs only helps if communication doesn't eat the gains. **Scaling efficiency** ≈ useful compute ÷ (compute + *exposed* communication). Levers to keep it high:\n\n"
                    "- **Overlap** comm with compute (separate streams, bucketing).\n"
                    "- **Larger per-GPU work** (bigger batch / more compute) so there's more to hide comm behind.\n"
                    "- **Right topology** — chatty parallelism on NVLink, cheap parallelism across nodes.\n"
                    "- **Fewer/larger messages** to hit peak bandwidth.\n\n"
                    "When efficiency drops at scale, the cause is almost always exposed communication — diagnose with a profiler timeline showing comm vs compute gaps."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Your data-parallel training scales to 8 GPUs at 95% efficiency but only 60% at 64 GPUs — diagnose and fix.",
            "Which NCCL collective(s) does FSDP use in the forward and backward pass, and why?",
            "Estimate per-GPU bytes moved by ring all-reduce of a 1 GB gradient across 32 GPUs.",
            "A 256-GPU job hangs intermittently with no error — how do you debug it?",
            "Why is tensor parallelism usually confined to a single NVLink node while data parallelism spans nodes?",
        ],
        "common": [
            "What is All-Reduce and why is it central to data-parallel training?",
            "Explain ring all-reduce and why its per-GPU bandwidth cost is independent of GPU count.",
            "Map each parallelism strategy (DP, FSDP, TP, PP, MoE) to the collective(s) it uses.",
            "How do you overlap communication with computation, and why does bucketing help?",
            "Compare NVLink, PCIe, and InfiniBand — where does each sit in a cluster?",
            "How would you debug a NCCL hang or a straggler in a large training run?",
        ],
    },

    "Roofline model, arithmetic intensity & profiling": {
        "points": [
            {
                "title": "The roofline model: compute roof vs memory-bandwidth roof",
                "notes": "Attainable FLOP/s = min(peak compute, arithmetic_intensity × memory bandwidth).",
                "explanation": (
                    "### One picture for 'what's limiting me'\n"
                    "The roofline plots attainable performance against **arithmetic intensity** (x-axis, FLOPs per byte) on log-log axes. Two ceilings bound you:\n\n"
                    "$$\\text{attainable FLOP/s} = \\min\\big(\\underbrace{\\text{peak compute}}_{\\text{flat roof}},\\ \\underbrace{\\text{AI} \\times \\text{peak memory BW}}_{\\text{slanted roof}}\\big)$$\n\n"
                    "At low intensity you're on the **slanted (memory) roof** — limited by how fast you can move bytes. Past the **ridge point** you hit the **flat (compute) roof** — limited by raw FLOP/s. "
                    "The model tells you, for a given kernel, whether to optimize memory traffic or arithmetic — and the ceiling you could reach if you did."
                ),
                "resources": [
                    {"title": "Roofline model (Berkeley) — overview", "url": "", "kind": "article", "query": "roofline model arithmetic intensity Williams Berkeley"},
                ],
            },
            {
                "title": "Arithmetic intensity (FLOPs per byte)",
                "notes": "AI = total FLOPs ÷ bytes moved to/from DRAM; it places a kernel on the roofline.",
                "explanation": (
                    "### The single most useful ratio\n"
                    "**Arithmetic intensity** is the work done per byte of memory traffic:\n\n"
                    "$$\\text{AI} = \\frac{\\text{FLOPs}}{\\text{bytes moved to/from DRAM}}$$\n\n"
                    "High AI (reuses data many times in registers/cache) → compute-bound, good GPU utilization. Low AI (touches each byte once) → memory-bound. "
                    "Examples: a large dense **GEMM** has high AI (each loaded element feeds many FMAs) → compute-bound; **elementwise ops** (add, activation, layernorm) have AI ≈ a fraction → deeply memory-bound. "
                    "Computing AI for your hot kernel immediately tells you which roof you're under and whether Tensor Cores can even help."
                ),
                "resources": [],
            },
            {
                "title": "Compute-bound vs memory-bound and the ridge point",
                "notes": "The ridge point AI* = peak FLOP/s ÷ peak BW; below it you're memory-bound, above it compute-bound.",
                "explanation": (
                    "### Where the two roofs meet\n"
                    "The **ridge point** is the arithmetic intensity at which the memory roof meets the compute roof:\n\n"
                    "$$\\text{AI}^* = \\frac{\\text{peak FLOP/s}}{\\text{peak memory BW}}$$\n\n"
                    "For modern GPUs this is high — e.g. an H100 has ~1000 TFLOP/s (BF16) and ~3.35 TB/s HBM, giving AI* ≈ 300 FLOP/byte. **You need ~300 FLOPs per byte just to be compute-bound.** "
                    "That's a high bar, which is why so many real workloads (anything elementwise, small-batch decode) sit firmly on the memory roof. Knowing AI* for your hardware tells you the intensity you must reach to use the compute you paid for."
                ),
                "resources": [],
            },
            {
                "title": "Why LLM inference decode is memory-bound",
                "notes": "Autoregressive decode does tiny GEMVs per token, reloading all weights → bandwidth-limited.",
                "explanation": (
                    "### The defining fact of inference perf\n"
                    "During autoregressive **decode**, each step processes a single new token: the matrix multiplies become **GEMV** (matrix × vector), so each weight is loaded from HBM and used for only *one* multiply — arithmetic intensity ≈ 1. The step time is dominated by **reading the weights**, not computing:\n\n"
                    "$$t_{\\text{decode}} \\approx \\frac{\\text{model bytes}}{\\text{memory bandwidth}}$$\n\n"
                    "This is why decode is **memory-bound** and why **batching** (reuse the loaded weights across many sequences) and **quantization** (fewer bytes per weight) are the big inference wins — both raise effective arithmetic intensity. Prefill, by contrast, processes many tokens at once (GEMM) and is compute-bound."
                ),
                "resources": [],
            },
            {
                "title": "Estimating AI for common kernels (GEMM, attention, elementwise)",
                "notes": "GEMM ∝ N (high AI); attention is memory-bound without fusion; elementwise/norm are memory-bound.",
                "explanation": (
                    "### Back-of-envelope per kernel\n"
                    "- **Dense GEMM** ($M\\times K \\cdot K\\times N$): $2MKN$ FLOPs vs $\\sim(MK+KN+MN)$ elements moved → AI grows with matrix size → **compute-bound** when large; Tensor Cores apply.\n"
                    "- **Attention**: the $QK^\\top$ and $\\cdot V$ are GEMMs, but a naive implementation materializes the $N\\times N$ scores to HBM → memory-bound. **FlashAttention** fuses it to keep scores in SRAM, raising AI and making it compute-bound.\n"
                    "- **Elementwise / LayerNorm / softmax / activations**: a few FLOPs per element, AI ≈ O(1) → **memory-bound**; the win is **kernel fusion** to avoid round-trips to HBM.\n\n"
                    "This is why fusing elementwise ops and using FlashAttention are such common, high-leverage optimizations."
                ),
                "resources": [],
            },
            {
                "title": "Profiling tools: Nsight Systems vs Nsight Compute",
                "notes": "Nsight Systems = whole-timeline view; Nsight Compute = single-kernel deep dive.",
                "explanation": (
                    "### Two complementary lenses\n"
                    "- **Nsight Systems (nsys)** — a **timeline** profiler: shows CPU/GPU activity, kernel durations, memcpys, gaps, and stream overlap across the whole run. Use it first to find *where* time goes — idle GPU? bad overlap? a dominant kernel? launch-overhead gaps?\n"
                    "- **Nsight Compute (ncu)** — a **per-kernel** profiler: for one kernel it reports achieved FLOP/s, memory throughput, occupancy, warp stalls, and **places it on a roofline**. Use it to understand *why* a specific hot kernel is slow.\n\n"
                    "Workflow: nsys to pick the offender → ncu to diagnose it → optimize → repeat. For PyTorch, `torch.profiler` gives a similar timeline + the Chrome trace viewer / TensorBoard plugin."
                ),
                "resources": [
                    {"title": "NVIDIA Nsight Systems", "url": "https://developer.nvidia.com/nsight-systems", "kind": "docs", "query": "NVIDIA Nsight Systems profiler"},
                    {"title": "PyTorch Profiler recipe", "url": "", "kind": "docs", "query": "pytorch torch.profiler tutorial trace"},
                ],
            },
            {
                "title": "Reading a profile: kernel time, memory throughput, occupancy, stalls",
                "notes": "Find the dominant kernels, then check if they hit memory-BW or compute peak, and why not.",
                "explanation": (
                    "### What to look at\n"
                    "1. **Top kernels by total time** — optimize the few that dominate (Amdahl).\n"
                    "2. **Achieved vs peak** — is the kernel near peak memory bandwidth (memory-bound, expected for elementwise) or near peak FLOP/s (compute-bound)? The gap is your headroom.\n"
                    "3. **Occupancy** — are enough warps resident to hide latency? Low occupancy from register/shared-memory pressure leaves the GPU stalling.\n"
                    "4. **Warp stall reasons** — memory dependency, sync, instruction fetch — point at the specific fix.\n"
                    "5. **Gaps / low GPU utilization** on the timeline — CPU-bound dataloader, kernel-launch overhead, or missing overlap.\n\n"
                    "The roofline view in ncu ties it together: a dot far below both roofs means there's real headroom to chase."
                ),
                "resources": [],
            },
            {
                "title": "A roofline-driven optimization workflow",
                "notes": "Memory-bound → fuse / cut traffic / raise reuse; compute-bound → Tensor Cores, better GEMM, lower precision.",
                "explanation": (
                    "### Let the roof tell you what to do\n"
                    "**If memory-bound** (most elementwise/decode work):\n"
                    "- **Fuse kernels** to avoid HBM round-trips (e.g. fused LayerNorm, FlashAttention).\n"
                    "- **Reduce bytes** — lower precision (FP16/FP8), in-place ops, smaller dtypes.\n"
                    "- **Increase reuse** — batch to amortize weight loads; tile to keep data in SRAM.\n\n"
                    "**If compute-bound** (large GEMMs):\n"
                    "- Use **Tensor Cores** (right dtype/shapes), pick good GEMM tiling (cuBLAS/CUTLASS), align dimensions.\n"
                    "- Consider lower-precision math if accuracy allows.\n\n"
                    "Always raising **arithmetic intensity** (more work per byte) moves you up the slanted roof toward the compute ceiling."
                ),
                "resources": [],
            },
            {
                "title": "MFU / HFU: model FLOPs utilization as a north-star metric",
                "notes": "MFU = achieved model FLOP/s ÷ hardware peak; a single number for how well you use the GPU.",
                "explanation": (
                    "### The headline efficiency number\n"
                    "**Model FLOPs Utilization (MFU)** is the fraction of peak compute your training/inference actually achieves:\n\n"
                    "$$\\text{MFU} = \\frac{\\text{model FLOPs/s actually done}}{\\text{hardware peak FLOP/s}}$$\n\n"
                    "Compute model FLOPs from the architecture (e.g. $\\approx 6 \\cdot N_{\\text{params}} \\cdot \\text{tokens}$ for a transformer training step) and divide by measured time × peak. "
                    "Good large-scale training runs reach ~**40–55% MFU**; much lower means time is lost to memory traffic, communication, or pipeline bubbles. **HFU** (hardware FLOPs utilization) counts redundant recompute (activation checkpointing) too. MFU is the one number to track when scaling — it captures compute, memory, *and* comm inefficiencies at once."
                ),
                "resources": [
                    {"title": "PaLM / MFU definition", "url": "", "kind": "article", "query": "model FLOPs utilization MFU definition transformer"},
                ],
            },
            {
                "title": "Common pitfalls: small batches, launch overhead, false peaks",
                "notes": "Tiny batches → memory-bound & low occupancy; many small kernels → launch-overhead-bound.",
                "explanation": (
                    "### Traps that waste the GPU\n"
                    "- **Too-small batch** — low arithmetic intensity and low occupancy; you sit on the memory roof and underuse compute. Increasing batch is often the single biggest win.\n"
                    "- **Kernel-launch overhead** — thousands of tiny kernels mean the GPU spends time launching, not computing; timeline shows gaps. Fix with fusion or **CUDA graphs**.\n"
                    "- **CPU-bound dataloader** — GPU idles waiting for input; the timeline shows GPU gaps aligned with host work.\n"
                    "- **Chasing peak FLOP/s on a memory-bound kernel** — pointless; the roofline tells you the real ceiling is the memory roof.\n\n"
                    "Always measure before optimizing: the profile usually contradicts your first guess about where the time goes."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Your training run shows 18% MFU on H100s — list the likely causes in priority order and how you'd confirm each.",
            "Compute the arithmetic intensity of a LayerNorm over a [8192, 4096] tensor and say which roof it's on.",
            "Estimate decode tokens/sec for a 13B FP16 model on a GPU with 2 TB/s memory bandwidth (single sequence).",
            "Given an Nsight Compute report showing 80% memory throughput and 12% SM utilization, what do you optimize?",
            "Where is the ridge point for an accelerator with 500 TFLOP/s and 2 TB/s bandwidth, and what does it imply?",
        ],
        "common": [
            "Explain the roofline model and how it tells you whether to optimize compute or memory.",
            "What is arithmetic intensity, and why is LLM decode memory-bound while prefill is compute-bound?",
            "When do you reach for Nsight Systems vs Nsight Compute?",
            "What is MFU, what's a good value at scale, and what drags it down?",
            "How does kernel fusion (or FlashAttention) change a kernel's position on the roofline?",
            "Name three reasons a GPU shows low utilization in a profile and the fix for each.",
        ],
    },

    # --------------------------------------------------------------- AI/ML ---
    "Probability/stats fundamentals (Bayes, MLE, distributions)": {
        "points": [
            {
                "title": "Random variables and the distributions you actually use",
                "notes": "Bernoulli/Binomial, Categorical, Gaussian, Poisson, Exponential — know shape, params, and where each shows up.",
                "explanation": (
                    "### The working set\n"
                    "- **Bernoulli / Binomial** — a single 0/1 outcome / count of successes; binary classification labels.\n"
                    "- **Categorical / Multinomial** — one of K classes; the target of a softmax.\n"
                    "- **Gaussian (Normal)** $\\mathcal{N}(\\mu,\\sigma^2)$ — ubiquitous: noise, weight init, the CLT limit.\n"
                    "- **Poisson** — count of rare events per interval (arrivals, clicks).\n"
                    "- **Exponential** — time between Poisson events (latency tails).\n\n"
                    "For each, know its **support, parameters, mean, and variance**. ML connection: a model's output layer encodes a distribution (softmax → Categorical, regression → Gaussian), and the loss is its negative log-likelihood."
                ),
                "resources": [
                    {"title": "Common probability distributions", "url": "", "kind": "article", "query": "common probability distributions machine learning cheat sheet"},
                ],
            },
            {
                "title": "Expectation, variance, covariance",
                "notes": "Mean, spread, and linear co-movement — the moments behind bias/variance and PCA.",
                "explanation": (
                    "### Summarizing randomness\n"
                    "$$\\mathbb{E}[X]=\\sum_x x\\,p(x),\\quad \\operatorname{Var}(X)=\\mathbb{E}[(X-\\mathbb{E}X)^2]=\\mathbb{E}[X^2]-(\\mathbb{E}X)^2$$\n\n"
                    "**Covariance** $\\operatorname{Cov}(X,Y)=\\mathbb{E}[(X-\\mathbb{E}X)(Y-\\mathbb{E}Y)]$ measures linear co-movement; normalized to $[-1,1]$ it's **correlation**. "
                    "Key facts: expectation is **linear** ($\\mathbb{E}[aX+bY]=a\\mathbb{E}X+b\\mathbb{E}Y$ always); variance adds for **independent** variables ($\\operatorname{Var}(X+Y)=\\operatorname{Var}X+\\operatorname{Var}Y$). "
                    "These power the **bias–variance decomposition**, the covariance matrix in **PCA**, and uncertainty propagation."
                ),
                "resources": [],
            },
            {
                "title": "Conditional probability and Bayes' theorem",
                "notes": "Update beliefs from evidence: posterior ∝ likelihood × prior.",
                "explanation": (
                    "### The rule that updates beliefs\n"
                    "$$P(A\\mid B)=\\frac{P(B\\mid A)\\,P(A)}{P(B)}$$\n\n"
                    "Read it as **posterior ∝ likelihood × prior**: start with a prior belief $P(A)$, see evidence $B$, update. "
                    "It underlies Naive Bayes, Bayesian inference, and reasoning about test accuracy. The classic trap is the **base rate**: even a 99%-accurate test for a rare (0.1%) disease yields mostly false positives, because the prior $P(\\text{disease})$ is tiny. Always factor in the base rate when interpreting a 'positive'."
                ),
                "resources": [
                    {"title": "Bayes' theorem (3Blue1Brown)", "url": "", "kind": "video", "query": "3blue1brown bayes theorem"},
                ],
            },
            {
                "title": "Frequentist vs Bayesian thinking",
                "notes": "Parameters as fixed-unknown (estimate via data) vs random (have distributions/priors).",
                "explanation": (
                    "### Two views of 'the parameter'\n"
                    "- **Frequentist** — parameters are fixed but unknown; probability is long-run frequency. You estimate a point value (MLE) and quantify uncertainty via confidence intervals over hypothetical repeated samples.\n"
                    "- **Bayesian** — parameters are random variables with a **prior**; data updates them into a **posterior** distribution, giving direct probability statements ('95% credible interval').\n\n"
                    "In practice deep learning is mostly frequentist (point estimates via MLE/SGD), but Bayesian ideas appear as **regularization** (a prior), in **uncertainty estimation**, and in small-data regimes where priors help. Knowing both framings helps you reason about regularization and uncertainty correctly."
                ),
                "resources": [],
            },
            {
                "title": "Maximum likelihood estimation (MLE)",
                "notes": "Pick parameters that maximize the data's likelihood; minimizing cross-entropy IS MLE.",
                "explanation": (
                    "### Why our loss functions look the way they do\n"
                    "MLE chooses parameters that make the observed data most probable. We maximize the **log**-likelihood (sums are nicer than products, numerically stable):\n\n"
                    "$$\\hat\\theta=\\arg\\max_\\theta \\sum_i \\log p(x_i\\mid\\theta)$$\n\n"
                    "Minimizing the **negative** log-likelihood is the standard training objective. This is *why* classification uses **cross-entropy** (NLL of a Categorical) and regression uses **MSE** (NLL of a Gaussian with fixed variance). When you call a loss, you're almost always doing MLE under some assumed output distribution."
                ),
                "resources": [],
            },
            {
                "title": "MAP estimation and priors as regularization",
                "notes": "MAP = MLE + log-prior; an L2 prior is weight decay, an L1 prior is Lasso.",
                "explanation": (
                    "### Where regularization comes from\n"
                    "**Maximum a posteriori** adds a prior to MLE:\n\n"
                    "$$\\hat\\theta=\\arg\\max_\\theta \\Big[\\sum_i \\log p(x_i\\mid\\theta) + \\log p(\\theta)\\Big]$$\n\n"
                    "Choosing a **Gaussian prior** on the weights yields an $L_2$ penalty — i.e. **weight decay / ridge**; a **Laplace prior** yields $L_1$ — i.e. **Lasso** (sparsity). "
                    "So regularization isn't an ad-hoc trick: it's a prior belief that weights should be small/sparse. As data grows, the likelihood dominates the prior and MAP → MLE."
                ),
                "resources": [],
            },
            {
                "title": "Cross-entropy and KL divergence",
                "notes": "KL measures distance between distributions; cross-entropy = entropy + KL, and is our classification loss.",
                "explanation": (
                    "### The information-theory behind the loss\n"
                    "**KL divergence** measures how far a predicted distribution $q$ is from the true $p$:\n\n"
                    "$$D_{KL}(p\\,\\|\\,q)=\\sum_x p(x)\\log\\frac{p(x)}{q(x)}\\ge 0$$\n\n"
                    "It's **not symmetric** ($D_{KL}(p\\|q)\\ne D_{KL}(q\\|p)$). **Cross-entropy** $H(p,q)=H(p)+D_{KL}(p\\|q)$; since the true label's entropy $H(p)$ is fixed, minimizing cross-entropy = minimizing KL to the labels. "
                    "KL also appears as a **regularizer/constraint** in VAEs and in RLHF/PPO (keep the policy close to the reference model). Knowing the asymmetry matters: mode-covering vs mode-seeking behavior."
                ),
                "resources": [],
            },
            {
                "title": "CLT, law of large numbers, and why Gaussians are everywhere",
                "notes": "Averages concentrate (LLN) and become Gaussian (CLT) — the basis of error bars and sampling.",
                "explanation": (
                    "### Why sample means behave\n"
                    "- **Law of Large Numbers** — the sample mean converges to the true mean as $n\\to\\infty$. It's why more eval examples / more Monte-Carlo samples give a more reliable estimate.\n"
                    "- **Central Limit Theorem** — the sum/mean of many independent variables is approximately **Gaussian**, regardless of their original distribution, with standard error $\\sigma/\\sqrt{n}$.\n\n"
                    "Consequences you use constantly: error bars shrink like $1/\\sqrt{n}$ (to halve them, 4× the data); A/B test and eval confidence intervals assume CLT; and many noise terms are modeled Gaussian because they're sums of many small effects."
                ),
                "resources": [],
            },
            {
                "title": "Sampling and Monte Carlo estimation",
                "notes": "Estimate expectations by averaging samples; the backbone of eval, RL returns, and generation.",
                "explanation": (
                    "### Estimating what you can't compute exactly\n"
                    "Many quantities are expectations $\\mathbb{E}_{x\\sim p}[f(x)]$ that are intractable to compute exactly. **Monte Carlo** approximates them by drawing samples and averaging:\n\n"
                    "$$\\mathbb{E}_{x\\sim p}[f(x)]\\approx \\frac1n\\sum_{i=1}^n f(x_i),\\quad x_i\\sim p$$\n\n"
                    "Error shrinks like $1/\\sqrt{n}$ (from the CLT). This underlies **evaluation** (averaging metric over a test set), **RL** (estimating returns), **dropout/ensemble uncertainty**, and **LLM sampling** itself. Variance-reduction tricks (importance sampling, control variates) buy accuracy with fewer samples."
                ),
                "resources": [],
            },
            {
                "title": "Hypothesis testing, confidence intervals, and p-values",
                "notes": "Decide if an observed difference is real vs noise — essential for A/B tests and eval deltas.",
                "explanation": (
                    "### Is the improvement real?\n"
                    "When model B scores higher than A, ask whether the gap exceeds noise. A **confidence interval** gives a plausible range for the true value; a **p-value** is the probability of seeing a difference this large *if there were truly none* (the null hypothesis). Small p (< 0.05) → unlikely to be chance.\n\n"
                    "Practical points: report **CIs**, not just point scores; account for **multiple comparisons** (testing many variants inflates false positives); ensure adequate **sample size / power**; and beware **p-hacking** (peeking, stopping early). For eval deltas on small benchmarks, the CI is often wide enough that a 1-point gain isn't significant — a crucial sanity check."
                ),
                "resources": [
                    {"title": "Statistical significance & A/B testing", "url": "", "kind": "article", "query": "p-value confidence interval ab testing explained"},
                ],
            },
        ],
        "example": [
            "A disease affects 0.5% of people; a test is 98% sensitive and 95% specific. Given a positive result, what's P(disease)?",
            "Derive why minimizing cross-entropy for classification is equivalent to MLE of a Categorical model.",
            "Show that an L2 weight penalty corresponds to a Gaussian prior under MAP estimation.",
            "Model B beats model A by 1.2% on a 500-example benchmark — is it significant? How would you check?",
            "You need E[f(x)] under an intractable distribution — set up a Monte Carlo estimator and its error.",
        ],
        "common": [
            "State Bayes' theorem and explain the base-rate fallacy with an example.",
            "What is MLE, and how does it connect to cross-entropy and MSE losses?",
            "Define KL divergence — is it symmetric, and where does it appear in ML?",
            "Explain the bias–variance tradeoff in terms of expectation and variance.",
            "What do the LLN and CLT tell you, and why does error scale as 1/√n?",
            "How do you tell whether an eval improvement is statistically significant?",
        ],
    },

    "Prompt engineering & in-context learning": {
        "points": [
            {
                "title": "In-context learning: the model learns from the prompt, not the weights",
                "notes": "LLMs adapt to a task from examples/instructions in the context — no gradient updates.",
                "explanation": (
                    "### The capability everything builds on\n"
                    "**In-context learning (ICL)** is the emergent ability of large models to perform a task purely from instructions and examples placed in the prompt — the weights don't change. Show a few input→output pairs and the model infers the pattern for the next input. "
                    "This is what makes prompting powerful: you adapt behavior at inference time, instantly, with no training. It emerges with scale (small models do it poorly). "
                    "Mental model: the context acts like a temporary task specification the model conditions on. The flip side — everything depends on the context, so prompt quality and ordering matter a lot, and the context window is a finite budget."
                ),
                "resources": [
                    {"title": "GPT-3 'Language Models are Few-Shot Learners'", "url": "", "kind": "article", "query": "language models are few-shot learners GPT-3 paper"},
                ],
            },
            {
                "title": "Zero-shot vs few-shot prompting",
                "notes": "Zero-shot = instruction only; few-shot = include worked examples (demonstrations).",
                "explanation": (
                    "### When to add examples\n"
                    "- **Zero-shot** — just describe the task ('Classify the sentiment as positive/negative'). Works well for tasks the instruction-tuned model already understands; cheapest in tokens.\n"
                    "- **Few-shot** — prepend a handful of input→output **demonstrations** before the real input. Helps when the task is unusual, the **output format** is specific, or zero-shot is unreliable.\n\n"
                    "Practical tips: 2–5 diverse, correct, representative examples usually suffice; example **order** and **label balance** affect results; keep formatting identical to what you want back. If few-shot still fails or examples are many/long, that's a signal to fine-tune or use retrieval instead."
                ),
                "resources": [],
            },
            {
                "title": "Anatomy of a good prompt",
                "notes": "Role/instruction + context + (examples) + explicit output format + the input, clearly delimited.",
                "explanation": (
                    "### Structure beats cleverness\n"
                    "A reliable prompt usually has:\n\n"
                    "1. **Instruction** — what to do, specific and unambiguous; state constraints.\n"
                    "2. **Context** — background, retrieved documents, definitions.\n"
                    "3. **Examples** (optional) — demonstrations of the exact behavior.\n"
                    "4. **Output format** — say exactly what you want ('Return JSON with keys x, y') and any length limits.\n"
                    "5. **Input** — the actual data, clearly **delimited** (triple backticks, XML tags) so it can't be confused with instructions.\n\n"
                    "Be concrete and positive ('do X' beats 'don't do Y'), put the most important instruction near the start or end, and prefer explicit structure over hoping the model guesses."
                ),
                "resources": [
                    {"title": "Anthropic prompt engineering guide", "url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview", "kind": "docs", "query": "anthropic prompt engineering guide"},
                ],
            },
            {
                "title": "Chain-of-thought: ask for reasoning before the answer",
                "notes": "Letting the model 'think step by step' raises accuracy on multi-step problems.",
                "explanation": (
                    "### Reasoning space improves answers\n"
                    "**Chain-of-thought (CoT)** prompting asks the model to produce intermediate reasoning steps before the final answer ('Let's think step by step'). For multi-step tasks — math, logic, multi-hop QA — this substantially improves accuracy, because the model uses the generated tokens as a scratchpad rather than committing to an answer immediately.\n\n"
                    "Notes: CoT helps most on larger models and harder problems; for simple tasks it just adds tokens. If you only need the final answer, you can have it reason then output a clearly-delimited result to parse. Modern reasoning models do this internally, but explicit CoT still helps with non-reasoning models and gives you visibility into the logic."
                ),
                "resources": [
                    {"title": "Chain-of-Thought prompting (paper)", "url": "", "kind": "article", "query": "chain of thought prompting elicits reasoning paper"},
                ],
            },
            {
                "title": "Self-consistency and sampling multiple paths",
                "notes": "Sample several CoT answers and take the majority — trades compute for accuracy.",
                "explanation": (
                    "### Vote across reasoning paths\n"
                    "**Self-consistency** improves on CoT: instead of one greedy chain, **sample several** reasoning paths (temperature > 0) and take the **majority answer**. Different paths that converge on the same answer are more likely correct; it averages out individual reasoning mistakes.\n\n"
                    "It's a pure compute-for-accuracy trade (N× the calls), so reserve it for high-value, hard questions. The same idea generalizes to **best-of-N** with a verifier/reward model that scores candidates rather than majority-voting. Know it as the canonical 'inference-time compute' technique."
                ),
                "resources": [],
            },
            {
                "title": "Structured output and format control",
                "notes": "Specify schemas, use delimiters, prefill, or constrained decoding to get reliable JSON.",
                "explanation": (
                    "### Getting machine-parseable output\n"
                    "When another system consumes the output, free text is fragile. Techniques, weakest→strongest:\n\n"
                    "- **Describe the schema** explicitly and give a one-shot example of the exact JSON.\n"
                    "- **Delimit** clearly and ask for *only* the JSON (no prose).\n"
                    "- **Prefill** the assistant turn with the opening `{` (or an XML tag) to force the shape.\n"
                    "- **Tool/function calling** or **constrained/structured decoding** — the API guarantees valid JSON against a schema (the robust choice for production).\n\n"
                    "Always validate and have a retry/repair path. Prefer the API's structured-output/tool features over prompt-only formatting when correctness matters."
                ),
                "resources": [],
            },
            {
                "title": "System vs user roles, and role prompting",
                "notes": "The system message sets persistent behavior/persona; user turns carry the task.",
                "explanation": (
                    "### Use the message roles deliberately\n"
                    "Chat models take a **system** message (persistent instructions, persona, rules, output policy) plus alternating **user**/**assistant** turns. Put durable behavior ('You are a careful SQL assistant; never modify data') in the **system** prompt, and the specific request in the **user** turn. "
                    "**Role prompting** ('You are an expert X') can focus tone and domain framing, though its effect is modest compared to clear instructions and examples. "
                    "Keep the system prompt stable across a conversation; the model weights it strongly, and it's the right place for guardrails and format contracts."
                ),
                "resources": [],
            },
            {
                "title": "Grounding with retrieval (RAG-style prompting)",
                "notes": "Inject retrieved, cited context so answers are factual and current, not from parametric memory.",
                "explanation": (
                    "### Don't rely on the model's memory\n"
                    "For factual, current, or proprietary information, **retrieve relevant documents and put them in the context**, then instruct the model to answer *only from the provided context and cite sources*. This reduces hallucination and lets you update knowledge without retraining. "
                    "Prompt-side best practices: clearly delimit the retrieved chunks, tell the model to say 'I don't know' if the context lacks the answer, and ask for citations to specific passages. "
                    "This is the prompt half of RAG; its quality depends on retrieval, but the prompt determines whether the model actually grounds in (vs ignores) the context."
                ),
                "resources": [],
            },
            {
                "title": "Decomposition: least-to-most, ReAct, and tool prompts",
                "notes": "Break hard tasks into steps or interleave reasoning with tool/actions.",
                "explanation": (
                    "### Structure the problem-solving\n"
                    "- **Least-to-most / decomposition** — split a complex task into simpler sub-questions solved in sequence, feeding answers forward.\n"
                    "- **ReAct** — interleave **Reason**ing and **Act**ions: the model thinks, calls a tool (search, calculator, code), observes the result, and continues. The backbone of agentic prompting.\n"
                    "- **Tool prompts** — describe available tools and when to use them; the model emits a structured call.\n\n"
                    "These turn a single prediction into a controllable, inspectable process and let the model offload what it's bad at (arithmetic, fresh facts) to reliable tools. They connect prompt engineering to agent design."
                ),
                "resources": [
                    {"title": "ReAct: reasoning + acting", "url": "", "kind": "article", "query": "ReAct reasoning acting language models paper"},
                ],
            },
            {
                "title": "Failure modes: injection, sensitivity, and verbosity",
                "notes": "Prompts are brittle and attackable — guard against injection and test systematically.",
                "explanation": (
                    "### What goes wrong\n"
                    "- **Prompt injection** — untrusted input (a web page, user text) contains instructions that hijack the model ('ignore previous instructions'). Mitigate by separating trusted instructions from untrusted data, delimiting/marking data, least-privilege tools, and never trusting model output blindly.\n"
                    "- **Sensitivity** — small wording/order/format changes swing results; few-shot example order matters. Don't over-fit to one phrasing.\n"
                    "- **Verbosity / sycophancy / hedging** — models pad, agree too readily, or refuse oddly; constrain length and be explicit.\n\n"
                    "Treat prompts like code: version them, and validate against an eval set rather than eyeballing one example."
                ),
                "resources": [
                    {"title": "Prompt injection explained", "url": "", "kind": "article", "query": "prompt injection attack llm explained"},
                ],
            },
            {
                "title": "Evaluate and iterate prompts systematically",
                "notes": "Build an eval set with metrics; change one thing at a time; track regressions.",
                "explanation": (
                    "### Prompt engineering is empirical\n"
                    "Tweaking a prompt and checking one example is how you fool yourself. Instead:\n\n"
                    "1. **Curate an eval set** of representative inputs with expected outputs (or a grading rubric / LLM-as-judge).\n"
                    "2. **Define metrics** — accuracy, format-validity, latency, token cost.\n"
                    "3. **Change one variable at a time** and re-run the whole set; watch for **regressions** on cases that previously passed.\n"
                    "4. **Version prompts** and record results.\n\n"
                    "This turns prompting from vibes into engineering, and it's exactly the discipline interviewers probe for in applied-LLM roles."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Turn an unreliable zero-shot classifier prompt into a robust few-shot one with guaranteed JSON output.",
            "Design a CoT + self-consistency setup for a multi-step math word-problem task and state the cost tradeoff.",
            "Write a RAG answer prompt that cites sources and refuses when the context is insufficient.",
            "Harden a prompt that summarizes user-submitted web pages against prompt injection.",
            "Set up an eval harness to compare two prompt variants on 100 cases.",
        ],
        "common": [
            "What is in-context learning, and how does it differ from fine-tuning?",
            "When do you use few-shot over zero-shot, and what makes good examples?",
            "Explain chain-of-thought and self-consistency, and when each is worth the extra tokens.",
            "How do you reliably get valid JSON out of an LLM?",
            "What is prompt injection and how do you defend against it?",
            "How would you systematically evaluate and improve a prompt?",
        ],
    },

    "Calibration, uncertainty & OOD detection": {
        "points": [
            {
                "title": "What calibration means",
                "notes": "A calibrated model's confidence matches reality: of things predicted 80%, ~80% are correct.",
                "explanation": (
                    "### Confidence you can trust\n"
                    "A model is **calibrated** if its predicted probabilities match empirical frequencies: among all predictions made with confidence 0.8, about 80% should actually be correct. "
                    "Calibration is distinct from **accuracy** — a model can be accurate but overconfident, or mediocre but well-calibrated. It matters whenever a downstream decision uses the probability: thresholding, ranking, abstaining, cost-sensitive choices, or combining models. "
                    "If you act on '90% sure' as if it means 90%, miscalibration directly causes bad decisions, so calibration is a first-class quality, not a nicety."
                ),
                "resources": [
                    {"title": "On Calibration of Modern Neural Networks (Guo et al.)", "url": "", "kind": "article", "query": "on calibration of modern neural networks Guo paper"},
                ],
            },
            {
                "title": "Reliability diagrams and Expected Calibration Error (ECE)",
                "notes": "Bin predictions by confidence; ECE = avg |confidence − accuracy| across bins.",
                "explanation": (
                    "### Measuring miscalibration\n"
                    "A **reliability diagram** bins predictions by confidence and plots **accuracy vs confidence** per bin; perfect calibration is the diagonal. Bars below the diagonal = overconfident.\n\n"
                    "**Expected Calibration Error** summarizes the gap as a weighted average:\n\n"
                    "$$\\text{ECE}=\\sum_{m} \\frac{|B_m|}{n}\\,\\big|\\,\\text{acc}(B_m)-\\text{conf}(B_m)\\,\\big|$$\n\n"
                    "where $B_m$ are confidence bins. Lower is better. Caveats: ECE depends on bin count and only checks the top class; complement it with the **Brier score** (a proper scoring rule) and reliability plots rather than trusting a single number."
                ),
                "resources": [],
            },
            {
                "title": "Why modern networks are miscalibrated (overconfident)",
                "notes": "High-capacity nets trained with NLL push probabilities toward 0/1, overfitting confidence.",
                "explanation": (
                    "### The overconfidence problem\n"
                    "Deep networks are typically **overconfident**: they assign very high probability even when wrong. Causes include training to minimize NLL with high capacity (the model keeps pushing correct-class logits up well past the point of correct classification), lack of regularization on probabilities, and label/temperature effects. "
                    "Modern large models trained on cross-entropy show large ECE out of the box. "
                    "Things that *help* calibration: temperature scaling (post-hoc), label smoothing, ensembles, and not over-training. Things that *hurt*: high capacity, batchnorm interactions, and aggressive fitting. Knowing this is why a raw softmax probability shouldn't be treated as a true probability without checking."
                ),
                "resources": [],
            },
            {
                "title": "Calibration methods: temperature scaling, Platt, isotonic",
                "notes": "Post-hoc fixes on a validation set; temperature scaling (one scalar T on logits) is the default.",
                "explanation": (
                    "### Fixing it after training\n"
                    "These rescale a trained model's outputs using a held-out validation set:\n\n"
                    "- **Temperature scaling** — divide logits by a single learned scalar $T$ before softmax: $\\text{softmax}(z/T)$. $T>1$ softens overconfident outputs. One parameter, doesn't change accuracy (argmax unchanged), remarkably effective — the **default**.\n"
                    "- **Platt scaling** — fit a logistic regression on the scores (binary).\n"
                    "- **Isotonic regression** — fit a non-parametric monotonic mapping; more flexible but needs more data and can overfit.\n\n"
                    "All are cheap and post-hoc. Temperature scaling is the first thing to try; reach for isotonic only with ample validation data."
                ),
                "resources": [],
            },
            {
                "title": "Aleatoric vs epistemic uncertainty",
                "notes": "Aleatoric = irreducible data noise; epistemic = model uncertainty, reducible with more data.",
                "explanation": (
                    "### Two sources of 'I'm not sure'\n"
                    "- **Aleatoric** — inherent randomness/ambiguity in the data (a blurry image, an ambiguous sentence). More data **won't** reduce it; the best you can do is model the noise.\n"
                    "- **Epistemic** — uncertainty about the *model/parameters* due to limited data, especially in regions the training set didn't cover. More data (or better coverage) **reduces** it.\n\n"
                    "The distinction guides action: high epistemic uncertainty → collect/label more data, or flag inputs as out-of-distribution; high aleatoric → the task is just noisy, set expectations accordingly. Epistemic uncertainty is also what's high on OOD inputs, linking this to OOD detection."
                ),
                "resources": [],
            },
            {
                "title": "Estimating uncertainty: ensembles, MC dropout, Bayesian",
                "notes": "Disagreement across models/forward passes approximates (epistemic) uncertainty.",
                "explanation": (
                    "### Getting an uncertainty estimate\n"
                    "- **Deep ensembles** — train several models (different seeds); their **disagreement** on an input estimates epistemic uncertainty. Simple, strong, but N× cost. The practical gold standard.\n"
                    "- **MC dropout** — keep dropout *on at inference*, run several forward passes, use the variance of predictions. A cheap approximation to a Bayesian posterior.\n"
                    "- **Bayesian NNs / Laplace approximation** — put distributions over weights; principled but expensive/approximate.\n\n"
                    "In all cases, **spread of predictions** ≈ uncertainty. Use the mean as the prediction and the variance/entropy as the confidence signal for abstention or OOD flags."
                ),
                "resources": [],
            },
            {
                "title": "Out-of-distribution (OOD) detection: why and what",
                "notes": "Models are unreliable on inputs unlike training data; detect them rather than trust the output.",
                "explanation": (
                    "### Knowing when not to trust the model\n"
                    "Models give confident, meaningless answers on inputs **far from the training distribution** (a new class, corrupted input, a different domain). **OOD detection** flags such inputs so the system can defer to a human, abstain, or route elsewhere — critical for safety-sensitive deployments. "
                    "The challenge: neural nets are often *more* confident on some OOD inputs, so a raw softmax max isn't enough. OOD detection is essentially asking 'is this input from the distribution my model was trained on?' — high epistemic uncertainty is the signal, and several scores try to capture it."
                ),
                "resources": [],
            },
            {
                "title": "OOD methods: max-softmax, energy, Mahalanobis, density",
                "notes": "Score 'in-distribution-ness' via softmax confidence, energy, feature-space distance, or a density model.",
                "explanation": (
                    "### Common detectors (roughly weakest→strongest)\n"
                    "- **Max softmax probability (MSP)** — low max prob ⇒ likely OOD. Simple baseline; weak because of overconfidence.\n"
                    "- **Energy score** — use $-\\log\\sum_j e^{z_j}$; better-behaved than softmax for OOD.\n"
                    "- **Mahalanobis distance** — fit class-conditional Gaussians in **feature space**; distance to the nearest class mean flags OOD. Strong, uses representations not just logits.\n"
                    "- **Density / likelihood models** — model $p(x)$ directly; low likelihood ⇒ OOD (though deep generative models can be unreliable here).\n\n"
                    "Distance-in-feature-space methods (Mahalanobis, kNN) tend to beat logit-only methods. Pick based on access to features and compute."
                ),
                "resources": [],
            },
            {
                "title": "Selective prediction (abstention)",
                "notes": "Let the model say 'I don't know' below a confidence threshold; trade coverage for accuracy.",
                "explanation": (
                    "### Answer only when confident\n"
                    "**Selective prediction** uses a confidence/uncertainty score to **abstain** on low-confidence inputs (route to a human or a fallback). This trades **coverage** (fraction answered) for **accuracy on the answered set**, summarized by a **risk–coverage curve** (and its area). "
                    "It needs a *good* confidence signal — which is why calibration and uncertainty estimation matter here. In practice you pick a threshold to hit a target precision/error rate. For LLMs this maps to 'say I don't know', defer to retrieval, or escalate — far safer than always answering."
                ),
                "resources": [],
            },
            {
                "title": "Calibration & uncertainty for LLMs",
                "notes": "Use token logprobs, sampled-answer agreement, or verbalized confidence — all imperfect; RLHF can worsen calibration.",
                "explanation": (
                    "### The LLM-specific picture\n"
                    "Estimating LLM confidence is harder than for classifiers:\n\n"
                    "- **Token logprobs** — sequence probability is a signal but conflates fluency with correctness.\n"
                    "- **Sampled-answer agreement** — sample several answers; high agreement (self-consistency) ≈ higher confidence; disagreement flags uncertainty.\n"
                    "- **Verbalized confidence** — ask the model to rate its certainty; usable but often poorly calibrated and gameable.\n\n"
                    "Notably, base models can be fairly calibrated on multiple-choice, but **RLHF tends to degrade calibration** (models become confidently agreeable). Tie-in: poor calibration ⇒ hallucinations stated with high confidence, so calibration and **hallucination detection / abstention** are deeply linked."
                ),
                "resources": [],
            },
            {
                "title": "Evaluation metrics: Brier score, NLL, AUROC for OOD",
                "notes": "Brier/NLL are proper scores for calibration; OOD detection is judged by AUROC/AUPR.",
                "explanation": (
                    "### Measuring it properly\n"
                    "- **Brier score** — mean squared error between predicted probability and the 0/1 outcome; a **proper scoring rule** that rewards calibration *and* accuracy.\n"
                    "- **NLL (log loss)** — also proper; penalizes confident mistakes harshly.\n"
                    "- **ECE** — interpretable calibration gap, but bin-sensitive and not proper — use alongside the above.\n"
                    "- **OOD detection** — treat as binary (ID vs OOD) and report **AUROC** / **AUPR** of the score, plus FPR@95%TPR.\n\n"
                    "Best practice: report a proper score (Brier/NLL) **and** a reliability diagram for calibration, and AUROC for OOD — no single number captures it all."
                ),
                "resources": [],
            },
        ],
        "example": [
            "A model is 92% accurate but its ECE is 0.15 — what does that mean and how do you fix it?",
            "Implement temperature scaling: what do you optimize, on what data, and why doesn't accuracy change?",
            "Design an OOD detector for an image classifier and choose a metric to evaluate it.",
            "Build a selective-prediction system targeting 99% precision — describe the score and threshold choice.",
            "How would you estimate and report uncertainty for an LLM's factual answers?",
        ],
        "common": [
            "What is calibration, and how is it different from accuracy?",
            "Explain ECE and reliability diagrams, and the pitfalls of ECE.",
            "Why are modern neural nets overconfident, and how does temperature scaling help?",
            "Distinguish aleatoric vs epistemic uncertainty and how you'd estimate each.",
            "What is OOD detection and what methods go beyond max-softmax-probability?",
            "How does RLHF affect an LLM's calibration, and what are the implications?",
        ],
    },

    "Recommender systems & learning-to-rank": {
        "points": [
            {
                "title": "The recommendation funnel: retrieval → ranking → re-ranking",
                "notes": "Narrow millions of items to a handful in stages — cheap recall first, expensive precision last.",
                "explanation": (
                    "### Why it's multi-stage\n"
                    "You can't score millions of items with a heavy model per request, so recommenders use a **funnel**:\n\n"
                    "```mermaid\nflowchart LR\n  C[Corpus ~10^6+] --> R[Retrieval / candidate gen ~1000]\n  R --> K[Ranking ~100]\n  K --> RR[Re-ranking ~10]\n  RR --> U[User]\n```\n\n"
                    "- **Retrieval (candidate generation)** — cheap, high-recall; cut the corpus to ~hundreds–thousands (e.g. ANN over embeddings).\n"
                    "- **Ranking** — a richer model scores those candidates precisely.\n"
                    "- **Re-ranking** — apply business logic: diversity, freshness, dedup, policy.\n\n"
                    "Each stage trades cost for precision. This architecture is the backbone of every large-scale recommender and a common system-design prompt."
                ),
                "resources": [
                    {"title": "YouTube deep-learning recommendations (paper)", "url": "", "kind": "article", "query": "deep neural networks youtube recommendations paper covington"},
                ],
            },
            {
                "title": "Collaborative filtering",
                "notes": "Recommend from behavior patterns: users who liked similar items will like similar items.",
                "explanation": (
                    "### 'People like you also liked…'\n"
                    "**Collaborative filtering (CF)** uses the **user–item interaction matrix** (clicks, ratings, purchases) — not item content. Two flavors:\n\n"
                    "- **User-based** — find users similar to you, recommend what they liked.\n"
                    "- **Item-based** — recommend items similar to ones you liked, where 'similar' = co-liked by the same users.\n\n"
                    "Strength: needs no content features, captures taste patterns. Weakness: **cold start** (new users/items have no interactions) and **sparsity** (most user–item pairs are unobserved). Latent-factor models (next) address sparsity by learning dense representations from the same matrix."
                ),
                "resources": [],
            },
            {
                "title": "Matrix factorization and latent factors",
                "notes": "Approximate the interaction matrix as user × item embeddings; dot product predicts affinity.",
                "explanation": (
                    "### Learning taste vectors\n"
                    "**Matrix factorization** approximates the sparse interaction matrix $R$ as the product of low-rank **user** and **item** embedding matrices:\n\n"
                    "$$\\hat r_{ui} = \\mathbf{p}_u^\\top \\mathbf{q}_i \\;(+\\,b_u + b_i)$$\n\n"
                    "Each user and item gets a $k$-dim latent vector; their dot product predicts affinity. Train by minimizing error on observed entries with regularization (classic **ALS**/**SGD**, popularized by the Netflix Prize). "
                    "It generalizes from sparse data by placing similar users/items near each other in latent space, and is the conceptual ancestor of modern **two-tower** retrieval. Bias terms capture popularity and user leniency."
                ),
                "resources": [],
            },
            {
                "title": "Content-based and hybrid recommenders",
                "notes": "Use item/user features (content) to handle cold start; hybrids combine CF + content.",
                "explanation": (
                    "### When behavior data isn't enough\n"
                    "**Content-based** recommendation uses item **features** (text, category, embeddings) and a user profile of features they've liked — 'you watched sci-fi, here's more sci-fi'. It handles **new items** (a fresh item has features even with zero interactions) and is explainable, but tends to over-specialize (low diversity) and needs good features.\n\n"
                    "**Hybrid** systems combine collaborative + content signals — e.g. use content features to bootstrap cold-start items, then let CF take over as interactions accumulate. Most production systems are hybrids, feeding both interaction and content/context features into the retrieval and ranking models."
                ),
                "resources": [],
            },
            {
                "title": "Two-tower retrieval and ANN candidate generation",
                "notes": "Separate user & item encoders → embeddings; retrieve top-k by approximate nearest neighbor.",
                "explanation": (
                    "### How modern retrieval scales\n"
                    "A **two-tower** model has separate neural encoders for the **user/context** and the **item**, each producing an embedding in a shared space; relevance is their dot product. Crucially, **item embeddings are precomputed** and indexed, so serving is: encode the user once → **approximate nearest neighbor (ANN)** search (HNSW, IVF/ScaNN) over millions of item vectors → top-k candidates in milliseconds.\n\n"
                    "This decoupling is what makes deep retrieval tractable at scale. Training uses positives (engaged items) vs sampled negatives with a contrastive/softmax loss. It's the embedding-retrieval pattern shared with semantic search and RAG."
                ),
                "resources": [],
            },
            {
                "title": "Learning-to-rank: pointwise, pairwise, listwise",
                "notes": "Optimize ordering, not absolute scores; pairwise/listwise match ranking metrics better.",
                "explanation": (
                    "### Optimizing for order\n"
                    "Ranking cares about **relative order**, not absolute scores. Three formulations:\n\n"
                    "- **Pointwise** — predict a score/relevance per item independently (regression/classification), then sort. Simple but ignores that ranking is relative.\n"
                    "- **Pairwise** — learn which of two items should rank higher (e.g. **RankNet**, **LambdaMART**); directly models preferences.\n"
                    "- **Listwise** — optimize a loss over the whole ranked list, closer to metrics like NDCG (**ListNet**, LambdaMART with λ-gradients).\n\n"
                    "Pairwise/listwise generally win because they align with how ranking is *evaluated*. **LambdaMART** (GBDT + pairwise λ-gradients) was long the competition-winning default."
                ),
                "resources": [
                    {"title": "Learning to rank overview", "url": "", "kind": "article", "query": "learning to rank pointwise pairwise listwise lambdamart"},
                ],
            },
            {
                "title": "Ranking models and features (GBDT, deep, DLRM)",
                "notes": "Combine many features (user, item, context, cross) via GBDTs or deep nets with embeddings.",
                "explanation": (
                    "### What scores the candidates\n"
                    "The ranking stage is feature-rich. **Features**: user (history, demographics), item (popularity, attributes), **context** (time, device), and **cross features** (user×item interactions). **Models**:\n\n"
                    "- **Gradient-boosted trees (GBDT)** — strong on tabular/dense features, the long-time default for LTR.\n"
                    "- **Deep ranking nets** — learn embeddings for high-cardinality categoricals (IDs) and feature crosses; **DLRM**, **Wide & Deep**, DCN are canonical.\n"
                    "- **Multi-task** — predict click *and* like *and* watch-time jointly, then combine.\n\n"
                    "High-cardinality ID embeddings dominate memory and are why recommender models can be huge despite simple per-example compute."
                ),
                "resources": [],
            },
            {
                "title": "Implicit feedback and negative sampling",
                "notes": "Most signals are implicit (clicks, not ratings); absence isn't a clear negative → sample carefully.",
                "explanation": (
                    "### Learning from clicks, not stars\n"
                    "Real systems mostly have **implicit feedback** (views, clicks, dwell, purchases) rather than explicit ratings. This is tricky: a non-click might mean dislike — or the item was never seen. So you can't treat all non-interactions as negatives.\n\n"
                    "**Negative sampling** picks a manageable set of negatives per positive: random items, **popularity-weighted**, or **hard negatives** (high-scoring but not engaged) which teach finer distinctions. The choice strongly affects quality. You also weight by confidence (a purchase > a click) and must correct for **exposure/position bias** — items shown more get more clicks regardless of relevance."
                ),
                "resources": [],
            },
            {
                "title": "Offline evaluation metrics: NDCG, MAP, recall@k",
                "notes": "Rank-aware metrics that reward putting relevant items high; recall@k for retrieval.",
                "explanation": (
                    "### Judging a ranking\n"
                    "- **Recall@k** — fraction of relevant items captured in the top-k. The key **retrieval** metric (did candidate generation include the good items?).\n"
                    "- **Precision@k / MAP** — precision among top-k; MAP averages precision across positions and queries.\n"
                    "- **NDCG@k** — **N**ormalized **D**iscounted **C**umulative **G**ain: rewards relevant items *and* discounts by position (a hit at rank 1 ≫ rank 10), normalized to $[0,1]$ by the ideal ordering. The standard **ranking** metric, handles graded relevance.\n\n"
                    "Use recall@k to evaluate the retrieval stage and NDCG/MAP for ranking. But offline metrics are proxies — confirm with online A/B tests."
                ),
                "resources": [],
            },
            {
                "title": "Cold start, online serving, and feedback loops",
                "notes": "New users/items need bootstrapping; production must serve fast and beware self-reinforcing bias.",
                "explanation": (
                    "### Production realities\n"
                    "- **Cold start** — new **users** (no history) get popularity/contextual/onboarding-based recs; new **items** lean on content features until interactions accrue; exploration (bandits) gathers signal.\n"
                    "- **Serving** — the funnel runs in real time: precomputed item embeddings + ANN for retrieval, a fast ranking model, feature stores for low-latency features, caching of hot results.\n"
                    "- **Feedback loops & bias** — the model influences what users see, which becomes its next training data, creating **popularity/filter-bubble** and **position bias**. Mitigate with exploration, debiasing (inverse-propensity weighting), and diversity in re-ranking.\n\n"
                    "Always validate with **online A/B tests** — offline gains often don't transfer due to these loop effects."
                ),
                "resources": [],
            },
        ],
        "example": [
            "Design a video recommendation system for 100 M users and 10 M items end-to-end (retrieval → ranking → re-rank).",
            "Explain how you'd build a two-tower retrieval model and serve it with ANN at scale.",
            "You have only implicit click data — how do you choose negatives and correct for position bias?",
            "Pick metrics to evaluate the retrieval stage vs the ranking stage and justify each.",
            "How would you handle cold-start for brand-new items and brand-new users?",
        ],
        "common": [
            "Why are recommenders built as a retrieval→ranking→re-ranking funnel?",
            "Explain collaborative filtering vs content-based, and the cold-start problem.",
            "What is matrix factorization, and how does it relate to two-tower retrieval?",
            "Compare pointwise, pairwise, and listwise learning-to-rank.",
            "Define NDCG and recall@k and say which stage each evaluates.",
            "What feedback-loop / bias problems arise in deployed recommenders and how do you mitigate them?",
        ],
    },
}


AUTHORED_ORDER: dict[str, list[dict]] = {
    "System Design": [
        {"title": "System design interview framework + capacity estimation", "level": "foundational"},
        {"title": "Fundamentals: load balancing, caching, sharding, replication, consistency", "level": "foundational"},
        {"title": "Design URL shortener / pastebin (warmup)", "level": "foundational"},
        {"title": "Consistent hashing & data partitioning", "level": "intermediate"},
        {"title": "Caching strategies, CDN & cache invalidation", "level": "intermediate"},
        {"title": "Idempotency, retries & exactly-once semantics", "level": "intermediate"},
        {"title": "Design rate limiter / distributed counter", "level": "intermediate"},
        {"title": "Observability: metrics, logging, distributed tracing", "level": "intermediate"},
        {"title": "Search, typeahead & autocomplete", "level": "intermediate"},
        {"title": "Design streaming chat / news feed / notification system", "level": "intermediate"},
        {"title": "Design distributed KV store / metadata service", "level": "advanced"},
        {"title": "Design distributed message queue / log (Kafka-style)", "level": "advanced"},
        {"title": "Design model evaluation / observability platform", "level": "advanced"},
        {"title": "Design LLM inference serving system (batching, KV cache, autoscaling)", "level": "advanced"},
        {"title": "Design RAG pipeline w/ vector search + eval", "level": "advanced"},
        {"title": "Design agent orchestration / tool-use system", "level": "advanced"},
        {"title": "Design distributed training cluster (DP/MP/PP, fault tolerance)", "level": "advanced"},
    ],
    "AI Infra": [
        {"title": "GPU architecture: SMs, memory hierarchy, Tensor Cores, NVLink", "level": "foundational"},
        {"title": "Memory math, arithmetic intensity & the roofline model", "level": "foundational"},
        {"title": "CUDA programming basics: kernels, shared memory, occupancy", "level": "intermediate"},
        {"title": "Roofline model, arithmetic intensity & profiling", "level": "intermediate"},
        {"title": "Mixed precision training & numerical stability", "level": "intermediate"},
        {"title": "NCCL collectives & communication patterns", "level": "intermediate"},
        {"title": "Input pipeline & data loading at scale", "level": "intermediate"},
        {"title": "Distributed training: DDP, FSDP, ZeRO-1/2/3, TP, PP", "level": "advanced"},
        {"title": "FlashAttention & memory-efficient attention variants", "level": "advanced"},
        {"title": "Quantization (INT8, FP8, FP4) & speculative decoding", "level": "advanced"},
        {"title": "Inference optimization: KV cache, PagedAttention, continuous batching (vLLM)", "level": "advanced"},
        {"title": "Serving frameworks: Triton, TensorRT-LLM, SGLang", "level": "advanced"},
        {"title": "MoE training & serving (expert & sequence parallelism)", "level": "advanced"},
        {"title": "Checkpointing, fault tolerance, large-cluster observability", "level": "advanced"},
        {"title": "Kubernetes / SLURM for ML workloads", "level": "intermediate"},
    ],
    "AI/ML": [
        {"title": "Probability/stats fundamentals (Bayes, MLE, distributions)", "level": "foundational"},
        {"title": "Classical ML refresher: regression, trees, gradient boosting", "level": "foundational"},
        {"title": "Embeddings & representation learning", "level": "foundational"},
        {"title": "Recommender systems & learning-to-rank", "level": "intermediate"},
        {"title": "Transformer deep dive: MHA, KV cache, RoPE, MoE routing", "level": "intermediate"},
        {"title": "Pretraining: scaling laws, data mixing, tokenization", "level": "intermediate"},
        {"title": "Decoding & sampling strategies (greedy, temperature, top-k/p, speculative)", "level": "intermediate"},
        {"title": "Prompt engineering & in-context learning", "level": "intermediate"},
        {"title": "Evaluation: benchmarks, human eval, hallucination detection", "level": "intermediate"},
        {"title": "RAG architectures vs fine-tuning tradeoffs", "level": "intermediate"},
        {"title": "Long-context & attention variants (GQA/MQA, sliding-window, context extension)", "level": "advanced"},
        {"title": "Post-training: SFT, RLHF, DPO, RLAIF, Constitutional AI", "level": "advanced"},
        {"title": "Calibration, uncertainty & OOD detection", "level": "advanced"},
        {"title": "Agentic systems: tool use, planning, MCP, multi-step reasoning", "level": "advanced"},
        {"title": "Diffusion models & multimodal architectures", "level": "advanced"},
        {"title": "AI safety: alignment, interpretability, red-teaming", "level": "advanced"},
    ],
}
