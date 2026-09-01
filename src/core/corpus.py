"""Deep corpus: traditional themes, proverbs and composed counsel.

Layer 2 of the knowledge base. `tables.py` holds the structure (bits,
names, ranks); this module holds the *depth*:

  * ODU_LEG_THEMES  - the traditional character of each of the 16
    principal Ifa legs (domain, motion, risk, gift);
  * PROVERBS        - Ifa-style proverbs, keyed by leg, selected
    deterministically for compound odus;
  * compound_parable() - weaves the two legs of a compound odu into
    flowing counsel (replacing the old "Left leg X leads: ... || Right
    leg Y modifies: ..." stitch);
  * HEXAGRAM_IMAGES - the classical Image (Xiang) text for each of the
    64 hexagrams, public-domain-adapted from the Legge (1899) line.

Deterministic: same legs in, same text out. No randomness.
"""

from __future__ import annotations

from typing import Dict

from .tables import ODU_PRINCIPALS_BY_NAME


# ----------------------------------------------------------------------
# The sixteen legs — traditional character
# ----------------------------------------------------------------------

ODU_LEG_THEMES: Dict[str, Dict[str, str]] = {
    "Ogbe": {
        "essence": "light at its first opening",
        "domain": "beginnings, clarity, the uncarried day",
        "motion": "rises and extends",
        "risk": "light that ignores the shadow exhausts itself by noon",
        "gift": "a clean start granted, not earned",
    },
    "Oyeku": {
        "essence": "the closing gate",
        "domain": "endings, ancestors, the fertile dark",
        "motion": "withdraws and gathers",
        "risk": "staying past the ending rots the granary",
        "gift": "peace made with what is finished",
    },
    "Iwori": {
        "essence": "the witness between two banks",
        "domain": "perception, transformation, honest seeing",
        "motion": "turns and returns",
        "risk": "seeing everything, choosing nothing",
        "gift": "the eye that judges itself first",
    },
    "Odi": {
        "essence": "the closed circle",
        "domain": "return, enclosure, what comes home",
        "motion": "circles inward",
        "risk": "the circle becomes a wall",
        "gift": "sanctuary and the second chance",
    },
    "Irosun": {
        "essence": "the old stain on the new cloth",
        "domain": "foundations, inheritance, blood memory",
        "motion": "seeps and steadies",
        "risk": "the past bleeding through every fresh start",
        "gift": "deep root, deep stand",
    },
    "Owonrin": {
        "essence": "the market on fire",
        "domain": "upheaval, reversal, unexpected news",
        "motion": "scatters and re-forms",
        "risk": "chasing every broken thing at once",
        "gift": "the old arrangement's funeral is the new one's wedding",
    },
    "Obara": {
        "essence": "the scale and the coin",
        "domain": "exchange, wealth, honest weight",
        "motion": "trades and balances",
        "risk": "riches that arrive faster than the character to hold them",
        "gift": "prosperity with clean hands",
    },
    "Okanran": {
        "essence": "the tested vow",
        "domain": "adversity, loyalty, the breaking point",
        "motion": "tightens and holds",
        "risk": "hardening into the very enemy being resisted",
        "gift": "loyalty proven is loyalty that leads",
    },
    "Ogunda": {
        "essence": "the clearing blade",
        "domain": "cutting through, sudden truth, surgery",
        "motion": "cuts once, cleanly",
        "risk": "a blade kept swinging finds its own leg",
        "gift": "the obstacle removed at the root",
    },
    "Osa": {
        "essence": "the storm that assembles",
        "domain": "scattering winds, sudden allies, gathering",
        "motion": "disperses then collects",
        "risk": "assembling a following with no center to hold them",
        "gift": "what scatters you also spreads your name",
    },
    "Ika": {
        "essence": "the slow poison, the slow medicine",
        "domain": "boundaries, subtle force, transformation of the hidden",
        "motion": "circles without sound",
        "risk": "the dose that heals is the dose that kills, differed only by patience",
        "gift": "mastery of the unseen lever",
    },
    "Oturupon": {
        "essence": "the long-walking elder",
        "domain": "endurance, maturity, the body's truth",
        "motion": "endures and ripens",
        "risk": "endurance worn as identity, not passage",
        "gift": "outlasting the thing that tested you",
    },
    "Otura": {
        "essence": "the cool noon",
        "domain": "peace, truth, the settled heart",
        "motion": "settles and clarifies",
        "risk": "calm mistaken for agreement",
        "gift": "the verdict that harms no one",
    },
    "Irete": {
        "essence": "the closed fist of order",
        "domain": "determination, law, force applied rightly",
        "motion": "grips and orders",
        "risk": "order without mercy becomes its own disorder",
        "gift": "the will that finishes the sentence",
    },
    "Ose": {
        "essence": "the blessing that outruns you",
        "domain": "victory, abundance, the granted wish",
        "motion": "arrives like weather",
        "risk": "the granted wish you were not ready to want",
        "gift": "winning without needing to win",
    },
    "Ofun": {
        "essence": "the long white road",
        "domain": "wisdom, patience, the elder's counsel",
        "motion": "extends and teaches",
        "risk": "wisdom deferred until the road forgives nothing",
        "gift": "the long view that shortens the road",
    },
}


