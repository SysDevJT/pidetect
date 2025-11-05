import aiohttp
import asyncio
import base64
import json
import logging
from ..config import Config
from ..utils.helpers import build_api_url, safe_trim, extract_choice_content

logger = logging.getLogger(__name__)

async def analyze_with_lmstudio_async(b64_image):
    if not (Config.LMSTUDIO_URL and Config.LMSTUDIO_MODEL):
        return {"status": "disabled", "reason": "LMSTUDIO_URL or LMSTUDIO_MODEL not set"}

    url = build_api_url(Config.LMSTUDIO_URL, "chat/completions")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Let op: nu vragen we expliciet om 3 velden in de JSON
    sys_msg = (
        "You are a vision-to-JSON extractor. "
        "Return ONLY compact JSON with three fields: objects_present, actions_present, and summary_text. "
        "objects_present: array of concise generic nouns in snake_case (e.g., desk, computer_keyboard, glasses, tape). "
        "actions_present: array of concise present-tense verb phrases in snake_case (e.g., typing, sitting, using_phone). "
        "summary_text: one concise natural-language sentence describing the scene (no JSON, just plain text, max ~40 words). "
        "No duplicates, no negations, no counts, no environment phrases, no extra top-level fields, no extra text outside JSON."
    )
    user_rules = (
        "Rules:\n"
        "1) Only what is visibly present.\n"
        "2) Prefer generic classes over descriptions.\n"
        "3) Avoid vague environment terms.\n"
        "4) If unsure, omit.\n"
        "5) Output MUST be STRICT JSON and nothing else.\n"
        "6) JSON schema: {\"objects_present\": [...], \"actions_present\": [...], \"summary_text\": \"...\"}."
    )

    msg_content = [
        {"type": "text", "text": user_rules},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
    ]

    payload_openai = {
        "model": Config.LMSTUDIO_MODEL,
        "stream": False,
        "temperature": 0.0,
        "top_p": 0.1,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": msg_content},
        ],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload_openai, timeout=60) as resp:
                text = await resp.text()
                if resp.status // 100 != 2:
                    return {
                        "status": "error",
                        "error": f"HTTP {resp.status}",
                        "body": safe_trim(text),
                    }

                data = json.loads(text)
                content = extract_choice_content(data)

                parsed = None
                if content:
                    # 1) liefst: pure JSON
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        # 2) fallback: JSON-blok eruit vissen
                        start = content.find("{")
                        end = content.rfind("}")
                        if start != -1 and end != -1 and end > start:
                            try:
                                parsed = json.loads(content[start:end+1])
                            except json.JSONDecodeError:
                                parsed = None

                if isinstance(parsed, dict) and \
                   "objects_present" in parsed and "actions_present" in parsed and "summary_text" in parsed:
                    # schoon de tags nog op als je wilt (optioneel)
                    # hier laat ik ze zoals LM Studio ze geeft
                    return {
                        "status": "ok",
                        "parsed": parsed,
                        "summary": parsed.get("summary_text"),
                    }

                # Als JSON-pad niet werkt, val terug op je bestaande fallback
                return await _fallback_vision_call(url, headers, b64_image, text)

    except Exception as e:
        logger.warning(f"LM Studio request exception: {repr(e)}")
        return {"status": "error", "error": f"Request exception: {repr(e)}"}


async def obsolete_analyze_with_lmstudio_async(b64_image):
    if not (Config.LMSTUDIO_URL and Config.LMSTUDIO_MODEL):
        return {"status": "disabled", "reason": "LMSTUDIO_URL or LMSTUDIO_MODEL not set"}

    url = build_api_url(Config.LMSTUDIO_URL, "chat/completions")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    sys_msg = (
        "You are a vision-to-JSON extractor. "
        "Return ONLY compact JSON with two arrays: objects_present and actions_present. "
        "Object labels should be concise generic nouns in snake_case. "
        "Actions should be concise present-tense verb phrases in snake_case. "
        "No duplicates, no negations, no counts, no environment phrases, no extra text."
    )
    user_rules = (
        "Rules:\n"
        "1) Only what is visibly present.\n"
        "2) Prefer generic classes over descriptions.\n"
        "3) Avoid vague environment terms.\n"
        "4) If unsure, omit.\n"
        "5) Output MUST be STRICT JSON and nothing else."
    )
    msg_content = [
        {"type": "text", "text": user_rules},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
    ]

    payload_openai = {
        "model": Config.LMSTUDIO_MODEL, "stream": False, "temperature": 0.0,
        "top_p": 0.1, "max_tokens": 256,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": msg_content},
        ],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload_openai, timeout=60) as resp:
                text = await resp.text()
                if resp.status // 100 != 2:
                    return {"status": "error", "error": f"HTTP {resp.status}", "body": safe_trim(text)}

                data = json.loads(text)
                content = extract_choice_content(data)

                if content:
                    try:
                        parsed = json.loads(content)
                        return {"status": "ok", "parsed": parsed}
                    except json.JSONDecodeError:
                        # Fallback for content that is not pure JSON
                        start = content.find("{")
                        end = content.rfind("}")
                        if start != -1 and end != -1 and end > start:
                            try:
                                parsed = json.loads(content[start:end+1])
                                return {"status": "ok", "parsed": parsed}
                            except json.JSONDecodeError:
                                pass # Fall through to fallback

                # If JSON parsing fails, go to fallback
                return await _fallback_vision_call(url, headers, b64_image, text)

    except Exception as e:
        logger.warning(f"LM Studio request exception: {repr(e)}")
        return {"status": "error", "error": f"Request exception: {repr(e)}"}

async def _fallback_vision_call(url, headers, b64_image, prev_error_body=None):
    payload_fallback = {
        "model": Config.LMSTUDIO_MODEL, "stream": False, "temperature": 0.2, "max_tokens": 400,
        "messages": [
            {"role": "system", "content": "You are a concise vision assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe the scene, objects and actions."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
            ]}
        ],
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload_fallback, timeout=60) as resp:
                text = await resp.text()
                if resp.status // 100 != 2:
                    return {"status": "error", "error": f"HTTP {resp.status}", "body": safe_trim(text)}

                data = json.loads(text)
                content = extract_choice_content(data)
                if content:
                    return {"status": "ok", "summary": content}

                # If no content, return the error body from the original JSON attempt if available
                return {"status": "error", "error": "missing choices/content", "body": safe_trim(prev_error_body or text)}

    except Exception as e:
        logger.warning(f"Fallback vision call exception: {repr(e)}")
        return {"status": "error", "error": f"Fallback request exception: {repr(e)}"}

def analyze_with_lmstudio(b64_image):
    try:
        return asyncio.run(analyze_with_lmstudio_async(b64_image))
    except RuntimeError:
        logger.exception("Asyncio loop issue while analyzing with LM Studio")
        return {"status": "error", "error": "asyncio loop problem"}
