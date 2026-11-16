# Next session — on the laptop, from B31's methodology (written 16 November 2026)

Jad moved the reading to his laptop on 16 November: the PC is training and he does not
want to load it. Nothing in this session needs the PC. This file replaces
`NEXT_SESSION_2026-11-13_reading.md`. Jad opens the session with a line like «أنا جاد،
اسحب الفرع واقرأ NEXT_SESSION_2026-11-16_reading.md»: that line answers CLAUDE.md's
first rule (who you are talking to).

## 0. Before the first reply

1. `git fetch origin`, switch to `JMF-2340550-Literature-review`, `git pull`: the commit
   that adds this file must be there.
2. Read `CLAUDE.md`, `team/jad.md` (follow it all session),
   `docs/literature/READING_METHOD.md` (Dr. Hammam's method; its last section describes
   the tracker) and `SESSION_REPORT_2026-11-13_reading-B19-B18-B06.md` (how the last
   three papers went).
3. Check that the Notion tools are loaded. On 16 November they were not, until Jad
   reconnected the connector (`/mcp`, or claude.ai, Settings, Connectors). If they are
   missing, say so before anything else.

## 1. Where the reading stands

The tracker: the Notion database "Literature Tracker · متتبع الأوراق" (under the GRAD
Project Dashboard), data source `collection://3b224093-a84e-459e-8801-ed312f744055`.
Query a row by `"userDefined:ID"`: the SQL can show Reader empty.

- B37, B40, B19, B18: done (Annotated).
- B06: closed on 16 November. Its Critical synopsis is in the cell (read back); Jad kept
  Status at "Annotated". Related? Yes; Bears on our claim: Background only; Theme L5.
- **B31: in progress** (section 2).
- Then A25, B49, C20, C18 (section 3).

## 2. B31: Liu et al. 2023, IEEE TCST 31(6), the hierarchical look-ahead eMPC

Notion page `4159ef59-7fcf-81d1-92cb-fe293bb8d140`; 12 pages with a text layer. A diesel
air path (VNT turbo, HP and LP EGR) on FEV's EURO 6 2 L mean-value model. The upper MPC
(HeMPC) looks 2 s ahead in 0.1 s steps and sets the VNT; the lower one (LeMPC) looks 0.1 s
ahead in 0.01 s steps, without look-ahead, and sets the two EGR valves; both run every
0.01 s. The look-ahead is the future engine speed and torque, assumed known. WLTC, in
simulation and on HiL.

**Done on the PC, 16 November:** the abstract and the conclusion. Jad set Related? =
Unsure, and asked for Status = "Abstract and conclusion read" (written and read back).
Every other field is empty.

**Where we stopped.** The first methodology message was sent; Jad had not answered it.
It explained how the 2 s was chosen (p. 4, Section III.A). The example: a mother deciding
how many days ahead to plan meals (who will be home is known about 3 days ahead; frozen
meat needs a day to thaw; each extra day is more effort; so 2 days). In the paper: torque
autocorrelation says about 3.5 s is useful (Fig. 3a); the turbo-lag is about 1.4 s, and
boost affects torque for up to about 8 s (Fig. 3b); the controller must finish every
0.01 s; and "to reduce the computational complexity, this study uses a 2-s look-ahead
horizon" (p. 4). The point made: the turbo's lag set the floor, the computation chose the
number. Open with one line on where we stopped and let Jad write what he understood; send
it again only if he asks.

**Next, one idea per message, in this order.** These are Claude's notes from the PC, with
pages. Check each against the text before saying it, and never fill a field from them
(`READING_LIST.md` rule 4).

1. *Only one horizon.* 2 s is the only look-ahead the paper runs; no other length is
   tried (p. 4; the conclusion calls it "long", p. 10). p. 4 adds that 2 s "is in
   agreement with [18] and [40]". So the paper cannot say where preview stops paying.
2. *The lower MPC's 0.1 s.* p. 5: the same 0.1 s for both EGR loops, although LP EGR
   settles slower (up to 0.5 s at medium to high load, 1.5 s at low load, p. 4). It
   "enables to meet the computational feasibility criteria but at the cost of higher use
   of HP EGR". Careful: p. 5 also says a larger LP share lowers the pumping loss and so
   improves fuel economy. On the PC, Jad was told that returning exhaust does not cut
   fuel. Say precisely that this saving comes from *which* loop carries the exhaust, not
   from returning exhaust as such.
