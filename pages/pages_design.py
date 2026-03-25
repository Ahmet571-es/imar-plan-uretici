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
        st.warning("⚠️ Önce hesaplama adımını tamamlayın.")
        return

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
                    if plan_data.get("reasoning"):
                        st.info(f"💬 {plan_data['reasoning']}")

                # Oda listesi tablosu
                if plan_data["plan"].rooms:
                    st.markdown("**Oda Detayları:**")
                    import pandas as pd
                    df = pd.DataFrame([{
                        "Oda": r.name, "Boyut": f"{r.width:.1f}×{r.height:.1f}m",
                        "Alan": f"{r.area:.1f} m²", "Cephe": r.facing_direction or "iç",
                        "Dış Duvar": "✅" if r.has_exterior_wall else "—",
                    } for r in plan_data["plan"].rooms])
                    st.dataframe(df, hide_index=True, use_container_width=True)

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
    """Sayfa 8 — 3D Görselleştirme + Plotly Canvas → Grok Imagine Pipeline.

    Pipeline stratejisi (sıfır hata hedefi):
    1. Sunucu tarafı Kaleido ile 3D model yakalama (güvenilir)
    2. Yakalanan görüntü → text-to-image ile fotorealistik render (wireframe edit sorunu yok)
    3. Opsiyonel: edit endpoint ile ince ayar (fotorealistik → fotorealistik, güvenilir)
    4. Manuel screenshot upload fallback
    5. Race condition koruması (processing flag)
    """
    from visualization_3d.building_model import build_3d_model
    from visualization_3d.plotly_capture import capture_plotly_to_bytes, is_kaleido_available

    st.header("🏗️ 3D Görselleştirme")

    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )
    imar = st.session_state.get("imar")
    parsel = st.session_state.get("parsel")

    if plan_data is None or "plan" not in plan_data:
        st.warning("Önce bir kat planı üretin ve seçin.")
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
    st.plotly_chart(fig, use_container_width=True, key="chart_3d_main")

    # ── 3D Model → Grok Imagine Fotorealistik Render Pipeline ──
    st.markdown("---")
    st.subheader("3D Model → Fotorealistik AI Render")

    grok_key = st.session_state.get("grok_api_key", "")

    # Stil ve prompt ayarları
    from prompts.style_configs import STYLE_VARIANTS, LIGHTING_OPTIONS

    render_col1, render_col2 = st.columns(2)
    with render_col1:
        ai_stil = st.selectbox(
            "Mimari Stil",
            list(STYLE_VARIANTS.keys()),
            format_func=lambda x: STYLE_VARIANTS[x]["isim"],
            key="3d_ai_stil",
        )
    with render_col2:
        ai_aydinlatma = st.select_slider(
            "Aydınlatma",
            LIGHTING_OPTIONS,
            value="Golden hour warm sunset",
            key="3d_ai_aydinlatma",
        )

    ek_prompt = st.text_input(
        "Ek talimat (opsiyonel)",
        placeholder="Örn: Cam cephe ekle, çevrede ağaçlar olsun, gece görünümü...",
        key="3d_ek_prompt",
    )

    # Bina boyutları
    hesap = st.session_state.get("hesaplama")
    if hesap and hesap.cekme_polygonu:
        from utils.geometry_helpers import polygon_bounds_boyutlar
        taban_en, taban_boy = polygon_bounds_boyutlar(hesap.cekme_polygonu)
    else:
        taban_en, taban_boy = 20.0, 15.0

    # Kaleido durumu
    kaleido_ok = is_kaleido_available()

    # Race condition koruması
    is_processing = st.session_state.get("_3d_render_processing", False)

    # ── Ana render butonu ──
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        render_btn = st.button(
            "3D Görünümü Yakala ve AI Render Oluştur" if kaleido_ok else "AI Render Oluştur (Parametrelerden)",
            type="primary",
            key="btn_3d_render",
            disabled=is_processing,
        )
    with btn_col2:
        uploaded = st.file_uploader(
            "Veya ekran görüntüsü yükle",
            type=["png", "jpg", "jpeg"],
            key="3d_screenshot_upload",
        )

    if not kaleido_ok:
        st.caption(
            "Kaleido kurulu değil — 3D yakalama devre dışı, doğrudan bina parametrelerinden render üretilecek. "
            "Kaleido kurmak için: `pip install kaleido`"
        )

    if render_btn and not is_processing:
        if not grok_key:
            st.warning("Sidebar'dan Grok/xAI API Key girin.")
        else:
            # Processing flag — race condition koruması
            st.session_state["_3d_render_processing"] = True

            try:
                # Adım 1: 3D model yakalama (Kaleido varsa)
                captured_bytes = b""
                if kaleido_ok:
                    with st.spinner("3D model görüntüsü yakalanıyor..."):
                        captured_bytes = capture_plotly_to_bytes(fig)

                    if captured_bytes:
                        st.success(f"3D görüntü yakalandı ({len(captured_bytes) // 1024}KB)")
                        with st.expander("Yakalanan 3D Görüntü", expanded=False):
                            st.image(captured_bytes, use_container_width=True)

                # Adım 2: Fotorealistik render üret
                from ai.grok_imagine import render_3d_to_photorealistic
                with st.spinner("Grok Imagine fotorealistik render üretiyor... (15-45 saniye)"):
                    result = render_3d_to_photorealistic(
                        captured_image_bytes=captured_bytes,
                        api_key=grok_key,
                        kat_sayisi=kat,
                        taban_en=taban_en,
                        taban_boy=taban_boy,
                        mimari_stil_key=ai_stil,
                        aydinlatma=ai_aydinlatma,
                        ek_prompt=ek_prompt,
                    )

                _handle_3d_render_result(result, STYLE_VARIANTS.get(ai_stil, {}).get("isim", ""))

            finally:
                st.session_state["_3d_render_processing"] = False

    # ── Manuel screenshot upload ──
    if uploaded is not None and not is_processing:
        img_bytes = uploaded.read()
        st.image(img_bytes, caption="Yüklenen 3D görüntü", use_container_width=True)

        if st.button("Yüklenen Görüntüden AI Render Oluştur", type="primary", key="btn_3d_upload_render"):
            if not grok_key:
                st.warning("Sidebar'dan Grok/xAI API Key girin.")
            else:
                st.session_state["_3d_render_processing"] = True
                try:
                    from ai.grok_imagine import render_3d_to_photorealistic
                    with st.spinner("Fotorealistik render üretiliyor..."):
                        result = render_3d_to_photorealistic(
                            captured_image_bytes=img_bytes,
                            api_key=grok_key,
                            kat_sayisi=kat,
                            taban_en=taban_en,
                            taban_boy=taban_boy,
                            mimari_stil_key=ai_stil,
                            aydinlatma=ai_aydinlatma,
                            ek_prompt=ek_prompt,
                        )
                    _handle_3d_render_result(result, STYLE_VARIANTS.get(ai_stil, {}).get("isim", ""))
                finally:
                    st.session_state["_3d_render_processing"] = False

    # ── Son render sonucu ve düzenleme ──
    if st.session_state.get("3d_render_result"):
        result_data = st.session_state["3d_render_result"]
        st.markdown("---")
        st.subheader("Fotorealistik Render Sonucu")

        if result_data.get("image_data_b64"):
            from utils.image_utils import base64_to_image_bytes
            img = base64_to_image_bytes(result_data["image_data_b64"])
            if img:
                st.image(img, use_container_width=True)

                method = result_data.get("metadata", {}).get("method", "")
                if method:
                    st.caption(f"Yöntem: {method}")

                # Düzenleme (fotorealistik → fotorealistik, edit endpoint güvenilir)
                edit_text = st.text_input(
                    "Render'ı düzenle",
                    placeholder="Örn: Cephe rengini beyaz yap, daha fazla yeşillik ekle...",
                    key="3d_render_edit",
                )
                if st.button("Düzenle", key="btn_3d_edit") and edit_text and grok_key:
                    from ai.grok_imagine import edit_image
                    with st.spinner("Düzenleme uygulanıyor..."):
                        edit_result = edit_image(
                            image_url=result_data.get("url", ""),
                            edit_prompt=edit_text,
                            api_key=grok_key,
                            image_base64=result_data["image_data_b64"] if not result_data.get("url") else "",
                        )
                    if edit_result.success and (edit_result.image_data or edit_result.image_url):
                        img_show = edit_result.image_data if edit_result.image_data else edit_result.image_url
                        st.image(img_show, use_container_width=True)
                        st.success("Düzenleme tamamlandı!")
                        st.session_state["3d_render_result"] = edit_result.to_dict()
                        _save_render_to_history(edit_result)
                    else:
                        st.error(f"Düzenleme hatası: {edit_result.error}")


