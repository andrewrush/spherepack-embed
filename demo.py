#!/usr/bin/env python3
import argparse
import sys
import os

from spherepack import (
    greedy_packing, packing_density, volume_n_ball, kissing_number_estimate,
    embedding_capacity, compare_bounds, minkowski_bound, kabatiansky_levenshtein_bound,
    zeta
)

def print_header():
    print("=" * 62)
    print("  SpherePack Embed — оптимизатор embedding-пространств")
    print("  Основано на прорыве Astra #1 (теорема упаковки шаров)")
    print("=" * 62)
    print()

def print_bounds_table():
    print("--- Сравнение теоретических границ packing density ---")
    print("  n |  Minkowski |      KL |       CFR |     Gap")
    print("-" * 55)
    n_values = [2, 3, 4, 8, 16, 24, 32, 64]
    for r in compare_bounds(n_values):
        print(f" {r['n']:2d} | {r['minkowski']:10.6f} | {r['kl']:7.5f} | {r['cfr']:9.6f} | {r['gap']:7.2f}x")
    print()
    print("  Minkowski = нижняя граница (решётки)")
    print("  KL = Kabatiansky-Levenshtein (верхняя, асимптотика)")
    print("  CFR = Coxeter-Few-Rogers (верхняя, конечные n)")
    print("  Gap = отношение верхней к нижней (чем меньше, тем точнее теория)")
    print()

def print_packing_demo(n=3, target=50, min_dist=0.25, seed=42):
    print(f"--- Демо: жадная упаковка шаров в {n}D ---")
    print(f"Параметры: размерность n={n}, min_dist={min_dist}, seed={seed}")

    centers = greedy_packing(n, target, min_dist, max_attempts=50000, seed=seed)
    r = min_dist / 2.0
    density = packing_density(centers, n, r)

    print(f"Упаковано шаров: {len(centers)} / {target} (попыток: 50000)")
    print(f"Packing density: {density:.6f}")
    print(f"Kissing number (оценка): {kissing_number_estimate(n)}")

    actual, mink_max, kl_max = embedding_capacity(n, min_dist, density)
    print(f"Ёмкость embedding-пространства:")
    print(f"  Фактическая:    {actual}")
    print(f"  Минковский max: {mink_max}")
    print(f"  KL max:         {kl_max}")
    print()

    if n == 3:
        print("Сгенерированы данные для 3D-визуализации.")
        print("Запустите: python demo.py --visualize для создания HTML.")
        print()

    return centers, density

def print_embedding_comparison():
    print("--- Сравнение: packing density в разных размерностях ---")
    print("Сценарий: жадная упаковка, target=1000, min_dist=0.30")
    print()
    print("  n | Packed | Density  | Minkowski | KL       | Применение")
    print("-" * 70)

    scenarios = [
        (3, "3D-визуализация"),
        (8, "Small embeddings (MNIST-like)"),
        (16, "Text embeddings (small)"),
        (32, "Sentence embeddings"),
        (64, "Image embeddings (CLIP)"),
        (128, "Large text embeddings"),
        (768, "BERT embeddings"),
    ]

    for n, app in scenarios:
        centers = greedy_packing(n, 1000, 0.30, max_attempts=50000, seed=42)
        r = 0.15
        density = packing_density(centers, n, r)
        mink = minkowski_bound(n)
        kl = kabatiansky_levenshtein_bound(n)

        print(f" {n:3d} | {len(centers):6d} | {density:8.2e} | {mink:9.2e} | {kl:8.2e} | {app}")

    print()
    print("Вывод: при росте размерности packing density падает")
    print("       экспоненциально (проклятие размерности).")
    print("       Astra #1 даёт более точные границы для высоких n,")
    print("       что критично для оптимизации embedding-пространств.")
    print()

