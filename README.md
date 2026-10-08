# Self-Correcting Agent

A Groq-powered Python agent that generates code, executes it in a separate subprocess, and sends failures back to the model for up to three correction attempts. Every run is recorded as JSON under `logs/`.

## Setup

```powershell
cd self_correcting_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` in `.env`. You may optionally set `GROQ_MODEL`; otherwise the agent selects the first supported model from its preference list that is available to the account.

## Usage

Run the default reverse-string task:

```powershell
python agent.py
```

Run a custom task:

```powershell
python agent.py "Write a function is_even(n) and include assertions for 2 and 3"
```

Run the live integration suite:

```powershell
python test_agent.py
```

The suite sends five prompts to Groq and may consume API quota. Logs and temporary sandbox files are intentionally ignored by Git.

## Execution model

1. The model returns Python source only.
2. Markdown fences are removed if the model adds them.
3. The source is written to `temp_execution/run_sandbox.py` and executed with the current Python interpreter.
4. Assertion errors, runtime errors, and timeouts are returned to the model as correction feedback.
5. The final attempts and execution output are saved to a timestamped JSON log.

The subprocess and timeout reduce accidental impact, but this is not a hardened security sandbox. Do not run generated code while sensitive credentials or valuable files are accessible.