def _handle_3d_render_result(result, style_name: str):
    """3D render sonucunu UI'da gösterir ve session state'e kaydeder."""
    from utils.image_utils import image_bytes_to_base64

    if result.success and (result.image_data or result.image_url):
        img_show = result.image_data if result.image_data else result.image_url
        st.image(img_show, use_container_width=True)
        st.success("Fotorealistik render tamamlandı!")

        render_data = result.to_dict()
        render_data["render_type"] = "3d_to_photorealistic"
        render_data["style"] = style_name
        st.session_state["3d_render_result"] = render_data

        result.render_type = "3d_to_photorealistic"
        result.style = style_name
        _save_render_to_history(result)
    else:
        st.error(f"Render hatası: {result.error}")


def sayfa_render():
    """Sayfa 9 — Grok Imagine 1.0 ile Fotorealistik AI Render.

    6 Özellik:
    1. Fotorealistik Dış Cephe Render
    2. İç Mekan Daire Planı Görselleştirme
    3. Çoklu Mimari Stil Alternatifleri (4 stil karşılaştırma)
    4. Arazi ve Çevre Konteksti (Site Planı)
    5. Multi-Turn İteratif Düzenleme
    6. Karşılaştırmalı Galeri ve PDF Rapor
    """
    from ai.grok_imagine import generate_image, edit_image, generate_style_comparison, ImageResult
    from prompts.exterior_prompts import build_exterior_prompt
    from prompts.interior_prompts import build_interior_prompt, ROOM_TYPE_DETAILS
    from prompts.site_plan_prompts import build_site_plan_prompt
    from prompts.style_configs import (
        STYLE_VARIANTS, CAMERA_ANGLES, LIGHTING_OPTIONS,
        BALCONY_TYPES, BALCONY_PROMPTS, OTOPARK_OPTIONS,
        PEYZAJ_OPTIONS,
    )
    from utils.image_utils import image_bytes_to_base64, base64_to_image_bytes

    st.header("🎨 Grok Imagine — Fotorealistik AI Render")

    # ── Session state başlangıç ──
    if "render_history" not in st.session_state:
        st.session_state.render_history = []
    if "last_render" not in st.session_state:
        st.session_state.last_render = None

    grok_key = st.session_state.get("grok_api_key", "")
    if not grok_key:
        st.warning("Sidebar'dan Grok/xAI API Key girin. Render'lar API key olmadan prompt önizleme modunda çalışır.")

    # ── Veri hazırlığı ──
    imar = st.session_state.get("imar")
    hesap = st.session_state.get("hesaplama")
    parsel = st.session_state.get("parsel")
    plan_data = st.session_state.get("selected_plan") or (
        st.session_state.get("generated_plans", [{}])[0] if st.session_state.get("generated_plans") else None
    )

    # Bina parametreleri (varsa hesaplamadan al, yoksa varsayılan)
    kat_sayisi = imar.kat_adedi if imar else 4
    kat_yuksekligi = 3.0
    if hesap and hesap.cekme_polygonu:
        from utils.geometry_helpers import polygon_bounds_boyutlar
        taban_en, taban_boy = polygon_bounds_boyutlar(hesap.cekme_polygonu)
    else:
        taban_en, taban_boy = 20.0, 15.0

    # Parsel boyutları
    if parsel:
        pb = parsel.polygon.bounds
        parsel_en = pb[2] - pb[0]
        parsel_boy = pb[3] - pb[1]
    else:
        parsel_en, parsel_boy = 30.0, 40.0

    on_bahce = imar.on_bahce if imar else 5.0
    yan_bahce = imar.yan_bahce if imar else 3.0
    arka_bahce = imar.arka_bahce if imar else 3.0

    bina_prog = st.session_state.get("bina_programi")
    if bina_prog and bina_prog.katlar and bina_prog.katlar[0].daireler:
        daire = bina_prog.katlar[0].daireler[0]
        daire_tipi = daire.tip
        daire_alan = daire.brut_m2
        daire_sayisi_per_kat = len(bina_prog.katlar[0].daireler)
    else:
        daire_tipi = "3+1"
        daire_alan = 120.0
        daire_sayisi_per_kat = 2

    # ── Tabs: 4 ana render modu ──
    tab_exterior, tab_interior, tab_site, tab_gallery = st.tabs([
        "🏢 Dış Cephe",
        "🛋️ İç Mekan",
        "🗺️ Site Planı",
        "🖼️ Galeri & Rapor",
    ])

    # ══════════════════════════════════════════════════
    # TAB 1: Dış Cephe Render
    # ══════════════════════════════════════════════════
    with tab_exterior:
        st.subheader("Fotorealistik Dış Cephe Render")

        col1, col2 = st.columns(2)
        with col1:
            render_modu = st.radio(
                "Render Modu",
                ["Tekli Render", "4 Stil Karşılaştırma"],
                key="ext_render_mode",
                horizontal=True,
            )
            mimari_stil = st.selectbox(
                "Mimari Stil",
                list(STYLE_VARIANTS.keys()),
                format_func=lambda x: STYLE_VARIANTS[x]["isim"],
                key="ext_stil",
            )
        with col2:
            kamera = st.select_slider(
                "Kamera Açısı",
                CAMERA_ANGLES,
                value="Elevated 30° corner perspective",
                key="ext_kamera",
            )
            aydinlatma = st.select_slider(
                "Aydınlatma",
                LIGHTING_OPTIONS,
                value="Golden hour warm sunset",
                key="ext_aydinlatma",
            )

        with st.expander("Detay Ayarları"):
            det_col1, det_col2 = st.columns(2)
            with det_col1:
                balkon_key = st.selectbox(
                    "Balkon Tipi",
                    list(BALCONY_TYPES.keys()),
                    format_func=lambda x: BALCONY_TYPES[x],
                    key="ext_balkon",
                )
                sehir = st.text_input("Şehir", "İstanbul", key="ext_sehir")
            with det_col2:
                zemin_kat = st.checkbox("Zemin kat ticari alan", key="ext_zemin")

        # Bina bilgi özeti
        st.info(
            f"Bina: {kat_sayisi} kat | {taban_en:.1f}x{taban_boy:.1f}m taban | "
            f"{daire_sayisi_per_kat} daire/kat | {daire_tipi} ({daire_alan:.0f}m²)"
        )

        prompt_kwargs = dict(
            kat_sayisi=kat_sayisi,
            taban_en=taban_en,
            taban_boy=taban_boy,
            kat_yuksekligi=kat_yuksekligi,
            daire_sayisi_per_kat=daire_sayisi_per_kat,
            daire_tipi=daire_tipi,
            daire_alan=daire_alan,
            balkon_tipi=balkon_key,
            mimari_stil_key=mimari_stil,
            sehir=sehir,
            kamera_acisi=kamera,
            aydinlatma=aydinlatma,
            zemin_kat_ticari=zemin_kat,
        )

        if render_modu == "Tekli Render":
            if st.button("AI Render Oluştur", type="primary", key="btn_ext_render"):
                prompt = build_exterior_prompt(**prompt_kwargs)

                if not grok_key:
                    st.warning("API key yok — prompt önizleme:")
                    st.code(prompt, language="text")
                else:
                    with st.spinner("Grok Imagine render üretiyor... (10-30 saniye)"):
                        result = generate_image(
                            prompt=prompt,
                            api_key=grok_key,
                            render_type="exterior",
                            style=STYLE_VARIANTS[mimari_stil]["isim"],
                        )

                    if result.success and result.image_data:
                        st.image(result.image_data, use_container_width=True)
                        st.success("Render tamamlandı!")
                        _save_render_to_history(result)
                    elif result.success and result.image_url:
                        st.image(result.image_url, use_container_width=True)
                        st.success("Render tamamlandı!")
                        _save_render_to_history(result)
                    else:
                        st.error(f"Render hatası: {result.error}")

        else:  # 4 Stil Karşılaştırma
            if st.button("4 Stil Karşılaştırma Oluştur", type="primary", key="btn_ext_4stil"):
                if not grok_key:
                    st.warning("API key gerekli — 4 stil karşılaştırma için Grok API key girin.")
                else:
                    with st.spinner("4 farklı mimari stilde render üretiliyor..."):
                        results = generate_style_comparison(
                            prompt_builder_func=build_exterior_prompt,
                            prompt_kwargs=prompt_kwargs,
                            api_key=grok_key,
                        )

                    cols = st.columns(2)
                    for i, res in enumerate(results):
                        with cols[i % 2]:
                            if res.success and (res.image_data or res.image_url):
                                img = res.image_data if res.image_data else res.image_url
                                st.image(img, caption=res.style, use_container_width=True)
                                _save_render_to_history(res)
                            else:
                                st.error(f"{res.style}: {res.error}")

        # ── Multi-turn düzenleme (Özellik 5) ──
        _render_edit_section(grok_key)

    # ══════════════════════════════════════════════════
    # TAB 2: İç Mekan Render
    # ══════════════════════════════════════════════════
    with tab_interior:
        st.subheader("İç Mekan Daire Planı Görselleştirme")

        has_plan = plan_data is not None and "plan" in (plan_data or {})

        if has_plan:
            plan = plan_data["plan"]
            oda_list = [r for r in plan.rooms if r.room_type not in ("koridor",)]
            oda_isimleri = [r.name for r in oda_list]
        else:
            oda_list = []
            oda_isimleri = []

        if not oda_isimleri:
            st.info("Kat planı seçilmemiş. Manuel oda bilgisi girin veya önce kat planı oluşturun.")
            ic_col1, ic_col2 = st.columns(2)
            with ic_col1:
                oda_tipi = st.selectbox(
                    "Oda Tipi",
                    list(ROOM_TYPE_DETAILS.keys()),
                    format_func=lambda x: x.replace("_", " ").title(),
                    key="int_oda_tipi_manual",
                )
                oda_en = st.number_input("Genişlik (m)", 2.0, 10.0, 4.5, 0.5, key="int_en_manual")
            with ic_col2:
                oda_boy = st.number_input("Derinlik (m)", 2.0, 10.0, 3.5, 0.5, key="int_boy_manual")
                pencere_yonu = st.selectbox("Pencere Yönü", ["south", "north", "east", "west"],
                                           format_func=lambda x: {"south": "Güney", "north": "Kuzey", "east": "Doğu", "west": "Batı"}[x],
                                           key="int_yon_manual")
        else:
            secili_oda = st.selectbox("Oda Seçin", oda_isimleri, key="int_oda_sec")
            room = next((r for r in oda_list if r.name == secili_oda), None)
            if room:
                oda_tipi = room.room_type
                oda_en = room.width
                oda_boy = room.height
                pencere_yonu = room.facing_direction or "south"
                st.info(f"{room.name}: {oda_en:.1f}x{oda_boy:.1f}m = {room.area:.1f}m²")
            else:
                oda_tipi, oda_en, oda_boy, pencere_yonu = "salon", 4.5, 3.5, "south"

        ic_stil = st.selectbox(
            "İç Mekan Stili",
            list(STYLE_VARIANTS.keys()),
            format_func=lambda x: STYLE_VARIANTS[x]["isim"],
            key="int_stil",
        )

        ic_render_mode = st.radio(
            "Render Modu",
            ["Tek Oda", "Tüm Odalar"],
            horizontal=True,
            key="int_render_mode",
        )

        if ic_render_mode == "Tek Oda":
            if st.button("İç Mekan Render Oluştur", type="primary", key="btn_int_render"):
                prompt = build_interior_prompt(
                    oda_tipi=oda_tipi,
                    oda_en=oda_en,
                    oda_boy=oda_boy,
                    pencere_yonu=pencere_yonu,
                    mimari_stil_key=ic_stil,
                )

                if not grok_key:
                    st.warning("API key yok — prompt önizleme:")
                    st.code(prompt, language="text")
                else:
                    with st.spinner("İç mekan render üretiliyor..."):
                        result = generate_image(
                            prompt=prompt,
                            api_key=grok_key,
                            render_type="interior",
                            style=STYLE_VARIANTS[ic_stil]["isim"],
                        )

                    if result.success and (result.image_data or result.image_url):
                        img = result.image_data if result.image_data else result.image_url
                        st.image(img, use_container_width=True)
                        st.success("İç mekan render tamamlandı!")
                        _save_render_to_history(result)
                    else:
                        st.error(f"Render hatası: {result.error}")

        else:  # Tüm Odalar
            if st.button("Tüm Odaları Render Et", type="primary", key="btn_int_all"):
                if not grok_key:
                    st.warning("Tüm odalar için API key gerekli.")
                elif not oda_list:
                    st.warning("Kat planı seçilmemiş.")
                else:
                    progress = st.progress(0)
                    for idx, room in enumerate(oda_list):
                        progress.progress((idx + 1) / len(oda_list), f"{room.name} render ediliyor...")
                        prompt = build_interior_prompt(
                            oda_tipi=room.room_type,
                            oda_en=room.width,
                            oda_boy=room.height,
                            pencere_yonu=room.facing_direction or "south",
                            mimari_stil_key=ic_stil,
                        )
                        result = generate_image(
                            prompt=prompt,
                            api_key=grok_key,
                            render_type="interior",
                            style=f"{STYLE_VARIANTS[ic_stil]['isim']} - {room.name}",
                        )
                        if result.success and (result.image_data or result.image_url):
                            img = result.image_data if result.image_data else result.image_url
                            st.image(img, caption=room.name, use_container_width=True)
                            _save_render_to_history(result)
                        else:
                            st.warning(f"{room.name}: {result.error}")

                    progress.progress(1.0, "Tamamlandı!")

        # İç mekan düzenleme
        _render_edit_section(grok_key, prefix="int")

    # ══════════════════════════════════════════════════
    # TAB 3: Site Planı
    # ══════════════════════════════════════════════════
    with tab_site:
        st.subheader("Arazi ve Çevre Konteksti — Kuşbakışı Site Planı")

        st.info(
            f"Parsel: {parsel_en:.1f}x{parsel_boy:.1f}m | "
            f"Bina: {taban_en:.1f}x{taban_boy:.1f}m | "
            f"Çekmeler: Ön {on_bahce:.1f}m, Yan {yan_bahce:.1f}m, Arka {arka_bahce:.1f}m"
        )

        site_col1, site_col2 = st.columns(2)
        with site_col1:
            otopark_sec = st.selectbox(
                "Otopark",
                list(OTOPARK_OPTIONS.keys()),
                format_func=lambda x: OTOPARK_OPTIONS[x],
                key="site_otopark",
            )
        with site_col2:
            peyzaj_sec = st.multiselect(
                "Peyzaj Öğeleri",
                PEYZAJ_OPTIONS,
                default=["Ağaçlar", "Çim alan", "Yürüyüş yolu"],
                key="site_peyzaj",
            )

        if st.button("Site Planı Render Oluştur", type="primary", key="btn_site_render"):
            prompt = build_site_plan_prompt(
                parsel_en=parsel_en,
                parsel_boy=parsel_boy,
                taban_en=taban_en,
                taban_boy=taban_boy,
                on_bahce=on_bahce,
                yan_bahce=yan_bahce,
                arka_bahce=arka_bahce,
                kat_sayisi=kat_sayisi,
                kat_yuksekligi=kat_yuksekligi,
                otopark=otopark_sec,
                peyzaj_secimler=peyzaj_sec,
            )

            if not grok_key:
                st.warning("API key yok — prompt önizleme:")
                st.code(prompt, language="text")
            else:
                with st.spinner("Site planı render üretiliyor..."):
                    result = generate_image(
                        prompt=prompt,
                        api_key=grok_key,
                        aspect_ratio="1:1",
                        render_type="site_plan",
                        style="Site Plan",
                    )

                if result.success and (result.image_data or result.image_url):
                    img = result.image_data if result.image_data else result.image_url
                    st.image(img, use_container_width=True)
                    st.success("Site planı render tamamlandı!")
                    _save_render_to_history(result)
                else:
                    st.error(f"Render hatası: {result.error}")

        _render_edit_section(grok_key, prefix="site")

    # ══════════════════════════════════════════════════
    # TAB 4: Galeri & PDF Rapor (Özellik 6)
    # ══════════════════════════════════════════════════
    with tab_gallery:
        st.subheader("Render Galerisi & PDF Rapor")

        history = st.session_state.get("render_history", [])

        if not history:
            st.info("Henüz render üretilmedi. Diğer sekmelerden render oluşturun.")
        else:
            st.markdown(f"**Toplam {len(history)} render**")

            # Galeri grid
            cols = st.columns(3)
            selected_indices = []
            for i, render in enumerate(history):
                with cols[i % 3]:
                    img_b64 = render.get("image_data_b64", "")
                    if img_b64:
                        img_bytes = base64_to_image_bytes(img_b64)
                        st.image(img_bytes, use_container_width=True)
                    else:
                        st.info(f"Görsel {i + 1} (veri yok)")

                    caption = render.get("style", render.get("render_type", ""))
                    ts = render.get("timestamp", "")
                    if ts:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(ts)
                            caption += f" | {dt.strftime('%H:%M')}"
                        except Exception:
                            pass
                    st.caption(caption)

                    if st.checkbox(f"Rapora ekle", key=f"gallery_sel_{i}", value=True):
                        selected_indices.append(i)

            # PDF Rapor oluşturma
            st.markdown("---")
            if st.button("PDF Rapor Oluştur", type="primary", key="btn_pdf"):
                from utils.pdf_report import generate_render_report

                # Parsel bilgileri
                parsel_bilgi = {}
                if parsel:
                    pb = parsel.polygon.bounds
                    parsel_bilgi = {
                        "Parsel Genislik (m)": f"{parsel_en:.1f}",
                        "Parsel Derinlik (m)": f"{parsel_boy:.1f}",
                        "Parsel Alan (m2)": f"{parsel_en * parsel_boy:.0f}",
                    }

                # İmar parametreleri
                imar_bilgi = {}
                if imar:
                    imar_bilgi = {
                        "Kat Adedi": imar.kat_adedi,
                        "TAKS": f"{imar.taks:.2f}",
                        "KAKS/Emsal": f"{imar.kaks:.2f}",
                        "On Bahce (m)": f"{imar.on_bahce:.1f}",
                        "Yan Bahce (m)": f"{imar.yan_bahce:.1f}",
                        "Arka Bahce (m)": f"{imar.arka_bahce:.1f}",
                    }

                # Hesaplama sonuçları
                hesap_bilgi = {}
                if hesap:
                    hesap_bilgi = {
                        "Taban Alani (m2)": f"{hesap.taban_insaat_alani:.1f}",
                        "Toplam Insaat (m2)": f"{hesap.toplam_insaat_alani:.1f}",
                        "Kat Basi Net (m2)": f"{hesap.kat_basi_net_alan:.1f}",
                    }

                secilen_renderlar = [history[i] for i in selected_indices if i < len(history)]

                with st.spinner("PDF rapor oluşturuluyor..."):
                    pdf_bytes = generate_render_report(
                        parsel_bilgileri=parsel_bilgi,
                        imar_parametreleri=imar_bilgi,
                        hesaplama_sonuclari=hesap_bilgi,
                        render_gorseller=secilen_renderlar,
                    )

                if pdf_bytes:
                    st.download_button(
                        "PDF İndir",
                        data=pdf_bytes,
                        file_name="imar_render_rapor.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success("PDF rapor hazır!")
                else:
                    st.error("PDF oluşturulamadı.")

            # Galeri temizle
            if st.button("Galeriyi Temizle", key="btn_clear_gallery"):
                st.session_state.render_history = []
                st.session_state.last_render = None
                st.rerun()


def _save_render_to_history(result):
    """Render sonucunu session_state geçmişine kaydeder."""
    from utils.image_utils import image_bytes_to_base64

    entry = result.to_dict()
    if result.image_data and not entry.get("image_data_b64"):
        entry["image_data_b64"] = image_bytes_to_base64(result.image_data)

    st.session_state.render_history.append(entry)
    st.session_state.last_render = entry


def _render_edit_section(grok_key: str, prefix: str = "ext"):
    """Multi-turn iteratif düzenleme bölümü (Özellik 5).

    Kullanıcı üretilen görseli doğal dilde düzenleyebilir.
    """
    from ai.grok_imagine import edit_image
    from utils.image_utils import image_bytes_to_base64, base64_to_image_bytes

    last = st.session_state.get("last_render")
    if not last or not last.get("image_data_b64"):
        return

    st.markdown("---")
    st.markdown("### Görseli Düzenle")
    st.caption("Önceki render'ı doğal dilde düzenleyin. Örnek: 'Cephe rengini bej yap', 'Balkonlara çiçek ekle'")

    edit_prompt = st.text_input(
        "Düzenleme talimatı",
        placeholder="Örn: Cephe rengini bej yap, balkonları cam korkuluklu yap...",
        key=f"edit_prompt_{prefix}",
    )

    if st.button("Düzenle", key=f"btn_edit_{prefix}") and edit_prompt:
        if not grok_key:
            st.warning("Düzenleme için API key gerekli.")
            return

        with st.spinner("Düzenleme uygulanıyor..."):
            # Önceki görselin URL'si veya base64'ünü kullan
            prev_url = last.get("url", "")
            prev_b64 = last.get("image_data_b64", "")

            result = edit_image(
                image_url=prev_url,
                edit_prompt=edit_prompt,
                api_key=grok_key,
                image_base64=prev_b64 if not prev_url else "",
            )

        if result.success and (result.image_data or result.image_url):
            img = result.image_data if result.image_data else result.image_url
            st.image(img, use_container_width=True)
            st.success("Düzenleme tamamlandı!")
            _save_render_to_history(result)
        else:
            st.error(f"Düzenleme hatası: {result.error}")
