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
}
