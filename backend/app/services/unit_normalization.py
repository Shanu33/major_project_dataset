import re
from typing import Optional, Tuple
from decimal import Decimal

def normalize_dimension(raw_value: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Deterministic unit normalization for basic physical length/dimension quantities.
    Converts standard linear dimensions (mm, cm, m) into normalized meters (m) as exact Decimal.
    Never mutates or discards raw_value.
    """
    if not raw_value or not isinstance(raw_value, str):
        return None, None

    cleaned = raw_value.strip().lower()
    
    # Match patterns like: "600 mm", "12.7 m", "15 cm"
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-z]+)$", cleaned)
    if not match:
        # Check if it's purely numeric without units
        try:
            val = Decimal(cleaned)
            return val, None
        except Exception:
            return None, None

    val_str, unit = match.groups()
    try:
        val = Decimal(val_str)
    except Exception:
        return None, None

    if unit in ["mm", "millimeter", "millimeters"]:
        return val / Decimal("1000"), "m"
    elif unit in ["cm", "centimeter", "centimeters"]:
        return val / Decimal("100"), "m"
    elif unit in ["m", "meter", "meters"]:
        return val, "m"
    else:
        # Retain original unit and value if unrecognized dimension
        return val, unit


UNIT_SYNONYMS = {
    # Volume
    "m3": "m3",
    "cum": "m3",
    "cu.m": "m3",
    "cu.m.": "m3",
    "cu m": "m3",
    "cubic meter": "m3",
    "cubic meters": "m3",
    "cubic metre": "m3",
    "cubic metres": "m3",
    # Area
    "m2": "m2",
    "sqm": "m2",
    "sq.m": "m2",
    "sq.m.": "m2",
    "sq m": "m2",
    "square meter": "m2",
    "square meters": "m2",
    "square metre": "m2",
    "square metres": "m2",
    # Length
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "linear meter": "m",
    "linear metre": "m",
    "lm": "m",
    "rmt": "m",
    # Weight / Mass
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "tonne": "tonne",
    "tonnes": "tonne",
    "mt": "tonne",
    "metric ton": "tonne",
    "metric tonne": "tonne",
    "t": "tonne",
    # Count / Units
    "nos": "nos",
    "no": "nos",
    "number": "nos",
    "numbers": "nos",
    "ea": "nos",
    "each": "nos",
    "pcs": "nos",
    "piece": "nos",
    "pieces": "nos",
    # Packaging
    "bag": "bags",
    "bags": "bags",
    # Time / Effort
    "hour": "hours",
    "hours": "hours",
    "hr": "hours",
    "hrs": "hours",
    "labour-hour": "hours",
    "labour-hours": "hours",
}


def normalize_unit(unit_str: Optional[str]) -> Optional[str]:
    """
    Deterministically normalizes standard construction units to canonical representations.
    E.g. 'cum' -> 'm3', 'sqm' -> 'm2', 'mt' -> 'tonne'.
    """
    if not unit_str or not isinstance(unit_str, str):
        return None
    cleaned = unit_str.strip().lower()
    return UNIT_SYNONYMS.get(cleaned, cleaned)


def are_units_compatible(u1: Optional[str], u2: Optional[str]) -> bool:
    """
    Determines if two unit strings represent the same canonical physical unit.
    """
    if not u1 or not u2:
        return False
    norm1 = normalize_unit(u1)
    norm2 = normalize_unit(u2)
    return norm1 is not None and norm2 is not None and norm1 == norm2

