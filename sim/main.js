// main.js — STRILAS 3D hårdvarusimulator
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import * as HW from './hardware.js';

// ---------------- grund ----------------
const app = document.getElementById('app');
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x0e1116, 40, 140);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 500);
camera.position.set(-9, 6, 11);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
app.appendChild(renderer.domElement);
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(14, 1, 0); orbit.update();
const fps = new PointerLockControls(camera, renderer.domElement);

// ---------------- ljus & miljö ----------------
const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x202830, 0.8);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffffff, 1.4);
sun.position.set(20, 40, 15); sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024); sun.shadow.camera.far = 120;
sun.shadow.camera.left = -40; sun.shadow.camera.right = 40;
sun.shadow.camera.top = 40; sun.shadow.camera.bottom = -40;
scene.add(sun);

// mark + rutnät
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(300, 120),
  new THREE.MeshStandardMaterial({ color: 0x1a2230, roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.position.x = 60; ground.receiveShadow = true;
scene.add(ground);
const grid = new THREE.GridHelper(120, 60, 0x2a3441, 0x222a36);
grid.position.set(60, 0.01, 0); scene.add(grid);
// avståndsmarkörer var 10 m
for (let d = 10; d <= 80; d += 10) {
  const t = makeLabel(d + ' m');
  t.position.set(d, 0.05, -7); scene.add(t);
}

// ---------------- skytt + vapen ----------------
const shooter = new THREE.Group(); shooter.position.set(0, 0, 0); scene.add(shooter);
const sbody = new THREE.Mesh(new THREE.CapsuleGeometry(0.25, 1.1, 4, 8),
  new THREE.MeshStandardMaterial({ color: 0x39d98a }));
sbody.position.y = 1.0; sbody.castShadow = true; shooter.add(sbody);
const rifle = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.08, 0.08),
  new THREE.MeshStandardMaterial({ color: 0x222831 }));
rifle.position.set(0.45, 1.45, 0.12); shooter.add(rifle);
const MUZZLE = new THREE.Vector3(0.8, 1.45, 0.12);
shooter.add(makeLabel('SKYTT', 0x39d98a).translateY(2.1));

// ---------------- mål (humanoid med zoner) ----------------
let target, zoneMesh = {}, zoneBase = {};
function buildTarget() {
  const g = new THREE.Group();
  zoneMesh = {}; zoneBase = {};
  const defs = {
    Ben: [0.25, 0.95, 0.33, 0.475], Mage: [0.25, 0.30, 0.40, 1.10],
    Bröst: [0.28, 0.35, 0.48, 1.425],
  };
  for (const [name, [dx, dy, dz, y]] of Object.entries(defs)) {
    const z = HW.ZONES.find(Z => Z.name === name);
    const m = new THREE.Mesh(new THREE.BoxGeometry(dx, dy, dz),
      new THREE.MeshStandardMaterial({ color: z.color, roughness: .7 }));
    m.position.y = y; m.castShadow = true; g.add(m);
    zoneMesh[name] = m; zoneBase[name] = z.color;
  }
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12),
    new THREE.MeshStandardMaterial({ color: 0xff5c5c, roughness: .7 }));
  head.position.y = 1.70; head.castShadow = true; g.add(head);
  zoneMesh['Huvud'] = head; zoneBase['Huvud'] = 0xff5c5c;
  scene.add(g); return g;
}
target = buildTarget();

// ---------------- visuella effekter ----------------
const beamMat = new THREE.LineBasicMaterial({ color: 0x39d98a, transparent: true });
const beam = new THREE.Line(new THREE.BufferGeometry().setFromPoints(
  [new THREE.Vector3(), new THREE.Vector3()]), beamMat);
scene.add(beam); let beamTtl = 0;
const round = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 8),
  new THREE.MeshBasicMaterial({ color: 0xffd35c }));
round.visible = false; scene.add(round);
let roundAnim = null;
// IR-räckviddsring
const rangeRing = new THREE.Mesh(new THREE.RingGeometry(0, 1, 64),
  new THREE.MeshBasicMaterial({ color: 0x39d98a, transparent: true, opacity: 0.06, side: THREE.DoubleSide }));
