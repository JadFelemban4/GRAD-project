// Pin and serve these dependencies locally; the lab never needs a CDN at runtime.
import { mkdir, copyFile } from 'node:fs/promises';
const here = new URL('.', import.meta.url);
const dest = new URL('static/vendor/three/', here);
await mkdir(new URL('addons/controls/', dest), { recursive: true });
for (const name of ['three.module.js', 'three.core.js']) {
  await copyFile(new URL(`node_modules/three/build/${name}`, here), new URL(name, dest));
}
await copyFile(new URL('node_modules/three/examples/jsm/controls/OrbitControls.js', here), new URL('addons/controls/OrbitControls.js', dest));
await copyFile(new URL('node_modules/three/LICENSE', here), new URL('LICENSE.txt', dest));
console.log('Three.js 0.180.0 copied with license for local, offline rendering.');
