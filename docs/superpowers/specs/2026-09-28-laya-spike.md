# Laya on this machine — a runtime spike before M3

28 September 2026. Jad asked to add Laya, a local model, beside jev in the agent
replay page's hidden panel (design walkthrough log, 28 Sep rows). Before
designing, a spike ran Laya on Jad's machine. **It is a runtime probe, not an
evaluation of Laya's quality**, and Laya's own README says an example result
does not mean it suits engine control. Nothing in the repository or in the Laya
folder was written; a socket guard recorded every connection attempt.

Laya: `C:/Users/admin/Documents/Local AI/laya`, model
`convaiinnovations/laya-multilingual` at revision `e4e9ddf`, package laya
0.3.20, Apache 2.0, its own `.venv` with PyTorch.

## 1. It runs, locally and fast

| quantity | measured |
|---|---|
| Application Control | blocked nothing in Laya's `.venv` |
| device | cuda (RTX 5070); weights float32, inference under bf16 autocast |
| model load | 4.0–5.2 s (first run of the day 32.7 s for the whole script: cold disk cache) |
| one five-question call, warm | 34 ms |
| GPU memory while resident | about 1.7 GB of 12.2 GB |
| network | 0 connection attempts across every load and call (offline flags + socket guard) |
| determinism | identical answers over 11 calls; no sampling (argmax) |

The server's system Python has no transformers, safetensors or laya, so the
recommended bridge is a **persistent worker process** running Laya's own
python, JSON lines over stdin/stdout: spawn to ready 6.2 s, then 34 ms a call;
closing stdin ends it in 0.7 s. Laya prints warnings to stdout, so the worker
must keep stdout for protocol lines only.

## 2. Its answers follow the ORDER of the options, not the engine state

The trial asked the design's five questions (§7: spark trim, lambda trim, boost
ceiling, fan, pump; five levels each) about a real simulated moment: mid-climb,
turbine housing 881 °C, 31 K over the 850 °C protection limit.

| question | Laya's choice | its probability |
|---|---|---|
| spark trim | advance 4° (the most knock-prone, hottest option) | 0.74 |
| lambda trim | leaner by 0.06 (hotter exhaust) | 0.50 |
| boost ceiling | no change | 0.98 |
| cooling fan | 100 % | 0.37 |
| coolant pump | 100 % | 0.36 |

- **A flat road at 434 °C** gave the same five choices.
- **Priorities changed to protect components 0.9** gave the same five choices.
- **The same options listed in reverse order** changed four of the five
  choices; fan and pump picked whichever option was listed last both times.
  Only boost's "no change" survived the reversal.
- On the hot climb it chose to advance spark and lean the mixture — the
  opposite of protecting a turbine over its limit.

**Reading, and its limit:** on this one probe Laya's answers track where an
option is listed, not what the engine is doing. That is a measured runtime
fact on five questions about two moments; it is not a benchmark, and a
different prompt or question wording might behave differently. Whatever the
page shows of Laya must carry this finding beside it.

## 3. Details any design must respect

- Laya's `confidence` is normalised entropy and is **not calibrated**;
  `answer_confidence` (max p) is the calibrated one.
- The state is cut from the right past about 900 tokens, so the task paragraph
  (serialised after the engine block) would be dropped first, silently.
- If GPU memory runs out, Laya moves to the CPU silently and its numbers change;
  the device should travel with every answer.
- One write path exists in laya (`_fix_tokenizer_config` rewrites a file inside
  the model folder); it is a no-op on this install.

The spike's scripts are in the session scratchpad and are not kept.
