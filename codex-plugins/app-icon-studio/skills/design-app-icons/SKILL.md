---
name: design-app-icons
description: Design, refine, validate, and package polished raster app icons for macOS and Windows across arbitrary brand palettes, especially restrained Liquid Glass-style icons with strong small-size legibility. Use when Codex needs to explore app-icon concepts and color directions, translate product meaning into one dominant symbol, preserve an approved visual direction during refinement, create optical 128/32/16 px variants, generate macOS iconsets and ICNS files, generate Windows ICO files, or verify that a packaged desktop app contains the intended icon.
---

# Design App Icons

Create premium icon systems, not only attractive 1024 px pictures. Preserve semantic clarity,
material quality, small-size recognition, and reproducible platform packaging.

## Load references selectively

- Read `references/visual-system.md` before concept generation or Liquid Glass refinement.
- Read `references/color-strategy.md` before selecting, proposing, or changing a palette.
- Read `references/platform-packaging.md` before producing ICNS/ICO assets or integrating an icon.
- Read `references/lessons-learned.md` when diagnosing blur, style drift, stale icons, or packaging failures.
- Use the images in `assets/` only as material and small-size quality benchmarks. Do not inherit
  their subject or colors unless the user explicitly selects those properties.

## Workflow

### 1. Establish the brief

Identify:

- product purpose and primary user action;
- target platforms and required formats;
- existing icon, screenshots, brand guidelines, color preferences, and visual references;
- the one idea the icon must communicate at 32 px;
- whether the request is exploration, refinement, packaging, or integration.

Determine the color authority before generating concepts:

- **Brand-constrained:** use supplied brand tokens or guidelines.
- **Reference-led:** ask whether the reference controls color, material, composition, or only mood.
- **Open exploration:** make color a deliberate variable in the concepts and explain each palette.

Ask only questions that materially change the symbol, platform output, or brand direction. If
brand compliance is required but colors or references are missing, ask for them. If exploration is
requested, do not block: propose distinct, product-relevant palettes with short rationales.
Never silently default to blue or to the palette of bundled examples.

### 2. Analyze references into rules

Inspect every supplied image. Convert references into constraints such as:

- one dominant symbol;
- simple outer silhouette;
- controlled depth hierarchy;
- intentional, limited palette with a documented source or rationale;
- selective translucency;
- high local contrast;
- generous internal spacing.

Reference a platform's design language without tracing proprietary marks or copying an existing
app symbol.

### 3. Generate up to three comparable concepts

For raster or material-rich directions, use the available image-generation tool. Use one call per
distinct concept. Keep the prompts comparable in framing, polish, and output scale.

Build a compact concept matrix. Keep scale and finish comparable, while varying the semantic
metaphor, material treatment, or palette only where that variation helps the user make a real
choice. For every candidate state:

- primary symbol and supporting gesture;
- palette with base, accent, and contrast role;
- why that palette fits the product and intended tone;
- how it remains recognizable on light/dark surfaces and at 32 px.

When no brand palette exists, make the candidates meaningfully different in color strategy rather
than producing three blue variations. Avoid arbitrary rainbow variety: derive hues from product
semantics, audience, market positioning, accessibility, and supplied references.

Require a single isolated square app icon. Exclude labels, text, Apple logos, checkmarks, pens,
snakes, diskettes, watermarks, grids, and surrounding UI unless product semantics require them.

Show concepts at full size and at 128/32 px. Do not integrate any concept before selection unless
the user explicitly requests autonomous selection.

### 4. Refine the selected concept without drift

Treat the selected image as the edit target. State invariants explicitly:

- preserve symbol, layout, proportions, approved palette, camera, and material identity;
- change only contrast, bloom, rim count, spacing, or local detail;
- do not reinterpret the icon as a new vector mark.

Perform one targeted edit per iteration. Compare the previous and new versions at actual 128 and
32 px sizes.

### 5. Build optical small-size masters

Do not rely on a single downscale for every size.

- At 128 px: retain material depth, reduce hairline highlights, strengthen internal glyphs.
- At 64/32 px: consolidate glass rims, increase local contrast, simplify low-value caustics.
- At 16 px: preserve the outer tile and dominant internal gesture; accept loss of micro-detail.

Keep glass convincing through broad refraction, one dominant edge highlight, one internal color
transition, and compact shadows. Never solve blur by flattening the approved concept into a
primitive symbol unless the user chooses that direction.

### 6. Prepare transparency

Prefer a source with clean alpha. If generation produces a uniform exterior background, remove
only the outside key color with conservative thresholds and inspect all four corners plus the
glass edge. Glass and reflections can retain background spill; validate visually on light and dark
surfaces.

Do not claim transparency from a checkerboard preview. Inspect the actual alpha channel.

### 7. Package platform assets

Ensure Pillow is available, then run:

```bash
python scripts/build_icon_assets.py \
  --source /path/to/icon.png \
  --small-source /path/to/icon-32-master.png \
  --medium-source /path/to/icon-128-master.png \
  --output-dir /path/to/output \
  --name AppIcon
```

The script creates:

- `AppIcon.iconset/` with all 10 macOS PNG representations;
- `AppIcon.icns`;
- `AppIcon.ico` with Windows sizes 16–256 px;
- `AppIcon-128.png` and `AppIcon-32.png` for review.

Use `--small-source` and `--medium-source` when optical masters exist. Omit them only for early
drafts.

### 8. Verify integration

After replacing application assets:

1. bump app version/build when desktop icon caching may hide the change;
2. rebuild the app from a clean build directory;
3. compare the source ICNS/ICO hash with the file inside the packaged app;
4. mount/open the installer and verify version plus icon inside it;
5. inspect Finder/Dock, Explorer/taskbar, and installer UI;
6. report architecture, signing, notarization, and cache limitations honestly.

Never infer that a DMG or installer contains the new icon merely because the source asset changed.

## Acceptance criteria

Deliver an icon only when:

- the palette source is recorded as brand-provided, reference-derived, or concept-proposed;
- no bundled example color was inherited without an explicit user choice;
- its meaning remains recognizable at 32 px;
- internal glyphs have sufficient contrast;
- glass rims do not merge into haze;
- 128 and 32 px previews are reviewed;
- alpha edges are clean;
- ICNS and ICO contain the required sizes;
- package contents are verified rather than assumed;
- source, optical masters, and packaged outputs have stable descriptive filenames.
