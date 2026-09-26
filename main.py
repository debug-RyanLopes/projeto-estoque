"""Minimal Claude API starter for projeto-estoque."""

import sys

import anthropic

MODEL = "claude-opus-5"
SYSTEM_PROMPT = (
    "You are an assistant for an inventory (estoque) management system. "
    "Answer clearly and concisely."
)


def ask_claude(client: anthropic.Anthropic, question: str) -> str:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": question}],
        # If a safety classifier declines the request, the API re-runs it
        # on Anthropic's recommended fallback model within the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise RuntimeError(f"Request was declined (category: {category})")

    return "".join(block.text for block in response.content if block.type == "text")


def main() -> None:
    question = " ".join(sys.argv[1:]) or "Give me three tips for keeping stock levels accurate."

    # Reads ANTHROPIC_API_KEY (or an `ant auth login` profile) from the environment.
    client = anthropic.Anthropic()

    try:
        print(ask_claude(client, question))
    except anthropic.AuthenticationError:
        sys.exit("Invalid or missing API key. Set ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        sys.exit("Rate limited. Try again in a moment.")
    except anthropic.APIStatusError as e:
        sys.exit(f"API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Network error. Check your internet connection.")


if __name__ == "__main__":
    main()
