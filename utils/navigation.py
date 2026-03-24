"""
Sayfa Navigasyon Yardımcıları — Progress indicator ve "Sonraki Adım" butonları.
"""

import streamlit as st

# Sayfa sırası ve bağımlılıkları
SAYFA_SIRASI = [
    ("1_parsel", "Parsel Girisi", "parsel"),
    ("2_konum", "Konum & Cevre", None),
    ("3_imar", "Imar Bilgileri", "imar"),
    ("4_hesaplama", "Hesaplama", "hesaplama"),
    ("5_daire", "Daire Bolumleme", "bina_programi"),
    ("6_plan", "Kat Plani", "plans"),
    ("7_ai", "AI Iyilestirme", None),
    ("8_3d", "3D Gorsellestirme", None),
    ("9_render", "Render", None),
    ("10_fizibilite", "Mali Fizibilite", None),
    ("11_deprem", "Deprem Risk", None),
    ("12_enerji", "Enerji Performans", None),
    ("13_gantt", "Insaat Suresi", None),
    ("14_karsilastir", "Parsel Karsilastirma", None),
    ("15_irtifak", "Kat Irtifaki", None),
    ("16_ruhsat", "Yapi Ruhsati", None),
    ("17_muteahhit", "Muteahhit Eslestirme", None),
    ("18_rapor", "Rapor & Disa Aktarma", None),
    ("19_whatsapp", "WhatsApp Bot", None),
    ("20_veri", "Veri Guncelleme", None),
    ("21_crm", "CRM", None),
    ("22_workflow", "Is Akisi Motoru", None),
    ("23_ajan_panel", "Ajan Kontrol Paneli", None),
    ("24_firsat", "Firsat Merkezi", None),
    ("25_piyasa", "Piyasa Istihbarat", None),
]


def render_progress_bar():
    """Kullanıcının tamamladığı adımları gösteren progress indicator."""
    completed_steps = []
    for key, label, state_key in SAYFA_SIRASI[:9]:
        if state_key and st.session_state.get(state_key) is not None:
            completed_steps.append(key)

    total_design = 9  # İlk 9 tasarım adımı
    completed_count = len(completed_steps)
    progress = completed_count / total_design

    aktif = st.session_state.get("aktif_sayfa", "1_parsel")

    # Progress bar
    st.progress(progress, text=f"Tasarim ilerlemesi: {completed_count}/{total_design} adim")

    # Mini step indicators
    cols = st.columns(min(9, total_design))
    for i, (key, label, state_key) in enumerate(SAYFA_SIRASI[:9]):
        with cols[i]:
            is_active = (aktif == key)
            is_done = key in completed_steps
            if is_done:
                icon = "✅"
            elif is_active:
                icon = "🔵"
            else:
                icon = "⬜"
            step_num = i + 1
            st.markdown(
                f"<div style='text-align:center; font-size:10px;'>"
                f"{icon}<br>{step_num}</div>",
                unsafe_allow_html=True,
            )


def render_next_step_button(current_page: str):
    """Mevcut sayfadan sonraki adıma geçiş butonu."""
    page_keys = [s[0] for s in SAYFA_SIRASI]
    if current_page not in page_keys:
        return

    idx = page_keys.index(current_page)
    if idx < len(page_keys) - 1:
        next_key = page_keys[idx + 1]
        next_label = SAYFA_SIRASI[idx + 1][1]

        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"Sonraki Adim: {next_label} →",
                         type="primary", use_container_width=True,
                         key=f"next_{current_page}"):
                st.session_state.aktif_sayfa = next_key
                st.rerun()

    # Önceki adım butonu
    if idx > 0:
        prev_key = page_keys[idx - 1]
        prev_label = SAYFA_SIRASI[idx - 1][1]
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"← Onceki: {prev_label}",
                         use_container_width=True,
                         key=f"prev_{current_page}"):
                st.session_state.aktif_sayfa = prev_key
                st.rerun()


def get_sidebar_style(page_key: str) -> str:
    """Aktif sayfa için sidebar stil sınıfı."""
    aktif = st.session_state.get("aktif_sayfa", "1_parsel")
    return "primary" if aktif == page_key else "secondary"
