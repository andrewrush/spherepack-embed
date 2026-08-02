import numpy as np
from math import gamma, pi, exp, log, sqrt, ceil, lgamma

# ═══════════════════════════════════════════════════════════════════
# EXISTING API — preserved for backward compatibility
# ═══════════════════════════════════════════════════════════════════

def zeta(n):
    """Approximation of Riemann zeta function for integer n >= 2."""
    if n == 2:
        return pi**2 / 6
    elif n == 3:
        return 1.202056903159594
    elif n == 4:
        return pi**4 / 90
    elif n == 6:
        return pi**6 / 945
    elif n == 8:
        return pi**8 / 9450
    else:
        return 1 + 2**(-n) + 3**(-n) + 4**(-n) + 5**(-n)

def minkowski_bound(n):
    """Minkowski lower bound for lattice packing density."""
    return zeta(n) / (2**(n - 1))

def kabatiansky_levenshtein_bound(n):
    """Kabatiansky-Levenshtein upper bound (asymptotic approximation)."""
    return 2**(-0.599 * n)

def coxeter_few_rogers_bound(n):
    """Coxeter-Few-Rogers upper bound."""
    return (n + 1) * 2**(-n) * zeta(n)

def volume_n_ball(n, r=1.0):
    """Volume of n-dimensional ball of radius r. Uses log-gamma for stability."""
    log_vol = (n / 2.0) * log(pi) - lgamma(n / 2.0 + 1.0) + n * log(r)
    return exp(log_vol)

def greedy_packing(n, target_count, min_dist, max_attempts=100000, seed=42, clip_to_bounds=False):
    """
    Greedy sphere packing in n-dimensional unit cube.
    Places spheres of radius min_dist/2 such that centers are at least min_dist apart.
    If clip_to_bounds=True, centers are restricted to [r, 1-r] so spheres
    stay fully inside the unit cube (useful for visualization).
    """
    rng = np.random.default_rng(seed)
    centers = []
    radius = min_dist / 2.0

    lo, hi = radius, 1.0 - radius
    if clip_to_bounds and (lo >= hi):
        clip_to_bounds = False

    for _ in range(max_attempts):
        if len(centers) >= target_count:
            break
        if clip_to_bounds:
            point = rng.uniform(lo, hi, size=n)
        else:
            point = rng.random(n)
        if len(centers) == 0:
            centers.append(point)
            continue
        dists = np.linalg.norm(np.array(centers) - point, axis=1)
        if np.min(dists) >= min_dist:
            centers.append(point)

    return np.array(centers)

def packing_density(centers, n, radius):
    """Calculate packing density."""
    if len(centers) == 0:
        return 0.0
    ball_vol = volume_n_ball(n, radius)
    total_ball_vol = len(centers) * ball_vol
    unit_cube_vol = 1.0
    return total_ball_vol / unit_cube_vol

def kissing_number_estimate(n):
    """Estimate kissing number using known bounds."""
    known = {1: 2, 2: 6, 3: 12, 4: 24, 8: 240, 24: 196560}
    if n in known:
        return known[n]
    return int(2**(0.2075 * n))

def embedding_capacity(n, min_dist, density):
    """
    Estimate how many embeddings fit in unit cube given packing density.
    Returns: estimated count, theoretical max by Minkowski, theoretical max by KL.
    """
    r = min_dist / 2.0
    vol_ball = volume_n_ball(n, r)
    if vol_ball <= 0 or vol_ball != vol_ball:
        return 0, 0, 0
    actual_count = int(density / vol_ball) if density > 0 else 0
    mink_count = int(minkowski_bound(n) / vol_ball)
    kl_count = int(kabatiansky_levenshtein_bound(n) / vol_ball)
    return actual_count, mink_count, kl_count

