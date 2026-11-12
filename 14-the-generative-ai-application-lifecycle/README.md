[![Integrating with function calling](./images/14-lesson-banner.png?WT.mc_id=academic-105485-koreyst)](https://youtu.be/ewtQY_RJrzs?si=dyJ2bjiljH7UUHCh)

# The Generative AI Application Lifecycle

An important question for all AI applications is the relevance of AI features, as AI is a fast evolving field, to ensure that your application remains relevant, reliable, and robust, you need to monitor, evaluate, and improve it continuously. This is where the generative AI lifecycle comes in.

The generative AI lifecycle is a framework that guides you through the stages of developing, deploying, and maintaining a generative AI application. It helps you to define your goals, measure your performance, identify your challenges, and implement your solutions. It also helps you to align your application with the ethical and legal standards of your domain and your stakeholders. By following the generative AI lifecycle, you can ensure that your application is always delivering value and satisfying your users.

## Introduction

In this chapter, you will:

- Understand the Paradigm Shift from MLOps to LLMOps
- The LLM Lifecycle
- Lifecycle Tooling
- Lifecycle Metrification and Evaluation
- Preflight Launch Configuration Validation and Secret Redaction

## Understand the Paradigm Shift from MLOps to LLMOps

LLMs are a new tool in the Artificial Intelligence arsenal, they are incredibly powerful in analysis and generation tasks for applications, however this power has some consequences in how we streamline AI and Classic Machine Learning tasks.

With this, we need a new Paradigm to adapt this tool in a dynamic, with the correct incentives. We can categorize older AI apps as "ML Apps" and newer AI Apps as "GenAI Apps" or just "AI Apps", reflecting the mainstream technology and techniques used at the time. This shifts our narrative in multiple ways, look at the following comparison.

![LLMOps vs. MLOps comparison](./images/01-llmops-shift.png?WT.mc_id=academic-105485-koreyst)

Notice that in LLMOps, we are more focused on the App Developers, using integrations as a key point, using "Models-as-a-Service" and thinking in the following points for metrics.

- Quality: Response quality
- Harm: Responsible AI
- Honesty: Response groundedness (Makes sense? It is correct?)
- Cost: Solution Budget
- Latency: Avg. time for token response

## The LLM Lifecycle

First, to understand the lifecycle and the modifications, let's note the next infographic.

![LLMOps infographic](./images/02-llmops.png?WT.mc_id=academic-105485-koreyst)

As you may note, this is different from the usual Lifecycles from MLOps. LLMs have many new requirements, as Prompting, different techniques to improve quality (Fine-Tuning, RAG, Meta-Prompts), different assessment and responsibility with responsible AI, lastly, new evaluation metrics (Quality, Harm, Honesty, Cost and Latency).

For instance, take a look at how we ideate. Using prompt engineering to experiment with various LLMs to explore possibilities to test if their Hypothesis could be correct.

Note that this is not linear, but integrated loops, iterative and with an overarching cycle.

How could we explore those steps? Let's step into detail in how could we build a lifecycle.

![LLMOps Workflow](./images/03-llm-stage-flows.png?WT.mc_id=academic-105485-koreyst)

This may look a bit complicated, lets focus on the three big steps first.

1. Ideating/Exploring: Exploration, here we can explore according to our business needs. Prototyping, creating a [PromptFlow](https://microsoft.github.io/promptflow/index.html?WT.mc_id=academic-105485-koreyst) and test if is efficient enough for our Hypothesis.
1. Building/Augmenting: Implementation, now, we start to evaluate for bigger datasets implement techniques, like Fine-tuning and RAG, to check the robustness of our solution. If it does not, re-implementing it, adding new steps in our flow or restructuring the data, might help. After testing our flow and our scale, if it works and check our Metrics, it is ready for the next step.
1. Operationalizing: Integration, now adding Monitoring and Alerts Systems to our system, deployment and application integration to our Application.

Then, we have the overarching cycle of Management, focusing on security, compliance and governance.

Congratulations, now you have your AI App ready to go and operational. For a hands on experience, take a look on the [Contoso Chat Demo.](https://nitya.github.io/contoso-chat/?WT.mc_id=academic-105485-koreyst)

Now, what tools could we use?

## Lifecycle Tooling

For Tooling, Microsoft provides the [Azure AI Platform](https://azure.microsoft.com/solutions/ai/?WT.mc_id=academic-105485-koreyst) and [PromptFlow](https://microsoft.github.io/promptflow/index.html?WT.mc_id=academic-105485-koreyst) facilitate and make your cycle easy to implement and ready to go.

The [Azure AI Platform](https://azure.microsoft.com/solutions/ai/?WT.mc_id=academic-105485-koreyst), allows you to use [Microsoft Foundry](https://ai.azure.com/?WT.mc_id=academic-105485-koreyst). Microsoft Foundry (formerly Azure AI Studio) is a web portal that lets you explore models, samples and tools, manage your resources, and use UI development flows as well as SDK/CLI options for Code-First development.

![Azure AI possibilities](./images/04-azure-ai-platform.png?WT.mc_id=academic-105485-koreyst)

Azure AI, allows you to use multiple resources, to manage your operations, services, projects, vector search and databases needs.

![LLMOps with Azure AI](./images/05-llm-azure-ai-prompt.png?WT.mc_id=academic-105485-koreyst)

Construct, from Proof-of-Concept(POC) until large scale applications with PromptFlow:

- Design and Build apps from VS Code, with visual and functional tools
- Test and fine-tune your apps for quality AI, with ease.
- Use Microsoft Foundry to Integrate and Iterate with cloud, Push and Deploy for quick integration.

![LLMOps with PromptFlow](./images/06-llm-promptflow.png?WT.mc_id=academic-105485-koreyst)

## Local Launch Configuration & Redaction Simulation (Applied Lab)

> **Simulation / Synthetic Fixture Notice:** The runnable lab at [example.py](./applied-labs/r40-t056/example.py?WT.mc_id=academic-105485-koreyst) (with tests in [test_example.py](./applied-labs/r40-t056/test_example.py?WT.mc_id=academic-105485-koreyst)) is a **local in-memory preflight simulation** (`"simulation": true`, `"launched": false`). It **never launches a process** and makes no claims about real hardware, cloud service behavior, or trained-model performance. Its simplifications stop at static schema validation and redaction over synthetic fixtures and do not check binary `PATH` availability, OS permissions, open network ports, PromptFlow/Microsoft Foundry endpoints, or secret-vault integration.

**Prerequisite tools:** Python 3.9+ (standard library only; no model download, API key, paid provider, GPU, or physical device required).

### Baseline vs. Extracted Responsibility & Fixture Contract

- **Baseline (`validate_launch_config_baseline`):** Validates `command`, argument-array `args`, and `env` keys/values in one function and returns a redacted report (`"launched": false`, values replaced by `"<REDACTED>"`).
- **Extracted responsibility (`redact_env_values`):** Isolates explicit `env` key/value validation and redaction into a named helper called by `validate_launch_config`, preserving the exact output and `ValueError` contract across every fixture case:
  - `valid`: `command="python3"`, `args=["-m", "http.server", "8080"]`, `env={"APP_ENV": "local-sim", "API_KEY": "synthetic-secret-value"}` -> returns redacted report with `"launched": false`.
  - `boundary_empty_args_and_env`: `command="uvicorn"`, `args=[]`, `env={}` -> valid boundary case.
  - `invalid_missing_command`: missing `command` -> fails with `ValueError("Missing or empty 'command'")`.
  - `invalid_string_args`: `args="--port 8080"` (single string instead of array) -> fails with `ValueError`.

### Exact Invocation and Expected Output

Run the valid fixture case from the repository root:

```bash
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/example.py --case valid
```

Expected output:

```json
{
  "simulation": true,
  "case": "valid",
  "equivalent": true,
  "report": {
    "simulation": true,
    "launched": false,
    "command": "python3",
    "args": [
      "-m",
      "http.server",
      "8080"
    ],
    "env_keys": [
      "APP_ENV",
      "API_KEY"
    ],
    "redacted_env": {
      "APP_ENV": "<REDACTED>",
      "API_KEY": "<REDACTED>"
    }
  }
}
```

Run the full before/after equivalence suite across all 4 fixtures and the unit tests:

```bash
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056/example.py
python3 -m unittest discover -s 14-the-generative-ai-application-lifecycle/applied-labs/r40-t056 -p "test_*.py"
```

## Great! Continue your Learning!

Amazing, now learn more about how we structure an application to use the concepts with the [Contoso Chat App](https://nitya.github.io/contoso-chat/?WT.mc_id=academic-105485-koreyst), to check how Cloud Advocacy adds those concepts in demonstrations. For more content, check our [Ignite breakout session!
](https://www.youtube.com/watch?v=DdOylyrTOWg)

Now, check Lesson 15, to understand how [Retrieval Augmented Generation and Vector Databases](../15-rag-and-vector-databases/README.md?WT.mc_id=academic-105485-koreyst) impact Generative AI and to make more engaging Applications!
