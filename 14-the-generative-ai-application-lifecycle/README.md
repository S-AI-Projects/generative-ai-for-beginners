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

## Applied Lab: R40-T043 — Server Launch Configuration Validation & Secret Redaction

> [!NOTE]
> **[SIMULATION / MOCK]** This lab operates locally on an in-memory configuration validator. No subprocesses are spawned, and no network ports are bound (`process_launched=False`). No cloud providers, models, or GPUs are required.

This applied lab extends Lesson 14 by illustrating preflight deployment validation in the LLMOps operationalization lifecycle. When configuring local model servers (e.g., Uvicorn, vLLM, or Ollama), startup commands and environment configurations must be strictly validated and sanitized before deployment.

### Core Contract & Boundary Rules

1. **Required Command**: Missing, `None`, or empty command strings fail with `ValueError`.
2. **Explicit Argument Array**: Passing a single string (e.g. `"--port 8000"`) where an array/list of arguments is expected fails with `TypeError` to enforce safe process boundaries and prevent shell injection.
3. **Secret Redaction**: Environment variable keys are recorded in the summary, but all values are replaced with `[REDACTED]`.
4. **No Process Launch**: Validating a configuration produces a `LaunchSummary` record without spawning any OS process.

### Focus: Comparison with Independent Reference Oracle Table

The direct implementation (`validate_launch_config`) is formally compared against an independent reference oracle calculation (`reference_oracle_table`) using identical test fixtures:

| Fixture | Input Command | Arguments | Configured Env Keys | Redaction Verified | Oracle Equivalence |
|---|---|---|---|---|---|
| **Inference Server** | `"uvicorn"` | `["main:app", "--port", "8000"]` | `{"KEY": "secret"}` | Values -> `[REDACTED]` | Verified ✓ |
| **Model Service** | `"vllm"` | `["serve", "--model", "phi-4"]` | `{"SECRET_A": "1", "SECRET_B": "2"}` | Values -> `[REDACTED]` | Verified ✓ |
| **Empty Bounds** | `"ollama"` | `[]` | `{}` | No keys exposed | Verified ✓ |

### Invocation and Test Suite

Execute the test suite using standard library `unittest`:

```bash
# Run from repository root
python3 -m unittest discover -s 14-the-generative-ai-application-lifecycle/applied-labs/r40-t043 -p "test_*.py" -v
```

Expected output (**9 tests**, exit code 0):

```
test_valid_record_produces_redacted_summary (test_example.TestLaunchConfigContract.test_valid_record_produces_redacted_summary) ... ok
test_missing_command_fails (test_example.TestLaunchConfigContract.test_missing_command_fails) ... ok
test_single_string_where_array_required_fails (test_example.TestLaunchConfigContract.test_single_string_where_array_required_fails) ... ok
test_comparison_with_independent_oracle (test_example.TestIndependentOracleComparison.test_comparison_with_independent_oracle) ... ok
...
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
```

> [!IMPORTANT]
> The checker exits non-zero if assertions fail. Deliberate failure tests (`test_deliberate_wrong_command_fails` and `test_deliberate_wrong_redaction_fails`) verify that any modified expected results or leaked secrets immediately raise an `AssertionError`.

### Simplification Boundary

This local validator isolates startup configuration preflight checks:
- It does **not** launch or monitor real operating system daemons.
- It does **not** communicate with remote Kubernetes, Docker, or Azure ML clusters.
- It makes no claims regarding actual server latency or inference performance.

---

## Great! Continue your Learning!

Amazing, now learn more about how we structure an application to use the concepts with the [Contoso Chat App](https://nitya.github.io/contoso-chat/?WT.mc_id=academic-105485-koreyst), to check how Cloud Advocacy adds those concepts in demonstrations. For more content, check our [Ignite breakout session!
](https://www.youtube.com/watch?v=DdOylyrTOWg)

Now, check Lesson 15, to understand how [Retrieval Augmented Generation and Vector Databases](../15-rag-and-vector-databases/README.md?WT.mc_id=academic-105485-koreyst) impact Generative AI and to make more engaging Applications!
