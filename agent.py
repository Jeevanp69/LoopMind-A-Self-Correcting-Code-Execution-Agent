import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are an autonomous Python coding agent.
Your objective:
1. Write executable Python code that accomplishes the task AND passes all embedded assert statements.
2. Return ONLY clean Python code. Do NOT output explanations, introductory text, or markdown code fences.
3. If provided with an execution failure or traceback from a previous attempt, analyze the error and output the complete revised Python code that fixes the bug.
"""

MODEL_PREFERENCES = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
)

def clean_code(raw_text: str) -> str:
    """Strips markdown backticks and formatting wrappers."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:python)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def resolve_model(client: Groq, requested_model: str | None = None) -> str:
    """Use an explicit model or choose one currently available to the API key."""
    if requested_model:
        return requested_model

    available_models = {model.id for model in client.models.list().data}
    for candidate in MODEL_PREFERENCES:
        if candidate in available_models:
            return candidate

    raise RuntimeError(
        "No supported Groq text model is available for this API key. "
        "Set GROQ_MODEL in .env to a model listed in the Groq console."
    )

def execute_sandboxed_code(code: str, timeout: int = 7) -> dict:
    """
    Executes generated code in an isolated subprocess with timeout protection.
    Never uses eval() or exec() inside the host runtime.
    """
    temp_dir = "temp_execution"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = os.path.join(temp_dir, "run_sandbox.py")

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code + "\n")

    try:
        proc = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
            "error_type": "Runtime/Assertion Error" if proc.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds (potential infinite loop).",
            "returncode": -1,
            "error_type": "TimeoutExpired"
        }
    except OSError as error:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(error),
            "returncode": -1,
            "error_type": "ExecutionError"
        }

def run_agent_loop(task_description: str, max_attempts: int = 3) -> dict:
    """
    The Execute, Observe, Self-Correct Loop.
    Maintains message history so the model understands prior mistakes.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found in environment.", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)
    model = resolve_model(client, os.getenv("GROQ_MODEL"))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task_description}
    ]

    history_log = {
        "task": task_description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempts": [],
        "passed": False
    }

    print("\n" + "=" * 65)
    print(f"TASK: {task_description}")
    print("=" * 65)

    for attempt in range(1, max_attempts + 1):
        print(f"\n[Attempt {attempt}/{max_attempts}] Querying LLM...")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        raw_code = response.choices[0].message.content
        code = clean_code(raw_code)

        print(f"[Attempt {attempt}] Executing code in isolated subprocess...")
        result = execute_sandboxed_code(code)

        attempt_record = {
            "attempt": attempt,
            "code": code,
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"]
        }
        history_log["attempts"].append(attempt_record)

        print("-" * 40)
        print("GENERATED CODE:")
        print(code)
        print("-" * 40)

        if result["success"]:
            print(f"[✓ PASS] Attempt {attempt} executed cleanly without errors!")
            if result["stdout"]:
                print(f"Output:\n{result['stdout']}")
            history_log["passed"] = True
            break
        else:
            print(f"[✗ FAIL] Attempt {attempt} failed.")
            print(f"Captured Error:\n{result['stderr']}")

            if attempt < max_attempts:
                print("[↻] Feedback piped to agent for self-correction...")
                # Append assistant attempt and the user/environment feedback
                messages.append({"role": "assistant", "content": code})
                feedback = (
                    f"Execution failed on attempt {attempt}.\n"
                    f"Error traceback:\n{result['stderr']}\n\n"
                    "Please diagnose this error and output only the complete corrected Python code."
                )
                messages.append({"role": "user", "content": feedback})
            else:
                print(f"[!] Reached max attempts ({max_attempts}). Failed to self-correct.")

    # Save log to logs directory
    os.makedirs("logs", exist_ok=True)
    log_file = os.path.join(
        "logs", f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history_log, f, indent=2)

    return history_log

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = (
            "Write a function reverse_string(s) that reverses a string. "
            "Must pass: assert reverse_string('agent') == 'tnega' and assert reverse_string('') == ''"
        )
    run_agent_loop(task)