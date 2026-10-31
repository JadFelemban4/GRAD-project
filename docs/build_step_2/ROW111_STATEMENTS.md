# Row 111's two statements, for the four-engine test only (to be signed by 1 November 2026)

Row 111 of `results/VALIDATION_DECISIONS.md` (option A, answered by both on 30 October)
asks both of you to sign two written statements by 1 November 2026, the day decision 25
names. Each statement holds for the four-engine test of decision 24 only. Each is cited
and disclosed in its preregistration (ORDER step 20). Neither changes `CLAUDE.md` for any
other experiment. The text below is row 111's own, set out to be signed, with one sentence of
(ii) corrected by row 127 (the B58's plant_sha moves at the plant commit, ORDER step 14). It was
drafted by the AI agents on 31 October 2026. From 31 October Ghassan works alone (row 133), so
each statement counts once Ghassan's column is filled.

## (i) Rule 2, amended for this test (decision 25)

> For the four-engine test only, rule 2 of `CLAUDE.md`'s rules for an experiment that will
> be reported ("Train from a clean, pushed commit whose `train.py` and `fingerprint.py` are
> `main`'s") reads instead: **train from the commit the preregistration names, clean and
> pushed.** Today `main` is `cf43fbb`, X1's plant. On `GRA-test`, `train.py` and
> `fingerprint.py` differ from `main`'s by 177 and 279 changed lines (row 111, MEASURED:
> `git diff --stat main GRA-test -- train.py fingerprint.py`), and `main` stays X1's plant
> until drive C's stage C.

## (ii) Gate item 6, waived for this test

> For the four-engine test only, the training gate's item 6 ("Drive C (knock), before
> drive A", which puts drive C before any training) is waived. The four-engine test trains
> before drive C. This waiver is what decision 25's fallback implies but does not write. In
> return:
> - every result is reported with and without the knock term (gate item 3). For the three
>   EPA engines this holds permanently, since their knock model is untested
>   (the contract, `results/ENGINE_THRESHOLDS.md`:1662-1664);
> - the B58 that is drawn on, measured on and scored on is X1's plant `cf43fbb`, frozen for this
>   test (decision 31): plant_sha 865f8e7b7e5c2dbe until the plant commit (row 94), whose code
>   edits move the plant_sha while the B58 stays identical at its defaults (its engine_sha
>   unchanged and the B58 identity certificate L1-L7 re-run, rows 94 and 117; row 127);
> - a stage-C retune enters only after scoring, as decision 31 says of new drives.

## Signatures

| statement | Ghassan | Jad |
|---|---|---|
| (i) rule 2 amended for this test | signed 31 Oct 2026, recorded by the agents on Ghassan's instruction (row 133 (4)) | not filled (row 133 (1)) |
| (ii) gate item 6 waived for this test | signed 31 Oct 2026, recorded by the agents on Ghassan's instruction (row 133 (4)) | not filled (row 133 (1)) |

Ghassan's instruction of 31 October, which the agents record as his signature of both:
"mate image me working alone no one else and honestly i dont want to do things myself do all the
steps approve what you recommend and i am with you". This file is committed before the draw (row 111: "The draw (row 96) waits for
this row's answer"). `CLAUDE.md`'s bracket on gate item 6 should say the item is waived for the
four-engine test, citing this file; that edit is Ghassan's (row 133 (4)).