rangeRing.rotation.x = -Math.PI / 2; rangeRing.position.y = 0.02; scene.add(rangeRing);

// ---------------- state ----------------
const S = {
  fsm: 'READY', ammo: 30, health: 100, hits: [], dead: false,
  climb: 0, imu: 0, fireAcc: 0, tTarget: 0, sinceShot: 999,
};
let profile = HW.PROFILES['M4 / 5.56'];

// ---------------- UI ----------------
const $ = id => document.getElementById(id);
// fyll selects
const selP = $('profile');
for (const k of Object.keys(HW.PROFILES)) selP.add(new Option(k, k));
const selE = $('env');
for (const k of Object.keys(HW.ENVIRONMENTS)) selE.add(new Option(k, k));
selE.value = 'Starkt solljus';
const C = {}; // control-cache
function readUI() {
  C.cur = +$('cur').value; C.beam = +$('beam').value; C.nled = +$('nled').value;
  C.filter = $('filter').checked; C.env = HW.ENVIRONMENTS[selE.value];
  C.fas2 = $('fas2').checked; C.sigma = +$('sigma').value; C.tspd = +$('tspd').value;
  C.autofire = $('autofire').checked;
  $('v-cur').textContent = C.cur.toFixed(1) + ' A'; $('v-beam').textContent = C.beam.toFixed(1) + '°';
  $('v-nled').textContent = C.nled; $('v-sigma').textContent = C.sigma.toFixed(1) + '°';
  $('v-tspd').textContent = C.tspd.toFixed(1) + ' m/s';
}
['cur', 'beam', 'nled', 'sigma', 'tspd'].forEach(id => $(id).addEventListener('input', readUI));
['filter', 'fas2', 'autofire'].forEach(id => $(id).addEventListener('change', readUI));
selE.addEventListener('change', readUI);
selP.addEventListener('change', () => {
  profile = HW.PROFILES[selP.value];
  $('beam').value = profile.beamHalf; S.ammo = profile.mag; S.fsm = 'READY'; readUI();
});
readUI();

$('btn-mag').onclick = () => { if (S.fsm === 'NO_MAG') S.fsm = 'MAG_IN'; };
$('btn-rack').onclick = () => { if ((S.fsm === 'MAG_IN' || S.fsm === 'EMPTY') && S.ammo > 0) S.fsm = 'READY'; };
$('btn-reload').onclick = () => { S.ammo = profile.mag; S.fsm = 'READY'; };
$('btn-fire').onclick = () => fire();
$('btn-reset').onclick = () => { S.health = 100; S.hits = []; S.dead = false; $('killbanner').style.display = 'none'; };
$('btn-fps').onclick = () => fps.lock();

// FPS-läge
let fpsActive = false;
fps.addEventListener('lock', () => {
  fpsActive = true; orbit.enabled = false; $('reticle').style.display = 'block';
  camera.position.copy(MUZZLE).add(new THREE.Vector3(-0.2, 0.1, 0));
});
fps.addEventListener('unlock', () => {
  fpsActive = false; orbit.enabled = true; $('reticle').style.display = 'none';
});
renderer.domElement.addEventListener('mousedown', e => { if (fpsActive && e.button === 0) fire(); });

