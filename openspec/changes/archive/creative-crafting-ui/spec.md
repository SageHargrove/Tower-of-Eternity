# Feature Spec: Creative Crafting UI

## Goal
Surface the existing LLM-driven "Creative Crafting" backend logic into a proper, user-facing UI inside the Forge. Players should be able to describe a custom item they want to commission, offer specific gathered materials from their inventory, and have the LLM invent the equipment (and a reusable recipe for it).

## Context
The backend logic for LLM creative crafting already exists, but it was left unsurfaced due to the lack of a proper "Commission" UI and cost guardrails. Currently, players only have access to strict slot-crafting and discoverable blueprints.

## Requirements

### 1. The "Commission" UI
- Add a new tab/section in the Forge UI labeled "Creative Commission" or "Custom Forging".
- **Input Fields:**
  - **Description Textbox:** "Describe the weapon or armor you wish to forge..." (e.g. "A massive flaming broadsword that deals splash damage").
  - **Material Offering:** A UI allowing the player to select 1-3 specific materials from their inventory to offer as the base ingredients.
- **Cost Guardrails:** Show a Gold/Aether cost required to initiate the LLM commission request to prevent spamming the LLM generation.

### 2. Backend Integration
- Wire the UI to the existing LLM crafting endpoint.
- Ensure the backend properly deducts the offered materials and Gold/Aether cost *before* calling the LLM.
- If the LLM successfully generates the item, add the newly invented item to the player's inventory.
- Save the LLM's generated recipe so the player can re-craft this custom item in the future without needing to re-prompt the LLM.

### 3. Edge Cases & Error Handling
- If the LLM generation fails or returns malformed JSON, refund the player's materials/gold and show an error message ("The forge fires sputtered out. Try again.").
- Implement a cooldown or hard cap on custom commissions per day if LLM API costs are a concern.
