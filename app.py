"""
İmar Uyumlu Kat Planı Üretici — Ana Streamlit Uygulaması
FAZ 1: Parsel Girişi → İmar Parametreleri → Hesaplama → Daire Bölümleme
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import numpy as np
import pandas as pd
import math

st.set_page_config(
    page_title="İmar Plan Üretici",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Stil ──
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stMetric > div { background: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 4px solid #1E88E5; }
    div[data-testid="stSidebar"] { background: #1a1a2e; }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3 { color: #e0e0e0; }
    .success-box { background: #e8f5e9; border-left: 4px solid #4CAF50; padding: 12px; border-radius: 4px; margin: 8px 0; }
    .warning-box { background: #fff3e0; border-left: 4px solid #FF9800; padding: 12px; border-radius: 4px; margin: 8px 0; }
    .info-box { background: #e3f2fd; border-left: 4px solid #1E88E5; padding: 12px; border-radius: 4px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ── Otomatik Kalıcılık Sistemi ──
# Her değişiklikte /tmp'ye otomatik kaydet, sayfa yenilendiğinde otomatik yükle.
# Kullanıcı hiçbir şey yapmak zorunda değil.

import json as _json
import os as _os

_AUTOSAVE_PATH = "/tmp/imar_plan_autosave.json"


def _auto_save():
    """Session state'i /tmp'ye otomatik kaydet."""
    try:
        data = {"aktif_sayfa": st.session_state.get("aktif_sayfa", "1_parsel")}
        if st.session_state.get("parsel"):
            p = st.session_state.parsel
            data["parsel"] = {"koordinatlar": p.koordinatlar, "yon": p.yon}
        if st.session_state.get("imar"):
            im = st.session_state.imar
            data["imar"] = {
                "kat_adedi": im.kat_adedi, "insaat_nizami": im.insaat_nizami,
                "taks": im.taks, "kaks": im.kaks,
                "on_bahce": im.on_bahce, "yan_bahce": im.yan_bahce, "arka_bahce": im.arka_bahce,
                "siginak_gerekli": im.siginak_gerekli, "otopark_gerekli": im.otopark_gerekli,
            }
        if st.session_state.get("claude_api_key"):
            data["claude_api_key"] = st.session_state.claude_api_key
        if st.session_state.get("grok_api_key"):
            data["grok_api_key"] = st.session_state.grok_api_key

        with open(_AUTOSAVE_PATH, "w") as f:
            _json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def _auto_load():
    """Sayfa yenilendiğinde /tmp'den otomatik yükle."""
    if not _os.path.exists(_AUTOSAVE_PATH):
        return
    try:
        with open(_AUTOSAVE_PATH) as f:
            data = _json.load(f)

        if "parsel" in data and st.session_state.get("parsel") is None:
            from core.parcel import Parsel
            coords = [tuple(c) for c in data["parsel"]["koordinatlar"]]
            st.session_state.parsel = Parsel.from_koordinatlar(coords, yon=data["parsel"].get("yon", "kuzey"))

        if "imar" in data and st.session_state.get("imar") is None:
            from core.zoning import ImarParametreleri
            st.session_state.imar = ImarParametreleri(**data["imar"])

        if st.session_state.get("parsel") and st.session_state.get("imar") and st.session_state.get("hesaplama") is None:
            from core.zoning import hesapla
            st.session_state.hesaplama = hesapla(st.session_state.parsel.polygon, st.session_state.imar)

        if "aktif_sayfa" in data:
            st.session_state.aktif_sayfa = data["aktif_sayfa"]

        if "claude_api_key" in data and not st.session_state.get("claude_api_key"):
            st.session_state.claude_api_key = data["claude_api_key"]
            _os.environ["ANTHROPIC_API_KEY"] = data["claude_api_key"]
        if "grok_api_key" in data and not st.session_state.get("grok_api_key"):
            st.session_state.grok_api_key = data["grok_api_key"]
            _os.environ["XAI_API_KEY"] = data["grok_api_key"]

    except Exception:
        pass


def _save_project_json() -> str:
    """Mevcut proje verilerini JSON olarak dışa aktar (manuel indirme için)."""
    data = {}
    if st.session_state.get("parsel"):
        p = st.session_state.parsel
        data["parsel"] = {"koordinatlar": p.koordinatlar, "yon": p.yon}
    if st.session_state.get("imar"):
        im = st.session_state.imar
        data["imar"] = {
            "kat_adedi": im.kat_adedi, "insaat_nizami": im.insaat_nizami,
            "taks": im.taks, "kaks": im.kaks,
            "on_bahce": im.on_bahce, "yan_bahce": im.yan_bahce, "arka_bahce": im.arka_bahce,
            "siginak_gerekli": im.siginak_gerekli, "otopark_gerekli": im.otopark_gerekli,
        }
    return _json.dumps(data, ensure_ascii=False, indent=2)


def _load_project_json(json_str: str):
    """JSON'dan proje verilerini yükle (manuel yükleme için)."""
    from core.parcel import Parsel
    from core.zoning import ImarParametreleri, hesapla

    data = _json.loads(json_str)
    if "parsel" in data:
        coords = [tuple(c) for c in data["parsel"]["koordinatlar"]]
        st.session_state.parsel = Parsel.from_koordinatlar(coords, yon=data["parsel"].get("yon", "kuzey"))
    if "imar" in data:
        st.session_state.imar = ImarParametreleri(**data["imar"])
    if st.session_state.get("parsel") and st.session_state.get("imar"):
        st.session_state.hesaplama = hesapla(st.session_state.parsel.polygon, st.session_state.imar)


# ── Session State Başlangıç ──
if "aktif_sayfa" not in st.session_state:
    st.session_state.aktif_sayfa = "1_parsel"
if "parsel" not in st.session_state:
    st.session_state.parsel = None
if "imar" not in st.session_state:
    st.session_state.imar = None
if "hesaplama" not in st.session_state:
    st.session_state.hesaplama = None
if "bina_programi" not in st.session_state:
    st.session_state.bina_programi = None

# Sayfa yenilendiğinde otomatik yükle
_auto_load()