def generate_html_visualization(centers, filename="spherepack_visualization.html", min_dist=0.25):
    """Generate standalone HTML with Three.js visualization.

    Args:
        centers: numpy array of sphere centers
        filename: output HTML filename
        min_dist: minimum distance between centers (determines sphere radius)
    """

    centers_js = []
    for c in centers:
        centers_js.append(f"new THREE.Vector3({c[0]:.6f}, {c[1]:.6f}, {c[2]:.6f})")
    centers_js_str = ",\n            ".join(centers_js)

    radius = min_dist / 2.0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpherePack Embed — 3D Visualization</title>
    <style>
        body {{ margin: 0; overflow: hidden; background: #0a0a0a; font-family: 'Segoe UI', sans-serif; }}
        #info {{
            position: absolute; top: 10px; left: 10px; color: #00ff88;
            background: rgba(0,0,0,0.7); padding: 15px; border-radius: 8px;
            font-size: 14px; z-index: 10; max-width: 300px;
        }}
        #info h1 {{ margin: 0 0 8px 0; font-size: 16px; color: #fff; }}
        #info p {{ margin: 4px 0; }}
        #controls {{
            position: absolute; bottom: 10px; left: 10px; z-index: 10;
        }}
        button {{
            background: #00ff88; border: none; padding: 8px 16px;
            margin: 2px; border-radius: 4px; cursor: pointer; font-weight: bold;
        }}
        button:hover {{ background: #00cc6a; }}
    </style>
</head>
<body>
    <div id="info">
        <h1>SpherePack Embed</h1>
        <p>Based on Astra #1 — Sphere Packing</p>
        <p>Spheres: <span id="count">{len(centers)}</span></p>
        <p>Min dist: {min_dist:.3f} &bull; Radius: {radius:.4f}</p>
        <p>Drag to rotate &bull; Scroll to zoom</p>
    </div>
    <div id="controls">
        <button onclick="resetCamera()">Reset</button>
        <button onclick="toggleRotation()">Rotate</button>
        <button onclick="toggleWireframe()">Wireframe</button>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a0a);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 100);
        camera.position.set(1.5, 1.2, 1.5);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(2, 3, 2);
        scene.add(dirLight);

        const pointLight = new THREE.PointLight(0x00ff88, 0.5, 10);
        pointLight.position.set(0.5, 0.5, 0.5);
        scene.add(pointLight);

        const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
        const cubeEdges = new THREE.EdgesGeometry(cubeGeometry);
        const cubeLine = new THREE.LineSegments(cubeEdges, new THREE.LineBasicMaterial({{ color: 0x444444 }}));
        cubeLine.position.set(0.5, 0.5, 0.5);
        scene.add(cubeLine);

        const radius = {radius:.6f};
        const sphereGeometry = new THREE.SphereGeometry(radius, 32, 32);
        const sphereMaterial = new THREE.MeshPhongMaterial({{
            color: 0x00ff88,
            transparent: true,
            opacity: 0.7,
            shininess: 100,
            side: THREE.DoubleSide
        }});

        const centers = [
            {centers_js_str}
        ];

        let wireframeMode = false;
        const spheres = [];

        centers.forEach((center, i) => {{
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial.clone());
            sphere.position.copy(center);
            const hue = (center.x + center.y + center.z) / 3;
            sphere.material.color.setHSL(0.3 + hue * 0.2, 0.8, 0.5);
            scene.add(sphere);
            spheres.push(sphere);
        }});

        const ballVol = (4/3) * Math.PI * Math.pow(radius, 3);
        const totalVol = centers.length * ballVol;

        let autoRotate = false;
        function toggleRotation() {{ autoRotate = !autoRotate; }}
        function toggleWireframe() {{
            wireframeMode = !wireframeMode;
            spheres.forEach(s => {{ s.material.wireframe = wireframeMode; }});
        }}
        function resetCamera() {{
            camera.position.set(1.5, 1.2, 1.5);
            camera.lookAt(0.5, 0.5, 0.5);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            if (autoRotate) {{ scene.rotation.y += 0.005; }}
            controls.update();
            renderer.render(scene, camera);
        }}

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        animate();
    </script>
</body>
</html>"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

    return filename

