#!/usr/bin/env python3
import time
from spherepack import (
    greedy_packing, packing_density, compare_bounds, volume_n_ball,
    kissing_number_estimate, lattice_density, optimal_density
)

def benchmark_packing():
    print("=" * 62)
    print("  SpherePack Embed — бенчмарк упаковки шаров")
    print("=" * 62)
    print()

    print("--- Бенчмарк: жадная упаковка ---")
    print("  n | Target | Packed | Время (мс) | Density")
    print("-" * 55)

    scenarios = [
        (3, 50, 0.25),
        (3, 100, 0.20),
        (8, 100, 0.35),
        (16, 50, 0.45),
        (32, 30, 0.50),
        (64, 20, 0.55),
    ]

    for n, target, min_dist in scenarios:
        t0 = time.perf_counter()
        centers = greedy_packing(n, target, min_dist, max_attempts=50000, seed=42)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000
        density = packing_density(centers, n, min_dist / 2.0)
        print(f" {n:2d} | {target:6d} | {len(centers):6d} | {elapsed_ms:9.3f} | {density:9.6f}")

    print()
    print("Вывод:")
    print("  • Упаковка 50 шаров в 3D — менее 10 мс.")
    print("  • С ростом n число успешно упакованных шаров падает")
    print("    (проклятие размерности), но алгоритм остаётся быстрым.")
    print("  • Для embeddings (n=64-768) жадный алгоритм даёт")
    print("    лишь базовую оценку ёмкости.")
    print()

    # NEW: Lattice vs Greedy comparison
    print("--- Бенчмарк: решётки vs жадная случайная ---")
    print("  n | Greedy Δ  | Lattice Δ | Best Known | Ratio L/G")
    print("-" * 60)

    for n in [2, 3, 4, 6, 8, 12, 16, 24]:
        centers = greedy_packing(n, min(500, 50 if n > 16 else 200), 0.3, max_attempts=50000, seed=42)
        greedy_d = packing_density(centers, n, 0.15)

        if n == 8:
            lat_d = lattice_density(8, "e8")
        elif n == 24:
            lat_d = lattice_density(24, "leech")
        else:
            lat_d = lattice_density(n, "dn")

        opt = optimal_density(n)
        opt_str = f"{opt:.2e}" if opt else "?"
        ratio = lat_d / greedy_d if greedy_d > 0 else float('inf')

        print(f" {n:2d} | {greedy_d:9.2e} | {lat_d:9.2e} | {opt_str:>10} | {ratio:8.1f}x")

    print()
    print("  Вывод: структурированные решётки на порядки плотнее")
    print("         случайного размещения в высоких размерностях.")
    print()

    print("--- Бенчмарк: вычисление теоретических границ ---")
    print("  n | Minkowski (µs) | KL (µs) | CFR (µs)")
    print("-" * 50)

    for n in [8, 16, 32, 64, 128, 256, 512]:
        t0 = time.perf_counter()
        for _ in range(1000):
            from spherepack import minkowski_bound, kabatiansky_levenshtein_bound, coxeter_few_rogers_bound
            minkowski_bound(n)
        t1 = time.perf_counter()
        mink_us = (t1 - t0) / 1000 * 1e6

        t0 = time.perf_counter()
        for _ in range(1000):
            kabatiansky_levenshtein_bound(n)
        t1 = time.perf_counter()
        kl_us = (t1 - t0) / 1000 * 1e6

        t0 = time.perf_counter()
        for _ in range(1000):
            coxeter_few_rogers_bound(n)
        t1 = time.perf_counter()
        cfr_us = (t1 - t0) / 1000 * 1e6

        print(f" {n:3d} | {mink_us:13.3f} | {kl_us:7.3f} | {cfr_us:7.3f}")

    print()
    print("Вывод: вычисление границ — микросекунды даже для n=512.")
    print()

if __name__ == "__main__":
    benchmark_packing()
