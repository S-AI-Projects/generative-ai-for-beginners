# Building With the Meta Family Models 

## Introduction 

This lesson will cover: 

- Exploring the two main Meta family models - Llama 3.1 and Llama 3.2, plus the currently available alternatives used in the code samples (Llama 3.3 and Llama 4) 
- Understanding the use-cases and scenarios for each model 
- Code sample to show the unique features of each model 
- Selecting eligible models from a local synthetic manifest using explicit RAM and context constraints


## The Meta Family of Models 

In this lesson, we will explore 2 models from the Meta family or "Llama Herd" - Llama 3.1 and Llama 3.2. The runnable code examples use Llama 3.3 and Llama 4, which are currently available alternatives in the Microsoft Foundry Models catalog.

These models come in different variants and are available in the [Microsoft Foundry Models catalog](https://ai.azure.com/catalog/models?WT.mc_id=academic-105485-koreyst).

> **Note:** GitHub Models is retiring at the end of July 2026. Here are more details on using [Microsoft Foundry Models](https://learn.microsoft.com/azure/ai-foundry/model-inference/overview?WT.mc_id=academic-105485-koreyst) to prototype with AI models.

> **Note:** The specific model versions this lesson was originally written against (Llama 3.1 70B/405B Instruct, Llama 3.2 11B/90B Vision Instruct) have since been retired from the Microsoft Foundry Models catalog. The code examples below use `Llama-3.3-70B-Instruct` and `Llama-4-Scout-17B-16E-Instruct` as currently available alternatives in the Microsoft Foundry Models catalog, so they still run today.

Model Variants (as originally covered in this lesson): 
- Llama 3.1 - 70B Instruct (retired) 
- Llama 3.1 - 405B Instruct (retired) 
- Llama 3.2 - 11B Vision Instruct (retired) 
- Llama 3.2 - 90B Vision Instruct (retired) 

Currently available alternatives used in the code examples: 
- Llama 3.3 - 70B Instruct (`Llama-3.3-70B-Instruct`) 
- Llama 4 Scout - 17B 16E Instruct (`Llama-4-Scout-17B-16E-Instruct`) 

*Note: The Llama 3 variants discussed above are retained for historical context and are no longer available in Microsoft Foundry Models.*

## Llama 3.1 

At 405 Billion Parameters, Llama 3.1 fits into the open source LLM category. 

The model is an upgrade to the earlier release Llama 3 by offering: 

- Larger context window - 128k tokens vs 8k tokens 
- Larger Max Output Tokens - 4096 vs 2048 
- Better Multilingual Support - due to increase in training tokens 

These enable Llama 3.1 to handle more complex use cases when building GenAI applications including: 
- Native Function Calling - the ability to call external tools and functions outside of the LLM workflow
- Better RAG Performance - due to the higher context window 
- Synthetic Data Generation - the ability to create effective data for tasks such as fine-tuning 

### Native Function Calling 

Llama 3.1 has been fine-tuned to be more effective at making function or tool calls. It also has two built-in tools that the model can identify as needing to be used based on the prompt from the user. These tools are: 

- **Brave Search** - Can be used to get up-to-date information like the weather by performing a web search 
- **Wolfram Alpha** - Can be used for more complex mathematical calculations so writing your own functions is not required. 

You can also create your own custom tools that the LLM can call. 

In the code example below: 

- We define the available tools (brave_search, wolfram_alpha) in the system prompt. 
- Send a user prompt that asks about the weather in a certain city. 
- The LLM will respond with a tool call to the Brave Search tool which will look like this `<|python_tag|>brave_search.call(query="Stockholm weather")` 

*Note: This example only makes the tool call, if you would like to get the results, you will need to create a free account on the Brave API page and define the function itself.

```python 
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Get these from your Microsoft Foundry project's "Overview" page
token = os.environ["AZURE_INFERENCE_CREDENTIAL"]
endpoint = os.environ["AZURE_INFERENCE_ENDPOINT"]
# Meta-Llama-3.1-405B-Instruct was retired from Microsoft Foundry on 2026-06-13 with no replacement listed;
# using Llama-3.3-70B-Instruct, a currently available alternative, instead
model_name = "Llama-3.3-70B-Instruct"

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)


tool_prompt=f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search, wolfram_alpha
Cutting Knowledge Date: December 2023
Today Date: 23 July 2024

You are a helpful assistant<|eot_id|>
"""

messages = [
    SystemMessage(content=tool_prompt),
    UserMessage(content="What is the weather in Stockholm?"),

]

response = client.complete(messages=messages, model=model_name)

print(response.choices[0].message.content)
```

## Llama 3.2 

Despite being an LLM, one limitation of Llama 3.1 is its lack of multimodality. That is, the inability to use different types of input such as images as prompts and provide responses. This ability is one of the main features of Llama 3.2. These features also include: 

- Multimodality -  has the ability to evaluate both text and image prompts 
- Small to Medium size variations (11B and 90B) - this provides flexible deployment options, 
- Text-only variations (1B and 3B) - this allows the model to be deployed on edge / mobile devices and provides low latency 

The multimodal support represents a big step in the world of open source models. The code example below takes both an image and text prompt to get an analysis of the image. Because Llama 3.2 90B Vision Instruct has been retired, the example uses `Llama-4-Scout-17B-16E-Instruct`, a currently available natively multimodal alternative. 


### Multimodal Support with Llama 3.2

```python 
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl,
    ImageDetailLevel,
)
from azure.core.credentials import AzureKeyCredential

# Get these from your Microsoft Foundry project's "Overview" page
token = os.environ["AZURE_INFERENCE_CREDENTIAL"]
endpoint = os.environ["AZURE_INFERENCE_ENDPOINT"]
# Llama-3.2-90B-Vision-Instruct was retired from Microsoft Foundry on 2026-06-13 with no replacement listed;
# using Llama-4-Scout-17B-16E-Instruct, a currently available natively multimodal alternative, instead
model_name = "Llama-4-Scout-17B-16E-Instruct"

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage(
            content="You are a helpful assistant that describes images in details."
        ),
        UserMessage(
            content=[
                TextContentItem(text="What's in this image?"),
                ImageContentItem(
                    image_url=ImageUrl.load(
                        image_file="sample.jpg",
                        image_format="jpg",
                        detail=ImageDetailLevel.LOW)
                ),
            ],
        ),
    ],
    model=model_name,
)

print(response.choices[0].message.content)
```

## Local Model Selection Simulation (Applied Lab)

> **Simulation / Synthetic Fixture Notice:** The runnable lab at [example.py](./applied-labs/r40-t051/example.py?WT.mc_id=academic-105485-koreyst) (with tests in [test_example.py](./applied-labs/r40-t051/test_example.py?WT.mc_id=academic-105485-koreyst)) is a **local synthetic simulation** using invented teaching fixtures (`Fixture A` and `Fixture B`). Its numbers are teaching placeholders—not claims about the named real Meta Llama models, physical hardware requirements, cloud service behavior, or trained-model performance. Its simplifications stop at static integer thresholds and do not model KV-cache growth, quantization, GPU VRAM vs. system RAM split, multimodal inputs, or live Microsoft Foundry API calls.

**Prerequisite tools:** Python 3.9+ (standard library only; no model download, API key, paid provider, GPU, or physical device required).

### Synthetic Teaching Fixture

- `Fixture A`: `min_ram_gb = 4`, `max_context_tokens = 2048`
- `Fixture B`: `min_ram_gb = 8`, `max_context_tokens = 4096`
- Simulated request: `ram_budget_gb = 6`, `requested_context_tokens = 1024` (admits only `Fixture A`)

### Public Inputs and Outputs Mapped to Lesson Concepts

| Public Symbol / Field | Role in `select_eligible_models` | Lesson Concept Connection |
| --- | --- | --- |
| `manifest` (`name`, `min_ram_gb`, `max_context_tokens`) | List of synthetic model entries evaluated locally | Represents candidate Meta-family variants across different sizes and context limits (e.g., compact edge-oriented variants vs. larger variants) |
| `ram_budget_gb` | Simulated device RAM limit (`6` GB by default) | Mirrors host/edge memory constraints that decide whether smaller variants can run locally while larger ones cannot |
| `requested_context_tokens` | Simulated prompt/context length (`1024` by default) | Mirrors prompt and RAG/tool-calling context-window needs emphasized in the Llama 3.1 context upgrade |
| `simulation` | Boolean flag (`true`) in the output payload | Marks the output as a deterministic local simulation rather than a live model or device probe |
| `eligible` | Entries where `min_ram_gb <= ram_budget_gb` and `max_context_tokens >= requested_context_tokens` | Candidate entries that fit both the device memory budget and prompt context requirement |
| `excluded` (with `reasons`) | Rejected entries paired with explicit per-constraint failure strings | Explains the exact trade-off (insufficient RAM, insufficient context window, or both) for each excluded entry |

### Exact Invocation and Expected Output

Run the local simulation from the repository root:

```bash
python3 21-meta/applied-labs/r40-t051/example.py
```

Expected output:

```json
{
  "simulation": true,
  "ram_budget_gb": 6,
  "requested_context_tokens": 1024,
  "eligible": [
    {
      "name": "Fixture A",
      "min_ram_gb": 4,
      "max_context_tokens": 2048
    }
  ],
  "excluded": [
    {
      "name": "Fixture B",
      "min_ram_gb": 8,
      "max_context_tokens": 4096,
      "reasons": [
        "min_ram_gb 8 exceeds ram_budget_gb 6"
      ]
    }
  ]
}
```

Run the unit tests:

```bash
python3 -m unittest discover -s 21-meta/applied-labs/r40-t051 -p "test_*.py"
```

## Learning does not stop here, continue the journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!

