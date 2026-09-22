# ABSTRACT.md — the submitted abstract, mirrored from `DOC/`

> ## Status, 22 September 2026
>
> **One abstract was handed in, and section 1 is its text.** What went to the
> supervisor on 21 September is `DOC/Abstract_EN.docx` and `DOC/Abstract_EN.pdf`,
> and nothing else. Section 1 below was regenerated from that `.docx` on
> 22 September 2026 — the abstract body only; the cover page with the team's
> names and university numbers is left out. If the two ever disagree, the
> `.docx` wins: regenerate section 1 rather than editing it by hand.
>
> **Everything after section 1 is history or a draft, and says which:**
>
> - **section 1b** — the English abstract as this file mirrored it on
>   16 September, before the `.docx` was rebuilt on its cover-page template.
>   History.
> - **sections 2 and 3** — the last text of `DOC/Abstract_AR.docx` and
>   `DOC/Abstract_Simplified.docx`, deleted on purpose on 21 September. History,
>   not deliverables.
> - **section 4** — a short cut for a word limit, never in the submitted `.docx`.
>   A live draft: its dataset figures and its ablation sentence were brought up
>   to date on 22 September.
>
> The history sections carry the retired dataset. The submitted abstract, the
> draft and the shipped data do not:
>
> <!-- RETIRED-OK: 175.5, 22, 74, 9 -->
> | | sections 1b, 2 and 3 | section 1 (submitted), section 4, and the shipped data |
> |---|---|---|
> | minutes | 175.5 | **295.0** |
> | drives | nine | **ten** (section 1 names no drive count) |
> | operating points | 22 | **26** |
> | span | 30–74 kPa | **30–75 kPa** |

> **One sentence in the submitted abstract is wrong about the code, not just
> out of date.** Section 1 says preview is isolated "by re-evaluating that policy
> blind"; sections 1b and 2 say "the identical trained policy with its preview
> channel disabled". That is the construction `AUDIT.md` C3 voided — it cannot
> fail and it is not evidence. `evaluate.py` scores a *second* agent, trained
> with its preview channel zeroed, which is the defensible design and the one
> Phase D ran. Raise the wording with the supervisor rather than silently
> re-submitting (`NEXT_SESSION_2026-09-21.md`, step 3). See `AUDIT2.md` findings
> H2-1 and H2-6.
>
> **The submitted abstract also predates the project's result.** It was written
> before Phase D ran and describes the agent in the future tense. Phase D has
> since returned a null on preview — with agents trained to the C1 budget,
> preview does not separate from seed noise, and the blinded arm was not
> blind (`results/PREREGISTRATION.md` limit 7) — and, as a separate claim, the
> trained agent beats the `current-grade` comparator. Neither is in the
> submitted text; `CLAUDE.md` carries both.

**Figures in the submitted abstract (section 1), and only these:** 295.0
minutes of logs, 26 operating points, 30–75 kPa, 1.4 % load residual with zero
fitted parameters. **No simulation-derived figure is quoted** — no premise
numbers, no preview-edge points: the pre-audit premise figures are void
([AUDIT.md](AUDIT.md) C1–C3), and the abstract was written before Phase D ran.
See [CONTROL_SCOPE.md](CONTROL_SCOPE.md) for why the read-only boundary is
stated the way it is.

---

## 1 · As submitted — `DOC/Abstract_EN.docx`

*Regenerated from the `.docx` on 22 September 2026: abstract body only, cover
page omitted. The `.docx` wins if the two ever disagree.*

### When is preview worth acquiring? A dimensionless criterion, H/τ, for predictive thermal protection

A turbocharged engine protects its turbine housing only after damage begins: the control unit retards ignition once knock appears and enriches the mixture once exhaust gas is already too hot. Reinforcement learning could act earlier, given preview, meaning advance knowledge of the road gradient ahead.