# ── Sidebar Navigasyon ──
with st.sidebar:
    st.markdown("## 🏗️ İmar Plan Üretici")
    st.markdown("---")

    st.markdown("### 📐 PROJE TASARIM")
    sayfa_secenekleri = {
        "1_parsel":       "📍 [1] Parsel Girişi",
        "2_konum":        "🗺️ [2] Konum & Çevre",
        "3_imar":         "📐 [3] İmar Bilgileri",
        "4_hesaplama":    "📊 [4] Hesaplama Sonuçları",
        "5_daire":        "🏠 [5] Daire Bölümleme",
        "6_plan":         "📋 [6] Kat Planı Üretimi",
        "7_ai":           "🤖 [7] AI İyileştirme & Tefriş",
        "8_3d":           "🏗️ [8] 3D Görselleştirme",
        "9_render":       "🎨 [9] AI Render (Grok Imagine)",
    }
    for key, label in sayfa_secenekleri.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if st.session_state.aktif_sayfa == key else "secondary"):
            st.session_state.aktif_sayfa = key
            st.rerun()

    st.markdown("### 💰 ANALİZ & FİZİBİLİTE")
    analiz_sayfalari = {
        "10_fizibilite":  "💰 [10] Mali Fizibilite",
        "11_deprem":      "🔬 [11] Deprem Risk",
        "12_enerji":      "⚡ [12] Enerji Performans",
        "13_gantt":       "📅 [13] İnşaat Süresi",
        "14_karsilastir": "🔄 [14] Parsel Karşılaştırma",
    }
    for key, label in analiz_sayfalari.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if st.session_state.aktif_sayfa == key else "secondary"):
            st.session_state.aktif_sayfa = key
            st.rerun()

    st.markdown("### 📜 HUKUK & BELGE")
    hukuk_sayfalari = {
        "15_irtifak":     "📜 [15] Kat İrtifakı",
        "16_ruhsat":      "🏛️ [16] Yapı Ruhsatı",
        "17_muteahhit":   "👷 [17] Müteahhit Eşleştirme",
        "18_rapor":       "📄 [18] Rapor & Dışa Aktarma",
    }
    for key, label in hukuk_sayfalari.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if st.session_state.aktif_sayfa == key else "secondary"):
            st.session_state.aktif_sayfa = key
            st.rerun()

    st.markdown("### ⚙️ OTOMASYON")
    otomasyon_sayfalari = {
        "19_whatsapp":    "📱 [19] WhatsApp Bot",
        "20_veri":        "🔄 [20] Veri Güncelleme",
        "21_crm":         "👥 [21] CRM",
        "22_workflow":    "⚙️ [22] İş Akışı Motoru",
    }
    for key, label in otomasyon_sayfalari.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if st.session_state.aktif_sayfa == key else "secondary"):
            st.session_state.aktif_sayfa = key
            st.rerun()

    st.markdown("### 🤖 AJANLAR")
    ajan_sayfalari = {
        "23_ajan_panel":  "🤖 [23] Ajan Kontrol Paneli",
        "24_firsat":      "🔍 [24] Fırsat Merkezi",
        "25_piyasa":      "📈 [25] Piyasa İstihbarat",
    }
    for key, label in ajan_sayfalari.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if st.session_state.aktif_sayfa == key else "secondary"):
            st.session_state.aktif_sayfa = key
            st.rerun()

    st.markdown("---")

    # ── API Key Ayarları ──
    with st.expander("🔑 API Ayarları", expanded=False):
        # Önce secrets.toml'dan, yoksa session_state'ten oku
        default_claude = ""
        default_grok = ""
        try:
            default_claude = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        try:
            default_grok = st.secrets.get("XAI_API_KEY", "")
        except Exception:
            pass

        claude_key = st.text_input(
            "Claude API Key",
            value=st.session_state.get("claude_api_key", default_claude),
            type="password", key="input_claude_key",
            help="Anthropic Claude API anahtarı — plan üretimi ve analiz için",
        )
        grok_key = st.text_input(
            "Grok/xAI API Key",
            value=st.session_state.get("grok_api_key", default_grok),
            type="password", key="input_grok_key",
            help="xAI Grok API anahtarı — bağımsız plan üretimi ve render için",
        )

        if claude_key:
            st.session_state.claude_api_key = claude_key
            import os; os.environ["ANTHROPIC_API_KEY"] = claude_key
        if grok_key:
            st.session_state.grok_api_key = grok_key
            import os; os.environ["XAI_API_KEY"] = grok_key

        # Durum göstergesi
        if claude_key:
            st.success("✅ Claude API aktif")
        else:
            st.caption("Claude API key girilmedi")
        if grok_key:
            st.success("✅ Grok API aktif")
        else:
            st.caption("Grok API key girilmedi")

    st.caption("v1.2 — Grok Imagine 1.0 Entegrasyonu")

    # ── Otomatik Kaydetme Durumu ──
    has_data = st.session_state.get("parsel") is not None or st.session_state.get("imar") is not None
    if has_data:
        st.caption("💾 Veriler otomatik kaydediliyor")

    # ── Proje Yedek / Yükle ──
    with st.expander("💾 Proje Yedek / Geri Yükle", expanded=False):
        st.caption("Verileriniz otomatik kaydedilir. Farklı cihazda devam etmek için yedek alın.")

        if has_data:
            json_data = _save_project_json()
            st.download_button("💾 Yedek İndir (JSON)", json_data,
                               "proje_yedek.json", "application/json",
                               use_container_width=True)

        uploaded = st.file_uploader("📂 Yedek Yükle", type="json", key="proje_upload")
        if uploaded:
            try:
                _load_project_json(uploaded.read().decode("utf-8"))
                _auto_save()
                st.success("✅ Proje yüklendi!")
                st.rerun()
            except Exception as e:
                st.error(f"Yükleme hatası: {e}")


