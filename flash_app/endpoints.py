from runpod_flash import Endpoint


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@Endpoint(name="buddy-extract-accessibility-claims", cpu="cpu3c-1-2", workers=(0, 1))
async def extract_accessibility_claims(input_data: dict) -> dict:
    """Extract accessibility evidence claims from scraped web/review/photo text."""
    import re
    from datetime import datetime

    source_type = input_data.get("source_type", "web")
    source_url = input_data.get("source_url")
    title = input_data.get("title")
    raw_items = input_data.get("items") or []
    if input_data.get("text"):
        raw_items.append({"text": input_data["text"], "title": title, "url": source_url})

    feature_patterns = {
        "entrance": [
            r"\b(step[- ]?free|no steps?|ramp|wheelchair entrance|accessible entrance|level entrance)\b",
            r"\b(stairs?|steps?|not wheelchair accessible|no ramp)\b",
        ],
        "restroom": [
            r"\b(accessible restroom|ada restroom|wheelchair restroom|bathroom access)\b",
            r"\b(no public restroom|restroom.*stairs|bathroom.*not accessible)\b",
        ],
        "seating": [
            r"\b(wheelchair seating|accessible seating|table access|wide aisle|clear path)\b",
            r"\b(tight seating|narrow aisle|bar stool only|high top only)\b",
        ],
        "route": [
            r"\b(elevator|accessible route|wide doorway|curb cut|path of travel)\b",
            r"\b(narrow doorway|blocked path|upstairs only|basement only)\b",
        ],
        "temporary_blocker": [
            r"\b(construction|temporar(?:y|ily)|blocked|out of service|broken elevator)\b",
        ],
        "hours": [r"\b(open|closed|hours?|today|tonight)\b"],
    }
    negative_words = re.compile(
        r"\b(no|not|without|unavailable|blocked|broken|stairs?|steps?|narrow|tight|closed|upstairs only)\b",
        re.I,
    )

    evidence = []
    for item in raw_items:
        text = str(item.get("text") or item.get("claim") or "").strip()
        if not text:
            continue
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        for sentence in sentences:
            lowered = sentence.lower()
            matched_feature = "unknown"
            for feature, patterns in feature_patterns.items():
                if any(re.search(pattern, lowered, re.I) for pattern in patterns):
                    matched_feature = feature
                    break
            if matched_feature == "unknown":
                continue

            polarity = "contradicts_access" if negative_words.search(sentence) else "supports_access"
            if matched_feature in {"temporary_blocker", "hours"} and not negative_words.search(sentence):
                polarity = "unknown"
            confidence = 0.72 if matched_feature != "unknown" else 0.35
            if item.get("source_type") in {"official", "call"} or source_type in {"official", "call"}:
                confidence += 0.12

            evidence.append(
                {
                    "source_type": item.get("source_type") or source_type,
                    "source_url": item.get("url") or source_url,
                    "source_timestamp": item.get("source_timestamp"),
                    "collected_at": datetime.utcnow().isoformat(),
                    "title": item.get("title") or title,
                    "claim": sentence,
                    "feature": matched_feature,
                    "polarity": polarity,
                    "confidence": round(_clamp(confidence), 2),
                    "image_url": item.get("image_url"),
                    "raw": item,
                }
            )

    return {"evidence": evidence, "claim_count": len(evidence)}


