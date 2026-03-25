"""
Plotly 3D Kamera → Prompt Açı Mapping.

Plotly scene camera koordinatlarını (eye.x, eye.y, eye.z) doğal dil
kamera açısı tanımlamasına dönüştürür. Grok Imagine prompt'larında kullanılır.

Plotly kamera sistemi:
- eye: kameranın 3D konumu (x, y, z)
- x pozitif = sağ (doğu), y pozitif = yukarı (kuzey), z pozitif = yükseklik
- center: kameranın baktığı nokta (genellikle 0,0,0)
- up: yukarı vektörü (genellikle z ekseni)
"""

import math
import logging

logger = logging.getLogger(__name__)

# ── 6 standart mimari kamera açısı ──
PRESET_CAMERAS = {
    "front_street": {
        "isim": "Ön Cephe (Sokak Seviyesi)",
        "eye": {"x": 0.0, "y": -2.5, "z": 0.3},
        "prompt": "Street level front facade view, eye-level perspective showing the main entrance and full front elevation, pedestrian viewpoint from across the street",
        "aspect_ratio": "16:9",
    },
    "corner_elevated": {
        "isim": "Köşe Perspektif (Yükseltilmiş)",
        "eye": {"x": 1.8, "y": -1.8, "z": 1.2},
        "prompt": "Elevated 30° corner perspective from southeast, showing two facades simultaneously, classic architectural photography angle, three-quarter view",
        "aspect_ratio": "16:9",
    },
    "side_street": {
        "isim": "Yan Cephe (Sokak Seviyesi)",
        "eye": {"x": 2.5, "y": 0.0, "z": 0.3},
        "prompt": "Street level side facade view from east, showing the full side elevation with depth perspective, balconies and windows clearly visible",
        "aspect_ratio": "16:9",
    },
    "aerial_45": {
        "isim": "Kuşbakışı 45°",
        "eye": {"x": 1.5, "y": -1.5, "z": 2.5},
        "prompt": "Aerial bird's eye view at 45 degrees from southeast corner, showing roof, all facades, surrounding landscape, parking area and garden layout",
        "aspect_ratio": "3:2",
    },
    "rear_garden": {
        "isim": "Arka Bahçe Görünümü",
        "eye": {"x": 0.0, "y": 2.5, "z": 0.5},
        "prompt": "Rear garden view showing the back facade, balconies, garden area with landscaping, peaceful residential atmosphere, slightly elevated perspective",
        "aspect_ratio": "16:9",
    },
    "night_corner": {
        "isim": "Gece Köşe Görünümü",
        "eye": {"x": 1.5, "y": -2.0, "z": 0.6},
        "prompt": "Night time corner perspective, warm interior lights glowing through windows, exterior architectural lighting, ambient blue hour sky transitioning to night, dramatic contrast between warm building lights and cool sky",
        "aspect_ratio": "16:9",
        "aydinlatma_override": "Night with interior lights glowing, exterior uplighting on facade",
    },
}


def plotly_camera_to_prompt(eye_x: float, eye_y: float, eye_z: float) -> str:
    """Plotly kamera eye koordinatlarını doğal dil prompt açısına çevirir.

    Args:
        eye_x: Kamera X konumu.
        eye_y: Kamera Y konumu.
        eye_z: Kamera Z konumu (yükseklik).

    Returns:
        Kamera açısı prompt tanımlaması.
    """
    # Yatay açı (azimut): atan2(x, -y) — Plotly'de -y ön cephe
    azimut_rad = math.atan2(eye_x, -eye_y)
    azimut_deg = math.degrees(azimut_rad) % 360

    # Dikey açı (elevasyon): z'nin yatay düzleme göre açısı
    horizontal_dist = math.sqrt(eye_x ** 2 + eye_y ** 2)
    if horizontal_dist > 0.01:
        elevation_rad = math.atan2(eye_z, horizontal_dist)
    else:
        elevation_rad = math.pi / 2 if eye_z > 0 else -math.pi / 2
    elevation_deg = math.degrees(elevation_rad)

    # Mesafe
    distance = math.sqrt(eye_x ** 2 + eye_y ** 2 + eye_z ** 2)

    # Yön tanımlaması
    direction = _azimut_to_direction(azimut_deg)

    # Yükseklik tanımlaması
    if elevation_deg < 5:
        height = "street level eye-height"
    elif elevation_deg < 20:
        height = f"slightly elevated {elevation_deg:.0f}°"
    elif elevation_deg < 40:
        height = f"elevated {elevation_deg:.0f}°"
    elif elevation_deg < 60:
        height = f"high angle {elevation_deg:.0f}°"
    else:
        height = "near top-down aerial"

    # Mesafe tanımlaması
    if distance < 1.5:
        dist_desc = "close-up detail"
    elif distance < 3.0:
        dist_desc = "medium distance"
    else:
        dist_desc = "wide establishing shot"

    prompt = (
        f"{height} perspective from {direction}, "
        f"{dist_desc}, showing building facades with accurate proportions"
    )

    logger.info(f"Kamera mapping: eye({eye_x:.1f}, {eye_y:.1f}, {eye_z:.1f}) → "
                f"azimut={azimut_deg:.0f}° elev={elevation_deg:.0f}° → {prompt}")

    return prompt


def _azimut_to_direction(deg: float) -> str:
    """Azimut derecesini yön tanımlamasına çevirir."""
    # 0° = kuzeyden bakış (ön cephe), saat yönünde
    directions = [
        (337.5, 360, "the north (front facade)"),
        (0, 22.5, "the north (front facade)"),
        (22.5, 67.5, "the northeast corner"),
        (67.5, 112.5, "the east (side facade)"),
        (112.5, 157.5, "the southeast corner"),
        (157.5, 202.5, "the south (rear facade)"),
        (202.5, 247.5, "the southwest corner"),
        (247.5, 292.5, "the west (side facade)"),
        (292.5, 337.5, "the northwest corner"),
    ]
    for low, high, desc in directions:
        if low <= deg < high:
            return desc
    return "the northeast corner"


def get_plotly_camera_eye(fig) -> dict:
    """Plotly figure'dan mevcut kamera eye koordinatlarını okur.

    Args:
        fig: Plotly Figure nesnesi.

    Returns:
        {"x": float, "y": float, "z": float} dict'i.
    """
    try:
        scene = fig.layout.scene
        if scene and scene.camera and scene.camera.eye:
            eye = scene.camera.eye
            return {
                "x": float(eye.x) if eye.x is not None else 1.5,
                "y": float(eye.y) if eye.y is not None else -1.5,
                "z": float(eye.z) if eye.z is not None else 1.0,
            }
    except Exception:
        pass
    # Varsayılan Plotly kamera
    return {"x": 1.5, "y": -1.5, "z": 1.0}


def set_plotly_camera(fig, eye: dict):
    """Plotly figure'ın kamera açısını ayarlar.

    Args:
        fig: Plotly Figure nesnesi.
        eye: {"x": float, "y": float, "z": float} kamera konumu.

    Returns:
        Güncellenmış Plotly Figure.
    """
    fig.update_layout(
        scene_camera=dict(
            eye=dict(x=eye["x"], y=eye["y"], z=eye["z"]),
            up=dict(x=0, y=0, z=1),
        )
    )
    return fig
