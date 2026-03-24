"""
Harita Görüntüleme — Folium ile OpenStreetMap, uydu katmanı ve çevre analizi.
"""

import logging

logger = logging.getLogger(__name__)


def create_parcel_map(
    latitude: float = 39.93,
    longitude: float = 32.86,
    parcel_coords_latlon: list[tuple[float, float]] | None = None,
    zoom_start: int = 17,
    show_satellite: bool = True,
    show_nearby: bool = True,
) -> "folium.Map | None":
    """Parsel konumunu harita üzerinde gösterir.

    Args:
        latitude: Parsel merkez enlemi.
        longitude: Parsel merkez boylamı.
        parcel_coords_latlon: Parsel köşe koordinatları [(lat, lon), ...].
        zoom_start: Başlangıç zoom seviyesi.
        show_satellite: Uydu görüntüsü katmanı.
        show_nearby: Çevre POI'leri göster.

    Returns:
        Folium Map nesnesi veya None.
    """
    try:
        import folium
        from folium.plugins import MeasureControl
    except ImportError:
        logger.warning("folium kurulu değil. pip install folium ile kurun.")
        return None

    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
    )

    # Uydu katmanı
    if show_satellite:
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Uydu Görüntüsü",
            overlay=False,
        ).add_to(m)

    # Parsel sınırı
    if parcel_coords_latlon and len(parcel_coords_latlon) >= 3:
        folium.Polygon(
            locations=parcel_coords_latlon,
            color="#FF5722",
            fill=True,
            fill_color="#FF5722",
            fill_opacity=0.2,
            weight=3,
            popup="Parsel Sınırı",
            tooltip="Proje Parseli",
        ).add_to(m)

    # Parsel merkez pin
    folium.Marker(
        location=[latitude, longitude],
        popup=f"Parsel Merkezi<br>Enlem: {latitude:.6f}<br>Boylam: {longitude:.6f}",
        tooltip="Parsel",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)

    # Çevre POI'leri
    if show_nearby:
        _add_nearby_pois(m, latitude, longitude)

    # Ölçüm aracı
    try:
        MeasureControl(position="topleft").add_to(m)
    except Exception:
        pass

    # Katman kontrolü
    folium.LayerControl().add_to(m)

    return m


def _add_nearby_pois(m, lat, lon):
    """Çevredeki önemli noktaları haritaya ekler (Overpass API)."""
    try:
        import requests

        # Overpass API — 500m yarıçapta POI'ler
        overpass_query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"school|hospital|mosque|pharmacy"](around:500,{lat},{lon});
          node["shop"~"supermarket|bakery"](around:500,{lat},{lon});
          node["leisure"~"park|playground"](around:300,{lat},{lon});
        );
        out body;
        """

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": overpass_query},
            timeout=15,
        )

        if response.status_code != 200:
            return

        data = response.json()
        elements = data.get("elements", [])

        icon_map = {
            "school": ("blue", "graduation-cap"),
            "hospital": ("green", "plus-square"),
            "mosque": ("darkgreen", "moon-o"),
            "pharmacy": ("lightgreen", "medkit"),
            "supermarket": ("orange", "shopping-cart"),
            "bakery": ("beige", "bread-slice"),
            "park": ("green", "tree"),
            "playground": ("lightblue", "child"),
        }

        import folium
        for elem in elements[:20]:  # Max 20 POI
            e_lat = elem.get("lat")
            e_lon = elem.get("lon")
            tags = elem.get("tags", {})
            name = tags.get("name", "")
            amenity = tags.get("amenity", tags.get("shop", tags.get("leisure", "")))

            if not e_lat or not e_lon:
                continue

            color, icon = icon_map.get(amenity, ("gray", "info"))

            folium.Marker(
                location=[e_lat, e_lon],
                popup=f"{name}<br>{amenity}",
                tooltip=name or amenity,
                icon=folium.Icon(color=color, icon=icon, prefix="fa"),
            ).add_to(m)

    except Exception as e:
        logger.debug(f"POI çekme hatası: {e}")


def create_shadow_analysis_map(
    latitude: float,
    longitude: float,
    building_height: float,
    parcel_coords_latlon: list[tuple[float, float]] | None = None,
):
    """Basit gölge analizi haritası oluşturur."""
    import math

    try:
        import folium
    except ImportError:
        return None

    m = create_parcel_map(latitude, longitude, parcel_coords_latlon)
    if m is None:
        return None

    # Kış gündönümü güneş açısı
    winter_angle = 90 - latitude - 23.45
    if winter_angle <= 0:
        winter_angle = 5

    # Gölge uzunluğu = bina yüksekliği / tan(güneş açısı)
    shadow_length = building_height / math.tan(math.radians(winter_angle))

    # Kuzey yönüne gölge (kış güneşi güneyden gelir)
    shadow_lat = latitude + (shadow_length / 111000)  # ~111km per degree

    folium.Circle(
        location=[shadow_lat, longitude],
        radius=shadow_length,
        color="#333",
        fill=True,
        fill_opacity=0.15,
        popup=f"Kış gölge uzunluğu: {shadow_length:.1f}m",
        tooltip="Kış Gölgesi (21 Aralık)",
    ).add_to(m)

    return m
