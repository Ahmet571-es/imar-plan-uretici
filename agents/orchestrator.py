"""
Orkestratör Ajan — Diğer ajanları yöneten, önceliklendiren ve özetleyen merkezi ajan.
"""

import logging
from datetime import datetime
from agents.base_agent import BaseAgent, AgentMessage, AgentRun
from database.db import get_session

logger = logging.getLogger(__name__)


class OrkestatorAjani(BaseAgent):
    """Tüm ajanları koordine eden merkezi ajan."""

    def __init__(self):
        super().__init__(
            name="orkestrator",
            description="Ajan sonuçlarını analiz eder, önceliklendirir, günlük özet oluşturur",
        )
        self.registered_agents = {}

    def register_agent(self, agent: BaseAgent):
        """Bir ajanı orkestratöre kaydeder."""
        self.registered_agents[agent.name] = agent

    def execute(self, **kwargs) -> dict:
        """Orkestratör döngüsü — mesajları oku, analiz et, karar ver."""
        # 1. Okunmamış mesajları al
        messages = self.get_unread_messages("orkestrator")

        # 2. Sonuçları kategorize et
        results = []
        alerts = []
        errors = []

        for msg in messages:
            if msg["type"] == "result":
                results.append(msg)
            elif msg["type"] == "alert":
                alerts.append(msg)
            elif msg["type"] == "error":
                errors.append(msg)

        # 3. Ajan durum özeti
        agent_statuses = {}
        for name, agent in self.registered_agents.items():
            agent_statuses[name] = agent.get_status()

        # 4. Günlük özet oluştur
        active_count = sum(1 for s in agent_statuses.values() if s.get("last_status") == "completed")
        error_count = sum(1 for s in agent_statuses.values() if s.get("last_status") == "failed")
        total_items = sum(s.get("last_items", 0) for s in agent_statuses.values())

        # 5. Aksiyonlar belirle
        aksiyonlar = []
        for msg in results:
            payload = msg.get("payload", {})
            ajan = msg.get("from", "")

            if ajan == "plan_optimizasyon":
                stats = payload.get("data", {}).get("stats", {})
                if stats.get("max_score", 0) > 70:
                    aksiyonlar.append({
                        "oncelik": "yüksek",
                        "aksiyon": f"Plan optimizasyon en iyi skor: {stats.get('max_score', 0):.0f}/100 — incelenmeli",
                        "kaynak": ajan,
                    })

            elif ajan == "daire_karmasi":
                en_karli = payload.get("data", {}).get("en_karli", {})
                if en_karli and en_karli.get("kar_marji", 0) > 20:
                    aksiyonlar.append({
                        "oncelik": "yüksek",
                        "aksiyon": f"Kârlı daire karması bulundu: {en_karli.get('label', '?')} — %{en_karli.get('kar_marji', 0):.0f} kâr",
                        "kaynak": ajan,
                    })

            elif ajan == "toplu_fizibilite":
                data = payload.get("data", {})
                cok_karli = data.get("istatistik", {}).get("cok_karli", 0)
                if cok_karli > 0:
                    top = data.get("sonuclar", [{}])[0]
                    aksiyonlar.append({
                        "oncelik": "yüksek",
                        "aksiyon": f"{cok_karli} çok kârlı parsel bulundu! En iyi: {top.get('isim', '?')} %{top.get('kar_marji', 0):.0f}",
                        "kaynak": ajan,
                    })

            elif ajan == "maliyet_optimizasyon":
                en_karli_s = payload.get("data", {}).get("en_karli_sistem", {})
                if en_karli_s:
                    aksiyonlar.append({
                        "oncelik": "orta",
                        "aksiyon": f"En kârlı yapı sistemi: {en_karli_s.get('sistem', '?')} — %{en_karli_s.get('kar_marji', 0):.0f} kâr",
                        "kaynak": ajan,
                    })

        for msg in errors:
            aksiyonlar.append({
                "oncelik": "düşük",
                "aksiyon": f"Hata: {msg.get('from', '?')} — {str(msg.get('payload', {}).get('error', ''))[:80]}",
                "kaynak": msg.get("from", "?"),
            })

        # Önceliğe göre sırala
        oncelik_sirasi = {"yüksek": 0, "orta": 1, "düşük": 2}
        aksiyonlar.sort(key=lambda x: oncelik_sirasi.get(x["oncelik"], 3))

        summary = (
            f"Orkestratör özeti: {active_count} ajan aktif, {error_count} hata, "
            f"{len(messages)} yeni mesaj, {total_items} toplam bulgu, "
            f"{len(aksiyonlar)} aksiyon."
        )

        return {
            "success": True,
            "items_found": len(aksiyonlar),
            "summary": summary,
            "data": {
                "agent_statuses": agent_statuses,
                "aksiyonlar": aksiyonlar,
                "mesaj_sayisi": {"result": len(results), "alert": len(alerts), "error": len(errors)},
                "zaman": datetime.utcnow().strftime("%d.%m.%Y %H:%M"),
            },
        }

    def run_all_agents(self, **common_kwargs) -> dict:
        """Tüm kayıtlı ajanları sırayla çalıştırır, sonra orkestratörü çalıştırır."""
        self.logger.info(f"=== Tüm ajanlar çalıştırılıyor ({len(self.registered_agents)} ajan) ===")

        results = {}
        for name, agent in self.registered_agents.items():
            if name == "orkestrator":
                continue
            self.logger.info(f"▶ {name} başlatılıyor...")
            result = agent.run(**common_kwargs)
            results[name] = result

        # Son olarak orkestratörü çalıştır
        self.logger.info("▶ Orkestratör çalıştırılıyor...")
        ork_result = self.run()
        results["orkestrator"] = ork_result

        return results
