# 📚 Library Assistant (OpenAI Agents SDK)

A Library Assistant built using **OpenAI Agents SDK**.  
This assistant can:

- 🔎 Search for books in the library
- ✅ Check availability of books (**only for registered members**)
- 🕘 Provide library timings
- 🚫 Ignore non-library-related questions (via guardrails)

---

## 🚀 Features

- **Agent-based design** using `agents.Agent`
- **Tools** implemented with `@function_tool`  
  - `search_book` → Search by title  
  - `check_availability` → Check number of copies (members only)  
  - `get_library_timings` → Returns library hours
- **Guardrails** with `@input_guardrail` to block non-library queries
- **Dynamic Instructions** → Personalized responses based on user name
- **Context Management** with `RunContextWrapper`
- **Multiple tool handling** → Search + Availability in one query

---

## 🛠️ Requirements

- Python 3.9+
- [OpenAI Agents SDK](https://github.com/openai/agents-python)  
- `pydantic`  
- `python-dotenv`

Install dependencies:

- pip install -r requirements.txt

## Running the Assistant
- python library_agent.py

## Output

USER: Search for Clean Code
ASSISTANT: ✅ Book 'Clean Code' is available.

USER: Is the library open on Sunday?
ASSISTANT: 🕘 The library is open from 9 AM to 8 PM, Monday to Saturday.

USER: Check availability of Clean Code
ASSISTANT: 📦 There are 4 copies of 'Clean Code' available.

USER: Do you like pizza?
ASSISTANT: 🚫 Sorry, I can only answer library-related questions.

