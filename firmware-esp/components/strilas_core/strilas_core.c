/* STRILAS — portabel algoritm-kärna (Fas 3). Se strilas_core.h. */
#include "strilas_core.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define DEG(x) ((x) * 57.29577951308232)   /* 180/pi */

/* ───────────────────────── blob-detektion (O(n) CCL) ─────────────────────────
 * Fas 2-fixen i C: tvåpass connected-components med union-find istället för den
 * O(n²)-greedy som skenar i dagsljus. På P4 körs detta lämpligen rad-baserat (två
 * rad-buffertar) + ROI; här en klar tvåpass-variant som är O(antal pixlar). */
static int uf_find(int *p, int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }
static void uf_union(int *p, int a, int b) { int ra = uf_find(p, a), rb = uf_find(p, b); if (ra != rb) p[ra] = rb; }

int sc_detect_blobs(const uint8_t *img, int w, int h,
                    double thresh_frac, int min_pix,
                    sc_blob_t *out, int max_out) {
    const int N = w * h;
    /* max-intensitet → tröskel */
    uint8_t mx = 0;
    for (int i = 0; i < N; i++) if (img[i] > mx) mx = img[i];
    if (mx == 0) return 0;
    const double thr = thresh_frac * (double)mx;

    int *label = (int *)malloc(sizeof(int) * N);   /* 0 = bakgrund */
    int *parent = (int *)malloc(sizeof(int) * (N + 1));
    if (!label || !parent) { free(label); free(parent); return 0; }
    memset(label, 0, sizeof(int) * N);
    int next = 1; parent[0] = 0;

    /* pass 1: tilldela provisoriska etiketter, unionera grannar (W, NW, N, NE) */
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            int idx = y * w + x;
            if ((double)img[idx] <= thr) continue;
            int best = 0;
            int nb[4], nn = 0;
            if (x > 0)              nb[nn++] = idx - 1;
            if (y > 0 && x > 0)     nb[nn++] = idx - w - 1;
            if (y > 0)              nb[nn++] = idx - w;
            if (y > 0 && x < w - 1) nb[nn++] = idx - w + 1;
            for (int k = 0; k < nn; k++) if (label[nb[k]]) { best = label[nb[k]]; break; }
            if (!best) { best = next; parent[next] = next; next++; }
            label[idx] = best;
            for (int k = 0; k < nn; k++) if (label[nb[k]]) uf_union(parent, best, label[nb[k]]);
        }
    }

    /* pass 2: ackumulera intensitets-viktade centroider per rot-etikett */
    double *su = (double *)calloc(next, sizeof(double));   /* Σ x·w */
    double *sv = (double *)calloc(next, sizeof(double));   /* Σ y·w */
    double *sw = (double *)calloc(next, sizeof(double));   /* Σ w   */
    int    *cnt = (int *)calloc(next, sizeof(int));
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            int idx = y * w + x;
            if (!label[idx]) continue;
            int r = uf_find(parent, label[idx]);
            double ww = (double)img[idx];
            su[r] += x * ww; sv[r] += y * ww; sw[r] += ww; cnt[r]++;
        }

    int m = 0;
    for (int r = 1; r < next && m < max_out; r++) {
        if (parent[r] != r) continue;            /* ej en rot */
        if (cnt[r] < min_pix || sw[r] <= 0) continue;
        out[m].u = su[r] / sw[r];
        out[m].v = sv[r] / sw[r];
        out[m].w = sw[r];
        m++;
    }
    free(label); free(parent); free(su); free(sv); free(sw); free(cnt);
    return m;
}

