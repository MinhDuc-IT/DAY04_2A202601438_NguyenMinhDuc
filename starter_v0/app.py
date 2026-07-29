from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import now_iso, run_model_tool_loop, safe_slug, write_transcript


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"


load_lab_env(ROOT)


def _render_rounds(rounds: list[dict[str, Any]]) -> None:
    for r in rounds:
        st.subheader(f"Round {r.get('round')}")
        st.write("Assistant text:")
        st.code(r.get("assistant_text") or "", language="text")
        st.write("Tool calls:")
        st.json(r.get("tool_calls", []))
        st.write("Tool results:")
        st.json(r.get("tool_results", []))


def main() -> None:
    st.set_page_config(page_title="Paper Scout Research Agent", layout="wide")
    st.title("Paper Scout Research Agent (Day04 Lab)")

    st.sidebar.header("Run settings")
    provider = st.sidebar.selectbox("Provider", options=["openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.sidebar.text_input("Artifact version label", value="v3")
    model = st.sidebar.text_input("Model (optional)", value="")
    max_tool_rounds = st.sidebar.slider("Max tool rounds", min_value=1, max_value=6, value=4)

    st.sidebar.markdown("---")
    user_text = st.text_area(
        "User request",
        value="Tìm 3 paper arXiv về retrieval augmented generation evaluation, sau đó trích method/results cho paper phù hợp.",
        height=120,
    )

    run_clicked = st.button("Run")

    if not run_clicked:
        return

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)

    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    provider_obj = make_provider(provider)
    selected_model = model.strip() or getattr(provider_obj, "default_model", None)

    transcript_id = "_".join([
        safe_slug(version),
        safe_slug(provider),
        __import__("datetime").datetime.now().strftime("%Y%m%dT%H%M%S%f"),
    ])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider_obj,
            messages=messages,
            tools=openai_tools,
            model=selected_model,
            max_tool_rounds=max_tool_rounds,
        )
        turn_record["status"] = result.get("status")
        turn_record["assistant_text"] = result.get("assistant_text")
        turn_record["rounds"] = result.get("rounds", [])
        turn_record["tool_events"] = result.get("tool_events", [])
        turn_record["ended_at"] = now_iso()
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {str(exc)}",
            "ended_at": now_iso(),
        })

    st.subheader("Final output")
    st.write(f"Status: {turn_record.get('status')}")
    st.code(turn_record.get("assistant_text") or "", language="text")

    st.subheader("Tool trace (evidence)")
    _render_rounds(turn_record.get("rounds", []))

    st.subheader("Transcript")
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 0,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [turn_record],
    }
    write_transcript(transcript_path, transcript)
    st.success(f"Transcript saved: {transcript_path}")


if __name__ == "__main__":
    main()

