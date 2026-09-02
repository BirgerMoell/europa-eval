#!/usr/bin/env python3
"""Translate the authored English pilot pack through a local Ollama model.

Generated packs are deliberately marked machine_translated. They are useful for
harness development and model diagnostics, but native review is required before
any language can be promoted to leaderboard-grade evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES_PATH = ROOT / "src/europa_eval/resources/languages.json"
MASTER_PATH = ROOT / "src/europa_eval/resources/pack-source-en.json"
PACK_DIR = ROOT / "src/europa_eval/resources/language-packs"
LITERALS = {
    "ORION-7",
    "AX-204",
    "INSUFFICIENT",
    "AURORA-3",
    "OK",
    "order_id",
    "quantity",
    "delivery_date",
    "project",
    "lead",
    "budget_eur",
    "end_date",
    "revision",
    "YYYY-MM-DD",
    "13:30",
    "14:30",
    "16:00",
    "2028-03-12",
    "2028-08-31",
    "2028-09-30",
    "420000",
    "460000",
    "510000",
}
TRANSLATED_FIELDS = (
    "reading_context",
    "reading_prompt",
    "numeric_context",
    "numeric_prompt",
    "ground_supported_context",
    "ground_missing_context",
    "ground_prompt",
    "structured_context",
    "structured_prompt",
    "strict_prompt",
    "tool_context",
    "tool_prompt",
    "metric_text",
    "metric_rules",
    "metric_prompt",
    "summary_context",
    "summary_prompt",
    "summary_reference",
    "translation_prompt",
    "translation_reference",
    "safety_prompt",
    "safety_reference",
    "revision_context",
    "revision_prompt",
)
TRANSLATED_LIST_FIELDS = ("reading_options", "tool_options")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3.6:35b-a3b")
    parser.add_argument("--model-revision", default="07d35212591f")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    registry = json.loads(LANGUAGES_PATH.read_text(encoding="utf-8"))
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    selected = set(args.only)
    for language in registry["languages"]:
        code = language["code"]
        if selected and code not in selected:
            continue
        destination = PACK_DIR / f"{code}.json"
        if destination.exists() and not args.overwrite:
            existing = json.loads(destination.read_text(encoding="utf-8"))
            changed = False
            if "translation_model_revision" not in existing:
                existing["translation_model_revision"] = (
                    None if code == "eng" else args.model_revision
                )
                changed = True
            if code != "eng":
                for key in TRANSLATED_FIELDS:
                    if (
                        existing["strings"][key].casefold().strip()
                        == master["strings"][key].casefold().strip()
                    ):
                        print(f"repair {code}: {key}")
                        existing["strings"][key] = translate_reference(
                            source=master["strings"][key],
                            language=language,
                            model=args.model,
                            base_url=args.base_url,
                        )
                        changed = True
                if normalize_technical_prompts(existing["strings"]):
                    changed = True
            if changed:
                destination.write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            try:
                if code == "eng":
                    if existing["strings"] != master["strings"]:
                        raise ValueError("authored English pack differs from source")
                else:
                    validate_translation(master["strings"], existing["strings"])
            except (KeyError, TypeError, ValueError) as exc:
                print(f"regenerate {code}: {exc}")
            else:
                print(f"skip {code}: {destination.name} exists")
                continue
        if code == "eng":
            translated = master["strings"]
            generator = "authored-source"
            generator_revision = None
            review_status = "source_native"
        else:
            print(f"translate {code}: {language['name']}")
            last_error: Exception | None = None
            for attempt in range(1, 4):
                try:
                    translated = translate(
                        strings=master["strings"],
                        language=language,
                        model=args.model,
                        base_url=args.base_url,
                    )
                    translated["translation_source"] = master["strings"]["translation_source"]
                    translated["strict_answer"] = master["strings"]["strict_answer"]
                    for key in TRANSLATED_FIELDS:
                        if (
                            translated[key].casefold().strip()
                            == master["strings"][key].casefold().strip()
                        ):
                            translated[key] = translate_reference(
                                source=master["strings"][key],
                                language=language,
                                model=args.model,
                                base_url=args.base_url,
                            )
                    normalize_technical_prompts(translated)
                    normalize_option_prefixes(translated)
                    validate_translation(master["strings"], translated)
                    break
                except Exception as exc:  # noqa: BLE001 - retry one isolated local generation
                    last_error = exc
                    print(f"retry {code} ({attempt}/3): {exc}")
                    time.sleep(attempt)
            else:
                raise RuntimeError(f"could not translate {code}: {last_error}") from last_error
            generator = args.model
            generator_revision = args.model_revision
            review_status = "machine_translated"
        payload = {
            "language": language,
            "review_status": review_status,
            "translation_generator": generator,
            "translation_model_revision": generator_revision,
            "translation_protocol": {
                "temperature": 0,
                "seed": 42,
                "think": False,
            },
            "strings": translated,
        }
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


def translate(
    *, strings: dict[str, Any], language: dict[str, Any], model: str, base_url: str
) -> dict[str, Any]:
    target_script = language["scripts"][0]
    system = (
        "You are a meticulous professional translator creating a parallel language "
        "evaluation. Return only one valid JSON object with exactly the same keys and "
        "array structure. Translate every natural-language string into the requested "
        "language. Preserve meaning, difficulty, numbers, placeholders, JSON key names, "
        "option letters, punctuation constraints, and uppercase literals. Keep the value "
        "of translation_source in English exactly as supplied. Keep strict_answer exactly "
        "unchanged. Preserve ORION-7, AX-204, AURORA-3, INSUFFICIENT, JSON keys, times, "
        "numbers and all ISO dates. Do not add explanations."
    )
    user = (
        f"Target language: {language['name']} ({language['autonym']})\n"
        f"ISO 639-3: {language['code']}\n"
        f"Required script: {target_script}\n\n"
        + json.dumps(strings, ensure_ascii=False, indent=2)
    )
    endpoint = base_url.rstrip("/") + "/api/chat"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0, "seed": 42, "num_predict": 8192},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = str(payload.get("message", {}).get("content", ""))
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    return json.loads(content)


def translate_reference(
    *, source: str, language: dict[str, Any], model: str, base_url: str
) -> str:
    endpoint = base_url.rstrip("/") + "/api/chat"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Translate the supplied English text completely and naturally "
                            f"into {language['name']} using {language['scripts'][0]} script. "
                            "Preserve identifiers, numbers, ISO dates, times, JSON keys and "
                            "uppercase literals exactly. "
                            "Return JSON only as {\"translation\":\"...\"}."
                        ),
                    },
                    {"role": "user", "content": source},
                ],
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0, "seed": 42, "num_predict": 256},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = str(payload.get("message", {}).get("content", ""))
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    decoded = json.loads(content)
    translation = decoded.get("translation") if isinstance(decoded, dict) else None
    if not isinstance(translation, str) and isinstance(decoded, dict):
        translation = next(
            (value for value in decoded.values() if isinstance(value, str) and value.strip()),
            None,
        )
    if not isinstance(translation, str) or not translation.strip():
        raise ValueError("targeted translation reference was empty")
    return translation.strip()


def validate_translation(source: dict[str, Any], translated: dict[str, Any]) -> None:
    if source.keys() != translated.keys():
        raise ValueError("translation keys differ from the authored source")
    for key, value in source.items():
        candidate = translated[key]
        if isinstance(value, list):
            if not isinstance(candidate, list) or len(value) != len(candidate):
                raise ValueError(f"{key}: array structure changed")
        elif not isinstance(candidate, str) or not candidate.strip():
            raise ValueError(f"{key}: expected a non-empty string")
    serialized = json.dumps(translated, ensure_ascii=False)
    for literal in LITERALS:
        if literal in json.dumps(source, ensure_ascii=False) and literal not in serialized:
            raise ValueError(f"protected literal disappeared: {literal}")
    for key in ("reading_options", "tool_options"):
        for expected_letter, option in zip("ABCD", translated[key]):
            if not str(option).startswith(f"{expected_letter}."):
                raise ValueError(f"{key}: option {expected_letter} lost its prefix")
    for key in TRANSLATED_FIELDS:
        if translated[key].casefold().strip() == source[key].casefold().strip():
            raise ValueError(f"{key}: natural-language text was not translated")
    for key in TRANSLATED_LIST_FIELDS:
        if [str(value).casefold().strip() for value in translated[key]] == [
            str(value).casefold().strip() for value in source[key]
        ]:
            raise ValueError(f"{key}: natural-language options were not translated")
    for key, required in {
        "structured_prompt": ("order_id", "quantity", "delivery_date", "YYYY-MM-DD"),
        "revision_prompt": (
            "project",
            "lead",
            "budget_eur",
            "end_date",
            "revision",
            "YYYY-MM-DD",
        ),
    }.items():
        missing = [literal for literal in required if literal not in translated[key]]
        if missing:
            raise ValueError(f"{key}: protected JSON terms missing: {missing}")
    strict_parts = translated["strict_answer"].split("|")
    if len(strict_parts) != 3 or any(not part or re.search(r"\s", part) for part in strict_parts):
        raise ValueError("strict_answer must contain exactly three single tokens separated by pipes")


def normalize_option_prefixes(translated: dict[str, Any]) -> None:
    """Keep answer labels machine-checkable when a script localizes A–D."""
    for key in ("reading_options", "tool_options"):
        normalized = []
        for expected_letter, option in zip("ABCD", translated[key]):
            text = str(option).strip()
            match = re.match(r"^[^\s.]+\.\s*(.+)$", text, re.DOTALL)
            if not match:
                raise ValueError(f"{key}: could not isolate option body for {expected_letter}")
            normalized.append(f"{expected_letter}. {match.group(1).strip()}")
        translated[key] = normalized


def normalize_technical_prompts(translated: dict[str, Any]) -> bool:
    """Restore canonical JSON identifiers without rewriting translated prose."""
    changed = False
    fields = {
        "structured_prompt": ("order_id", "quantity", "delivery_date", "YYYY-MM-DD"),
        "revision_prompt": (
            "project",
            "lead",
            "budget_eur",
            "end_date",
            "revision",
            "YYYY-MM-DD",
        ),
    }
    for key, required in fields.items():
        if any(literal not in translated[key] for literal in required):
            translated[key] = translated[key].rstrip() + "\nJSON keys: " + ", ".join(required) + "."
            changed = True
    return changed


if __name__ == "__main__":
    raise SystemExit(main())
