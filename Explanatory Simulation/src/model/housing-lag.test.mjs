import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { inputsOf, settleOf, stepHousing, tauOf } from './housing-lag.mjs';

const params = JSON.parse(readFileSync(new URL('../../figures/housing-lag/params.json', import.meta.url), 'utf8'));
const { turbine, reference } = params;

function run(seconds, litFor) {
  const lit = inputsOf(params, true), off = inputsOf(params, false);
  let t = lit.tAmbK;
  const out = [t];
  for (let second = 0; second < seconds; second++) {
    const input = second < litFor ? lit : off;
    for (let i = 0; i < Math.round(1 / reference.dt); i++) t = stepHousing(turbine, t, reference.dt, input.mdotExhGps, input.egtK, input.tAmbK);
    out.push(t);
  }
  return out;
}

test('the figure reproduces ThermalNetwork, lit then off, every second', () => {
  const ours = run(reference.heat_s + reference.cool_s, reference.heat_s);
  assert.equal(ours.length, reference.t_turb_k.length);
  ours.forEach((value, second) => assert.ok(Math.abs(value - reference.t_turb_k[second]) < 1e-9, `second ${second}: ${value} vs ${reference.t_turb_k[second]}`));
});

test('one long step equals the same time in 0.1 s steps, as thermal.py sub-steps it', () => {
  const lit = inputsOf(params, true);
  let fine = lit.tAmbK;
  for (let i = 0; i < 10; i++) fine = stepHousing(turbine, fine, 0.1, lit.mdotExhGps, lit.egtK, lit.tAmbK);
  const coarse = stepHousing(turbine, lit.tAmbK, 1.0, lit.mdotExhGps, lit.egtK, lit.tAmbK);
  assert.ok(Math.abs(fine - coarse) < 1e-9);
});

test('tau is the time to cover 63 % of the way to where the housing settles', () => {
  const lit = inputsOf(params, true), off = inputsOf(params, false);
  for (const [input, start] of [[lit, lit.tAmbK], [off, settleOf(turbine, lit.mdotExhGps, lit.egtK, lit.tAmbK)]]) {
    const tau = tauOf(turbine, input.mdotExhGps);
    const settle = settleOf(turbine, input.mdotExhGps, input.egtK, input.tAmbK);
    let t = start, time = 0;
    while (time < tau - 1e-9) { const h = Math.min(0.1, tau - time); t = stepHousing(turbine, t, h, input.mdotExhGps, input.egtK, input.tAmbK); time += h; }
    const covered = (t - start) / (settle - start);
    assert.ok(Math.abs(covered - (1 - Math.exp(-1))) < 0.002, `covered ${covered} in tau ${tau}`);
  }
});

test('off is slower than lit: with no flow only the ambient side cools the housing', () => {
  assert.ok(tauOf(turbine, 0) > 5 * tauOf(turbine, params.engine.mdot_exh_gps));
});
