/** Named presentation phases match the illustrative valve windows in EngineAssembly. */
export const STROKE_STATIONS = Object.freeze([
  Object.freeze({ id: 'intake', name: 'سحب', angle: 90, intakeOpen: true, exhaustOpen: false, pistonDirection: 'down', hint: 'تدخل الشحنة عبر صمام السحب وينزل المكبس.' }),
  Object.freeze({ id: 'compression', name: 'ضغط', angle: 270, intakeOpen: false, exhaustOpen: false, pistonDirection: 'up', hint: 'يصعد المكبس ويضغط الشحنة المحبوسة.' }),
  Object.freeze({ id: 'power', name: 'قدرة', angle: 450, intakeOpen: false, exhaustOpen: false, pistonDirection: 'down', hint: 'الشرارة تسبق الاحتراق؛ الغازات تدفع المكبس إلى الأسفل.' }),
  Object.freeze({ id: 'exhaust', name: 'عادم', angle: 630, intakeOpen: false, exhaustOpen: true, pistonDirection: 'up', hint: 'يصعد المكبس وتخرج الغازات عبر صمام العادم.' }),
]);

export function strokeAtDegrees(degrees) {
  const wrapped = ((degrees % 720) + 720) % 720;
  return STROKE_STATIONS[Math.floor(wrapped / 180)];
}

export function globalCycleForCylinder(degrees, index) {
  return (((degrees / 720 - index / 6) % 1) + 1) % 1;
}

export function cylinderCycleDegrees(globalCycle, index) {
  return (((globalCycle + index / 6) % 1) + 1) % 1 * 720;
}
/** Illustrative ignition display windows, in crank degrees; not factory duration. */
export const SPARK_PULSE_DEGREES = 8;
export const COMBUSTION_DEGREES = 115.2;
const normalizeDegrees = degrees => ((degrees % 720) + 720) % 720;
export function ignitionCommandDegrees(spark) {
  return typeof spark === 'number' && Number.isFinite(spark) ? normalizeDegrees(360 - spark) : null;
}
export function sparkPulseAtDegrees(degrees, spark) {
  const command = ignitionCommandDegrees(spark);
  if (command === null || !Number.isFinite(degrees)) return 0;
  const elapsed = normalizeDegrees(degrees - command);
  // Floating-point round trip of a selected-cylinder clock can land just before zero.
  return elapsed > 720 - 1e-8 ? 1 : elapsed < SPARK_PULSE_DEGREES ? 1 - elapsed / SPARK_PULSE_DEGREES : 0;
}
export function combustionAtDegrees(degrees, spark) {
  const command = ignitionCommandDegrees(spark);
  if (command === null || !Number.isFinite(degrees)) return 0;
  const elapsed = normalizeDegrees(degrees - command);
  return elapsed < COMBUSTION_DEGREES ? Math.sin(elapsed / COMBUSTION_DEGREES * Math.PI) : 0;
}
