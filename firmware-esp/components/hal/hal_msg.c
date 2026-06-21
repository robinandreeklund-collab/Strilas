/* STRILAS — meddelande-packning (Fas 3, portabel: ingen ESP-/HW-koppling).
 * Producerar JSON med EXAKT samma fältnamn/typer som firmware/protocol.py så att
 * Python-servern (engine.py) kan json.loads() noderna direkt. Flyttals-FORMAT
 * spelar ingen roll (servern parsar), bara nycklar/typer/struktur. */
#include "hal.h"
#include <stdio.h>

int hal_pack_fire(const fire_event_t *fe, char *buf, size_t n) {
    return snprintf(buf, n,
        "{\"shooter_id\": %d, \"t_fire\": %.6f, \"seq\": %d, \"nonce\": %u, "
        "\"aim_az_deg\": %.6f, \"aim_el_deg\": %.6f, \"range_m\": %.3f, "
        "\"target_vx_mps\": %.3f, \"weapon_profile\": \"%s\", \"fire_control\": %s, "
        "\"ir_code\": %u, \"n_blobs\": %d, \"hmac\": \"%s\"}",
        fe->shooter_id, fe->t_fire, fe->seq, fe->nonce,
        fe->aim_az_deg, fe->aim_el_deg, fe->range_m, fe->target_vx_mps,
        fe->weapon_profile, fe->fire_control ? "true" : "false",
        (unsigned)fe->ir_code, fe->n_blobs, fe->hmac);
}

int hal_pack_irhit(const ir_hit_t *ih, char *buf, size_t n) {
    return snprintf(buf, n,
        "{\"target_id\": %d, \"t_rx\": %.6f, \"ir_code\": %u, "
        "\"shooter_id_decoded\": %d, \"zone_hint\": \"%s\", \"rssi\": %.1f, "
        "\"seq\": %d, \"hmac\": \"%s\"}",
        ih->target_id, ih->t_rx, (unsigned)ih->ir_code,
        ih->shooter_id_decoded, ih->zone_hint, ih->rssi, ih->seq, ih->hmac);
}
