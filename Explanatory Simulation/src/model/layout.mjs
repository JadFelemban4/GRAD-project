/** Teaching assembly in the original Supra's +X-forward coordinates. */
export const routes = {
  air: [[2.65,.83,.62],[2.42,.9,.68],[2.08,.95,.79]],
  charge: [[2.08,.96,.82],[2.5,.88,.82],[2.65,.64,.1],[2.66,.67,-.56],[2.15,.87,-.6],[1.5,1.08,-.5],[.94,1.05,-.31]],
  exhaust: [[.97,.98,.31],[1.43,.87,.45],[1.82,.85,.44],[2.04,.92,.46]],
  tail: [[2.05,.85,.47],[1.56,.4,.45],[.3,.38,.43],[-1.6,.38,.44],[-2.62,.42,.54],[-3.12,.56,.71]],
  coolant: [[1.2,.76,-.28],[2.2,.7,-.56],[2.76,.73,-.52],[2.76,1.01,.42],[2.14,1.01,.3],[1.2,.93,.27],[1.2,.76,-.28]],
  oil: [[1.5,.48,0],[1.02,.64,-.38],[1.04,.93,-.32],[1.97,.94,-.3],[1.98,.53,-.18],[1.5,.48,0]],
};
export function cylinderPose(phase) {
  const angle=phase*Math.PI*4;
  const radius=.095, rodLength=.27;
  const pinY=.59+radius*Math.cos(angle), pinZ=radius*Math.sin(angle);
  const jointY=pinY+Math.sqrt(rodLength*rodLength-pinZ*pinZ);
  return {pinY,pinZ,jointY,pistonY:jointY+.035};
}
