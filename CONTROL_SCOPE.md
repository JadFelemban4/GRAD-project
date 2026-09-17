# CONTROL_SCOPE.md — why the agent controls a simulator and not the car

**Status: draft for team discussion, 16 September 2026.** Nothing in here is
checked by `verify_docs.py` yet. Two claims in section 2 are marked UNVERIFIED
on purpose — read them before repeating them to anyone outside the team.

---

## ملخّص للفريق (اقرأ هذا أولًا)

الخطة الأولى كانت: **العميل يتحكّم بالمحرك مباشرة.** لم نتراجع عنها اقتناعًا —
اصطدمنا بحاجزين:

1. **لا نملك صلاحية الكتابة على وحدة التحكّم.** نقرأ عبر OBD-II فقط. الكتابة
   تتطلّب أدوات برمجة ووصولًا لا نملكه، وعلى الأرجح وحدة موقّعة تشفيريًا —
   **وهذا الأخير لم نتحقّق منه بعد، ولا يُقال لشركة قبل التحقّق.**
2. **السلامة.** سيارة طريق واحدة، يقودها أحدنا يوميًا، على طريق عام في جدة. أمر
   شرارة أو إثراء خاطئ يتلف محرّكًا أو يسبّب حادثًا. لا داينو، لا مقبض إيقاف
   طارئ، لا طريقة للتراجع خلال جزء من الثانية.

فبنينا الانقسام التالي، **عمدًا لا اضطرارًا**:

| أين | ماذا يفعل العميل |
|---|---|
| **المحاكي** | تحكّم كامل، خمسة أذرع |
| **السيارة الحقيقية** | قراءة فقط. يراقب ويُنبِّه. لا يكتب أبدًا |

**وما يجب أن يُقال بدقّة لشركة سيارات، لا أكثر ولا أقل:**

> «القيد لديكم ليس قيدًا. نحن لم نستطع الكتابة على وحدة التحكّم، لا لأن الفكرة
> لا تعمل، بل لأننا فريق طلابي بسيارة طريق واحدة. المعيار نفسه — H/τ — قابل
> للقياس على منصّة اختبار لديكم في أسبوع، والنتيجة تُخبركم **قبل البناء** ما إذا
> كانت معلومة الاستباق تستحقّ كلفتها على أيّ مكوّن، لا على محرّك واحد.»

**تحذير قبل أيّ عرض:** لا تقل «في المحاكاة الأمور تمام» بعد. الطور D لم يبدأ،
ولم يُدرَّب أيّ عميل، وأرقام المحاكاة الحالية تحت التصحيح — انظر
[AUDIT.md](AUDIT.md) والقسم 6 في الأسفل.

---

## 1. What the original plan was

The agent was to command the engine directly: read the road ahead, and set
spark, mixture and boost before the load arrives. That is still what the agent
does — inside `engine_env.py`. Five levers, full authority, every step:

| lever | range | kind |
|---|---|---|
| spark advance trim | −8° to +4° | trim on what the baseline ECU commands |
| lambda trim | −0.15 to +0.06 | trim |
| boost trim | −40 to +15 kPa | trim |
| cooling fan duty | 0.0 to 1.0 | **absolute command** |
| coolant pump duty | 0.3 to 1.0 | **absolute command** |

Source: `ACT_LO` / `ACT_HI` in [engine_env.py](engine_env.py). The zero action
reproduces the baseline ECU exactly, so every reward figure is
baseline-relative by construction.

**The control problem was never abandoned. Only its target moved** — from a
road car to a validated model of that road car.

---

## 2. The two things that stopped us, stated at the confidence we actually have

### 2a. Write access — UNVERIFIED in its strong form

What is **certain**: everything this project has ever done to the vehicle is a
read. Nine drives, 175.5 minutes, logged through BimmerLink over OBD-II. The
channel census in [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) enumerates
all 656 channels the car offers — all of them readable, none of them writable
through that path. Writing a calibration is a different operation entirely:
flashing the DME, with tooling and authorisation we do not have.

What is **NOT verified, and must not be asserted to an OEM**: that this
particular engine computer is cryptographically locked. It is widely reported
that BMW's current-generation DMEs ship signed and encrypted firmware, but
**nobody on this team has opened a source that states it for the unit in this
car, and nobody has recorded which unit this car carries.**

> **Before saying the word "encrypted" to BMW or Porsche, do this:** record the
> DME part number from the vehicle, and find one primary source for its
> firmware protection. BMW knows exactly what is in their own car. Asserting
> something wrong about it in front of their engineer costs more credibility
> than the point is worth.
>
> The safe version needs no source at all: **"we had no write authority and no
> tooling."** That is true, sufficient, and unattackable.

