# YICHEN Drive visual verification — 2026-10-09

final result: blocked

## Findings and iteration history

- **[P2, fixed] Desktop catalogue touched viewport edges.** The supplied reference has outer gutters; the first browser capture showed cards and filters flush against the screen. Added 36 px horizontal padding to `.wrap.search-layout`, retaining 17 px on small screens. Revised browser measurement: left 36, right 1096, width 1060 at a 1132 px viewport. Before/after combined evidence: `catalog-comparison-before.jpg`, `catalog-comparison-after.jpg`.
- **[P2, fixed] Geographic labels became too small inside the map column.** Increased Chinese labels from 12.2 to 20 pt and English labels from 10.5 to 16 pt, increased callout offsets and brightened text. Regenerated 24 map images. Revised Chinese labels are readable and separated in the desktop capture. Evidence: `services-fullpage.png`, `services-fullpage-final.png`, `regions-comparison-final.jpg`.
- **Verification blocker:** documented viewport `set()` calls timed out without producing a mobile viewport. Default desktop browser operation continued to work; `reset()` succeeded. No mobile screenshot or responsive acceptance is claimed.

## Source and rendered evidence

Source truth: `design/reference-service-layout/catalog.png` (2264 × 1406), `footer.png` (2242 × 468), `regions.png` (2220 × 1366). These are the user's supplied layout references, with a different brand, six example vehicles and eight example city cards.

Rendered implementation: actual in-app browser at `http://127.0.0.1:8766/`. CSS viewport measured 1132 × 991. Native viewport screenshots initially returned only 1132 × 704; full-page browser captures were therefore used for complete content comparison. Sources are approximately double density. Source and implementation regions were proportionally scaled to equal comparison-column widths; no pixel-exact fidelity is claimed for different content or section heights.

Evidence folder: `design/browser-qa-20261009/`.

- `catalog-fullpage-after.png`: 1132 × 3217; focused first-row crop `catalog-first-row-after.png`: 1132 × 439.
- `services-fullpage-final.png`: 1132 × 2067, captured at scroll zero, with all twelve cities. Focused crop `regions-final.png`: 1060 × 852.
- `destinations-landmarks.png`: 1132 × 1196, centered landmark images and complete footer.
- `footer-after.png`: 1132 × 392, cropped from the real destination page capture.
- `services-en-fullpage.png`: English service page after language switching.
- Combined source/implementation images actually opened and judged: `catalog-comparison-before.jpg`, `catalog-comparison-after.jpg`, `footer-comparison-after.jpg`, `regions-comparison-final.jpg`.

Focused regions were necessary to inspect vehicle framing, contacts, typography and map labels. Full-page captures made while scrolled show the sticky header at its current offset; the final service screenshot was captured at scroll zero to remove that capture artifact.

## Required fidelity surfaces

**Typography:** browser computed style confirms the YICHEN wordmark uses Times New Roman / Times / serif. Main headings retain the existing Chinese serif hierarchy; body/card names use the existing sans serif. Names, prices, email and address show no visible truncation in inspected desktop states. Branding adapts the reference to YICHEN.

**Spacing:** three catalogue columns, consistent 3:2 photo frames and corrected outer gutters. Footer has four columns. Service map remains left, city cards right. Twelve cities need six rows rather than the reference's four, explaining the taller section. Document width and scroll width were both 1132 px on inspected catalogue, service and destination states.

**Colors:** dark olive card bodies, pale photo surfaces, muted green accents and existing cream YICHEN background are retained. The reference uses dark studio imagery; current vehicle sources retain light or real-world backgrounds. Consistent framing is verified; identical lighting, photographic style or camera angles are not claimed.

**Images:** all twelve catalogue photos loaded with nonzero natural width. Whole vehicles display with `contain`. Three city-landmark images loaded with computed `object-position: 50% 50%`. The saved Sichuan geographic data is used for the map; Chinese labels were visually checked after the fix. New destination photographs and licensing decisions await the research report and user selection.

**Copy:** all four requested city summaries appear correctly. Twelve city links, actual supplied email/address and the requested blank phone are respected. No example phone, invented capacity/equipment or fabricated availability was added. English map and contact content updated correctly.

## Actual checks

- Buick filter returns two GL8 models; clearing filters restores the collection.
- Mianyang selection changes the route, pressed city, selected heading, email subject and highlighted map.
- English switch changes the map to `mianyang-en.png` and translates service/contact content; Chinese restores correctly.
- City-landmark filter returns three centered, loaded photo cards.
- Footer email/address targets were inspected; no enquiry was sent.
- Warning/error log checks returned empty lists for inspected service/destination states.
- `node work/ui-check.cjs en`: 41 templates and functional checks passed; zero remaining Chinese phrases in English output.

## Implementation checklist

- [x] Correct catalogue gutters and map label readability.
- [x] Capture and compare actual desktop implementation against supplied references.
- [x] Check brand filter, city selection, bilingual map, contacts and centered photographs.
- [ ] Verify mobile layout/scrolling when browser viewport control works.
- [ ] Import 5–10 distinct sourced images for each of 30 existing/proposed destinations.
- [ ] Obtain photo choices and optional-addition approvals before updating the live destination collection.

Desktop findings were fixed and rechecked. Overall handoff remains blocked on mobile evidence and the separate photo-selection deliverable. The old local-browser-access blocker is superseded.
