"""
Ajan Kontrol Paneli — Streamlit sayfası.
Ajan durumu, başlat/durdur, sonuçlar ve orkestratör özeti.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from agents.agent_config import (
    create_agent_system, DEFAULT_PARAMS, AJAN_BILGILERI,
)
from agents.base_agent import BaseAgent


def init_agent_system():
    """Session state'te ajan sistemini başlat."""
    if "agent_system" not in st.session_state:
        orkestrator, ajanlar = create_agent_system()
        st.session_state.agent_system = {
            "orkestrator": orkestrator,
            "ajanlar": ajanlar,
        }
    return st.session_state.agent_system


def render_agent_dashboard():
    """Ajan kontrol paneli sayfasını render eder."""
    st.header("🤖 Ajan Kontrol Paneli")

    system = init_agent_system()
    orkestrator = system["orkestrator"]
    ajanlar = system["ajanlar"]

    # ═══ Üst Bölüm: Genel Durum ═══
    st.subheader("📊 Genel Durum")
    col1, col2, col3, col4 = st.columns(4)

    all_statuses = {name: agent.get_status() for name, agent in ajanlar.items()}
    all_statuses["orkestrator"] = orkestrator.get_status()

    completed = sum(1 for s in all_statuses.values() if s.get("last_status") == "completed")
    failed = sum(1 for s in all_statuses.values() if s.get("last_status") == "failed")
    never = sum(1 for s in all_statuses.values() if s.get("last_status") == "never_run")
    total_items = sum(s.get("last_items", 0) for s in all_statuses.values())

    col1.metric("Toplam Ajan", len(all_statuses))
    col2.metric("✅ Başarılı", completed)
    col3.metric("❌ Hata", failed)
    col4.metric("📦 Toplam Bulgu", total_items)

    # ═══ Toplu Çalıştırma ═══
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("🚀 Tüm Ajanları Çalıştır", type="primary", use_container_width=True):
            with st.spinner("Tüm ajanlar çalışıyor..."):
                results = {}
                progress = st.progress(0)
                ajan_list = list(ajanlar.items())

                for i, (name, agent) in enumerate(ajan_list):
                    st.toast(f"▶ {AJAN_BILGILERI.get(name, {}).get('baslik', name)} çalışıyor...")
                    params = DEFAULT_PARAMS.get(name, {})
                    result = agent.run(**params)
                    results[name] = result
                    progress.progress((i + 1) / (len(ajan_list) + 1))

                # Orkestratör
                st.toast("🧠 Orkestratör çalışıyor...")
                ork_result = orkestrator.run()
                results["orkestrator"] = ork_result
                progress.progress(1.0)

                st.session_state.last_agent_results = results
            st.success(f"✅ {len(results)} ajan tamamlandı!")
            st.rerun()

    with col_btn2:
        if st.button("🧠 Sadece Orkestratör", use_container_width=True):
            with st.spinner("Orkestratör çalışıyor..."):
                result = orkestrator.run()
                st.session_state.last_ork_result = result
            st.success("✅ Orkestratör tamamlandı!")
            st.rerun()

    # ═══ Ajan Kartları ═══
    st.markdown("---")
    st.subheader("🤖 Ajanlar")

    for name, agent in {**ajanlar, "orkestrator": orkestrator}.items():
        info = AJAN_BILGILERI.get(name, {})
        status = all_statuses.get(name, {})

        emoji = info.get("emoji", "🔧")
        baslik = info.get("baslik", name)
        aciklama = info.get("aciklama", "")
        sure = info.get("calisma_suresi", "?")

        last_status = status.get("last_status", "never_run")
        if last_status == "completed":
            status_badge = "✅"
        elif last_status == "failed":
            status_badge = "❌"
        elif last_status == "running":
            status_badge = "🔄"
        else:
            status_badge = "⏸️"

        with st.expander(f"{emoji} {baslik} {status_badge}", expanded=False):
            col_info, col_action = st.columns([3, 1])

            with col_info:
                st.markdown(f"**{aciklama}**")
                st.caption(f"Tahmini süre: {sure}")

                if last_status != "never_run":
                    st.markdown(
                        f"Son çalışma: **{status.get('last_run', '-')}** | "
                        f"Süre: **{status.get('last_duration', '-')}** | "
                        f"Bulgu: **{status.get('last_items', 0)}**"
                    )
                    if status.get("last_summary"):
                        st.info(status["last_summary"])
                    if status.get("last_error"):
                        st.error(f"Hata: {status['last_error']}")
                else:
                    st.caption("Henüz çalıştırılmadı")

            with col_action:
                if name != "orkestrator":
                    if st.button(f"▶ Çalıştır", key=f"run_{name}", use_container_width=True):
                        with st.spinner(f"{baslik} çalışıyor..."):
                            params = DEFAULT_PARAMS.get(name, {})
                            result = agent.run(**params)
                        st.success(f"✅ {baslik} tamamlandı!")
                        st.rerun()

    # ═══ Son Sonuçlar Detay ═══
    if "last_agent_results" in st.session_state:
        st.markdown("---")
        st.subheader("📋 Son Çalışma Sonuçları")

        results = st.session_state.last_agent_results

        # Orkestratör aksiyonları
        ork = results.get("orkestrator", {})
        ork_data = ork.get("data", {})
        aksiyonlar = ork_data.get("aksiyonlar", [])

        if aksiyonlar:
            st.markdown("### 🎯 Aksiyonlar")
            for aksiyon in aksiyonlar:
                oncelik = aksiyon.get("oncelik", "orta")
                icon = "🔴" if oncelik == "yüksek" else "🟡" if oncelik == "orta" else "🔵"
                st.markdown(f"{icon} **[{oncelik.upper()}]** {aksiyon['aksiyon']} _{aksiyon['kaynak']}_")

        # Ajan bazlı sonuçlar
        for name, result in results.items():
            if name == "orkestrator":
                continue
            info = AJAN_BILGILERI.get(name, {})
            data = result.get("data", {})

            if not data:
                continue

            with st.expander(f"{info.get('emoji', '')} {info.get('baslik', name)} — Detaylı Sonuç"):
                # Plan optimizasyon
                if name == "plan_optimizasyon" and "stats" in data:
                    stats = data["stats"]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Test Edilen", stats.get("total_tested", 0))
                    c2.metric("En İyi Puan", f"{stats.get('max_score', 0):.0f}/100")
                    c3.metric("Ortalama", f"{stats.get('avg_score', 0):.0f}/100")
                    c4.metric(">70 Puan", stats.get("above_70", 0))

                    if "top_plans" in data:
                        st.dataframe(pd.DataFrame(data["top_plans"]), hide_index=True, use_container_width=True)

                # Maliyet optimizasyon
                elif name == "maliyet_optimizasyon":
                    if "yapi_sistemleri" in data:
                        st.markdown("**Yapı Sistemi Karşılaştırması:**")
                        st.dataframe(pd.DataFrame(data["yapi_sistemleri"]), hide_index=True, use_container_width=True)
                    if "malzeme_senaryolari" in data:
                        st.markdown("**Malzeme Senaryoları:**")
                        st.dataframe(pd.DataFrame(data["malzeme_senaryolari"]), hide_index=True, use_container_width=True)

                # Daire karması
                elif name == "daire_karmasi":
                    for label, key in [("🏆 En Kârlı", "en_karli"), ("⚡ En Hızlı Satış", "en_hizli_satis"), ("⚖️ Dengeli", "dengeli")]:
                        s = data.get(key, {})
                        if s:
                            st.markdown(f"**{label}:** {s.get('label', '?')} — Kâr: %{s.get('kar_marji', 0):.1f} | Satış: {s.get('ort_satis_suresi_ay', 0):.0f} ay")

                    if "tum_senaryolar" in data:
                        df = pd.DataFrame(data["tum_senaryolar"][:10])
                        if not df.empty:
                            display_cols = [c for c in ["label", "kar_marji", "roi", "ort_satis_suresi_ay", "daire_sayisi"] if c in df.columns]
                            st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

                # Toplu fizibilite
                elif name == "toplu_fizibilite":
                    if "istatistik" in data:
                        ist = data["istatistik"]
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Analiz Edilen", ist.get("basarili", 0))
                        c2.metric("Kârlı Parsel", ist.get("karli", 0))
                        c3.metric("Ort. Kâr Marjı", f"%{ist.get('ort_kar_marji', 0)}")

                    if "sonuclar" in data:
                        df = pd.DataFrame(data["sonuclar"][:10])
                        if not df.empty:
                            display_cols = [c for c in ["isim", "alan", "kar_marji", "roi", "kar", "daire_sayisi"] if c in df.columns]
                            st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

    # ═══ Çalışma Geçmişi ═══
    st.markdown("---")
    st.subheader("📜 Çalışma Geçmişi")

    recent = BaseAgent.get_recent_runs(limit=20)
    if recent:
        df_hist = pd.DataFrame(recent)
        st.dataframe(df_hist, hide_index=True, use_container_width=True)
    else:
        st.caption("Henüz çalışma kaydı yok.")
