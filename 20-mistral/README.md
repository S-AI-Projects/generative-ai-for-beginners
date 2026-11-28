# Building with Mistral Models 

## Introduction 

This lesson will cover: 
- Exploring the different Mistral Models 
- Understanding the use-cases and scenarios for each model 
- Exploring code samples that show the unique features of each model. 

## The Mistral Models 

In this lesson, we will explore 3 different Mistral models: 
**Mistral Large**, **Mistral Small** and **Mistral Nemo**. 

Each of these models is available free on [Microsoft Foundry Models](https://ai.azure.com/catalog/models?WT.mc_id=academic-105485-koreyst). The code in this notebook will be using these models to run the code.

> **Note:** GitHub Models is retiring at the end of July 2026. Here are more details on using [Microsoft Foundry Models](https://learn.microsoft.com/azure/ai-foundry/model-inference/overview?WT.mc_id=academic-105485-koreyst) to prototype with AI models. 


## Mistral Large 2 (2407)
Mistral Large 2 is currently the flagship model from Mistral and is designed for enterprise use. 

The model is an upgrade to the original Mistral Large by offering 
-  Larger Context Window - 128k vs 32k 
-  Better performance on Math and Coding Tasks - 76.9% average accuracy vs 60.4% 
-  Increased multilingual performance - languages include: English, French, German, Spanish, Italian, Portuguese, Dutch, Russian, Chinese, Japanese, Korean, Arabic, and Hindi.

With these features, Mistral Large excels at 
- *Retrieval Augmented Generation (RAG)* - due to the larger context window
- *Function Calling* - this model has native function calling which allows integration with external tools and APIs. These calls can be made both in parallel or one after another in a sequential order. 
- *Code Generation* - this model excels on Python, Java, TypeScript and C++ generation. 

### RAG Example using Mistral Large 2 

In this example, we are using Mistral Large 2 to run a RAG pattern over a text document. The question is written in Korean and asks about the author's activities before college. 

It uses Cohere Embeddings Model to create embeddings of the text document as well as the question. For this sample, it uses the faiss Python package as a vector store. 

The prompt sent to the Mistral model includes both the questions and the retrieved chunks that are similar to the question. The Model then provides a natural language response. 

```python 
pip install faiss-cpu
```

```python 
import requests
import numpy as np
import faiss
import os

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import EmbeddingsClient

# Get these from your Microsoft Foundry project's "Overview" page
endpoint = os.environ["AZURE_INFERENCE_ENDPOINT"]
model_name = "Mistral-large"
token = os.environ["AZURE_INFERENCE_CREDENTIAL"]

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = requests.get('https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/examples/data/paul_graham/paul_graham_essay.txt')
text = response.text

chunk_size = 2048
chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
len(chunks)

embed_model_name = "cohere-embed-v3-multilingual" 

embed_client = EmbeddingsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token)
)

embed_response = embed_client.embed(
    input=chunks,
    model=embed_model_name
)



text_embeddings = []
for item in embed_response.data:
    length = len(item.embedding)
    text_embeddings.append(item.embedding)
text_embeddings = np.array(text_embeddings)


d = text_embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(text_embeddings)

question = "저자가 대학에 오기 전에 주로 했던 두 가지 일은 무엇이었나요?"

question_embedding = embed_client.embed(
    input=[question],
    model=embed_model_name
)

question_embeddings = np.array(question_embedding.data[0].embedding)


D, I = index.search(question_embeddings.reshape(1, -1), k=2) # distance, index
retrieved_chunks = [chunks[i] for i in I.tolist()[0]]

prompt = f"""
Context information is below.
---------------------
{retrieved_chunks}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {question}
Answer:
"""


chat_response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content=prompt),
    ],
    temperature=1.0,
    top_p=1.0,
    max_tokens=1000,
    model=model_name
)

print(chat_response.choices[0].message.content)
```

## Mistral Small 
Mistral Small is another model in the Mistral family of models under the premier/enterprise category. As the name implies, this model is a Small Language Model (SLM). The advantages of using Mistral Small are that it is: 
- Cost Saving compared to Mistral LLMs like Mistral Large and NeMo - 80% price drop
- Low latency - faster response compared to Mistral's LLMs
- Flexible - can be deployed across different environments with less restrictions on required resources. 


Mistral Small is great for: 
- Text based tasks such as summarization, sentiment analysis and translation. 
- Applications where frequent requests are made due to its cost effectiveness 
- Low latency code tasks like review and code suggestions 

## Comparing Mistral Small and Mistral Large 

To show differences in latency between Mistral Small and Large, run the below cells. 

You should see a difference in response times between 3-5 seconds. Also note the response lengths and style over the same prompt.  

```python 

import os 
endpoint = os.environ["AZURE_INFERENCE_ENDPOINT"]
model_name = "Mistral-small"
token = os.environ["AZURE_INFERENCE_CREDENTIAL"]

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful coding assistant."),
        UserMessage(content="Can you write a Python function to the fizz buzz test?"),
    ],
    temperature=1.0,
    top_p=1.0,
    max_tokens=1000,
    model=model_name
)

print(response.choices[0].message.content)

```

```python 

import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = os.environ["AZURE_INFERENCE_ENDPOINT"]
model_name = "Mistral-large"
token = os.environ["AZURE_INFERENCE_CREDENTIAL"]

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful coding assistant."),
        UserMessage(content="Can you write a Python function to the fizz buzz test?"),
    ],
    temperature=1.0,
    top_p=1.0,
    max_tokens=1000,
    model=model_name
)

print(response.choices[0].message.content)

```

## Mistral NeMo

Compared to the other two models discussed in this lesson, Mistral NeMo is the only free model with an Apache2 License. 

It is viewed as an upgrade to the earlier open source LLM from Mistral, Mistral 7B. 

Some other features of the NeMo model are: 

- *More efficient tokenization:* This model uses the Tekken tokenizer over the more commonly used tiktoken. This allows for better performance over more languages and code. 

- *Finetuning:* The base model is available for finetuning. This allows for more flexibility for use-cases where finetuning may be needed. 

- *Native Function Calling* - Like Mistral Large, this model has been trained on function calling. This makes it unique as being one of the first open source models to do so. 


### Comparing Tokenizers 

In this sample, we will look at how Mistral NeMo handles tokenization compared to Mistral Large. 

Both samples take the same prompt but you should see that NeMo returns fewer tokens than Mistral Large. 

```bash
pip install mistral-common
```

```python 
# Import needed packages:
from mistral_common.protocol.instruct.messages import (
    UserMessage,
)
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from mistral_common.protocol.instruct.tool_calls import (
    Function,
    Tool,
)
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer

# Load Mistral tokenizer

model_name = "open-mistral-nemo"

tokenizer = MistralTokenizer.from_model(model_name)

# Tokenize a list of messages
tokenized = tokenizer.encode_chat_completion(
    ChatCompletionRequest(
        tools=[
            Tool(
                function=Function(
                    name="get_current_weather",
                    description="Get the current weather",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit to use. Infer this from the user's location.",
                            },
                        },
                        "required": ["location", "format"],
                    },
                )
            )
        ],
        messages=[
            UserMessage(content="What's the weather like today in Paris"),
        ],
        model=model_name,
    )
)
tokens, text = tokenized.tokens, tokenized.text

# Count the number of tokens
print(len(tokens))
```

```python
# Import needed packages:
from mistral_common.protocol.instruct.messages import (
    UserMessage,
)
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from mistral_common.protocol.instruct.tool_calls import (
    Function,
    Tool,
)
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer

# Load Mistral tokenizer

model_name = "mistral-large-latest"

tokenizer = MistralTokenizer.from_model(model_name)

# Tokenize a list of messages
tokenized = tokenizer.encode_chat_completion(
    ChatCompletionRequest(
        tools=[
            Tool(
                function=Function(
                    name="get_current_weather",
                    description="Get the current weather",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit to use. Infer this from the user's location.",
                            },
                        },
                        "required": ["location", "format"],
                    },
                )
            )
        ],
        messages=[
            UserMessage(content="What's the weather like today in Paris"),
        ],
        model=model_name,
    )
)
tokens, text = tokenized.tokens, tokenized.text

# Count the number of tokens
print(len(tokens))
```

---

## Applied lab r40-t055 — lexical retriever behind a callable interface

The RAG example above puts a real embedding model (Cohere Embed v4) and a
real vector index (faiss) behind `client.embeddings.create` and
`index.search`. This lab adds a small local simulation of that same shape:
a tiny retriever over three local documents, with the external dependency
put behind a plain callable interface and a deterministic local adapter
supplied for it.

> **Lexical test double / simulation behaviour:** `LocalLexicalRetriever`
> scores query/document overlap on lowercase word **sets**. It is a
> **lexical test double**, not a production vector search: it performs
> **no** embedding, **no** faiss/ANN index, **no** model download, **no**
> remote API call, **no** GPU and **no** network access.

### Exact invocation

```bash
# Inside the repository root
python3 20-mistral/applied-labs/r40-t055/example.py

# Test suite, in a fresh process
python3 -m unittest discover -s 20-mistral/applied-labs/r40-t055 -p "test_*.py"
```

### Fixture (synthetic teaching corpus)

| doc_id | text |
|---|---|
| A | `"red apple"` |
| B | `"green apple"` |
| C | `"blue sky"` |

### Expected output (exact)

```text
[LESSON: query normalization] corpus=[('A', 'red apple'), ('B', 'green apple'), ('C', 'blue sky')]
  retriever=LocalLexicalRetriever (lexical test double, NOT a production vector search)
[LESSON: retrieval ranking] query='red apple' -> [('A', 2), ('B', 1)]
[LESSON: empty results] query='ocean' -> [] (no match)
[LESSON: citations] every result names its source doc_id, e.g. 'A'
[LESSON: unestablished real-service behavior] this mock does not establish:
  - semantic/embedding similarity beyond exact lowercase word overlap
  - stemming, lemmatization, or synonym matching (e.g. 'ocean' vs 'sea')
  - ranking quality, relevance feedback, or any learned re-ranking
  - network latency, rate limits, or failure modes of a real embedding/search API
  - scaling behavior over large corpora, or approximate nearest-neighbor search
```

Query `"red apple"` ranks **A** (score 2, both words match) before **B**
(score 1, only "apple" matches); **C** has zero overlap and is dropped
entirely. Query `"ocean"` matches nothing, so it returns `[]` rather than a
fabricated low-score hit.

### The focus: the callable interface and its deterministic adapter

```python
class Retriever(Protocol):
    def __call__(self, query: str) -> list[RetrievalResult]: ...

def run_retrieval(retriever: Retriever, query: str) -> list[RetrievalResult]:
    return retriever(query)
```

`run_retrieval` depends only on the `Retriever` callable interface -- it
never references `LocalLexicalRetriever` by name. `LocalLexicalRetriever`
is the deterministic local adapter supplied behind that interface for this
lab; in production the same interface could be implemented by a client
that embeds the query and searches a real vector index, exactly as the RAG
example above does, without `run_retrieval` changing at all.

### What this mock does not establish

Listed explicitly in `UNESTABLISHED_REAL_SERVICE_BEHAVIORS` and asserted
non-empty by the tests: semantic/embedding similarity, stemming or synonym
matching, learned ranking/relevance feedback, the latency/availability/
cost behaviour of a real embedding or vector-search API, and scaling to
large corpora or approximate nearest-neighbor search. This lab makes no
claim about any of those.

### Boundary and failure scenarios

| scenario | input | expected |
|---|---|---|
| normal | query `"red apple"` | `[A(2), B(1)]`, C excluded |
| tie-break | query `"apple"` | `[A(1), B(1)]` -- tie broken by ascending `doc_id` |
| normalization | query `"APPLE RED"` | same ranking as `"red apple"` (case/order-insensitive) |
| empty query | query `""` | `[]` |
| no match | query `"ocean"` | `[]` |
| non-string query | `None` | `TypeError` |
| duplicate document IDs | corpus with two `"A"` entries | `ValueError` at construction |

These are fully covered by
[`test_r40_t055.py`](20-mistral/applied-labs/r40-t055/test_r40_t055.py);
the regression check lives in
[`check_r40_t055.py`](20-mistral/applied-labs/r40-t055/check_r40_t055.py).

### Lesson-concept mapping: public inputs / outputs

| public input / output | lesson concept it illustrates |
|---|---|
| `_normalize(text)` | query normalization before matching, as both sides of the RAG example's `index.search` call need a comparable representation |
| `LocalLexicalRetriever.__call__` / `RetrievalResult.score` | retrieval ranking, standing in for `index.search(...)` |
| an unmatched query returning `[]` | empty results -- no fabricated match when nothing is relevant |
| `RetrievalResult.doc_id` | citations -- every result is traceable to a source document, as `retrieved_chunks` are in the RAG example |

### Where the simplification stops

This fixture models retrieval *bookkeeping* only: word-set intersection,
a sort, and a tie-break. It does not call any embedding model, does not
build or query a vector index, does not measure semantic similarity, and
makes no claim about real hardware, cloud-service behaviour, or
trained-model performance. It demonstrates the *shape* of a
query-in/ranked-results-out retrieval interface, not the Cohere Embed +
faiss pipeline used in this lesson's RAG example.

## Learning does not stop here, continue the journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!