// ---------------- hjälpfunktioner ----------------
function gaussian() { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
function makeLabel(text, color = 0x8b949e) {
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
  const cx = cv.getContext('2d'); cx.fillStyle = '#' + color.toString(16).padStart(6, '0');
  cx.font = 'bold 34px Consolas'; cx.textAlign = 'center'; cx.fillText(text, 128, 44);
  const tex = new THREE.CanvasTexture(cv);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  sp.scale.set(2.5, 0.62, 1); return sp;
}
function targetPos(t) {
  const x = 26 - 6 * Math.sin(0.2 * t);
  const w = C.tspd / 10;                 // amplitud 10 → maxfart = C.tspd
  const z = 10 * Math.sin(w * t);
  return new THREE.Vector3(x, 0, z);
}
function targetVelZ(t) {
  const w = C.tspd / 10; return 10 * w * Math.cos(w * t); // m/s lateralt
}

// ---------------- AVFYRNING ----------------
function fire() {
  if (S.fsm !== 'READY' || S.ammo <= 0 || S.dead) return;
  S.ammo--; S.sinceShot = 0;
  S.climb += profile.recoilDeg * 0.5;          // rekyl: klättring ackumuleras
  if (S.ammo === 0) S.fsm = 'EMPTY';

  const tp = targetPos(S.tTarget);
  const R = Math.hypot(tp.x - MUZZLE.x, tp.z - MUZZLE.z);
  const tofS = HW.tof(R, profile.v0);
  const irMax = HW.maxRange(C.cur, C.beam, C.env, C.nled, C.filter);
  const inRange = R <= irMax;

  // siktriktning
  let dir, muzzle = MUZZLE.clone(), aimEnd;
  if (fpsActive) {
    dir = new THREE.Vector3(); camera.getWorldDirection(dir); muzzle = camera.position.clone();
  } else {
    const lead = C.fas2 ? targetVelZ(S.tTarget) * tofS : 0;
    const aim = new THREE.Vector3(tp.x, 1.40, tp.z + lead);
    // siktfel (σ) + rekyl-klättring (pekar uppåt → träffar högre)
    aim.z += R * Math.tan((gaussian() * C.sigma) * Math.PI / 180);
    aim.y += R * Math.tan((gaussian() * C.sigma) * Math.PI / 180);
    aim.y += R * Math.tan(S.climb * Math.PI / 180);
    dir = aim.clone().sub(muzzle).normalize();
  }
  // skär målplanet X = tp.x
  const s = (tp.x - muzzle.x) / (dir.x || 1e-6);
  aimEnd = muzzle.clone().add(dir.clone().multiplyScalar(s));

  // var är målet när kulan anländer (Fas 2) resp. nu (Fas 1)
  const arrZ = C.fas2 ? targetPos(S.tTarget + tofS).z : tp.z;
  const cy = aimEnd.z - arrZ;            // lateralt avstånd från kroppscentrum
  const cz = aimEnd.y;                   // höjd
  const r = HW.beamRadius(R, C.beam);
  const overlap = Math.abs(cy) <= HW.BODY_HW + r && cz >= -r && cz <= HW.BODY_H + r;
  const hit = overlap && inRange;

  // zon
  let zone = null;
  if (hit) {
    zone = HW.zoneAt(cz, cy);
    if (C.fas2) { if (!zone) zone = HW.ZONES.reduce((a, Z) =>
        Math.min(Math.abs(cz - Z.zl), Math.abs(cz - Z.zh)) <
        Math.min(Math.abs(cz - a.zl), Math.abs(cz - a.zh)) ? Z : a); }
    else { // Fas 1: headshot bara om fläcken får plats på huvudet
      if (zone && zone.name === 'Huvud' && r >= 0.13) zone = HW.ZONES[1]; // → Bröst
      if (!zone) zone = HW.ZONES[1];
    }
  }

  // verkan
  const beamColor = !inRange ? 0xff5c5c : hit ? 0x39d98a : 0xffb000;
  showBeam(muzzle, aimEnd, beamColor);
  if (C.fas2 && inRange) flyRound(muzzle, aimEnd, hit, zone);
  else if (hit) applyHit(zone);

  // MilesTag-paket + telemetri
  const pkt = HW.milestagShot(7, 1, profile.dmg);
  $('packet').textContent = pkt.bits + '  (' + pkt.airtimeMs.toFixed(0) + ' ms)';
  $('t-ie').textContent = HW.emitterIe(C.cur, C.beam, C.nled).toFixed(0) + ' W/sr';
  updateHUD(R, tofS, irMax);
}

function applyHit(zone) {
  if (!zone || S.dead) return;
  S.health = Math.max(0, S.health - 18 * zone.mult);
  S.hits.push({ t: S.tTarget, zone: zone.name });
  flashZone(zone.name);
  if (S.health <= 0 && !S.dead) { S.dead = true; $('killbanner').style.display = 'block'; }
  updateHUD();
}
function flashZone(name) {
  const m = zoneMesh[name]; if (!m) return;
  m.material.emissive = new THREE.Color(0xffffff); m.material.emissiveIntensity = 1.0;
  setTimeout(() => { m.material.emissiveIntensity = 0; }, 220);
}
function showBeam(a, b, color) {
  beam.geometry.setFromPoints([a, b]); beam.material.color.setHex(color);
  beam.material.opacity = 1; beamTtl = 0.12;
}
function flyRound(a, b, hit, zone) {
  round.visible = true; roundAnim = { a: a.clone(), b: b.clone(), t: 0, dur: 0.18, hit, zone };
}

// ---------------- HUD ----------------
function updateHUD(R, tofS, irMax) {
  $('hud-ammo').textContent = S.ammo;
  const st = $('hud-state'); st.textContent = S.fsm; st.className = 'state s-' + S.fsm;
  if (R !== undefined) {
    $('hud-range').textContent = R.toFixed(0) + ' m';
    $('hud-tof').textContent = (tofS * 1000).toFixed(0) + ' ms';
    $('hud-irrange').textContent = irMax.toFixed(0) + ' m';
  }
  $('hud-hits').textContent = S.hits.length;
  const hp = S.health / 100;
  const bar = $('hp-bar'); bar.style.width = (hp * 100) + '%';
  bar.style.background = hp > .5 ? '#39d98a' : hp > .2 ? '#ffb000' : '#ff5c5c';
  $('hitlog').innerHTML = S.hits.slice(-5).reverse().map(h =>
    `<div style="color:${h.zone === 'Huvud' ? '#ff5c5c' : '#e6edf3'}">` +
    `${h.t.toFixed(1)}s · ${h.zone}${h.zone === 'Huvud' ? ' ★HEADSHOT' : ''}</div>`).join('');
}

// ---------------- loop ----------------
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  S.tTarget += dt; S.sinceShot += dt;

  // mål
  const tp = targetPos(S.tTarget);
  target.position.set(tp.x, 0, tp.z);
  target.lookAt(0, 1, 0);
  if (S.dead) { target.children.forEach(c => c.material.color.setHex(0x6e7681)); }
  else { for (const n in zoneMesh) zoneMesh[n].material.color.setHex(zoneBase[n]); }

  // rekyl-återhämtning
  S.climb = Math.max(0, S.climb - dt * 6);          // återhämtar ~6°/s
  S.imu = HW.imuRate(Math.min(S.sinceShot, 0.08));

  // auto-eld
  if (C.autofire && !S.dead && S.fsm === 'READY' && S.ammo > 0) {
    S.fireAcc += dt;
    if (S.fireAcc >= 60 / profile.rofRpm) { S.fireAcc = 0; fire(); }
  }
  if (C.autofire && S.fsm === 'EMPTY' && S.sinceShot > 1.2) { S.ammo = profile.mag; S.fsm = 'READY'; }

  // beam fade
  if (beamTtl > 0) { beamTtl -= dt; beam.material.opacity = Math.max(0, beamTtl / 0.12); }
  else beam.material.opacity = 0;

  // round flight
  if (roundAnim) {
    roundAnim.t += dt;
    const u = Math.min(roundAnim.t / roundAnim.dur, 1);
    round.position.lerpVectors(roundAnim.a, roundAnim.b, u);
    if (u >= 1) { round.visible = false; if (roundAnim.hit) applyHit(roundAnim.zone); roundAnim = null; }
  }

  // IR-räckviddsring (uppdateras med miljö/ström/stråle)
  const irMax = HW.maxRange(C.cur, C.beam, C.env, C.nled, C.filter);
  rangeRing.scale.set(irMax, irMax, 1);
  rangeRing.material.color.setHex(targetPos(S.tTarget).x <= irMax ? 0x39d98a : 0xff5c5c);

  // telemetri
  $('t-imu').textContent = (S.imu).toFixed(0) + '°/s';
  $('t-climb').textContent = S.climb.toFixed(1) + '°';

  // recoil i FPS: luta kameran
  if (fpsActive) camera.rotation.x += 0; // (klättring syns i auto-aim; FPS visar beam)

  if (S.health !== undefined) {
    $('hud-ammo').textContent = S.ammo;
    const st = $('hud-state'); st.textContent = S.fsm; st.className = 'state s-' + S.fsm;
  }
  renderer.render(scene, camera);
}
updateHUD(targetPos(0).x, HW.tof(26, profile.v0), HW.maxRange(3, 1, 30));
animate();
