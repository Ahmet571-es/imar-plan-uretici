"""
Geometri Yardımcı Fonksiyonları — Parsel oluşturma, çekme hesapları, alan işlemleri.
"""

import math
import numpy as np
from shapely.geometry import Polygon, MultiPolygon


def kenarlar_ve_acilardan_polygon(kenarlar: list[float], acilar: list[float]) -> Polygon:
    """Kenar uzunlukları ve iç açılardan (derece) parsel poligonu oluşturur.

    Koordinatları (0,0) başlangıçlı olarak hesaplar.
    İlk kenar pozitif x yönünde başlar.

    Args:
        kenarlar: Kenar uzunlukları listesi (metre).
        acilar: İç açılar listesi (derece). len(acilar) == len(kenarlar).

    Returns:
        Shapely Polygon nesnesi.
    """
    n = len(kenarlar)
    if n < 3:
        raise ValueError("En az 3 kenar gereklidir.")
    if len(acilar) != n:
        raise ValueError("Kenar ve açı sayıları eşit olmalıdır.")

    coords = [(0.0, 0.0)]
    # İlk kenar yönü: pozitif x (0 derece)
    direction = 0.0  # radyan

    for i in range(n - 1):
        dx = kenarlar[i] * math.cos(direction)
        dy = kenarlar[i] * math.sin(direction)
        x_new = coords[-1][0] + dx
        y_new = coords[-1][1] + dy
        coords.append((x_new, y_new))
        # Dış açı = 180 - iç açı
        dis_aci = 180.0 - acilar[(i + 1) % n]
        direction += math.radians(dis_aci)

    # Son noktayı ilk noktaya eşitle (kapatma)
    coords.append(coords[0])

    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def dikdortgen_polygon(en: float, boy: float) -> Polygon:
    """Basit dikdörtgen parsel oluşturur."""
    return Polygon([(0, 0), (en, 0), (en, boy), (0, boy), (0, 0)])


def koordinatlardan_polygon(coords: list[tuple[float, float]]) -> Polygon:
    """Verilen koordinat listesinden Polygon oluşturur."""
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def polygon_alan(poly: Polygon) -> float:
    """Poligon alanını döndürür (m²)."""
    return poly.area


def polygon_cevre(poly: Polygon) -> float:
    """Poligon çevre uzunluğunu döndürür (metre)."""
    return poly.length


def kenar_uzunluklari(poly: Polygon) -> list[float]:
    """Poligonun kenar uzunluklarını döndürür."""
    coords = list(poly.exterior.coords)
    uzunluklar = []
    for i in range(len(coords) - 1):
        dx = coords[i + 1][0] - coords[i][0]
        dy = coords[i + 1][1] - coords[i][1]
        uzunluklar.append(math.sqrt(dx**2 + dy**2))
    return uzunluklar


def kose_acilari(poly: Polygon) -> list[float]:
    """Poligonun köşe iç açılarını derece olarak döndürür."""
    coords = list(poly.exterior.coords)[:-1]  # son = ilk, çıkar
    n = len(coords)
    acilar = []
    for i in range(n):
        p0 = np.array(coords[(i - 1) % n])
        p1 = np.array(coords[i])
        p2 = np.array(coords[(i + 1) % n])
        v1 = p0 - p1
        v2 = p2 - p1
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = math.degrees(math.acos(cos_angle))
        acilar.append(round(angle, 1))
    return acilar


