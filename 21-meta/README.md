# Building With the Meta Family Models 

## Introduction 

This lesson will cover: 

- Exploring the two main Meta family models - Llama 3.1 and Llama 3.2, plus the currently available alternatives used in the code samples (Llama 3.3 and Llama 4) 
- Understanding the use-cases and scenarios for each model 
- Code sample to show the unique features of each model 


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

### Applied Lab: Model Manifest Selection & Resource Constraint Evaluation (R40-T029)

To explore host memory constraints, context window requirements, and deterministic candidate filtering across the Meta family model ecosystem, see the self-contained local lab:
[Applied Lab — Model Manifest Selection & Resource Constraint Evaluation (R40-T029)](./applied-labs/r40-t029/README.md?WT.mc_id=academic-105485-koreyst).

**Classification & Scope Note (Simulation / Test Double):** This component is strictly a **deterministic local constraint-satisfaction engine and test double**, not an inference server. It executes entirely locally using Python's standard library. It requires zero cloud credentials, no paid API keys, no weights download, and no GPU hardware.

#### Fixture and Selection Contract
The local test fixtures model:
- **Canonical Model Manifest**:
  - `model-a` (Fixture A): Needs RAM `4.0` GB, supports context `2048` tokens.
  - `model-b` (Fixture B): Needs RAM `8.0` GB, supports context `4096` tokens.
- **Resource Constraints**:
  - Host RAM Invariant: min_ram_gb <= budget_ram_gb.
  - Context Invariant: max_context_tokens >= requested_context_tokens.
- **Canonical Workload Outcome**:
  - Given budget RAM `6.0` GB and requested context `1024` tokens, the selector admits **ONLY Fixture A**.
  - Fixture B is excluded with the diagnostic explanation: `RAM requirement (8.0 GB) exceeds host budget (6.0 GB) by 2.0 GB` (`RAM_EXCEEDS_BUDGET`).
- **Controlled Configurations Comparison (Evaluation Experiment)**:
  - Compares three host configurations (Edge Constrained: 6 GB RAM / 1024 Context; Long-Context Cloud: 8 GB RAM / 4096 Context; Generous Workstation: 16 GB RAM / 1024 Context) using admission rates, memory slack, context headroom, and bottleneck analysis without claiming real-world model accuracy.

#### Exact Invocations and Expected Output

Run the decision table check across all canonical scenarios:

```bash
python3 21-meta/applied-labs/r40-t029/example.py --check
```

Expected output (`exit 0`):

```json
{
  "classification": "model_manifest_selection_canonical_check",
  "status": "success",
  "total_scenarios": 4,
  "passed_scenarios": 4,
  "failed_scenarios": 0,
  "all_passed": true,
  "scenarios": [
    {
      "scenario_id": "SCENARIO_NORMAL",
      "scenario_type": "normal",
      "expected_admitted": [
        "model-a"
      ],
      "actual_admitted": [
        "model-a"
      ],
      "expected_decision": "SELECTIVE_ADMISSION_SUCCESS",
      "actual_decision": "SELECTIVE_ADMISSION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Admitted 1 of 2 candidates (model-a). Excluded 1 candidates (model-b) due to resource deficits."
    },
    {
      "scenario_id": "SCENARIO_BOUNDARY",
      "scenario_type": "boundary",
      "expected_decision": "BOUNDARY_VERIFICATION_SUCCESS",
      "actual_decision": "BOUNDARY_VERIFICATION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Exact equality at boundary admits Fixture A; step-off deficit (3.9 GB) excludes it."
    },
    {
      "scenario_id": "SCENARIO_FAILURE",
      "scenario_type": "failure_validation",
      "expected_decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
      "actual_decision": "INPUT_VALIDATION_HANDLED_CLEANLY",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Invalid negative RAM, zero context, and duplicate IDs were handled with explicit exceptions."
    },
    {
      "scenario_id": "SCENARIO_EXPERIMENT",
      "scenario_type": "evaluation_experiment",
      "expected_decision": "EXPERIMENT_EVALUATION_SUCCESS",
      "actual_decision": "EXPERIMENT_EVALUATION_SUCCESS",
      "status": "PASS",
      "matches_table": true,
      "rationale": "Evaluated 3 controlled configurations reporting admission rates, resource slack, and trade-offs."
    }
  ]
}
```

Run the automated test suite:

```bash
python3 -m unittest discover -s 21-meta/applied-labs/r40-t029 -p "test_*.py" -v
```

## Learning does not stop here, continue the journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!