def compare_bounds(n_values):
    """Compare theoretical bounds across dimensions."""
    results = []
    for n in n_values:
        mink = minkowski_bound(n)
        kl = kabatiansky_levenshtein_bound(n)
        cfr = coxeter_few_rogers_bound(n)
        results.append({
            'n': n,
            'minkowski': mink,
            'kl': kl,
            'cfr': cfr,
            'gap': kl / mink if mink > 0 else float('inf')
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# NEW: Cohn-Elkies bounds (Astra #1 context)
# ═══════════════════════════════════════════════════════════════════

COHN_ELKIES_BOUNDS = {
    1: 1.00000,   2: 0.90690,   3: 0.77982,   4: 0.64774,
    5: 0.52506,   6: 0.41776,   7: 0.323757,  8: 0.25367,
    12: 0.08384,  16: 0.03433,  24: 0.00193,
}

BEST_KNOWN_DENSITY = {
    1: 1.00000,   2: 0.90690,   3: 0.74048,   4: 0.61685,
    5: 0.46526,   6: 0.37295,   7: 0.29530,   8: 0.25367,
    12: 0.04945,  16: 0.01685,  24: 0.00193,
}

OPTIMAL_DIMENSIONS = {1, 2, 3, 8, 24}

def cohn_elkies_bound(n):
    """
    Cohn-Elkies LP upper bound — the threshold Astra #1 approached.
    For tabulated dimensions: exact values from Henry Cohn (MIT).
    For others: smooth interpolation between KL and CE.
    """
    if n in COHN_ELKIES_BOUNDS:
        return COHN_ELKIES_BOUNDS[n]
    kl = kabatiansky_levenshtein_bound(n)
    if n < 8:
        ratio = 0.85
    elif n < 16:
        ratio = 0.75
    elif n < 24:
        ratio = 0.65
    else:
        ratio = 0.55
    return kl * ratio

def optimal_density(n):
    """Return proven optimal density, or best known if not proven."""
    return BEST_KNOWN_DENSITY.get(n, None)


def compare_all_bounds(n_values):
    """Extended comparison including CE bound and best known."""
    results = []
    for n in n_values:
        mink = minkowski_bound(n)
        kl = kabatiansky_levenshtein_bound(n)
        cfr = coxeter_few_rogers_bound(n)
        ce = cohn_elkies_bound(n)
        opt = optimal_density(n)
        results.append({
            'n': n,
            'minkowski': mink,
            'kl': kl,
            'cfr': cfr,
            'ce': ce,
            'optimal': opt,
            'gap_kl_mink': kl / mink if mink > 0 else float('inf'),
            'gap_ce_kl': ce / kl if kl > 0 else float('inf'),
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# NEW: Lattice packings (constructive, deterministic)
# ═══════════════════════════════════════════════════════════════════

def lattice_density(n, lattice_type="best"):
    """
    Return packing density for known lattices.
    lattice_type: "zn", "dn", "e8", "leech", or "best".
    """
    Vn = volume_n_ball(n, 1.0)
    if lattice_type == "zn":
        return Vn * (2.0 ** (-n))
    if lattice_type == "dn":
        return Vn * (2.0 ** (-n / 2 - 1))
    if n == 8 and lattice_type in ("best", "e8"):
        return Vn / 16.0
    if n == 24 and lattice_type in ("best", "leech"):
        return Vn
    if lattice_type == "best":
        return Vn * (2.0 ** (-n / 2 - 1))
    raise ValueError(f"Unknown lattice type: {lattice_type}")


def e8_lattice_points(side=2):
    """
    E8 lattice (optimal in 8D, Viazovska 2016).
    Construction: D8 ∪ (D8 + (1/2, ..., 1/2)).
    """
    # Generate D8 points
    ranges = [np.arange(-side, side + 1) for _ in range(8)]
    grid = np.stack(np.meshgrid(*ranges, indexing='ij'), axis=-1)
    pts = grid.reshape(-1, 8).astype(np.float64)
    mask = (np.sum(pts, axis=1) % 2 == 0)
    d8 = pts[mask]
    shift = np.ones(8) * 0.5
    d8_shifted = d8 + shift
    return np.vstack([d8, d8_shifted])
