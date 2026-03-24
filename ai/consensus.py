"""
Konsensüs Mekanizması — En iyi planları seçme.
"""


def select_best_plans(all_plans: list, top_n: int = 3) -> list:
    """Tüm planlardan en iyi N tanesini seçer.

    Sıralama: score.total (yüksekten düşüğe).
    Aynı AI'dan gelen benzer planlar varsa çeşitliliği korur.
    """
    # Puanla sırala
    scored = [(p, p.score.total if p.score else 0) for p in all_plans]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Çeşitlilik: farklı kaynaklardan plan seçmeye çalış
    selected = []
    sources_count = {"claude": 0, "grok": 0}

    for plan, score in scored:
        if len(selected) >= top_n:
            break
        # Bir kaynaktan en fazla 2 plan
        if sources_count.get(plan.source, 0) < 2:
            selected.append(plan)
            sources_count[plan.source] = sources_count.get(plan.source, 0) + 1

    # Yeterli plan yoksa geri kalanları ekle
    if len(selected) < top_n:
        for plan, score in scored:
            if plan not in selected:
                selected.append(plan)
            if len(selected) >= top_n:
                break

    return selected[:top_n]
