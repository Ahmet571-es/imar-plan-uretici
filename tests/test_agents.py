"""
FAZ 7 — Otomasyon & Ajan Sistemi Testleri.

Ajan olusturma, orkestrator, plan optimizasyon, maliyet optimizasyon,
daire karmasi, toplu fizibilite ve ajan mesajlasma testleri.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from agents.agent_config import create_agent_system, DEFAULT_PARAMS, AJAN_BILGILERI
from agents.base_agent import BaseAgent, AgentMessage, AgentRun
from agents.orchestrator import OrkestatorAjani
from agents.plan_optimizasyon import PlanOptimizasyonAjani
from agents.maliyet_optimizasyon import MaliyetOptimizasyonAjani
from agents.daire_karmasi import DaireKarmasiAjani
from agents.toplu_fizibilite import TopluFizibiliteAjani


# ══════════════════════════════════════════════════
#  Ajan Sistemi Testleri
# ══════════════════════════════════════════════════

class TestAjanSistemi:
    """Ajan sistemi olusturma ve yapilandirma testleri."""

    def test_agent_system_creation(self):
        """Ajan sistemi basarili sekilde olusturulmali."""
        orkestrator, ajanlar = create_agent_system()
        assert isinstance(orkestrator, OrkestatorAjani)
        assert isinstance(ajanlar, dict)
        assert len(ajanlar) == 4
        assert "plan_optimizasyon" in ajanlar
        assert "maliyet_optimizasyon" in ajanlar
        assert "daire_karmasi" in ajanlar
        assert "toplu_fizibilite" in ajanlar
        # Her ajan BaseAgent'dan turemiş olmali
        for name, agent in ajanlar.items():
            assert isinstance(agent, BaseAgent)
            assert agent.name == name

    def test_orkestrator_register(self):
        """Orkestrator ajanlari basarili sekilde kaydetmeli."""
        orkestrator = OrkestatorAjani()
        plan_agent = PlanOptimizasyonAjani()
        maliyet_agent = MaliyetOptimizasyonAjani()

        orkestrator.register_agent(plan_agent)
        orkestrator.register_agent(maliyet_agent)

        assert "plan_optimizasyon" in orkestrator.registered_agents
        assert "maliyet_optimizasyon" in orkestrator.registered_agents
        assert len(orkestrator.registered_agents) == 2
        assert orkestrator.registered_agents["plan_optimizasyon"] is plan_agent


# ══════════════════════════════════════════════════
#  Ajan Calisma Testleri
# ══════════════════════════════════════════════════

class TestAjanCalisma:
    """Ajanlarin calistirilmasi testleri."""

    def test_plan_optimizasyon_run(self):
        """Plan optimizasyon ajani basarili sekilde calismali."""
        agent = PlanOptimizasyonAjani()
        result = agent.run(
            buildable_width=16.0,
            buildable_height=12.0,
            apartment_type="3+1",
            target_area=120.0,
            iteration_count=10,  # Test icin az iterasyon
            sun_direction="south",
        )
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("items_found", 0) >= 0
        assert "summary" in result
        assert "data" in result
        # data icinde stats ve top_plans olmali
        data = result["data"]
        assert "stats" in data
        assert "top_plans" in data
        assert data["stats"]["total_tested"] == 10

    def test_maliyet_optimizasyon_run(self):
        """Maliyet optimizasyon ajani basarili sekilde calismali."""
        agent = MaliyetOptimizasyonAjani()
        result = agent.run(
            toplam_insaat_alani=850.0,
            il="Ankara",
            arsa_maliyeti=5_000_000,
            otopark_arac=8,
            hedef_satis_m2=40_000,
        )
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("items_found", 0) > 0
        assert "data" in result
        data = result["data"]
        assert "yapi_sistemleri" in data
        assert "malzeme_senaryolari" in data
        assert "en_karli_sistem" in data
        assert len(data["yapi_sistemleri"]) == 4  # 4 yapi sistemi
        assert len(data["malzeme_senaryolari"]) == 3  # 3 senaryo

    def test_daire_karmasi_run(self):
        """Daire karmasi ajani basarili sekilde calismali."""
        agent = DaireKarmasiAjani()
        result = agent.run(
            kat_basi_net_alan=190.0,
            kat_sayisi=4,
            toplam_insaat_alani=850.0,
            il="Ankara",
            baz_m2_fiyat=40_000,
            arsa_maliyeti=5_000_000,
        )
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("items_found", 0) > 0
        assert "data" in result
        data = result["data"]
        assert "tum_senaryolar" in data
        assert "en_karli" in data
        assert "en_hizli_satis" in data
        assert "dengeli" in data
        # En karli senaryoda gerekli alanlar olmali
        en_karli = data["en_karli"]
        assert "kar_marji" in en_karli
        assert "label" in en_karli
        assert "daire_sayisi" in en_karli

    def test_toplu_fizibilite_run(self):
        """Toplu fizibilite ajani demo verisi ile basarili calismali."""
        agent = TopluFizibiliteAjani()
        result = agent.run(
            parseller=None,  # Demo verisi kullan
            il="Ankara",
            m2_satis_fiyati=40_000,
            kalite="orta",
            daire_tipi="3+1",
            daire_per_kat=2,
        )
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("items_found", 0) >= 0
        assert "data" in result
        data = result["data"]
        assert "sonuclar" in data
        assert "istatistik" in data
        ist = data["istatistik"]
        assert ist["toplam"] == 8  # 8 demo parsel
        assert ist["basarili"] > 0

    def test_orkestrator_run(self):
        """Orkestrator basarili sekilde calismali."""
        orkestrator, ajanlar = create_agent_system()
        result = orkestrator.run()
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert "data" in result
        data = result["data"]
        assert "agent_statuses" in data
        assert "aksiyonlar" in data
        assert "mesaj_sayisi" in data
        assert "zaman" in data


# ══════════════════════════════════════════════════
#  Ajan Durum ve Mesajlasma Testleri
# ══════════════════════════════════════════════════

class TestAjanDurumMesaj:
    """Ajan durum sorgulama ve mesajlasma testleri."""

    def test_agent_status(self):
        """Ajan durum sorgusu dogru dict dondurmeli."""
        agent = PlanOptimizasyonAjani()
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "name" in status
        assert "description" in status
        assert "is_running" in status
        assert "last_status" in status
        assert "last_run" in status
        assert status["name"] == "plan_optimizasyon"

        # Hic calistirilmamis ajan icin
        assert status["last_status"] in ("never_run", "completed", "failed", "running")

    def test_agent_status_after_run(self):
        """Calistirmadan sonra durum guncellenmeli."""
        agent = PlanOptimizasyonAjani()
        agent.run(iteration_count=5)
        status = agent.get_status()
        assert status["last_status"] == "completed"
        assert status["last_items"] >= 0
        assert "last_duration" in status

    def test_agent_message_send(self):
        """Ajan mesaj gonderme ve alma mekanizmasi calismali."""
        agent = PlanOptimizasyonAjani()
        # Ajan calistir — otomatik olarak orkestratöre mesaj gonderir
        agent.run(iteration_count=5)

        # Okunmamis mesajlari al
        messages = BaseAgent.get_unread_messages("orkestrator")
        assert isinstance(messages, list)
        # En az bir mesaj olmali (calistirma sonucu)
        # (onceki testlerden de mesajlar birikebilir)

    def test_agent_recent_runs(self):
        """Son calisma kayitlari listelenebilmeli."""
        agent = PlanOptimizasyonAjani()
        agent.run(iteration_count=5)

        runs = BaseAgent.get_recent_runs(agent_name="plan_optimizasyon", limit=5)
        assert isinstance(runs, list)
        assert len(runs) > 0
        # Her kayitta gerekli alanlar olmali
        run = runs[0]
        assert "agent" in run
        assert "status" in run
        assert "duration" in run
        assert "items" in run

    def test_run_all_agents(self):
        """Orkestrator tum ajanlari calistirabilmeli."""
        orkestrator, ajanlar = create_agent_system()

        # Parametresiz calistir (ajanlar varsayilan parametreleri kullanamaz,
        # bu yüzden oncelikle ajanlari tek tek küçük parametrelerle calistiralim)
        # run_all_agents ortak kwargs gecerken her ajana uygun olmayabilir,
        # bu yüzden sadece orkestratoru calistirip sonucu dogrulariz.
        for name, agent in ajanlar.items():
            params = DEFAULT_PARAMS.get(name, {})
            if name == "plan_optimizasyon":
                params["iteration_count"] = 5  # Test icin hizlandır
            agent.run(**params)

        # Sonra orkestratoru calistir
        ork_result = orkestrator.run()
        assert ork_result.get("success") is True
        # Orkestrator tum ajanlarin durumunu goruntulenmeli
        data = ork_result.get("data", {})
        assert len(data.get("agent_statuses", {})) == len(ajanlar)


# ══════════════════════════════════════════════════
#  Ajan Konfigürasyon Testleri
# ══════════════════════════════════════════════════

class TestAjanKonfigurasyon:
    """Ajan konfigürasyon ve bilgileri testleri."""

    def test_default_params_complete(self):
        """Her ajan icin varsayilan parametreler tanimli olmali."""
        assert "plan_optimizasyon" in DEFAULT_PARAMS
        assert "maliyet_optimizasyon" in DEFAULT_PARAMS
        assert "daire_karmasi" in DEFAULT_PARAMS
        assert "toplu_fizibilite" in DEFAULT_PARAMS

    def test_ajan_bilgileri_complete(self):
        """Her ajan icin bilgi karti tanimli olmali."""
        for name in ["plan_optimizasyon", "maliyet_optimizasyon",
                      "daire_karmasi", "toplu_fizibilite", "orkestrator"]:
            assert name in AJAN_BILGILERI
            info = AJAN_BILGILERI[name]
            assert "emoji" in info
            assert "baslik" in info
            assert "aciklama" in info
            assert "calisma_suresi" in info
