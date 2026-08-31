"""The Oracle's voice.

Turns a consultation document into what the Oracle actually *says* —
warm, domestic, cryptic-but-direct. She never answers the question.
She makes the asker hear their own answer.

Deterministic: the same cast always produces the same words. The seed
is the cast itself (judge bits + primary hexagram bits + odu bits), so
the voice feels like recognition, not randomness.

Structure of a voice:
    address   - an opening line (she greets you)
    words     - the reading, in kitchen language (2-3 short sentences)
    question  - ONE Socratic question that returns the choice to the asker
    cookie    - the catalyst line (advice is candy, not force)
    full      - everything joined, ready to speak aloud
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------- language

ADDRESSES = [
    "Sit down, dear.",
    "Come in. The kettle is already on.",
    "There you are.",
    "You found the door again. Good.",
    "I was expecting you — everyone who knocks is.",
]

# The geomantic Judge is the verdict of the whole chart. She translates
# each of the eight possible judges into kitchen language.
JUDGE_WORDS = {
    "Acquisitio": (
        "The dough is rising. Gain gathers to the open hand — "
        "so keep yours open, and do not clutch."
    ),
    "Amissio": (
        "Some milk is meant to spill. What leaves your hands now "
        "is making room for what comes next."
    ),
    "Conjunctio": (
        "Two flavors are meeting in the pot. Do not taste yet — "
        "let them marry first."
    ),
    "Populus": (
        "A crowded kitchen. Everyone has an opinion. "
        "Listen for the one voice that sounds like yours."
    ),
    "Via": (
        "The road is the point. Walk it — "
        "the destination will arrive on its own two feet."
    ),
    "Carcer": (
        "The bread is still in the oven. "
        "Open the door now and it falls. Wait, but wait warmly."
    ),
    "Fortuna Major": (
        "The table is set, and it is generous. "
        "Say yes before you have finished counting the cost."
    ),
    "Fortuna Minor": (
        "Small lights tonight. Enough for the next step — "
        "not for the whole road. Step, then look again."
    ),
}

RECONCILER_WORDS = {
    "Via": "Sit with it by moving — a short walk settles more than a long argument.",
    "Populus": "Sit with it among people. Say it aloud to someone kind.",
    "Conjunctio": "Sit with it by joining two things you kept apart.",
    "Carcer": "Sit with it alone, behind a closed door, for one honest hour.",
    "Acquisitio": "Sit with it by giving something small away first.",
    "Amissio": "Sit with it by letting go of the smallest thing on your list.",
    "Fortuna Major": "Sit with it openly — make it a celebration, not a decision.",
    "Fortuna Minor": "Sit with it quietly, near a small light.",
}

# Socratic questions, keyed by the cast's signature. First match wins.
QUESTIONS = [
    # binary framing in the asker's own words
    (lambda d: " or " in d["decision"].lower(),
     "You set two plates on the table. But your hand already reached — "
     "which plate did it go to first?"),
    # strong motion in the I Ching cast
    (lambda d: len(d.get("changing_lines") or []) >= 2,
     "Two lines are moving — you are not deciding between places, you are "
     "deciding between *who you are* at each one. Which self do you miss less?"),
    # pure passage figures in the cast
    (lambda d: {"Via", "Populus"} & set(d["figure_names"]),
     "If no one would ever know what you chose — "
     "which way would your feet go on their own?"),
    # blocked/held figures
    (lambda d: {"Carcer", "Tristitia"} & set(d["figure_names"]),
     "What are you protecting by waiting? "
     "The outcome — or your right to choose again?"),
    # default: the rehearsal test
    (lambda d: True,
     "You came to me with options. But tell me — "
     "which one do you keep rehearsing in the dark?"),
]

COOKIES = [
    "Here — have a cookie. I promise, by the time you are done eating it, "
    "you will feel right as rain.",
    "Take a sweet. You already know who is coming to dinner.",
    "One for the road. It will not tell you the way — "
    "it will tell you why you are walking.",
    "Sugar for the nerves. Fear is only excitement wearing the wrong coat.",
    "Eat slowly. Answers are like pastry — they fall apart when you rush.",
]

CLOSERS = [
    "I can only show you the door. You are the one that has to walk through it.",
    "The beginning is already behind you. So the end is only a doorway, not a wall.",
    "You did not come here to make the choice. You came to understand it. Now you do.",
    "Everything that has a beginning has an end. Make your peace with that, "
    "and every door becomes a gift.",
]


# ------------------------------------------------------------------ engine

def _seed(doc: Dict[str, Any]) -> int:
    """Deterministic seed from the cast bits themselves."""
    bits = ""
    chart = doc.get("geomanticChart") or {}
    for part in ("judge", "reconciler"):
        node = chart.get(part) or {}
        bits += str(node.get("binaryVector") or "")
    for fig in doc.get("figure") or []:
        bits += str(fig.get("binaryVector") or "")
    if not bits:
        bits = str(doc.get("decisionText") or "mantic")
    return int(hashlib.sha256(bits.encode()).hexdigest(), 16)


def _extract(doc: Dict[str, Any]) -> Dict[str, Any]:
    chart = doc.get("geomanticChart") or {}
    judge = (chart.get("judge") or {}).get("label") or ""
    reconciler = (chart.get("reconciler") or {}).get("label") or ""
    names: List[str] = []
    for fig in doc.get("figure") or []:
        if fig.get("label"):
            names.append(str(fig["label"]))
    changing = (doc.get("hexagramCast") or {}).get("changingLines") or []
    return {
        "decision": str(doc.get("decisionText") or ""),
        "judge": judge,
        "reconciler": reconciler,
        "figure_names": names,
        "changing_lines": changing,
        "counsel": str(doc.get("strategicCounsel") or ""),
    }


def oracle_voice(doc: Dict[str, Any]) -> Dict[str, str]:
    """Render the Oracle's spoken response for a consultation document."""
    seed = _seed(doc)
    d = _extract(doc)

    address = ADDRESSES[seed % len(ADDRESSES)]

    sentences: List[str] = []
    judge_words = JUDGE_WORDS.get(d["judge"])
    if judge_words:
        sentences.append(f"The chart judges through {d['judge']}. {judge_words}")
    rec_words = RECONCILER_WORDS.get(d["reconciler"])
    if rec_words:
        sentences.append(rec_words)

    question = next(q for cond, q in QUESTIONS if cond(d))

    cookie = COOKIES[(seed >> 4) % len(COOKIES)]
    closer = CLOSERS[(seed >> 8) % len(CLOSERS)]

    words = " ".join(sentences) if sentences else d["counsel"]
    full = f"{address} {words} {question} {cookie} {closer}"

    return {
        "address": address,
        "words": words,
        "question": question,
        "cookie": cookie,
        "closer": closer,
        "full": full,
    }


__all__ = ["oracle_voice"]
