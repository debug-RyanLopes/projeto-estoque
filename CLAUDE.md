# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An early-stage project (single script) that calls the Claude API to act as an assistant for
an inventory (estoque) management system. There is no inventory data model, storage, or
tooling yet — `main.py` sends one free-text question to Claude and prints the answer.

## Setup and running

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python main.py "How should I organize SKUs for a small warehouse?"
```

There is no test suite or lint config in this repo yet.

## Architecture

- [main.py](main.py) — entire application. `ask_claude()` sends a single request via
  `client.beta.messages.create()` and returns the concatenated text blocks; `main()` wires up
  the CLI argument, the `Anthropic()` client, and top-level error handling for the SDK's typed
  exceptions (auth, rate limit, API status, connection).
- Model and system prompt are set as module-level constants (`MODEL`, `SYSTEM_PROMPT`) in
  `main.py`, not read from config — change them there directly.
- The request enables adaptive thinking and opts into server-side model fallback
  (`fallbacks="default"` under the `server-side-fallback-2026-07-01` beta): if Claude's safety
  classifier declines a request, the API retries it on a recommended backup model
  automatically. `response.stop_reason == "refusal"` is checked before reading `response.content`
  because a fallback can still itself refuse.
- Credentials are read from the environment (`ANTHROPIC_API_KEY`), never hardcoded.

## Extending this project

The natural next step when adding real inventory features is to give Claude tools (e.g.
`get_product`, `list_low_stock`) via the `tools` parameter rather than only sending free text —
there is no tool-use loop implemented yet.
