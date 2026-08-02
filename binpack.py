#!/usr/bin/env python3
"""
binpack.py — Optimal binary section placement using sphere packing analogy.
For kernel/ISO development: pack sections with alignment constraints,
minimizing padding (wasted space) between blocks.

Run: python binpack.py
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Section:
    name: str
    size: int          # bytes
    align: int         # alignment (must be power of 2)
    flags: str = "R"   # R=read, W=write, X=execute


def align_up(addr: int, alignment: int) -> int:
    """Align address up to nearest multiple of alignment."""
    return (addr + alignment - 1) & ~(alignment - 1)


def naive_place(sections: List[Section], base: int = 0x1000) -> List[Tuple[str, int, int]]:
    """Naive sequential placement with alignment."""
    addr = base
    result = []
    for sec in sections:
        addr = align_up(addr, sec.align)
        start = addr
        end = addr + sec.size
        result.append((sec.name, start, end))
        addr = end
    return result


def optimal_place(sections: List[Section], base: int = 0x1000) -> List[Tuple[str, int, int]]:
    """
    Optimized placement: sort by alignment (largest first) to minimize padding.
    Analogous to sphere packing: larger alignment = larger "exclusion zone".
    """
    sorted_secs = sorted(sections, key=lambda s: (-s.align, -s.size))
    addr = base
    result = []
    for sec in sorted_secs:
        addr = align_up(addr, sec.align)
        start = addr
        end = addr + sec.size
        result.append((sec.name, start, end))
        addr = end
    return result


def compute_padding(placement: List[Tuple[str, int, int]], base: int) -> int:
    """Total padding (wasted bytes) in placement."""
    if not placement:
        return 0
    total = placement[-1][2] - base
    used = sum(p[2] - p[1] for p in placement)
    return total - used


def print_layout(placement: List[Tuple[str, int, int]], base: int, title: str = "Layout"):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    print(f"{'Section':>12} | {'Start':>10} | {'End':>10} | {'Size':>10}")
    print("-" * 50)
    for name, start, end in placement:
        print(f"{name:>12} | 0x{start:08x} | 0x{end:08x} | {end-start:>10}")
    total = placement[-1][2] - base
    padding = compute_padding(placement, base)
    print("-" * 50)
    print(f"Total span: {total} bytes ({total//1024} KiB)")
    print(f"Padding:    {padding} bytes ({padding/total*100:.1f}%)")


def demo():
    """Demo with typical kernel/ELF section layout."""
    sections = [
        Section(".text",   size=0x28000, align=0x1000, flags="RX"),
        Section(".rodata", size=0x0C000, align=0x1000, flags="R"),
        Section(".data",   size=0x08000, align=0x1000, flags="RW"),
        Section(".bss",    size=0x14000, align=0x1000, flags="RW"),
        Section(".init",   size=0x00200, align=0x0100, flags="RX"),
        Section(".fini",   size=0x00200, align=0x0100, flags="RX"),
        Section(".symtab", size=0x05000, align=0x0008, flags="R"),
        Section(".strtab", size=0x03000, align=0x0008, flags="R"),
    ]

    base = 0x00100000  # 1 MiB

    naive = naive_place(sections, base)
    optimal = optimal_place(sections, base)

    print_layout(naive, base, "NAIVE: Original order")
    print_layout(optimal, base, "OPTIMAL: Sorted by alignment")

    pad_naive = compute_padding(naive, base)
    pad_opt = compute_padding(optimal, base)
    saved = pad_naive - pad_opt
    print(f"\nPadding saved: {saved} bytes ({saved/1024:.1f} KiB)")
    if pad_naive > 0:
        print(f"Relative: {saved/pad_naive*100:.1f}% less padding")
    else:
        print("Relative: 0.0% (no padding in naive layout)")


if __name__ == "__main__":
    demo()
