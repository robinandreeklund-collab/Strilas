/* STRILAS — portabel algoritm-kärna (Fas 3).
 *
 * Den HETA, port-kritiska logiken i ren C99 (endast <math.h>): blob-detektion
 * (O(n) connected-components — Fas 2-fixen), pose, fire-control, ballistik och
 * rullande IR-kod. Identisk matematik som Python-referensen (firmware *.py) och
 * paritetstestad mot den (test/core_test.c). INGA ESP-IDF-beroenden → kompilerar
 * och testas på host; länkas oförändrad in i nod-firmware via HAL:en.
 *
 * Server-sidan (adjudicator/engine) STANNAR i Python — bara nodernas hot-path portas.
 */
#ifndef STRILAS_CORE_H
#define STRILAS_CORE_H
#include <stdint.h>
#include <stddef.h>

/* ---- kamera/konstellation/profil (speglar firmware/config.py) ---- */
#define SC_NX        1280
#define SC_NY        800
#define SC_FOV_DEG   13.7
#define SC_F_PX      5327.6529   /* (NX/2)/tan(FOV/2) */
#define SC_CX        640.0
#define SC_CY        400.0
#define SC_BASELINE_V 0.600      /* hjälm→midja [m] */
#define SC_V0        880.0       /* mynningshastighet [m/s] */

typedef struct { double u, v, w; } sc_blob_t;            /* centroid + intensitetsvikt */
typedef struct { double az_deg, el_deg, range_m; int n; } sc_pose_t;
typedef struct { double lead_az_deg, holdover_el_deg, tof, drop, vimp; } sc_solution_t;

/* ---- blob-detektion: mono8-frame → centroider (O(n) connected-components) ----
 * thresh_frac av max (0.35 default), min_pix minsta pixlar per blob.
 * Skriver upp till max_out blobbar i out[], returnerar antalet. */
int sc_detect_blobs(const uint8_t *img, int w, int h,
                    double thresh_frac, int min_pix,
                    sc_blob_t *out, int max_out);

/* ---- pose: blobbar → (az, el, range). Speglar cv_pose.estimate_pose. ---- */
int sc_estimate_pose(const sc_blob_t *blobs, int n, sc_pose_t *out);

/* ---- ballistik: Euler-integration → flygtid/drop/anslagsfart (cachad per v0) ---- */
void sc_ballistics(double range_m, double v0, double *tof, double *drop, double *vimp);

/* ---- fire-control: lead (rörligt mål) + holdover (drop) i grader ---- */
void sc_firing_solution(double range_m, double v_lat_mps, double v0, sc_solution_t *out);

/* ---- rullande IR-kod (LCG), delas vapen↔server. Speglar anticheat.RollingCode ---- */
typedef struct { uint32_t state; } sc_rolling_t;
void     sc_rolling_init(sc_rolling_t *r, uint32_t seed);
uint16_t sc_rolling_next(sc_rolling_t *r);

#endif /* STRILAS_CORE_H */
