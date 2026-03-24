"""
TKGM API Entegrasyonu — Parsel sorgulama ve koordinat çekme.

İyileştirmeler:
- pyproj ile doğru WGS84→UTM koordinat dönüşümü
- API endpoint validasyonu
- Daha güvenilir hata yönetimi
"""

import math
import logging
import requests
from dataclasses import dataclass, field
from shapely.geometry import Polygon, shape

logger = logging.getLogger(__name__)

TKGM_CBS_BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/parsel"
TKGM_WFS_BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/iltce"
TIMEOUT = 15
MAX_RETRIES = 3

TKGM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://parselsorgu.tkgm.gov.tr/",
    "Origin": "https://parselsorgu.tkgm.gov.tr",
    "Connection": "keep-alive",
}


@dataclass
class TKGMParselSonuc:
    """TKGM sorgu sonucu."""
    basarili: bool = False
    il: str = ""
    ilce: str = ""
    mahalle: str = ""
    ada: str = ""
    parsel: str = ""
    alan: float = 0.0
    koordinatlar: list = field(default_factory=list)
    polygon: Polygon | None = None
    pafta: str = ""
    nitelik: str = ""
    hata: str = ""
    ham_veri: dict = field(default_factory=dict)
    utm_zone: int = 0
    epsg_code: str = ""


def parsel_sorgula(
    il: str = "",
    ilce: str = "",
    mahalle: str = "",
    ada: str = "",
    parsel: str = "",
) -> TKGMParselSonuc:
    """TKGM API üzerinden parsel bilgisi sorgular."""
    sonuc = TKGMParselSonuc(il=il, ilce=ilce, mahalle=mahalle,
                             ada=ada, parsel=parsel)

    # Yöntem 1: CBS API
    try:
        result = _query_cbs_api(il, ilce, mahalle, ada, parsel)
        if result:
            sonuc.basarili = True
            sonuc.alan = result.get("alan", 0)
            sonuc.pafta = result.get("pafta", "")
            sonuc.nitelik = result.get("nitelik", "")
            sonuc.ham_veri = result

            geom = result.get("geometry", result.get("geom", {}))
            if geom:
                coords = _extract_coordinates(geom)
                if coords:
                    sonuc.koordinatlar = coords
                    sonuc.polygon = _coords_to_polygon_pyproj(coords)
                    if sonuc.alan == 0 and sonuc.polygon:
                        sonuc.alan = sonuc.polygon.area

            logger.info(f"TKGM sorgu basarili: {ada}/{parsel} — "
                        f"{sonuc.alan:.1f} m2")
            return sonuc
    except Exception as e:
        logger.warning(f"CBS API hatasi: {e}")

    # Yöntem 2: WFS servisi
    try:
        result = _query_wfs(il, ilce, ada, parsel)
        if result:
            sonuc.basarili = True
            sonuc.ham_veri = result
            geom = result.get("geometry", {})
            if geom:
                coords = _extract_coordinates(geom)
                if coords:
                    sonuc.koordinatlar = coords
                    sonuc.polygon = _coords_to_polygon_pyproj(coords)
                    sonuc.alan = (sonuc.polygon.area
                                  if sonuc.polygon else 0)
            logger.info(f"WFS sorgu basarili: {ada}/{parsel}")
            return sonuc
    except Exception as e:
        logger.warning(f"WFS hatasi: {e}")

    sonuc.hata = (
        "TKGM API'ye erisilemedi. Olasi nedenler:\n"
        "- TKGM sunuculari gecici olarak yanit vermiyor\n"
        "- Streamlit Cloud sunucusu Turkiye disinda — TKGM cografi "
        "kisitlama uygulayabilir\n"
        "-> Manuel Giris sekmesinden parsel olculerini girebilirsiniz."
    )
    logger.error(f"TKGM erisilemedi: {il}/{ilce} {ada}/{parsel}")
    return sonuc


