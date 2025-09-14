# library_agent.py
"""
Library Assistant using OpenAI Agents SDK.
- Tools: search_book, check_availability, get_library_timings
- Guardrail blocks non-library queries
- check_availability allowed only for registered members (via RunContextWrapper)
- Uses @function_tool, @input_guardrail, Runner.run / Runner.run_sync, dynamic instructions, ModelSettings
- Tests: runs 3 example queries and prints results

Notes:
- Put your API key in .env.local as OPENAI_API_KEY=...
"""

import os
from typing import Optional, List, Union
from pydantic import BaseModel
from dotenv import load_dotenv

# Agents SDK imports
from agents import (
    Agent,
    Runner,
    function_tool,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    ModelSettings,
    TResponseInputItem,
)

# --------------------------
# Load API key from .env.local
# --------------------------
load_dotenv(".env.local")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY! Add it to .env.local")

# --------------------------
# 1) User Context model (Pydantic)
# --------------------------
class UserContext(BaseModel):
    name: str
    member_id: Optional[str] = None  # e.g. "M001" if registered

# --------------------------
# 2) Book Database (dict of title -> copies)
# --------------------------
BOOK_DB = {
    "Clean Code": 2,
    "Atomic Habits": 5,
    "The Pragmatic Programmer": 0,
    "Deep Work": 1,
    "Harry Potter and the Sorcerer's Stone": 3,
}

# Registered members
MEMBERS = {
    "M001": "Muhammad Annas",
    "M002": "Ali Khan",
}

# --------------------------
# 3) Tools
# --------------------------
@function_tool
def search_book(query: str) -> str:
    """Search books by partial title match and return matching titles."""
    q = query.strip().lower()
    matches = [title for title in BOOK_DB.keys() if q in title.lower()]
    if not matches:
        return f"No books found matching '{query}'."
    return "Found: " + ", ".join(matches)


@function_tool
def check_availability(ctx: RunContextWrapper[UserContext], book_title: str) -> str:
    """Check book availability (registered members only)."""
    user_ctx = ctx.context
    if not user_ctx or not user_ctx.member_id or user_ctx.member_id not in MEMBERS:
        return "Access denied: availability check is for registered members only."
    copies = BOOK_DB.get(book_title, None)
    if copies is None:
        return f"Book '{book_title}' not found in catalog."
    if copies == 0:
        return f"'{book_title}' is currently not available (0 copies)."
    return f"'{book_title}' — {copies} copies available."


@function_tool
def get_library_timings() -> str:
    """Return library timings."""
    return "Library timings: Mon-Fri 09:00-18:00; Sat 10:00-14:00; Sun closed."

# --------------------------
# 4) Guardrail: block non-library queries
# --------------------------
class GuardrailOutput(BaseModel):
    is_library_query: bool
    reason: Optional[str] = None

guardrail_agent = Agent(
    name="LibraryGuardrail",
    instructions=(
        "Classify whether the user's message is about library services "
        "(searching books, checking availability, timings, membership). "
        "Return boolean `is_library_query` and optional `reason`."
    ),
    output_type=GuardrailOutput,
)

@input_guardrail
async def library_input_guardrail(
    ctx: RunContextWrapper[UserContext],
    agent: Agent,
    input: Union[str, List[TResponseInputItem]],
) -> GuardrailFunctionOutput:
    guard_result = await Runner.run(guardrail_agent, input, context=ctx.context)
    try:
        out = guard_result.final_output
        is_lib = bool(getattr(out, "is_library_query", False))
    except Exception:
        is_lib = True  # fallback
    return GuardrailFunctionOutput(
        output_info=guard_result.final_output, tripwire_triggered=(not is_lib)
    )

# --------------------------
# 5) Dynamic instructions
# --------------------------
def dynamic_instructions(context: RunContextWrapper[UserContext], agent: Agent) -> str:
    name = "Library user"
    if context and context.context and getattr(context.context, "name", None):
        name = context.context.name
    return (
        f"Hello {name}. You are a helpful Library Assistant.\n"
        "- Use search_book to find books.\n"
        "- Use check_availability only for registered members.\n"
        "- Use get_library_timings for hours.\n"
        "- Refuse politely if it's not a library-related query.\n"
        "You may call multiple tools in one query."
    )

# --------------------------
# 6) Build the Library Agent
# --------------------------
library_agent = Agent(
    name="LibraryAssistant",
    instructions=dynamic_instructions,
    tools=[search_book, check_availability, get_library_timings],
    input_guardrails=[library_input_guardrail],
    model_settings=ModelSettings(
        tool_choice="auto",
        parallel_tool_calls=True,
        verbosity="low",
    ),
)

# --------------------------
# 7) Run helpers & tests
# --------------------------
def run_query_sync_print(query: str, user_ctx: UserContext):
    print("\n====")
    print("Query:", query)
    try:
        result = Runner.run_sync(library_agent, query, context=user_ctx)
        print("Result:", result.final_output)
    except InputGuardrailTripwireTriggered:
        print("Guardrail triggered: Non-library question ignored.")
    except Exception as exc:
        print("Error running agent:", repr(exc))


if __name__ == "__main__":
    # Test 1: Registered member
    user1 = UserContext(name="Muhammad Annas", member_id="M001")
    run_query_sync_print(
        "Search for 'Clean Code' and tell me how many copies are available.", user1
    )

    # Test 2: Non-library question
    user2 = UserContext(name="Visitor")
    run_query_sync_print("What's the weather in Karachi today?", user2)

    # Test 3: Guest without membership
    guest = UserContext(name="Guest User")
    run_query_sync_print(
        "Do you have 'The Pragmatic Programmer'? If yes, check copies.", guest
    )

    # Test 4: Ask timings
    user4 = UserContext(name="Student")
    run_query_sync_print("What are the library timings?", user4)

    print("\nFinished tests.")