# ═══════════════════════════════════════════════════════════════
# SAYFA 1 — PARSEL GİRİŞİ
# ═══════════════════════════════════════════════════════════════
def sayfa_parsel():
    from core.parcel import Parsel

    st.header("📍 Parsel Geometrisi Girişi")

    tab_manuel, tab_tkgm = st.tabs(["✏️ Manuel Giriş", "🌐 TKGM Otomatik"])

    with tab_manuel:
        st.subheader("Parsel Şekli ve Ölçüleri")

        col1, col2 = st.columns([1, 1])

        with col1:
            sekil = st.selectbox(
                "Parsel Şekli",
                ["Dikdörtgen", "Dörtgen (Genel)", "Beşgen", "Altıgen", "Düzensiz"],
                key="parsel_sekil",
            )

            yon = st.selectbox(
                "Kuzey Yönü (Ön Cephe)",
                ["Kuzey", "Güney", "Doğu", "Batı", "Kuzeydoğu", "Kuzeybatı", "Güneydoğu", "Güneybatı"],
                key="parsel_yon",
            )

            if sekil == "Dikdörtgen":
                en = st.number_input("Parsel Eni (m)", min_value=5.0, max_value=200.0, value=22.0, step=0.1, key="p_en")
                boy = st.number_input("Parsel Boyu (m)", min_value=5.0, max_value=200.0, value=28.0, step=0.1, key="p_boy")

                if st.button("✅ Parseli Oluştur", type="primary", key="btn_dikdortgen"):
                    parsel = Parsel.from_dikdortgen(en, boy, yon=yon.lower())
                    st.session_state.parsel = parsel

            elif sekil == "Dörtgen (Genel)":
                st.markdown("**4 kenar uzunluğunu ve 4 iç açıyı girin:**")
                kenarlar = []
                acilar = []
                for i in range(4):
                    c1, c2 = st.columns(2)
                    with c1:
                        k = st.number_input(f"Kenar {i+1} (m)", min_value=1.0, max_value=200.0,
                                           value=[22.0, 28.0, 22.0, 28.0][i], step=0.1, key=f"k4_{i}")
                        kenarlar.append(k)
                    with c2:
                        a = st.number_input(f"Açı {i+1} (°)", min_value=30.0, max_value=170.0,
                                           value=90.0, step=0.5, key=f"a4_{i}")
                        acilar.append(a)

                aci_otomatik = st.checkbox("Açıları otomatik hesapla (düzenli çokgen)", value=False, key="aci_oto_4")

                if st.button("✅ Parseli Oluştur", type="primary", key="btn_dortgen"):
                    if aci_otomatik:
                        acilar = None
                    parsel = Parsel.from_kenarlar_acilar(kenarlar, acilar, yon=yon.lower())
                    st.session_state.parsel = parsel

            elif sekil in ["Beşgen", "Altıgen", "Düzensiz"]:
                if sekil == "Beşgen":
                    n = 5
                elif sekil == "Altıgen":
                    n = 6
                else:
                    n = st.number_input("Köşe Sayısı", min_value=3, max_value=12, value=5, key="kose_n")

                st.markdown(f"**{n} kenar uzunluğunu girin:**")
                kenarlar = []
                for i in range(n):
                    k = st.number_input(f"Kenar {i+1} (m)", min_value=1.0, max_value=200.0,
                                       value=20.0, step=0.1, key=f"kn_{i}")
                    kenarlar.append(k)

                aci_otomatik = st.checkbox("Açıları otomatik hesapla", value=True, key="aci_oto_n")

                acilar_input = None
                if not aci_otomatik:
                    st.markdown(f"**{n} iç açıyı girin:**")
                    acilar_input = []
                    varsayilan_aci = (n - 2) * 180.0 / n
                    for i in range(n):
                        a = st.number_input(f"Açı {i+1} (°)", min_value=30.0, max_value=170.0,
                                           value=varsayilan_aci, step=0.5, key=f"an_{i}")
                        acilar_input.append(a)

                if st.button("✅ Parseli Oluştur", type="primary", key="btn_cokgen"):
                    parsel = Parsel.from_kenarlar_acilar(kenarlar, acilar_input, yon=yon.lower())
                    st.session_state.parsel = parsel

        with col2:
            if st.session_state.parsel is not None:
                parsel = st.session_state.parsel
                st.markdown("### 📊 Parsel Bilgileri")

                m1, m2, m3 = st.columns(3)
                m1.metric("Alan", f"{parsel.alan:.1f} m²")
                m2.metric("Çevre", f"{parsel.cevre:.1f} m")
                m3.metric("Köşe Sayısı", f"{parsel.kose_sayisi}")

                # Kenar ve açı tablosu
                df_kenar = pd.DataFrame({
                    "Kenar": [f"Kenar {i+1}" for i in range(len(parsel.kenarlar))],
                    "Uzunluk (m)": [round(k, 2) for k in parsel.kenarlar],
                    "Açı (°)": [round(a, 1) for a in parsel.acilar],
                })
                st.dataframe(df_kenar, hide_index=True, use_container_width=True)

                # Parsel çizimi
                fig = parsel.ciz()
                st.pyplot(fig, use_container_width=True)

                st.success("✅ Parsel oluşturuldu. Sonraki adım: **İmar Bilgileri** →")

    with tab_tkgm:
        st.subheader("🌐 TKGM Parsel Sorgulama")
        from core.tkgm_api import parsel_sorgula, get_il_ilce_listesi

        il_ilce = get_il_ilce_listesi()
        iller = list(il_ilce.keys())

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            secili_il = st.selectbox("İl", iller, key="tkgm_il")
            ilceler = il_ilce.get(secili_il, ["Merkez"])
            secili_ilce = st.selectbox("İlçe", ilceler, key="tkgm_ilce")
            mahalle_input = st.text_input("Mahalle (opsiyonel)", key="tkgm_mahalle", placeholder="")
        with col_t2:
            ada_input = st.text_input("Ada No", key="tkgm_ada", placeholder="1301")
            parsel_input = st.text_input("Parsel No", key="tkgm_parsel", placeholder="7")

        if st.button("🔍 Parsel Sorgula (TKGM)", type="primary", key="btn_tkgm"):
            if not ada_input or not parsel_input:
                st.error("Ada ve Parsel numarasını girin.")
            else:
                with st.spinner("TKGM'den parsel sorgulanıyor..."):
                    sonuc = parsel_sorgula(
                        il=secili_il, ilce=secili_ilce,
                        mahalle=mahalle_input, ada=ada_input, parsel=parsel_input,
                    )

                if sonuc.basarili and sonuc.polygon:
                    parsel = Parsel(sonuc.polygon, yon="kuzey")
                    st.session_state.parsel = parsel
                    st.success(f"✅ Parsel bulundu! Alan: {sonuc.alan:.1f} m², Köşe: {parsel.kose_sayisi}")
                    if sonuc.nitelik:
                        st.info(f"Nitelik: {sonuc.nitelik}")
                elif sonuc.basarili and not sonuc.polygon:
                    st.warning("Parsel bulundu ama koordinat verisi alınamadı. Manuel giriş kullanın.")
                    if sonuc.alan > 0:
                        st.info(f"TKGM alan bilgisi: {sonuc.alan:.1f} m²")
                else:
                    st.error(f"❌ {sonuc.hata}")
                    st.caption("TKGM API'ye erişilemedi veya parsel bulunamadı. Manuel Giriş sekmesinden devam edebilirsiniz.")

    # Sonraki adım butonu
    if st.session_state.parsel is not None:
        st.markdown("---")
        if st.button("➡️ Sonraki Adım: İmar Bilgileri", type="primary", key="btn_next_1"):
            st.session_state.aktif_sayfa = "3_imar"
            st.rerun()


