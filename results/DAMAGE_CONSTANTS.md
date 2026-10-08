# The damage formula, constant by constant

7 October 2026. Asked by Ghassan: *"Every constant in the formula is a design
choice, not a property of the car. Look for every constant, and if we can
calculate it, do it."* Every number here is printed by `python damage_constants.py`
(`results/damage_constants.json`, `results/figures/damage_constants.png`).

```
d = exp((T_turb − 1123)/45) + 0.4·exp((T_oil − 408)/12) + 40·max(0, KI − 0.85)²     per second
```

**Nothing in `engine_env.py` changed.** The formula is the reward's, it sets
every damage figure, and its turbine knee is the hand-written policies' trigger
(`TURB_PROTECT_K`). Adopting any value below means retraining, so it is a
decision for Jad and Ghassan, made in the next preregistration.

## What the structure settles before any source

- **A weight and a knee in one exponential are one number:**
  w·exp((T − K)/s) = exp((T − K − s·ln w)/s). The oil term's 0.4 and 408 K are
  a single reference temperature, **397.0 K (123.9 °C)**, where the oil term is
  1 per second.
- **Only relative damage is reported** (cut against the baseline ECU under the
  same formula; decision 5), so a factor on all three terms changes nothing
  reported. What remains to set: two temperature scales, where the oil and knock
  terms sit against the turbine term, and the knock term's shape.

## The seven constants

| constant | published | can anything set it? | result |
|---|---|---|---|
| turbine scale | 45 K | **calculated for one mechanism.** Creep rupture follows Larson–Miller, t_r = 10^(P/T − C); at constant stress its e-folding scale is T / (ln 10 · (C + log t_r)). With C = 20 (Abdallah et al. 2014) | **20.3 K** for a 10 000 h life; 19.5–21.2 K over 10³–10⁵ h |
| | | Oxidation (parabolic scale growth) has scale R·T²/Q | the published 45 K **is** Q = 233 kJ/mol; no opened source gives Q for the housing's alloy, and BMW names only "cast steel" (ST1505 §5.2.1) |
| | | Thermo-mechanical fatigue, which housings are designed against, is counted per heat-up cycle (BorgWarner: life "calculated based on load spectra") | no per-second rate can stand for it; it would be a different formula |
| turbine knee | 1123 K (850 °C, housing node) | **bracketed.** A published GAS limit has to be carried to the housing node: at steady state thermal.py's turbine node sits r = 0.142 of the way from the gas to the ambient (read off the baseline's own climb, which ends at 1022 °C gas, 883 °C housing). The published knee is therefore 984 °C of gas | 900 °C gas (BorgWarner load-spectrum parameter) → **778 °C**; 930 °C (Conway et al. 2018) → **804 °C**; 1050 °C (BorgWarner, cast-steel housings) → **907 °C**. Which limit the knee means is a choice |
| oil scale | 12 K | **calculated from a rule of thumb**: "for every 10 °C the rate of lubricant oxidation doubles" (Fitch 2024) is 10/ln 2 | **14.4 K**. The rule is not universal (Holloway 2026). The one oil paper found with activation energies (Tripathi & Vinu 2015) measures decomposition under nitrogen, a stability marker, and is NOT used |
| oil weight and knee | 0.4, 408 K | one number (397.0 K); a **valuation** of oil life against housing life | needs each component's life and cost; nothing physical sets it |
| knock knee | 0.85 | **cannot yet**: drive C gives the knock integral at which the car's own ECU starts to retard | — |
| knock weight, square | 40, 2 | a **valuation**: no published law gives knock damage per second from a knock integral | — |

## Do the conclusions move? The twenty frozen episodes, re-scored

All 24 policies, from their per-step records. The published formula gives back
every committed damage first (worst relative difference 1.0e-07).

| formula | current-grade cut | sighted / blinded median cut | agents beating current-grade | ablation, sighted − blinded, 95 % CI |
|---|---|---|---|---|
| as published | 43.4 % | 67.9 / 65.4 % | 20/20 | +1.17 [−4.44, +6.78] |
| turbine scale 20.3 K (creep) | 73.5 % | 91.3 / 90.2 % | 20/20 | +1.01 [−2.30, +4.32] |
| oil scale 14.4 K (10 °C rule) | 43.1 % | 67.4 / 64.9 % | 20/20 | +1.17 [−4.40, +6.73] |
| both calculated scales | 73.2 % | 91.0 / 89.9 % | 20/20 | +1.01 [−2.29, +4.31] |
| knee 778 °C (900 °C gas) | 46.8 % | 67.9 / 68.7 % | 20/20 | −1.06 [−6.72, +4.60] |
| knee 804 °C (930 °C gas) | 46.1 % | 67.9 / 68.2 % | 20/20 | −0.71 [−6.36, +4.93] |
| knee 907 °C (1050 °C gas) | 35.0 % | 65.2 / 58.3 % | 20/20 | **+6.33 [+0.35, +12.30]** |
| knee 907 °C, no knock term | 46.0 % | 65.3 / 66.7 % | 20/20 | −1.43 [−6.87, +4.01] |
| as published, no knock term | 47.2 % | 67.0 / 68.5 % | 20/20 | −1.50 [−7.10, +4.10] |