This is the same rule the project already applies to every published band —
see [REFERENCES.md](REFERENCES.md): never promote a claim from memory.

### 2b. Safety — needs no citation

One road car, owned by a team member, driven on public roads in Jeddah. A
supervisory agent writing spark, lambda or boost to that engine has:

- no dynamometer and no test cell,
- no abort path that acts inside one combustion cycle,
- no second observer, no instrumented exhaust, no cylinder-pressure sensing,
- and a failure mode — sustained knock, or a lean excursion under boost — that
  destroys the engine in seconds and is invisible until it has happened.

The project's own damage model says why this is not a conservative posture but
an arithmetic one: turbine damage is `exp((T − 1123)/45)`. An exponential
failure surface with no fast abort is not something a student team puts a
partially trained neural network on top of.

### 2c. The third leg, which we should also say out loud

Scope. Five undergraduates, one shared car that somebody needs on Sunday
morning, and a graduation deadline. Even with a fully unlocked ECU, calibrating
and validating a real supervisory controller on a real engine is a different
project with a different budget.

---

## 3. What we built instead, and why it is a design rule rather than a regret

The constraint is written into the repository as a rule, not as an apology —
[CLAUDE.md](CLAUDE.md), "Hard constraint, no exceptions":

> The project never writes to the vehicle's ECU. Read-only OBD-II logging only.
> If a task seems to require writing to the car, it is the wrong task. Say so
> rather than finding a way.

And the sharpest sentence, from [README.md](README.md):

> Suggesting an ECU parameter as text is a different product from applying one,
> **and they must never share a code path.**

That is the whole architecture in one line. Two products, deliberately
separated:

| | the agent | the app (`app/`) |
|---|---|---|
| lives in | `engine_env.py`, a simulator | beside the real car, in real time |
| authority | full, five levers | none. It cannot write |
| output | control actions | three kinds of alert, three audiences |
| validated by | Phase D (not done yet) | replay against our own nine drives |

The read-only property is not a promise in prose — `app/test_replay.py` asserts
it, so breaking it fails a test rather than going unnoticed.

---

## 4. The paragraph to put in front of a car company

> We set out to build a supervisory agent that acts on the road ahead. We could
> not run it on our own vehicle: we have no write authority over the engine
> computer, and no safe way to let a partially trained policy command spark and
> boost on a road car. So we did two things instead. We calibrated a cycle model
> and a thermal network against 175.5 minutes of read-only logs from that car —
> over 22 pooled steady operating points at 30–74 kPa the modelled load agrees
> with the vehicle's own to 1.4 %, with no fitted parameters — and we gave the
> agent full authority inside that model.
>
> That turned the project into something more useful to you than one more
> controller. The question we answer is not *"can preview control work"* — you
> already ship that. It is **when preview information is worth acquiring at
> all**, governed by one dimensionless ratio, H/τ: the preview horizon divided
> by the thermal time constant of the component being protected. If that
> criterion holds across dissimilar plants, it tells an engineering team whether
> preview pays **before** they build the sensing, the mapping and the
> connectivity to get it.
>
> The two barriers that stopped us are not barriers for you. On a test bench
> with a calibration seat, this is a week of work.

**Say the limits in the same breath.** The validation covers 30–74 kPa only;
the load residual is a consistency check between two ECU channels and does not
by itself validate the breathing model; the turbine heat capacity that sets τ is
an assumed number, which is exactly why it is swept over a factor of 75. An OEM
engineer will find all three in under a minute. Stating them first is the only
version of this conversation that survives.

---

## 5. What an OEM engineer will ask, and the honest answer

| question | answer |
|---|---|
| "How do we know the simulator is right?" | 22 pooled points, 30–74 kPa, 1.4 % load residual, zero fitted parameters — and read `CLAUDE.md` mistake 12 for what that residual does *not* test. 8 of 11 published bands inside, three documented misses, not tuned away. |
| "So you never ran it on an engine." | Correct, and we say so first. That is the bench work, and it is the natural next step. |
| "Why should we care about H/τ rather than your controller?" | Because the controller is yours already. The criterion is what tells you, before building, whether the preview earns its cost — on a turbine housing, a battery pack, or anything with a thermal memory. |
| "Your turbine heat capacity is assumed." | Yes, and stated. The claim is about the ratio, not about one housing, which is why `generality_test.py` sweeps it from 800 to 60 000 J/K. |
| "Did you tune anything to make it look good?" | A rejected `ambient + 8 K` fit scored *better* than the shipped model and was thrown out for being tuned to the target. It is documented in `plant.charge_temperature()`. |

