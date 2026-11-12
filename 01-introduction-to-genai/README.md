# Introduction to Generative AI and Large Language Models

[![Introduction to Generative AI and Large Language Models](./images/01-lesson-banner.png?WT.mc_id=academic-105485-koreyst)](https://youtu.be/lFXQkBvEe0o?si=6ZBcQTwLJJDpnX0K)

_(Click the image above to view video of this lesson)_

Generative AI is artificial intelligence capable of generating text, images and other types of content. What makes it a fantastic technology is that it democratizes AI, anyone can use it with as little as a text prompt, a sentence written in a natural language. There's no need for you to learn a language like Java or SQL to accomplish something worthwhile, all you need is to use your language, state what you want and out comes a suggestion from an AI model. The applications and impact for this are huge, you write or understand reports, write applications and much more, all in seconds.

In this curriculum, we’ll explore how our startup leverages generative AI to unlock new scenarios in the education world and how we address the inevitable challenges associated with the social implications of its application and the technology limitations.

## Introduction

This lesson will cover:

- Introduction to the business scenario: our startup idea and mission.
- Generative AI and how we landed on the current technology landscape.
- Inner working of a large language model.
- Main capabilities and practical use cases of Large Language Models.
- Worked startup decision-table lab: evaluating prompt inputs, token limits, and human review.

## Learning Goals

After completing this lesson, you will understand:

- What generative AI is and how Large Language Models work.
- How you can leverage large language models for different use cases, with a focus on education scenarios.

## Scenario: our educational startup

Generative Artificial Intelligence (AI) represents the pinnacle of AI technology, pushing the boundaries of what was once thought impossible. Generative AI models have several capabilities and applications, but for this curriculum we'll explore how it's revolutionizing education through a fictional startup. We'll refer to this startup as _our startup_. Our startup works in the education domain with the ambitious mission statement of

> _improving accessibility in learning, on a global scale, ensuring equitable access to education and providing personalized learning experiences to every learner, according to their needs_.

Our startup team is aware we’ll not be able to achieve this goal without leveraging one of the most powerful tools of modern times – Large Language Models (LLMs).

Generative AI is expected to revolutionize the way we learn and teach today, with students having at their disposal virtual teachers 24 hours a day who provide vast amounts of information and examples, and teachers able to leverage innovative tools to assess their students and give feedback.

![Five young students looking at a monitor - image by DALLE2](./images/students-by-DALLE2.png?WT.mc_id=academic-105485-koreyst)

To start, let’s define some basic concepts and terminology we’ll be using throughout the curriculum.

## How did we get Generative AI?

Despite the extraordinary _hype_ created lately by the announcement of generative AI models, this technology is decades in the making, with the first research efforts dating back to the 60s. We're now at a point with AI having human cognitive capabilities, like conversation as shown by for example [OpenAI ChatGPT](https://openai.com/chatgpt) or [Microsoft Copilot](https://copilot.microsoft.com/?WT.mc_id=academic-105485-koreyst), which also uses a GPT model for its conversational web search experience.

Backing up a bit, the very first prototypes of AI consisted of typewritten chatbots, relying on a knowledge base extracted from a group of experts and represented into a computer. The answers in the knowledge base were triggered by keywords appearing in the input text.
However, it soon became clear that such an approach, using typewritten chatbots, did not scale well.

### A statistical approach to AI: Machine Learning

A turning point arrived during the 90s, with the application of a statistical approach to text analysis. This led to the development of new algorithms – known as machine learning – capable of learning patterns from data without being explicitly programmed. This approach allows machines to simulate human language understanding: a statistical model is trained on text-label pairings, enabling the model to classify unknown input text with a pre-defined label representing the intention of the message.

### Neural networks and modern virtual assistants

In recent years, the technological evolution of hardware, capable of handling larger amounts of data and more complex computations, encouraged research in AI, leading to the development of advanced machine learning algorithms known as neural networks or deep learning algorithms.

Neural networks (and in particular Recurrent Neural Networks – RNNs) significantly enhanced natural language processing, enabling the representation of the meaning of text in a more meaningful way, valuing the context of a word in a sentence.

This is the technology that powered the virtual assistants born in the first decade of the new century, very proficient in interpreting human language, identifying a need, and performing an action to satisfy it – like answering with a pre-defined script or consuming a 3rd party service.

### Present day, Generative AI

So that’s how we came to Generative AI today, which can be seen as a subset of deep learning.

![AI, ML, DL and Generative AI](./images/AI-diagram.png?WT.mc_id=academic-105485-koreyst)

After decades of research in the AI field, a new model architecture – called _Transformer_ – overcame the limits of RNNs, being able to get much longer sequences of text as input. Transformers are based on the attention mechanism, enabling the model to give different weights to the inputs it receives, ‘paying more attention’ where the most relevant information is concentrated, regardless of their order in the text sequence.

Most of the recent generative AI models – also known as Large Language Models (LLMs), since they work with textual inputs and outputs – are indeed based on this architecture. What’s interesting about these models – trained on a huge amount of unlabeled data from diverse sources like books, articles and websites – is that they can be adapted to a wide variety of tasks and generate grammatically correct text with a semblance of creativity. So, not only did they incredibly enhance the capacity of a machine to ‘understand’ an input text, but they enabled their capacity to generate an original response in human language.

## How do large language models work?

In the next chapter we are going to explore different types of Generative AI models, but for now let’s have a look at how large language models work, with a focus on OpenAI GPT (Generative Pre-trained Transformer) models.

- **Tokenizer, text to numbers**: Large Language Models receive a text as input and generate a text as output. However, being statistical models, they work much better with numbers than text sequences. That’s why every input to the model is processed by a tokenizer, before being used by the core model. A token is a chunk of text – consisting of a variable number of characters, so the tokenizer's main task is splitting the input into an array of tokens. Then, each token is mapped with a token index, which is the integer encoding of the original text chunk.

![Example of tokenization](./images/tokenizer-example.png?WT.mc_id=academic-105485-koreyst)

- **Predicting output tokens**: Given n tokens as input (with max n varying from one model to another), the model is able to predict one token as output. This token is then incorporated into the input of the next iteration, in an expanding window pattern, enabling a better user experience of getting one (or multiple) sentence as an answer. This explains why, if you ever played with ChatGPT, you might have noticed that sometimes it looks like it stops in the middle of a sentence.

- **Selection process, probability distribution**: The output token is chosen by the model according to its probability of occurring after the current text sequence. This is because the model predicts a probability distribution over all possible ‘next tokens’, calculated based on its training. However, not always is the token with the highest probability chosen from the resulting distribution. A degree of randomness is added to this choice, in a way that the model acts in a non-deterministic fashion - we do not get the exact same output for the same input. This degree of randomness is added to simulate the process of creative thinking and it can be tuned using a model parameter called temperature.

## How can our startup leverage Large Language Models?

Now that we have a better understanding of the inner working of a large language model, let’s see some practical examples of the most common tasks they can perform pretty well, with an eye to our business scenario.
We said that the main capability of a Large Language Model is _generating a text from scratch, starting from a textual input, written in natural language_.

But what kind of textual input and output?
The input of a large language model is known as a prompt, while the output is known as a completion, term that refers to the model mechanism of generating the next token to complete the current input. We are going to dive deep into what is a prompt and how to design it in a way to get the most out of our model. But for now, let’s just say that a prompt may include:

- An **instruction** specifying the type of output we expect from the model. This instruction sometimes might embed some examples or some additional data.

  1. Summarization of an article, book, product reviews and more, along with extraction of insights from unstructured data.
    
    ![Example of summarization](./images/summarization-example.png?WT.mc_id=academic-105485-koreyst)
  
  2. Creative ideation and design of an article, an essay, an assignment or more.
      
     ![Example of creative writing](./images/creative-writing-example.png?WT.mc_id=academic-105485-koreyst)

- A **question**, asked in the form of a conversation with an agent.
  
  ![Example of conversation](./images/conversation-example.png?WT.mc_id=academic-105485-koreyst)

- A chunk of **text to complete**, which implicitly is an ask for writing assistance.
  
  ![Example of text completion](./images/text-completion-example.png?WT.mc_id=academic-105485-koreyst)

- A chunk of **code** together with the ask of explaining and documenting it, or a comment asking to generate a piece of code performing a specific task.
  
  ![Coding example](./images/coding-example.png?WT.mc_id=academic-105485-koreyst)

The examples above are quite simple and are not intended to be an exhaustive demonstration of Large Language Models' capabilities. They are meant to show the potential of using generative AI, in particular but not limited to educational contexts.

Also, the output of a generative AI model is not perfect and sometimes the creativity of the model can work against it, resulting in an output which is a combination of words that the human user can interpret as a mystification of reality, or it can be offensive. Generative AI is not intelligent - at least in the more comprehensive definition of intelligence, including critical and creative reasoning or emotional intelligence; it is not deterministic, and it is not trustworthy, since fabrications, such as erroneous references, content, and statements, may be combined with correct information, and presented in a persuasive and confident manner. In the following lessons, we’ll be dealing with all these limitations and we’ll see what we can do to mitigate them.

## Assignment

Your assignment is to read up more on [generative AI](https://en.wikipedia.org/wiki/Generative_artificial_intelligence?WT.mc_id=academic-105485-koreyst) and try to identify an area where you would add generative AI today that doesn't have it. How would the impact be different from doing it the "old way", can you do something you couldn't before, or are you faster? Write a 300 word summary on what your dream AI startup would look like and include headers like "Problem", "How I would use AI", "Impact" and optionally a business plan.

If you did this task, you might even be ready to apply to Microsoft's incubator, [Microsoft for Startups Founders Hub](https://www.microsoft.com/startups?WT.mc_id=academic-105485-koreyst) we offer credits for both Azure, OpenAI, mentoring and much more, check it out!

## Knowledge check

What's true about large language models?

1. You get the exact same response every time.
1. It does things perfectly, great at adding numbers, produce working code etc.
1. The response may vary despite using the same prompt. It's also great at giving you a first draft of something, be it text or code. But you need to improve on the results.

A: 3, an LLM is non-deterministic, the response varies, however, you can control its variance via a temperature setting. You also shouldn't expect it to do things perfectly, it's here to do the heavy-lifting for you which often means you get a good first attempt at something that you need to gradually improve.

## Educational Startup Decision Table: Worked Examples (Applied Lab)

> **Simulation / Synthetic Fixture Notice:** The runnable lab at [example.py](./applied-labs/r40-t057/example.py?WT.mc_id=academic-105485-koreyst) (with regression tests in [test_example.py](./applied-labs/r40-t057/test_example.py?WT.mc_id=academic-105485-koreyst)) is a **local deterministic decision-table simulation** (`"simulation": true`). It illustrates Lesson 01's _"our educational startup"_ scenario—checking whether a natural-language prompt fits inside a model's `n`-token expanding window with human review enabled—using small local fixtures only. Its simplifications stop at static rule checking: it calls no real LLM API, downloads no weights, uses no real subword tokenizer, and makes no claims about hardware, cloud services, or trained-model performance.

**Prerequisite tools:** Python 3.9+ (standard library only; no model download, API key, paid provider, GPU, or physical device required).

### Published Decision Table (`R1`–`R4`)

| Rule | Condition on `input_facts` | Expected Decision | Lesson 01 Connection |
| :--- | :--- | :--- | :--- |
| `R1` | Any required fact (`role`, `task_type`, `prompt_text`, `estimated_tokens`, `max_input_tokens`, `human_review_enabled`) is `None` or blank | `request_missing_information` | Prompts require clear natural-language instructions, and educational workflows must enforce governance facts upfront rather than guessing. |
| `R2` | All facts present and `estimated_tokens >= max_input_tokens` | `chunk_prompt_at_token_limit` | Models take up to `n` tokens and generate iteratively in an expanding window; hitting `n` leaves zero output headroom and risks stopping mid-sentence. |
| `R3` | All facts present, `estimated_tokens < max_input_tokens`, and `human_review_enabled is False` | `require_human_review_gate` | LLM completions are non-deterministic first drafts that can contain fabrications and require human/teacher oversight. |
| `R4` | All facts present, `estimated_tokens < max_input_tokens`, and `human_review_enabled is True` | `approve_llm_draft` | Supports our startup's personalized tutoring and feedback mission safely within token limits and human supervision. |

### Worked Input-to-Output Explanation (Three Scenarios)

1. **Normal (`normal`)**: `role="student"`, `task_type="concept_explanation"`, `prompt_text="Explain fractions with two everyday visual examples for a 10-year-old."`, `estimated_tokens=18`, `max_input_tokens=100`, `human_review_enabled=True` -> `R1` False -> `R2` False (`18 < 100`) -> `R3` False (`True`) -> `R4` fires -> **`approve_llm_draft`**.
2. **Boundary (`boundary`)**: `role="teacher"`, `task_type="article_summarization"`, `prompt_text="Summarize this curriculum reading passage at the exact 100-token context limit."`, `estimated_tokens=100`, `max_input_tokens=100`, `human_review_enabled=True` -> `R1` False -> `R2` True (`100 >= 100`, exact window limit `n`) -> **`chunk_prompt_at_token_limit`**.
3. **Missing Information (`missing_info`)**: `role="teacher"`, `task_type="essay_feedback"`, `prompt_text=""`, `estimated_tokens=None`, `max_input_tokens=100`, `human_review_enabled=None` -> `R1` True (missing `prompt_text`, `estimated_tokens`, `human_review_enabled`) -> **`request_missing_information`**.

Human reviewers can verify each published `rationale` directly against the lesson sections above, while the decision-table checker executes all three worked scenarios as a regression test and fails with exit code `1` if any decision is deliberately altered.

### Exact Invocation and Expected Output

Run the normal scenario from the repository root:

```bash
python3 01-introduction-to-genai/applied-labs/r40-t057/example.py --scenario normal
```

Expected output:

```json
{
  "simulation": true,
  "checked_count": 1,
  "all_passed": true,
  "mismatches": [],
  "results": [
    {
      "scenario_id": "normal",
      "title": "Normal scenario: personalized concept explanation with human review",
      "input_facts": {
        "role": "student",
        "task_type": "concept_explanation",
        "prompt_text": "Explain fractions with two everyday visual examples for a 10-year-old.",
        "estimated_tokens": 18,
        "max_input_tokens": 100,
        "human_review_enabled": true
      },
      "expected_decision": "approve_llm_draft",
      "actual_decision": "approve_llm_draft",
      "rule_id": "R4",
      "trace": [
        "R1 skipped: all required facts present",
        "R2 skipped: estimated_tokens (18) < max_input_tokens (100)",
        "R3 skipped: human_review_enabled is True",
        "R4 matched: all guardrails satisfied"
      ],
      "worked_trace": "R1 (missing info): False (all 6 required facts present); R2 (token boundary): False (18 < 100); R3 (no human review): False (human_review_enabled=True); R4 fires -> approve_llm_draft.",
      "rationale": "Lesson 01 frames our educational startup around accessible, personalized learning using natural-language prompts as a strong first draft checked by humans because LLMs are non-deterministic. All required facts are supplied, estimated_tokens (18) leaves headroom inside max_input_tokens (100), and human_review_enabled is True.",
      "passed": true
    }
  ]
}
```

Run all three scenarios, confirm the deliberate tamper failure exits non-zero, and run the regression test suite:

```bash
python3 01-introduction-to-genai/applied-labs/r40-t057/example.py
python3 01-introduction-to-genai/applied-labs/r40-t057/example.py --scenario normal --tamper-decision chunk_prompt_at_token_limit
python3 -m unittest discover -s 01-introduction-to-genai/applied-labs/r40-t057 -p "test_*.py"
```

## Great Work! Continue the Journey

After completing this lesson, check out our [Generative AI Learning collection](https://aka.ms/genai-collection?WT.mc_id=academic-105485-koreyst) to continue leveling up your Generative AI knowledge!

Head over to Lesson 2 where we will look at how to [explore and compare different LLM types](../02-exploring-and-comparing-different-llms/README.md?WT.mc_id=academic-105485-koreyst)!