# Sayfa 2 imported from pages.pages_other


# ═══════════════════════════════════════════════════════════════
# SAYFA 3 — İMAR BİLGİLERİ GİRİŞİ
# ═══════════════════════════════════════════════════════════════
def sayfa_imar():
    from core.zoning import ImarParametreleri
    from utils.constants import INSAAT_NIZAMLARI

    st.header("📐 İmar Bilgileri Girişi")

    if st.session_state.parsel is None:
        st.warning("⚠️ Önce parsel oluşturun. [Parsel Girişi] sayfasına gidin.")
        return

    st.markdown("Belediye e-imar uygulamasından alınan yapılaşma bilgilerini girin.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Temel İmar Parametreleri")

        kat_adedi = st.number_input("Kat Adedi", min_value=1, max_value=30, value=4, step=1, key="imar_kat")

        nizam_options = list(INSAAT_NIZAMLARI.values())
        nizam_keys = list(INSAAT_NIZAMLARI.keys())
        nizam_idx = st.selectbox(
            "İnşaat Nizamı",
            range(len(nizam_options)),
            format_func=lambda i: f"{nizam_keys[i]} — {nizam_options[i]}",
            key="imar_nizam",
        )
        insaat_nizami = nizam_keys[nizam_idx]

        taks = st.number_input("TAKS (Taban Alanı Kat Sayısı)", min_value=0.05, max_value=1.0,
                               value=0.35, step=0.05, format="%.2f", key="imar_taks")
        kaks = st.number_input("KAKS / Emsal", min_value=0.1, max_value=5.0,
                               value=1.40, step=0.05, format="%.2f", key="imar_kaks")

    with col2:
        st.subheader("Çekme Mesafeleri (m)")

        on_bahce = st.number_input("Ön Bahçe", min_value=0.0, max_value=30.0,
                                   value=5.0, step=0.5, key="imar_on")
        yan_bahce = st.number_input("Yan Bahçe", min_value=0.0, max_value=30.0,
                                    value=3.0, step=0.5, key="imar_yan")
        arka_bahce = st.number_input("Arka Bahçe", min_value=0.0, max_value=30.0,
                                     value=3.0, step=0.5, key="imar_arka")

        st.subheader("Ek Limitler")
        bina_yuk = st.number_input("Bina Yüksekliği Limiti (m) — 0=sınır yok",
                                   min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="imar_byuk")
        bina_der = st.number_input("Bina Derinliği Limiti (m) — 0=sınır yok",
                                   min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="imar_bder")

    st.markdown("---")
    st.subheader("Ek Gereksinimler")
    col_ek1, col_ek2, col_ek3 = st.columns(3)
    with col_ek1:
        asansor_info = "✅ Zorunlu (4+ kat)" if kat_adedi >= 4 else "İsteğe bağlı"
        st.checkbox(f"Asansör ({asansor_info})", value=kat_adedi >= 4,
                    disabled=kat_adedi >= 4, key="imar_asansor")
    with col_ek2:
        siginak = st.checkbox("Sığınak Gereksinimi", value=False, key="imar_siginak")
    with col_ek3:
        otopark = st.checkbox("Otopark Gereksinimi", value=True, key="imar_otopark")

    # Kaydet butonu
    if st.button("💾 İmar Bilgilerini Kaydet", type="primary", key="btn_imar_kaydet"):
        imar = ImarParametreleri(
            kat_adedi=kat_adedi,
            insaat_nizami=insaat_nizami,
            taks=taks,
            kaks=kaks,
            on_bahce=on_bahce,
            yan_bahce=yan_bahce,
            arka_bahce=arka_bahce,
            bina_yuksekligi_limiti=bina_yuk,
            bina_derinligi_limiti=bina_der,
            siginak_gerekli=siginak,
            otopark_gerekli=otopark,
        )
        st.session_state.imar = imar
        st.success("✅ İmar bilgileri kaydedildi.")

    # Özet göster
    if st.session_state.imar is not None:
        imar = st.session_state.imar
        st.markdown("---")
        st.subheader("📋 Kayıtlı İmar Özeti")
        ozet_data = {
            "Parametre": ["Kat Adedi", "İnşaat Nizamı", "TAKS", "KAKS", "Ön Bahçe", "Yan Bahçe",
                          "Arka Bahçe", "Asansör Zorunlu", "Sığınak"],
            "Değer": [imar.kat_adedi, f"{imar.insaat_nizami} — {INSAAT_NIZAMLARI[imar.insaat_nizami]}",
                      imar.taks, imar.kaks, f"{imar.on_bahce} m", f"{imar.yan_bahce} m",
                      f"{imar.arka_bahce} m", "Evet" if imar.asansor_zorunlu else "Hayır",
                      "Evet" if imar.siginak_gerekli else "Hayır"],
        }
        st.dataframe(pd.DataFrame(ozet_data), hide_index=True, use_container_width=True)

        if st.button("➡️ Sonraki Adım: Hesaplama Sonuçları", type="primary", key="btn_next_3"):
            st.session_state.aktif_sayfa = "4_hesaplama"
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# SAYFA 4 — HESAPLAMA SONUÇLARI
# ═══════════════════════════════════════════════════════════════
def sayfa_hesaplama():
    from core.zoning import hesapla
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    st.header("📊 Otomatik Hesaplama Sonuçları")

    if st.session_state.parsel is None:
        st.warning("⚠️ Önce parsel oluşturun.")
        return
    if st.session_state.imar is None:
        st.warning("⚠️ Önce imar bilgilerini girin.")
        return

    parsel = st.session_state.parsel
    imar = st.session_state.imar

    # Hesaplama yap
    sonuc = hesapla(parsel.polygon, imar)
    st.session_state.hesaplama = sonuc

    # Metrikler
    st.subheader("🔢 Hesaplama Sonuçları")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Parsel Alanı", f"{sonuc.parsel_alani:.1f} m²")
    col2.metric("Maks. Taban Alanı", f"{sonuc.max_taban_alani:.1f} m²")
    col3.metric("Toplam İnşaat", f"{sonuc.toplam_insaat_alani:.1f} m²")
    col4.metric("Kat Başı Net", f"{sonuc.kat_basi_net_alan:.1f} m²")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Çekme Sonrası", f"{sonuc.cekme_sonrasi_alan:.1f} m²")
    col6.metric("Kat Başı Brüt", f"{sonuc.kat_basi_brut_alan:.1f} m²")
    col7.metric("Ortak Alan / Kat", f"{sonuc.toplam_ortak_alan:.1f} m²")
    col8.metric("Kat Sayısı", f"{imar.kat_adedi}")

    # Detay tablosu
    st.markdown("---")
    st.subheader("📋 Detaylı Hesaplama Tablosu")
    ozet = sonuc.ozet_dict()
    df = pd.DataFrame({"Kalem": list(ozet.keys()), "Değer": list(ozet.values())})
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Ortak alan dağılımı
    st.markdown("---")
    col_viz1, col_viz2 = st.columns(2)

    with col_viz1:
        st.subheader("🏗️ Ortak Alan Dağılımı")
        ortak_items = {
            "Merdiven Evi": sonuc.merdiven_alani,
            "Asansör": sonuc.asansor_alani,
            "Sığınak": sonuc.siginak_alani,
        }
        ortak_items = {k: v for k, v in ortak_items.items() if v > 0}

        if ortak_items:
            fig_pie, ax_pie = plt.subplots(figsize=(5, 4))
            colors = ["#1E88E5", "#FF9800", "#4CAF50", "#E91E63"]
            ax_pie.pie(ortak_items.values(), labels=ortak_items.keys(),
                      autopct='%1.1f%%', colors=colors[:len(ortak_items)],
                      textprops={'fontsize': 10})
            ax_pie.set_title("Ortak Alan Dağılımı (m²)", fontsize=12, fontweight="bold")
            st.pyplot(fig_pie)

    with col_viz2:
        st.subheader("📐 Parsel & Yapılaşma Alanı")
        fig = parsel.ciz(cekme_polygonu=sonuc.cekme_polygonu)
        st.pyplot(fig)

    # Uyarılar
    if sonuc.uyarilar:
        st.markdown("---")
        st.subheader("⚠️ Uyarılar")
        for uyari in sonuc.uyarilar:
            st.warning(uyari)

    # Sonraki adım
    st.markdown("---")
    if st.button("➡️ Sonraki Adım: Daire Bölümleme", type="primary", key="btn_next_4"):
        st.session_state.aktif_sayfa = "5_daire"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# SAYFA 5 — DAİRE BÖLÜMLEME
