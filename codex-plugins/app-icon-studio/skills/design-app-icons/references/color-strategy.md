# Color strategy for app-icon concepts

## Establish color authority

Choose one mode before writing prompts:

| Mode | Evidence | Required behavior |
|---|---|---|
| Brand-constrained | Brand guide, tokens, existing product UI | Use the provided colors and verify contrast; do not invent replacements. |
| Reference-led | Images, competitor set, mood board | Clarify which properties transfer. Treat hue as binding only when the user says so. |
| Open exploration | No binding brand direction | Propose distinct product-relevant palettes and explain the tradeoff of each. |

Do not infer that a reference controls color merely because it controls material or composition.
Do not use a bundled asset as color evidence.

## Ask or proceed

Ask a concise color question when:

- the user requests brand alignment but supplies no brand colors;
- references conflict materially;
- a regulated, accessibility, or cultural constraint could invalidate a palette;
- changing an already approved palette would constitute a redesign.

Proceed without blocking when the user asks for concepts and has no fixed palette. Make palette
selection part of the concepts.

## Build concept palettes

For each concept, define:

1. base role: tile/background and overall temperature;
2. primary object role: light/dark separation from the base;
3. accent role: the semantic gesture or focal point;
4. transition role: optional, local, and subordinate;
5. rationale: product meaning, audience, emotional tone, or supplied evidence.

Choose hues from the product rather than from a universal list. Relevant dimensions include:

- calm versus energetic;
- technical versus human;
- premium versus playful;
- trusted versus experimental;
- personal versus enterprise;
- dense utility versus lightweight creation.

Make up to three concepts genuinely comparable. Color may vary together with the metaphor when the
pairing is intentional, but avoid changing every variable at once. If evaluating color alone, keep
symbol, composition, lighting, and material fixed.

## Avoid false variety

- Do not default to blue for utility, trust, technology, or macOS styling.
- Do not generate three near-identical cool palettes and call them separate directions.
- Do not use a rainbow merely to signal creativity.
- Do not let gradient complexity replace semantic hierarchy.
- Do not sample proprietary competitor colors as a shortcut to category fit.

## Validate

Review each palette:

- on light and dark neutral backgrounds;
- at 128 and 32 px;
- in grayscale to test value hierarchy;
- with simulated common color-vision deficiencies when tools permit;
- against supplied brand tokens and neighboring application icons.

At small sizes, preserve value and edge contrast even if subtle transparency or secondary hue
variation must be reduced.

## Handoff

Record the chosen palette as:

```text
Color authority: brand-constrained | reference-led | concept-proposed
Base: <value and role>
Primary object: <value and role>
Accent: <value and role>
Transition: <optional value and role>
Rationale: <one or two sentences>
Small-size adjustment: <contrast or saturation changes, if any>
```

After selection, palette becomes an invariant during optical refinement unless the user explicitly
requests a color redesign.
