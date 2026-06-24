/* STRILAS — app-entry (Fas 3). Väljer nod-roll vid byggtid (-DSTRILAS_ROLE=...)
 * så SAMMA bygge/kodbas ger optik-, väst- eller hjälm-firmware. På ESP-IDF blir
 * detta app_main(); här en vanlig main() så strukturen kan länk-kollas på host. */
#include "hal.h"

#ifndef STRILAS_ROLE
#define STRILAS_ROLE 0          /* 0=optik, 1=väst, 2=hjälm */
#endif

/* nod-API:er (main/node_*.c) */
void node_optik_init(void);
int  node_optik_perceive(sc_pose_t *pose);
void node_optik_fire(const sc_pose_t *pose, double v_lat_mps, int use_fc);
void node_target_init(node_role_t role);
void node_target_on_ir(void);
void node_target_tick_state(double x, double vx);

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
void app_main(void)
#else
int main(void)
#endif
{
    node_role_t role = (node_role_t)STRILAS_ROLE;
    if (role == NODE_OPTIK) {
        node_optik_init();
        /* loop: 120 fps frame-tick → perceive; avtryck → fire. (drivs av kamera-/GPIO-event) */
    } else {
        node_target_init(role);
        /* loop: TSOP-event → on_ir; 10 Hz timer → tick_state; verdict-cb → vibrate. */
    }
#ifndef ESP_PLATFORM
    return 0;
#endif
}
