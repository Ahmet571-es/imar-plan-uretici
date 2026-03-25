"""
Sayfa modülleri: Mali Fizibilite, Deprem, Enerji, Gantt, Parsel Karşılaştırma.
"""

import streamlit as st
import pandas as pd
import numpy as np


def sayfa_fizibilite():
    """Sayfa 10 — Mali Fizibilite."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from analysis.cost_estimator import hesapla_maliyet
    from analysis.revenue_estimator import hesapla_gelir
    from analysis.feasibility import hesapla_fizibilite, duyarlilik_analizi, create_sensitivity_heatmap
    from config.cost_defaults import get_iller, MALIYET_DAGILIMI

    st.header("💰 Mali Fizibilite Analizi")

    hesap = st.session_state.get("hesaplama")
    imar = st.session_state.get("imar")
    bina = st.session_state.get("bina_programi")

    if hesap is None:
        st.warning("⚠️ Önce hesaplama adımını tamamlayın.")
        return

    # ── Maliyet Girişi ──
    st.subheader("📊 Maliyet Parametreleri")
    col1, col2, col3 = st.columns(3)
    with col1:
        il = st.selectbox("İl", get_iller(), index=1, key="fiz_il")
        kalite = st.selectbox("Yapı Kalitesi", ["ekonomik", "orta", "luks"],
                              format_func=lambda x: {"ekonomik": "Ekonomik", "orta": "Orta", "luks": "Lüks"}[x],
                              index=1, key="fiz_kalite")
    with col2:
        arsa_maliyet = st.number_input("Arsa Maliyeti (₺)", 0, 100_000_000, 5_000_000, step=500_000, key="fiz_arsa")
        otopark_tipi = st.selectbox("Otopark Tipi", ["acik", "kapali"],
                                    format_func=lambda x: "Açık" if x == "acik" else "Kapalı", key="fiz_otopark")
    with col3:
        m2_fiyat = st.number_input("m² Satış Fiyatı (₺)", 10_000, 200_000, 40_000, step=5_000, key="fiz_m2")
        cephe = st.selectbox("Ana Cephe", ["güney", "kuzey", "doğu", "batı"], key="fiz_cephe")

    if st.button("💰 Fizibilite Hesapla", type="primary", key="btn_fiz"):
        daire_sayisi = bina.toplam_daire if bina else imar.kat_adedi * 2

        # Maliyet
        maliyet = hesapla_maliyet(
            hesap.toplam_insaat_alani, il, kalite,
            arsa_maliyeti=arsa_maliyet,
            otopark_tipi=otopark_tipi,
            otopark_arac_sayisi=daire_sayisi,
        )

        # Gelir
        daire_listesi = []
        if bina:
            for d in bina.tum_daireler():
                daire_listesi.append({"daire_no": d.numara, "kat": d.kat, "tip": d.tip, "net_alan": d.net_alan})
        else:
            for i in range(daire_sayisi):
                daire_listesi.append({"daire_no": i+1, "kat": i // 2 + 1, "tip": "3+1", "net_alan": 95})

        gelir = hesapla_gelir(daire_listesi, m2_fiyat, imar.kat_adedi, cephe_yon=cephe)

        # Fizibilite
        satilanabilir = hesap.toplam_insaat_alani * 0.78
        fiz = hesapla_fizibilite(gelir.toplam_gelir, maliyet.toplam_maliyet, satilanabilir)

        st.session_state.fiz_result = {"maliyet": maliyet, "gelir": gelir, "fizibilite": fiz}

    if "fiz_result" in st.session_state:
        r = st.session_state.fiz_result
        maliyet, gelir, fiz = r["maliyet"], r["gelir"], r["fizibilite"]

        st.markdown("---")

        # Özet metrikler
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Toplam Maliyet", f"₺{maliyet.toplam_maliyet:,.0f}")
        col2.metric("Toplam Gelir", f"₺{gelir.toplam_gelir:,.0f}")
        color = "normal" if fiz.karli_mi else "inverse"
        col3.metric("Kâr / Zarar", f"₺{fiz.kar_zarar:,.0f}")
        col4.metric("Kâr Marjı", f"%{fiz.kar_marji:.1f}")

        if fiz.karli_mi:
            st.success(f"✅ Proje KÂRLI — ROI: %{fiz.roi:.1f}, Başabaş m²: ₺{fiz.basabas_m2_fiyat:,.0f}")
        else:
            st.error(f"❌ Proje ZARARDA — Minimum satış fiyatı: ₺{fiz.basabas_m2_fiyat:,.0f}/m² olmalı")

        # Detay tablolar
        tab_mal, tab_gel, tab_fiz = st.tabs(["Maliyet Detayı", "Gelir Detayı", "Kâr/Zarar"])
        with tab_mal:
            st.dataframe(pd.DataFrame({"Kalem": list(maliyet.to_dict().keys()), "Tutar": list(maliyet.to_dict().values())}),
                        hide_index=True, use_container_width=True)
            # Maliyet pasta grafiği
            fig_pie, ax = plt.subplots(figsize=(6, 4))
            labels = list(MALIYET_DAGILIMI.keys())
            values = [maliyet.kaba_insaat_maliyeti * v for v in MALIYET_DAGILIMI.values()]
            ax.pie(values, labels=[l[:20] for l in labels], autopct="%1.0f%%", textprops={"fontsize": 8})
            ax.set_title("Maliyet Dağılımı", fontweight="bold")
            st.pyplot(fig_pie)

        with tab_gel:
            if gelir.daire_gelirleri:
                df_gel = pd.DataFrame([{
                    "Daire": f"D{dg.daire_no}", "Kat": dg.kat, "Tip": dg.tip,
                    "Net m²": f"{dg.net_alan:.0f}", "m² Fiyat": f"₺{dg.m2_fiyat:,.0f}",
                    "Kat Primi": f"%{dg.kat_primi*100:+.0f}", "Satış": f"₺{dg.satis_fiyati:,.0f}",
                } for dg in gelir.daire_gelirleri])
                st.dataframe(df_gel, hide_index=True, use_container_width=True)

        with tab_fiz:
            st.dataframe(pd.DataFrame({"Kalem": list(fiz.to_dict().keys()), "Değer": list(fiz.to_dict().values())}),
                        hide_index=True, use_container_width=True)

        # Duyarlılık analizi
        st.markdown("---")
        st.subheader("📈 Duyarlılık Analizi")
        matris = duyarlilik_analizi(maliyet.toplam_maliyet, gelir.toplam_gelir)
        m_labels = [f"Maliyet {row[0]['maliyet_degisim']}" for row in matris]
        f_labels = [cell["fiyat_degisim"] for cell in matris[0]]
        fig_heat = create_sensitivity_heatmap(matris, m_labels, f_labels)
        st.pyplot(fig_heat)

        # Monte Carlo simülasyonu
        st.markdown("---")
        st.subheader("🎲 Monte Carlo Risk Simülasyonu")
        from analysis.feasibility import monte_carlo_simulasyonu, create_monte_carlo_chart

        col_mc1, col_mc2 = st.columns(2)
        with col_mc1:
            mc_maliyet_std = st.slider("Maliyet Belirsizliği (%)", 5, 30, 10, key="mc_mal_std") / 100
        with col_mc2:
            mc_gelir_std = st.slider("Gelir Belirsizliği (%)", 5, 40, 15, key="mc_gel_std") / 100

        if st.button("🎲 Simülasyon Çalıştır (5000 senaryo)", type="primary", key="btn_mc"):
            mc = monte_carlo_simulasyonu(
                maliyet.toplam_maliyet, gelir.toplam_gelir,
                maliyet_std=mc_maliyet_std, gelir_std=mc_gelir_std,
            )
            st.session_state.mc_result = mc

        if "mc_result" in st.session_state:
            mc = st.session_state.mc_result
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("Zarar Olasılığı", f"%{mc['zarar_olasiligi']:.1f}")
            col_r2.metric("Ortalama Kâr", f"₺{mc['kar_ortalama']:,.0f}")
            col_r3.metric("En Kötü Senaryo (P5)", f"₺{mc['percentiles']['p5']:,.0f}")
            col_r4.metric("En İyi Senaryo (P95)", f"₺{mc['percentiles']['p95']:,.0f}")

            fig_mc = create_monte_carlo_chart(mc)
            st.pyplot(fig_mc)


def sayfa_deprem():
    """Sayfa 11 — Deprem Risk Analizi."""
    from analysis.earthquake_risk import deprem_risk_analizi, ZEMIN_SINIFLARI

    st.header("🔬 Deprem Risk Analizi")

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Enlem", 36.0, 42.5, 39.93, step=0.01, key="dep_lat")
        lon = st.number_input("Boylam", 26.0, 45.0, 32.86, step=0.01, key="dep_lon")
    with col2:
        kat = st.number_input("Kat Sayısı", 1, 30, st.session_state.get("imar", type("",(),{"kat_adedi":4})).kat_adedi, key="dep_kat")
        zemin = st.selectbox("Zemin Sınıfı", list(ZEMIN_SINIFLARI.keys()),
                             format_func=lambda x: f"{x} — {ZEMIN_SINIFLARI[x]['aciklama']}", index=2, key="dep_zemin")

    if st.button("🔬 Deprem Analizi Yap", type="primary"):
        sonuc = deprem_risk_analizi(lat, lon, kat, zemin)
        st.session_state.deprem_result = sonuc

    if "deprem_result" in st.session_state:
        s = st.session_state.deprem_result
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Seviyesi", s.risk_seviyesi)
        col2.metric("Ss (Kısa Periyot)", f"{s.ss:.3f}")
        col3.metric("S1 (1sn Periyot)", f"{s.s1:.3f}")

        st.subheader("🏗️ Taşıyıcı Sistem Önerisi")
        st.info(f"**{s.tasiyici_sistem_onerisi}**\n\nKolon Grid: {s.kolon_grid_onerisi}\n\nPerde: {s.perde_onerisi}")

        st.subheader("📋 Detaylar")
        df = pd.DataFrame({"Parametre": list(s.to_dict().keys()), "Değer": list(s.to_dict().values())})
        st.dataframe(df, hide_index=True, use_container_width=True)

        for d in s.detaylar:
            st.markdown(f"  {d}")


def sayfa_enerji():
    """Sayfa 12 — Enerji Performans Tahmini."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from analysis.energy_performance import enerji_performans_hesapla, ENERJI_SINIFLARI

    st.header("⚡ Enerji Performans Tahmini")

    hesap = st.session_state.get("hesaplama")
    imar = st.session_state.get("imar")

    col1, col2 = st.columns(2)
    with col1:
        duvar_yal = st.selectbox("Duvar Yalıtımı", ["duvar_5cm_eps", "duvar_8cm_eps", "duvar_10cm_eps", "duvar_12cm_xps"],
                                 format_func=lambda x: x.replace("duvar_", "").replace("_", " ").upper(), index=1, key="enj_duvar")
        pencere = st.selectbox("Pencere Tipi", ["tek_cam", "cift_cam", "isicam", "low_e"],
                               format_func=lambda x: x.replace("_", " ").title(), index=2, key="enj_pencere")
    with col2:
        cati_yal = st.checkbox("Çatı Yalıtımı", True, key="enj_cati")
        isitma = st.selectbox("Isıtma Sistemi", ["dogalgaz_kombi", "merkezi", "isi_pompasi"],
                              format_func=lambda x: {"dogalgaz_kombi": "Doğalgaz Kombi", "merkezi": "Merkezi Sistem", "isi_pompasi": "Isı Pompası"}[x], key="enj_isitma")
        pencere_oran = st.slider("Pencere/Duvar Oranı", 0.15, 0.50, 0.25, 0.05, key="enj_pw")

    if st.button("⚡ Enerji Hesapla", type="primary"):
        toplam_alan = hesap.toplam_insaat_alani if hesap else 850
        kat = imar.kat_adedi if imar else 4
        sonuc = enerji_performans_hesapla(toplam_alan, kat, duvar_yal, pencere, cati_yal, pencere_oran, isitma)
        st.session_state.enerji_result = sonuc

    if "enerji_result" in st.session_state:
        s = st.session_state.enerji_result
        sinif_info = ENERJI_SINIFLARI.get(s.enerji_sinifi, {})

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Enerji Sınıfı", f"{s.enerji_sinifi} — {sinif_info.get('aciklama', '')}")
        col2.metric("Yıllık Isıtma", f"{s.yillik_isitma_kwh_m2:.0f} kWh/m²·yıl")
        col3.metric("Yıllık Maliyet", f"₺{s.yillik_enerji_maliyeti:,.0f}")

        # Enerji sınıfı göstergesi
        st.subheader("📊 Enerji Sınıfı Göstergesi")
        fig_e, ax_e = plt.subplots(figsize=(10, 2))
        siniflar = list(ENERJI_SINIFLARI.keys())
        renkler = [ENERJI_SINIFLARI[s_]["renk"] for s_ in siniflar]
        for i, (sinif, renk) in enumerate(zip(siniflar, renkler)):
            ax_e.barh(0, 1, left=i, color=renk, height=0.6)
            ax_e.text(i + 0.5, 0, sinif, ha="center", va="center", fontsize=14, fontweight="bold",
                     color="white" if sinif in ("E", "F", "G") else "black")
        idx = siniflar.index(s.enerji_sinifi) if s.enerji_sinifi in siniflar else 2
        ax_e.annotate("▼", xy=(idx + 0.5, 0.4), fontsize=20, ha="center", color="black")
        ax_e.set_xlim(0, 7)
        ax_e.set_ylim(-0.5, 0.8)
        ax_e.axis("off")
        ax_e.set_title("Bina Enerji Sınıfı", fontweight="bold")
        st.pyplot(fig_e)

        st.subheader("💡 Öneriler")
        for o in s.oneriler:
            st.markdown(f"  {o}")

        df = pd.DataFrame({"Parametre": list(s.to_dict().keys()), "Değer": list(s.to_dict().values())})
        st.dataframe(df, hide_index=True, use_container_width=True)


