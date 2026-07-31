# Visual system for premium desktop app icons

## Design target

Aim for the restraint of first-party platform icons rather than maximum surface detail. A premium
icon usually contains:

1. one stable rounded-square base;
2. one dominant semantic object;
3. one supporting gesture or accent;
4. no more than three meaningful depth planes.

Use `../assets/reference-liquid-glass-quality.png` only as a benchmark for material quality and
hierarchy:

- stable rounded-square tile;
- frosted primary object;
- readable internal glyphs;
- one coherent glass gesture;
- selective highlights rather than glow everywhere.

The reference demonstrates depth, edge control, and optical simplification. Its blue/cyan hues and
CV/resume subject are not defaults. Ignore them unless the user explicitly selects them.

## Liquid Glass rules

- Use thick, optically coherent glass rather than thin transparent outlines.
- Give each glass object one dominant white rim and at most one colored inner reflection.
- Use refraction and color depth inside large masses; remove repeated hairline rims.
- Keep bloom narrow. White-on-white glow destroys the subject at small sizes.
- Separate adjacent translucent objects with local value contrast, not extra outlines.
- Place the brightest highlight on the main gesture, not on every edge.
- Usually limit the palette to one base hue, one accent hue, and an optional small transition hue.
  Select those hues through `color-strategy.md`, never by copying this reference automatically.

## Semantic hierarchy

At 32 px, viewers should read:

```text
outer tile → primary object → primary gesture
```

Supporting lines, portrait features, folds, and caustics are optional. If removing a detail does not
change meaning, simplify it in small masters.

## Optical sizing

| Size | Preserve | Reduce |
|---:|---|---|
| 512–1024 | material, depth, caustics | random micro-texture |
| 256 | all semantic objects | duplicate reflections |
| 128 | profile/glyph, gesture, broad depth | hairlines and weak shadows |
| 64 | two or three main masses | internal optical noise |
| 32 | silhouette and bold internal glyph | subtle transparency and thin rims |
| 16 | tile plus dominant gesture | almost all secondary detail |

Do not merely sharpen a noisy downscale. First simplify the source, then use modest sharpening.

## Prompt blueprint

```text
Asset type: macOS/Windows app icon.
Product meaning: <one sentence>.
Primary symbol: <one large object>.
Supporting gesture: <one accent object>.
Style: restrained platform-system icon, compact 3D layering, selective Liquid Glass.
Composition: centered, simple silhouette, fills 70–76% of the tile, readable at 32 px.
Materials: frosted surface plus one coherent thick glass accent.
Lighting: soft top-left light, one highlight per surface, limited bloom.
Palette: <base>, <accent>, optional small transition hue.
Palette rationale: <brand token, supplied reference, or product-specific reasoning>.
Constraints: one isolated icon; no text, labels, grid, watermark, Apple logo, or extra objects.
```

For refinement, add:

```text
Preserve exactly: symbol, layout, proportions, palette, camera, and material identity.
Change only: <one targeted adjustment>.
This is an optical cleanup, not a redesign.
```

## Comparison protocol

Show:

- the full candidate;
- side-by-side previous/new at 128 px;
- side-by-side previous/new at 32 px;
- previews on light and dark neutral backgrounds.

Judge recognition before glass realism at 32 px and material quality before micro-detail at 512 px.