@Endpoint(name="buddy-score-accessibility-status", cpu="cpu3c-1-2", workers=(0, 1))
async def score_accessibility_status(input_data: dict) -> dict:
    """Score preliminary accessibility status and identify missing critical facts."""
    evidence = input_data.get("evidence") or []
    needs = input_data.get("needs") or {}
    required = {
        "entrance": needs.get("step_free_entrance", True),
        "restroom": needs.get("accessible_restroom", True),
        "seating": needs.get("wheelchair_seating_or_path", True),
        "route": needs.get("wheelchair_seating_or_path", True),
        "temporary_blocker": needs.get("avoid_temporary_blockers", True),
    }

    scores = {feature: 0.0 for feature, enabled in required.items() if enabled}
    support = 0
    contradictions = 0
    for item in evidence:
        feature = item.get("feature", "unknown")
        if feature not in scores:
            continue
        weight = float(item.get("confidence") or 0.0)
        if item.get("polarity") == "supports_access":
            scores[feature] += weight
            support += 1
        elif item.get("polarity") == "contradicts_access":
            scores[feature] -= weight
            contradictions += 1

    missing = []
    questions = {
        "entrance": "Is there a step-free entrance that a wheelchair user can use today?",
        "restroom": "Is there an accessible customer restroom available today?",
        "seating": "Is there wheelchair-accessible seating or a clear path to the main service area?",
        "route": "Is the route from the entrance to the service area wide and step-free?",
        "temporary_blocker": "Are there any temporary blockers today, like construction or a broken elevator?",
    }
    for feature, score in scores.items():
        if abs(score) < 0.5:
            missing.append(
                {
                    "feature": feature,
                    "question": questions[feature],
                    "reason": "No recent high-confidence evidence confirms this need.",
                    "critical": feature in {"entrance", "restroom", "seating"},
                }
            )

    if contradictions:
        preliminary_status = "red" if contradictions >= support else "yellow"
    elif missing:
        preliminary_status = "yellow"
    elif support:
        preliminary_status = "green"
    else:
        preliminary_status = "unknown"

    confidence = _clamp((support + contradictions) / max(len(scores) * 2, 1))
    return {
        "enough_evidence": not missing and preliminary_status in {"green", "red"},
        "missing_facts": missing,
        "evidence": evidence,
        "preliminary_status": preliminary_status,
        "preliminary_summary": (
            f"{support} supporting and {contradictions} conflicting accessibility claims found; "
            f"{len(missing)} critical facts still need confirmation."
        ),
        "confidence": round(confidence, 2),
    }


@Endpoint(name="buddy-plan-call-questions", cpu="cpu3c-1-2", workers=(0, 1))
async def plan_call_questions(input_data: dict) -> dict:
    """Create a concise venue call plan from missing facts and user needs."""
    place = input_data.get("place") or {}
    missing_facts = input_data.get("missing_facts") or []
    requested_for = input_data.get("requested_for")
    needs = input_data.get("needs") or {}

    questions = []
    if not missing_facts:
        missing_facts = [
            {
                "feature": "entrance",
                "question": "Is there a step-free entrance that a wheelchair user can use today?",
                "reason": "Confirming visit-critical access.",
                "critical": True,
            }
        ]
    for fact in missing_facts:
        question = fact.get("question")
        if question and question not in questions:
            questions.append(question)

    if needs.get("avoid_temporary_blockers", True):
        blocker_question = "Are there any temporary accessibility blockers today, such as construction, blocked paths, or an out-of-service elevator?"
        if blocker_question not in questions:
            questions.append(blocker_question)

    call_context = f"calling {place.get('name') or place.get('query') or 'the venue'}"
    if requested_for:
        call_context += f" for a visit around {requested_for}"

    return {
        "opening": "Hi, I am calling to quickly confirm accessibility before someone visits.",
        "call_context": call_context,
        "questions": questions[:6],
        "closing": "Thank you, that helps us give the visitor accurate guidance.",
        "metadata": {"place": place, "requested_for": requested_for},
    }


@Endpoint(name="buddy-parse-voice-transcript", cpu="cpu3c-1-2", workers=(0, 1))
async def parse_voice_transcript(input_data: dict) -> dict:
    """Parse a real call transcript into structured accessibility facts."""
    import re

    transcript = input_data.get("transcript") or []
    text = "\n".join(str(turn.get("text", "")) for turn in transcript if turn.get("speaker") != "buddy")
    lowered = text.lower()

    def classify(positive_patterns: list[str], negative_patterns: list[str]) -> str:
        if any(re.search(pattern, lowered) for pattern in negative_patterns):
            return "no"
        if any(re.search(pattern, lowered) for pattern in positive_patterns):
            return "yes"
        return "unknown"

    entrance = classify(
        [r"\b(no steps?|step[- ]?free|ramp|level entrance|accessible entrance)\b"],
        [r"\b(steps?|stairs?|no ramp|not accessible entrance|entrance.*not wheelchair)\b"],
    )
    restroom = classify(
        [r"\b(accessible restroom|ada restroom|wheelchair.*bathroom|bathroom.*accessible)\b"],
        [r"\b(no accessible restroom|no public restroom|restroom.*not accessible|bathroom.*stairs)\b"],
    )
    seating = classify(
        [r"\b(wheelchair seating|accessible seating|clear path|wide aisle|room for wheelchair)\b"],
        [r"\b(no wheelchair seating|tight seating|narrow aisle|high top only|bar stool only)\b"],
    )

    blockers = []
    for pattern in [r"construction[^.?!]*", r"blocked[^.?!]*", r"elevator[^.?!]*(?:broken|out of service)", r"temporary[^.?!]*"]:
        blockers.extend(match.group(0).strip() for match in re.finditer(pattern, lowered))

    known = [entrance, restroom, seating].count("yes") + [entrance, restroom, seating].count("no")
    needs_followup = known < 3 or any(value == "unknown" for value in [entrance, restroom, seating])
    confidence = _clamp((known / 3) * 0.78 + (0.12 if transcript else 0.0))
    notes = "Parsed from venue transcript." if transcript else "No transcript turns were provided."

    return {
        "step_free_entrance": entrance,
        "accessible_restroom": restroom,
        "wheelchair_seating_or_path": seating,
        "temporary_blockers": blockers[:5],
        "confidence": round(confidence, 2),
        "notes": notes,
        "needs_followup": needs_followup,
    }