3. *The baselines (p. 3).* The eMPC of [19] (the same group, 2021): a single eMPC for the
   slow and the fast dynamics, without look-ahead. It differs from the LAeMPC in structure
   as well as in preview, so the gap is not preview alone. (The PC session also noted a
   different solver and tuning: not re-checked, check before saying it.) And a
   production-line controller: reactive, feedforward plus PI/PID ([35], [36]).
4. *Where it was tested.* WLTC in simulation (Table III, p. 7) and on HiL: the controller
   on a Cortex-A15 core of an A80Q7 board, the engine model on a dSPACE SCALEXIO (p. 7,
   Fig. 4; p. 10). No real engine anywhere: the HiL runs the same model. Worst-case
   execution time 8.9 ms (p. 10).
5. *Two sets of numbers.* The contributions list (p. 3) and the conclusion (p. 10) give
   different NOx and soot percentages, 0.2 points apart each; torque tracking is the same
   in both. Quote both before using either.
6. *Perfect preview, then a noise test.* The main results assume the look-ahead is
   exact. p. 9: a random delay of 0 to 2 s and multiplicative Gaussian noise; p. 10: the
   benefit fades, and disappears at a noise SD of about 13 % of the nominal speed and
   torque range. (Jad already has an example for this from the conclusion: a friend ahead
   on the road calling about traffic.)
7. *An automatic gearbox* (p. 10): the benefits "remain consistent".
8. *What it leaves out, and why.* p. 9: soot accumulation and DPF regeneration are not
   considered "for their longer horizon related to the temperature dynamics". The paper
   itself says the thermal problem needs a longer look-ahead than 2 s: the closest it
   comes to H/τ.
9. *Against H/τ.* H = 2 s against a turbo-lag τ of about 1.4 s (p. 4): a ratio of order
   one, chosen for computation and never varied; and this τ is a boost-pressure lag, not a
   thermal time constant.

**Leads to** (the references, p. 11): [18] Liao-McPherson et al., CCTA 2017 (a cascaded
eMPC with a non-uniform horizon) and [40] Liao-McPherson et al., Int. J. Robust Nonlinear
Control 2020 (diesel air-path emissions MPC, tested on an engine), both cited for the 2 s;
[19] Liu et al., Control Eng. Pract. 108, 2021 (the baseline eMPC); [32] Umezawa et al.,
Control Theory Technol. 2022 (hierarchical MPC for long and short horizons); [35] Vagnoni
et al., Int. J. Engine Res. (diesel control with predictive driving information); [38]
Shin and Sunwoo, IEEE T-ITS 2019 (speed prediction with a Markov chain).

**Then** "Bears on our claim" with the reason against H/τ, the Theme (B18 and B06 are L5
Predictive powertrain), and ask Jad before moving Status on.

## 3. After B31

Fetch each page with `include_file_urls` and download the PDF at once (the links expire
in 5 minutes), each into its own new scratchpad folder. "Read it for", as the tracker had
it on 16 November (re-read it from the row):

| ID | paper | Notion page | Read it for |
|---|---|---|---|
| A25 | Wei et al. 2026, L4 | `4159ef597fcf811dac28fb7307ba7ef8` | how the ≈0.7–1.5 τf rule was derived and tested |
| B49 | Laguna et al. 2022, L4 | `4159ef597fcf81c89696cd535a98d390` | the thermal-inertia period from the ARX lag order, against C/UA τ |
| C20 | Zeng, He and Wu 2025, L8 | `4159ef597fcf8133a4a9f02ab80c69e4` | how the ablation removes the slope signal; how many seeds |
| C18 | Hu et al. 2019, L9 | `4159ef597fcf81d4adb6cb24b5d13c29` | over which part of FTP-72 the PID IAE of 41.72 was computed |

## 4. The method (unchanged)

