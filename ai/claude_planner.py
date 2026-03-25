"""
Claude Sonnet 4.6 Plan Üretim Modülü.
Claude API ile kat planı alternatiflerini üretir.
"""

import json
import logging
import os
from core.plan_scorer import FloorPlan, PlanRoom

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Sen uzman bir Türk mimarısın. Verilen kısıtlamalara göre konut daire kat planı tasarla.

KURALLAR:
1. Tüm odalar dikdörtgen olmalı (basit geometri).
2. Odalar çakışmamalı — hiçbir oda diğerinin üzerine binmemeli.
3. Tüm odalar yapılaşma alanı (buildable polygon) içinde kalmalı.
4. Islak hacimler (banyo, wc, mutfak) mümkünse gruplanmalı.
5. Salon ve balkonlar güneş alan cepheye bakmalı.
6. Yatak odaları sessiz cepheye (arka/yan) yerleştirilmeli.
7. Antre kapıdan girişte ilk karşılaşılan alan olmalı.
8. Koridor tüm odalara erişimi sağlamalı.
9. Türk yapı yönetmeliği minimum ölçüleri:
   - Oturma odası min 12m², Yatak odası min 9m², Mutfak min 5m²
   - Banyo min 3.5m², WC min 1.5m², Koridor genişliği min 1.10m

VERİ SETİ İSTATİSTİKLERİ:
{dataset_rules}

Cevabını SADECE aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:
{{
  "plans": [
    {{
      "rooms": [
        {{
          "name": "Salon",
          "type": "salon",
          "x": 0.0,
          "y": 0.0,
          "width": 6.0,
          "height": 5.0,
          "has_exterior_wall": true,
          "facing_direction": "south",
          "doors": [{{"wall": "north", "position": 0.15, "width": 0.90}}],
          "windows": [{{"wall": "south", "position": 0.5, "width": 1.80}}]
        }}
      ],
      "reasoning": "Salonu güney cepheye yerleştirdim çünkü..."
    }}
  ]
}}"""


def generate_plans_claude(
    polygon_coords: list[tuple[float, float]],
    apartment_program: dict,
    dataset_rules: dict,
    sun_direction: str = "south",
    api_key: str = "",
    plan_count: int = 2,
    previous_feedback: str | None = None,
) -> list[dict]:
    """Claude API ile plan üretir.

    Args:
        polygon_coords: Yapılaşma alanı koordinatları.
        apartment_program: Daire programı.
        dataset_rules: Veri seti kuralları.
        sun_direction: En iyi güneş yönü.
        api_key: Claude API anahtarı.
        plan_count: Üretilecek plan sayısı.
        previous_feedback: Önceki iterasyondan geri bildirim.

    Returns:
        [{"floor_plan": FloorPlan, "reasoning": str}, ...]
    """
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        logger.warning("Claude API key bulunamadı. Demo plan üretiliyor.")
        return _generate_demo_plans(polygon_coords, apartment_program, plan_count)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        rules_summary = _summarize_rules(dataset_rules)
        system = SYSTEM_PROMPT.format(dataset_rules=rules_summary)

        user_prompt = _build_user_prompt(
            polygon_coords, apartment_program, sun_direction, plan_count, previous_feedback
        )

        response = client.messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = response.content[0].text
        # Markdown code block içinden JSON çıkar
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        plans_data = json.loads(response_text.strip())
        return _parse_plans(plans_data)

    except Exception as e:
        logger.error(f"Claude API hatası: {e}")
        return _generate_demo_plans(polygon_coords, apartment_program, plan_count)


def _build_user_prompt(
    polygon_coords, apartment_program, sun_direction, plan_count, previous_feedback
) -> str:
    prompt = f"""Yapılaşma alanı köşe koordinatları (metre): {polygon_coords}

Daire programı:
- Daire tipi: {apartment_program.get('tip', '3+1')}
- Brüt alan: {apartment_program.get('brut_alan', 120)} m²
- Odalar: {json.dumps(apartment_program.get('odalar', []), ensure_ascii=False)}

Güneş verisi: En çok güneş alan cephe: {sun_direction}

