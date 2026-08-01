#!/bin/bash
set -e

echo "SpherePack Embed — установка зависимостей для Termux"

pkg update -y
pkg install -y python

pip install numpy

echo ""
echo "Установка завершена!"
echo "Запустите демо: python demo.py"
echo "Или с визуализацией: python demo.py --visualize"
echo "HTML откроется через: termux-open spherepack_visualization.html"
