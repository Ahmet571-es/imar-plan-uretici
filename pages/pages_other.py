"""
Sayfa modülleri: Konum, Hukuk/Belge, Rapor, Fırsat/Piyasa.
"""

import streamlit as st
import pandas as pd


def sayfa_konum():
    """Sayfa 2 — Konum & Çevre Analizi + Güneş."""
    from analysis.sun_analysis import analyze_sun, create_sun_chart

    st.header("🗺️ Konum & Çevre Analizi")

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Enlem", 36.0, 42.5, 39.93, step=0.01, key="loc_lat")
        lon = st.number_input("Boylam", 26.0, 45.0, 32.86, step=0.01, key="loc_lon")

    with col2:
        st.markdown("### 📍 Hızlı Şehir Seçimi")
        sehirler = {"Ankara": (39.93, 32.86), "İstanbul": (41.01, 28.97), "İzmir": (38.42, 27.14),
                    "Antalya": (36.89, 30.71), "Kütahya": (39.42, 29.98), "Bursa": (40.19, 29.06)}
        secim = st.selectbox("Şehir", list(sehirler.keys()), key="loc_sehir")
        if st.button("Koordinatları Uygula", key="loc_apply"):
            st.session_state.loc_lat = sehirler[secim][0]
            st.session_state.loc_lon = sehirler[secim][1]
            st.rerun()

    # Harita
    st.subheader("🗺️ Harita")
    try:
        from map.location_picker import create_parcel_map
        m = create_parcel_map(lat, lon)
        if m:
            from streamlit_folium import st_folium
            st_folium(m, width=None, height=450)
        else:
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
    except ImportError:
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
        st.caption("Detaylı harita için: pip install folium streamlit-folium")

    # Güneş analizi
    st.markdown("---")
    st.subheader("☀️ Güneş Analizi")

    if st.button("☀️ Güneş Analizi Yap", type="primary", key="btn_sun"):
        sonuc = analyze_sun(lat, lon)
        st.session_state.sun_result = sonuc

    if "sun_result" in st.session_state:
        s = st.session_state.sun_result
        col1, col2, col3 = st.columns(3)
        col1.metric("En İyi Cephe", s.best_facade.title())
        col2.metric("Yıllık Güneş", f"{s.annual_solar_hours:.0f} saat")
        col3.metric("Yaz Güneş Açısı", f"{s.summer_solstice_angle:.1f}°")

        fig = create_sun_chart(s)
        st.pyplot(fig)

        st.subheader("💡 Öneriler")
        for r in s.recommendations:
            st.markdown(f"  {r}")