def interactive_mode():
    print("--- Интерактивный режим ---")
    try:
        n = input("Размерность n (3 для визуализации, рекомендуется 3-64): ").strip()
        n = int(n) if n else 3

        target = input("Целевое число шаров (рекомендуется 20-200): ").strip()
        target = int(target) if target else 50

        min_dist = input("Минимальное расстояние (рекомендуется 0.15-0.35): ").strip()
        min_dist = float(min_dist) if min_dist else 0.25

        seed_in = input("Seed (Enter для случайного): ").strip()
        seed = int(seed_in) if seed_in else 42

    except ValueError:
        print("Ошибка ввода. Использую значения по умолчанию.")
        n, target, min_dist, seed = 3, 50, 0.25, 42

    print()
    print_header()
    print_bounds_table()

    if n == 3:
        centers = greedy_packing(n, target, min_dist, max_attempts=50000, seed=seed, clip_to_bounds=True)
        r = min_dist / 2.0
        density = packing_density(centers, n, r)
        print(f"\n--- Демо: жадная упаковка шаров в {n}D (визуализация) ---")
        print(f"Параметры: размерность n={n}, min_dist={min_dist}, seed={seed}")
        print(f"Упаковано шаров: {len(centers)} / {target} (попыток: 50000)")
        print(f"Packing density: {density:.6f}")
        print(f"Kissing number (оценка): {kissing_number_estimate(n)}")
        actual, mink_max, kl_max = embedding_capacity(n, min_dist, density)
        print(f"Ёмкость embedding-пространства:")
        print(f"  Фактическая:    {actual}")
        print(f"  Минковский max: {mink_max}")
        print(f"  KL max:         {kl_max}")
        print()
    else:
        centers, density = print_packing_demo(n, target, min_dist, seed)
    print_embedding_comparison()

    if n == 3 and len(centers) > 0:
        fname = generate_html_visualization(centers, min_dist=min_dist)
        print(f"Рабочая HTML-визуализация сохранена: {fname}")
        print("Откройте в браузере (экспериментальный файл, перезаписывается при запуске):")
        print(f"  termux-open {fname}")
        print()

def main():
    parser = argparse.ArgumentParser(description='SpherePack Embed demo')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--visualize', '-v', action='store_true', help='Generate HTML visualization')
    parser.add_argument('--n', type=int, default=3, help='Dimension (default: 3)')
    parser.add_argument('--target', type=int, default=50, help='Target sphere count (default: 50)')
    parser.add_argument('--min-dist', type=float, default=0.25, help='Minimum distance (default: 0.25)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    print_header()
    print_bounds_table()

    # For 3D visualization, use clip_to_bounds so spheres stay inside the cube
    if args.visualize or args.n == 3:
        centers = greedy_packing(args.n, args.target, args.min_dist, max_attempts=50000, seed=args.seed, clip_to_bounds=True)
        r = args.min_dist / 2.0
        density = packing_density(centers, args.n, r)
        print(f"\n--- Демо: жадная упаковка шаров в {args.n}D (визуализация) ---")
        print(f"Параметры: размерность n={args.n}, min_dist={args.min_dist}, seed={args.seed}")
        print(f"Упаковано шаров: {len(centers)} / {args.target} (попыток: 50000)")
        print(f"Packing density: {density:.6f}")
        print(f"Kissing number (оценка): {kissing_number_estimate(args.n)}")
        actual, mink_max, kl_max = embedding_capacity(args.n, args.min_dist, density)
        print(f"Ёмкость embedding-пространства:")
        print(f"  Фактическая:    {actual}")
        print(f"  Минковский max: {mink_max}")
        print(f"  KL max:         {kl_max}")
        print()
    else:
        centers, density = print_packing_demo(args.n, args.target, args.min_dist, args.seed)
    print_embedding_comparison()

    if args.visualize or args.n == 3:
        if len(centers) > 0:
            fname = generate_html_visualization(centers, min_dist=min_dist)
            print(f"Рабочая HTML-визуализация сохранена: {fname}")
            print("Откройте в браузере (экспериментальный файл, перезаписывается при запуске):")
            print(f"  termux-open {fname}")
            print()

if __name__ == '__main__':
    main()
