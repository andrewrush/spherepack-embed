import numpy as np
from math import gamma, pi, exp, log, sqrt, ceil, lgamma

# Riemann zeta function approximation for integer n >= 2
def zeta(n):
    """Approximation of Riemann zeta function for integer n."""
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
        # Radius too large, fall back to full cube
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
    if vol_ball <= 0 or vol_ball != vol_ball:  # NaN check
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
