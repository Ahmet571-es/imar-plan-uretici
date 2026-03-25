"""
FAZ 7 Testleri — Otomasyon & Agent Sistemi.
Agent oluşturma, çalıştırma, orkestrasyon testleri.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.agent_config import create_agent_system, DEFAULT_PARAMS, AJAN_BILGILERI


@pytest.fixture
def agent_system():
    """Agent sistemi oluştur."""
    ork, ajanlar = create_agent_system()
    return ork, ajanlar


class TestAgentSistemOlusturma:
    """Agent sistemi oluşturma testleri."""

    def test_agent_system_creation(self, agent_system):
        ork, ajanlar = agent_system
        assert ork is not None
        assert len(ajanlar) == 4  # plan, maliyet, daire, toplu

    def test_orkestrator_register(self, agent_system):
        ork, ajanlar = agent_system
        assert len(ork.registered_agents) == 4

    def test_ajan_bilgileri_tamamlik(self):
        gerekli_ajanlar = ["plan_optimizasyon", "maliyet_optimizasyon", "daire_karmasi", "toplu_fizibilite", "orkestrator"]
        for ajan in gerekli_ajanlar:
            assert ajan in AJAN_BILGILERI, f"{ajan} AJAN_BILGILERI'nde bulunamadı"
            assert "emoji" in AJAN_BILGILERI[ajan]
            assert "baslik" in AJAN_BILGILERI[ajan]


class TestAjanCalistirma:
    """Tekil ajan çalıştırma testleri."""

    def test_plan_optimizasyon_run(self, agent_system):
        _, ajanlar = agent_system
        result = ajanlar["plan_optimizasyon"].run(**DEFAULT_PARAMS["plan_optimizasyon"])
        assert result["success"] is True
        assert result["items_found"] >= 0
        assert "summary" in result

    def test_maliyet_optimizasyon_run(self, agent_system):
        _, ajanlar = agent_system
        result = ajanlar["maliyet_optimizasyon"].run(**DEFAULT_PARAMS["maliyet_optimizasyon"])
        assert result["success"] is True
        assert "data" in result

    def test_daire_karmasi_run(self, agent_system):
        _, ajanlar = agent_system
        result = ajanlar["daire_karmasi"].run(**DEFAULT_PARAMS["daire_karmasi"])
        assert result["success"] is True
        assert result.get("data", {}).get("en_karli") is not None

    def test_toplu_fizibilite_run(self, agent_system):
        _, ajanlar = agent_system
        result = ajanlar["toplu_fizibilite"].run(**DEFAULT_PARAMS["toplu_fizibilite"])
        assert result["success"] is True


class TestOrkestrator:
    """Orkestratör testleri."""

    def test_orkestrator_run(self, agent_system):
        ork, _ = agent_system
        result = ork.run()
        assert result["success"] is True
        assert "summary" in result

    def test_orkestrator_aksiyonlar(self, agent_system):
        ork, ajanlar = agent_system
        # Önce bir ajan çalıştır
        ajanlar["maliyet_optimizasyon"].run(**DEFAULT_PARAMS["maliyet_optimizasyon"])
        result = ork.run()
        assert "data" in result
        assert "aksiyonlar" in result["data"]


class TestAgentDurum:
    """Agent durum ve mesajlaşma testleri."""

    def test_agent_status(self, agent_system):
        _, ajanlar = agent_system
        ajan = ajanlar["plan_optimizasyon"]
        status = ajan.get_status()
        assert isinstance(status, dict)

    def test_agent_message_send(self, agent_system):
        _, ajanlar = agent_system
        ajan = ajanlar["plan_optimizasyon"]
        # Private metod ile mesaj gönderme testi
        ajan._send_message("test", {"test": True})
        # Hata vermemesi yeterli

    def test_run_all_agents(self, agent_system):
        ork, _ = agent_system
        results = ork.run_all_agents(**DEFAULT_PARAMS.get("plan_optimizasyon", {}))
        assert isinstance(results, dict)
        assert "orkestrator" in results