# ═══════════════════════════════════════════════════════════════
def sayfa_daire():
    from core.apartment_divider import (
        varsayilan_daireler_olustur,
        daire_olustur_custom,
        BinaProgrami,
        KatPlani,
        Daire,
        Oda,
    )
    from config.room_defaults import DAIRE_SABLONLARI, get_default_rooms
    from utils.validation import validate_daire, validate_kat, validate_bina
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    st.header("🏠 Daire Bölümleme")

    if st.session_state.hesaplama is None:
        st.warning("⚠️ Önce hesaplama adımını tamamlayın.")
        return

    sonuc = st.session_state.hesaplama
    imar = st.session_state.imar

    st.info(
        f"📊 **Kat başı net alan:** {sonuc.kat_basi_net_alan:.1f} m² | "
        f"**Kat sayısı:** {imar.kat_adedi} | "
        f"**Ortak alan / kat:** {sonuc.toplam_ortak_alan:.1f} m²"
    )

    tab_manuel, tab_ai = st.tabs(["✏️ Manuel Giriş", "🤖 AI ile Doğal Dil"])

    with tab_manuel:
        st.subheader("Kat ve Daire Ayarları")

        col1, col2, col3 = st.columns(3)
        with col1:
            daire_per_kat = st.number_input("Kat başına daire sayısı", min_value=1, max_value=8,
                                            value=2, step=1, key="daire_per_kat")
        with col2:
            daire_tipi = st.selectbox("Varsayılan daire tipi", list(DAIRE_SABLONLARI.keys()),
                                      index=2, key="daire_tipi_sec")
        with col3:
            daire_brut = sonuc.kat_basi_net_alan / max(daire_per_kat, 1)
            st.metric("Daire Başı Brüt Alan", f"{daire_brut:.1f} m²")

        # Daire tipi bilgisi
        sablon = DAIRE_SABLONLARI.get(daire_tipi, {})
        ideal_min, ideal_max = sablon.get("brut_alan_aralik", (0, 0))
        if daire_brut < ideal_min:
            st.warning(f"⚠️ Daire başı alan ({daire_brut:.0f} m²) {daire_tipi} için önerilen minimumun ({ideal_min} m²) altında.")
        elif daire_brut > ideal_max:
            st.info(f"ℹ️ Daire başı alan ({daire_brut:.0f} m²) {daire_tipi} için geniş. Daha büyük tip düşünebilirsiniz.")

        # Bina programı oluştur
        if st.button("🏗️ Bina Programını Oluştur", type="primary", key="btn_bina_olustur"):
            bina = varsayilan_daireler_olustur(
                kat_basi_net_alan=sonuc.kat_basi_net_alan,
                kat_sayisi=imar.kat_adedi,
                kat_basi_brut_alan=sonuc.kat_basi_brut_alan,
                ortak_alan=sonuc.toplam_ortak_alan,
                daire_sayisi_per_kat=daire_per_kat,
                daire_tipi=daire_tipi,
            )
            st.session_state.bina_programi = bina

        # Bina programı gösterimi
        if st.session_state.bina_programi is not None:
            bina = st.session_state.bina_programi

            st.markdown("---")
            st.subheader("🏢 Bina Programı Özeti")

            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Kat", bina.kat_sayisi)
            m2.metric("Toplam Daire", bina.toplam_daire)
            m3.metric("Toplam İnşaat", f"{bina.toplam_insaat:.1f} m²")

            # Kat kat daire tablosu
            for kat in bina.katlar:
                with st.expander(f"🏗️ Kat {kat.kat_no} — {len(kat.daireler)} daire | Net: {kat.net_kullanilabilir:.1f} m²", expanded=kat.kat_no == 1):

                    for daire in kat.daireler:
                        st.markdown(f"**Daire {daire.numara}** — {daire.tip} | Brüt: {daire.brut_alan:.1f} m²")

                        # Oda tablosu (düzenlenebilir)
                        oda_data = []
                        for idx, oda in enumerate(daire.odalar):
                            oda_data.append({
                                "Oda": oda.isim,
                                "Tip": oda.tip,
                                "Alan (m²)": oda.m2,
                                "Min": oda.min_m2,
                                "Max": oda.max_m2,
                            })

                        df_oda = pd.DataFrame(oda_data)

                        edited_df = st.data_editor(
                            df_oda,
                            column_config={
                                "Oda": st.column_config.TextColumn("Oda", disabled=True),
                                "Tip": st.column_config.TextColumn("Tip", disabled=True),
                                "Alan (m²)": st.column_config.NumberColumn("Alan (m²)", min_value=1.0, max_value=100.0, step=0.5),
                                "Min": st.column_config.NumberColumn("Min", disabled=True),
                                "Max": st.column_config.NumberColumn("Max", disabled=True),
                            },
                            hide_index=True,
                            use_container_width=True,
                            key=f"oda_editor_{daire.numara}",
                        )

                        # Toplam ve validasyon
                        toplam_oda = edited_df["Alan (m²)"].sum()
                        col_t1, col_t2 = st.columns(2)
                        col_t1.metric("Oda Toplamı", f"{toplam_oda:.1f} m²")
                        col_t2.metric("Duvar/Kayıp", f"{daire.brut_alan - toplam_oda:.1f} m²")

                        # Validasyon
                        val_odalar = [{"isim": row["Oda"], "tip": row["Tip"], "m2": row["Alan (m²)"]}
                                     for _, row in edited_df.iterrows()]
                        val_sonuc = validate_daire(val_odalar, daire.brut_alan)
                        hatalar = [v for v in val_sonuc if not v["gecerli"]]
                        if hatalar:
                            for h in hatalar:
                                st.error(h["mesaj"])
                        else:
                            st.success("✅ Tüm odalar yönetmeliğe uygun.")

                        st.markdown("---")

            # Bina düzeyi validasyon
            st.subheader("✅ Bina Validasyonu")
            bina_val = validate_bina(imar.kat_adedi, bina.toplam_daire)
            for v in bina_val:
                if v["gecerli"]:
                    st.info(v["mesaj"])
                else:
                    st.error(v["mesaj"])

            # Alan dağılımı grafiği
            st.markdown("---")
            st.subheader("📊 Alan Dağılımı")

            # İlk dairenin oda dağılımı
            ilk_daire = bina.katlar[0].daireler[0] if bina.katlar and bina.katlar[0].daireler else None
            if ilk_daire:
                fig_bar, ax_bar = plt.subplots(figsize=(10, 4))
                oda_isimleri = [o.isim for o in ilk_daire.odalar]
                oda_alanlari = [o.m2 for o in ilk_daire.odalar]
                colors = plt.cm.Set3(np.linspace(0, 1, len(oda_isimleri)))
                bars = ax_bar.barh(oda_isimleri, oda_alanlari, color=colors)
                ax_bar.set_xlabel("Alan (m²)")
                ax_bar.set_title(f"Daire {ilk_daire.numara} ({ilk_daire.tip}) — Oda Dağılımı", fontweight="bold")
                for bar, val in zip(bars, oda_alanlari):
                    ax_bar.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                               f'{val:.1f}', va='center', fontsize=9)
                fig_bar.tight_layout()
                st.pyplot(fig_bar)

    with tab_ai:
        st.subheader("🤖 AI ile Doğal Dil Girişi")

        claude_key = st.session_state.get("claude_api_key", "")

        ai_input = st.text_area(
            "Daire programınızı doğal dille yazın:",
            placeholder="Örnek: Her katta 2 daire olsun, her biri 3+1, 125 metrekare. Salon 30, yatak odaları 15-20, mutfak 12, bir balkon olsun",
            height=120,
            key="ai_daire_input",
        )

        if st.button("🧠 AI ile Analiz Et", key="btn_ai_daire", disabled=not claude_key):
            if ai_input.strip():
                with st.spinner("Claude analiz ediyor..."):
                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=claude_key)
                        response = client.messages.create(
                            model="claude-sonnet-4-6-20250514",
                            max_tokens=2048,
                            system="Sen bir mimari asistansın. Kullanıcının doğal dildeki talebini analiz et ve JSON formatında daire programı çıkar. Yanıtın SADECE JSON olsun, başka metin ekleme. Format: {\"kat_basi_daire\": 2, \"daire_tipi\": \"3+1\", \"daireler\": [{\"tip\": \"3+1\", \"brut_alan\": 125, \"odalar\": [{\"isim\": \"Salon\", \"tip\": \"salon\", \"m2\": 30}]}]}",
                            messages=[{"role": "user", "content": f"Kısıtlamalar: Kat başı net alan {sonuc.kat_basi_net_alan:.0f} m², {imar.kat_adedi} kat. Talep: {ai_input}"}],
                        )
                        import json
                        text = response.content[0].text
                        if "```json" in text:
                            text = text.split("```json")[1].split("```")[0]
                        elif "```" in text:
                            text = text.split("```")[1].split("```")[0]
                        parsed = json.loads(text)

                        # Parsed sonucu bina programına dönüştür
                        st.success("✅ AI analizi tamamlandı!")
                        st.json(parsed)
                        st.info("Yukarıdaki sonucu Manuel Giriş sekmesinden düzenleyebilirsiniz.")
                    except Exception as e:
                        st.error(f"AI analiz hatası: {e}")
            else:
                st.warning("Lütfen bir metin girin.")

        if not claude_key:
            st.caption("💡 AI analizi için sidebar'dan Claude API key girin.")

    # Sonraki adım
    if st.session_state.bina_programi is not None:
        st.markdown("---")
        if st.button("➡️ Sonraki Adım: Kat Planı Üretimi", type="primary", key="btn_next_5"):
            st.session_state.aktif_sayfa = "6_plan"
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# SAYFA İMPORTLARI — LAZY LOADING (Bellek optimizasyonu)
# Her sayfa sadece açıldığında yüklenir, başlangıçta RAM kullanmaz.
# ═══════════════════════════════════════════════════════════════

