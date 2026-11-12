import argparse
import json


# Small local fixture (mock documents)
DOCUMENTS = [
    {"id": 1, "text": "red apple"},
    {"id": 2, "text": "red berry"},
    {"id": 3, "text": "blue sky"},
]


def search(query, min_score=1):
    """Search local documents using unique-token overlap."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if isinstance(min_score, bool) or not isinstance(min_score, int):
        raise ValueError("Minimum score must be an integer.")

    if min_score < 0:
        raise ValueError("Minimum score cannot be negative.")

    query_tokens = set(query.lower().split())

    results = []

    for document in DOCUMENTS:
        document_tokens = set(document["text"].lower().split())

        score = len(query_tokens & document_tokens)

        if score >= min_score:
            results.append({
                "id": document["id"],
                "score": score
            })

    # Highest score first; smaller source ID breaks ties.
    results.sort(key=lambda result: (-result["score"], result["id"]))

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search a small local document collection."
    )
    parser.add_argument("query", help="Words to search for")
    parser.add_argument(
        "--min-score",
        type=int,
        default=1,
        help="Minimum token-overlap score (default: 1)"
    )

    args = parser.parse_args()

    print(json.dumps(search(args.query, args.min_score), indent=2))
    
