"""
Sayfa modülleri: Plan Üretimi, AI Tefriş, 3D Görselleştirme, Render.
"""

import streamlit as st
import pandas as pd
import numpy as np


def sayfa_plan():
    """Sayfa 6 — Kat Planı Üretimi (Profesyonel + Dual AI)."""
    from core.floor_plan_generator import generate_professional_plan, generate_multiple_plans
    from core.plan_scorer import score_plan, FloorPlan
    from drawing.plan_renderer_matplotlib import render_floor_plan, render_plan_comparison

    st.header("📋 Kat Planı Üretimi")

    if st.session_state.get("hesaplama") is None:
        st.warning("⚠️ Önce hesaplama adımını tamamlayın. Soldaki menüden **[4] Hesaplama Sonuçları** sayfasına gidin.")
        return

    st.markdown("""
    <div style="background:#f0f7ff; border-left:3px solid #1E88E5; padding:10px 14px; border-radius:4px; margin:8px 0; font-size:14px;">
    <b>Bu adımda ne yapacaksınız?</b> Daire tipi ve g\u00fcne\u015f y\u00f6n\u00fcn\u00fc se\u00e7in, ard\u0131ndan plan \u00fcretim butonuna t\u0131klay\u0131n.
    Sistem birden fazla alternatif plan \u00fcretir ve puanlar. <b>Profesyonel \u00dcretim</b> sekmesi API key olmadan \u00e7al\u0131\u015f\u0131r.
    <b>AI Destekli</b> sekmesi Claude veya Grok API ile daha detayl\u0131 planlar \u00fcretir.
    </div>
    """, unsafe_allow_html=True)

    hesap = st.session_state.hesaplama
    imar = st.session_state.imar
    bina = st.session_state.get("bina_programi")

    # Yapılaşma alanı boyutları
    from utils.geometry_helpers import polygon_bounds_boyutlar
    if hesap.cekme_polygonu:
        bw, bh = polygon_bounds_boyutlar(hesap.cekme_polygonu)
        bounds = hesap.cekme_polygonu.bounds
        ox, oy = bounds[0], bounds[1]
    else:
        bw, bh = 16.0, 12.0
        ox, oy = 0.0, 0.0

    st.info(f"📐 Yapılaşma alanı: {bw:.1f} × {bh:.1f} m | Kat başı net: {hesap.kat_basi_net_alan:.1f} m²")

    col1, col2 = st.columns(2)
    with col1:
        daire_tipi = st.selectbox("Daire Tipi", ["1+1", "2+1", "3+1", "4+1"], index=2, key="plan_tip")
        sun_dir = st.selectbox("Güneş Yönü", ["south", "north", "east", "west"],
                               format_func=lambda x: {"south": "Güney", "north": "Kuzey", "east": "Doğu", "west": "Batı"}[x],
                               key="plan_sun")
    with col2:
        plan_sayisi = st.slider("Alternatif Sayısı", 2, 4, 3, key="plan_count")
        target_alan = st.number_input("Hedef Daire Alanı (m²)",
                                       50.0, 250.0,
                                       hesap.kat_basi_net_alan / 2,
                                       step=5.0, key="plan_target")

    # Oda programını hazırla
    room_program = None
    if bina and bina.katlar and bina.katlar[0].daireler:
        d = bina.katlar[0].daireler[0]
        room_program = [{"isim": o.isim, "tip": o.tip, "m2": o.m2} for o in d.odalar]

    tab_pro, tab_ai = st.tabs(["📐 Profesyonel Üretim", "🤖 AI Destekli Üretim"])

    with tab_pro:
        if st.button("📐 Profesyonel Plan Üret", type="primary", key="btn_gen_pro"):
            with st.spinner(f"{plan_sayisi * 3} varyasyon deneniyor, en iyi {plan_sayisi} seçiliyor..."):
                plans = generate_multiple_plans(
                    bw, bh, ox, oy,
                    room_program=room_program,
                    apartment_type=daire_tipi,
                    target_area=target_alan,
                    sun_direction=sun_dir,
                    plan_count=plan_sayisi,
                )

                if plans:
                    st.session_state.generated_plans = [
                        {"plan": p["floor_plan"], "score": p["score"], "reasoning": p["reasoning"]}
                        for p in plans
                    ]
                else:
                    st.error("Plan üretilemedi.")

    with tab_ai:
        claude_key = st.session_state.get("claude_api_key", "")
        grok_key = st.session_state.get("grok_api_key", "")

        if not claude_key and not grok_key:
            st.info("ℹ️ AI destekli plan üretimi için sidebar'dan API key girin. Profesyonel Üretim sekmesi API key olmadan çalışır.")
        else:
            iteration = st.slider("İterasyon Sayısı", 1, 3, 1, key="plan_iter")

            if st.button("🤖 AI Plan Üret", type="primary", key="btn_gen_ai"):
                with st.spinner("Dual AI planları üretiyor..."):
                    coords = list(hesap.cekme_polygonu.exterior.coords) if hesap.cekme_polygonu else [(ox,oy),(ox+bw,oy),(ox+bw,oy+bh),(ox,oy+bh)]
                    apt_program = {"tip": daire_tipi, "brut_alan": target_alan, "odalar": room_program or []}

                    from ai.dual_ai_engine import generate_dual_ai_plans
                    from dataset.dataset_rules import ROOM_SIZE_STATS
                    result = generate_dual_ai_plans(
                        buildable_polygon_coords=coords,
                        apartment_program=apt_program,
                        dataset_rules=ROOM_SIZE_STATS,
                        sun_best_direction=sun_dir,
                        claude_api_key=claude_key,
                        grok_api_key=grok_key,
                        max_iterations=iteration,
                    )
                    if result.best_plans:
                        st.session_state.generated_plans = [
                            {"plan": p.plan, "score": p.score, "reasoning": p.reasoning}
                            for p in result.best_plans
                        ]
                    else:
                        st.warning("AI plan üretemedi, profesyonel modda üretiliyor...")
                        plans = generate_multiple_plans(bw, bh, ox, oy, room_program, daire_tipi, target_alan, sun_dir, plan_sayisi)
                        st.session_state.generated_plans = [
                            {"plan": p["floor_plan"], "score": p["score"], "reasoning": p["reasoning"]}
                            for p in plans
                        ]

    # ── Plan gösterimi ──
    if "generated_plans" in st.session_state and st.session_state.generated_plans:
        plans = st.session_state.generated_plans
        st.markdown("---")
        st.subheader(f"🏗️ {len(plans)} Alternatif Plan")

        tabs = st.tabs([f"Plan {i+1} ({p['score'].total:.0f} puan)" for i, p in enumerate(plans)])
        for i, (tab, plan_data) in enumerate(zip(tabs, plans)):
            with tab:
                col_plan, col_score = st.columns([2, 1])
                with col_plan:
                    fig = render_floor_plan(plan_data["plan"], title=f"Alternatif {i+1}")
                    st.pyplot(fig)
                with col_score:
                    st.markdown("### 📊 Puan Kartı")
                    score_dict = plan_data["score"].to_dict()
                    for k, v in score_dict.items():
                        if k == "TOPLAM":
                            st.metric("TOPLAM", v)
                        else:
                            st.text(f"{k}: {v}")

                    # Derinleştirilmiş analiz verileri
                    sc = plan_data["score"]
                    if hasattr(sc, "mahremiyet_puani") and sc.mahremiyet_puani > 0:
                        st.markdown("---")
                        st.markdown("**Ek Analizler:**")
                        st.text(f"Mahremiyet: {sc.mahremiyet_puani:.0f}/100")
                        st.text(f"Fonksiyonel Bölge: {sc.fonksiyonel_bolge_puani:.0f}/100")
                        st.text(f"Min. Boyut Uyumu: {sc.min_boyut_uyumu:.0f}/100")

                    if hasattr(sc, "alan_dagilim_analizi") and sc.alan_dagilim_analizi:
                        with st.expander("Alan Dağılımı"):
                            for k2, v2 in sc.alan_dagilim_analizi.items():
                                st.text(f"{k2}: {v2}")

                    if hasattr(sc, "genel_degerlendirme") and sc.genel_degerlendirme:
                        st.success(f"📝 {sc.genel_degerlendirme}")

                    if plan_data.get("reasoning"):
                        st.info(f"💬 {plan_data['reasoning']}")

                # Oda listesi tablosu
                if plan_data["plan"].rooms:
                    st.markdown("**Oda Detayları:**")
                    import pandas as pd
                    df = pd.DataFrame([{
                        "Oda": r.name, "Boyut": f"{r.width:.1f}×{r.height:.1f}m",
                        "Alan": f"{r.area:.1f} m²",
                        "Min Kenar": f"{r.min_dimension:.2f}m",
                        "Cephe": r.facing_direction or "iç",
                        "Dış Duvar": "✅" if r.has_exterior_wall else "—",
                    } for r in plan_data["plan"].rooms])
                    st.dataframe(df, hide_index=True, use_container_width=True)

                    # Güneş detayı
                    if hasattr(sc, "gunes_detay") and sc.gunes_detay:
                        with st.expander("☀️ Güneş Optimizasyonu Detayı"):
                            for oda_adi, g_info in sc.gunes_detay.items():
                                st.text(f"{oda_adi}: {g_info['yon']} yönü → {g_info['puan']}/100 (ideal: {g_info['ideal_yon']})")

                if st.button(f"✅ Plan {i+1}'i Seç", key=f"select_plan_{i}"):
                    st.session_state.selected_plan = plan_data
                    st.success(f"Plan {i+1} seçildi!")

        if len(plans) >= 2:
            st.markdown("---")
            st.subheader("📊 Yan Yana Karşılaştırma")
            fig_comp = render_plan_comparison(
                [p["plan"] for p in plans],
                [f"Alt. {i+1} ({p['score'].total:.0f}p)" for i, p in enumerate(plans)]
            )
            st.pyplot(fig_comp)


