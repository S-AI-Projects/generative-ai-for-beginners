[![Open Source Models](./images/17-lesson-banner.png?WT.mc_id=academic-105485-koreyst)](https://youtu.be/yAXVW-lUINc?si=bOtW9nL6jc3XJgOM)

## Introduction

AI Agents represent an exciting development in Generative AI, enabling Large Language Models (LLMs) to evolve from assistants into agents capable of taking actions. AI Agent frameworks enable developers to create applications that give LLMs access to tools and state management. These frameworks also enhance visibility, allowing users and developers to monitor the actions planned by LLMs, thereby improving experience management.

The lesson will cover the following areas:

- Understanding what an AI Agent is - What exactly is an AI Agent?
- Exploring five different AI Agent Frameworks - What makes them unique?
- Applying these AI Agents to different use cases - When should we use AI Agents?

### Applied Lab: Typed Tool Dispatch and Boundary Validation (R40-T022)

To understand how agents interact with tools, explore the local hands-on fixture:
[Applied Lab — Typed Tool Dispatch and Boundary Validation](./applied-labs/r40-t022/README.md?WT.mc_id=academic-105485-koreyst).

In AI agent frameworks, an LLM emits a structured JSON payload proposing a tool call (such as a function name and arguments). Before any underlying function or external API executes, the agent runtime must validate the request against an explicit tool allowlist and verify argument types.

This local contract fixture demonstrates defensive tool dispatch using Python's standard library:
- **Explicit Tool Allowlist:** Only `add(a, b)` and `multiply(a, b)` are permitted; unknown tools return a structured `UnknownToolError`.
- **Strict Numeric Validation:** Arguments `a` and `b` must be finite numbers (`int` or `float`). Strings (e.g., `"2"`), booleans (`True`/`False`), and non-finite floats (`NaN`, `inf`) are rejected with a structured `ValidationError`.
- **Failure Isolation:** A failed call halts the execution pipeline immediately—a failed call cannot execute another tool.
- **Contract Boundary Decision:** Booleans (`True`/`False`) subclass `int` in Python, but in JSON schemas they represent distinct primitives; thus, booleans are strictly rejected. String arguments are not coerced into numbers.
- **Scope Note (Simulation/Mock):** This is a simulated local contract fixture illustrating dispatch and validation mechanics; it is not a full Model Context Protocol (MCP) transport implementation (no JSON-RPC 2.0 framing, stdio/SSE socket transport, or network daemon) and requires no model download or cloud credentials.

#### Exact Invocations and Expected Output

1. **Successful Addition:**
   ```bash
   python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
   ```
   Expected output (`exit 0`):
   ```json
   {
     "status": "success",
     "tool": "add",
     "arguments": {
       "a": 2,
       "b": 3
     },
     "result": 5
   }
   ```

2. **Successful Multiplication:**
   ```bash
   python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'
   ```
   Expected output (`exit 0`):
   ```json
   {
     "status": "success",
     "tool": "multiply",
     "arguments": {
       "a": 2,
       "b": 3
     },
     "result": 6
   }
   ```

3. **Structured Error (Unknown Tool):**
   ```bash
   python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "divide", "arguments": {"a": 6, "b": 2}}'
   ```
   Expected output (`exit 1`):
   ```json
   {
     "status": "error",
     "error": {
       "type": "UnknownToolError",
       "code": "TOOL_NOT_ALLOWED",
       "message": "Tool 'divide' is not permitted in allowlist. Allowed tools: ['add', 'multiply']",
       "details": {
         "tool": "divide",
         "allowed_tools": [
           "add",
           "multiply"
         ]
       }
     },
     "tool": "divide",
     "arguments": {
       "a": 6,
       "b": 2
     }
   }
   ```

4. **Structured Error (String Argument `a`):**
   ```bash
   python3 17-ai-agents/applied-labs/r40-t022/example.py --call '{"tool": "add", "arguments": {"a": "2", "b": 3}}'
   ```
   Expected output (`exit 1`):
   ```json
   {
     "status": "error",
     "error": {
       "type": "ValidationError",
       "code": "INVALID_ARGUMENT_TYPE",
       "message": "Argument 'a' must be a finite number (int or float), got str: \"2\"",
       "details": {
         "parameter": "a",
         "expected": "number (int or float)",
         "received_type": "str",
         "received_value": "2"
       }
     },
     "tool": "add",
     "arguments": {
       "a": "2",
       "b": 3
     }
   }
   ```

5. **Failure Halting (A Failed Call Cannot Execute Another Tool):**
   ```bash
   python3 17-ai-agents/applied-labs/r40-t022/example.py --pipeline '[{"tool": "add", "arguments": {"a": "invalid", "b": 3}}, {"tool": "multiply", "arguments": {"a": 2, "b": 3}}]'
   ```
   Expected output (`exit 1`):
   ```json
   {
     "status": "error",
     "pipeline_halted": true,
     "failed_step_index": 0,
     "completed_steps": 0,
     "total_steps": 2,
     "executed_results": [],
     "failed_call": {
       "status": "error",
       "error": {
         "type": "ValidationError",
         "code": "INVALID_ARGUMENT_TYPE",
         "message": "Argument 'a' must be a finite number (int or float), got str: \"invalid\"",
         "details": {
           "parameter": "a",
           "expected": "number (int or float)",
           "received_type": "str",
           "received_value": "invalid"
         }
       },
       "tool": "add",
       "arguments": {
         "a": "invalid",
         "b": 3
       }
     },
     "aborted_calls": [
       {
         "tool": "multiply",
         "arguments": {
           "a": 2,
           "b": 3
         }
       }
     ],
     "message": "Pipeline halted: a failed call cannot execute another tool."
   }
   ```

Run the unit tests:
```bash
python3 -m unittest discover -s 17-ai-agents/applied-labs/r40-t022 -p "test_*.py" -v
```

## Learning goals

After taking this lesson, you'll be able to:

- Explain what AI Agents are and how they can be used.
- Have an understanding of the differences between some of the popular AI Agent Frameworks, and how they differ.
- Understand how AI Agents function in order to build applications with them.

## What Are AI Agents?

AI Agents are a very exciting field in the world of Generative AI. With this excitement comes sometimes a confusion of terms and their application. To keep things simple and inclusive of most of the tools that refer to AI Agents, we are going to use this definition:

AI Agents allow Large Language Models (LLMs) to perform tasks by giving them access to a **state** and **tools**.

![Agent Model](images/what-agent.png?WT.mc_id=academic-105485-koreyst)

Let's define these terms:

**Large Language Models** - These are the models referred throughout this course such as GPT-5, GPT-4o, and Llama 3.3, etc.

**State** - This refers to the context that the LLM is working in. The LLM uses the context of its past actions and the current context, guiding its decision-making for subsequent actions. AI Agent Frameworks allow developers to maintain this context easier.

**Tools** - To complete the task that the user has requested and that the LLM has planned out, the LLM needs access to tools. Some examples of tools can be a database, an API, an external application or even another LLM!

These definitions will hopefully give you a good grounding going forward as we look at how they are implemented. Let's explore a few different AI Agent frameworks:

## LangChain Agents

[LangChain Agents](https://python.langchain.com/docs/how_to/#agents?WT.mc_id=academic-105485-koreyst) is an implementation of the definitions we provided above.

To manage the **state** , it uses a built-in function called the `AgentExecutor`. This accepts the defined `agent` and the `tools` that are available to it.

The `Agent Executor` also stores the chat history to provide the context of the chat.

![Langchain Agents](images/langchain-agents.png?WT.mc_id=academic-105485-koreyst)

LangChain offers a [catalog of tools](https://integrations.langchain.com/tools?WT.mc_id=academic-105485-koreyst) that can be imported into your application in which the LLM can get access to. These are made by the community and by the LangChain team.

You can then define these tools and pass them to the `Agent Executor`.

Visibility is another important aspect when talking about AI Agents. It is important for application developers to understand which tool the LLM is using and why.. For that, the team at LangChain have developed LangSmith.

## AutoGen

The next AI Agent framework we will discuss is [AutoGen](https://microsoft.github.io/autogen/?WT.mc_id=academic-105485-koreyst). The main focus of AutoGen is conversations. Agents are both **conversable** and **customizable**.

**Conversable -** LLMs can start and continue a conversation with another LLM in order to complete a task. This is done by creating `AssistantAgents` and giving them a specific system message.

```python

autogen.AssistantAgent( name="Coder", llm_config=llm_config, ) pm = autogen.AssistantAgent( name="Product_manager", system_message="Creative in software product ideas.", llm_config=llm_config, )

```

**Customizable** - Agents can be defined not only as LLMs but be a user or a tool. As a developer, you can define a `UserProxyAgent` which is responsible for interacting with the user for feedback in completing a task. This feedback can either continue the execution of the task or stop it.

```python
user_proxy = UserProxyAgent(name="user_proxy")
```

### State and Tools

To change and manage state, an assistant Agent generates Python code to complete the task.

Here is an example of the process:

![AutoGen](images/autogen.png?WT.mc_id=academic-105485-koreyst)

#### LLM Defined with a System Message

```python
system_message="For weather related tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done."
```

This system messages directs this specific LLM to which functions are relevant for its task. Remember, with AutoGen you can have multiple defined AssistantAgents with different system messages.

#### Chat is Initiated by User

```python
user_proxy.initiate_chat( chatbot, message="I am planning a trip to NYC next week, can you help me pick out what to wear? ", )

```

This message from the user_proxy (Human) is what will start the process of the Agent to explore the possible functions that it should execute.

#### Function is Executed

```bash
chatbot (to user_proxy):

***** Suggested tool Call: get_weather ***** Arguments: {"location":"New York City, NY","time_periond:"7","temperature_unit":"Celsius"} ******************************************************** --------------------------------------------------------------------------------

>>>>>>>> EXECUTING FUNCTION get_weather... user_proxy (to chatbot): ***** Response from calling function "get_weather" ***** 112.22727272727272 EUR ****************************************************************

```

Once the initial chat is processed, the Agent will send the suggest tool to call. In this case, it is a function called `get_weather`. Depending on your configuration, this function can be automatically executed and read by the Agent or can be executed based on user input.

You can find a list of [AutoGen code samples](https://microsoft.github.io/autogen/docs/Examples/?WT.mc_id=academic-105485-koreyst) to further explore how to get started building.

## Microsoft Agent Framework

[Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/?WT.mc_id=academic-105485-koreyst) is Microsoft's open-source SDK for building AI Agents and multi-agent systems in both **Python** and **.NET**. It brings together the strengths of two earlier Microsoft projects — the enterprise features of **Semantic Kernel** and the multi-agent orchestration of **AutoGen** — into a single, supported framework. If you are starting a new agent project today, this is the recommended successor to AutoGen.

The framework scales from a single **chat agent** all the way up to complex **multi-agent workflows**, and it integrates directly with Microsoft Foundry, Azure OpenAI, and OpenAI. It also provides built-in observability through OpenTelemetry so you can trace exactly what your agents are doing.

### State and Tools

**State** - The framework manages conversation context for you through **threads**. An agent keeps track of the message history (user requests, tool calls, and their results), so each turn builds on the previous ones. Threads can also be persisted, allowing a conversation to be paused and resumed later.

**Tools** - You give an agent tools by passing plain Python functions. Type-annotated parameters are automatically turned into a schema, so the model knows how and when to call them (function calling). The framework also supports Model Context Protocol (MCP) servers and hosted tools such as a code interpreter.

Here is an example of a single agent with a custom tool:

```python
import asyncio
from typing import Annotated

from pydantic import Field
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    return f"The weather in {location} is sunny with a high of 22°C."


async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        instructions="You are a helpful assistant that can answer weather questions.",
        tools=[get_weather],
    )

    response = await agent.run("What's the weather in Amsterdam?")
    print(response)


asyncio.run(main())
```

To connect to Azure OpenAI in Microsoft Foundry instead, pass your endpoint and credentials to the client:

```python
from azure.identity.aio import AzureCliCredential
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(
    model="my-gpt-5-mini-deployment",
    azure_endpoint="https://my-resource.openai.azure.com",
    credential=AzureCliCredential(),
)
```

### Multi-agent workflows

Where the framework really stands out is orchestrating several agents together. For example, you can run agents one after another (each passing its context to the next) or fan out to several agents in parallel and aggregate their results:

```python
from agent_framework.orchestrations import SequentialBuilder, ConcurrentBuilder

# Run agents in sequence, passing the conversation context along the chain
sequential = SequentialBuilder(participants=[researcher, writer, editor]).build()

# Fan out to agents in parallel, then aggregate their responses
concurrent = ConcurrentBuilder(participants=[analyst_a, analyst_b, analyst_c]).build()
```

To install the framework and get started:

```bash
pip install agent-framework-core
# Optional integrations
pip install agent-framework-openai       # OpenAI and Azure OpenAI
pip install agent-framework-foundry      # Microsoft Foundry
```

You can explore more in the [Microsoft Agent Framework repository](https://github.com/microsoft/agent-framework?WT.mc_id=academic-105485-koreyst) and the [official documentation](https://learn.microsoft.com/agent-framework/?WT.mc_id=academic-105485-koreyst).

## Taskweaver

The next agent framework we will explore is [Taskweaver](https://microsoft.github.io/TaskWeaver/?WT.mc_id=academic-105485-koreyst). It is known as a "code-first" agent because instead of working strictly with `strings` , it can work with DataFrames in Python. This becomes extremely useful for data analysis and generation tasks. This can be things like creating graphs and charts or generating random numbers.

### State and Tools

To manage the state of the conversation, TaskWeaver uses the concept of a `Planner`. The `Planner` is a LLM that takes the request from the users and maps out the tasks that need to be completed to fulfill this request.

To complete the tasks the `Planner` is exposed to the collection of tools called `Plugins`. This can be Python classes or a general code interpreter. This plugins are stored as embeddings so that the LLM can better search for the correct plugin.

![Taskweaver](images/taskweaver.png?WT.mc_id=academic-105485-koreyst)

Here is an example of a plugin to handle anomaly detection:

```python
class AnomalyDetectionPlugin(Plugin): def __call__(self, df: pd.DataFrame, time_col_name: str, value_col_name: str):
```

The code is verified before executing. Another feature to manage context in Taskweaver is `experience`. Experience allows for the context of a conversation to be stored over to the long term in a YAML file. This can be configured so that the LLM improves over time on certain tasks given that it is exposed to prior conversations.

## JARVIS

The last agent framework we will explore is [JARVIS](https://github.com/microsoft/JARVIS?tab=readme-ov-file&WT.mc_id=academic-105485-koreyst). What makes JARVIS unique is that it uses an LLM to manage the `state` of the conversation and the `tools`are other AI models. Each of the AI models are specialized models that perform certain tasks such as object detection, transcription or image captioning.

![JARVIS](images/jarvis.png?WT.mc_id=academic-105485-koreyst)

The LLM, being a general purpose model, receives the request from the user and identifies the specific task and any arguments/data that is needed to complete the task.

```python
[{"task": "object-detection", "id": 0, "dep": [-1], "args": {"image": "e1.jpg" }}]
```

The LLM then formats the request in a manner that the specialized AI model can interpret, such as JSON. Once the AI model has returned its prediction based on the task, the LLM receives the response.

If multiple models are required to complete the task, it will also interpret the response from those models before bringing them together to generate to the response to the user.

The example below shows how this would work when a user is requesting a description and count of the objects in a picture:

## Assignment

To continue your learning of AI Agents you can build with Microsoft Agent Framework:

- An application that simulates a business meeting with different departments of an education startup.
- Create system messages that guide LLMs in understanding different personas and priorities, and enable the user to pitch a new product idea.
- The LLM should then generate follow-up questions from each department to refine and improve the pitch and the product idea

## Learning does not stop here, continue the Journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!
