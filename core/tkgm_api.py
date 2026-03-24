"""
TKGM API Entegrasyonu — Parsel sorgulama ve koordinat çekme.
cbsapi.tkgm.gov.tr veya parselsorgu.tkgm.gov.tr üzerinden sorgu yapar.
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

# TKGM Türkiye dışından erişimi engelleyebilir.
# Gerçek tarayıcı gibi davranmak için detaylı header'lar kullanıyoruz.
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
    koordinatlar: list = field(default_factory=list)  # [(lon, lat), ...]
    polygon: Polygon | None = None
    pafta: str = ""
    nitelik: str = ""
    hata: str = ""
    ham_veri: dict = field(default_factory=dict)


def parsel_sorgula(
    il: str = "",
    ilce: str = "",
    mahalle: str = "",
    ada: str = "",
    parsel: str = "",
) -> TKGMParselSonuc:
    """TKGM API üzerinden parsel bilgisi sorgular.

    Birden fazla endpoint dener, başarısız olursa hata döner.
    """
    sonuc = TKGMParselSonuc(il=il, ilce=ilce, mahalle=mahalle, ada=ada, parsel=parsel)

    # Yöntem 1: CBS API — koordinat bazlı parsel sorgu
    try:
        result = _query_cbs_api(il, ilce, mahalle, ada, parsel)
        if result:
            sonuc.basarili = True
            sonuc.alan = result.get("alan", 0)
            sonuc.pafta = result.get("pafta", "")
            sonuc.nitelik = result.get("nitelik", "")
            sonuc.ham_veri = result

            # Koordinatları çıkar
            geom = result.get("geometry", result.get("geom", {}))
            if geom:
                coords = _extract_coordinates(geom)
                if coords:
                    sonuc.koordinatlar = coords
                    sonuc.polygon = _coords_to_polygon(coords)
                    if sonuc.alan == 0 and sonuc.polygon:
                        sonuc.alan = sonuc.polygon.area

            logger.info(f"TKGM sorgu başarılı: {ada}/{parsel} — {sonuc.alan:.1f} m²")
            return sonuc
    except Exception as e:
        logger.warning(f"CBS API hatası: {e}")

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
                    sonuc.polygon = _coords_to_polygon(coords)
                    sonuc.alan = sonuc.polygon.area if sonuc.polygon else 0
            logger.info(f"WFS sorgu başarılı: {ada}/{parsel}")
            return sonuc
    except Exception as e:
        logger.warning(f"WFS hatası: {e}")

    sonuc.hata = (
        "TKGM API'ye erişilemedi. Olası nedenler:\n"
        "• TKGM sunucuları geçici olarak yanıt vermiyor\n"
        "• Streamlit Cloud sunucusu Türkiye dışında — TKGM coğrafi kısıtlama uygulayabilir\n"
        "→ Manuel Giriş sekmesinden parsel ölçülerini girebilirsiniz."
    )
    logger.error(f"TKGM erişilemedi: {il}/{ilce} {ada}/{parsel}")
    return sonuc


def _query_cbs_api(il, ilce, mahalle, ada, parsel) -> dict | None:
    """TKGM CBS API sorgusu."""
    # Endpoint 1: Doğrudan ada/parsel sorgusu
    url = f"{TKGM_CBS_BASE}/{il}/{ilce}/{mahalle}/{ada}/{parsel}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                url,
                timeout=TIMEOUT,
                headers=TKGM_HEADERS,
            )
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
                logger.debug(f"Parsel bulunamadı: {ada}/{parsel}")
                return None
            else:
                logger.debug(f"TKGM CBS yanıt: {resp.status_code}")
        except requests.Timeout:
            logger.debug(f"TKGM CBS timeout (deneme {attempt+1}/{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.debug(f"TKGM CBS istek hatası: {e}")

    return None


def _query_wfs(il, ilce, ada, parsel) -> dict | None:
    """TKGM WFS sorgusu (GeoJSON)."""
    # WFS GetFeature sorgusu
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
            resp = requests.get(
                TKGM_WFS_BASE,
                params=params,
                timeout=TIMEOUT,
                headers=TKGM_HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    props = feat.get("properties", {})
                    props["geometry"] = feat.get("geometry", {})
                    return props
        except Exception as e:
            logger.debug(f"WFS hatası (deneme {attempt+1}): {e}")

    return None


def _extract_coordinates(geom: dict) -> list[tuple[float, float]]:
    """GeoJSON geometry'den koordinatları çıkarır."""
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if not coords:
        return []

    if geom_type == "Polygon":
        # İlk ring (dış sınır)
        ring = coords[0] if coords else []
        return [(c[0], c[1]) for c in ring]
    elif geom_type == "MultiPolygon":
        # En büyük poligonu al
        biggest = max(coords, key=lambda p: len(p[0]) if p else 0)
        ring = biggest[0] if biggest else []
        return [(c[0], c[1]) for c in ring]
    elif geom_type == "Point":
        return [(coords[0], coords[1])]
    else:
        # Düz koordinat listesi
        if isinstance(coords[0], (list, tuple)) and len(coords[0]) >= 2:
            return [(c[0], c[1]) for c in coords]
        return []


