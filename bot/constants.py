"""Shared bot constants."""

COMMAND_PREFIXES = ["m.", "myami.", "my."]

CANCEL_WORDS = ["quit", "exit", "中止", "q"]

JANKEN_LABELS = {
    "rock": "グー",
    "scissors": "チョキ",
    "paper": "パー",
}
JANKEN_ALIASES = {
    "rock": {"グー", "ぐー", "g", "rock", "r", "✊", "gu-"},
    "scissors": {"チョキ", "ちょき", "s", "scissors", "✌", "c", "choki"},
    "paper": {"パー", "ぱー", "p", "paper", "✋", "pa-"},
}

COIN_LABELS = {
    "heads": "表",
    "tails": "裏",
}
COIN_ALIASES = {
    "heads": {"表", "おもて", "heads", "head", "h", "0", "true", "omote"},
    "tails": {"裏", "うら", "tails", "tail", "t", "1", "false", "ura"},
}
