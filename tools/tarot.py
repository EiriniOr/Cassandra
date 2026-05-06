import random

MAJOR = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
]

SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
RANKS = [
    "Ace",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "Page",
    "Knight",
    "Queen",
    "King",
]

DECK = MAJOR + [f"{r} of {s}" for s in SUITS for r in RANKS]


def tarot_draw(spread: str = "single", question: str = "") -> str:
    spreads = {
        "single": ["Card"],
        "three": ["Past", "Present", "Future"],
        "celtic": [
            "Present",
            "Challenge",
            "Past",
            "Future",
            "Above (conscious)",
            "Below (subconscious)",
            "Advice",
            "External influences",
            "Hopes/fears",
            "Outcome",
        ],
    }
    positions = spreads.get(spread, spreads["single"])
    cards = random.sample(DECK, len(positions))
    lines = [f"Tarot reading — {spread} spread"]
    if question:
        lines.append(f"Question: {question}")
    lines.append("")
    for pos, card in zip(positions, cards):
        reversed_ = random.random() < 0.3
        suffix = " (reversed)" if reversed_ else ""
        lines.append(f"  {pos}: {card}{suffix}")
    lines.append(
        "\nInterpret these cards in light of the question. Be thoughtful but don't take it too seriously."
    )
    return "\n".join(lines)


SCHEMA = {
    "name": "tarot_draw",
    "description": "Draw tarot cards for a question. Spreads: 'single' (1 card), 'three' (past/present/future), 'celtic' (10-card cross).",
    "input_schema": {
        "type": "object",
        "properties": {
            "spread": {"type": "string", "enum": ["single", "three", "celtic"]},
            "question": {"type": "string"},
        },
    },
}
