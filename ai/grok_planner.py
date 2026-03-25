"""
Grok 4.20 Plan Üretim Modülü.
xAI API (OpenAI uyumlu) ile bağımsız plan üretimi ve değerlendirme.
"""

import json
import logging
import os
from core.plan_scorer import FloorPlan, PlanRoom

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Turkish architect. Design residential apartment floor plans
based on the given constraints. Respond ONLY in valid JSON format.

RULES:
- All rooms must be rectangular.
- Rooms must not overlap.
- Wet areas (bathroom, WC, kitchen) should be clustered together.
- Living room and balconies should face the sunniest direction.
- Bedrooms should be in quieter zones (back/side).
- Follow Turkish building codes: min room sizes, corridor widths.

DATASET STATISTICS:
{dataset_rules}

JSON FORMAT:
{{
  "plans": [
    {{
      "rooms": [
        {{
          "name": "Salon",
          "type": "salon",
          "x": 0.0, "y": 0.0,
          "width": 6.0, "height": 5.0,
          "has_exterior_wall": true,
          "facing_direction": "south",
          "doors": [{{"wall": "north", "position": 0.15, "width": 0.90}}],
          "windows": [{{"wall": "south", "position": 0.5, "width": 1.80}}]
        }}
      ],
      "reasoning": "I placed the living room facing south because..."
    }}
  ]
}}"""


def generate_plans_grok(
    polygon_coords: list[tuple[float, float]],
    apartment_program: dict,
    dataset_rules: dict,
    sun_direction: str = "south",
    api_key: str = "",
    plan_count: int = 2,
    previous_feedback: str | None = None,
    timeout: float = 30.0,
) -> list[dict]:
    """Grok 4.20 API ile plan üretir.

    Args:
        polygon_coords: Yapılaşma alanı koordinatları.
        apartment_program: Daire programı.
        dataset_rules: Veri seti kuralları.
        sun_direction: En iyi güneş yönü.
        api_key: Grok/xAI API anahtarı.
        plan_count: Üretilecek plan sayısı.
        previous_feedback: Önceki iterasyondan geri bildirim.
        timeout: API isteği zaman aşımı süresi (saniye, varsayılan 30s).

    Returns:
        [{"floor_plan": FloorPlan, "reasoning": str}, ...]
    """
    if not api_key:
        api_key = os.getenv("XAI_API_KEY", "")

    if not api_key:
        logger.warning("Grok API key bulunamadı. Demo plan üretiliyor.")
        return _generate_grok_demo(polygon_coords, apartment_program, plan_count)

    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=api_key,
            timeout=timeout,
        )

        rules_summary = _summarize_rules(dataset_rules)
        system = SYSTEM_PROMPT.format(dataset_rules=rules_summary)
        user_prompt = _build_prompt(polygon_coords, apartment_program, sun_direction, plan_count, previous_feedback)

        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4096,
        )

        text = response.choices[0].message.content
        # JSON çıkar
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text)
        return _parse_plans(data)

    except Exception as e:
        logger.error(f"Grok API hatası: {e}")
        return _generate_grok_demo(polygon_coords, apartment_program, plan_count)


def _build_prompt(polygon_coords, apartment_program, sun_dir, plan_count, feedback) -> str:
    prompt = f"""Buildable area coordinates (meters): {polygon_coords}

Apartment program:
- Type: {apartment_program.get('tip', '3+1')}
- Gross area: {apartment_program.get('brut_alan', 120)} m²
- Rooms: {json.dumps(apartment_program.get('odalar', []), ensure_ascii=False)}

Sun data: Best sun direction: {sun_dir}

Generate {plan_count} different plan alternatives with different layout strategies."""

    if feedback:
        prompt += f"\n\nPREVIOUS FEEDBACK:\n{feedback}\nFix these issues."
    return prompt


def _summarize_rules(dataset_rules: dict) -> str:
    try:
        from dataset.dataset_rules import ROOM_SIZE_STATS
        lines = []
        for room, stats in ROOM_SIZE_STATS.items():
            lines.append(f"{room}: avg {stats['avg']}m² ({stats['min']}-{stats['max']})")
        return "\n".join(lines)
    except Exception:
        return str(dataset_rules)[:500]


def _parse_plans(data: dict) -> list[dict]:
    results = []
    for plan_data in data.get("plans", []):
        rooms = []
        for r in plan_data.get("rooms", []):
            rooms.append(PlanRoom(
                name=r.get("name", "Room"),
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
        fp = FloorPlan(rooms=rooms, total_area=sum(r.area for r in rooms))
        results.append({"floor_plan": fp, "reasoning": plan_data.get("reasoning", "")})
    return results


def _generate_grok_demo(polygon_coords, apartment_program, plan_count):
    """Grok API olmadan demo plan üretir (farklı strateji)."""
    import math
    results = []

    if polygon_coords and len(polygon_coords) >= 3:
        xs = [c[0] for c in polygon_coords]
        ys = [c[1] for c in polygon_coords]
        tw = max(xs) - min(xs)
        th = max(ys) - min(ys)
        ox, oy = min(xs), min(ys)
    else:
        tw, th, ox, oy = 16.0, 12.0, 0.0, 0.0

    odalar = apartment_program.get("odalar", [
        {"isim": "Salon", "tip": "salon", "m2": 24},
        {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "m2": 14},
        {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "m2": 12},
        {"isim": "Mutfak", "tip": "mutfak", "m2": 10},
        {"isim": "Banyo", "tip": "banyo", "m2": 5},
        {"isim": "WC", "tip": "wc", "m2": 2.5},
        {"isim": "Antre", "tip": "antre", "m2": 5},
        {"isim": "Koridor", "tip": "koridor", "m2": 4},
        {"isim": "Balkon", "tip": "balkon", "m2": 5},
    ])

    for plan_idx in range(plan_count):
        rooms = []
        # Grok stratejisi: ıslak hacimleri bir tarafa toplama
        wet = [o for o in odalar if o.get("tip") in ("banyo", "wc", "mutfak")]
        dry = [o for o in odalar if o.get("tip") not in ("banyo", "wc", "mutfak", "koridor")]
        corridor = [o for o in odalar if o.get("tip") == "koridor"]

        y_cur = oy
        for oda in dry:
            m2 = oda.get("m2", oda.get("varsayilan_m2", 10))
            w = min(tw * 0.6, math.sqrt(m2 * 1.3))
            h = m2 / w
            if y_cur + h > oy + th:
                break
            rooms.append(PlanRoom(
                name=oda["isim"], room_type=oda["tip"],
                x=round(ox, 2), y=round(y_cur, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=True, facing_direction="south" if y_cur == oy else "west",
            ))
            y_cur += h + 0.1

        # Islak hacimler sağda
        y_wet = oy
        wet_x = ox + tw * 0.65
        for oda in wet:
            m2 = oda.get("m2", oda.get("varsayilan_m2", 5))
            w = min(tw * 0.3, max(2.0, math.sqrt(m2)))
            h = m2 / w
            if y_wet + h > oy + th:
                break
            rooms.append(PlanRoom(
                name=oda["isim"], room_type=oda["tip"],
                x=round(wet_x, 2), y=round(y_wet, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=True, facing_direction="east",
            ))
            y_wet += h + 0.1

        fp = FloorPlan(rooms=rooms, total_area=sum(r.area for r in rooms),
                       apartment_type=apartment_program.get("tip", "3+1"))
        results.append({"floor_plan": fp, "reasoning": f"Grok demo plan {plan_idx+1} — ıslak hacim gruplaması"})

    return results
