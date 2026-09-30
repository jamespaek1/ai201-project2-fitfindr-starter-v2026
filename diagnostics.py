"""Deliberately exercise the three required failure modes and a full trace."""
import os
from pathlib import Path
import subprocess
import sys

import config


def main():
    root = Path(__file__).parent
    env = dict(os.environ, AI201_CACHE="0")
    good_key = env.get("GEMINI_API_KEY", "")
    if not good_key:
        raise RuntimeError("Configure GEMINI_API_KEY before running diagnostics.")
    bad_env = dict(env)
    # Corrupt exactly one character in this child only. Never edit or print .env.
    bad_env["GEMINI_API_KEY"] = good_key[:-1] + ("A" if good_key[-1] != "A" else "B")
    cases = [
        ("empty_search", ["designer ballgown size XXS under $5", "--trace"], env),
        ("empty_wardrobe", ["vintage graphic tee under $30, size M", "--empty-wardrobe", "--trace"], env),
        ("model_unavailable", ["vintage graphic tee under $30, size M", "--trace"], bad_env),
        ("happy_trace", ["vintage graphic tee under $30, size M", "--trace"], env),
    ]
    for name, args, child_env in cases:
        run = subprocess.run([sys.executable, "app.py", "ask", *args], cwd=root,
                             env=child_env, capture_output=True, text=True, timeout=180)
        output = run.stdout + run.stderr
        for key in (good_key, bad_env["GEMINI_API_KEY"]):
            output = output.replace(key, "[REDACTED]")
        path = root / "results" / f"unit4_{name}.txt"
        path.write_text(output, encoding="utf-8")
        print(f"{name}: exit {run.returncode}; saved {path.name}", flush=True)
    print("The original .env was never modified; the final happy run uses the original key.")


if __name__ == "__main__":
    main()
