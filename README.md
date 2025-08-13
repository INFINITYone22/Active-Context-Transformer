# Active Context Transformer (ACT)

## The Problem: The AI Gets "Dumb" in Long Conversations

We've all experienced it. You're in a long, productive conversation with an AI like ChatGPT, and slowly, it starts to lose its spark. Its responses become less creative, its reasoning gets fuzzy, and it seems to struggle with tasks it handled easily at the start. Even when you're well within the official context limit, the *quality* of the interaction degrades.

This isn't just the AI "forgetting." The root cause is that we are overloading its attention mechanism. The model's capacity for attention is related to its internal dimensionality; pushing too much information into it creates noise and confusion. While models with higher dimensionality can handle more context, they aren't immune—and they quickly run into other practical limits, like ballooning KV cache memory usage.

The smarter approach isn't to chase ever-longer context windows, but to keep the active context at an optimal length. For many powerful models today, a 32,000-token window is a sweet spot. It's large enough for complex tasks but focused enough to prevent this cognitive degradation.

## The Solution: AI-Driven Context Curation

The solution I am proposing with ACT is to let the model itself become the curator of its own memory.

By operating within a fixed, optimal context window (e.g., 32k tokens), the model maintains its peak performance. To handle history beyond this window, ACT provides a simple protocol for the AI to save and retrieve critical information.

Based on the task at hand, the AI decides what to store. This capability can be enabled through training on a dataset containing the memory commands or, for a sufficiently well-tuned model, it can be guided by a simple system prompt. This approach respects the model's intelligence by giving it agency over its own focus, ensuring the active context is always sharp and relevant.

## Project Goal and Philosophy

This repository now includes a minimal, production-ready implementation of the Active Context Transformer alongside the conceptual paper.

- 📄 Research Paper: [Paper.md](./Paper.md)
- 🧩 Python package: middleware, storage, parser, CLI, and FastAPI server
- ✅ Tests included (pytest)

---

## Quickstart

### 1) Install

Option A: editable install

```bash
pip install -e .
```

Option B: use requirements

```bash
pip install -r requirements.txt
```

### 2) CLI usage

Process a model response containing memory commands and print cleaned text:

```bash
act process-output --text "Here is an answer.```MEMORY_CMD\nSTORE|blk1|summary|note|full content|a,b\n```"
```

Manually store and retrieve blocks:

```bash
act store blk1 --summary "summary" --type note --content "full content" --tags a,b
act retrieve blk1 | jq .
act list
```

The storage file defaults to `data/context_store.json`. Override with `--store-path /custom/path.json` or set `ACT_STORE_PATH`.

### 3) Run the server

```bash
act-server
```

Endpoints:
- GET `/health`
- POST `/process_output` { text }
- POST `/store` { id, summary, type, content, tags }
- GET `/retrieve/{id}`
- GET `/blocks` (optional query, tag)
- DELETE `/blocks/{id}`

### 4) Example MEMORY_CMD formats

- Store:

```
STORE|block_id|summary_of_content|type|full_content|tag1,tag2
```

- Retrieve:

```
RETRIEVE|block_id
```

You can embed these as:

- A fenced block:

```
```MEMORY_CMD
STORE|...|...|...|...|...
```
```

- An inline directive:

```
MEMORY_CMD: STORE|...|...|...|...|...
```

- Or on its own line:

```
STORE|...|...|...|...|...
```

---

### A Note from the Author

I spend my time thinking about AI. Not just the code, but the nature of intelligence, the architecture of these models, and how to create systems that are genuinely useful and creative. This project comes from that passion.

I see a frustration in the tech world, especially in places like Hyderabad, where a person's worth is often judged by a GPA from an institute rather than by their genuine, world-aware knowledge and relentless drive to innovate. True understanding doesn't come from a few hours in a classroom; it comes from a deep, abiding interest and the courage to think differently.

This project is my statement. It’s built on the belief that the best ideas come from those who are truly immersed in the subject, not those who have simply memorized a curriculum. It’s for those of us who see the deeper picture and are dedicated to building what’s next.

While I can develop this concept into a full, production-ready implementation, I've kept this repository focused on the core architectural idea. This is just one of many concepts I am developing. I don't just theorize; I build advanced AI models and the applications that bring them to life. If you are looking for someone who thinks deeply about these systems and can deliver state-of-the-art results, I encourage you to reach out.

*A creative personal project by Rohith Garapati (GitHub: INFINITYone22)* 