/* ───────────────────────── pose (speglar cv_pose.estimate_pose) ───────────────────────── */
int sc_estimate_pose(const sc_blob_t *b, int n, sc_pose_t *o) {
    if (n < 2) return -1;
    double cu = 0, cv = 0, vmin = b[0].v, vmax = b[0].v;
    for (int i = 0; i < n; i++) {
        cu += b[i].u; cv += b[i].v;
        if (b[i].v < vmin) vmin = b[i].v;
        if (b[i].v > vmax) vmax = b[i].v;
    }
    cu /= n; cv /= n;
    o->az_deg = DEG(atan((cu - SC_CX) / SC_F_PX));
    o->el_deg = -DEG(atan((cv - SC_CY) / SC_F_PX));
    double ang = (vmax - vmin) / SC_F_PX;        /* radianer */
    o->range_m = (ang > 1e-9) ? (SC_BASELINE_V / tan(ang)) : INFINITY;
    o->n = n;
    return 0;
}

/* ───────────────────────── ballistik (speglar ballistics.py) ───────────────────────── */
#define BAL_G 9.81
#define BAL_KD 0.001277
#define BAL_DT 5e-4
#define BAL_MAXPTS 8192
typedef struct { double v0; int n; double X[BAL_MAXPTS], T[BAL_MAXPTS], Y[BAL_MAXPTS], V[BAL_MAXPTS]; } bal_table_t;
static bal_table_t g_cache[8];
static int g_cache_n = 0;

static bal_table_t *bal_table(double v0) {
    v0 = round(v0 * 10.0) / 10.0;                 /* round(v0,1) som Python */
    for (int i = 0; i < g_cache_n; i++) if (g_cache[i].v0 == v0) return &g_cache[i];
    bal_table_t *t = &g_cache[g_cache_n < 8 ? g_cache_n++ : 0];
    t->v0 = v0;
    double x = 0, y = 0, tm = 0, vx = v0, vy = 0;
    int k = 0;
    t->X[k] = 0; t->T[k] = 0; t->Y[k] = 0; t->V[k] = v0; k++;
    while (x < 320 && y > -5 && k < BAL_MAXPTS) {
        double sp = sqrt(vx * vx + vy * vy);
        vx += -BAL_KD * sp * vx * BAL_DT;
        vy += (-BAL_G - BAL_KD * sp * vy) * BAL_DT;
        x += vx * BAL_DT; y += vy * BAL_DT; tm += BAL_DT;
        t->X[k] = x; t->T[k] = tm; t->Y[k] = -y; t->V[k] = sqrt(vx * vx + vy * vy); k++;
    }
    t->n = k;
    return t;
}

static double interp(double xq, const double *X, const double *F, int n) {
    if (xq <= X[0]) return F[0];
    if (xq >= X[n - 1]) return F[n - 1];
    int lo = 0, hi = n - 1;                       /* X är monotont stigande */
    while (hi - lo > 1) { int mid = (lo + hi) / 2; if (X[mid] <= xq) lo = mid; else hi = mid; }
    double f = (xq - X[lo]) / (X[hi] - X[lo]);
    return F[lo] + f * (F[hi] - F[lo]);
}

void sc_ballistics(double range_m, double v0, double *tof, double *drop, double *vimp) {
    bal_table_t *t = bal_table(v0);
    if (tof)  *tof  = interp(range_m, t->X, t->T, t->n);
    if (drop) *drop = interp(range_m, t->X, t->Y, t->n);
    if (vimp) *vimp = interp(range_m, t->X, t->V, t->n);
}

/* ───────────────────────── fire-control (speglar fire_control.py) ───────────────────────── */
void sc_firing_solution(double range_m, double v_lat_mps, double v0, sc_solution_t *o) {
    sc_ballistics(range_m, v0, &o->tof, &o->drop, &o->vimp);
    o->lead_az_deg     = DEG(atan((v_lat_mps * o->tof) / range_m));
    o->holdover_el_deg = DEG(atan(o->drop / range_m));
}

/* ───────────────────────── rullande IR-kod (speglar anticheat.RollingCode) ───────────────────────── */
void sc_rolling_init(sc_rolling_t *r, uint32_t seed) { r->state = seed; }
uint16_t sc_rolling_next(sc_rolling_t *r) {
    r->state = (uint32_t)(r->state * 1103515245u + 12345u);
    return (uint16_t)((r->state >> 8) & 0xFFFF);
}
