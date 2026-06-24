// main.js — STRILAS 3D-simulator (NIVÅ 3: geometrisk ballistik-adjudikation)
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import * as HW from './hardware.js';

// ---------------- grund ----------------
const app = document.getElementById('app');
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x0e1116, 50, 160);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 500);
camera.position.set(-10, 7, 13);
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
orbit.target.set(16, 1, 0); orbit.update();
const fps = new PointerLockControls(camera, renderer.domElement);

// ---------------- ljus & mark ----------------
scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x202830, 0.85));
const sun = new THREE.DirectionalLight(0xffffff, 1.3);
sun.position.set(20, 40, 15); sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024); sun.shadow.camera.far = 120;
Object.assign(sun.shadow.camera, { left: -50, right: 50, top: 50, bottom: -50 });
scene.add(sun);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 160),
  new THREE.MeshStandardMaterial({ color: 0x1a2230, roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.position.x = 70; ground.receiveShadow = true; scene.add(ground);
const grid = new THREE.GridHelper(160, 80, 0x2a3441, 0x222a36);
grid.position.set(70, 0.01, 0); scene.add(grid);

function makeLabel(text, color = 0x8b949e) {
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
  const cx = cv.getContext('2d'); cx.fillStyle = '#' + color.toString(16).padStart(6, '0');
  cx.font = 'bold 34px Consolas'; cx.textAlign = 'center'; cx.fillText(text, 128, 44);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), transparent: true }));
  sp.scale.set(2.6, 0.65, 1); return sp;
}
for (let d = 10; d <= 90; d += 10) { const t = makeLabel(d + 'm'); t.position.set(d, 0.06, -8); scene.add(t); }

// ---------------- skytt ----------------
const shooter = new THREE.Group(); scene.add(shooter);
const sbody = new THREE.Mesh(new THREE.CapsuleGeometry(0.25, 1.1, 4, 8),
  new THREE.MeshStandardMaterial({ color: 0x39d98a }));
sbody.position.y = 1.0; sbody.castShadow = true; shooter.add(sbody);
const rifle = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.08, 0.08),
  new THREE.MeshStandardMaterial({ color: 0x222831 }));
rifle.position.set(0.45, 1.45, 0.12); shooter.add(rifle);
shooter.add(makeLabel('SKYTT', 0x39d98a).translateY(2.15));
const MUZZLE = new THREE.Vector3(0.8, 1.45, 0.12);

// ---------------- mål (kapsel-kropp) ----------------
const CAPS = [
  { name: 'Huvud', kind: 'sph', r: 0.10, y: 1.70, color: 0xff5c5c },
  { name: 'Bröst', kind: 'cap', r: 0.17, len: 0.30, y: 1.40, color: 0xffb000 },
  { name: 'Mage', kind: 'cap', r: 0.16, len: 0.20, y: 1.05, color: 0xffd35c },
  { name: 'Ben', kind: 'cap', r: 0.14, len: 0.55, y: 0.45, color: 0x4aa3ff },
];
const target = new THREE.Group(); scene.add(target);
const capMesh = {};
for (const c of CAPS) {
  const geo = c.kind === 'sph' ? new THREE.SphereGeometry(c.r, 16, 12)
    : new THREE.CapsuleGeometry(c.r, c.len, 6, 12);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: c.color, roughness: .65, transparent: true, opacity: .92 }));
  m.position.y = c.y; m.castShadow = true; target.add(m); capMesh[c.name] = m;
}
target.add(makeLabel('MÅL', 0xff5c5c).translateY(2.05));

// ---------- emitter-ring + sikteskamera-modul (vid mynningen, samaxlig) ----------
const optic = new THREE.Group(); optic.position.copy(MUZZLE); scene.add(optic);
const camBox = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 0.05),
  new THREE.MeshStandardMaterial({ color: 0x00bcd4, emissive: 0x004a55, emissiveIntensity: 1 }));