def sayfa_gantt():
    """Sayfa 13 — İnşaat Süresi (Gantt)."""
    from analysis.construction_timeline import hesapla_sure, create_gantt_chart
    from datetime import datetime

    st.header("📅 İnşaat Süresi Tahmini")

    imar = st.session_state.get("imar")

    col1, col2, col3 = st.columns(3)
    with col1:
        kat = st.number_input("Kat Sayısı", 1, 30, imar.kat_adedi if imar else 4, key="gantt_kat")
    with col2:
        bodrum = st.checkbox("Bodrum Kat", False, key="gantt_bodrum")
    with col3:
        baslangic = st.date_input("Başlangıç Tarihi", datetime.now(), key="gantt_tarih")

    if st.button("📅 Süre Hesapla", type="primary"):
        sonuc = hesapla_sure(kat, bodrum, datetime.combine(baslangic, datetime.min.time()))
        st.session_state.gantt_result = sonuc

    if "gantt_result" in st.session_state:
        s = st.session_state.gantt_result
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Süre", f"{s.toplam_sure_ay:.0f} ay")
        col2.metric("Tahmini Bitiş", s.tahmini_bitis)
        col3.metric("İş Kalemi", f"{len(s.is_kalemleri)}")

        fig = create_gantt_chart(s)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 İş Kalemleri")
        df = pd.DataFrame(s.is_kalemleri)
        df["kritik_yol"] = df["kritik_yol"].map({True: "🔴 Evet", False: "Hayır"})
        st.dataframe(df, hide_index=True, use_container_width=True)