def cekme_mesafesi_uygula(
    parsel: Polygon,
    on_bahce: float,
    yan_bahce: float,
    arka_bahce: float,
    yon_bilgisi: str = "kuzey",
) -> Polygon:
    """Parsel poligonundan cepheye göre farklı çekme mesafelerini uygular.

    Basitleştirilmiş yaklaşım:
    - En uzun kenar = ön cephe (yol cephesi)
    - En uzun kenarın karşısı = arka cephe
    - Diğerleri = yan cephe

    Daha gelişmiş versiyon: her kenarı ayrı ayrı offset edip intersection al.
    Şimdilik uniform buffer kullanıyoruz (en basit yaklaşım).
    """
    # Basit yaklaşım: tüm kenarlardan ortalama çekme
    # Daha doğru yaklaşım için her kenarı ayrı offset etmek gerekir
    # Ama çoğu durumda dikdörtgen parsellerde:
    min_cekme = min(on_bahce, yan_bahce, arka_bahce)

    # Gelişmiş yaklaşım: her kenarı ayrı offset et
    coords = list(parsel.exterior.coords)[:-1]
    n = len(coords)

    if n != 4:
        # Dörtgen olmayan parseller için uniform buffer
        avg_cekme = (on_bahce + 2 * yan_bahce + arka_bahce) / 4.0
        result = parsel.buffer(-avg_cekme)
        if result.is_empty:
            return parsel.buffer(-min_cekme)
        if isinstance(result, MultiPolygon):
            result = max(result.geoms, key=lambda g: g.area)
        return result

    # Dörtgen parseller için kenar bazlı çekme
    kenarlar = []
    for i in range(n):
        p1 = np.array(coords[i])
        p2 = np.array(coords[(i + 1) % n])
        uzunluk = np.linalg.norm(p2 - p1)
        kenarlar.append((i, uzunluk))

    # En uzun kenar = ön cephe
    kenarlar_sorted = sorted(kenarlar, key=lambda x: x[1], reverse=True)
    on_kenar_idx = kenarlar_sorted[0][0]
    arka_kenar_idx = (on_kenar_idx + 2) % n  # karşı kenar

    # Her kenar için offset mesafesi belirle
    cekme_dict = {}
    for i in range(n):
        if i == on_kenar_idx:
            cekme_dict[i] = on_bahce
        elif i == arka_kenar_idx:
            cekme_dict[i] = arka_bahce
        else:
            cekme_dict[i] = yan_bahce

    # Her kenarı içeri offset et
    offset_lines = []
    for i in range(n):
        p1 = np.array(coords[i], dtype=float)
        p2 = np.array(coords[(i + 1) % n], dtype=float)

        # Kenar vektörü ve normal vektörü
        edge = p2 - p1
        normal = np.array([-edge[1], edge[0]], dtype=float)
        normal = normal / (np.linalg.norm(normal) + 1e-10)

        # İçeri doğru offset
        mesafe = cekme_dict[i]
        # Poligon merkezine doğru olan yön
        centroid = np.array([parsel.centroid.x, parsel.centroid.y])
        mid = (p1 + p2) / 2.0
        to_center = centroid - mid
        if np.dot(normal, to_center) < 0:
            normal = -normal

        offset_p1 = p1 + normal * mesafe
        offset_p2 = p2 + normal * mesafe
        offset_lines.append((tuple(offset_p1), tuple(offset_p2)))

    # Offset çizgilerin kesişim noktalarından yeni poligon oluştur
    new_coords = []
    for i in range(n):
        line1 = offset_lines[i]
        line2 = offset_lines[(i + 1) % n]
        intersect = _line_intersection(line1[0], line1[1], line2[0], line2[1])
        if intersect is not None:
            new_coords.append(intersect)

    if len(new_coords) >= 3:
        new_coords.append(new_coords[0])
        result = Polygon(new_coords)
        if result.is_valid and result.area > 0:
            return result

    # Fallback: uniform buffer
    result = parsel.buffer(-min_cekme)
    if result.is_empty:
        return parsel
    if isinstance(result, MultiPolygon):
        result = max(result.geoms, key=lambda g: g.area)
    return result


def _line_intersection(p1, p2, p3, p4):
    """İki doğru parçasının (sonsuz) kesişim noktasını bulur."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    return (x, y)


def polygon_bounds_boyutlar(poly: Polygon) -> tuple[float, float]:
    """Poligonun bounding box genişlik ve yüksekliğini döndürür."""
    minx, miny, maxx, maxy = poly.bounds
    return (maxx - minx, maxy - miny)


def polygon_to_coords_list(poly: Polygon) -> list[tuple[float, float]]:
    """Polygon koordinatlarını liste olarak döndürür."""
    return list(poly.exterior.coords)


def otomatik_acilar_hesapla(kenarlar: list[float]) -> list[float]:
    """Düzenli polygon için iç açıları hesaplar.

    NOT: Bu sadece düzgün (convex) poligonlar için geçerli bir yaklaşım.
    Düzensiz poligonlar için gerçek açılar gerekir.
    """
    n = len(kenarlar)
    # Düzgün poligon iç açısı = (n-2) * 180 / n
    aci = (n - 2) * 180.0 / n
    return [aci] * n