camBox.position.x = 0.02; optic.add(camBox);                       // kamera i mitten
const emitMeshes = [];
for (const [ey, ez] of [[0.055, 0.055], [0.055, -0.055], [-0.055, 0.055], [-0.055, -0.055]]) {
  const e = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0x39d98a, emissive: 0x0c3a24, emissiveIntensity: 1 }));
  e.position.set(0.04, ey, ez); optic.add(e); emitMeshes.push(e);  // 4 IR-emittrar i kvadrat
}

// ---------- fiducial-konstellation på målets bröst (sett av sikteskameran) ----------
const fidGroup = new THREE.Group(); scene.add(fidGroup);
const fidNodes = [];
for (const [fx, fy] of [[-0.1, 0.11], [0.1, 0.11], [-0.1, -0.11], [0.1, -0.11]]) {
  const f = new THREE.Mesh(new THREE.SphereGeometry(0.022, 8, 8), new THREE.MeshBasicMaterial({ color: 0x2a3441 }));
  f.position.set(fx, fy, 0); fidGroup.add(f); fidNodes.push(f);
}
const lockMat = new THREE.LineBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0 });
const lockLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), lockMat);
scene.add(lockLine);

// ---------------- effekter ----------------
const trajMat = new THREE.LineBasicMaterial({ color: 0xffd35c, transparent: true });
const trajLine = new THREE.Line(new THREE.BufferGeometry(), trajMat); scene.add(trajLine); let trajTtl = 0;
const irMat = new THREE.LineBasicMaterial({ color: 0x39d98a, transparent: true });
const irLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), irMat);
scene.add(irLine); let irTtl = 0;
const round = new THREE.Mesh(new THREE.SphereGeometry(0.08, 8, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }));
round.visible = false; scene.add(round); let roundAnim = null;
const impact = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 10), new THREE.MeshBasicMaterial({ color: 0x39d98a })); impact.visible = false; scene.add(impact); let impactTtl = 0;
const rangeRing = new THREE.Mesh(new THREE.RingGeometry(0.98, 1, 64),
  new THREE.MeshBasicMaterial({ color: 0x39d98a, transparent: true, opacity: .35, side: THREE.DoubleSide }));
rangeRing.rotation.x = -Math.PI / 2; rangeRing.position.y = 0.03; scene.add(rangeRing);

// ---------------- state ----------------
const S = { fsm: 'READY', ammo: 30, health: 100, hits: [], dead: false,
  climb: 0, imu: 0, fireAcc: 0, tT: 0, sinceShot: 999, drift: 0,
  camLocked: false, sigmaEff: 0.5 };
let profile = HW.PROFILES['M4 / 5.56'];

// ---------------- UI ----------------
const $ = id => document.getElementById(id);
const selP = $('profile'); for (const k of Object.keys(HW.PROFILES)) selP.add(new Option(k, k));
const selE = $('env'); for (const k of Object.keys(HW.ENVIRONMENTS)) selE.add(new Option(k, k)); selE.value = 'Starkt solljus';
const C = {};
function readUI() {
  C.cur = +$('cur').value; C.beam = +$('beam').value; C.nled = +$('nled').value;
  C.filter = $('filter').checked; C.env = HW.ENVIRONMENTS[selE.value];
  C.gnss = $('gnss').checked; C.cam = $('cam').checked;
  C.fas2 = $('fas2').checked; C.sigma = +$('sigma').value; C.tspd = +$('tspd').value;
  C.wind = +$('wind').value; C.autofire = $('autofire').checked;
  $('v-cur').textContent = C.cur.toFixed(1) + ' A'; $('v-beam').textContent = C.beam.toFixed(1) + '°';
  $('v-nled').textContent = C.nled; $('v-sigma').textContent = C.sigma.toFixed(1) + '°';
  $('v-tspd').textContent = C.tspd.toFixed(1) + ' m/s'; $('v-wind').textContent = C.wind.toFixed(1) + ' m/s';
}
['cur', 'beam', 'nled', 'sigma', 'tspd', 'wind'].forEach(id => $(id).addEventListener('input', readUI));
['filter', 'fas2', 'autofire', 'gnss', 'cam'].forEach(id => $(id).addEventListener('change', readUI));
selE.addEventListener('change', readUI);
selP.addEventListener('change', () => { profile = HW.PROFILES[selP.value]; $('beam').value = profile.beamHalf; S.ammo = profile.mag; S.fsm = 'READY'; readUI(); });
readUI();
$('btn-mag').onclick = () => { if (S.fsm === 'NO_MAG') S.fsm = 'MAG_IN'; };
$('btn-rack').onclick = () => { if ((S.fsm === 'MAG_IN' || S.fsm === 'EMPTY') && S.ammo > 0) S.fsm = 'READY'; };
$('btn-reload').onclick = () => { S.ammo = profile.mag; S.fsm = 'READY'; };
$('btn-fire').onclick = () => fire();
$('btn-reset').onclick = () => { S.health = 100; S.hits = []; S.dead = false; $('killbanner').style.display = 'none'; };
$('btn-fps').onclick = () => fps.lock();
let fpsActive = false;
fps.addEventListener('lock', () => { fpsActive = true; orbit.enabled = false; $('reticle').style.display = 'block'; camera.position.copy(MUZZLE).add(new THREE.Vector3(-0.2, 0.12, 0)); });
fps.addEventListener('unlock', () => { fpsActive = false; orbit.enabled = true; $('reticle').style.display = 'none'; });
renderer.domElement.addEventListener('mousedown', e => { if (fpsActive && e.button === 0) fire(); });