def sayfa_irtifak():
    """Sayfa 15 — Kat İrtifakı / Mülkiyet Taslağı."""
    from legal.kat_irtifaki import olustur_kat_irtifaki, taslak_to_text

    st.header("📜 Kat İrtifakı / Mülkiyet Belge Taslağı")

    bina = st.session_state.get("bina_programi")
    parsel = st.session_state.get("parsel")
    hesap = st.session_state.get("hesaplama")

    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı", "Konut Projesi", key="irt_adi")
        il = st.text_input("İl", "Ankara", key="irt_il")
        ilce = st.text_input("İlçe", "", key="irt_ilce")
    with col2:
        ada = st.text_input("Ada No", "", key="irt_ada")
        parsel_no = st.text_input("Parsel No", "", key="irt_parsel")

    if st.button("📜 Taslak Oluştur", type="primary"):
        daireler = []
        if bina:
            for d in bina.tum_daireler():
                daireler.append({
                    "daire_no": d.numara, "kat": d.kat, "tip": d.tip,
                    "brut_alan": d.brut_alan, "net_alan": d.net_alan,
                    "eklentiler": ["balkon"],
                })
        else:
            for i in range(8):
                daireler.append({"daire_no": i+1, "kat": i//2+1, "tip": "3+1", "brut_alan": 95, "net_alan": 78})

        taslak = olustur_kat_irtifaki(
            daireler, proje_adi, il, ilce, ada, parsel_no,
            parsel.alan if parsel else 600,
            hesap.toplam_insaat_alani if hesap else 850,
        )
        st.session_state.irtifak_result = taslak

    if "irtifak_result" in st.session_state:
        taslak = st.session_state.irtifak_result
        st.markdown("---")
        st.warning(taslak.uyari)

        st.subheader("📋 Bağımsız Bölüm Listesi")
        df = pd.DataFrame([{
            "No": bb.bolum_no, "Kat": bb.kat, "Tip": bb.daire_tipi,
            "Brüt m²": bb.brut_alan, "Net m²": bb.net_alan,
            "Arsa Payı": f"{bb.arsa_payi_pay}/{bb.arsa_payi_payda}",
        } for bb in taslak.bagimsiz_bolumler])
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.subheader("🏢 Ortak Alanlar")
        for i, oa in enumerate(taslak.ortak_alanlar, 1):
            st.markdown(f"  {i}. {oa}")

        text = taslak_to_text(taslak)
        st.download_button("📥 Taslağı İndir (TXT)", text, "kat_irtifaki_taslak.txt", "text/plain")


def sayfa_ruhsat():
    """Sayfa 16 — Yapı Ruhsatı Paketi."""
    from legal.ruhsat_paketi import RUHSAT_KONTROL_LISTESI, olustur_alan_hesap, alan_hesap_to_text, gerekli_yetki_sinifi, YETKI_SINIFLARI

    st.header("🏛️ Yapı Ruhsatı Başvuru Paketi")

    hesap = st.session_state.get("hesaplama")
    imar = st.session_state.get("imar")

    toplam_insaat = hesap.toplam_insaat_alani if hesap else 850
    yetki = gerekli_yetki_sinifi(toplam_insaat)

    st.info(f"📐 Toplam inşaat: {toplam_insaat:,.0f} m² → Gerekli müteahhit yetki sınıfı: **{yetki}** ({YETKI_SINIFLARI[yetki]})")

    # Kontrol listesi
    st.subheader("✅ Başvuru Evrak Kontrol Listesi")
    for item in RUHSAT_KONTROL_LISTESI:
        col1, col2, col3 = st.columns([0.5, 4, 1])
        with col1:
            checked = st.checkbox("", key=f"ruhsat_{item['belge'][:20]}")
        with col2:
            zorunlu = "🔴 Zorunlu" if item["zorunlu"] else "🟡 Opsiyonel"
            st.markdown(f"**{item['belge']}** {zorunlu}")
        with col3:
            if item["hazirlanabilir"]:
                st.markdown("✅ Otomatik")
            else:
                st.markdown("📝 Manuel")

    # Alan hesap tablosu
    st.markdown("---")
    st.subheader("📊 Alan Hesap Tablosu")
    if hesap and imar:
        bina = st.session_state.get("bina_programi")
        daireler = []
        if bina:
            for d in bina.tum_daireler():
                daireler.append({"daire_no": d.numara, "tip": d.tip, "brut_alan": d.brut_alan, "net_alan": d.net_alan})
        tablo = olustur_alan_hesap(
            hesap.parsel_alani, imar.taks, imar.kaks,
            hesap.max_taban_alani, hesap.toplam_insaat_alani,
            imar.kat_adedi, daireler, bina.toplam_daire if bina else 8,
        )
        text = alan_hesap_to_text(tablo)
        st.code(text, language="text")
        st.download_button("📥 Alan Hesabını İndir", text, "alan_hesap_tablosu.txt", "text/plain")
    else:
        st.warning("⚠️ Önce hesaplama adımını tamamlayın.")


def sayfa_muteahhit():
    """Sayfa 17 — Müteahhit Eşleştirme."""
    from legal.ruhsat_paketi import YETKI_SINIFLARI, gerekli_yetki_sinifi

    st.header("👷 Müteahhit / Taşeron Eşleştirme")

    hesap = st.session_state.get("hesaplama")
    toplam = hesap.toplam_insaat_alani if hesap else 850
    yetki = gerekli_yetki_sinifi(toplam)

    st.info(f"Bu proje için minimum **{yetki} sınıfı** yetki belgesi gerekli.")

    st.subheader("📋 Yetki Belgesi Sınıfları")
    df = pd.DataFrame([{"Sınıf": k, "Açıklama": v} for k, v in YETKI_SINIFLARI.items()])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.subheader("🔍 Müteahhit Arama Kaynakları")
    st.markdown("""
    - **YAMB** (Yapı Müteahhitleri Bilgi Sistemi): [yamb.csb.gov.tr](https://yamb.csb.gov.tr/)
    - **Ticaret Odası** kayıtları
    - **Google Maps**: "inşaat firması" + ilçe araması
    """)
    st.caption("Otomatik müteahhit eşleştirme için YAMB API entegrasyonu sonraki fazda eklenecektir.")


def sayfa_rapor():
    """Sayfa 18 — Rapor & Dışa Aktarma."""
    from export.feasibility_report import olustur_fizibilite_pdf
    import os

    st.header("📄 Rapor & Dışa Aktarma")

    hesap = st.session_state.get("hesaplama")
    imar = st.session_state.get("imar")
    parsel = st.session_state.get("parsel")
    fiz = st.session_state.get("fiz_result")
    deprem = st.session_state.get("deprem_result")
    enerji = st.session_state.get("enerji_result")

    st.subheader("📊 Mevcut Veriler")
    data_status = {
        "Parsel": "✅" if parsel else "❌",
        "İmar Hesaplama": "✅" if hesap else "❌",
        "Mali Fizibilite": "✅" if fiz else "❌",
        "Deprem Analizi": "✅" if deprem else "❌",
        "Enerji Performansı": "✅" if enerji else "❌",
    }
    for k, v in data_status.items():
        st.markdown(f"  {v} {k}")

    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı", "Konut Fizibilite Raporu", key="rapor_adi")
        il = st.text_input("İl", "Ankara", key="rapor_il")
    with col2:
        ilce = st.text_input("İlçe", "", key="rapor_ilce")
        ada = st.text_input("Ada/Parsel", "", key="rapor_ada")

    if st.button("📄 PDF Rapor Oluştur", type="primary"):
        with st.spinner("PDF oluşturuluyor..."):
            proje_bilgi = {
                "proje_adi": proje_adi, "il": il, "ilce": ilce, "ada": ada,
                "parsel_alani": f"{parsel.alan:.1f} m²" if parsel else "-",
                "kat_sayisi": imar.kat_adedi if imar else "-",
                "toplam_insaat": f"{hesap.toplam_insaat_alani:.1f} m²" if hesap else "-",
            }
            pdf_path = olustur_fizibilite_pdf(
                proje_bilgileri=proje_bilgi,
                hesaplama=hesap.ozet_dict() if hesap else {},
                maliyet=fiz["maliyet"].to_dict() if fiz else {},
                gelir=fiz["gelir"].to_dict() if fiz else {},
                fizibilite=fiz["fizibilite"].to_dict() if fiz else {},
                deprem=deprem.to_dict() if deprem else None,
                enerji=enerji.to_dict() if enerji else None,
                output_path="/tmp/fizibilite_raporu.pdf",
            )

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📥 PDF İndir", f, "fizibilite_raporu.pdf", "application/pdf")
            st.success("✅ PDF rapor oluşturuldu!")
        else:
            st.error("❌ PDF oluşturulamadı. reportlab kurulu olduğundan emin olun.")


def sayfa_firsat():
    """Sayfa 24 — Fırsat Merkezi (Ajan sonuçlarından)."""
    from agents.base_agent import BaseAgent

    st.header("🔍 Fırsat Merkezi")

    results = st.session_state.get("last_agent_results", {})

    if not results:
        st.info("Henüz ajan sonucu yok. Ajan Kontrol Paneli'nden ajanları çalıştırın.")
        if st.button("🤖 Ajan Paneline Git"):
            st.session_state.aktif_sayfa = "23_ajan_panel"
            st.rerun()
        return

    # Toplu fizibilite sonuçları
    toplu = results.get("toplu_fizibilite", {})
    toplu_data = toplu.get("data", {})
    sonuclar = toplu_data.get("sonuclar", [])

    if sonuclar:
        st.subheader("📊 Parsel Fırsatları (Kârlılık Sırası)")
        df = pd.DataFrame(sonuclar)
        if "hata" in df.columns:
            df = df[df["hata"].isna() | (df["hata"] == "")]
        display_cols = [c for c in ["isim", "alan", "kar_marji", "roi", "kar", "toplam_insaat", "daire_sayisi"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].head(10), hide_index=True, use_container_width=True)

    # Daire karması sonuçları
    karma = results.get("daire_karmasi", {})
    karma_data = karma.get("data", {})
    if karma_data:
        st.markdown("---")
        st.subheader("🏠 En İyi Daire Karması Önerileri")
        for label, key in [("🏆 En Kârlı", "en_karli"), ("⚡ En Hızlı Satış", "en_hizli_satis"), ("⚖️ Dengeli", "dengeli")]:
            s = karma_data.get(key, {})
            if s:
                st.markdown(f"**{label}:** {s.get('label', '?')} — Kâr: %{s.get('kar_marji', 0):.1f} | ROI: %{s.get('roi', 0):.1f} | Satış: {s.get('ort_satis_suresi_ay', 0):.0f} ay")

    # Maliyet optimizasyon
    maliyet_opt = results.get("maliyet_optimizasyon", {})
    maliyet_data = maliyet_opt.get("data", {})
    if maliyet_data:
        st.markdown("---")
        st.subheader("💰 Yapı Sistemi Önerileri")
        yapi = maliyet_data.get("yapi_sistemleri", [])
        if yapi:
            st.dataframe(pd.DataFrame(yapi), hide_index=True, use_container_width=True)


def sayfa_piyasa():
    """Sayfa 25 — Piyasa İstihbarat."""
    st.header("📈 Piyasa İstihbarat")

    results = st.session_state.get("last_agent_results", {})

    if not results:
        st.info("Piyasa verileri için ajanları çalıştırın.")
        return

    # Plan optimizasyon istatistikleri
    plan_opt = results.get("plan_optimizasyon", {})
    plan_data = plan_opt.get("data", {})
    if plan_data and "stats" in plan_data:
        st.subheader("📐 Plan Kalite İstatistikleri")
        stats = plan_data["stats"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Test Edilen", stats.get("total_tested", 0))
        col2.metric("En İyi Puan", f"{stats.get('max_score', 0):.0f}/100")
        col3.metric("Ortalama", f"{stats.get('avg_score', 0):.0f}/100")
        col4.metric(">70 Puan", stats.get("above_70", 0))

    # Orkestratör aksiyonları
    ork = results.get("orkestrator", {})
    aksiyonlar = ork.get("data", {}).get("aksiyonlar", [])
    if aksiyonlar:
        st.markdown("---")
        st.subheader("🎯 Güncel Aksiyonlar")
        for a in aksiyonlar:
            icon = "🔴" if a["oncelik"] == "yüksek" else "🟡" if a["oncelik"] == "orta" else "🔵"
            st.markdown(f"{icon} **[{a['oncelik'].upper()}]** {a['aksiyon']}")

    st.markdown("---")
    st.caption("ℹ️ Canlı piyasa verileri (Sahibinden, TCMB, TÜİK) FAZ 9'da eklenecektir.")
