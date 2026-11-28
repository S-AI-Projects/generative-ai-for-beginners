# Integrating with function calling

[![Integrating with function calling](./images/11-lesson-banner.png?WT.mc_id=academic-105485-koreyst)](https://youtu.be/DgUdCLX8qYQ?si=f1ouQU5HQx6F8Gl2)

You've learned a fair bit so far in the previous lessons. However, we can improve further. Some things we can address are how we can get a more consistent response format to make it easier to work with the response downstream. Also, we might want to add data from other sources to further enrich our application.

The above-mentioned problems are what this chapter is looking to address.

## Introduction

This lesson will cover:

- Explain what function calling is and its use cases.
- Creating a function call using Azure OpenAI.
- How to integrate a function call into an application.

## Learning Goals

By the end of this lesson, you will be able to:

- Explain the purpose of using function calling.
- Setup Function Call using the Azure OpenAI Service.
- Design effective function calls for your application's use case.

## Scenario: Improving our chatbot with functions

For this lesson, we want to build a feature for our education startup that allows users to use a chatbot to find technical courses. We will recommend courses that fit their skill level, current role and technology of interest.

To complete this scenario, we will use a combination of:

- `Azure OpenAI` to create a chat experience for the user.
- `Microsoft Learn Catalog API` to help users find courses based on the request of the user.
- `Function Calling` to take the user's query and send it to a function to make the API request.

To get started, let's look at why we would want to use function calling in the first place:

## Why Function Calling

Before function calling, responses from an LLM were unstructured and inconsistent. Developers were required to write complex validation code to make sure they were able to handle each variation of a response. Users could not get answers like "What is the current weather in Stockholm?". This is because models were limited to the time the data was trained on.

Function Calling is a feature of the Azure OpenAI Service to overcome the following limitations:

- **Consistent response format**. If we can better control the response format we can more easily integrate the response downstream to other systems.
- **External data**. Ability to use data from other sources of an application in a chat context.

## Illustrating the problem through a scenario

> We recommend you to use the [included notebook](./python/aoai-assignment.ipynb?WT.mc_id=academic-105485-koreyst) if you want to run the below scenario. You can also just read along as we're trying to illustrate a problem where functions can help to address the problem.

Let's look at the example that illustrates the response format problem:

Let's say we want to create a database of student data so we can suggest the right course to them. Below we have two descriptions of students that are very similar in the data they contain.

1. Create a connection to our Azure OpenAI resource:

   ```python
   import os
   import json
   from openai import OpenAI
   from dotenv import load_dotenv
   load_dotenv()

   # The Responses API is served from the Azure OpenAI (Microsoft Foundry) v1
   # endpoint, so we point the OpenAI client at <your-endpoint>/openai/v1/.
   endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
   client = OpenAI(
   api_key=os.environ['AZURE_OPENAI_API_KEY'],
   base_url=f"{endpoint.rstrip('/')}/openai/v1/",
   )

   deployment=os.environ['AZURE_OPENAI_DEPLOYMENT']
   ```

   Below is some Python code for configuring our connection to Azure OpenAI. Because we use the v1 endpoint, we only need to set the `api_key` and `base_url` (no `api_version` is required).

1. Creating two student descriptions using variables `student_1_description` and `student_2_description`.

   ```python
   student_1_description="Emily Johnson is a sophomore majoring in computer science at Duke University. She has a 3.7 GPA. Emily is an active member of the university's Chess Club and Debate Team. She hopes to pursue a career in software engineering after graduating."

   student_2_description = "Michael Lee is a sophomore majoring in computer science at Stanford University. He has a 3.8 GPA. Michael is known for his programming skills and is an active member of the university's Robotics Club. He hopes to pursue a career in artificial intelligence after finishing his studies."
   ```

   We want to send the above student descriptions to an LLM to parse the data. This data can later be used in our application and be sent to an API or stored in a database.

1. Let's create two identical prompts in which we instruct the LLM on what information we are interested in:

   ```python
   prompt1 = f'''
   Please extract the following information from the given text and return it as a JSON object:

   name
   major
   school
   grades
   club

   This is the body of text to extract the information from:
   {student_1_description}
   '''

   prompt2 = f'''
   Please extract the following information from the given text and return it as a JSON object:

   name
   major
   school
   grades
   club

   This is the body of text to extract the information from:
   {student_2_description}
   '''
   ```

   The above prompts instruct the LLM to extract information and return the response in JSON format.

1. After setting up the prompts and the connection to Azure OpenAI, we will now send the prompts to the LLM by using `client.responses.create`. We store the prompt in the `input` variable and assign the role to `user`. This is to mimic a message from a user being written to a chatbot.

   ```python
   # response from prompt one
   openai_response1 = client.responses.create(
   model=deployment,
   input = [{'role': 'user', 'content': prompt1}],
   store=False,
   )
   openai_response1.output_text

   # response from prompt two
   openai_response2 = client.responses.create(
   model=deployment,
   input = [{'role': 'user', 'content': prompt2}],
   store=False,
   )
   openai_response2.output_text
   ```

Now we can send both requests to the LLM and examine the response we receive by finding it like so `openai_response1.output_text`.

1. Lastly, we can convert the response to JSON format by calling `json.loads`:

   ```python
   # Loading the response as a JSON object
   json_response1 = json.loads(openai_response1.output_text)
   json_response1
   ```

   Response 1:

   ```json
   {
     "name": "Emily Johnson",
     "major": "computer science",
     "school": "Duke University",
     "grades": "3.7",
     "club": "Chess Club"
   }
   ```

   Response 2:

   ```json
   {
     "name": "Michael Lee",
     "major": "computer science",
     "school": "Stanford University",
     "grades": "3.8 GPA",
     "club": "Robotics Club"
   }
   ```

   Even though the prompts are the same and the descriptions are similar, we see values of the `Grades` property formatted differently, as we can sometimes get the format `3.7` or `3.7 GPA` for example.

   This result is because the LLM takes unstructured data in the form of the written prompt and returns also unstructured data. We need to have a structured format so that we know what to expect when storing or using this data

So how do we solve the formatting problem then? By using functional calling, we can make sure that we receive structured data back. When using function calling, the LLM does not actually call or run any functions. Instead, we create a structure for the LLM to follow for its responses. We then use those structured responses to know what function to run in our applications.

![function flow](./images/Function-Flow.png?WT.mc_id=academic-105485-koreyst)

We can then take what is returned from the function and send this back to the LLM. The LLM will then respond using natural language to answer the user's query.

## Use Cases for using function calls

There are many different use cases where function calls can improve your app like:

- **Calling External Tools**. Chatbots are great at providing answers to questions from users. By using function calling, the chatbots can use messages from users to complete certain tasks. For example, a student can ask the chatbot to "Send an email to my instructor saying I need more assistance with this subject". This can make a function call to `send_email(to: string, body: string)`

- **Create API or Database Queries**. Users can find information using natural language that gets converted into a formatted query or API request. An example of this could be a teacher who requests "Who are the students that completed the last assignment" which could call a function named `get_completed(student_name: string, assignment: int, current_status: string)`

- **Creating Structured Data**. Users can take a block of text or CSV and use the LLM to extract important information from it. For example, a student can convert a Wikipedia article about peace agreements to create AI flashcards. This can be done by using a function called `get_important_facts(agreement_name: string, date_signed: string, parties_involved: list)`

## Creating Your First Function Call

The process of creating a function call includes 3 main steps:

1. **Calling** the Responses API with a list of your functions (tools) and a user message.
2. **Reading** the model's response to perform an action i.e. execute a function or API Call.
3. **Making** another call to the Responses API with the response from your function to use that information to create a response to the user.

![LLM Flow](./images/LLM-Flow.png?WT.mc_id=academic-105485-koreyst)

### Step 1 - creating messages

The first step is to create a user message. This can be dynamically assigned by taking the value of a text input or you can assign a value here. If this is your first time working with the Responses API, we need to define the `role` and the `content` of the message.

The `role` can be either `system` (creating rules), `assistant` (the model) or `user` (the end-user). For function calling, we will assign this as `user` and an example question.

```python
messages= [ {"role": "user", "content": "Find me a good course for a beginner student to learn Azure."} ]
```

By assigning different roles, it's made clear to the LLM if it's the system saying something or the user, which helps to build a conversation history that the LLM can build upon.

### Step 2 - creating functions

Next, we will define a function and the parameters of that function. We will use just one function here called `search_courses` but you can create multiple functions.

> **Important** : Functions are included in the system message to the LLM and will be included in the amount of available tokens you have available.

Below, we create the functions as an array of items. Each item is a tool in the flat Responses API format, with properties `type`, `name`, `description` and `parameters`:

```python
functions = [
   {
      "type":"function",
      "name":"search_courses",
      "description":"Retrieves courses from the search index based on the parameters provided",
      "parameters":{
         "type":"object",
         "properties":{
            "role":{
               "type":"string",
               "description":"The role of the learner (i.e. developer, data scientist, student, etc.)"
            },
            "product":{
               "type":"string",
               "description":"The product that the lesson is covering (i.e. Azure, Power BI, etc.)"
            },
            "level":{
               "type":"string",
               "description":"The level of experience the learner has prior to taking the course (i.e. beginner, intermediate, advanced)"
            }
         },
         "required":[
            "role"
         ]
      }
   }
]
```

Let's describe each function instance more in detail below:

- `name` - The name of the function that we want to have called.
- `description` - This is the description of how the function works. Here it's important to be specific and clear.
- `parameters` - A list of values and format that you want the model to produce in its response. The parameters array consists of items where the items have the following properties:
  1.  `type` - The data type of the properties will be stored in.
  1.  `properties` - List of the specific values that the model will use for its response
      1. `name` - The key is the name of the property that the model will use in its formatted response, for example, `product`.
      1. `type` - The data type of this property, for example, `string`.
      1. `description` - Description of the specific property.

There's also an optional property `required` - required property for the function call to be completed.

### Step 3 - Making the function call

After defining a function, we now need to include it in the call to the Responses API. We do this by adding `tools` to the request. In this case `tools=functions`.

There is also an option to set `tool_choice` to `auto`. This means we will let the LLM decide which function should be called based on the user message rather than assigning it ourselves.

Here's some code below where we call `client.responses.create`, note how we set `tools=functions` and `tool_choice="auto"` and thereby giving the LLM the choice when to call the functions we provide it:

```python
response = client.responses.create(model=deployment,
                                        input=messages,
                                        tools=functions,
                                        tool_choice="auto",
                                        store=False)

print(response.output)
```

The response coming back now includes a `function_call` item in `response.output` that looks like so:

```json
{
  "type": "function_call",
  "name": "search_courses",
  "call_id": "call_abc123",
  "arguments": "{\n  \"role\": \"student\",\n  \"product\": \"Azure\",\n  \"level\": \"beginner\"\n}"
}
```

Here we can see how the function `search_courses` was called and with what arguments, as listed in the `arguments` property in the JSON response.

The conclusion the LLM was able to find the data to fit the arguments of the function as it was extracting it from the value provided to the `input` parameter in the Responses API call. Below is a reminder of the `messages` value:

```python
messages= [ {"role": "user", "content": "Find me a good course for a beginner student to learn Azure."} ]
```

As you can see, `student`, `Azure` and `beginner` was extracted from `messages` and set as input to the function. Using functions this way is a great way to extract information from a prompt but also to provide structure to the LLM and have reusable functionality.

Next, we need to see how we can use this in our app.

## Integrating Function Calls into an Application

After we have tested the formatted response from the LLM, we can now integrate this into an application.

### Managing the flow

To integrate this into our application, let's take the following steps:

1. First, let's make the call to the OpenAI services and extract the function call items from the response `output`.

   ```python
   response_items = response.output
   tool_calls = [item for item in response_items if item.type == "function_call"]
   ```

1. Now we will define the function that will call the Microsoft Learn API to get a list of courses:

   ```python
   import requests

   def search_courses(role, product, level):
     url = "https://learn.microsoft.com/api/catalog/"
     params = {
        "role": role,
        "product": product,
        "level": level
     }
     response = requests.get(url, params=params)
     modules = response.json()["modules"]
     results = []
     for module in modules[:5]:
        title = module["title"]
        url = module["url"]
        results.append({"title": title, "url": url})
     return str(results)
   ```

   Note how we now create an actual Python function that maps to the function names introduced in the `functions` variable. We're also making real external API calls to fetch the data we need. In this case, we go against the Microsoft Learn API to search for training modules.

Ok, so we created `functions` variables and a corresponding Python function, how do we tell the LLM how to map these two together so our Python function is called?

1. To see if we need to call a Python function, we need to look into the LLM response and see if a `function_call` item is part of it and call the pointed-out function. Here's how you can make the mentioned check below:

   ```python
   # Check if the model wants to call a function
   if tool_calls:
    for tool_call in tool_calls:
     print("Recommended Function call:")
     print(tool_call.name)
     print()

     # Call the function.
     function_name = tool_call.name

     available_functions = {
             "search_courses": search_courses,
     }
     function_to_call = available_functions[function_name]

     function_args = json.loads(tool_call.arguments)
     function_response = function_to_call(**function_args)

     print("Output of function call:")
     print(function_response)
     print(type(function_response))

     # Add the function call and its result back to the conversation.
     # The model's function_call item must be appended before its output.
     messages.append(tool_call)  # the assistant's function_call item
     messages.append( # the function result
         {
             "type": "function_call_output",
             "call_id": tool_call.call_id,
             "output": function_response,
         }
     )
   ```

   These three lines, ensure we extract the function name, the arguments and make the call:

   ```python
   function_to_call = available_functions[function_name]

   function_args = json.loads(tool_call.arguments)
   function_response = function_to_call(**function_args)
   ```

   Below is the output from running our code:

   **Output**

   ```Recommended Function call:
   {
     "name": "search_courses",
     "arguments": "{\n  \"role\": \"student\",\n  \"product\": \"Azure\",\n  \"level\": \"beginner\"\n}"
   }

   Output of function call:
   [{'title': 'Describe concepts of cryptography', 'url': 'https://learn.microsoft.com/training/modules/describe-concepts-of-cryptography/?
   WT.mc_id=api_CatalogApi'}, {'title': 'Introduction to audio classification with TensorFlow', 'url': 'https://learn.microsoft.com/en-
   us/training/modules/intro-audio-classification-tensorflow/?WT.mc_id=api_CatalogApi'}, {'title': 'Design a Performant Data Model in Azure SQL
   Database with Azure Data Studio', 'url': 'https://learn.microsoft.com/training/modules/design-a-data-model-with-ads/?
   WT.mc_id=api_CatalogApi'}, {'title': 'Getting started with the Microsoft Cloud Adoption Framework for Azure', 'url':
   'https://learn.microsoft.com/training/modules/cloud-adoption-framework-getting-started/?WT.mc_id=api_CatalogApi'}, {'title': 'Set up the
   Rust development environment', 'url': 'https://learn.microsoft.com/training/modules/rust-set-up-environment/?WT.mc_id=api_CatalogApi'}]
   <class 'str'>
   ```

1. Now we will send the updated message, `messages` to the LLM so we can receive a natural language response instead of an API JSON formatted response.

   ```python
   print("Messages in next request:")
   print(messages)
   print()

   second_response = client.responses.create(
      input=messages,
      model=deployment,
      tool_choice="auto",
      tools=functions,
      temperature=0,
      store=False,
         )  # get a new response from the model where it can see the function response


   print(second_response.output_text)
   ```

   **Output**

   ```text
   I found some good courses for beginner students to learn Azure:

   1. [Describe concepts of cryptography](https://learn.microsoft.com/training/modules/describe-concepts-of-cryptography/?WT.mc_id=api_CatalogApi)
   2. [Introduction to audio classification with TensorFlow](https://learn.microsoft.com/training/modules/intro-audio-classification-tensorflow/?WT.mc_id=api_CatalogApi)
   3. [Design a Performant Data Model in Azure SQL Database with Azure Data Studio](https://learn.microsoft.com/training/modules/design-a-data-model-with-ads/?WT.mc_id=api_CatalogApi)
   4. [Getting started with the Microsoft Cloud Adoption Framework for Azure](https://learn.microsoft.com/training/modules/cloud-adoption-framework-getting-started/?WT.mc_id=api_CatalogApi)
   5. [Set up the Rust development environment](https://learn.microsoft.com/training/modules/rust-set-up-environment/?WT.mc_id=api_CatalogApi)

   You can click on the links to access the courses.
   ```

## Assignment

To continue your learning of Azure OpenAI Function Calling you can build:

- More parameters of the function that might help learners find more courses.
- Create another function call that takes more information from the learner like their native language
- Create error handling when the function call and/or API call does not return any suitable courses

Hint: Follow the [Learn API reference documentation](https://learn.microsoft.com/training/support/catalog-api-developer-reference?WT.mc_id=academic-105485-koreyst) page to see how and where this data is available.

## Applied lab r40-t054 — recorded state history and the reconstruction invariant

This lab adds a small local simulation on top of the lesson concepts: given
one response message with a stable ID, model its local pending, streaming,
complete and error states as chunks arrive, **recording an immutable
snapshot after every step**, and test the invariant that the final output
can always be rebuilt from that recorded history alone.

> **Simulation / mock behaviour:** the example performs **no** model
> download, **no** remote API call, **no** GPU and **no** network access.
> It is a local state machine over plain strings, not a claim about Azure
> OpenAI's actual streaming wire format, timing or error codes.

### Exact invocation

```bash
# Inside the repository root
python3 11-integrating-with-function-calling/applied-labs/r40-t054/example.py

# Test suite, in a fresh process
python3 -m unittest discover -s 11-integrating-with-function-calling/applied-labs/r40-t054 -p "test_*.py"
```

### Fixture (synthetic teaching scenario) and recorded history

| step | action | message_id | state after | text after |
|---|---|---|---|---|
| 0 | `create_message("msg-1")` | `msg-1` | `pending` | `""` |
| 1 | `append_chunk("Here are some ")` | `msg-1` | `streaming` | `"Here are some "` |
| 2 | `append_chunk("Azure courses.")` | `msg-1` | `streaming` | `"Here are some Azure courses."` |
| 3 | `complete_message()` | `msg-1` | `complete` | `"Here are some Azure courses."` |

Every row above is one `StateSnapshot` appended to `Message.history` as it
happens -- the example records the intermediate state after each step, not
just the final one.

### Expected output (exact)

```text
[LESSON: message identity] creating message id=msg-1
  step=0 action=create state=pending text=''
[LESSON: streaming state] step=1 chunk appended -> state=streaming text='Here are some '
[LESSON: streaming state] step=2 chunk appended -> state=streaming text='Here are some Azure courses.'
[LESSON: completion] step=3 state=complete text='Here are some Azure courses.' message_id=msg-1
[LESSON: invariant] reconstruct_text_from_history(history)='Here are some Azure courses.' == message.text='Here are some Azure courses.' -> True
[LESSON: message identity] creating message id=msg-2
[LESSON: recovery] state=error text='Here are some [ERROR: upstream timeout]' error='upstream timeout' message_id=msg-2
[LESSON: invariant] reconstruct_text_from_history(history)='Here are some [ERROR: upstream timeout]' == message.text='Here are some [ERROR: upstream timeout]' -> True
[LESSON: boundary] chunk after finalize rejected: chunk rejected: message 'msg-2' is already finalized in state 'error'
[LESSON: invariant] history length unchanged by rejected step: 3
```

Two chunks append **in order** onto the same `message_id` (`msg-1`, stable
throughout). A second message (`msg-2`) receives one chunk, then an error:
the already-received text `"Here are some "` is preserved and an
`[ERROR: upstream timeout]` marker is appended. Any chunk sent after a
message reaches `complete` or `error` is rejected -- and, because the
rejection happens before any mutation, it never grows `history` either.

### The focus: recording intermediate state and testing the invariant

`reconstruct_text_from_history(history)` rebuilds the final text **purely
from the recorded `StateSnapshot`s** -- it never reads the live `Message`
object. The invariant this lab tests is:

```text
reconstruct_text_from_history(message.history) == message.text
```

for every message, in every scenario (normal completion, error, and the
zero-chunk boundary case). If the recorded history ever diverged from the
live state -- for example, if a step mutated `text` without recording a
snapshot, or recorded the wrong chunk -- this invariant would catch it,
because the final output would then disagree with the history replay.
`test_each_intermediate_snapshot_matches_live_state_at_that_point` in the
test module goes one step further and checks the snapshot recorded at
*each* step, not only the last one.

### Boundary and failure scenarios

| scenario | input | expected |
|---|---|---|
| smallest valid case | zero chunks, then complete | `complete`, `text=""`, invariant holds |
| single chunk | one chunk, then complete | `complete`, `text` = the one chunk |
| normal | two chunks, then complete | `complete`, `text` = chunks joined in order, invariant holds |
| error with prior text | one chunk, then fail("upstream timeout") | `error`, invariant holds |
| chunk after completion | append after `complete_message()` | `ValueError`, history unchanged |
| chunk after error | append after `fail_message()` | `ValueError`, history unchanged |
| double complete | `complete_message()` twice | `ValueError` |
| empty message id | `create_message("")` | `ValueError` |

These are fully covered by
[`test_r40_t054.py`](11-integrating-with-function-calling/applied-labs/r40-t054/test_r40_t054.py);
the regression check lives in
[`check_r40_t054.py`](11-integrating-with-function-calling/applied-labs/r40-t054/check_r40_t054.py).

### Lesson-concept mapping: public inputs / outputs

| public input / output | lesson concept it illustrates |
|---|---|
| `Message.message_id` | per-item identity, as with the Responses API's `call_id` on a function call |
| `Message.state` / `append_chunk` | building up a response incrementally before it is used downstream |
| `Message.history` / `StateSnapshot` | recording intermediate state at each step of that incremental build-up |
| `reconstruct_text_from_history` | the invariant linking recorded intermediate state to the final output |
| `fail_message` / `Message.error` | the assignment's call to "create error handling when ... does not return any suitable courses" |

### Where the simplification stops

This fixture models message *bookkeeping* only: one in-memory `Message`
object, a list of immutable snapshots, and string concatenation for
chunks. It does not call `client.responses.create`, does not stream real
server-sent events, does not model partial JSON/tool-call argument
streaming, and does not model retries, backoff or concurrent messages. It
demonstrates the *shape* of recording and verifying state history against
a final output, not the Azure OpenAI SDK's actual streaming behavior.

## Great Work! Continue the Journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!

Head over to Lesson 12, where we will look at how to [design UX for AI applications](../12-designing-ux-for-ai-applications/README.md?WT.mc_id=academic-105485-koreyst)!