**The supervision claim holds under every calculated value**: all twenty agents
beat current-grade. (It does not survive forbidding spark advance —
`knock_margin.py` — which is a different question.)

**The ablation stays inconclusive under every calculated value except one, and
that one is the knock term.** With the knee taken from the 1050 °C rating, the
turbine term shrinks until the knock term is a fifth to a third of the damage
(19.6 % of the baseline ECU's, 33.3 % of current-grade's, 24.3 % of the agents').
Removing the knock term at the same knee brings the interval back to
−1.43 [−6.87, +4.01]. It is the one-step knock spike at the grade step (merge
review, finding 2), the same pattern as `damage_robustness.py`'s post-hoc
knock ×4 ruler. It is post-hoc, one look of many, and it rests on the knock
model that is untested against the car. It is not a preview result.

**What matters most is the turbine scale.** It sets how much a few kelvin of
housing temperature are worth. On the climb the turbine term is 85–93 % of
the damage of the baseline ECU, current-grade and the agents, and the oil term
0.9–2.4 %, so the oil constants barely move anything.

## What this asks of Jad and Ghassan

Decisions 8–10 in `results/VALIDATION_DECISIONS.md` (with the seven validation
decisions):

8. **Which mechanism the turbine term stands for.** Creep rupture (20.3 K,
   calculated), oxidation (45 K, which needs Q = 233 kJ/mol, not found for the
   alloy), or keep 45 K as a stated design value. Thermo-mechanical fatigue
   would be a new formula, not a constant.
9. **Which gas limit the knee means**: the 900 °C load-spectrum parameter
   (778 °C housing), Conway's 930 °C (804 °C), the published 984 °C equivalent
   (850 °C), or the 1050 °C cast-steel rating (907 °C). Moving it moves the
   hand-written trigger too.
10. **The oil scale**: 14.4 K from the 10 °C rule, or keep 12 K. Either way the
    oil term is 1–2.4 % of the damage on the climb.

The weights (0.4, 40) and the knock term's shape stay valuations, stated as
such. The knock knee waits for drive C.

## Sources, opened on 7 October 2026

- BMW Group University, *B58 Engine*, ST1505 (April 2015), §5.2.1: *"The exhaust
  manifold of the 3rd and 4th cylinder and the turbocharger housing form one
  single cast steel part"* (grey source, REFERENCES.md).
- Simon, V., Oberholz, G., Mayer, M., BorgWarner Turbo Systems technical paper on
  turbochargers for 1050 °C exhaust gas (BWTS library 105/327; undated, cites
  work of 2000), printed pp. 3–4: at 950 °C inlet the inner wall near the flange reaches
  the gas temperature, with about 100 °C of gradient inside the housing;
  Ni-resist D5S *"maximum application temperature of 850°C, in special cases of
  up to 900°C"*; *"the service life of the turbine housing is calculated based on
  load spectra. A deciding parameter in this regard is the percentage of time at
  full capacity at exhaust temperatures over 900°C … 5% of the time"*;
  heat-resistant austenitic cast steel for 1050 °C.
- Conway, G. et al., SAE 2018-01-1423, p. 10: 930 °C pre-turbine (REFERENCES.md).
- Abdallah et al., *Materials (Basel)*, 2014, PMC5453208: P_LM = T·(C_LM + log t_f),
  C_LM *"to be taken as 20 for metallic materials"*, and that it varies by alloy.
- Fitch, B., *Machinery Lubrication* (2024): *"For every 10°C (18°F) increase in
  temperature, the rate of lubricant oxidation doubles."*
- Holloway, M. D., *Plant Services* (28 September 2026): the 10-degree rule is
  not a universal law; the multiplier depends on the activation energy and on
  the temperature range.
- Tripathi, A. K., Vinu, R., *Lubricants* 3 (2015) 54–79: activation energies of
  oil decomposition under nitrogen. Opened and not used, for the reason above.
