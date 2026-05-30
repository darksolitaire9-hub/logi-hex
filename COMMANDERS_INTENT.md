# COMMANDER's INTENT: Logi-Hex

**MISSION PURPOSE (The "Why"):**
Logi-Hex exists to provide absolute data sovereignty and mathematically flawless inventory forecasting to professional operators. It must remain unbreakable, offline-capable, and fully auditable without requiring an active internet connection.

## 🔴 UNBREAKABLE LAWS (The Negative Space)
These are the architectural boundaries of the system. An AI or Human developer may **never** write code that violates these laws.

1. **NO CLOUD SYNC.** 
   - All state must remain on the local disk (SQLite). Never introduce AWS, Firebase, or external telemetry that compromises data sovereignty.
2. **NO BLACK BOX AI.** 
   - Forecasting logic (TimesFM or Pure Math) must be completely transparent to the operator. The operator must always have the ability to explicitly override the AI using deterministic units (not vague percentages).
3. **NO NEGATIVE INVENTORY.** 
   - The ledger must mathematically reflect physical reality. You cannot subtract items you do not possess.
4. **NO SILENT MUTATIONS.**
   - If bad data is submitted, the system must throw a loud, explicit error to the operator. The system must never silently clamp, fix, or "guess" what the user meant.
5. **NO HALLUCINATED DEMAND.**
   - The AI must differentiate between "0 Usage" (nobody wanted it) and "Out of Stock" (we had none to give). Out of stock days must use Linear Interpolation, not 0.

---
*End of Intent. If tactical communication is lost, act in accordance with this document.*