@Endpoint(name="buddy-generate-local-render-payload", cpu="cpu3c-1-2", workers=(0, 1))
async def generate_local_render_payload(input_data: dict) -> dict:
    """Generate a final report and a local renderer payload for mobile clients."""
    from datetime import datetime, timedelta, timezone

    place = input_data.get("place") or {}
    analysis = input_data.get("analysis") or {}
    call_facts = input_data.get("call_facts") or {}
    evidence = input_data.get("evidence") or analysis.get("evidence") or []
    transcript = input_data.get("voice_transcript") or []

    status = analysis.get("preliminary_status", "unknown")
    fact_values = [
        call_facts.get("step_free_entrance"),
        call_facts.get("accessible_restroom"),
        call_facts.get("wheelchair_seating_or_path"),
    ]
    if "no" in fact_values:
        status = "red"
    elif fact_values and all(value == "yes" for value in fact_values):
        status = "green"
    elif any(value == "yes" for value in fact_values) or analysis.get("missing_facts"):
        status = "yellow"

    labels = {
        "step_free_entrance": "Step-free entrance",
        "accessible_restroom": "Accessible restroom",
        "wheelchair_seating_or_path": "Wheelchair seating or clear path",
    }
    confirmed = [label for key, label in labels.items() if call_facts.get(key) == "yes"]
    risks = [label for key, label in labels.items() if call_facts.get(key) == "no"]
    risks.extend(call_facts.get("temporary_blockers") or [])
    unknowns = [label for key, label in labels.items() if call_facts.get(key, "unknown") == "unknown"]
    unknowns.extend(fact.get("question") for fact in analysis.get("missing_facts", []) if fact.get("question"))

    place_name = place.get("name") or place.get("query") or "This place"
    summary = input_data.get("summary") or f"{place_name} is currently scored {status} for the requested access needs."
    recommendation_map = {
        "green": "Looks reasonable to visit, with normal day-of caution.",
        "yellow": "Proceed with caution and confirm unknowns before relying on the visit.",
        "red": "Access needs may not be met. Consider calling again or choosing another venue.",
        "unknown": "There is not enough reliable information yet to recommend a visit.",
    }
    expires_at = datetime.now(timezone.utc) + timedelta(hours=int(input_data.get("ttl_hours", 24)))
    confidence_values = [
        float(analysis.get("confidence") or 0.0),
        float(call_facts.get("confidence") or 0.0),
    ]
    confidence = max(confidence_values) if any(confidence_values) else 0.35

    report = {
        "status": status,
        "summary": summary,
        "recommendation": input_data.get("recommendation") or recommendation_map.get(status, recommendation_map["unknown"]),
        "confirmed_facts": confirmed,
        "risks": risks,
        "unknowns": unknowns,
        "evidence_ids": [item.get("id") for item in evidence if item.get("id")],
        "evidence": evidence,
        "voice_conversation_summary": input_data.get("voice_conversation_summary") or call_facts.get("notes"),
        "voice_transcript": transcript,
        "confidence": round(_clamp(confidence), 2),
        "expires_at": expires_at.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    local_render_payload = {
        "target": input_data.get("target", "react-native"),
        "component": "AccessibilityReport",
        "props": {
            "place": place,
            "status": status,
            "summary": report["summary"],
            "recommendation": report["recommendation"],
            "sections": [
                {"title": "Confirmed", "items": confirmed},
                {"title": "Risks", "items": risks},
                {"title": "Unknowns", "items": unknowns},
            ],
            "confidence": report["confidence"],
            "expiresAt": report["expires_at"],
        },
    }
    report["local_render_payload"] = local_render_payload
    report["render_payload"] = local_render_payload
    return report