---

## 6. Before anyone shows this to anyone — the honest current state

**Do not say "in simulation everything works" yet.** As of 16 September:

1. **Nothing has been trained.** `train.py` has never run past its import guard.
   Phase C is the next step, and Phase D — the agent beating two baselines with a
   preview ablation — has not started. It is the project's passing floor.
2. **The simulation headline figures are under correction.** [AUDIT.md](AUDIT.md),
   15 September, found the premise numbers reproduce exactly but are mislabelled:
   the baseline row runs with its cooling disabled, the baseline ECU is scheduled
   on a manifold pressure the engine is not at, and the measured preview edge is
   protection depth rather than anticipation. Until those are fixed, quote no
   simulation-derived number — only the dataset figures, which survived the audit.
3. **What is safe to quote today:** nine drives, 175.5 minutes, 22 operating
   points, 30–74 kPa, 1.4 % load residual with zero fitted parameters. That is
   what [ABSTRACT.md](ABSTRACT.md) restricts itself to, for this reason.

---

## 7. If we ever do want real control — the legitimate path

It is a bench, not a road car, and it stays inside the hard constraint because a
bench is not "the vehicle".

1. An engine on a test stand or a hardware-in-the-loop rig, with an open
   calibration interface and a hardware abort.
2. An authority envelope enforced in hardware, not in the policy: the agent may
   only trim within limits the rig itself clamps.
3. A pre-trained policy, frozen — no exploration on real hardware, ever.
4. Cylinder-pressure or knock-sensor instrumentation, so the knock integral the
   model predicts can be checked against what the engine actually does. This is
   also the open item `AUDIT.md` H5 raises against the model itself.

None of that is available to this team. All of it is ordinary at an OEM. That
asymmetry **is** the pitch.

---

## 8. How it would reach a driver — the delivery chain

The team's preliminary plan, recorded 16 September so it is not lost, with the
three corrections it needs before anyone builds it.

**As proposed.** OBD-II streams live with nothing recorded; the phone's GPS
supplies the road ahead; the stream reaches a local n8n instance through an API,
then a dashboard, then notifications to the driver or to a company; and, as
future work, the ECU. Target latency: half a second from the port to the message.

**What is strong in it, and it is the important part.** GPS is a real source for
**H**. Today `_preview()` in `engine_env.py` reads the grade ahead out of a
synthetic scenario array — the preview horizon is handed to the agent for free,
and nothing in the project says where it would come from on a real road. Phone
GPS plus a road-elevation source supplies it, which turns H from an assumption
into a measurement. Note that GPS alone gives position, not the slope ahead: an
elevation source is needed too, and H in seconds is distance ahead ÷ speed.

**Correction 1 — half a second is not available, and is not needed.** The
adapter polls one channel per round trip, so the link rate divides by the channel
count: measured on this car, 7.5 s per channel at 26 channels and 1.45 s at 7.
The bottleneck is the OBD port, not the network, and no software downstream can
recover it. It does not matter: the protected component's time constant is about
48 s, so a 1.5 s sample interval is 3 % of it. Optimising the transport below a
second optimises the wrong number.

**Correction 2 — the physics has to run somewhere, and it is missing from the
chain.** Turbine temperature is not a channel that can be read; it is the output
of `app/estimator.py` running the cycle model and the thermal network on every
sample. n8n does not run a combustion model. The corrected chain is: OBD → a
Python service holding the estimator and the alert engine → two outputs.

**Correction 3 — split the chain by audience, which the code already does.**
`app/alerts.py` classifies every alert as driver, mechanic or engineer. Route
them accordingly: the thermal alert goes to the driver directly and locally, and
must never depend on n8n or on a network, because it has to work in the place
where it matters; the mismatch and novel alerts can take the slow path through
n8n to a workshop or to the team.

**One decision deferred, and it is not a bug.** "Nothing recorded" stops being
true the moment anything reaches a company: that is a recording, off the car and
off the phone. The current privacy model is strict — raw data never touch disk,
only marked events, and `app/test_replay.py` asserts it. Decide explicitly what
leaves the device, and write it down, because it changes what the product is.

---

## Open items on this document

- [ ] Record the DME part number from the car, and settle section 2a.
- [ ] Settle which engine version the car is (285 kW vs 250 kW) — it decides the
      compression ratio, and it is already open in `REFERENCES.md`.
- [ ] Decide with the team whether this becomes a "Limitations and future work"
      section in the thesis, a slide, or both.
- [ ] Re-read section 6 before any external presentation; it goes stale fastest.
