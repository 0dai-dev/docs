#!/usr/bin/env python3
"""Semantic search over ai/experience/ using TF-IDF scoring.

Ranks results by relevance instead of simple substring matching.
Zero external dependencies — uses Python stdlib only.

Usage:
    python3 scripts/search_experience.py --target /path --query "bugfix auth"
    0dai search --target /path --query "deployment failed"
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def build_index(root: pathlib.Path) -> tuple[list[dict], list[Counter]]:
    docs: list[dict] = []
    token_counts: list[Counter] = []

    for subdir in ["events", "candidates", "accepted", "outbox"]:
        base = root / "ai" / "experience" / subdir
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue

            tokens = tokenize(text)
            if not tokens:
                continue

            docs.append({
                "path": str(path.relative_to(root)),
                "category": subdir,
                "preview": text[:300].strip(),
                "size": len(text),
            })
            token_counts.append(Counter(tokens))

    return docs, token_counts


def tfidf_search(
    query: str,
    docs: list[dict],
    token_counts: list[Counter],
    top_k: int = 10,
) -> list[dict]:
    query_tokens = tokenize(query)
    if not query_tokens or not docs:
        return []

    n = len(docs)

    # Document frequency for each query token
    df: dict[str, int] = {}
    for token in query_tokens:
        df[token] = sum(1 for tc in token_counts if token in tc)

    # Score each document
    scored: list[tuple[float, int]] = []
    for idx, tc in enumerate(token_counts):
        score = 0.0
        doc_len = sum(tc.values()) or 1
        for token in query_tokens:
            tf = tc.get(token, 0) / doc_len
            idf = math.log((n + 1) / (df.get(token, 0) + 1)) + 1
            score += tf * idf
        if score > 0:
            scored.append((score, idx))

    scored.sort(key=lambda x: -x[0])

    results = []
    for score, idx in scored[:top_k]:
        entry = dict(docs[idx])
        entry["score"] = round(score, 4)
        results.append(entry)

    return results


def main() -> None:
    target = pathlib.Path(".")
    query = ""
    top_k = 10

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--target" and i + 1 < len(sys.argv):
            target = pathlib.Path(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--query" and i + 1 < len(sys.argv):
            query = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--top" and i + 1 < len(sys.argv):
            top_k = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if not query:
        print("usage: search_experience.py --target <path> --query <text>", file=sys.stderr)
        raise SystemExit(1)

    docs, token_counts = build_index(target)
    results = tfidf_search(query, docs, token_counts, top_k)

    output = {
        "query": query,
        "indexed_documents": len(docs),
        "matches": len(results),
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
