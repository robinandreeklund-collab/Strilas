/* STRILAS — OPTIK/VAPEN-nod (Fas 3). Hårdvaru-oberoende logik; all I/O via hal.h.
 * Loop: grabba frame → O(n)-blobbar → pose. Vid trigger: fire-control (lead+holdover)
 * + rullande kod → signerad FireEvent → mesh → server. (Server-adjudikation = Python.)
 * Speglar firmware/weapon_node.py. */
#include "hal.h"
#include "strilas_core.h"
#include <string.h>
#include <stdio.h>

#define SHOOTER_ID 7
static sc_rolling_t g_roll;
static int g_seq = 0;
static uint8_t g_frame[SC_NX * SC_NY];

void node_optik_init(void) {
    hal_radio_init(NODE_OPTIK);
    sc_rolling_init(&g_roll, 0x1A2Bu ^ SHOOTER_ID);
    hal_set_constellation(0.0);     /* vapnet driver ej konstellation; mål gör det */
}

/* anropas av kamera-frame-tick (eller ROI-spårning @120 fps) */
int node_optik_perceive(sc_pose_t *pose) {
    if (hal_camera_grab(g_frame, SC_NX, SC_NY) != 0) return -1;
    sc_blob_t blobs[16];
    int n = sc_detect_blobs(g_frame, SC_NX, SC_NY, 0.35, 2, blobs, 16);
    return sc_estimate_pose(blobs, n, pose);
}

/* anropas vid avtryck (om NFC-ammo>0 + make-ready) */
void node_optik_fire(const sc_pose_t *pose, double v_lat_mps, int use_fc) {
    sc_solution_t s; double az = 0, el = 0;
    if (use_fc) {
        sc_firing_solution(pose->range_m, v_lat_mps, SC_V0, &s);
        az = s.lead_az_deg;
        el = s.holdover_el_deg;       /* + zon-vinkel adderas av sikteslogiken */
    }
    fire_event_t fe = {0};
    fe.shooter_id = SHOOTER_ID; fe.t_fire = hal_now(); fe.seq = ++g_seq;
    fe.ir_code = sc_rolling_next(&g_roll); fe.nonce = sc_rolling_next(&g_roll);
    fe.aim_az_deg = az; fe.aim_el_deg = el; fe.range_m = pose->range_m;
    fe.target_vx_mps = v_lat_mps; fe.weapon_profile = "M4 / 5.56";
    fe.fire_control = use_fc; fe.n_blobs = pose->n;

    char payload[160];
    snprintf(payload, sizeof payload, "%d|%.6f|%d|%u|%u|%.5f|%.5f|%.3f",
             fe.shooter_id, fe.t_fire, fe.seq, fe.nonce, fe.ir_code,
             fe.aim_az_deg, fe.aim_el_deg, fe.range_m);
    hal_hmac16(payload, fe.hmac);

    hal_fire_laser(fe.ir_code);       /* 56 kHz IR-burst med koden */
    hal_recoil(fe.weapon_profile);

    char json[256];
    int len = hal_pack_fire(&fe, json, sizeof json);
    hal_radio_send("fire", json, len);
}