// ---------------- hjälp ----------------
function gaussian() { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
function targetPos(t) { const x = 28 - 7 * Math.sin(0.18 * t); const w = C.tspd / 11; return new THREE.Vector3(x, 0, 11 * Math.sin(w * t)); }
function targetVelZ(t) { const w = C.tspd / 11; return 11 * w * Math.cos(w * t); }
function zoneByName(n) { return HW.ZONES.find(z => z.name === n) || HW.ZONES[1]; }
function nearestZone(cz) {
  let best = HW.ZONES[1], bd = 1e9;
  for (const z of HW.ZONES) { const d = Math.min(Math.abs(cz - z.zl), Math.abs(cz - z.zh)); if (d < bd) { bd = d; best = z; } }
  return best;
}

// ---------------- AVFYRNING (nivå 3-pipeline) ----------------
function fire() {
  if (S.fsm !== 'READY' || S.ammo <= 0 || S.dead) return;
  S.ammo--; S.sinceShot = 0; S.climb += profile.recoilDeg * 0.5;
  if (S.ammo === 0) S.fsm = 'EMPTY';

  const tp0 = targetPos(S.tT);                                  // mål vid avfyrning
  const Rt = Math.hypot(tp0.x - MUZZLE.x, tp0.z - MUZZLE.z);
  const irMax = HW.maxRange(C.cur, C.beam, C.env, C.nled, C.filter);

  // --- ① sikte (fuserad pose: IMU + GNSS-yaw + IR-ankare + ev. kamera/AI) ---
  let dir, muzzle = MUZZLE.clone();
  if (fpsActive) { dir = new THREE.Vector3(); camera.getWorldDirection(dir); muzzle = camera.position.clone(); }
  else {
    // kameran mäter målets fart optiskt → exakt lead; annars kräver Fas 2 för lead
    const lead = (C.fas2 || S.camLocked) ? targetVelZ(S.tT) * HW.tof(Rt, profile.v0) : 0;
    const aim = new THREE.Vector3(tp0.x, 1.42, tp0.z + lead);
    const headErr = C.gnss ? HW.GNSS_YAW_RESID * gaussian() : S.drift;        // GNSS binder yaw, annars vandrar IMU-driften
    const sig = S.sigmaEff;                                                    // σ_eff: kamera/AI-lås krymper siktfelet
    aim.z += Rt * Math.tan((gaussian() * sig + headErr) * Math.PI / 180);      // siktfel + heading
    aim.y += Rt * Math.tan((gaussian() * sig + S.climb) * Math.PI / 180);      // + rekyl-klättring
    dir = aim.clone().sub(muzzle).normalize();
  }

  // --- ④ IR LOS + zon (rakt sikte mot målplanet) ---
  const sP = (tp0.x - muzzle.x) / (dir.x || 1e-6);
  const aimPlane = muzzle.clone().add(dir.clone().multiplyScalar(sP));
  const cy = aimPlane.z - tp0.z, cz = aimPlane.y, rB = HW.beamRadius(Rt, C.beam);
  const irOverlap = Math.abs(cy) <= 0.25 + rB && cz >= -rB && cz <= 1.85 + rB;
  const irHit = irOverlap && Rt <= irMax;
  const irZone = irHit ? (HW.zoneAt(cz, cy)?.name || nearestZone(cz).name) : null;
  if (irHit) S.drift = 0;                                       // IR-ankaret nollställer heading-drift

  // --- ② ballistik-bana (3D, drop+drag+vind) ---
  const traj = HW.integrate3D(muzzle.x, muzzle.y, muzzle.z, dir.x, dir.y, dir.z,
    profile.v0, [0, 0, C.wind], Rt + 12);

  // --- ③ geometri: CCD-skärning mot rörliga kapslar ---
  let geo = { arrived: false };
  for (let i = 0; i < traj.length - 1 && !geo.arrived; i++) {
    const s0 = traj[i], s1 = traj[i + 1];
    const tp = targetPos(S.tT + s0.t);                          // målet hann röra sig (lead/CCD)
    for (const c of HW.bodyCapsules(tp.x, tp.z)) {
      const cs = HW.closestSegSeg([s0.x, s0.y, s0.z], [s1.x, s1.y, s1.z], c.p0, c.p1);
      if (cs.dist < c.r + 0.011) {
        geo = { arrived: true, zone: c.name, mult: c.mult, point: cs.point, v: s0.v, t: s0.t,
          range: Math.hypot(s0.x - muzzle.x, s0.y - muzzle.y, s0.z - muzzle.z) };
        break;
      }
    }
  }

  // --- visualisera bana ---
  trajLine.geometry.setFromPoints(traj.map(s => new THREE.Vector3(s.x, s.y, s.z)));
  trajMat.color.setHex(geo.arrived ? 0x39d98a : 0xffb000); trajMat.opacity = 1; trajTtl = 0.5;
  irLine.geometry.setFromPoints([muzzle, aimPlane]);
  irMat.color.setHex(!irHit ? (Rt > irMax ? 0xff5c5c : 0x6e7681) : 0x39d98a); irMat.opacity = 1; irTtl = 0.18;

  // flyg kulan längs banan, applicera fusionen vid ankomst
  roundAnim = { traj, t: 0, dur: Math.min(Math.max(traj[traj.length - 1].t * 4, 0.25), 0.7),
    geo, irHit, irZone, dragRange: Rt };

  // telemetri/HUD
  const pkt = HW.milestagShot(7, 1, profile.dmg);
  $('packet').textContent = pkt.bits + '  (' + pkt.airtimeMs.toFixed(0) + ' ms)';
  $('t-ie').textContent = HW.emitterIe(C.cur, C.beam, C.nled).toFixed(0) + ' W/sr';
  updateAdjud({ Rt, irMax, irHit, irZone, irOverlap, geo });
  updateHUD(Rt, HW.tof(Rt, profile.v0), irMax);
}

// fusion appliceras när kulan "anländer"
function resolve(a) {
  const ir = a.irHit, geo = a.geo;
  let verdict, cls, zone = null, dmg = 0;
  if (geo.arrived && ir) {
    zone = a.irZone; dmg = profile.dmg * zoneByName(zone).mult * Math.max(0.5, geo.v / profile.v0);
    verdict = `HIT · ${zone}`; cls = zone === 'Huvud' ? 'no' : 'ok';
    applyHit(zone, dmg, geo);
  } else if (geo.arrived && !ir) { verdict = 'NEAR-MISS (ingen LOS)'; cls = 'warn'; }
  else if (!geo.arrived && ir) { verdict = 'FÖRKASTAD (nådde ej fram)'; cls = 'no'; }
  else { verdict = 'MISS'; cls = 'no'; }
  const el = $('a-final'); el.textContent = verdict; el.className = 'v ' + cls;
}
function applyHit(zone, dmg, geo) {
  if (S.dead) return;
  S.health = Math.max(0, S.health - dmg);
  S.hits.push({ t: S.tT, zone, dmg: Math.round(dmg) });
  const m = capMesh[zone]; if (m) { m.material.emissive = new THREE.Color(0xffffff); m.material.emissiveIntensity = 1; setTimeout(() => m.material.emissiveIntensity = 0, 220); }
  impact.position.set(geo.point[0], geo.point[1], geo.point[2]); impact.visible = true; impactTtl = 0.4;
  if (S.health <= 0 && !S.dead) { S.dead = true; $('killbanner').style.display = 'block'; }
  updateHUD();
}

// ---------------- HUD ----------------
function updateAdjud(a) {
  const set = (id, txt, cls) => { const e = $(id); e.textContent = txt; e.className = 'v ' + (cls || ''); };
  const poseTxt = (C.cam && S.camLocked) ? 'kamera-lås' : (C.gnss ? 'IMU+GNSS' : 'IMU');
  set('a-aim', (a.irOverlap ? 'inom strålkon' : 'utanför') + ' · ' + poseTxt + ' σ' + S.sigmaEff.toFixed(2) + '°', a.irOverlap ? 'ok' : 'no');
  set('a-traj', 'integrerad (3-DOF)', '');
  set('a-tof', (HW.tof(a.geo.arrived ? a.geo.range : a.Rt, profile.v0) * 1000).toFixed(0) + ' ms / ' + (HW.drop(a.geo.arrived ? a.geo.range : a.Rt, profile.v0) * 100).toFixed(1) + ' cm', '');
  set('a-vimp', a.geo.arrived ? a.geo.v.toFixed(0) + ' m/s' : '–', '');
  set('a-geo', a.geo.arrived ? 'anlände · ' + a.geo.zone : 'nådde ej fram', a.geo.arrived ? 'ok' : 'no');
  set('a-ir', a.irHit ? 'LOS ✓ · ' + a.irZone : (a.Rt > a.irMax ? 'utom IR-räckvidd' : 'ingen LOS'), a.irHit ? 'ok' : 'no');
}
function updateHUD(R, tofS, irMax) {
  $('hud-ammo').textContent = S.ammo;
  const st = $('hud-state'); st.textContent = S.fsm; st.className = 'state s-' + S.fsm;
  if (R !== undefined) { $('hud-range').textContent = R.toFixed(0) + ' m'; $('hud-tof').textContent = (tofS * 1000).toFixed(0) + ' ms'; $('hud-irrange').textContent = irMax.toFixed(0) + ' m'; }
  $('hud-hits').textContent = S.hits.length;
  const hp = S.health / 100, bar = $('hp-bar');
  bar.style.width = (hp * 100) + '%'; bar.style.background = hp > .5 ? '#39d98a' : hp > .2 ? '#ffb000' : '#ff5c5c';
  $('hitlog').innerHTML = S.hits.slice(-5).reverse().map(h =>
    `<div style="color:${h.zone === 'Huvud' ? '#ff5c5c' : '#e6edf3'}">${h.t.toFixed(1)}s · ${h.zone} −${h.dmg}${h.zone === 'Huvud' ? ' ★' : ''}</div>`).join('');
}

// ---------------- loop ----------------
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  S.tT += dt; S.sinceShot += dt;
  S.climb = Math.max(0, S.climb - dt * 6);
  S.drift = Math.min(S.drift + dt * 0.15, 3);      // IMU heading-drift (nollställs av IR-träff)
  S.imu = HW.imuRate(Math.min(S.sinceShot, 0.08));

  const tp = targetPos(S.tT); target.position.set(tp.x, 0, tp.z); target.lookAt(0, 1, 0);
  for (const c of CAPS) capMesh[c.name].material.color.setHex(S.dead ? 0x6e7681 : c.color);

  // --- fuserad pose: live kamera-lås + effektiv siktprecision (σ_eff) ---
  const Rlive = Math.hypot(tp.x - MUZZLE.x, tp.z - MUZZLE.z);
  const camS = C.cam ? HW.cameraPose(Rlive, 0, true) : null;       // optisk bäring (grader) eller null
  S.camLocked = camS != null;
  S.sigmaEff = camS != null ? Math.hypot(C.sigma * 0.12, camS) : C.sigma;  // AI fire-control förfinar siktet

  // emitter-ring + fiducial-konstellation + lås-linje
  for (const e of emitMeshes) e.material.emissiveIntensity = irTtl > 0 ? 2.4 : 1;   // blixtrar vid skott
  camBox.material.emissiveIntensity = C.cam ? 1.6 : 0.4;
  fidGroup.visible = C.cam;
  fidGroup.position.set(tp.x, 1.40, tp.z); fidGroup.lookAt(MUZZLE.x, 1.40, MUZZLE.z);
  const lit = C.cam && S.camLocked && !S.dead;
  for (const f of fidNodes) f.material.color.setHex(lit ? 0x00e5ff : 0x2a3441);
  if (lit) {
    lockLine.geometry.setFromPoints([new THREE.Vector3(MUZZLE.x + 0.05, MUZZLE.y, MUZZLE.z), new THREE.Vector3(tp.x, 1.40, tp.z)]);
    lockMat.opacity = 0.4;
  } else lockMat.opacity = 0;

  if (C.autofire && !S.dead && S.fsm === 'READY' && S.ammo > 0) {
    S.fireAcc += dt; if (S.fireAcc >= 60 / profile.rofRpm) { S.fireAcc = 0; fire(); }
  }
  if (C.autofire && S.fsm === 'EMPTY' && S.sinceShot > 1.2) { S.ammo = profile.mag; S.fsm = 'READY'; }

  if (trajTtl > 0) { trajTtl -= dt; trajMat.opacity = Math.min(1, trajTtl / 0.5); } else trajMat.opacity = 0;
  if (irTtl > 0) { irTtl -= dt; irMat.opacity = Math.min(1, irTtl / 0.18); } else irMat.opacity = 0;
  if (impactTtl > 0) { impactTtl -= dt; } else impact.visible = false;

  if (roundAnim) {
    roundAnim.t += dt; const u = Math.min(roundAnim.t / roundAnim.dur, 1);
    const tr = roundAnim.traj, idx = Math.min(Math.floor(u * (tr.length - 1)), tr.length - 1);
    const s = tr[idx]; round.position.set(s.x, s.y, s.z); round.visible = true;
    if (u >= 1) { round.visible = false; resolve(roundAnim); roundAnim = null; }
  }

  const irMax = HW.maxRange(C.cur, C.beam, C.env, C.nled, C.filter);
  rangeRing.scale.set(irMax, irMax, 1);
  rangeRing.material.color.setHex(Math.hypot(tp.x, tp.z) <= irMax ? 0x39d98a : 0xff5c5c);

  $('t-imu').textContent = S.imu.toFixed(0) + '°/s'; $('t-climb').textContent = S.climb.toFixed(1) + '°';
  $('t-pose').textContent = (C.cam && S.camLocked) ? 'IMU+GNSS+IR+Kamera' : (C.gnss ? 'IMU+GNSS+IR' : 'IMU+IR');
  $('t-sigma').textContent = S.sigmaEff.toFixed(2) + '°';
  const cl = $('t-camlock');
  cl.textContent = C.cam ? (S.camLocked ? 'LÅST' : 'inget lås') : 'av';
  cl.className = 'v ' + (C.cam ? (S.camLocked ? 'ok' : 'no') : '');
  $('hud-ammo').textContent = S.ammo;
  const st = $('hud-state'); st.textContent = S.fsm; st.className = 'state s-' + S.fsm;
  renderer.render(scene, camera);
}
updateHUD(targetPos(0).x, HW.tof(28, profile.v0), HW.maxRange(3, 1, 30));
animate();
