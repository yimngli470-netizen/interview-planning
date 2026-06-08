"""One-off batch: LLM-enrich the curated DEFAULT topics with comprehensive,
uncapped learning points — each now carrying a long-form markdown `explanation`
(KaTeX + mermaid) and 1-3 free `resources` — plus example/common questions, AND
a per-domain pedagogical ORDER (learning path + difficulty level).

Results are cached to JSON (resumable) and emitted as app/content_generated.py,
which the seeder merges additively on top of the hand-authored content.py.

Run inside the backend container:
    docker compose exec -T backend python _enrich.py "System Design" "AI Infra" "AI/ML"
Re-running skips topics already cached in the v2 (explanation-bearing) format.
"""
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import content, llm
from app.seed import SKIP_GENERATED  # flagship topics — hand-authored, don't regen points
try:
    from app.content_authored import AUTHORED  # hand-authored rich topics — never regenerate
except Exception:  # noqa: BLE001
    AUTHORED = {}
# Titles we must never call the API for (hand-authored already).
NEVER_GENERATE = set(SKIP_GENERATED) | set(AUTHORED)

CACHE = "/app/app/_generated_cache.json"
OUT = "/app/app/content_generated.py"
MAX_WORKERS = 4

_lock = threading.Lock()


def load_cache() -> dict:
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with _lock:
        tmp = CACHE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CACHE)


def _is_v2(entry: dict) -> bool:
    """A v2 entry stores points as dicts with an `explanation` key (v1 used
    [title, notes] pairs and had no explanation/resources)."""
    pts = entry.get("points") if isinstance(entry, dict) else None
    return bool(pts) and isinstance(pts[0], dict) and "explanation" in pts[0]


def _clean_resources(raw) -> list[dict]:
    """Keep only well-formed resource dicts (the model occasionally emits a bare
    string or a partial object)."""
    out = []
    for r in raw or []:
        if isinstance(r, dict) and (r.get("title") or r.get("query") or r.get("url")):
            out.append({
                "title": (r.get("title") or "").strip(),
                "url": (r.get("url") or "").strip(),
                "kind": (r.get("kind") or "article").strip(),
                "query": (r.get("query") or "").strip(),
            })
        elif isinstance(r, str) and r.strip():
            out.append({"title": r.strip(), "url": "", "kind": "article", "query": r.strip()})
    return out


def enrich_one(domain: str, title: str) -> tuple[str, dict | None]:
    r = llm.generate_topic_content(title, domain)
    if not r:
        return title, None
    points = []
    for lp in r.get("learning_points", []):
        # Tolerate schema drift: a point may arrive as a bare string instead of
        # an object — coerce it rather than dropping the whole topic.
        if isinstance(lp, str):
            t = lp.strip()
            if t:
                points.append({"title": t[:300], "notes": "", "explanation": "", "resources": []})
            continue
        if not isinstance(lp, dict):
            continue
        t = (lp.get("title") or "").strip()
        if not t:
            continue
        points.append({
            "title": t,
            "notes": (lp.get("details") or "").strip(),
            "explanation": (lp.get("explanation") or "").strip(),
            "resources": _clean_resources(lp.get("resources")),
        })
    return title, {
        "points": points,
        "example": [q.strip() for q in r.get("example_questions", []) if isinstance(q, str) and q.strip()],
        "common": [q.strip() for q in r.get("common_questions", []) if isinstance(q, str) and q.strip()],
    }


def main(domains: list[str]) -> None:
    cache = load_cache()
    order = cache.get("__order__", {})

    # 1) Per-topic enrichment (skip flagships + anything already v2-cached).
    jobs = []
    for domain in domains:
        for spec in content.CONTENT_BY_DOMAIN.get(domain, []):
            title = spec["title"]
            if title in NEVER_GENERATE:
                continue
            if title in cache and _is_v2(cache[title]):
                continue
            jobs.append((domain, title))
    print(f"{len(jobs)} topics to enrich. Workers={MAX_WORKERS}", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(enrich_one, d, t): t for d, t in jobs}
        for fut in as_completed(futs):
            title = futs[fut]
            try:
                title, data = fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"  FAIL {title[:50]}: {e}", flush=True)
                continue
            done += 1
            if data is None:
                print(f"  [{done}/{len(jobs)}] NONE {title[:50]}", flush=True)
                continue
            cache[title] = data
            save_cache(cache)
            n_exp = sum(1 for p in data["points"] if p["explanation"])
            n_res = sum(len(p["resources"]) for p in data["points"])
            print(f"  [{done}/{len(jobs)}] {len(data['points'])} pts ({n_exp} explained, "
                  f"{n_res} resources), {len(data['example'])+len(data['common'])} qs  {title[:46]}", flush=True)

    # 2) Per-domain ordering (learning path + level). Covers ALL topics incl. flagships.
    for domain in domains:
        titles = [s["title"] for s in content.CONTENT_BY_DOMAIN.get(domain, [])]
        ordered = llm.order_domain(domain, titles)
        if ordered:
            order[domain] = [{"title": o["title"], "level": o.get("level", "")} for o in ordered]
            cache["__order__"] = order
            save_cache(cache)
            print(f"  ORDER {domain}: {len(ordered)} topics sequenced", flush=True)
        else:
            print(f"  ORDER {domain}: FAILED (keeping any prior)", flush=True)

    emit(cache)
    n_topics = sum(1 for k in cache if k != "__order__")
    print(f"Wrote {OUT} with {n_topics} topics + ordering for {len(order)} domains.", flush=True)


def _norm_points(entry: dict) -> list[dict]:
    """Normalize an entry's points to the v2 dict shape, upgrading any legacy
    [title, notes] pairs (empty explanation/resources) so the emitted file is
    uniform and the seeder only handles one format."""
    out = []
    for p in entry.get("points", []):
        if isinstance(p, dict):
            out.append({
                "title": p.get("title", ""), "notes": p.get("notes", ""),
                "explanation": p.get("explanation", ""), "resources": p.get("resources") or [],
            })
        else:  # legacy [title, notes]
            t, n = (list(p) + ["", ""])[:2]
            out.append({"title": t, "notes": n, "explanation": "", "resources": []})
    return out


def emit(cache: dict) -> None:
    order = cache.get("__order__", {})
    lines = [
        '"""AUTO-GENERATED by _enrich.py — comprehensive LLM-authored learning points',
        "(each with a markdown `explanation` + free `resources`), questions, and a per-domain",
        "learning-path ORDER. Merged additively by the seeder on top of curated content.py.",
        'Regenerate with _enrich.py; do not hand-edit."""',
        "",
        "GENERATED: dict[str, dict] = {",
    ]
    for title in sorted(k for k in cache if k != "__order__"):
        d = cache[title]
        lines.append(f"    {title!r}: {{")
        lines.append('        "points": [')
        for p in _norm_points(d):
            lines.append("            {")
            lines.append(f'                "title": {p["title"]!r},')
            lines.append(f'                "notes": {p["notes"]!r},')
            lines.append(f'                "explanation": {p["explanation"]!r},')
            lines.append(f'                "resources": {p["resources"]!r},')
            lines.append("            },")
        lines.append("        ],")
        lines.append(f'        "example": {d["example"]!r},')
        lines.append(f'        "common": {d["common"]!r},')
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("# domain -> ordered [{title, level}] (index drives path_order)")
    lines.append(f"ORDER: dict[str, list[dict]] = {order!r}")
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    domains = sys.argv[1:] or ["System Design", "AI Infra", "AI/ML"]
    main(domains)
