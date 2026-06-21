/* STRILAS — på-enhet HAL (Fas 3). Speglar firmware/hal.py:s gränssnitt i C.
 * Nod-logiken (main/node_*.c) anropar BARA detta + strilas_core; all hårdvara
 * (kamera/IMU/TSOP/IR/TPIC/radio) ligger bakom drivrutins-implementationen
 * (hal_esp.c). Byt hal_esp.c → annan bärare utan att röra nod-logiken. */
#ifndef STRILAS_HAL_H
#define STRILAS_HAL_H
#include <stdint.h>
#include <stddef.h>
#include "strilas_core.h"

typedef enum { NODE_OPTIK = 0, NODE_VEST = 1, NODE_HELMET = 2 } node_role_t;

/* ---- meddelanden (samma fält/namn som firmware/protocol.py → JSON till servern) ---- */
typedef struct {
    int shooter_id; double t_fire; int seq; uint32_t nonce;
    double aim_az_deg, aim_el_deg, range_m, target_vx_mps;
    const char *weapon_profile; int fire_control; uint16_t ir_code; int n_blobs;
    char hmac[17];
} fire_event_t;

typedef struct {
    int target_id; double t_rx; uint16_t ir_code; int shooter_id_decoded;
    const char *zone_hint; double rssi; int seq; char hmac[17];
} ir_hit_t;

/* JSON-packning som matchar protocol.py (för Python-servern). Returnerar längd. */
int hal_pack_fire(const fire_event_t *fe, char *buf, size_t n);
int hal_pack_irhit(const ir_hit_t *ih, char *buf, size_t n);

/* ---- klocka (PTP-synkad monoton på HW) ---- */
double hal_now(void);                 /* sekunder, synkad mot serverns klocka */

/* ---- radio (ESP-NOW/WiFi6-mesh; topic → MQTT på server-gateway) ---- */
typedef void (*hal_rx_cb)(const char *topic, const uint8_t *data, size_t len);
int  hal_radio_init(node_role_t role);
int  hal_radio_send(const char *topic, const void *data, size_t len);
int  hal_radio_subscribe(const char *topic, hal_rx_cb cb);

/* ---- sensorer (rollberoende; saknad HW → returnerar 0/negativt) ---- */
int  hal_camera_grab(uint8_t *frame, int w, int h);          /* optik: OV9281 → mono8 */
int  hal_imu_read(double rpy[3], double gyro_dps[3]);        /* ICM-42688-P */
int  hal_ir_decode(uint16_t *ir_code, int *shooter_id, const char **zone);  /* TSOP4856 */

/* ---- ställdon ---- */
void hal_fire_laser(uint16_t ir_code);                       /* SFH4725S CC-driver, 56 kHz */
void hal_recoil(const char *profile);
void hal_vibrate(const char *zone, double intensity);        /* TPIC6B595 → ERM */
void hal_set_constellation(double current_a);                /* LED_EN → CC-sänka (C6/C23) */

/* ---- anti-fusk HMAC (säkert element på HW) ---- */
void hal_hmac16(const char *payload, char out[17]);

#endif
