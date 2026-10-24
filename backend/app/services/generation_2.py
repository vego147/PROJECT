
import json
import re
import asyncio

from json_repair import repair_json
from ..config import settings


REQUIRED_FIELDS = (
    "article_title",
    "article",
    "title",
    "caption",
    "hashtags",
    "call_to_action",
    "image_prompt",
)


def parse_llm_response(raw: str) -> dict:
    """Parse JSON even when the model adds surrounding text or code fences."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("LLM returned an empty response")

    cleaned = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        raw.strip(),
        flags=re.IGNORECASE,
    )

    # Try normal JSON parsing first.
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = None

        # Find the first decodable JSON object without using a greedy
        # regex that breaks when the response contains nested objects.
        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(cleaned[index:])
                if isinstance(candidate, dict):
                    data = candidate
                    break
            except json.JSONDecodeError:
                continue

        # Last parsing attempt: repair malformed JSON.
        if data is None:
            data = repair_json(cleaned, return_objects=True)

    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")

    return data


def validate_and_normalize(data: dict) -> dict:
    """Reject incomplete packages instead of silently accepting bad output."""
    missing = [
        field for field in REQUIRED_FIELDS
        if field not in data or data[field] is None
    ]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Text fields must contain meaningful, non-empty strings.
    text_fields = (
        "article_title",
        "article",
        "title",
        "caption",
        "call_to_action",
        "image_prompt",
    )

    for field in text_fields:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid or empty field: {field}")
        data[field] = value.strip()

    MIN_ARTICLE_WORDS = 400
    MAX_ARTICLE_WORDS = 800

    article_words = re.findall(r"\b[\w'-]+\b", data["article"])
    word_count = len(article_words)

    if word_count < MIN_ARTICLE_WORDS:
        raise ValueError(
            f"Article is too short: {word_count} words. "
            f"Minimum required: {MIN_ARTICLE_WORDS} words."
        )

    if word_count > MAX_ARTICLE_WORDS:
        raise ValueError(
            f"Article is too long: {word_count} words. "
            f"Maximum allowed: {MAX_ARTICLE_WORDS} words."
        )

    hashtags = data["hashtags"]

    # Normalize a single string into a list when possible.
    if isinstance(hashtags, str):
        hashtags = re.findall(r"#[A-Za-z0-9_]+", hashtags)

    if not isinstance(hashtags, list):
        raise ValueError("Hashtags must be a list")

    hashtags = [
        tag.strip() if isinstance(tag, str) else ""
        for tag in hashtags
    ]
    hashtags = [
        tag if tag.startswith("#") else f"#{tag}"
        for tag in hashtags
        if tag and re.fullmatch(r"#?[A-Za-z0-9_]+", tag)
    ]

    # Deduplicate while preserving order.
    data["hashtags"] = list(dict.fromkeys(hashtags))[:8]

    if len(data["hashtags"]) < 5:
        raise ValueError("At least 5 valid hashtags are required")

    return data


def build_fallback(topic: str, sources: list[dict]) -> dict:
    """Retained fallback. This is explicitly NOT an LLM-generated package."""
    clean = topic.strip().rstrip(".!?") or "Untitled topic"

    evidence_text = " ".join(
        (
            source.get("extracted_content")
            or source.get("snippet")
            or ""
        )
        for source in sources[:3]
    )
    usable = re.sub(r"\s+", " ", evidence_text).strip()

    if usable:
        article = (
            f"# {clean}\n\n"
            f"{usable[:1400]}\n\n"
            "## What this means\n\n"
            f"The available material provides an initial starting point "
            f"for understanding {clean}. Verify dates, context, figures, "
            "and claims against the original publications before publishing.\n\n"
            "## Conclusion\n\n"
            "This is an automatically assembled fallback draft, "
            "not independently verified reporting."
        )
    else:
        article = (
            f"# {clean}\n\n"
            f"This is a fallback outline about {clean}. "
            "Source text was unavailable, so specific factual claims "
            "have been omitted. Research and verify primary sources "
            "before publication."
        )

    topic_tags = [
        "#" + re.sub(r"[^A-Za-z0-9_]", "", word).title()
        for word in clean.split()
    ]
    topic_tags = [tag for tag in topic_tags if len(tag) > 1]

    hashtags = list(dict.fromkeys(
        (topic_tags + ["#Insights", "#Research", "#Updates",
                       "#News", "#Analysis"])[:8]
    ))

    return {
        "article_title": f"{clean}: Key Developments and Context",
        "article": article,
        "title": f"A closer look at {clean}",
        "caption": (
            f"What the available source material says about {clean}. "
            "Check the original reporting and verify the claims "
            "before sharing."
        ),
        "hashtags": hashtags,
        "call_to_action": (
            "Read the sources, verify the details, and share your perspective."
        ),
        "image_prompt": (
            f"Create an editorial visual illustrating {clean}, "
            "based on available source context. Professional art direction, "
            "strong composition, landscape 16:9, no text, logos, or watermark."
        ),
    }


async def generate_copy(
    topic: str,
    platform: str,
    tone: str,
    sources: list[dict],
) -> tuple[dict, str, list[dict]]:

    stages = []
    max_attempts = 3

    extracted = [
        {
            "title": source.get("title"),
            "url": source.get("url"),
            "published_date": source.get("published_date"),
            "content": (
                source.get("extracted_content")
                or source.get("snippet")
                or ""
            )[:5000],
        }
        for source in sources[:5]
    ]

    evidence = json.dumps(extracted, ensure_ascii=False)[:18000]

    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=0.3,
                max_retries=2,
                timeout=45,
            )

            prompt = f"""
