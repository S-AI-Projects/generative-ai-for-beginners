# R40-T041: Building a Local Search Application

## Overview

This lab demonstrates a simple local search application using Python's standard library.

It searches a small collection of documents using token overlap. Each matching document receives a score based on the number of unique words shared with the query.

## Requirements

- Python 3
- No external packages or API keys required.

## Local document collection

The example uses three sample documents:

| ID | Text |
|---|---|
| 1 | red apple |
| 2 | red berry |
| 3 | blue sky |

## Run the example

From the repository root, run:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py red
```

Expected output:

```json
[
  {
    "id": 1,
    "score": 1
  },
  {
    "id": 2,
    "score": 1
  }
]
```

Try a query with no matches:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py orange
```

Expected output:

```json
[]
```

You can also set a minimum score:

```bash
python3 08-building-search-applications/applied-labs/r40-t041/example.py red --min-score 2
```

Expected output:

```json
[]
```

## Run automated tests

```bash
python3 -m unittest discover -s 08-building-search-applications/applied-labs/r40-t041 -p "test_*.py"
```

## Connection to the lesson

The main lesson introduces search applications, including keyword search and semantic search using embeddings and cosine similarity.

This lab demonstrates a smaller foundational idea: keyword-based retrieval. It compares the unique words in a query with the unique words in each local document and calculates a simple overlap score.

Unlike the lesson's embedding-based semantic search, this example does not understand meaning or related words. For example, searching for `car` will not match `automobile`.

## Limitations

- Uses a small hardcoded local collection.
- Matches exact words after converting them to lowercase.
- Splits text using whitespace; punctuation is not normalized.
- Does not use embeddings, vector databases, or semantic similarity.
- Scores represent shared unique tokens, not relevance probabilities.
- Results are ordered by descending score, then ascending document ID.

This is a learning example, not a production search engine.
