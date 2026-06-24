/* STRILAS — MÅL-nod (väst & hjälm, Fas 3). Samma kod, olika target_id/roll.
 * TSOP avkodar IR → IRHit → mesh → server. Verdikt-broadcast → vibrera träffad zon.
 * Strömmar låg-rate PlayerState för serverns lag-komp. Speglar firmware/target_node.py.
 * Konstellations-LED drivs här (väst/hjälm) via CC-sänkan; kamera-synkad strobe. */
#include "hal.h"
#include "strilas_core.h"
#include <string.h>
#include <stdio.h>

static int g_target_id;
static int g_seq = 0;

static void on_verdict(const char *topic, const uint8_t *data, size_t len) {
    (void)topic; (void)len;
    /* servern broadcastar Verdict-JSON; vibrera om HIT på denna nod (parsning utelämnad i stub) */
    const char *s = (const char *)data;
    if (strstr(s, "\"result\": \"HIT\"")) hal_vibrate("Bröst", 1.0);
}

void node_target_init(node_role_t role) {
    g_target_id = (role == NODE_VEST) ? 1 : 2;
    hal_radio_init(role);
    hal_radio_subscribe("verdict", on_verdict);
    hal_set_constellation(1.0);       /* 1 A default-tak (eye-safe); kamera-synkad strobe */
}

/* anropas när TSOP avkodat en stråle */
void node_target_on_ir(void) {
    uint16_t code; int shooter; const char *zone;
    if (hal_ir_decode(&code, &shooter, &zone) != 0) return;
    ir_hit_t ih = {0};
    ih.target_id = g_target_id; ih.t_rx = hal_now(); ih.ir_code = code;
    ih.shooter_id_decoded = shooter; ih.zone_hint = zone ? zone : "Bröst";
    ih.rssi = -40.0; ih.seq = ++g_seq;
    char payload[96];
    snprintf(payload, sizeof payload, "%d|%.6f|%u|%d", ih.target_id, ih.t_rx, ih.ir_code, ih.seq);
    hal_hmac16(payload, ih.hmac);
    char json[200];
    int len = hal_pack_irhit(&ih, json, sizeof json);
    hal_radio_send("irhit", json, len);
}

/* anropas ~10 Hz (lag-komp): PlayerState. (position från RTK-puck på hjälm) */
void node_target_tick_state(double x, double vx) {
    char json[160];
    int len = snprintf(json, sizeof json,
        "{\"player_id\": %d, \"t\": %.6f, \"x\": %.3f, \"y\": 0.0, \"z\": 0.0, "
        "\"vx\": %.3f, \"vy\": 0.0, \"posture\": \"stand\"}",
        g_target_id, hal_now(), x, vx);
    hal_radio_send("pstate", json, len);
}
