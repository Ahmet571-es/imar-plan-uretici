"""
Dual AI Plan Üretim Motoru — Claude Sonnet 4.6 + Grok 4.20 koordinatörü.

4 plan üretir (her AI'dan 2), puanlar, en iyi 3'ü seçer.
Çapraz değerlendirme ile kaliteyi artırır.
"""

import json
import logging
import os
from dataclasses import dataclass, field

from ai.claude_planner import generate_plans_claude
from ai.grok_planner import generate_plans_grok
from ai.cross_review import cross_review
from ai.consensus import select_best_plans
from core.plan_scorer import score_plan, FloorPlan, ScoreBreakdown

logger = logging.getLogger(__name__)


@dataclass
class PlanAlternatif:
    """Bir plan alternatifi."""
    plan: FloorPlan
    source: str              # "claude" veya "grok"
    score: ScoreBreakdown | None = None
    cross_review_score: float = 0.0
    cross_review_notes: str = ""
    final_score: float = 0.0
    reasoning: str = ""


@dataclass
class DualAIResult:
    """Dual AI sonuç paketi."""
    all_plans: list[PlanAlternatif] = field(default_factory=list)
    best_plans: list[PlanAlternatif] = field(default_factory=list)
    iteration: int = 1
    summary: str = ""


def generate_dual_ai_plans(
    buildable_polygon_coords: list[tuple[float, float]],
    apartment_program: dict,
    dataset_rules: dict,
    sun_best_direction: str = "south",
    building_codes: dict | None = None,
    claude_api_key: str = "",
    grok_api_key: str = "",
    max_iterations: int = 3,
) -> DualAIResult:
    """Dual AI ile plan üretim döngüsü.

    Args:
        buildable_polygon_coords: Yapılaşma alanı köşe koordinatları.
        apartment_program: Daire programı (tip, oda listesi, m²).
        dataset_rules: Veri seti kuralları dict.
        sun_best_direction: En iyi güneş yönü.
        building_codes: Yapı yönetmeliği kuralları.
        claude_api_key: Claude API anahtarı.
        grok_api_key: Grok/xAI API anahtarı.
        max_iterations: Maksimum iterasyon sayısı.

    Returns:
        DualAIResult nesnesi.
    """
    result = DualAIResult()

    # Her iki API anahtarı da yoksa kullanıcıyı bilgilendir
    has_claude_key = bool(claude_api_key or os.environ.get("ANTHROPIC_API_KEY", ""))
    has_grok_key = bool(grok_api_key or os.environ.get("XAI_API_KEY", ""))
    if not has_claude_key and not has_grok_key:
        logger.warning(
            "Claude ve Grok API anahtarları bulunamadı. "
            "Demo modunda çalışılıyor — algoritmik planlar üretilecek."
        )

    for iteration in range(1, max_iterations + 1):
        result.iteration = iteration
        logger.info(f"=== İterasyon {iteration}/{max_iterations} ===")

        # ── 1. Claude'dan 2 plan al ──
        try:
            claude_plans = generate_plans_claude(
                polygon_coords=buildable_polygon_coords,
                apartment_program=apartment_program,
                dataset_rules=dataset_rules,
                sun_direction=sun_best_direction,
                api_key=claude_api_key,
                plan_count=2,
                previous_feedback=_get_feedback(result.best_plans, "claude") if iteration > 1 else None,
            )
            for plan in claude_plans:
                result.all_plans.append(PlanAlternatif(
                    plan=plan["floor_plan"],
                    source="claude",
                    reasoning=plan.get("reasoning", ""),
                ))
        except Exception as e:
            logger.error(f"Claude plan üretimi hatası: {e}")
            # Fallback: boş plan ekle
            claude_plans = []

        # ── 2. Grok 4.20'den 2 plan al ──
        try:
            grok_plans = generate_plans_grok(
                polygon_coords=buildable_polygon_coords,
                apartment_program=apartment_program,
                dataset_rules=dataset_rules,
                sun_direction=sun_best_direction,
                api_key=grok_api_key,
                plan_count=2,
                previous_feedback=_get_feedback(result.best_plans, "grok") if iteration > 1 else None,
            )
            for plan in grok_plans:
                result.all_plans.append(PlanAlternatif(
                    plan=plan["floor_plan"],
                    source="grok",
                    reasoning=plan.get("reasoning", ""),
                ))
        except Exception as e:
            logger.error(f"Grok plan üretimi hatası: {e}")
            grok_plans = []

        # ── 3. Tüm planları puanla ──
        for alt in result.all_plans:
            if alt.score is None:
                alt.score = score_plan(
                    alt.plan,
                    sun_best_direction=sun_best_direction,
                )

        # ── 4. En iyi 3'ü seç ──
        result.best_plans = select_best_plans(result.all_plans, top_n=3)

        if not result.best_plans:
            logger.warning(f"İterasyon {iteration}: Hiç plan üretilemedi, sonraki iterasyona geçiliyor.")
            continue

        # ── 5. Çapraz değerlendirme ──
        try:
            cross_review(
                plans=result.best_plans,
                claude_api_key=claude_api_key,
                grok_api_key=grok_api_key,
            )
        except Exception as e:
            logger.error(f"Çapraz değerlendirme hatası: {e}")

        # ── 6. Final puanı hesapla ──
        for alt in result.best_plans:
            own_score = alt.score.total if alt.score else 0
            # API anahtarları yoksa çapraz değerlendirme yapılamaz, kendi puanını kullan
            if alt.cross_review_score > 0:
                alt.final_score = own_score * 0.4 + alt.cross_review_score * 0.6
            else:
                alt.final_score = own_score

        # Sırala
        result.best_plans.sort(key=lambda x: x.final_score, reverse=True)

        logger.info(f"İterasyon {iteration} tamamlandı. "
                    f"En iyi puan: {result.best_plans[0].final_score:.1f}/100"
                    if result.best_plans else "Plan üretilemedi.")

    # Özet oluştur
    if result.best_plans:
        result.summary = (
            f"{len(result.all_plans)} plan üretildi, en iyi 3 seçildi.\n"
            f"En iyi puan: {result.best_plans[0].final_score:.1f}/100 "
            f"(kaynak: {result.best_plans[0].source})\n"
            f"İterasyonlar: {max_iterations}"
        )

    return result


def _get_feedback(best_plans: list[PlanAlternatif], source: str) -> str:
    """Önceki iterasyondan geri bildirim oluştur."""
    feedback_parts = []
    for p in best_plans:
        if p.cross_review_notes:
            feedback_parts.append(f"Plan ({p.source}): {p.cross_review_notes}")
        if p.score and p.score.details:
            issues = [d for d in p.score.details if d.startswith("⚠️")]
            if issues:
                feedback_parts.append("Sorunlar: " + "; ".join(issues[:3]))
    return "\n".join(feedback_parts) if feedback_parts else ""