def sayfa_ai_tefris():
    """Sayfa 7 — AI İyileştirme & Tefriş."""
    from core.furniture_placer import place_furniture
    from drawing.plan_renderer_matplotlib import render_floor_plan

    st.header("🤖 AI İyileştirme & Mobilya Yerleştirme")

    st.markdown("""
    <div style="background:#f0f7ff; border-left:3px solid #1E88E5; padding:10px 14px; border-radius:4px; margin:8px 0; font-size:14px;">
    <b>Bu adımda ne yapacaksınız?</b> Seçtiğiniz kat planına otomatik mobilya yerleştirme yapabilirsiniz.
    Salon, yatak odası, mutfak gibi her odaya uygun mobilyalar otomatik konumlandırılır.
    </div>
    """, unsafe_allow_html=True)

    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )

    if plan_data is None or "plan" not in plan_data:
        st.warning("⚠️ Önce Kat Planı Üretimi sayfasından bir plan seçin.")
        return

    plan = plan_data["plan"]
    st.info(f"📐 Seçili plan: {len(plan.rooms)} oda, {plan.total_area:.1f} m², Puan: {plan_data.get('score', type('',(),{'total':0})).total:.0f}/100")

    if st.button("🪑 Mobilya Yerleştir", type="primary"):
        with st.spinner("Mobilyalar yerleştiriliyor..."):
            all_furniture = {}
            for room in plan.rooms:
                placed = place_furniture(room)
                all_furniture[room.name] = placed

            st.session_state.furniture_data = all_furniture

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = render_floor_plan(plan, title="Kat Planı + Tefriş", show_furniture=True)
        st.pyplot(fig)

    with col2:
        if "furniture_data" in st.session_state:
            st.subheader("🪑 Mobilya Listesi")
            for room_name, items in st.session_state.furniture_data.items():
                with st.expander(f"{room_name} ({len(items)} mobilya)"):
                    for f in items:
                        st.text(f"  • {f.isim} ({f.en:.1f}×{f.boy:.1f}m)")