# ----------------------------------------------------------------------
# Proverbs — Ifa-style, keyed by the leading leg, second-keyed by the
# modifying leg so compound selection is fully deterministic.
# ----------------------------------------------------------------------

LEG_PROVERBS: Dict[str, str] = {
    "Ogbe": "However long the night, the dawn arrives without knocking.",
    "Oyeku": "The elder who greets the ancestors first eats the fattest yam.",
    "Iwori": "The eye that sees the river's two banks sees its own reflection last.",
    "Odi": "What leaves the village by the east gate returns by the west.",
    "Irosun": "The new house stands because the old foundation kept its silence.",
    "Owonrin": "When the market burns, the patient trader counts ash, the wise one counts stalls.",
    "Obara": "The coin does not know whose hand is honest; the scale does.",
    "Okanran": "The dog that guards the compound through famine deserves the first bone.",
    "Ogunda": "Do not sharpen the blade twice for one stubborn root.",
    "Osa": "The wind that scatters the millet also carries the seed to new soil.",
    "Ika": "The quiet river is the one that moved the boundary stone.",
    "Oturupon": "The elder walks slowly because the road already knows his name.",
    "Otura": "Cool water settles the quarrel that hot words started.",
    "Irete": "The fist that grips the law must first have held the scale.",
    "Ose": "The blessing finds the house with an open door, not the loudest drum.",
    "Ofun": "The one who asks the road three times arrives once, and whole.",
}

MODIFIER_PROVERBS: Dict[str, str] = {
    "Ogbe": "Yet light renews its contract every morning.",
    "Oyeku": "Yet every open road remembers where it closed.",
    "Iwori": "Yet the witness sees what the traveler cannot.",
    "Odi": "Yet what returns carries news of the far bank.",
    "Irosun": "Yet the ground beneath holds the oldest vote.",
    "Owonrin": "Yet the unexpected guest often carries the needed key.",
    "Obara": "Yet the market weighs all news in the same scale.",
    "Okanran": "Yet the tested vow outlives the easy one.",
    "Ogunda": "Yet one clean cut spares a hundred small ones.",
    "Osa": "Yet the storm rearranges the furniture before the feast.",
    "Ika": "Yet the smallest rudder turns the longest canoe.",
    "Oturupon": "Yet patience is the only horse that finishes the race.",
    "Otura": "Yet the cool heart reads the hot hour correctly.",
    "Irete": "Yet the matter ends where the will stands firm.",
    "Ose": "Yet the harvest answers the name of the patient farmer.",
    "Ofun": "Yet the elder's word outruns the young man's horse.",
}


def compound_parable(left_name: str, right_name: str) -> str:
    """Weave a compound odu's two legs into flowing counsel.

    The leading (left) leg sets the stage; the modifying (right) leg
    bends its meaning. A proverb grounds the weave.
    """
    left = ODU_LEG_THEMES[left_name]
    right = ODU_LEG_THEMES[right_name]
    parable = (
        f"{left_name} rises first — {left['essence']} — and sets the stage "
        f"of {left['domain']}. Over it walks {right_name}, {right['essence']}: "
        f"{left['motion'].capitalize()}, the reading now {right['motion']}. "
        f"The danger here is {left['risk']}; the working gift is {right['gift']}. "
        f'"{LEG_PROVERBS[left_name]} {MODIFIER_PROVERBS[right_name]}"'
    )
    return parable


# ----------------------------------------------------------------------
# The sixty-four Images (Xiang) — public-domain-adapted from Legge 1899
# ----------------------------------------------------------------------

