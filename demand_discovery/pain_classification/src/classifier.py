"""ClothScout module; migrated without changing business thresholds."""
import re
from runtime_support.text_identity.src.identity import normalized
from demand_discovery.pain_classification.src.rules import RULES

def classify(text):
    t = normalized(text)
    if not t:
        return [], "empty", []
    if re.search(r"ignore (?:all |previous )?instructions|powershell|system prompt|执行命令|忽略.*指令", t):
        return [], "manual_review", ["instruction_like_source_text"]
    if re.search(r"[?？]|吗|^(?:are|is|do|does|did|can|could|would|will|should)\b", t) and not re.match(r"^(?:does not|did not) fit\b", t):
        return [], "manual_review", ["question_or_hypothetical"]
    remaining_negation = re.sub(r"does not fit|did not fit|not as flowy|not flowy|does not drape", "", t)
    if re.search(r"\b(?:not|never|no)\b|\b(?:aren|weren)['’]t\b", remaining_negation):
        if re.search(r"never received|not received|did not receive|never got|no recibido", t):
            return [], "delivery", []
        return [], "manual_review", ["negation_needs_review"]
    if re.search(r"\b(?:packaging|package|shipping|delivery|arriv\w*|waiting)\b|不太|没太|包装", t):
        return [], "manual_review", ["non_garment_context_or_negation"]
    # Qualifiers and double negation need language understanding beyond this rule slice.
    if re.search(r"\b(?:but|however|although|thought|expected|wish|would|isn['’]t|wasn['’]t)\b|不是|并不", t):
        return [], "manual_review", ["ambiguous_or_contrastive_language"]
    negated = re.search(r"\b(?:not|never)\s+(?:at all\s+)?(?:too|see[- ]through|itchy|shrank|shrunk)|\bno\s+(?:shrinkage|issue|problem)", t)
    if negated:
        return [], "manual_review", ["negation_needs_review"]
    hits = [{"issue": key, "quote": match.group(0), "start": match.start(), "end": match.end()}
            for key, pattern, _, _ in RULES
            if (match := re.search(pattern, t))]
    # Locate an exact excerpt in original text (normalization may change offsets).
    for hit in hits:
        pattern = next(pattern for key, pattern, _, _ in RULES if key == hit["issue"])
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hit.update(quote=match.group(0), start=match.start(), end=match.end())
        else:
            hit.update(quote=text, start=0, end=len(text))
    if hits:
        return hits, "specific_complaint", []
    if re.search(r"never received|not received|didn['’]t receive|did not receive|not delivered|never got|no recibido|未收到", t):
        return [], "delivery", []
    if re.fullmatch(r"(?:fits? perfectly|true to size)[.!\s]*", t):
        return [], "positive_fit", []
    if re.search(r"\b(?:love|beautiful|great|like it)\b|好看", t):
        return [], "praise_or_unclear", []
    return [], "manual_review", ["uncovered_expression"]
