"""
domain/language/suggestions.py — UX suggestions for the UI.

Covers:
- SUGGESTED_UNITS: common unit values and labels the UI may pre-populate.
  Units are free text in the domain — these are suggestions only, not constraints.

Human reference: docs/LANGUAGE.md — Units (suggested values)
"""

SUGGESTED_UNITS: list[dict[str, str]] = [
    {"value": "pcs", "label": "Pieces (pcs)"},
    {"value": "kg", "label": "Kilograms (kg)"},
    {"value": "g", "label": "Grams (g)"},
    {"value": "L", "label": "Litres (L)"},
    {"value": "ml", "label": "Millilitres (ml)"},
    {"value": "box", "label": "Box"},
    {"value": "bag", "label": "Bag"},
    {"value": "portion", "label": "Portion"},
]