Preview-based control is well established in automotive thermal management, yet preview is never free: it must be bought with mapping, connectivity, additional sensing and computation. The literature reports its benefit case by case and plant by plant, with no criterion that transfers between systems. An engineer deciding whether to acquire preview before building anything therefore has nothing general to consult.

This project proposes and tests a criterion governed by one dimensionless ratio: H/τ, the preview horizon divided by the thermal time constant of the protected part. If it holds, preview value falls on one curve in H/τ for any plant.

Completed pilot work calibrates a zero-dimensional cycle model and a three-node thermal network on 295.0 minutes of read-only OBD-II logging from the team's car; over 26 steady points, 30–75 kPa, modelled load matches the car to 1.4% with no fitted parameters. A deep reinforcement-learning agent (Soft Actor-Critic) will be trained and evaluated against a production baseline and a reactive policy under a fixed protocol, isolating preview by re-evaluating that policy blind. A battery plant tests transfer; non-overlap is a result.

The result is a design chart: knowing a component's time constant and the horizon available, an engineer can decide whether preview is worth buying. Manufacturers and researchers benefit. The physics runs live as a read-only supervisor estimating what the car cannot measure – protection before the damage, not after.

**Application field:** Automotive powertrain – engine thermal management, component protection, and on-board virtual sensing from read-only OBD-II data.

**AI area:** Deep reinforcement learning (Soft Actor-Critic) and preview-based predictive control.

**Keywords:** preview control; preview horizon; thermal time constant; dimensionless criterion; reinforcement learning; engine thermal protection; virtual sensing; OBD-II validation.

---

## 1b · The English abstract as mirrored on 16 September — history

### When is preview worth acquiring? A dimensionless criterion, H/τ, tested on two plants

<!-- RETIRED-OK: section 175.5, 22, 74, 9 -- the retired dataset, kept as history -->
*Superseded by section 1. Kept so the text is not lost; never hand it in.*

Preview-based control, which acts on a disturbance before that disturbance arrives, is well established in automotive thermal management. What is not established is when preview is worth acquiring at all. It costs sensing, mapping, connectivity and computation, and the literature reports its benefit case by case, with no criterion that transfers between systems.

