// The words of the housing-lag figure, Arabic first. Every number arrives from
// build.mjs, which takes it from params.json and the turbine-node model; none is
// typed here. Units stay left-to-right inside <bdi dir="ltr">, as in the lab.

const v = (text) => `<bdi dir="ltr">${text}</bdi>`;

export function copyFor(n) {
  return {
    ar: {
      fig: "شكل 1",
      title: "تأخّر هيكل التوربين",
      hint: "المسافة: تشغيل الموقد وإطفاؤه · R: من البداية",
      hintTouch: "انقر: تشغيل الموقد وإطفاؤه",
      keys: ["معدن الهيكل: حرارته في النموذج", "الغاز عند مدخل الهيكل", "نقطة 63 %: نهاية τ"],
      phase: { cold: "بارد", heating: "تسخين", cooling: "تبريد" },
      gas: "الغاز",
      housing: "الهيكل",
      seconds: "s",
      label:
        "منصة اختبار بالغاز الساخن: موقد يدفع الغاز في مجرى إلى هيكل توربين على قاعدة، ومسجّل بقلمين يرسم على ورقة متحركة حرارة الغاز وحرارة معدن الهيكل.",
      stage: "تشغيل الموقد وإطفاؤه بمفتاح المسافة أو بالنقر، والحرف R للبدء من جديد",
      caption:
        `منصة اختبار بالغاز الساخن. يقوم الموقد مقام المحرك: عند تشغيله يدفع غازًا حرارته ${v(n.gas)} وتدفقه ${v(n.flow)}، ` +
        `وهذا ما يتوقعه نموذج المحرك في المشروع عند ${v(n.rpm)} و${v(n.map)} وحرارة جو ${v(n.amb)}. ` +
        `عند إطفائه يتوقف التدفق، كما في تجربة الحرارة في المختبر. حرارة الهيكل تحسبها عقدة التوربين في ${v("thermal.py")} بالخطوة نفسها (${v(n.dt)}). ` +
        `أثناء التسخين يقطع الهيكل 63 % من الطريق إلى حرارة استقراره (${v(n.settle)}) خلال ${v("τ = " + n.tauOn)}، وبلا تدفق يبرد بـ ${v("τ = " + n.tauOff)}. ` +
        `يستقر الهيكل تحت حرارة الغاز لأنه يفقد حرارة إلى الهواء. يدور الدولاب ليُظهر أن الغاز يتدفق فقط؛ سرعته غير محسوبة. ` +
        `الثابتان مبنيّان على سعة حرارية مفترضة (${v("c_turb = " + n.c)}): لا يوجد في السيارة حساس يقيس حرارة الهيكل. الزمن هنا أسرع من الواقع ${v(n.speed)} مرات.`,
    },
    en: {
      fig: "Fig 1",
      title: "Housing lag",
      hint: "Space: burner on / off · R: restart",
      hintTouch: "Tap: burner on / off",
      keys: ["Housing metal: its modelled temperature", "Gas at the housing inlet", "63 % point: the end of τ"],
      phase: { cold: "cold", heating: "heating", cooling: "cooling" },
      gas: "gas",
      housing: "housing",
      seconds: "s",
      label:
        "A hot-gas test stand: a burner drives gas through a duct into a turbine housing on a pedestal, and a two-pen recorder draws the gas temperature and the housing metal's temperature on moving paper.",
      stage: "Burner on and off with Space or a click; R starts again",
      caption:
        `A hot-gas test stand. The burner stands in for the engine: lit, it delivers gas at ${v(n.gas)} and ${v(n.flow)}, ` +
        `what the project's engine model predicts at ${v(n.rpm)}, ${v(n.map)} and ${v(n.amb)} ambient. ` +
        `Off, the flow stops, as in the lab's thermal experiment. The housing follows the project's turbine node (${v("thermal.py")}) in the same ${v(n.dt)} steps. ` +
        `Heating, it covers 63 % of the way to where it settles (${v(n.settle)}) in ${v("τ = " + n.tauOn)}; with no flow it cools with ${v("τ = " + n.tauOff)}. ` +
        `It settles below the gas because it loses heat to the air. The wheel turns only to show that gas flows; its speed is not computed. ` +
        `Both time constants rest on an assumed heat capacity (${v("c_turb = " + n.c)}): no sensor on the car measures the housing. Time runs ${v(n.speed + "×")} faster than real.`,
    },
  };
}
