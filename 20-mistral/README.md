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

### Applied Lab: Lexical Retriever with Source Attribution and Equivalence Refactoring (R40-T026)

To understand how retrieval systems normalize queries, assign document-level source attribution, deterministically resolve ranking ties, and handle empty search boundaries before generating prompts, explore the local hands-on lab:
[Applied Lab — Lexical Retriever with Source Attribution and Equivalence Refactoring](./applied-labs/r40-t026/README.md?WT.mc_id=academic-105485-koreyst).

**Classification & Scope Note (Lexical Test Double):** This component is strictly a **lexical test double**, not a production vector search. It executes entirely locally with Python's standard library using exact lowercase word-set overlap. It requires no vector embeddings, no vector database (FAISS/Chroma), no API keys, and no GPU hardware.

#### Fixture and Retrieval Contract
The local test fixture consists of three documents:
- Document A: `"red apple"`
- Document B: `"green apple"`
- Document C: `"blue sky"`

Retrieval contract rules:
1. Normal query `"red apple"` matches Doc A (score 2) and Doc B (score 1), ranking A before B with source attribution; Doc C (0 overlap) is omitted.
2. Boundary query `"ocean"` returns no match (`[]`), preventing hallucinated context.
3. Tie-breaking query `"apple"` matches Doc A (score 1) and Doc B (score 1), deterministically ranking A before B by document ID.
4. Refactoring focus: A monolithic `BaselineLexicalRetriever` is refactored by extracting `WordSetOverlapScorer`, with mathematical equivalence proven across all test queries.

#### Exact Invocations and Expected Output

Run the decision table check across all canonical scenarios:

```bash
python3 20-mistral/applied-labs/r40-t026/example.py --check
```

Expected output (`exit 0`):

```json
{
  "status": "success",
  "total_scenarios": 4,
  "passed_scenarios": 4,
  "failed_scenarios": 0,
  "all_passed": true,
  "classification": "lexical_test_double",
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_decision": "RETRIEVAL_SUCCESS_RANKED",
      "actual_decision": "RETRIEVAL_SUCCESS_RANKED",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        2,
        1
      ],
      "rationale": "Query 'red apple' overlaps Doc A on {'red', 'apple'} (score 2) and Doc B on {'apple'} (score 1). Ranks A before B with source attribution; Doc C ('blue sky') has 0 overlap and is omitted."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "expected_decision": "EMPTY_RESULT_NO_MATCH",
      "actual_decision": "EMPTY_RESULT_NO_MATCH",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [],
      "scores": [],
      "rationale": "Query 'ocean' has zero word overlap with any document in the corpus. The retriever cleanly returns an empty match set [], avoiding hallucination or irrelevant prompt context."
    },
    {
      "scenario_id": "SCENARIO_TIEBREAK",
      "scenario_type": "boundary",
      "expected_decision": "RETRIEVAL_TIEBREAK_RESOLVED",
      "actual_decision": "RETRIEVAL_TIEBREAK_RESOLVED",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": [
        "A",
        "B"
      ],
      "scores": [
        1,
        1
      ],
      "rationale": "Query 'apple' matches Doc A and Doc B with identical score 1. The tie-breaking rule deterministically ranks Doc A before Doc B using document ID order ('A' < 'B')."
    },
    {
      "scenario_id": "SCENARIO_EQUIVALENCE",
      "scenario_type": "equivalence",
      "expected_decision": "REFACTORING_EQUIVALENCE_PROVEN",
      "actual_decision": "REFACTORING_EQUIVALENCE_PROVEN",
      "matches_table": true,
      "status": "PASS",
      "doc_ids": null,
      "scores": null,
      "rationale": "BaselineLexicalRetriever and RefactoredLexicalRetriever (with extracted WordSetOverlapScorer) produce 100% identical ranked results, document IDs, and scores across all fixture queries."
    }
  ]
}
```

Run the automated test suite:

```bash
python3 -m unittest discover -s 20-mistral/applied-labs/r40-t026 -p "test_*.py"
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

## Learning does not stop here, continue the journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!
