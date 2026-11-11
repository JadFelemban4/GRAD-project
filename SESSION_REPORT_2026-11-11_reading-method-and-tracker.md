# Session report — 11 November 2026: Dr. Hammam's reading method, and the paper tracker in Notion

Jad's session on `JMF-2340550-merge-2026-11-11`. Nothing in the physics, the data
or the training changed. New: `docs/literature/READING_METHOD.md`, this report and
`NEXT_SESSION_2026-11-11_reading.md`; edited: `CHECKPOINT.md` (item 11),
`STATE_HISTORY.md` (parts AQ to AS), `HISTORY.md`.

## 1. What was done

- **The last session's close, committed** (`0fb89d3`): its report, its prompt,
  the rewritten `CHECKPOINT.md` and `HISTORY.md` had been written but not
  committed. Committed unchanged at the start of this session.
- **Dr. Hammam's lecture, transcribed and written up** (`98a2efd`). Both parts of
  the literature-review lecture (research methods, chapter 3; 25 and 16 minutes)
  were transcribed on Jad's PC with faster-whisper large-v3, language Arabic, and
  the 24 slides read from frames of the video. `docs/literature/READING_METHOD.md`
  holds the method with timestamps: the five stages, how to read one paper
  (abstract and conclusion first, then the methodology), how themes form, the
  writing rules of part 2, and the tracker's columns, each traced to a point of
  the lecture. The transcripts sit beside the videos in Jad's meetings folder,
  not in the repository (they hold other students' voices).
- **The tracker, in the team's Notion** (Jad chose Notion over Google Sheets): the
  database "Literature Tracker · متتبع الأوراق" under the GRAD Project Dashboard,
  one page per paper, the reading fields as columns, a page layout in sections,
  five views, and the reading order in its description (English and Arabic).
- **50 papers**: the 40 of `TOP40.md`, then 10 added at Jad's request for the 50
  Dr. Hammam aims for. The rule and the list are in `READING_METHOD.md`, last
  section.
- **The PDFs**: the 9 papers of Ghassan's `sources.zip` that are among the 40 and
  the thesis A06; 18 free texts downloaded from the list's links and checked
  against their titles; six that Jad added from his browser, each downloaded back
  and checked; 8 of the 10 added. 42 of the 50 have a file (counted from the
  table); `READING_METHOD.md` names the 8 without and why.
- **Jad's ten**: Jad is the reader of B37, B40, B19, B18, B06, B31, A25, B49, C20
  and C18, chosen to tell one story (what exists, then how close each comes to
  the claim), all with their PDF; he reads them with Claude in the next session.

Commits: `0fb89d3`, `98a2efd`, `a597017`, `9eb4541`, `86eb35b`, `9efa19f`, and the
close commit.

## 2. What was found and left alone

- **Notion's free plan has a block limit.** When the 40 pages went in, Notion
  reported the workspace out of free blocks, with a grace period to 14 November
  before adding content needs an upgrade. Every paragraph and heading in a page
  body is a block. Jad chose to slim the pages rather than pay or move to Sheets:
  the empty template headings were removed and the reading fields became columns.
  Whether the workspace is back under the limit was not measured.
- **Notion's free plan takes 5 MiB per file**, by its own refusal message. Larger
  PDFs were split by page range, every page kept.
- **Four publishers refuse an automated download**: HAL and AAAI with a bot check,
  Bath and MDPI with 403. They were not forced; a browser download works (Jad
  added six that way). C48 and C61 still wait for one.
- **Notion's SQL query does not show a file added through the app**; a fetch of
  the page does.
- **The GPU path of the transcription failed**: ctranslate2 could not load
  `cublas64_12.dll`, although a copy sits in the Python 3.12 site-packages
  (`nvidia\cublas\bin`, not on the DLL path). The CPU path (int8) did the work.

## 3. Checks at the close

- `python verify_docs.py`: read by its exit code, see the close commit.

## 4. Next

Jad reads his ten with Claude: `NEXT_SESSION_2026-11-11_reading.md`. Waiting on
Jad: readers for the other 40; C48 and C61 from a browser; whether to push this
branch; the housing-lag exporter's port (`CHECKPOINT.md` item 4); the paid D01,
A03 and C36.