This project proposes and tests such a criterion, governed by a single dimensionless ratio: **H/** **τ** , the available preview horizon divided by the thermal time constant of the component being protected. The hypothesis is that preview value collapses onto a single curve when plotted against H/τ, whichever physical plant produced the point. Two dissimilar plants test it: a turbocharged spark-ignition engine and an electric-vehicle battery pack. If the two do not overlap, the criterion is wrong or incomplete, and that outcome is reported as a result rather than discarded.

The engine plant is a zero-dimensional single-zone cycle model of a 3.0 L turbocharged inline-six, coupled to a three-node lumped-capacitance thermal network representing the block, the oil and the turbine housing, and calibrated against 175.5 minutes of read-only OBD-II logs recorded from the team's own vehicle across nine drives. Over 22 pooled quasi-steady operating points spanning 30–74 kPa manifold pressure, the modelled engine load agrees with the vehicle's reported load to **1.4 %, with no fitted parameters** ; the thesis states the limits of that agreement explicitly, since it does not by itself validate the breathing model. A reinforcement-learning supervisor is then evaluated against a production-style controller and a reactive protection policy under a fixed protocol, and the contribution of preview is isolated by re-evaluating the identical trained policy with its preview channel disabled.

Three artefacts are delivered. The criterion itself, as a design chart on which an engineer who knows a component's time constant and the horizon actually available can decide whether to buy preview before building anything. The validated simulation, the trained supervisor and the ablation table that stand behind that chart. And a working real-time application, which runs the same validated physics alongside the car on a laptop as a virtual sensor for quantities the vehicle has no gauge for — turbine-housing temperature, charge temperature, knock margin and accumulated thermal damage — presented through a dashboard, a glanceable driver warning raised before the estimated temperature reaches the knee of the damage curve, and a post-drive review of what the model marked, written for a mechanic.

Control and observation are deliberately separated, and the separation is stated rather than implied. Inside the validated simulation the supervisor holds full authority over spark advance, mixture, boost and cooling. On the vehicle itself the interface is read-only, and structurally so: the application issues no write commands and has no code path to the vehicle bus, and raw vehicle data are never written to disk — only the events the model marks. That boundary follows from having neither write authority over the engine computer nor any safe way to let a partially trained policy command a road car; it is reported as a scope decision rather than as an omission, and transferring the supervisor to real hardware belongs on an instrumented test bench, which is identified as future work.

*Keywords: preview control; predictive thermal management; dimensionless criterion; reinforcement learning; engine thermal protection; virtual sensor; OBD-II validation.*

---

## 2 · Arabic version — `DOC/Abstract_AR.docx`, deleted 21 September — history

### متى يستحقّ الاستباق أن يُكتسب؟ معيار عديم الأبعاد، H/τ، مختبرًا على نظامين

<!-- RETIRED-OK: section 175.5, 22, 74, 9 -- the retired dataset, kept as history -->

يُعدّ التحكّم الاستباقي (preview control)، أي التحكّم الذي يتصرّف بناءً على معلومة عن اضطراب قادم قبل وصوله فعليًا، أسلوبًا راسخًا في الإدارة الحرارية للمركبات. لكن ما لم يُحسم بعد هو: متى تستحقّ هذه المعلومة الاستباقية أن تُكتسب أصلًا؟ فالمعلومة الاستباقية لها كلفة حقيقية — استشعار، وخرائط، واتصال، وحساب — والأدبيات تُبلّغ عن فائدتها حالةً بحالة، دون معيار قابل للانتقال بين الأنظمة.

يقترح هذا المشروع معيارًا واحدًا لذلك ويختبره، ويحكمه نسبة واحدة عديمة الأبعاد هي **H/τ** : أفق الاستباق المتاح مقسومًا على الثابت الزمني الحراري للمكوّن المراد حمايته. والفرضية أن قيمة الاستباق تنهار على منحنى واحد عند رسمها مقابل H/τ، أيًّا كان النظام الفيزيائي الذي أنتج النقطة. ولاختبار ذلك يُستخدم نظامان مختلفان جوهريًا: محرّك بنزين مزوّد بشاحن توربيني، وحزمة بطارية مركبة كهربائية. وإذا لم ينطبق المنحنيان أحدهما على الآخر، فالمعيار خاطئ أو ناقص، ويُبلَّغ عن ذلك بوصفه نتيجة لا بوصفه فشلًا.

ونموذج المحرّك هو نموذج دورة صفري الأبعاد أحادي المنطقة لمحرّك سعة ٣٫٠ لتر، ستّ أسطوانات على خطّ واحد، مزوّد بشاحن توربيني، مقترنًا بشبكة حرارية ثلاثية العقد ذات سعات حرارية مُجمَّعة تمثّل كتلة المحرّك والزيت وغلاف التوربين. وقد جرت معايرته مقابل ١٧٥٫٥ دقيقة من سجلات OBD-II مقروءة فقط، سُجِّلت من سيارة الفريق نفسها عبر تسع رحلات. وعلى ٢٢ نقطة تشغيل شبه مستقرة مُجمَّعة تمتدّ بين ٣٠ و٧٤ كيلوباسكال من ضغط المشعب، يتوافق الحمل المحسوب من النموذج مع الحمل الذي تُبلّغ عنه السيارة بفارق **١٫٤ ٪ ودون أيّ معامل مُعاير** . ويُصرَّح في الرسالة بنطاق هذا التوافق صراحةً: فهو اختبار اتّساق بين قناتين من قنوات وحدة التحكّم بالمحرّك، ولا يُثبت وحده نموذج التنفّس؛ كما أن التحقّق من الكفاءة الحجمية عند الأحمال الجزئية غير ممكن على هذه السيارة، لأن قناتَي الضغط المُسجَّلتين كلتيهما تقعان قبل صمّام الخانق.

بعد ذلك يُدرَّب مُشرِف قائم على التعلّم المعزّز على نموذج المحرّك، ويُقيَّم مقابل مرجعيّتين — وحدة تحكّم مُعايرة على نمط الإنتاج، وسياسة حماية تفاعليّة — ضمن بروتوكول تقييم ثابت. ويُعزَل إسهام الاستباق عبر تجربة حذف (ablation): إذ تُعاد تقييم السياسة المدرَّبة نفسها بعد تعطيل قناة الاستباق لديها، بحيث يصبح أيّ فارق أداء متبقٍّ عائدًا إلى المعلومة الاستباقية وحدها دون سواها.

وتتمثّل مخرجات المشروع في ثلاثة. أوّلها المعيار نفسه، مقدَّمًا في هيئة مخطّط تصميمي يستطيع المهندس، متى عرف الثابت الزمني للمكوّن المراد حمايته والأفق المتاح له فعليًا، أن يقرأ منه مباشرةً هل يستحقّ الاستباق كلفته قبل الشروع في بنائه. وثانيها المحاكاة المُعايَرة مع المُشرِف المدرَّب وجدول تجربة الحذف الذي يفصل إسهام الاستباق عن إسهام وحدة التحكّم. وثالثها تطبيق عامل في الزمن الحقيقي: يُشغّل الفيزياء المُعايَرة نفسها بالتوازي مع السيارة على حاسوب محمول، فيعمل مستشعرًا افتراضيًا للكميات التي لا تملك السيارة مؤشّرًا لها — حرارة غلاف التوربين، وحرارة الشحنة، وهامش الطَّرق، والضرر الحراري المتراكم — ويعرضها عبر لوحة معلومات كاملة، وواجهة سائق تُقرأ بنظرة واحدة وتُنذر قبل أن تبلغ الحرارة المُقدَّرة ركبة منحنى الضرر، ومراجعة بعد الرحلة لما وسَمه النموذج بأنه غير اعتيادي، مكتوبة لفنّي الصيانة لا للسائق.

ويُفصَل التحكّم عن المراقبة فصلًا مقصودًا، ويُصرَّح به بدل أن يُترك ضمنيًّا: فداخل المحاكاة المُعايَرة يملك المُشرِف سلطة كاملة على زاوية الإشعال والخليط وضغط الشحن والتبريد؛ أمّا الواجهة مع السيارة نفسها فللقراءة فقط، وبنيويًّا كذلك — يفتح التطبيق منفذ OBD-II للقراءة ولا يُصدر أيّ أمر كتابة، ولا يوجد مسار برمجي منه إلى ناقل السيارة، ولا تُكتب بيانات السيارة الخام على القرص إطلاقًا، بل تُكتب وحدها الأحداث التي يسِمُها النموذج. وهذا الحدّ ناتج عن أمرين: انعدام صلاحية الكتابة على وحدة التحكّم بالمحرّك، وغياب أيّ سبيل آمن لترك سياسة غير مكتملة التدريب تتحكّم بسيارة على طريق عامّ. ويُذكر ذلك بوصفه قرار نطاق لا إغفالًا؛ ونقل المُشرِف إلى عتاد حقيقي موضعه منصّة اختبار مُجهّزة، وهو مُدرَج ضمن الأعمال المستقبلية.

---

## 3 · Simplified version — `DOC/Abstract_Simplified.docx`, deleted 21 September — history

### 3a · English

<!-- RETIRED-OK: section 175.5, 22, 74, 9 -- the retired dataset, kept as history -->

**The one-line version:** we are working out when it is worth knowing what is coming.

Think about boiling a pot of water on the stove.

If someone warns you ten seconds before the pot boils over, that warning is useless — the pot takes eight minutes to get there, and you had eight minutes of chances to notice. The warning told you nothing you could not have seen.

Now think about a lit match. A ten-second warning is also useless there, but for the opposite reason: the match is done in two seconds. By the time your warning means anything, it is over.

The warning is only worth having when **how far ahead you can see** and **how fast the thing changes** are roughly the same size. That is the whole idea.

We give those two things names:

**H** = how far ahead you can see. Your forecast.

**τ** ("tau") = how long the thing takes to change. The pot's eight minutes.

The number that matters is **H divided by τ** . Not H on its own, not τ on its own — the ratio.

**The claim, and it is a real one:** this ratio is all you need to know. Two completely different systems with the same H/τ should get the same benefit from a forecast. So we test it on two things that have nothing in common — a petrol engine and an electric-car battery — and check whether they land on the same curve. If they do not, we say so. That is still a finding.

**Why it matters:** looking ahead is not free. It costs sensors, maps, an internet connection and computing power. Right now every engineering team works out whether it is worth it by building the whole thing and measuring. We are trying to give them one number they can check first.

**What we have done so far:** built the pot, and showed it boils like the real one. We drove our own car for 175.5 minutes across nine trips, recorded what it was doing, and the computer model agrees with the real car to within 1.4 %. Next we teach the software when to look ahead.

**One rule we never break:** we only ever read from the car. We never send it anything. It is a stethoscope, not a steering wheel.

**Why we never let it drive:** inside our simulation the software has full control — it sets the spark, the mixture and the cooling, and that is where we test whether looking ahead pays. On the real car it only watches, and tells the driver what it sees. Two reasons, and we say both: we have no permission to write to the car’s computer, and letting half-trained software command a real engine on a public road is not something we would do. The place for that is a test bench, not our own car.

**العربية**

### 3b · Arabic — العربية

<!-- RETIRED-OK: section 175.5, 22, 74, 9 -- the retired dataset, kept as history -->

**السطر الواحد:** نحن نحدّد متى يستحقّ أن تعرف ما هو قادم.

تخيّل قدرًا من الماء على النار.

لو حذّرك أحدهم قبل عشر ثوانٍ من فوران القدر، فالتحذير بلا قيمة — القدر يحتاج ثماني دقائق ليصل، وكانت أمامك ثماني دقائق لتلاحظ. التحذير لم يخبرك بشيء لم تكن تراه أصلًا.

والآن تخيّل عود ثقاب مشتعلًا. تحذير من عشر ثوانٍ بلا قيمة أيضًا، لكن للسبب المعاكس: العود ينتهي خلال ثانيتين. وحين يصبح لتحذيرك معنى، يكون كلّ شيء قد انتهى.

التحذير يستحقّ فقط حين يكون **مدى ما تراه أمامك** و**سرعة تغيّر الشيء** متقاربَين في الحجم. هذه هي الفكرة كاملة.

ونعطي هذين الأمرين اسمين:

**H** = إلى أيّ مدى ترى أمامك. أي توقّعك.

**τ** («تاو») = كم يستغرق الشيء ليتغيّر. أي ثماني دقائق القدر.

والرقم المهمّ هو **H مقسومًا على** **τ** . لا H وحده، ولا τ وحده — بل النسبة.

**ما ندّعيه، وهو ادّعاء حقيقي:** هذه النسبة هي كلّ ما تحتاج معرفته. نظامان مختلفان تمامًا لهما النسبة نفسها يجب أن يستفيدا الفائدة نفسها من التوقّع. ولذلك نختبرها على شيئين لا يجمعهما شيء — محرّك بنزين وبطارية سيارة كهربائية — ونرى هل يقعان على المنحنى نفسه. وإن لم يقعا، قلنا ذلك. وهذه أيضًا نتيجة.

**لماذا يهمّ هذا:** النظر إلى الأمام ليس مجانيًا. فهو يكلّف مستشعرات وخرائط واتصالًا بالإنترنت وقدرة حسابية. واليوم، كلّ فريق هندسي يعرف إن كان الأمر يستحقّ بأن يبني المنظومة كاملة ثم يقيس. ونحن نحاول أن نمنحهم رقمًا واحدًا يتحقّقون منه قبل ذلك.

**ما أنجزناه حتى الآن:** بنينا «القدر»، وأظهرنا أنه يغلي مثل الحقيقي. قدنا سيارتنا ١٧٥٫٥ دقيقة عبر تسع رحلات، وسجّلنا ما كانت تفعله، والنموذج الحاسوبي يتّفق مع السيارة الحقيقية بفارق لا يتجاوز ١٫٤ ٪. والخطوة التالية أن نعلّم البرنامج متى ينظر إلى الأمام.

**قاعدة لا نكسرها أبدًا:** نحن نقرأ من السيارة فقط، ولا نرسل إليها شيئًا أبدًا. إنها سمّاعة طبيب، لا مقود.

**لماذا لا ندعه يقود أبدًا:** داخل محاكاتنا يملك البرنامج تحكّمًا كاملًا — يضبط الشرارة والخليط والتبريد، وهناك نختبر هل النظر إلى الأمام يستحقّ كلفته. أمّا على السيارة الحقيقية فهو يراقب فقط ويُخبر السائق بما يرى. والسببان مُعلنان: لا نملك صلاحية الكتابة على حاسوب السيارة، وترك برنامج نصف مدرّب يقود محرّكًا حقيقيًا على طريق عامّ ليس شيئًا نفعله. مكان ذلك منصّة اختبار، لا سيارتنا.

---

## 4 · Short cut, if a word limit applies

**NOT in the current `.docx`.** It was in the 16 September version of
`Abstract_EN.docx` and was dropped when the document was rebuilt on its cover-page
template. Kept here so the work is not lost; paste it back if a limit is set.
**Brought up to date on 22 September** so that pasting it back cannot
reintroduce the retired dataset or the voided ablation design: the dataset
figures are the shipped ones, and the ablation sentence says what `evaluate.py`
does, on the per-episode randomised road that Phase D2 uses
(`results/PREREGISTRATION_D2.md`). The 16 September wording is in git history.
It still states no result. **Before pasting it back, note that the one ablation
run so far does not meet that description:** Phase D's road was fixed, so its
blinded arm was not blind (`results/PREREGISTRATION.md` limit 7), and its agents
were trained only to the C1 budget — 50 000 steps, 11 training episodes. With
agents trained to the C1 budget, preview did not separate from seed noise; that
is not the same claim as *preview does not help*. `CLAUDE.md` carries both.

Preview-based control acts on a disturbance before it arrives, and is well established in automotive thermal management. What is not established is when the preview is worth acquiring at all, given that sensing, mapping and connectivity all cost something. This project proposes a criterion governed by one dimensionless ratio, **H/τ** : the available preview horizon divided by the thermal time constant of the protected component. The hypothesis is that preview value collapses onto a single curve against H/τ regardless of the plant, and it is to be tested on two dissimilar plants — a turbocharged spark-ignition engine and an electric-vehicle battery pack, the second not yet built. The engine plant is a zero-dimensional cycle model coupled to a three-node thermal network, calibrated against read-only OBD-II logs from the team's own vehicle — 295.0 minutes over ten drives, seven of them carrying usable samples; across 26 pooled quasi-steady operating points at 30–75 kPa it agrees with the vehicle to 1.4 % with no fitted parameters. A reinforcement-learning supervisor is evaluated against a production-style controller and a reactive policy, and the contribution of preview is to be isolated by training a second agent identically with its preview channel zeroed, on a road whose climb is randomised per episode so that the blinded agent cannot infer when it comes, and comparing the two under the same fixed protocol. The project delivers the criterion as a design chart, the validated simulation and ablation table behind it, and a real-time application that runs the same physics alongside the car as a virtual sensor for turbine-housing temperature, knock margin and accumulated thermal damage, warning the driver and logging what it marks for a mechanic. The vehicle interface is strictly read-only throughout: the application issues no write commands and has no code path to the vehicle bus.
