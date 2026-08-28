"""Canonical data tables for the Multi-System Mantic Oracle Engine (DVSystoE).

This module is the single source of truth for:

  * the 64 King Wen hexagrams (trigram composition -> 6-bit vectors),
  * the 16 geomantic figures of Arabic Geomancy / Sikidy,
  * the 16 principal Ifa odus (from which all 256 compound odus derive),
  * cross-system archetype links, and
  * the classical changing-line reading rules of the Zhouyi.

Conventions
-----------
I Ching   bits are read bottom line (index 0) -> top line (index 5);
          1 = yang, 0 = yin.
Geomancy  bits are read head (row 1, fire) -> feet (row 4, earth);
          1 = single/active row, 0 = double/passive row.
Ifa       an odu is 8 bits: left leg (4 bits) then right leg (4 bits),
          each leg read top to bottom; 1 = single mark.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple

MANTIC_NS = "https://w3id.org/mantic/core#"

#################################################################
# Trigrams (bagua)
#################################################################

TRIGRAM_BITS: Dict[str, str] = {
    # bits read bottom -> top within the trigram
    "Qian": "111",
    "Dui": "110",
    "Li": "101",
    "Zhen": "100",
    "Xun": "011",
    "Kan": "010",
    "Gen": "001",
    "Kun": "000",
}

TRIGRAM_ELEMENT: Dict[str, str] = {
    "Qian": "Heaven",
    "Dui": "Lake",
    "Li": "Fire",
    "Zhen": "Thunder",
    "Xun": "Wind",
    "Kan": "Water",
    "Gen": "Mountain",
    "Kun": "Earth",
}


@dataclass(frozen=True)
class HexagramSpec:
    """One of the 64 hexagrams in King Wen order."""

    number: int          # King Wen number, 1..64
    pinyin: str          # romanised name
    english: str         # traditional English name
    lower: str           # lower (inner) trigram
    upper: str           # upper (outer) trigram
    judgment: str        # archetypal counsel (original paraphrase)

    @property
    def bits(self) -> str:
        """6-bit vector, bottom line first."""
        return TRIGRAM_BITS[self.lower] + TRIGRAM_BITS[self.upper]

    @property
    def element(self) -> str:
        return TRIGRAM_ELEMENT[self.upper]

    @property
    def label(self) -> str:
        return f"{self.pinyin} ({self.english})"


# King Wen sequence. `bits` is derived from trigram composition, so the
# mapping is typo-proof by construction.
KING_WEN: List[HexagramSpec] = [
    HexagramSpec(1,  "Qian", "The Creative", "Qian", "Qian",
                 "Unbroken yang: creative force at full voltage. Initiate - but as the dragon that knows when not to fly."),
    HexagramSpec(2,  "Kun", "The Receptive", "Kun", "Kun",
                 "Unbroken yin: pure carrying capacity. Yield and gather; what serves without claiming inherits the outcome."),
    HexagramSpec(3,  "Zhun", "Difficulty at the Beginning", "Zhen", "Kan",
                 "Birth-sprouts in mud: the new thing stalls by its own roots. Steadfastness, not force; sort allies before roads."),
    HexagramSpec(4,  "Meng", "Youthful Folly", "Kan", "Gen",
                 "The unripe ask. Answer the sincere question once - the second asking is the answer."),
    HexagramSpec(5,  "Xu", "Waiting", "Qian", "Kan",
                 "Meat on the fire, danger not yet ripe. Nourish certainty in place; the crossing opens by itself."),
    HexagramSpec(6,  "Song", "Conflict", "Kan", "Qian",
                 "Heaven and water run opposite. Do not drive the case to verdict - settle midway or cede the field."),
    HexagramSpec(7,  "Shi", "The Army", "Kan", "Kun",
                 "The multitude needs a worthy general and a lawful cause; discipline is the permit for mass."),
    HexagramSpec(8,  "Bi", "Holding Together", "Kun", "Kan",
                 "Water seeks the low places. Bind early to the right center; late binding meets a closed gate."),
    HexagramSpec(9,  "Xiao Chu", "Small Taming", "Qian", "Xun",
                 "Dense clouds, no rain: the small gentles the strong without toppling it. Prepare; do not launch."),
    HexagramSpec(10, "Lu", "Treading", "Dui", "Qian",
                 "Step on the tiger's tail: conduct, not courage, survives proximity to power."),
    HexagramSpec(11, "Tai", "Peace", "Qian", "Kun",
                 "Heaven under earth: full exchange. Peak flow - bank some of it for the turning wheel."),
    HexagramSpec(12, "Pi", "Standstill", "Kun", "Qian",
                 "Earth under heaven: exchange blocked. The unworthy rise; keep the inner merit and the small duty."),
    HexagramSpec(13, "Tong Ren", "Fellowship", "Li", "Qian",
                 "Fire climbs toward heaven: fellowship by purpose, not kin - such company can cross the river."),
    HexagramSpec(14, "Da You", "Great Possession", "Qian", "Li",
                 "Fire high in heaven: abundance visible to all. Hold it with modesty and share to legitimize it."),
    HexagramSpec(15, "Qian", "Modesty", "Gen", "Kun",
                 "The mountain bows under the earth: what is full tilts, what is empty receives - modesty finishes the work."),
    HexagramSpec(16, "Yu", "Enthusiasm", "Kun", "Zhen",
                 "Thunder rolls out of the earth: enthusiasm moves the many - set the direction before the drums."),
    HexagramSpec(17, "Sui", "Following", "Zhen", "Dui",
                 "The joyous follows the moving: follow what is correct, not merely what is strong."),
    HexagramSpec(18, "Gu", "Work on the Decayed", "Xun", "Gen",
                 "The mildew has reached the beam: repair at the root. Three days before, three days after - name what rotted."),
    HexagramSpec(19, "Lin", "Approach", "Dui", "Kun",
                 "The great approaches the small: administer generously; the window is generous but counted."),
    HexagramSpec(20, "Guan", "Contemplation", "Kun", "Xun",
                 "Wind moves over the land: watch as one watched; the view decides the act."),
    HexagramSpec(21, "Shi He", "Biting Through", "Zhen", "Li",
                 "Obstruction between the teeth: bite through with firm, visible law - separation reunites."),
    HexagramSpec(22, "Bi", "Grace", "Li", "Gen",
                 "Fire below the mountain: form lit from within. Adorn the essential; polish never replaces bone."),
    HexagramSpec(23, "Bo", "Splitting Apart", "Kun", "Gen",
                 "The great is peeled by the small: rest quiet while the rotten strips away - do not rebuild mid-fall."),
    HexagramSpec(24, "Fu", "Return", "Zhen", "Kun",
                 "One yang under five yin: the turning point. Return arrives in seven days; the way renews itself."),
    HexagramSpec(25, "Wu Wang", "Integrity", "Zhen", "Qian",
                 "Thunder under heaven: act from nature, not scheming - the unexpected is not permission."),
    HexagramSpec(26, "Da Xu", "Great Taming", "Qian", "Gen",
                 "Heaven penned by the mountain: stockpile strength and virtue, not momentum."),
    HexagramSpec(27, "Yi", "Nourishment", "Zhen", "Gen",
                 "The mouth's two corners: watch intake and outflow - speech is also food."),
    HexagramSpec(28, "Da Guo", "Great Excess", "Xun", "Dui",
                 "The ridgepole sags under abnormal load. Extraordinary measures, taken early, right the beam."),
    HexagramSpec(29, "Kan", "The Abysmal", "Kan", "Kan",
                 "Water doubled: danger repeated like heartbeats. Keep the line true through every repetition."),
    HexagramSpec(30, "Li", "The Clinging", "Li", "Li",
                 "Fire doubled: clarity needs fuel. Radiance borrows; tend what you burn upon."),
    HexagramSpec(31, "Xian", "Influence", "Gen", "Dui",
                 "The lake above the mountain: attraction by stillness. Courtship precedes fusion; the small moves the great."),
    HexagramSpec(32, "Heng", "Duration", "Xun", "Zhen",
                 "Thunder over wind: persistence in motion, not in stance. Endure as rivers do."),
    HexagramSpec(33, "Dun", "Retreat", "Gen", "Qian",
                 "The strong steps back from the small: withdrawal in good order preserves the whole campaign."),
    HexagramSpec(34, "Da Zhuang", "Great Power", "Qian", "Zhen",
                 "The ram butts the fence. True power stops at correctness; force past it breaks horns."),
    HexagramSpec(35, "Jin", "Progress", "Kun", "Li",
                 "The sun rises over the earth: advance like the prince thrice received in one day - brightness earns speed."),
    HexagramSpec(36, "Ming Yi", "Darkening of the Light", "Li", "Kun",
                 "Light wounded beneath the earth: conceal the brilliance, keep the inner dawn, endure outward dusk."),
    HexagramSpec(37, "Jia Ren", "The Family", "Li", "Xun",
                 "Wind issues from fire: order kindles inside first; hold each role and the house orders itself."),
    HexagramSpec(38, "Kui", "Opposition", "Dui", "Li",
                 "Fire rises, the lake sinks: divergent natures on shared ground. In small matters, meet anyway."),
    HexagramSpec(39, "Jian", "Obstruction", "Gen", "Kan",
                 "Water below the mountain: the road dams. Turn inward, seek the southwest ally, refuse the blind north."),
    HexagramSpec(40, "Xie", "Deliverance", "Kan", "Zhen",
                 "Thunder breaks the storm: the knot loosens. Forgive quickly, return to the plain road."),
    HexagramSpec(41, "Sun", "Decrease", "Dui", "Gen",
                 "Two plates offered below: sincere decrease generates - sacrifice the small to keep the covenant."),
    HexagramSpec(42, "Yi", "Increase", "Zhen", "Xun",
                 "Wind and thunder compound each other: see good and copy it, see fault and mend it; ride surplus outward."),
    HexagramSpec(43, "Guai", "Breakthrough", "Qian", "Dui",
                 "Five yang resolve the last yin: proclaim the corrupt at court, win without war, then disarm."),
    HexagramSpec(44, "Gou", "Coming to Meet", "Xun", "Qian",
                 "The unexpected yin slips beneath five yang: do not marry the first insinuation - contain it at the door."),
    HexagramSpec(45, "Cui", "Gathering", "Kun", "Dui",
                 "The lake gathers over the earth: assemble the many around the great sacrifice, not the raid."),
    HexagramSpec(46, "Sheng", "Pushing Upward", "Xun", "Kun",
                 "Trees grow from low earth: ascend by stages; small works done well lift the whole."),
    HexagramSpec(47, "Kun", "Oppression", "Kan", "Dui",
                 "The lake is drained: words are not believed now. Endure outwardly, keep the hidden joy."),
    HexagramSpec(48, "Jing", "The Well", "Xun", "Kan",
                 "Towns move, the well does not: draw from the common depth - the jug matters at the rope's end."),
    HexagramSpec(49, "Ge", "Revolution", "Li", "Dui",
                 "Fire and lake cancel each other: the mandate changes when the day ripens - declare what is already true."),
    HexagramSpec(50, "Ding", "The Cauldron", "Xun", "Li",
                 "Wind feeds fire beneath the vessel: refine the raw into nourishment; feed the worthy."),
    HexagramSpec(51, "Zhen", "The Arousing", "Zhen", "Zhen",
                 "Shock upon shock: the centered laugh after the first terror; survey while others reel."),
    HexagramSpec(52, "Gen", "Stillness", "Gen", "Gen",
                 "Mountain on mountain: still the back so the courtyard empties; stop where stopping is right."),
    HexagramSpec(53, "Jian", "Development", "Gen", "Xun",
                 "The tree on the mountain: gradual advance; the maiden walks the rites to the full term."),
    HexagramSpec(54, "Gui Mei", "Marrying Maiden", "Dui", "Zhen",
                 "Thunder over the willing lake: a role taken as second best; know what union this is or the position erodes."),
    HexagramSpec(55, "Feng", "Abundance", "Li", "Zhen",
                 "Thunder and lightning at noon: fullness is a passing zenith - act within the light while it lasts."),
    HexagramSpec(56, "Lu", "The Wanderer", "Gen", "Li",
                 "Fire on the mountain: the stranger survives by courtesy, not assertion; petty gains cost the road."),
    HexagramSpec(57, "Xun", "The Gentle", "Xun", "Xun",
                 "Wind doubled: penetration by small returns; the gentle enters where force cannot."),
    HexagramSpec(58, "Dui", "The Joyous", "Dui", "Dui",
                 "Lakes joined: joy that exchanges; the firm center keeps pleasure from spilling."),
    HexagramSpec(59, "Huan", "Dispersion", "Kan", "Xun",
                 "Wind over water: dissolve the ice, gather the scattered - row the shared boat across."),
    HexagramSpec(60, "Jie", "Limitation", "Dui", "Kan",
                 "Water held by the lake banks: measure with accepted form; sweet limits empower, bitter limits break."),
    HexagramSpec(61, "Zhong Fu", "Inner Truth", "Dui", "Xun",
                 "Wind over the lake: the empty center registers the invisible - even pigs and fish are reached."),
    HexagramSpec(62, "Xiao Guo", "Small Excess", "Gen", "Zhen",
                 "Thunder under the mountain: the bird flies low. In small matters exceed; in great matters, echo."),
    HexagramSpec(63, "Ji Ji", "After Completion", "Li", "Kan",
                 "Water over fire: the work stands done - guard the seals at the joints; endings decay first."),
    HexagramSpec(64, "Wei Ji", "Before Completion", "Kan", "Li",
                 "Fire over water: the fox nearly across - lift the tail at the last step, not before it."),
]

KING_WEN_BY_BITS: Dict[str, HexagramSpec] = {h.bits: h for h in KING_WEN}
KING_WEN_BY_NUMBER: Dict[int, HexagramSpec] = {h.number: h for h in KING_WEN}

assert len(KING_WEN_BY_BITS) == 64, "King Wen table must contain 64 distinct vectors"


@dataclass(frozen=True)
class GeomanticSpec:
    """One of the 16 figures of the geomantic tableau."""

    rank: int            # rank within the 16, 1..16
    name: str
    bits: str            # 4 bits, head (fire) -> feet (earth)
    planet: str          # classical planetary / nodal attribution
    element: str         # elemental attribution of the planet
    keyword: str
    parable: str


GEOMANTIC_FIGURES: List[GeomanticSpec] = [
    GeomanticSpec(1, "Via", "1111", "Moon", "Water", "passage",
                  "The straight road: pure momentum with nothing carried - move, but do not mistake speed for direction."),
    GeomanticSpec(2, "Populus", "0000", "Moon", "Water", "assembly",
                  "The square full of faces: the outcome is collective and inert; wait a tide before reading the sea."),
    GeomanticSpec(3, "Fortuna Major", "0111", "Sun", "Fire", "earned victory",
                  "Sun behind the wall: victory earned through patient strength - help arrives from what you cannot command."),
    GeomanticSpec(4, "Fortuna Minor", "1110", "Sun", "Fire", "swift luck",
                  "The swift flame: quick gain by cleverness - secure it now, it will not hold."),
    GeomanticSpec(5, "Acquisitio", "0011", "Jupiter", "Air", "gain",
                  "The rising cup: gain gathers to the low and open hand; receive without gripping."),
    GeomanticSpec(6, "Amissio", "1100", "Venus", "Water", "loss",
                  "The funnel: loss through the narrow top - release the perishable before it prices itself."),
    GeomanticSpec(7, "Laetitia", "0001", "Jupiter", "Air", "joy rising",
                  "A single spark at the base: joy rises like sap - protect the small fire and let it climb."),
    GeomanticSpec(8, "Tristitia", "1000", "Saturn", "Earth", "sorrow hanging",
                  "Weight at the crown: sorrow hangs the head - invert the figure and the seed becomes summit."),
    GeomanticSpec(9, "Puer", "1011", "Mars", "Fire", "impetuous strength",
                  "The drawn blade of youth: courage without patience; cut once, then sheath."),
    GeomanticSpec(10, "Puella", "1101", "Venus", "Water", "harmonious grace",
                  "The mirror of delight: harmony earned by grace; beauty binds only while sincere."),
    GeomanticSpec(11, "Albus", "1010", "Mercury", "Air", "clear thought",
                  "The clear goblet: thought purified - withdraw into counsel; do not act on heat."),
    GeomanticSpec(12, "Rubeus", "0101", "Mars", "Fire", "passion clouding",
                  "The red vapor: passion at the feet of reason - postpone the irreversible."),
    GeomanticSpec(13, "Conjunctio", "1001", "Mercury", "Air", "union",
                  "The meeting of roads: union or negotiation; combine unequal halves in the open."),
    GeomanticSpec(14, "Carcer", "0110", "Saturn", "Earth", "containment",
                  "The cage of law: what encloses also defines - name the constraint precisely to unlock it."),
    GeomanticSpec(15, "Caput Draconis", "0010", "North Node", "Air", "ingress",
                  "The door opening inward: beginnings permitted - enter with the tide."),
    GeomanticSpec(16, "Cauda Draconis", "0100", "South Node", "Earth", "egress",
                  "The door opening outward: endings demanded - leave before you are left."),
]

GEOMANTIC_BY_BITS: Dict[str, GeomanticSpec] = {f.bits: f for f in GEOMANTIC_FIGURES}

assert len(GEOMANTIC_BY_BITS) == 16, "Geomantic table must contain 16 distinct vectors"


@dataclass(frozen=True)
class OduSpec:
    """One of the 16 principal (Meji-generating) Ifa odus."""

    rank: int            # seniority, 1..16
    name: str
    bits: str            # 4-bit leg, read top to bottom
    parable: str


ODU_PRINCIPALS: List[OduSpec] = [
    OduSpec(1, "Ogbe", "1111",
            "Light at fullness: destiny aligned - proceed without arrogance; the bright road punishes pride."),
    OduSpec(2, "Oyeku", "0000",
            "Darkness at fullness: the ancestor road closes a cycle - retreat honors what opens next."),
    OduSpec(3, "Iwori", "1001",
            "The eye turned inward: verify the seer before the seeing; the answer observes the asker."),
    OduSpec(4, "Odi", "0110",
            "The sealed calabash: what turns inward ripens or rots - tend the interior."),
    OduSpec(5, "Irosun", "0111",
            "Blood on the imprint: legacies owed; settle the old account before new ventures."),
    OduSpec(6, "Owonrin", "1110",
            "The scattered roof: sudden disorder - repair shelter first, plans second."),
    OduSpec(7, "Obara", "0100",
            "The lone strong mark: wealth arrives disguised as the strange; do not refuse the plain gift."),
    OduSpec(8, "Okanran", "0010",
            "The urgent call: answer now; in delay the trap sets itself."),
    OduSpec(9, "Ogunda", "1100",
            "The clearing cut: sever cleanly what obstructs - surgery, not demolition."),
    OduSpec(10, "Osa", "0011",
            "The multitude arrives at once: choose the emissary or be swept by the crowd."),
    OduSpec(11, "Ika", "0101",
            "The coiled serpent: delay woven into the path - unwind by patience, never by force."),
    OduSpec(12, "Oturupon", "1010",
            "The burdened back: endurance past fatigue; share the load or it shares you."),
    OduSpec(13, "Otura", "1101",
            "The calm sky: peace is earned and defended - protect the quiet deliberately."),
    OduSpec(14, "Irete", "1011",
            "The bent reed reaching heaven: negotiate with power; humility is the tactic, not the defeat."),
    OduSpec(15, "Ose", "0001",
            "The winning whisper: victory through the small - bless the source of the stream."),
    OduSpec(16, "Ofun", "1000",
            "The full gourd poured: abundance in circulation; give the stream its bed or it digs its own."),
]

ODU_PRINCIPALS_BY_BITS: Dict[str, OduSpec] = {o.bits: o for o in ODU_PRINCIPALS}
ODU_PRINCIPALS_BY_NAME: Dict[str, OduSpec] = {o.name: o for o in ODU_PRINCIPALS}

assert len(ODU_PRINCIPALS_BY_BITS) == 16, "Odu principal table must contain 16 distinct legs"


def odu_index(left_bits: str, right_bits: str) -> int:
    """Seniority index 1..256 of a compound odu.

    Ordering convention: left leg seniority dominates; within a left leg,
    the right legs run in principal seniority.
    """
    left_rank = ODU_PRINCIPALS_BY_BITS[left_bits].rank - 1
    right_rank = ODU_PRINCIPALS_BY_BITS[right_bits].rank - 1
    return left_rank * 16 + right_rank + 1


def compound_odu_name(left_bits: str, right_bits: str) -> str:
    left = ODU_PRINCIPALS_BY_BITS[left_bits].name
    right = ODU_PRINCIPALS_BY_BITS[right_bits].name
    if left == right:
        return f"{left} Meji"
    return f"{left}-{right}"


#################################################################
# Cross-system archetype links (seed)
#################################################################

# figure name -> King Wen number (curated, narrative-strong pairings)
GEOMANTY_HEXAGRAM_LINKS: List[Tuple[str, int]] = [
    ("Via", 1),              # all-active road <-> pure creative force
    ("Populus", 2),          # all-passive assembly <-> pure receptivity
    ("Fortuna Major", 11),   # earned victory <-> peak flow
    ("Fortuna Minor", 12),   # swift luck that will not hold <-> standstill
    ("Acquisitio", 14),      # gain <-> great possession
    ("Amissio", 41),         # loss <-> decrease
    ("Laetitia", 46),        # joy rising <-> pushing upward
    ("Tristitia", 23),       # hanging sorrow <-> splitting apart
    ("Conjunctio", 61),      # union <-> inner truth
    ("Carcer", 60),          # containment <-> limitation
    ("Caput Draconis", 24),  # ingress <-> return
    ("Cauda Draconis", 33),  # egress <-> retreat
    ("Puer", 34),            # impetuous strength <-> great power
    ("Puella", 58),          # grace <-> the joyous
    ("Albus", 20),           # clear thought <-> contemplation
    ("Rubeus", 21),          # passion clouding <-> biting through
]

# King Wen number -> principal odu name (curated)
HEXAGRAM_ODU_LINKS: List[Tuple[int, str]] = [
    (1, "Ogbe"),    # Qian <-> Eji Ogbe (all yang / all marks)
    (2, "Oyeku"),   # Kun <-> Oyeku Meji (all yin / all open)
    (61, "Iwori"),  # inner truth <-> the inward eye
    (24, "Ose"),    # return <-> the winning small
]

# figure name -> principal odu name is identity-of-bits: every figure links
# to the Meji (doubled) odu carrying its exact 4-bit pattern (auto-generated).

# Figures whose counsel canonically addresses each decision-context class.
RESOLVES_AMBIGUITY_SEEDS: List[Tuple[str, str]] = [
    ("Populus", "Deadlock"),
    ("Via", "ParetoFlat"),
    ("Rubeus", "OODSurprise"),
    ("Puella", "ParetoFlat"),
    ("Carcer", "Deadlock"),
    ("Osa", "OODSurprise"),
    ("OduOgunda", "Deadlock"),
    ("OduIrete", "ParetoFlat"),
]


#################################################################
# Zhouyi changing-line reading rules (Zhu Xi / standard table)
#################################################################

CHANGING_LINE_COUNSEL: Dict[int, str] = {
    0: "No lines move: the counsel stands exactly as cast - act on the primary reading without amendment.",
    1: "One line moves: the oracle speaks through that single position; the resultant hexagram shows where the change lands.",
    2: "Two lines move: two currents compete - read both, the upper (later) line governs; hold until one dominates.",
    3: "Three lines move: the situation is mid-transformation - read the middle (central) changing line and consult both hexagrams.",
    4: "Four lines move: change floods the field - read the two unmoving lines, the lower one governs; stability is the message.",
    5: "Five lines move: nearly total change - read the single unmoving line; it is what persists through the overturn.",
    6: "All lines move: total transformation - discard the primary judgment and read the resultant hexagram alone.",
}
