# What the official wayfinding PDFs really contain (Area B, B-01..B-04)

Source: the D-block wayfinding PDF (`yer-yon-haritalari-d-blok.pdf`, 7 pages = levels -2, -1, 0, 1, 2, 3, 4),
public on tedu.edu.tr and in our shared Drive (`491-492/Prototype/uploads`). It is not in the repo;
put it in `uploads/` to run the tools.

1. **Walls are a picture, not vector lines.** Each plan is an embedded image (~6800 px wide). Only the
   numbered room circles and all text are vector data. Project.md §7/§12 says "vector": that is wrong.
   Consequence: room names and positions can be extracted automatically (B-04), walls cannot; the
   walking graph (B-06/B-11) has to be drawn.
2. **Room codes are not only `D###`.** Level -1 has `DB014`–`DB022`, level -2 has `CB204`.
   Regexes in the backend/NLP must accept two letters (`[A-Z]{1,2}\d{3}`).
3. **The ground-floor PDF numbers plan and legend differently.** Plan markers 14–17 are the four big
   rooms on the east side, but legend rows 14–17 are small offices; plan markers 18–24 are the bottom-row
   rooms, but legend rows 21–24 are the amphis D026–D032. Floors 1–3 have the same building layout with
   correct numbers, so `data/floorplans/D/overrides.json` maps: bottom row = offices D001–D013, big east
   rooms = amphis D026–D032, marker 13 = cafeteria. **Marked `verified: false` → check on campus (S-04).**
4. **Floors are drawn at different zoom levels on their pages.** Floors 1 and 2 match exactly; floor 0 is
   ×1.04 and floor 3 ×0.89. Needed for aligning floors (later step).
5. **The library is in D block** (levels 3 and 4). On level 3 it has two markers (13) and sub-areas 13.1, 13.2,
   so a room can have several anchors.
6. **Advisor's office D207** is marker 21 on level 2 (confirmed).
7. **Prototype people data has rooms that do not exist** on the official maps: D314, D014.

Result of B-04: 125 rooms on 7 levels, each with Turkish and English name, type and position;
markers = legend rows on every level (`python tools/extract_rooms.py ...`, tests in `tools/tests`).
