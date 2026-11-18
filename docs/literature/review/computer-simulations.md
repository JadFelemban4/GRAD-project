# Computer simulations of engines, vehicles and buildings

Approved by Jad, 17 November 2026.

Jad's section of the literature review: one of the six kinds of study on the team's map
("Where each paper is used", Ghassan's page), each kind written by one team member. It feeds
the SP1 proposal's chapter 2. Claude drafted it from Jad's own notes in the Notion tracker,
and Jad reviewed and approved it. Citations here are tracker IDs; the team's combined draft
numbers them [15] to [18] in IEEE order, from `docs/literature/references.bib`.

Papers: B18, B31, B06 and A25, each read and annotated by Jad. The team's map also lists B02,
B10, B49 and A28 under this kind; Jad has not read them, and B49 is his next paper.

## The section

Four of the reviewed works test a look-ahead controller inside a computer model, not on real
hardware. Chen et al. [B18] simulated an engine's cooling on one drive with a 20-minute climb
in GT-SUITE, which the authors say was validated on a vehicle, without showing data. Liu et al.
[B31] used a diesel-engine model validated in earlier work, and later ran the controller on a
real embedded processor while the engine stayed a model. Prakash et al. [B06] reduced the car
to a point with no engine and computed fuel afterwards with a separate EPA model. Wei et al.
[A25] calibrated a simple heat-balance model of a broiler house on its own measurements, yet
the model still missed the measured temperature by about 2.5 K.

Inside these models, the controllers in [B18] and [B31] each used one preview length, about
4 min and 2 s. The studies in [B06] and [A25] varied it: 20 s matched full knowledge of the car
ahead [B06], and 4-8 h, about 0.7-1.5 times the house's fast time constant, regulated best,
with longer horizons no better [A25]. Most runs assumed a perfect prediction. The findings are
therefore only as good as each model, and this project, also a simulation, must state its
model's limits in the same way.

## Where each sentence comes from (pages of the tracker's PDFs)

- [B18]: one cycle with a 15 % climb at 40 mph for 20 minutes, 45 C (p. 3); the GT-SUITE
  model "was validated using real-world vehicle test data", with no data shown (p. 6); GPS sees
  the hill 240 s ahead (p. 6).
- [B31]: the FEV engine model was experimentally validated in its references [34] and [35]
  (p. 3); hardware-in-the-loop runs the controller on an A80Q7 board (Cortex-A15) and the
  engine model on a dSPACE SCALEXIO (p. 7); the 2 s horizon was chosen "to reduce the
  computational complexity" (p. 4).
- [B06]: the follower is a point mass and the planner "does not consider the engine"
  (p. 2-3); fuel from EPA's ALPHA model of a 2013 Ford Escape (p. 3); 20 s of preview matched
  the full-knowledge result (p. 1; p. 4, Fig. 3); "perfect prediction ... is assumed for all
  cases" (p. 5).
- [A25]: the heat-balance model was calibrated by grid search on the training segment (p. 6);
  replaying the farm's actions through it gives about 2.5 K error (p. 17); 4 h and 8 h
  (0.7 and 1.5 times the fast scale of 5.5 h) regulated best, 24 h and 48 h worse (p. 17-18).
- "Most runs assumed a perfect prediction": [B06] (p. 5), [B31]'s controller reads the future
  from a stored array (p. 7), and [B18] assumes GPS detects the hill 240 s ahead (p. 6);
  [A25] does not say.
