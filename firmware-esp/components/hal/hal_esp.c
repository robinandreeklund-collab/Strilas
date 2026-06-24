/* STRILAS — HAL-implementation för ESP-IDF (Fas 3, INTEGRATIONS-STUBBAR).
 *
 * Detta är den ENDA filen som rör hårdvaran. Varje funktion har en TODO som pekar
 * på rätt ESP-IDF-drivrutin + kortets pinout (verifierad i hardware *_netlist.py).
 * Bygger mot ESP-IDF (esp_timer/esp_now/driver). Nod-logiken (main/node_*.c) är
 * redan klar och hårdvaru-oberoende — den körs paritetstestad via strilas_core.
 *
 * STATUS: ramverk + drivrutins-anknytning. Fylls i vid bänk-bringup (HIL), då
 * Fas 2:s checklista mäts (kamera-fps, CCL µs, ström/läge, dagsljus-SNR).
 */
#include "hal.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

#ifdef ESP_PLATFORM
#include "esp_timer.h"
#include "esp_now.h"
#include "esp_log.h"
static const char *TAG = "strilas_hal";
#else                              /* host-byggd attrapp (för länk-/struktur-koll) */
#include <time.h>
#define ESP_LOGW(t, ...) (void)0
#define ESP_LOGI(t, ...) (void)0
#endif

/* ───────── klocka ───────── */
double hal_now(void) {
#ifdef ESP_PLATFORM
    return (double)esp_timer_get_time() / 1e6 + 0.0 /* + PTP-offset från synk */;
#else
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
#endif
}

/* ───────── radio (ESP-NOW broadcast + topic-prefix; gateway bryggar → MQTT) ───────── */
int hal_radio_init(node_role_t role) {
    /* TODO: esp_now_init(); registrera peer (broadcast) på C6-radion (WiFi6).
     * Server-gateway (laptop) prenumererar och bryggar topics → MQTT (engine.py). */
    ESP_LOGI(TAG, "radio_init roll=%d (ESP-NOW/WiFi6 via onboard C6)", role);
    return 0;
}
int hal_radio_send(const char *topic, const void *data, size_t len) {
    /* TODO: packa [topic|payload] och esp_now_send(broadcast, ...). */
    (void)topic; (void)data; (void)len;
    return 0;
}
int hal_radio_subscribe(const char *topic, hal_rx_cb cb) {
    /* TODO: spara cb i tabell; esp_now_register_recv_cb() dispatchar per topic. */
    (void)topic; (void)cb;
    return 0;
}

/* ───────── sensorer ───────── */
int hal_camera_grab(uint8_t *frame, int w, int h) {
    /* TODO: OV9281 global shutter → mono8. Fas 2-beslut: MIPI-CSI (full-frame @120 fps)
     * ELLER USB-UVC full-frame @30 fps + ROI-spårning @120 fps. esp_cam/usb_host_uvc. */
    (void)frame; (void)w; (void)h;
    ESP_LOGW(TAG, "camera_grab: koppla OV9281 (se Fas 2 bandbredds-beslut)");
    return -1;
}
int hal_imu_read(double rpy[3], double gyro_dps[3]) {
    /* TODO: ICM-42688-P över SPI (SCK=GPIO23/MOSI=27/MISO=22/CS=32) el. I²C (SCL8/SDA7). */
    (void)rpy; (void)gyro_dps;
    return -1;
}
int hal_ir_decode(uint16_t *ir_code, int *shooter_id, const char **zone) {
    /* TODO: TSOP4856 DATA-linje (OR-diodad per patch) → RMT 56 kHz-avkodning → paket. */
    (void)ir_code; (void)shooter_id; (void)zone;
    return -1;
}

/* ───────── ställdon ───────── */
void hal_fire_laser(uint16_t ir_code) {
    /* TODO: SFH4725S CC-driver, 56 kHz-burst med koden. EYE-SAFE: HW-tak 1 A i kretsen. */
    (void)ir_code;
}
void hal_recoil(const char *profile) { (void)profile; /* TODO: solenoid-PWM + FAULT */ }
void hal_vibrate(const char *zone, double intensity) {
    /* TODO: TPIC6B595 open-drain PWM → ERM-vibrator för träffad zon. */
    (void)zone; (void)intensity;
}
void hal_set_constellation(double current_a) {
    /* TODO: LED_EN filtrerad PWM → CC-sänkans setpunkt (C6/C23 = 22 nF, τ≈20 µs). */
    (void)current_a;
}

/* ───────── anti-fusk HMAC ───────── */
void hal_hmac16(const char *payload, char out[17]) {
    /* TODO: HMAC-SHA256 med per-spelare-nyckel i säkert element (ATECC608/eFuse).
     * Här platshållare så strukturen länkar; matcha anticheat.sign (16 hex). */
    (void)payload;
    strcpy(out, "0000000000000000");
}
