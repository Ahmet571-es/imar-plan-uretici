"""
Sayfa modülleri: Plan Üretimi, AI Tefriş, 3D Görselleştirme, Render.
"""

import streamlit as st
import pandas as pd
import numpy as np


def sayfa_plan():
    """Sayfa 6 — Kat Planı Üretimi (Dual AI)."""
    from ai.claude_planner import generate_plans_claude, _generate_demo_plans
    from core.plan_scorer import score_plan, FloorPlan
    from drawing.plan_renderer_matplotlib import render_floor_plan, render_plan_comparison

    st.header("📋 Kat Planı Üretimi — Dual AI")

    if st.session_state.get("hesaplama") is None:
        st.warning("⚠️ Önce hesaplama adımını tamamlayın.")
        return

    hesap = st.session_state.hesaplama
    imar = st.session_state.imar
    bina = st.session_state.get("bina_programi")

    st.info(f"📐 Yapılaşma alanı: {hesap.cekme_sonrasi_alan:.1f} m² | Kat başı net: {hesap.kat_basi_net_alan:.1f} m²")

    col1, col2 = st.columns(2)
    with col1:
        daire_tipi = st.selectbox("Daire Tipi", ["1+1", "2+1", "3+1", "4+1"], index=2, key="plan_tip")
        sun_dir = st.selectbox("Güneş Yönü", ["south", "north", "east", "west"], key="plan_sun")
    with col2:
        plan_sayisi = st.slider("Alternatif Sayısı", 2, 4, 2, key="plan_count")
        iteration = st.slider("İterasyon", 1, 3, 1, key="plan_iter")

    if st.button("🤖 Plan Üret", type="primary", key="btn_generate_plan"):
        with st.spinner("AI planları üretiyor..."):
            coords = list(hesap.cekme_polygonu.exterior.coords) if hesap.cekme_polygonu else [(0,0),(16,0),(16,12),(0,12)]
            apt_program = {
                "tip": daire_tipi,
                "brut_alan": hesap.kat_basi_net_alan / 2,
                "odalar": [],
            }
            if bina and bina.katlar and bina.katlar[0].daireler:
                d = bina.katlar[0].daireler[0]
                apt_program["odalar"] = [{"isim": o.isim, "tip": o.tip, "m2": o.m2} for o in d.odalar]

            plans = _generate_demo_plans(coords, apt_program, plan_sayisi)
            scored_plans = []
            for p in plans:
                fp = p["floor_plan"]
                sc = score_plan(fp, sun_best_direction=sun_dir)
                scored_plans.append({"plan": fp, "score": sc, "reasoning": p.get("reasoning", "")})

            scored_plans.sort(key=lambda x: x["score"].total, reverse=True)
            st.session_state.generated_plans = scored_plans

    if "generated_plans" in st.session_state:
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
                    if plan_data.get("reasoning"):
                        st.info(f"💬 {plan_data['reasoning']}")

                if st.button(f"✅ Plan {i+1}'i Seç", key=f"select_plan_{i}"):
                    st.session_state.selected_plan = plan_data
                    st.success(f"Plan {i+1} seçildi!")

        if len(plans) >= 2:
            st.markdown("---")
            st.subheader("📊 Karşılaştırma")
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

    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )
    imar = st.session_state.get("imar")
    parsel = st.session_state.get("parsel")

    if plan_data is None or "plan" not in plan_data:
        st.warning("⚠️ Önce bir kat planı üretin ve seçin.")
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

    api_key = st.text_input("Grok/xAI API Key (opsiyonel)", type="password", key="render_api")

    if st.button("🎨 Render Oluştur", type="primary"):
        if not api_key:
            st.warning("⚠️ Grok API key girilmedi. Render üretimi için `XAI_API_KEY` gereklidir.")
            from ai.render_generator import _build_render_prompt
            prompt = _build_render_prompt(secili_oda, room.room_type if room else "salon",
                                         room.area if room else 20, "south", stil)
            st.markdown("**Oluşturulan prompt (API key ile render üretilecek):**")
            st.code(prompt, language="text")
        else:
            from ai.render_generator import generate_render
            with st.spinner("Render üretiliyor..."):
                result = generate_render(
                    secili_oda, room.room_type, room.area,
                    room.facing_direction or "south", stil, api_key,
                )
            if result.success and result.image_url:
                st.image(result.image_url, caption=f"{secili_oda} — {RENDER_STYLES[stil]['isim']}")
            else:
                st.error(f"Render hatası: {result.error}")
