# Destination expansion — 2026-10-09

Status: awaiting research report; photo catalogue is not complete.

Scope: `visual-assets/destination-expansion-plan.json` contains 13 existing destinations and 17 proposed additions, each requiring 5–10 independent real photographs. User explicitly approved adding **交子之环**, ID `jiaozi-ring`. The separately confirmed 锦江交子之桥 has ID `jiaozi-bridge`; never substitute their photos.

Special briefs: 四姑娘山日照金山、九寨沟晴天、青城山重新选图、天府广场正面图. Main-site destination/route images use centered positioning. Earlier user-confirmed choices remain in place.

Manus task: https://manus.im/app/Gk85EFZQ9bWSuxuQqpF6fy

Connector returned an asynchronous receipt but exposes no status/report retrieval tool in this session. One direct browser attempt timed out; web reader could not access the task URL. No report has been imported; no completion/failure is inferred. User was asked to send the exported report attachment.

`work/build-destination-catalog.py` prepares the next local review page from the complete JSON report. It checks all thirty places have 5–10 candidates, nonduplicate IDs/image URLs, source links and safe local paths. Incomplete reports are rejected before generating a page. The review supports six category filters, add/skip choices, keeping existing photos, centered full-image previews, source/rights notes, load failure states, local choice persistence and copyable results. It never replaces the live collection automatically.

Output target: `dist/destination-photo-catalog.html`. It does not exist yet because the report is unavailable. Apply new destinations/photos after user selection, retaining credits and original watermarks.