{plan_count} farklı plan alternatifi üret. Her plan farklı yerleşim stratejisi kullansın."""

    if previous_feedback:
        prompt += f"\n\nÖNCEKİ İTERASYONDAN GERİ BİLDİRİM:\n{previous_feedback}\nBu sorunları gidererek daha iyi planlar üret."

    return prompt


def _summarize_rules(dataset_rules: dict) -> str:
    """Kural özetini prompt için formatla."""
    try:
        from dataset.dataset_rules import ROOM_SIZE_STATS, ADJACENCY_PROBABILITY
        lines = ["Oda boyut ortalamaları:"]
        for room, stats in ROOM_SIZE_STATS.items():
            lines.append(f"  {room}: {stats['avg']}m² (min:{stats['min']}, max:{stats['max']})")
        lines.append("\nÖnemli bitişiklik kuralları:")
        for (r1, r2), prob in sorted(ADJACENCY_PROBABILITY.items(), key=lambda x: -x[1])[:8]:
            lines.append(f"  {r1}↔{r2}: {prob:.0%}")
        return "\n".join(lines)
    except Exception:
        return str(dataset_rules)[:1000]


def _parse_plans(data: dict) -> list[dict]:
    """AI çıktısını FloorPlan nesnelerine dönüştür."""
    results = []
    for plan_data in data.get("plans", []):
        rooms = []
        for r in plan_data.get("rooms", []):
            rooms.append(PlanRoom(
                name=r.get("name", "Oda"),
                room_type=r.get("type", "diger"),
                x=float(r.get("x", 0)),
                y=float(r.get("y", 0)),
                width=float(r.get("width", 3)),
                height=float(r.get("height", 3)),
                has_exterior_wall=r.get("has_exterior_wall", False),
                facing_direction=r.get("facing_direction", ""),
                doors=r.get("doors", []),
                windows=r.get("windows", []),
            ))

        total_area = sum(r.area for r in rooms)
        fp = FloorPlan(rooms=rooms, total_area=total_area)

        results.append({
            "floor_plan": fp,
            "reasoning": plan_data.get("reasoning", ""),
        })

    return results


def _generate_demo_plans(
    polygon_coords: list[tuple[float, float]],
    apartment_program: dict,
    plan_count: int = 2,
) -> list[dict]:
    """API key olmadan demo plan üretir (algoritmik yerleştirme)."""
    results = []

    # Yapılaşma alanı boyutlarını hesapla
    if polygon_coords and len(polygon_coords) >= 3:
        xs = [c[0] for c in polygon_coords]
        ys = [c[1] for c in polygon_coords]
        total_w = max(xs) - min(xs)
        total_h = max(ys) - min(ys)
        origin_x = min(xs)
        origin_y = min(ys)
    else:
        total_w, total_h = 16.0, 12.0
        origin_x, origin_y = 0.0, 0.0

    odalar = apartment_program.get("odalar", [
        {"isim": "Salon", "tip": "salon", "m2": 24},
        {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "m2": 14},
        {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "m2": 12},
        {"isim": "Yatak Odası 3", "tip": "yatak_odasi", "m2": 10},
        {"isim": "Mutfak", "tip": "mutfak", "m2": 10},
        {"isim": "Banyo", "tip": "banyo", "m2": 5},
        {"isim": "WC", "tip": "wc", "m2": 2.5},
        {"isim": "Antre", "tip": "antre", "m2": 5},
        {"isim": "Koridor", "tip": "koridor", "m2": 4},
        {"isim": "Balkon", "tip": "balkon", "m2": 5},
    ])

    for plan_idx in range(plan_count):
        rooms = []
        import math

        # Basit grid-based yerleştirme (strateji farklılığı plan_idx'e göre)
        if plan_idx == 0:
            # Strateji 1: Salon ön cephe, yatak odaları arka
            _place_rooms_strategy_1(rooms, odalar, total_w, total_h, origin_x, origin_y)
        else:
            # Strateji 2: L-şekilli salon, mutfak ortada
            _place_rooms_strategy_2(rooms, odalar, total_w, total_h, origin_x, origin_y)

        total_area = sum(r.area for r in rooms)
        fp = FloorPlan(rooms=rooms, total_area=total_area,
                       apartment_type=apartment_program.get("tip", "3+1"))

        results.append({
            "floor_plan": fp,
            "reasoning": f"Demo plan {plan_idx + 1} — algoritmik yerleştirme",
        })

    return results


def _place_rooms_strategy_1(rooms, odalar, tw, th, ox, oy):
    """Strateji 1: Salon güneyde, yatak odaları kuzeyde."""
    import math
    x, y = ox, oy
    row_height = th / 3

    for oda in odalar:
        m2 = oda.get("m2", oda.get("varsayilan_m2", 10))
        tip = oda.get("tip", "diger")
        isim = oda.get("isim", "Oda")

        width = min(math.sqrt(m2 * 1.3), tw - (x - ox))
        height = m2 / width if width > 0 else 3.0

        if x - ox + width > tw:
            x = ox
            y += row_height

        if y - oy + height > th:
            height = th - (y - oy)

        is_exterior = (x <= ox + 0.1 or x + width >= ox + tw - 0.1 or
                       y <= oy + 0.1 or y + height >= oy + th - 0.1)

        rooms.append(PlanRoom(
            name=isim, room_type=tip,
            x=round(x, 2), y=round(y, 2),
            width=round(width, 2), height=round(height, 2),
            has_exterior_wall=is_exterior,
            facing_direction="south" if y <= oy + 0.5 else "north",
        ))

        x += width + 0.1


def _place_rooms_strategy_2(rooms, odalar, tw, th, ox, oy):
    """Strateji 2: Odalar çevrede, sirkülasyon ortada."""
    import math
    corridor_width = 1.2
    half_w = (tw - corridor_width) / 2
    left_x = ox
    right_x = ox + half_w + corridor_width
    y_left = oy
    y_right = oy

    for i, oda in enumerate(odalar):
        m2 = oda.get("m2", oda.get("varsayilan_m2", 10))
        tip = oda.get("tip", "diger")
        isim = oda.get("isim", "Oda")

        if tip == "koridor":
            rooms.append(PlanRoom(
                name=isim, room_type=tip,
                x=round(ox + half_w, 2), y=round(oy, 2),
                width=round(corridor_width, 2), height=round(th, 2),
                has_exterior_wall=False,
            ))
            continue

        # Sola ve sağa dağıt
        if i % 2 == 0:
            width = min(half_w, math.sqrt(m2 * 1.5))
            height = m2 / width if width > 0 else 3.0
            if y_left + height > oy + th:
                continue
            rooms.append(PlanRoom(
                name=isim, room_type=tip,
                x=round(left_x, 2), y=round(y_left, 2),
                width=round(width, 2), height=round(height, 2),
                has_exterior_wall=True,
                facing_direction="west",
            ))
            y_left += height + 0.1
        else:
            width = min(half_w, math.sqrt(m2 * 1.5))
            height = m2 / width if width > 0 else 3.0
            if y_right + height > oy + th:
                continue
            rooms.append(PlanRoom(
                name=isim, room_type=tip,
                x=round(right_x, 2), y=round(y_right, 2),
                width=round(width, 2), height=round(height, 2),
                has_exterior_wall=True,
                facing_direction="east",
            ))
            y_right += height + 0.1