HEXAGRAM_IMAGES: Dict[int, str] = {
    1: "Heaven moves with power: the great person strengthens without pause.",
    2: "Earth's capacity is receptive: the great person carries all things with generous virtue.",
    3: "Clouds and thunder: the beginning struggles — the great person untangles and governs.",
    4: "A spring beneath a mountain: youth — the wise nourish character by thoroughness.",
    5: "Clouds rise in heaven: waiting — the wise enjoy the hour and eat, drink and are glad.",
    6: "Heaven and water go contrary: conflict — the wise deliberates on the beginning of things.",
    7: "Water within the earth: the army — the wise nourishes the multitude and bears with the people.",
    8: "Water on the earth: union — the ancient kings founded states and allied with the clans.",
    9: "Wind moves across heaven: small restraint — the wise refines the outward substance of character.",
    10: "Heaven above, the lake below: treading — the wise distinguishes high and low and steadies the people's will.",
    11: "Heaven and earth commune: peace — the ruler diminishes the full and gives to the empty.",
    12: "Heaven and earth do not meet: standstill — the wise withdraws from wealth and honor to guard his purpose.",
    13: "Fire rises with heaven: fellowship — the wise sorts kinds and distinguishes beings.",
    14: "Fire high in heaven: great possession — the wise curbs wrath and halts crime, yet shines forth.",
    15: "A mountain under the earth: modesty — the wise diminishes the much and adds to the little.",
    16: "Thunder comes out of the earth: enthusiasm — the ancient kings made music to honor virtue.",
    17: "Thunder within the lake: following — the wise enters rest at nightfall.",
    18: "Wind below the mountain: decay — the wise stirs the people and grows their minds.",
    19: "The earth above the lake: approach — the wise is inexhaustible in teaching and boundless in tolerating.",
    20: "Wind moves over the earth: contemplation — the ancient kings toured the regions and observed the people.",
    21: "Thunder and lightning: biting through — the ancients made penalties clear and enforced the law.",
    22: "Fire below the mountain: grace — the wise brightens the administration but dares not decide cases lightly.",
    23: "The mountain rests on the earth: splitting apart — the rulers strengthened the people below.",
    24: "Thunder within the earth: return — the shut the solstice gates and rested.",
    25: "Thunder under heaven: innocence — the ancient kings, rich in virtue, matched the seasons.",
    26: "Heaven within the mountain: great accumulation — the wise gathers knowledge, word and deed.",
    27: "Thunder below the mountain: nourishment — the wise is careful of words and temperate in eating.",
    28: "The lake drowns the trees: excess — the sage stands alone without fear.",
    29: "Water flows on unceasingly: danger — the wise walks in lasting virtue and teaches constantly.",
    30: "Brightness doubled: fire — the great person illuminates the four quarters.",
    31: "The lake above the mountain: influence — the ruler takes in the people with an open heart.",
    32: "Thunder and wind: duration — the wise stands firm and does not change his direction.",
    33: "The mountain under heaven: retreat — the wise keeps distant from the small-minded without anger.",
    34: "Thunder above heaven: great power — the noble person does not walk where he does not belong.",
    35: "The sun rises over the earth: progress — the ruler makes the people's hearts bright.",
    36: "The light enters the earth: darkening — the wise masks brilliance and keeps the inner light.",
    37: "Wind comes from fire: the family — the wise has substance in words and constancy in conduct.",
    38: "Fire above, the lake below: opposition — the sage holds the common while differing.",
    39: "Thunder on the mountain: obstruction — the wise turns inward and repairs himself.",
    40: "Thunder and rain release: deliverance — the ruler pardons mistakes and forgives faults.",
    41: "The lake below the mountain: decrease — the wise restrains anger and curbs desire.",
    42: "Wind and thunder: increase — the ruler, seeing good, imitates it; having faults, corrects them.",
    43: "The lake rises to heaven: breakthrough — the ruler proclaims goodness to the people.",
    44: "Wind under heaven: coming to meet — the ruler publishes orders and warns the four quarters.",
    45: "The lake rises over the earth: gathering — the ruler renews weapons to guard against the unforeseen.",
    46: "Trees rise from the earth: pushing upward — the ruler, growing in virtue, accumulates the small into the high.",
    47: "The lake without water: oppression — the wise lives for his purpose and attains happiness.",
    48: "Water over wood: the well — the town may move, the well cannot.",
    49: "Fire in the lake: revolution — the ruler orders the calendar and makes the seasons clear.",
    50: "Fire over wood: the cauldron — the sage keeps his position straight and secures fate.",
    51: "Thunder repeated: the arousing — the wise fears, examines and reforms.",
    52: "Mountains stand together: stillness — the wise does not let thoughts leave his situation.",
    53: "Wind on the mountain: gradual progress — the ruler lives in dignity and improves the people's manners.",
    54: "Thunder over the lake: the marrying maiden — the wise knows the flaws of things and foresees their end.",
    55: "Thunder and lightning arrive: abundance — the ruler decides lawsuits and applies penalties.",
    56: "Fire on the mountain: the wanderer — the wise is clear-minded and careful in applying punishments.",
    57: "Wind follows wind: gentleness — the ruler repeats commands and carries out commands.",
    58: "Lakes joined: joy — the ruler renews the people in friendship and counsel.",
    59: "Wind moves over water: dispersion — the ruler sacrifices at the ancestral shrine.",
    60: "Water over the lake: limitation — the wise makes rules for measuring numbers.",
    61: "Wind over the lake: inner truth — the ruler deliberates on lawsuits and delays death.",
    62: "Thunder over the mountain: the small exceeding — the wise in small matters exceeds in reverence.",
    63: "Water over fire: after completion — the wise thinks of danger and guards against it in advance.",
    64: "Fire over water: before completion — the wise distinguishes things so each finds its place.",
}


__all__ = [
    "ODU_LEG_THEMES",
    "LEG_PROVERBS",
    "MODIFIER_PROVERBS",
    "compound_parable",
    "HEXAGRAM_IMAGES",
]
