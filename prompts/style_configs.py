"""
Mimari stil konfigürasyonları — Grok Imagine prompt parametreleri.
4 farklı mimari stil için detaylı tanımlamalar.
"""

STYLE_VARIANTS = {
    "modern_minimalist": {
        "isim": "Modern Minimalist",
        "mimari_stil": (
            "Modern Minimalist — clean geometric lines, flat roof, "
            "floor-to-ceiling windows, white and gray color palette with wood accents"
        ),
        "cephe_malzemesi": (
            "White stucco walls, anthracite aluminum window frames, "
            "wooden cladding panels, glass balcony railings"
        ),
        "ic_mekan_stili": (
            "Minimalist modern interior, clean lines, neutral tones, "
            "natural materials, open-plan living"
        ),
        "renk_paleti": "White, light gray, warm wood tones, matte black accents",
    },
    "neo_osmanli": {
        "isim": "Neo-Osmanlı",
        "mimari_stil": (
            "Neo-Ottoman Contemporary — traditional Ottoman architectural elements "
            "reinterpreted with modern materials, pointed arches, ornamental patterns"
        ),
        "cephe_malzemesi": (
            "Natural stone facade, ornamental iron balcony railings, "
            "arched window frames, terracotta roof tiles, geometric Islamic patterns"
        ),
        "ic_mekan_stili": (
            "Ottoman-inspired interior, rich textures, ornate details, "
            "warm colors, traditional Turkish motifs with modern comfort"
        ),
        "renk_paleti": "Warm terracotta, deep blue, gold accents, natural stone tones",
    },
    "akdeniz": {
        "isim": "Akdeniz",
        "mimari_stil": (
            "Mediterranean Turkish — warm earth tones, terracotta elements, "
            "natural stone, lush balcony gardens"
        ),
        "cephe_malzemesi": (
            "Cream/beige stucco, terracotta tile roof, wrought iron railings, "
            "natural stone ground floor, wooden shutters"
        ),
        "ic_mekan_stili": (
            "Mediterranean warmth, natural materials, terracotta and stone, "
            "arched doorways, rustic elegance"
        ),
        "renk_paleti": "Cream, terracotta, olive green, sky blue, warm brown",
    },
    "cagdas_turk": {
        "isim": "Çağdaş Türk",
        "mimari_stil": (
            "Contemporary Turkish Urban — bold geometric facade, mixed materials, "
            "dynamic balcony configurations, sustainable design elements"
        ),
        "cephe_malzemesi": (
            "Composite panels, exposed concrete elements, perforated metal screens, "
            "green facade sections, energy-efficient glazing"
        ),
        "ic_mekan_stili": (
            "Contemporary Turkish design, bold colors, mixed textures, "
            "sustainable materials, innovative space solutions"
        ),
        "renk_paleti": "Charcoal, forest green, warm copper, concrete gray, natural wood",
    },
}

CAMERA_ANGLES = [
    "Street level front facade",
    "Street level corner view 30°",
    "Elevated 15° front perspective",
    "Elevated 30° corner perspective",
    "Bird's eye 45°",
    "Aerial top-down",
]

LIGHTING_OPTIONS = [
    "Sunrise warm golden light",
    "Midday bright clear sky",
    "Golden hour warm sunset",
    "Blue hour twilight",
    "Night with interior lights glowing",
]

BALCONY_TYPES = {
    "cam_korkuluk": "Cam korkuluklu modern balkon",
    "ferforje": "Ferforje korkuluklu klasik balkon",
    "ahsap": "Ahşap korkuluklu balkon",
    "kapali_cam": "Kapalı cam balkon",
}

BALCONY_PROMPTS = {
    "cam_korkuluk": "modern glass railing balconies",
    "ferforje": "ornamental wrought iron railing balconies",
    "ahsap": "wooden railing balconies with natural finish",
    "kapali_cam": "enclosed glass balconies",
}

OTOPARK_OPTIONS = {
    "acik": "Açık otopark",
    "kapali": "Kapalı otopark",
    "bodrum": "Bodrum otopark",
}

PEYZAJ_OPTIONS = [
    "Ağaçlar",
    "Çim alan",
    "Yürüyüş yolu",
    "Çocuk parkı",
    "Oturma alanı",
    "Süs havuzu",
]

PEYZAJ_PROMPTS = {
    "Ağaçlar": "mature trees",
    "Çim alan": "manicured lawn",
    "Yürüyüş yolu": "paved walking paths",
    "Çocuk parkı": "children's playground",
    "Oturma alanı": "outdoor seating areas with benches",
    "Süs havuzu": "decorative water fountain",
}
