/** Visual rate is deliberately 18 times slower than physical crank speed. */
export function advanceVisualCycle(phase, dt, rpm, rate, playing) {
  if(!playing||![phase,dt,rpm,rate].every(Number.isFinite))return phase;
  return ((phase+Math.max(0,Math.min(.1,dt))*Math.max(0,rpm)/120/18*Math.max(0,rate))%1+1)%1;
}
export function manualCycle(degrees) { return Number.isFinite(degrees)?((degrees%720)+720)%720/720:0; }
