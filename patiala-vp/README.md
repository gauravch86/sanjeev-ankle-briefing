# NDBA / Patiala House — VP Strategy Pack (Sanjeev)

Internal campaign briefing page for **Sanjeev** (VP contest, Patiala House Courts Bar Association).

## View
Open `index.html` in a browser (needs network only for Chart.js CDN). Keep `categories.json` beside `index.html` so snapshot cards and chart bars can load name lists.

## Interactive snapshot
- Click any **Executive snapshot** card (or a bar in the lever / enrolment cohort charts) to:
  1. Open a sticky summary panel (count + plain-English meaning + campaign use)
  2. Jump to **11b. Category name lists** and populate the table (phones stripped)
- Search box filters the loaded category client-side. Large categories show up to 500 rows (P0 first) with a “Showing 500 of N” note.
- Secondary **Read strategy** chip jumps to the matching narrative section (`#junior`, `#geo`, `#chamber`, `#caste`, etc.).

## Share-safe
Phone numbers are removed from this public page and from `categories.json`. Full contact CSV stays private campaign material only.

## Files
- `index.html` — strategy pack UI
- `categories.json` — category → name rows (no mobiles), built from `../voters-tagged.csv`
