"""
Ajan 5 — Plan Optimizasyon: Yüzlerce plan varyasyonu üretip en iyisini seçer.
Dış API gerektirmez — mevcut plan_scorer + demo planner kullanır.
"""

import math
import random
import logging
from agents.base_agent import BaseAgent
from core.plan_scorer import score_plan, FloorPlan, PlanRoom
from dataset.dataset_rules import (
    ROOM_SIZE_STATS, ROOM_ASPECT_RATIOS, ROOM_PLACEMENT_RULES,
    calculate_ideal_dimensions, get_adjacency_score,
)

logger = logging.getLogger(__name__)


class PlanOptimizasyonAjani(BaseAgent):
    """Gece boyunca yüzlerce plan varyasyonu üretip en iyisini seçer."""

    def __init__(self):
        super().__init__(
            name="plan_optimizasyon",
            description="Plan varyasyonları üretir, puanlar, en iyilerini seçer",
        )

    def execute(
        self,
        buildable_width: float = 16.0,
        buildable_height: float = 12.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        apartment_type: str = "3+1",
        target_area: float = 120.0,
        iteration_count: int = 200,
        sun_direction: str = "south",
        **kwargs,
    ) -> dict:
        """Plan optimizasyonu çalıştırır."""
        from core.floor_plan_generator import generate_professional_plan
        self.logger.info(f"Plan optimizasyonu başlıyor — {iteration_count} iterasyon")

        all_plans = []
        best_score = 0

        for i in range(iteration_count):
            plan = generate_professional_plan(
                buildable_width, buildable_height, origin_x, origin_y,
                apartment_type=apartment_type, target_area=target_area,
                sun_direction=sun_direction,
                entrance_side=["south", "south", "west", "east"][i % 4],
                seed=i * 7 + 13,
            )

            if plan and plan.rooms:
                sc = score_plan(plan, sun_best_direction=sun_direction)
                all_plans.append({"plan": plan, "score": sc.total, "strategy": i % 4})

                if sc.total > best_score:
                    best_score = sc.total

        # En iyi 5'i seç
        all_plans.sort(key=lambda x: x["score"], reverse=True)
        top_5 = all_plans[:5]

        # Puan dağılımı istatistikleri
        scores = [p["score"] for p in all_plans if p["score"] > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        summary = (
            f"{iteration_count} plan test edildi. "
            f"En iyi: {max_score:.1f}/100, Ortalama: {avg_score:.1f}/100, "
            f"En düşük: {min_score:.1f}/100. "
            f"Top 5 strateji: {[p['strategy'] for p in top_5]}"
        )

        return {
            "success": True,
            "items_found": len([p for p in all_plans if p["score"] > 50]),
            "summary": summary,
            "data": {
                "top_plans": [
                    {
                        "score": p["score"],
                        "strategy": p["strategy"],
                        "room_count": len(p["plan"].rooms),
                        "total_area": p["plan"].total_area,
                    }
                    for p in top_5
                ],
                "stats": {
                    "total_tested": iteration_count,
                    "avg_score": round(avg_score, 1),
                    "max_score": round(max_score, 1),
                    "min_score": round(min_score, 1),
                    "above_60": len([s for s in scores if s > 60]),
                    "above_70": len([s for s in scores if s > 70]),
                },
            },
        }