def sayfa_karsilastir():
    """Sayfa 14 — Parsel Karşılaştırma."""
    from analysis.parcel_comparison import ParselOzet, karsilastirma_tablosu, create_radar_chart, create_bar_comparison

    st.header("🔄 Parsel Karşılaştırma")

    st.info("2-3 parselin fizibilite karşılaştırması. Parametreleri girin ve karşılaştırın.")

    parsel_count = st.radio("Parsel Sayısı", [2, 3], horizontal=True, key="kars_count")
    parseller = []

    cols = st.columns(parsel_count)
    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Parsel {i+1}")
            isim = st.text_input("İsim", f"Parsel {chr(65+i)}", key=f"kars_isim_{i}")
            alan = st.number_input("Alan (m²)", 100.0, 5000.0, 600.0 + i*100, key=f"kars_alan_{i}")
            taks = st.number_input("TAKS", 0.1, 1.0, 0.35, key=f"kars_taks_{i}")
            kaks = st.number_input("KAKS", 0.1, 5.0, 1.40, key=f"kars_kaks_{i}")
            maliyet = st.number_input("Tahmini Maliyet (M₺)", 1.0, 200.0, 25.0 + i*5, key=f"kars_mal_{i}") * 1_000_000
            satis = st.number_input("Tahmini Satış (M₺)", 1.0, 300.0, 32.0 + i*5, key=f"kars_sat_{i}") * 1_000_000

            kar = satis - maliyet
            marji = (kar / satis * 100) if satis > 0 else 0

            parseller.append(ParselOzet(
                isim=isim, alan=alan, taks=taks, kaks=kaks,
                toplam_insaat=alan * kaks,
                tahmini_maliyet=maliyet, tahmini_satis=satis,
                kar_marji=marji, roi=(kar / maliyet * 100) if maliyet > 0 else 0,
                deprem_riski="🟡 Orta", enerji_sinifi="B",
                insaat_suresi_ay=14 + i*2, gunes_skoru=7 - i,
            ))

    if st.button("🔄 Karşılaştır", type="primary"):
        st.markdown("---")

        st.subheader("📊 Karşılaştırma Tablosu")
        rows = karsilastirma_tablosu(parseller)
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎯 Radar Analiz")
            fig_radar = create_radar_chart(parseller)
            st.plotly_chart(fig_radar, use_container_width=True)
        with col2:
            st.subheader("📊 Kârlılık")
            fig_bar = create_bar_comparison(parseller)
            st.plotly_chart(fig_bar, use_container_width=True)