Create a factual content package about: {topic}
Platform: {platform}
Tone: {tone}

Use the supplied source text as evidence. Never invent facts, quotes,
statistics, dates, or claims. Be explicit about uncertainty.

Return ONLY one valid JSON object with exactly these keys:
{", ".join(REQUIRED_FIELDS)}

Requirements:
- article_title: a useful article headline
- article: at least 150 words when evidence allows, with headings
- title: a concise social media hook
- caption: platform-appropriate copy based on the evidence
- hashtags: an array of 5-8 relevant strings beginning with #
- call_to_action: a relevant action for the audience
- image_prompt: an original editorial visual, landscape 16:9,
  without text, logos, or watermarks

Every key is mandatory. Every text value must be non-empty.
SOURCE MATERIAL:
{evidence}
"""

            messages = [
                SystemMessage(content=(
                    "You are a careful journalist and social content editor. "
                    "Return valid JSON only. Follow the requested schema."
                )),
                HumanMessage(content=prompt),
            ]

            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    response = await llm.ainvoke(messages)

                    raw = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )

                    data = validate_and_normalize(
                        parse_llm_response(raw)
                    )

                    stages.append({
                        "name": "LLM article + social package",
                        "status": "completed",
                        "detail": (
                            f"Generated and validated using "
                            f"{settings.groq_model}; attempt {attempt}."
                        ),
                    })
                    stages.append({
                        "name": "Image prompt",
                        "status": "completed",
                        "detail": "Generated by the LLM and validated.",
                    })

                    return data, "groq", stages

                except Exception as exc:
                    last_error = exc
                    print(
                        f"Groq generation attempt {attempt}/"
                        f"{max_attempts} failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    # Give the model a chance to correct invalid output.
                    messages = [
                        SystemMessage(content=(
                            "Return one valid JSON object only. "
                            "All seven required fields must be present "
                            "and non-empty. Hashtags must be an array "
                            "containing at least five valid hashtags."
                        )),
                        HumanMessage(content=f"""
Your previous response failed validation:
{type(exc).__name__}: {exc}

Generate a COMPLETE corrected content package. Do not return
an explanation, a partial object, or only the missing fields.

Topic: {topic}
Platform: {platform}
Tone: {tone}

Required keys: {", ".join(REQUIRED_FIELDS)}
Source material:
{evidence}

Return JSON only.
"""),
                    ]

                    if attempt < max_attempts:
                        await asyncio.sleep(attempt)

            stages.append({
                "name": "LLM generation",
                "status": "failed",
                "detail": (
                    f"Groq failed validation or generation after "
                    f"{max_attempts} attempts: "
                    f"{type(last_error).__name__}"
                ),
            })

        except Exception as exc:
            print(f"Groq initialization failed: {type(exc).__name__}: {exc}")
            stages.append({
                "name": "LLM initialization",
                "status": "failed",
                "detail": f"{type(exc).__name__}: {exc}",
            })
    else:
        stages.append({
            "name": "LLM initialization",
            "status": "failed",
            "detail": "GROQ_API_KEY is missing or empty.",
        })

    # Last resort only. Never label fallback content as Groq output.
    fallback = build_fallback(topic, sources)

    stages.append({
        "name": "Fallback article + social package",
        "status": "warning",
        "detail": (
            "Fallback template used after LLM generation failed. "
            "This content was NOT generated by an LLM."
        ),
    })
    stages.append({
        "name": "Image prompt",
        "status": "warning",
        "detail": "Image prompt created by the fallback template.",
    })

    return fallback, "fallback", stages
