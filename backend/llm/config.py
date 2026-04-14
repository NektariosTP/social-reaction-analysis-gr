"""
backend/llm/config.py

Central configuration for the LLM Processing pipeline (Phase 4).
Values are loaded from the project .env file via python-dotenv.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

# ------------------------------------------------------------------
# LLM provider settings
# ------------------------------------------------------------------
# Model passed to litellm.completion(). Auto-selected based on available
# API keys if not explicitly set in the environment.
def _auto_model() -> str:
    explicit = os.getenv("LLM_MODEL")
    if explicit:
        return explicit
    if os.getenv("GROQ_API_KEY"):
        return "groq/llama-3.3-70b-versatile"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini/gemini-2.0-flash"
    return "ollama/gemma3:4b"

LLM_MODEL: str = _auto_model()

# Optional API key overrides (litellm respects OPENAI_API_KEY, etc. automatically).
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Maximum tokens for LLM responses.
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "512"))

# Temperature for classification / summarization calls (0 = deterministic).
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# ------------------------------------------------------------------
# Classification
# ------------------------------------------------------------------
# The 5 reaction categories this project tracks.
REACTION_CATEGORIES: list[str] = [
    "Mass Mobilization & Street Actions",
    "Labor & Economic Reaction",
    "Institutional & Political Behavior",
    "Digital Reaction",
    "Conflict Reaction",
]

# Rich bilingual descriptions for zero-shot embedding classification.
# Used by classify_event_embedding() for zero-shot category matching.
CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Mass Mobilization & Street Actions": (
        "Συλλαλητήριο διαδήλωση πορεία πλατεία Σύνταγμα κινητοποίηση διαμαρτυρία "
        "αντιπολεμικό αντικυβερνητικό συγκέντρωση μαζική κινητοποίηση εκδήλωση "
        "πολίτες δρόμος παρέλαση μαθητές φοιτητές πανεκπαιδευτικό "
        "protest rally demonstration street march mobilization gathering crowd citizens"
    ),
    "Labor & Economic Reaction": (
        "Απεργία στάση εργασίας σωματείο ΓΣΕΕ ΑΔΕΔΥ εργαζόμενοι συνδικάτο "
        "24ωρη 48ωρη πανελλαδική εργολαβικοί ΟΛΜΕ ΔΟΕ ΔΕΗ λιμενεργάτες ΜΜΜ "
        "εκπαιδευτικοί νοσοκομείο αίτημα μισθοί συμβάσεις ΚΑΕ εργοδότης "
        "strike labor union workers stoppage wages collective agreement industry"
    ),
    "Institutional & Political Behavior": (
        "Βουλή κυβέρνηση υπουργός πρωθυπουργός κόμμα ΝΔ ΣΥΡΙΖΑ ΠΑΣΟΚ ΚΚΕ "
        "ψηφοφορία νόμος δικαστήριο δίκη εισαγγελία εκλογές ανακοίνωση αποχή "
        "κατηγορία κατεδάφιση ψηφοφόρος πολιτική απόφαση κοινοβούλιο "
        "parliament government minister court trial political party election institutional decision"
    ),
    "Digital Reaction": (
        "Viral social media Twitter Instagram TikTok hashtag διαδίκτυο "
        "online αναρτήσεις YouTube δημοσίευση trending θέμα ψηφιακή εκστρατεία "
        "διαδικτυακή διαμαρτυρία likes shares σχόλια κοινωνικά μέσα "
        "viral campaign digital protest online reaction trending hashtag social media post shares"
    ),
    "Conflict Reaction": (
        "Επεισόδια σύγκρουση συμπλοκή επίθεση βία ξύλο τραυματίες πετροπόλεμος "
        "μολότοφ χημικά δακρυγόνα οπαδοί προσαγωγές συλλήψεις πυροβολισμοί "
        "μαχαίρι ληστεία χειροπέδες αστυνομία βιαιοπραγία ξυλοδαρμός "
        "conflict violence attack fight brawl clashes injury arrest police shooting crime"
    ),
}
# User-agent string required by Nominatim fair-use policy.
NOMINATIM_USER_AGENT: str = os.getenv(
    "NOMINATIM_USER_AGENT",
    "social-reaction-analysis-gr/1.0",
)

# Seconds between Nominatim requests (1 req/sec fair use limit).
NOMINATIM_DELAY_SECONDS: float = float(os.getenv("NOMINATIM_DELAY_SECONDS", "1.1"))

# Bounding box for Greece (lon_min, lat_min, lon_max, lat_max).
# Used as a viewbox hint to bias geocoding results toward Greece.
GREECE_BBOX: tuple[float, float, float, float] = (19.3, 34.8, 28.3, 42.0)