def _query_cbs_api(il, ilce, mahalle, ada, parsel) -> dict | None:
    """TKGM CBS API sorgusu."""
    url = f"{TKGM_CBS_BASE}/{il}/{ilce}/{mahalle}/{ada}/{parsel}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers=TKGM_HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                elif isinstance(data, dict) and data.get("features"):
                    features = data["features"]
                    if features:
                        return features[0].get("properties", features[0])
                return data if isinstance(data, dict) else None
            elif resp.status_code == 404:
                logger.debug(f"Parsel bulunamadi: {ada}/{parsel}")
                return None
            else:
                logger.debug(f"TKGM CBS yanit: {resp.status_code}")
        except requests.Timeout:
            logger.debug(f"TKGM CBS timeout (deneme {attempt + 1}/"
                         f"{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.debug(f"TKGM CBS istek hatasi: {e}")

    return None


def _query_wfs(il, ilce, ada, parsel) -> dict | None:
    """TKGM WFS sorgusu (GeoJSON)."""
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": "parsel",
        "outputFormat": "application/json",
        "CQL_FILTER": f"ada='{ada}' AND parsel='{parsel}'",
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(TKGM_WFS_BASE, params=params,
                                timeout=TIMEOUT, headers=TKGM_HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    props = feat.get("properties", {})
                    props["geometry"] = feat.get("geometry", {})
                    return props
        except Exception as e:
            logger.debug(f"WFS hatasi (deneme {attempt + 1}): {e}")

    return None


def _extract_coordinates(geom: dict) -> list[tuple[float, float]]:
    """GeoJSON geometry'den koordinatları çıkarır."""
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if not coords:
        return []

    if geom_type == "Polygon":
        ring = coords[0] if coords else []
        return [(c[0], c[1]) for c in ring]
    elif geom_type == "MultiPolygon":
        biggest = max(coords, key=lambda p: len(p[0]) if p else 0)
        ring = biggest[0] if biggest else []
        return [(c[0], c[1]) for c in ring]
    elif geom_type == "Point":
        return [(coords[0], coords[1])]
    else:
        if isinstance(coords[0], (list, tuple)) and len(coords[0]) >= 2:
            return [(c[0], c[1]) for c in coords]
        return []


def _get_utm_zone(longitude: float) -> int:
    """Boylama göre UTM zone hesaplar."""
    return int((longitude + 180) / 6) + 1


def _get_utm_epsg(latitude: float, longitude: float) -> int:
    """WGS84 koordinatlardan UTM EPSG kodu döndürür."""
    zone = _get_utm_zone(longitude)
    if latitude >= 0:
        return 32600 + zone  # Kuzey yarımküre
    else:
        return 32700 + zone  # Güney yarımküre


def _coords_to_polygon_pyproj(
    coords: list[tuple[float, float]],
) -> Polygon | None:
    """Koordinatlardan Shapely Polygon oluşturur.

    pyproj varsa doğru UTM dönüşümü yapar, yoksa yaklaşık hesap.
    """
    if len(coords) < 3:
        return None

    # Koordinatlar derece cinsinde mi kontrol et
    if not all(abs(c[0]) < 180 and abs(c[1]) < 90 for c in coords[:3]):
        # Zaten metre cinsinde
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly

    # WGS84 → UTM dönüşümü
    ref_lat = sum(c[1] for c in coords) / len(coords)
    ref_lon = sum(c[0] for c in coords) / len(coords)

    try:
        from pyproj import Transformer
        epsg_utm = _get_utm_epsg(ref_lat, ref_lon)
        transformer = Transformer.from_crs(
            "EPSG:4326", f"EPSG:{epsg_utm}", always_xy=True
        )
        meter_coords = []
        for lon, lat in coords:
            x, y = transformer.transform(lon, lat)
            meter_coords.append((x, y))
        logger.info(f"pyproj UTM donusumu: EPSG:{epsg_utm}")
    except ImportError:
        logger.warning("pyproj kurulu degil, yaklasik hesap kullaniliyor")
        meter_coords = []
        for lon, lat in coords:
            x = (lon - ref_lon) * 111320 * math.cos(math.radians(ref_lat))
            y = (lat - ref_lat) * 110540
            meter_coords.append((x, y))

    poly = Polygon(meter_coords)
    if not poly.is_valid:
        poly = poly.buffer(0)

    return poly


def test_tkgm_connection() -> dict:
    """TKGM API bağlantı testi."""
    results = {
        "cbs_api": False,
        "wfs_api": False,
        "details": [],
    }

    # CBS API test
    try:
        resp = requests.get(
            f"{TKGM_CBS_BASE}/06/01/01/100/1",
            timeout=10, headers=TKGM_HEADERS,
        )
        results["cbs_api"] = resp.status_code in (200, 404)
        results["details"].append(
            f"CBS API: HTTP {resp.status_code}")
    except Exception as e:
        results["details"].append(f"CBS API hata: {e}")

    # WFS API test
    try:
        resp = requests.get(
            TKGM_WFS_BASE,
            params={"service": "WFS", "request": "GetCapabilities"},
            timeout=10, headers=TKGM_HEADERS,
        )
        results["wfs_api"] = resp.status_code == 200
        results["details"].append(
            f"WFS API: HTTP {resp.status_code}")
    except Exception as e:
        results["details"].append(f"WFS API hata: {e}")

    return results


def get_il_ilce_listesi() -> dict:
    """İl ve ilçe listesini döndürür (statik)."""
    return {
        "Ankara": ["Cankaya", "Kecioren", "Yenimahalle", "Etimesgut",
                    "Mamak", "Sincan", "Pursaklar", "Golbasi",
                    "Altindag", "Polatli"],
        "Istanbul": ["Kadikoy", "Besiktas", "Bakirkoy", "Uskudar",
                      "Kartal", "Maltepe", "Atasehir", "Beylikduzu",
                      "Basaksehir", "Cekmekoy"],
        "Izmir": ["Konak", "Bornova", "Karsiyaka", "Buca", "Bayrakli",
                   "Cigli", "Gaziemir", "Narlidere", "Balcova"],
        "Kutahya": ["Merkez", "Tavsanli", "Simav", "Emet", "Gediz",
                     "Domanic"],
        "Antalya": ["Muratpasa", "Konyaalti", "Kepez", "Alanya",
                     "Manavgat", "Serik"],
        "Bursa": ["Osmangazi", "Nilufer", "Yildirim", "Mudanya",
                   "Gemlik", "Inegol"],
        "Konya": ["Selcuklu", "Meram", "Karatay", "Eregli", "Aksehir"],
        "Gaziantep": ["Sahinbey", "Sehitkamil", "Oguzeli", "Nizip"],
        "Trabzon": ["Ortahisar", "Akcaabat", "Yomra", "Arakli", "Of"],
        "Eskisehir": ["Odunpazari", "Tepebasi", "Sivrihisar"],
        "Kayseri": ["Melikgazi", "Kocasinan", "Talas", "Incesu"],
        "Samsun": ["Ilkadim", "Atakum", "Canik", "Tekkekoy"],
        "Diyarbakir": ["Baglar", "Kayapinar", "Yenisehir", "Sur"],
    }