def sayfa_3d():
    """Sayfa 8 — 3D Görselleştirme."""
    from visualization_3d.building_model import build_3d_model

    st.header("🏗️ 3D Görselleştirme")

    st.markdown("""
    <div style="background:#f0f7ff; border-left:3px solid #1E88E5; padding:10px 14px; border-radius:4px; margin:8px 0; font-size:14px;">
    <b>Bu sayfada ne göreceksiniz?</b> Binanızın interaktif 3D modeli. Fare ile döndürebilir, yakınlaştırabilirsiniz.
    Çatı tipini değiştirebilir, patlak görünümle her katı ayrı ayrı inceleyebilirsiniz.
    </div>
    """, unsafe_allow_html=True)

    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )
    imar = st.session_state.get("imar")
    parsel = st.session_state.get("parsel")

    if plan_data is None or "plan" not in plan_data:
        st.warning("⚠️ Önce bir kat planı üretin ve seçin. Soldaki menüden **[6] Kat Planı Üretimi** sayfasına gidin.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kat = st.number_input("Kat Sayısı", 1, 20, imar.kat_adedi if imar else 4, key="3d_kat")
    with col2:
        cati = st.selectbox("Çatı Tipi", ["kirma", "teras"], key="3d_cati")
    with col3:
        exploded = st.checkbox("Patlak Görünüm", key="3d_explode")
    with col4:
        sel_floor = st.selectbox("Kat Filtre", ["Tümü"] + [f"Kat {i+1}" for i in range(kat)], key="3d_floor")

    selected_floor = None if sel_floor == "Tümü" else int(sel_floor.split()[-1]) - 1
    parsel_coords = list(parsel.polygon.exterior.coords) if parsel else None

    fig = build_3d_model(
        plans=[plan_data["plan"]],
        kat_sayisi=kat,
        parsel_coords=parsel_coords,
        roof_type=cati,
        exploded=exploded,
        selected_floor=selected_floor,
    )
    st.plotly_chart(fig, use_container_width=True)


def sayfa_render():
    """Sayfa 9 — Fotogerçekçi Render."""
    from ai.render_generator import RENDER_STYLES

    st.header("🎨 Fotogerçekçi İç Mekan Render")

    st.markdown("""
    <div style="background:#f0f7ff; border-left:3px solid #1E88E5; padding:10px 14px; border-radius:4px; margin:8px 0; font-size:14px;">
    <b>Bu sayfada ne yapacaksınız?</b> Seçtiğiniz odanın fotogerçekçi iç mekan görselini AI ile oluşturabilirsiniz.
    Oda ve stil seçin, ardından render butonuna tıklayın. Bu özellik Grok/xAI API key gerektirir.
    API key yoksa render promptu metin olarak gösterilir.
    </div>
    """, unsafe_allow_html=True)

    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )

    if plan_data is None or "plan" not in plan_data:
        st.warning("⚠️ Önce bir kat planı seçin.")
        return

    plan = plan_data["plan"]
    oda_isimleri = [r.name for r in plan.rooms if r.room_type not in ("koridor", "antre")]

    col1, col2 = st.columns(2)
    with col1:
        secili_oda = st.selectbox("Oda Seçin", oda_isimleri, key="render_oda")
    with col2:
        stil = st.selectbox("Render Stili", list(RENDER_STYLES.keys()),
                           format_func=lambda x: f"{RENDER_STYLES[x]['isim']} — {RENDER_STYLES[x]['aciklama']}", key="render_stil")

    room = next((r for r in plan.rooms if r.name == secili_oda), None)
    if room:
        st.info(f"📐 {room.name}: {room.width:.1f}×{room.height:.1f}m = {room.area:.1f} m² | Yön: {room.facing_direction or 'belirsiz'}")

    grok_key = st.session_state.get("grok_api_key", "")

    if st.button("🎨 Render Oluştur", type="primary"):
        if not grok_key:
            st.warning("⚠️ Sidebar'dan Grok/xAI API key girin. Şimdilik prompt gösteriliyor:")
            from ai.render_generator import _build_render_prompt
            prompt = _build_render_prompt(secili_oda, room.room_type if room else "salon",
                                         room.area if room else 20, "south", stil)
            st.code(prompt, language="text")
        else:
            from ai.render_generator import generate_render
            with st.spinner("Render üretiliyor..."):
                result = generate_render(
                    secili_oda, room.room_type, room.area,
                    room.facing_direction or "south", stil, grok_key,
                )
            if result.success and result.image_url:
                st.image(result.image_url, caption=f"{secili_oda} — {RENDER_STYLES[stil]['isim']}")
            else:
                st.error(f"Render hatası: {result.error}")