def sayfa_plan():
    from pages.pages_design import sayfa_plan as _f; _f()

def sayfa_ai():
    from pages.pages_design import sayfa_ai_tefris as _f; _f()

def sayfa_3d():
    from pages.pages_design import sayfa_3d as _f; _f()

def sayfa_render():
    from pages.pages_design import sayfa_render as _f; _f()

def sayfa_fizibilite():
    from pages.pages_analysis import sayfa_fizibilite as _f; _f()

def sayfa_deprem():
    from pages.pages_analysis import sayfa_deprem as _f; _f()

def sayfa_enerji():
    from pages.pages_analysis import sayfa_enerji as _f; _f()

def sayfa_gantt():
    from pages.pages_analysis import sayfa_gantt as _f; _f()

def sayfa_karsilastir():
    from pages.pages_analysis import sayfa_karsilastir as _f; _f()

def sayfa_konum():
    from pages.pages_other import sayfa_konum as _f; _f()

def sayfa_irtifak():
    from pages.pages_other import sayfa_irtifak as _f; _f()

def sayfa_ruhsat():
    from pages.pages_other import sayfa_ruhsat as _f; _f()

def sayfa_muteahhit():
    from pages.pages_other import sayfa_muteahhit as _f; _f()

def sayfa_rapor():
    from pages.pages_other import sayfa_rapor as _f; _f()

