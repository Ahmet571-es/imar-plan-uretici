"""
Parsel Geometrisi İşlemleri — Parsel oluşturma, görselleştirme, TKGM entegrasyonu.
"""

import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from shapely.geometry import Polygon

from utils.geometry_helpers import (
    kenarlar_ve_acilardan_polygon,
    dikdortgen_polygon,
    koordinatlardan_polygon,
    polygon_alan,
    polygon_cevre,
    kenar_uzunluklari,
    kose_acilari,
    polygon_to_coords_list,
    otomatik_acilar_hesapla,
)


class Parsel:
    """Parsel nesnesi — geometri, alan, kenar ve açı bilgilerini tutar."""

    def __init__(self, polygon: Polygon, yon: str = "kuzey"):
        self.polygon = polygon
        self.yon = yon  # Kuzey yönü bilgisi
        self._kenarlar = None
        self._acilar = None

    @classmethod
    def from_kenarlar_acilar(cls, kenarlar: list[float], acilar: list[float] | None = None, yon: str = "kuzey"):
        """Kenar uzunlukları ve açılardan Parsel oluştur."""
        if acilar is None:
            acilar = otomatik_acilar_hesapla(kenarlar)
        poly = kenarlar_ve_acilardan_polygon(kenarlar, acilar)
        return cls(poly, yon=yon)

    @classmethod
    def from_dikdortgen(cls, en: float, boy: float, yon: str = "kuzey"):
        """Dikdörtgen parsel oluştur."""
        poly = dikdortgen_polygon(en, boy)
        return cls(poly, yon=yon)

    @classmethod
    def from_koordinatlar(cls, coords: list[tuple[float, float]], yon: str = "kuzey"):
        """Koordinatlardan Parsel oluştur."""
        poly = koordinatlardan_polygon(coords)
        return cls(poly, yon=yon)

    @property
    def alan(self) -> float:
        """Parsel alanı (m²)."""
        return polygon_alan(self.polygon)

    @property
    def cevre(self) -> float:
        """Parsel çevresi (metre)."""
        return polygon_cevre(self.polygon)

    @property
    def kenarlar(self) -> list[float]:
        """Kenar uzunlukları listesi."""
        if self._kenarlar is None:
            self._kenarlar = kenar_uzunluklari(self.polygon)
        return self._kenarlar

    @property
    def acilar(self) -> list[float]:
        """Köşe iç açıları listesi (derece)."""
        if self._acilar is None:
            self._acilar = kose_acilari(self.polygon)
        return self._acilar

    @property
    def kose_sayisi(self) -> int:
        """Köşe sayısı."""
        return len(list(self.polygon.exterior.coords)) - 1

    @property
    def koordinatlar(self) -> list[tuple[float, float]]:
        """Koordinat listesi."""
        return polygon_to_coords_list(self.polygon)

    @property
    def bounds(self):
        return self.polygon.bounds

    def ozet(self) -> dict:
        """Parsel özet bilgileri."""
        return {
            "alan_m2": round(self.alan, 2),
            "cevre_m": round(self.cevre, 2),
            "kose_sayisi": self.kose_sayisi,
            "kenarlar_m": [round(k, 2) for k in self.kenarlar],
            "acilar_derece": [round(a, 1) for a in self.acilar],
            "yon": self.yon,
        }

    def ciz(self, ax=None, cekme_polygonu: Polygon | None = None, figsize=(8, 8)) -> plt.Figure:
        """Parseli matplotlib ile çizer.

        Args:
            ax: Mevcut matplotlib axes (varsa).
            cekme_polygonu: Çekme sonrası yapılaşmaya uygun alan poligonu.
            figsize: Figür boyutu.

        Returns:
            matplotlib Figure nesnesi.
        """
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=figsize)
        else:
            fig = ax.figure

        coords = self.koordinatlar

        # Parsel çizimi
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        ax.fill(xs, ys, alpha=0.15, color="#1E88E5", label="Parsel")
        ax.plot(xs, ys, color="#1E88E5", linewidth=2.0)

        # Çekme sonrası alan
        if cekme_polygonu is not None and not cekme_polygonu.is_empty:
            cx = [c[0] for c in cekme_polygonu.exterior.coords]
            cy = [c[1] for c in cekme_polygonu.exterior.coords]
            ax.fill(cx, cy, alpha=0.25, color="#4CAF50", label="Yapılaşma Alanı")
            ax.plot(cx, cy, color="#4CAF50", linewidth=1.5, linestyle="--")

        # Kenar uzunluklarını yaz
        coords_nolast = coords[:-1]
        for i in range(len(coords_nolast)):
            p1 = np.array(coords_nolast[i])
            p2 = np.array(coords_nolast[(i + 1) % len(coords_nolast)])
            mid = (p1 + p2) / 2.0
            uzunluk = self.kenarlar[i]

            # Kenar normal yönünde biraz dışarı offset
            edge = p2 - p1
            normal = np.array([-edge[1], edge[0]])
            normal = normal / (np.linalg.norm(normal) + 1e-10)
            centroid = np.array([self.polygon.centroid.x, self.polygon.centroid.y])
            if np.dot(normal, centroid - mid) > 0:
                normal = -normal
            offset_pos = mid + normal * 1.2

            ax.annotate(
                f"{uzunluk:.1f}m",
                xy=offset_pos,
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="center",
                color="#333",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#ccc", alpha=0.8),
            )

        # Köşe açılarını yaz
        for i, aci in enumerate(self.acilar):
            x, y = coords_nolast[i]
            ax.annotate(
                f"{aci:.0f}°",
                xy=(x, y),
                fontsize=7,
                color="#E65100",
                ha="center",
                va="center",
                xytext=(5, 5),
                textcoords="offset points",
            )

        # Alan bilgisi
        cx, cy = self.polygon.centroid.x, self.polygon.centroid.y
        ax.text(
            cx, cy,
            f"{self.alan:.1f} m²",
            fontsize=12,
            fontweight="bold",
            ha="center",
            va="center",
            color="#1565C0",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#1565C0", alpha=0.9),
        )

        # Kuzey yönü oku
        minx, miny, maxx, maxy = self.polygon.bounds
        arrow_x = maxx + (maxx - minx) * 0.1
        arrow_y = maxy - (maxy - miny) * 0.1
        ax.annotate(
            "K",
            xy=(arrow_x, arrow_y),
            xytext=(arrow_x, arrow_y - (maxy - miny) * 0.15),
            fontsize=11,
            fontweight="bold",
            ha="center",
            arrowprops=dict(arrowstyle="->", color="red", lw=2),
            color="red",
        )

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("x (metre)")
        ax.set_ylabel("y (metre)")
        ax.set_title("Parsel Görünümü", fontsize=13, fontweight="bold")

        if cekme_polygonu is not None:
            ax.legend(loc="upper left", fontsize=9)

        fig.tight_layout()
        return fig
