# Lessons learned

## Visual direction

- Preserve a user-approved raster direction aggressively. A clean vector reinterpretation can be
  technically sharper while feeling like a different, more primitive icon.
- Separate a reference's transferable qualities from its incidental properties. Material depth,
  hierarchy, and edge control may transfer while hue, subject, and symbolism do not.
- Never encode one successful project's palette as a universal default. Ask for brand constraints
  when compliance matters; otherwise expose color as a reasoned concept choice.
- Use official platform icons to extract hierarchy and restraint, not to copy their subjects.
- Distinguish concept changes from optical corrections. Communicate which one is being performed.
- Keep one dominant symbol. A snake, diskette, pen, badge, and document cannot all compete.

## Small-size clarity

- A beautiful 1024 px render does not prove that 128 or 32 px versions work.
- Duplicate glass rims become blur after downscaling.
- White profile glyphs on a frosted white card disappear; use controlled local contrast.
- Sharpening alone cannot recover a weak silhouette.
- Create optical masters for 128, 32, and sometimes 16 px while keeping the same material language.

## Transparency

- A black or checkerboard preview does not prove that alpha is correct.
- Chroma removal around glass requires conservative thresholds and edge inspection.
- Keep source and cleaned-alpha files separately until validation completes.

## Packaging

- Rebuilding a PNG is not enough; rebuild iconset, ICNS/ICO, app, and installer in that order.
- Compare hashes inside the final bundle and installer to detect stale assets.
- `iconutil` may reject an iconset even when dimensions are correct; use a deterministic PNG-backed
  ICNS writer as a fallback.
- Windows needs a dedicated multi-resolution ICO and version-resource file.
- Bump build versions because desktop environments cache icons.

## Process

- Show no more than three comparable concepts.
- Obtain selection before replacing production assets.
- Make one targeted refinement per iteration.
- Validate at actual output sizes, not enlarged nearest-neighbor previews alone.
- Keep generated sources, transparent finals, optical masters, and packaged assets named
  independently.