def sayfa_firsat():
    from pages.pages_other import sayfa_firsat as _f; _f()

def sayfa_piyasa():
    from pages.pages_other import sayfa_piyasa as _f; _f()

def sayfa_ajan_panel():
    from agents.agent_dashboard import render_agent_dashboard; render_agent_dashboard()


# ── Placeholder'lar (Dış API gerektiren sayfalar) ──
def placeholder_sayfa(baslik, faz, aciklama=""):
    st.header(baslik)
    st.info(f"Bu sayfa **{faz}**'da geliştirilecektir. Dış servis entegrasyonu gerektirir.")
    if aciklama:
        st.markdown(aciklama)

def sayfa_whatsapp():
    placeholder_sayfa("📱 WhatsApp Bot", "FAZ 8", "Twilio/Green API ile sahadan hızlı fizibilite sorgusu.")

def sayfa_veri():
    placeholder_sayfa("🔄 Veri Güncelleme", "FAZ 9", "Sahibinden, TCMB, TÜİK scraper'ları + otomatik güncelleme.")

def sayfa_crm():
    """CRM Sayfası — Müşteri ve proje takibi."""
    st.header("CRM — Musteri ve Proje Takibi")

    from database.db import get_engine
    try:
        from sqlalchemy import text
        engine = get_engine()
    except Exception:
        engine = None

    # Müşteri ekleme formu
    with st.expander("Yeni Musteri Ekle", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            mus_ad = st.text_input("Ad Soyad", key="crm_ad")
            mus_tel = st.text_input("Telefon", key="crm_tel")
            mus_email = st.text_input("E-posta", key="crm_email")
        with col2:
            mus_tip = st.selectbox("Musteri Tipi",
                                    ["Bireysel", "Kurumsal", "Muteahhit"],
                                    key="crm_tip")
            mus_durum = st.selectbox("Durum",
                                      ["Aday", "Gorusme", "Teklif", "Sozlesme", "Tamamlandi"],
                                      key="crm_durum")
            mus_not = st.text_area("Notlar", key="crm_not", height=68)

        if st.button("Musteri Kaydet", type="primary", key="crm_kaydet"):
            if not mus_ad:
                st.warning("Ad Soyad zorunludur.")
            else:
                if "crm_musteriler" not in st.session_state:
                    st.session_state.crm_musteriler = []
                st.session_state.crm_musteriler.append({
                    "ad": mus_ad, "tel": mus_tel, "email": mus_email,
                    "tip": mus_tip, "durum": mus_durum, "not": mus_not,
                })
                st.success(f"Musteri eklendi: {mus_ad}")
                st.rerun()

    # Proje ekleme
    with st.expander("Yeni Proje Ekle", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            prj_ad = st.text_input("Proje Adi", key="crm_prj_ad")
            prj_il = st.text_input("Il/Ilce", key="crm_prj_il")
        with col2:
            prj_durum = st.selectbox("Proje Durumu",
                                      ["Fizibilite", "Tasarim", "Ruhsat", "Insaat", "Teslim"],
                                      key="crm_prj_durum")
            prj_butce = st.number_input("Butce (TL)", 0, 100_000_000, 5_000_000,
                                         step=100_000, key="crm_prj_butce")

        if st.button("Proje Kaydet", type="primary", key="crm_prj_kaydet"):
            if not prj_ad:
                st.warning("Proje adi zorunludur.")
            else:
                if "crm_projeler" not in st.session_state:
                    st.session_state.crm_projeler = []
                st.session_state.crm_projeler.append({
                    "ad": prj_ad, "il": prj_il,
                    "durum": prj_durum, "butce": prj_butce,
                })
                st.success(f"Proje eklendi: {prj_ad}")
                st.rerun()

    # Müşteri listesi
    st.subheader("Musteri Listesi")
    musteriler = st.session_state.get("crm_musteriler", [])
    if musteriler:
        import pandas as pd
        df = pd.DataFrame(musteriler)
        st.dataframe(df, use_container_width=True)

        # Kanban görünüm
        st.subheader("Kanban Gorunum")
        durumlar = ["Aday", "Gorusme", "Teklif", "Sozlesme", "Tamamlandi"]
        cols = st.columns(len(durumlar))
        for i, durum in enumerate(durumlar):
            with cols[i]:
                st.markdown(f"**{durum}**")
                filtered = [m for m in musteriler if m["durum"] == durum]
                for m in filtered:
                    st.markdown(
                        f"<div style='background:#f0f0f0; padding:8px; "
                        f"border-radius:4px; margin:4px 0; font-size:12px;'>"
                        f"<b>{m['ad']}</b><br>{m.get('tel','')}</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("Henuz musteri eklenmedi. Yukaridaki formdan ekleyebilirsiniz.")

    # Proje listesi
    st.subheader("Proje Listesi")
    projeler = st.session_state.get("crm_projeler", [])
    if projeler:
        import pandas as pd
        df_p = pd.DataFrame(projeler)
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("Henuz proje eklenmedi.")


def sayfa_workflow():
    """Is Akisi Motoru — Gorev zamanlama ve workflow editor."""
    st.header("Is Akisi Motoru")

    # Hazır şablonlar
    st.subheader("Hazir Is Akisi Sablonlari")

    sablonlar = {
        "Standart Konut Projesi": [
            {"gorev": "Parsel analizi", "sure_gun": 2, "bagimllik": None},
            {"gorev": "Imar parametreleri belirleme", "sure_gun": 1, "bagimllik": "Parsel analizi"},
            {"gorev": "Fizibilite raporu", "sure_gun": 3, "bagimllik": "Imar parametreleri belirleme"},
            {"gorev": "Kat plani tasarimi", "sure_gun": 5, "bagimllik": "Fizibilite raporu"},
            {"gorev": "3D modelleme", "sure_gun": 3, "bagimllik": "Kat plani tasarimi"},
            {"gorev": "Yapi ruhsati basvurusu", "sure_gun": 10, "bagimllik": "Kat plani tasarimi"},
            {"gorev": "Insaat baslangici", "sure_gun": 0, "bagimllik": "Yapi ruhsati basvurusu"},
        ],
        "Hizli Fizibilite": [
            {"gorev": "Parsel secimi", "sure_gun": 1, "bagimllik": None},
            {"gorev": "Otomatik hesaplama", "sure_gun": 0, "bagimllik": "Parsel secimi"},
            {"gorev": "Maliyet analizi", "sure_gun": 1, "bagimllik": "Otomatik hesaplama"},
            {"gorev": "Rapor olusturma", "sure_gun": 1, "bagimllik": "Maliyet analizi"},
        ],
        "Tam Proje Sureci": [
            {"gorev": "Arazi kesfesi", "sure_gun": 3, "bagimllik": None},
            {"gorev": "Jeolojik etut", "sure_gun": 15, "bagimllik": "Arazi kesfesi"},
            {"gorev": "Mimari proje", "sure_gun": 30, "bagimllik": "Jeolojik etut"},
            {"gorev": "Statik proje", "sure_gun": 20, "bagimllik": "Mimari proje"},
            {"gorev": "Tesisat projeleri", "sure_gun": 15, "bagimllik": "Mimari proje"},
            {"gorev": "Ruhsat sureci", "sure_gun": 30, "bagimllik": "Statik proje"},
            {"gorev": "Insaat (kaba)", "sure_gun": 120, "bagimllik": "Ruhsat sureci"},
            {"gorev": "Insaat (ince)", "sure_gun": 90, "bagimllik": "Insaat (kaba)"},
            {"gorev": "Iskan", "sure_gun": 30, "bagimllik": "Insaat (ince)"},
        ],
    }

    sablon_sec = st.selectbox("Sablon Sec", list(sablonlar.keys()),
                               key="wf_sablon")

    if st.button("Sablonu Yukle", type="primary", key="wf_yukle"):
        st.session_state.wf_gorevler = list(sablonlar[sablon_sec])
        st.success(f"Sablon yuklendi: {sablon_sec}")

    # Görev listesi
    gorevler = st.session_state.get("wf_gorevler", [])

    if gorevler:
        st.subheader("Gorev Listesi")
        import pandas as pd
        df = pd.DataFrame(gorevler)
        st.dataframe(df, use_container_width=True)

        # Basit Gantt görünümü
        st.subheader("Zaman Cizelgesi")
        cumulative_day = 0
        for g in gorevler:
            days = g["sure_gun"]
            bar_width = max(days * 3, 10)
            left_offset = cumulative_day * 3
            st.markdown(
                f"<div style='display:flex; align-items:center; margin:2px 0;'>"
                f"<div style='width:200px; font-size:11px;'>{g['gorev']}</div>"
                f"<div style='margin-left:{left_offset}px; background:#1E88E5; "
                f"height:18px; width:{bar_width}px; border-radius:3px; "
                f"color:white; font-size:10px; padding:1px 4px;'>"
                f"{days}g</div></div>",
                unsafe_allow_html=True,
            )
            cumulative_day += days

        st.caption(f"Toplam tahmini sure: {sum(g['sure_gun'] for g in gorevler)} gun")

    # Manuel görev ekleme
    with st.expander("Gorev Ekle", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            yeni_gorev = st.text_input("Gorev Adi", key="wf_yeni_gorev")
        with col2:
            yeni_sure = st.number_input("Sure (gun)", 0, 365, 5, key="wf_yeni_sure")
        with col3:
            mevcut = [g["gorev"] for g in gorevler] if gorevler else []
            yeni_bag = st.selectbox("Bagimlilik",
                                     [None] + mevcut, key="wf_yeni_bag")

        if st.button("Gorev Ekle", key="wf_ekle"):
            if yeni_gorev:
                if "wf_gorevler" not in st.session_state:
                    st.session_state.wf_gorevler = []
                st.session_state.wf_gorevler.append({
                    "gorev": yeni_gorev,
                    "sure_gun": yeni_sure,
                    "bagimllik": yeni_bag,
                })
                st.success(f"Gorev eklendi: {yeni_gorev}")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# SAYFA YÖNLENDİRME
# ═══════════════════════════════════════════════════════════════
SAYFA_MAP = {
    "1_parsel":       sayfa_parsel,
    "2_konum":        sayfa_konum,
    "3_imar":         sayfa_imar,
    "4_hesaplama":    sayfa_hesaplama,
    "5_daire":        sayfa_daire,
    "6_plan":         sayfa_plan,
    "7_ai":           sayfa_ai,
    "8_3d":           sayfa_3d,
    "9_render":       sayfa_render,
    "10_fizibilite":  sayfa_fizibilite,
    "11_deprem":      sayfa_deprem,
    "12_enerji":      sayfa_enerji,
    "13_gantt":       sayfa_gantt,
    "14_karsilastir": sayfa_karsilastir,
    "15_irtifak":     sayfa_irtifak,
    "16_ruhsat":      sayfa_ruhsat,
    "17_muteahhit":   sayfa_muteahhit,
    "18_rapor":       sayfa_rapor,
    "19_whatsapp":    sayfa_whatsapp,
    "20_veri":        sayfa_veri,
    "21_crm":         sayfa_crm,
    "22_workflow":    sayfa_workflow,
    "23_ajan_panel":  sayfa_ajan_panel,
    "24_firsat":      sayfa_firsat,
    "25_piyasa":      sayfa_piyasa,
}

# ── Progress indicator ──
try:
    from utils.navigation import render_progress_bar, render_next_step_button
    render_progress_bar()
except Exception:
    pass

# Aktif sayfayı göster
sayfa_fonksiyonu = SAYFA_MAP.get(st.session_state.aktif_sayfa, sayfa_parsel)
sayfa_fonksiyonu()

# ── Sonraki Adım butonu ──
try:
    render_next_step_button(st.session_state.aktif_sayfa)
except Exception:
    pass

# ── Her render sonrası otomatik kaydet ──
_auto_save()