def _coords_to_polygon(coords: list[tuple[float, float]]) -> Polygon | None:
    """Koordinatlardan Shapely Polygon oluşturur.

    TKGM genellikle EPSG:4326 (WGS84) döner — derece cinsinden.
    Metre cinsinden alan için UTM'e dönüştürmek gerekir.
    Basit yaklaşım: enlem/boylamdan metre tahmini.
    """
    if len(coords) < 3:
        return None

    # Eğer koordinatlar derece cinsindeyse (enlem/boylam)
    if all(abs(c[0]) < 180 and abs(c[1]) < 90 for c in coords[:3]):
        # WGS84 → yaklaşık metre dönüşümü
        ref_lat = sum(c[1] for c in coords) / len(coords)
        ref_lon = sum(c[0] for c in coords) / len(coords)

        meter_coords = []
        for lon, lat in coords:
            x = (lon - ref_lon) * 111320 * math.cos(math.radians(ref_lat))
            y = (lat - ref_lat) * 110540
            meter_coords.append((x, y))

        poly = Polygon(meter_coords)
    else:
        # Zaten metre cinsinde (EPSG:3857 vb.)
        poly = Polygon(coords)

    if not poly.is_valid:
        poly = poly.buffer(0)

    return poly


def get_il_ilce_listesi() -> dict:
    """İl ve ilçe listesini döndürür (statik)."""
    return {
        "Ankara": ["Çankaya", "Keçiören", "Yenimahalle", "Etimesgut", "Mamak", "Sincan", "Pursaklar", "Gölbaşı", "Altındağ", "Polatlı"],
        "İstanbul": ["Kadıköy", "Beşiktaş", "Bakırköy", "Üsküdar", "Kartal", "Maltepe", "Ataşehir", "Beylikdüzü", "Başakşehir", "Çekmeköy"],
        "İzmir": ["Konak", "Bornova", "Karşıyaka", "Buca", "Bayraklı", "Çiğli", "Gaziemir", "Narlıdere", "Balçova"],
        "Kütahya": ["Merkez", "Tavşanlı", "Simav", "Emet", "Gediz", "Domaniç"],
        "Antalya": ["Muratpaşa", "Konyaaltı", "Kepez", "Alanya", "Manavgat", "Serik"],
        "Bursa": ["Osmangazi", "Nilüfer", "Yıldırım", "Mudanya", "Gemlik", "İnegöl"],
        "Konya": ["Selçuklu", "Meram", "Karatay", "Ereğli", "Akşehir"],
        "Gaziantep": ["Şahinbey", "Şehitkamil", "Oğuzeli", "Nizip"],
        "Trabzon": ["Ortahisar", "Akçaabat", "Yomra", "Araklı", "Of"],
        "Eskişehir": ["Odunpazarı", "Tepebaşı", "Sivrihisar"],
        "Kayseri": ["Melikgazi", "Kocasinan", "Talas", "İncesu"],
        "Samsun": ["İlkadım", "Atakum", "Canik", "Tekkeköy"],
        "Diyarbakır": ["Bağlar", "Kayapınar", "Yenişehir", "Sur"],
    }