For each paper, one step at a time: the abstract and the conclusion first (a patent has
none: claim 1 stands in for it), and Jad sets "Related?"; then the methodology; then the
evidence and the rest. Explain in Arabic, a familiar example first, one idea per message,
the passage quoted with its page. Do not end with a check question: Jad writes back what he
understood, and you confirm or correct it. If he does not understand, change the example
and cut the numbers; do not repeat. He goes through the text himself; the fields hold his
words (type what he says, never your own summary). If he asks you to complete his notes,
write in his style (الي، انو، ف، ح), show him the text before it goes in, and list exactly
what you added. After each paper, help him set "Bears on our claim" with the reason
(against H/τ) and the theme, and ask him before moving "Status" on.

## 5. What was taught on 16 November, on the PC (for `team/jad.md` at the close)

The examples, in order:

- The abstract: a water heater and the shower mixer. The heater is slow, so you switch it
  on half an hour before; the mixer is fast, so you set it a second before; one shower,
  and each part looks ahead as far as its own speed. Jad took the slow part and the fast
  part and their two horizons, placed the EGR valve inside the turbo, and asked whether
  the paper does cooling.
- The air path: the car's A/C. The fan is the turbo pushing clean air; the recirculation
  button is the EGR valve returning part of the exhaust. Jad then traced the path right
  (air in, burnt, part of the exhaust back in), but said the burn becomes easier and fuel
  falls.
- The charcoal: blowing on it makes it hotter, covering it calms it; returned exhaust is
  the cover (less oxygen, a calmer burn, less NOx, more soot). Jad: «تمام».
- The conclusion's noise test: a friend ahead on the road calling about traffic. A small
  error still helps, a larger one helps less, and past some point it is as if he had not
  called.
- The 2 s: the mother planning meals (sent last; not answered yet).

The corrections made: the EGR valve is not in the turbo, it is its own pipe from the
exhaust side to the intake (p. 3, Fig. 1); the paper does no cooling, it controls air; the
burn becomes calmer, not easier; pollution falls because of the calmer burn, not because
less air leaves; returning exhaust does not cut fuel (see idea 2 for the nuance); the rest
of the exhaust is not wasted, it spins the turbo.

## 6. Tools

- The Read tool could not render PDFs on the PC (no pdftoppm); check on the laptop. A PDF
  with a text layer: `pdftotext` (Git for Windows ships it, `/mingw64/bin/pdftotext` in
  Git Bash); pages split on form feeds. A scan: render the pages to PNG with PyMuPDF and
  read the images.
- Put each download in its own new scratchpad folder and any script outside it; run
  Python that reads them with `-I`.
- On the PC, curl to Notion's file host failed inside the sandbox ("Empty reply from
  server") and worked with the sandbox off.
- The Notion connector can fail mid-write (ECONNRESET, "Internal server error"): read
  every write back before telling Jad it is saved.
- Write Arabic as characters, never as `\u` escapes: the Write tool decodes them into
  literal characters.

## 7. Rules (Jad's, verbatim)

Write only in the columns, never in a page body (the workspace is at Notion's free block
limit). Never put the brain's content in Notion or in this public repo. Never write to the
car's ECU; never run train.py without my yes. Commit by explicit path; push only where I
name it, naming the destination back first. Reply in Arabic.

## 8. At the close («قفلنا»)

This handoff did not rewrite `CHECKPOINT.md` or index anything: the close does, for the
whole of 16 November (the PC part above and the laptop part).

1. A session report, `SESSION_REPORT_2026-11-16_reading-....md`, on the pattern of
   13 November's: what was done, the tracker as left, what in the fields is not Jad's own
   wording, page pointers, tools, how the reading went, the checks, what is next.
2. `CHECKPOINT.md` item 11: rewrite it, and move the old text verbatim to the end of
   `STATE_HISTORY.md` as a new part (AU was 13 November's). Never append.
3. `HISTORY.md`: index this file, the report and the next prompt.
4. `team/jad.md`: the 16 November entry (section 5 and the laptop part).
5. The next prompt under a new name: never overwrite a file Jad has been handed.
6. `python verify_docs.py` needs Python 3.13.2 with the lock's packages (it imports
   stable-baselines3). If the laptop lacks them, say so in the close commit.
7. Commit by explicit path, never `git add -A` (another session may share a tree). Push
   only where Jad names, naming it back first; his branches are `JMF-2340550-*`, never
   `main`.
8. A short summary to Jad, in Arabic.
