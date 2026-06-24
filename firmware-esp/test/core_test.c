/* STRILAS — host-paritetstest för strilas_core (Fas 3).
 * Kompileras och körs på host (gcc) UTAN ESP-IDF. Verifierar att den portade
 * C-kärnan ger SAMMA resultat som Python-referensen (firmware *.py). Referens-
 * värdena är fångade direkt ur Python (se commit-meddelandet).
 *   cc -O2 -I../components/strilas_core core_test.c ../components/strilas_core/strilas_core.c -lm -o /tmp/sc && /tmp/sc
 */
#include "strilas_core.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

static int fails = 0;
static void chk(const char *name, double got, double exp, double tol) {
    int ok = fabs(got - exp) <= tol;
    printf("  %s %-28s got %.10f  exp %.10f  (tol %.0e)\n", ok ? "OK " : "ERR", name, got, exp, tol);
    if (!ok) fails++;
}
static void chk_u(const char *name, unsigned got, unsigned exp) {
    int ok = got == exp;
    printf("  %s %-28s got %u  exp %u\n", ok ? "OK " : "ERR", name, got, exp);
    if (!ok) fails++;
}

int main(void) {
    printf("STRILAS — strilas_core host-paritetstest (C ↔ Python-referens)\n");

    /* 1) ballistik @150 m, v0=880 */
    double tof, drop, vimp;
    sc_ballistics(150.0, 880.0, &tof, &drop, &vimp);
    chk("ballistics.tof", tof, 0.187937, 1e-5);
    chk("ballistics.drop", drop, 0.163163, 1e-5);
    chk("ballistics.vimp", vimp, 726.491954, 1e-3);

    /* 2) fire-control @150 m, mål 4 m/s */
    sc_solution_t s;
    sc_firing_solution(150.0, 4.0, 880.0, &s);
    chk("fc.lead_az_deg", s.lead_az_deg, 0.287144, 1e-5);
    chk("fc.holdover_el_deg", s.holdover_el_deg, 0.062323, 1e-5);

    /* 3) rullande IR-kod, seed = 0x1A2B ^ 7 = 0x1A2C — EXAKT heltalsmatch */
    sc_rolling_t r; sc_rolling_init(&r, 0x1A2Bu ^ 7u);
    unsigned roll_exp[6] = {3260, 32074, 51960, 27309, 47411, 60805};
    for (int i = 0; i < 6; i++) { char nm[24]; sprintf(nm, "roll[%d]", i); chk_u(nm, sc_rolling_next(&r), roll_exp[i]); }

    /* 4) pose från Python:s EXAKTA detekterade blob-centroider */
    sc_blob_t b[5] = {
        {640.0000000000, 386.5013501808, 5.3409426808},
        {634.7512641939, 398.9750163495, 6.0693939328},
        {645.2487358061, 398.9750163495, 6.0693939328},
        {635.7854202540, 407.9287949231, 6.0473808646},
        {644.2145797460, 407.9287949231, 6.0473808646},
    };
    sc_pose_t p; sc_estimate_pose(b, 5, &p);
    chk("pose.az_deg", p.az_deg, 0.0000000000, 1e-9);
    chk("pose.el_deg", p.el_deg, -0.0006645641, 1e-7);
    chk("pose.range_m", p.range_m, 149.1813207419, 1e-3);

    /* 5) O(n)-CCL korrekthet: rendera 5 IR-spots i en mono8-frame → hitta 5 blobbar
     *    nära rätt centra (sub-px-parwith Pythons float-render krävs ej; båda korrekta). */
    uint8_t *img = (uint8_t *)calloc(SC_NX * SC_NY, 1);
    double cx[5] = {640.0, 634.672, 645.328, 635.738, 644.262};
    double cy[5] = {386.503, 398.934, 398.934, 407.814, 407.814};
    for (int c = 0; c < 5; c++)
        for (int dy = -5; dy <= 5; dy++)
            for (int dx = -5; dx <= 5; dx++) {
                int x = (int)lround(cx[c]) + dx, y = (int)lround(cy[c]) + dy;
                if (x < 0 || x >= SC_NX || y < 0 || y >= SC_NY) continue;
                double g = 255.0 * exp(-((dx * dx + dy * dy) / (2.0 * 1.2 * 1.2)));
                int v = (int)(g); if (v > img[y * SC_NX + x]) img[y * SC_NX + x] = (uint8_t)v;
            }
    sc_blob_t found[16];
    int nb = sc_detect_blobs(img, SC_NX, SC_NY, 0.35, 2, found, 16);
    chk_u("ccl.n_blobs", (unsigned)nb, 5);
    sc_pose_t pc; int ok = (nb >= 2) ? (sc_estimate_pose(found, nb, &pc) == 0) : 0;
    if (ok) {
        int near = fabs(pc.range_m - 150.0) < 3.0;   /* render-shift → ~149-150 m, korrekt */
        printf("  %s ccl.pose.range_m            got %.4f  (förväntat ~149-150 m)\n", near ? "OK " : "ERR", pc.range_m);
        if (!near) fails++;
    } else { printf("  ERR ccl.pose misslyckades\n"); fails++; }
    free(img);

    printf("\n%s  (%d fel)\n", fails ? "PARITETSTEST: FEL" : "PARITETSTEST: ALLA OK", fails);
    return fails ? 1 : 0;
}
