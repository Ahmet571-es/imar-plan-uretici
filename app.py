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

# ── Stil — Profesyonel SaaS görünümü ve mobil uyumluluk ──
st.markdown("""
<style>
    /* Genel düzen */
    .block-container { padding-top: 1.5rem; max-width: 1200px; }

    /* Metrik kartları — profesyonel görünüm */
    .stMetric > div {
        background: linear-gradient(135deg, #f8f9fa 0%, #e8eaf6 100%);
        border-radius: 10px;
        padding: 14px;
        border-left: 4px solid #1565C0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stMetric > div:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(21,101,192,0.15);
    }
    .stMetric label { color: #546E7A !important; font-size: 0.85rem; letter-spacing: 0.02em; }
    .stMetric [data-testid="stMetricValue"] { color: #1565C0 !important; font-weight: 700; }
    .stMetric [data-testid="stMetricDelta"] { font-size: 0.8rem; }

    /* Kenar çubuğu */
    div[data-testid="stSidebar"] { background: #1a1a2e; }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3 { color: #e0e0e0; }

    /* Bilgi kutuları */
    .success-box { background: #e8f5e9; border-left: 4px solid #4CAF50; padding: 12px; border-radius: 4px; margin: 8px 0; }
    .warning-box { background: #fff3e0; border-left: 4px solid #FF9800; padding: 12px; border-radius: 4px; margin: 8px 0; }
    .info-box { background: #e3f2fd; border-left: 4px solid #1E88E5; padding: 12px; border-radius: 4px; margin: 8px 0; }

    /* Buton tutarlılığı */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1565C0, #1E88E5);
        border: none;
        font-weight: 600;
        transition: opacity 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.9; }

    /* İndirme butonları — ayırt edici stil */
    .stDownloadButton > button {
        border: 1px solid #1565C0;
        color: #1565C0;
        font-weight: 500;
        transition: background 0.15s ease;
    }
    .stDownloadButton > button:hover {
        background: #e3f2fd;
    }

    /* Tablo ve veri çerçevesi tutarlılığı */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Sekmeler — tutarlı renk şeması */
    .stTabs [data-baseweb="tab-highlight"] { background-color: #1565C0; }
    .stTabs [data-baseweb="tab"] { font-weight: 500; }

    /* Profesyonel alt bilgi */
    .app-footer {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        margin-top: 3rem;
        border-top: 1px solid #e0e0e0;
        color: #9e9e9e;
        font-size: 0.75rem;
        line-height: 1.6;
    }
    .app-footer a { color: #1565C0; text-decoration: none; }

    /* Mobil uyumluluk */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem; }
        div[data-testid="stSidebar"] { width: 250px !important; }
        .stMetric > div { padding: 8px; font-size: 0.85rem; }
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.15rem !important; }
        /* Mobilde tablo yatay kaydırma */
        .stDataFrame { overflow-x: auto; }
    }

    /* Tablet uyumluluk */
    @media (max-width: 1024px) and (min-width: 769px) {
        .block-container { padding: 0.75rem; }
        .stMetric > div { padding: 10px; }
    }
</style>
""", unsafe_allow_html=True)

# ── Basit Kimlik Doğrulama Katmanı ──
# st.secrets içinde AUTH_ENABLED=true ise giriş formu gösterilir.
# AUTH_ENABLED yoksa veya false ise doğrudan uygulamaya geçilir.
# İleride Supabase Auth entegrasyonu için taslak görevi görür.


def _kimlik_dogrulama_kontrol():
    """Basit parola kapısı. Secrets'tan kullanıcı adı/parola doğrular.

    Gerekli secrets anahtarları (AUTH_ENABLED=true olduğunda):
        AUTH_USERNAME: Kullanıcı adı
        AUTH_PASSWORD: Parola
    """
    try:
        auth_aktif = st.secrets.get("AUTH_ENABLED", False)
    except Exception:
        # secrets.toml yoksa veya okunamazsa doğrulamayı atla
        return True

    # AUTH_ENABLED string olarak da gelebilir
    if isinstance(auth_aktif, str):
        auth_aktif = auth_aktif.lower() in ("true", "1", "yes", "evet")

    if not auth_aktif:
        return True

    # Oturum zaten doğrulanmışsa tekrar sorma
    if st.session_state.get("_authenticated", False):
        return True

    # Giriş formu göster
    st.markdown("## 🔐 Giriş")
    st.markdown("Bu uygulamaya erişmek için giriş yapmanız gerekmektedir.")

    with st.form("login_form"):
        kullanici_adi = st.text_input("Kullanıcı Adı", key="_login_user")
        parola = st.text_input("Parola", type="password", key="_login_pass")
        giris_btn = st.form_submit_button("Giriş Yap", type="primary")

    if giris_btn:
        dogru_kullanici = st.secrets.get("AUTH_USERNAME", "")
        dogru_parola = st.secrets.get("AUTH_PASSWORD", "")

        if kullanici_adi == dogru_kullanici and parola == dogru_parola:
            st.session_state["_authenticated"] = True
            st.rerun()
        else:
            st.error("Kullanıcı adı veya parola hatalı.")

    return False


# Kimlik doğrulama kapısı — geçemezse uygulamanın geri kalanı çalışmaz
if not _kimlik_dogrulama_kontrol():
    st.stop()

# ── Otomatik Kalıcılık Sistemi ──
# Her değişiklikte /tmp'ye otomatik kaydet, sayfa yenilendiğinde otomatik yükle.
# Kullanıcı hiçbir şey yapmak zorunda değil.

import json as _json
import os as _os

_AUTOSAVE_PATH = "/tmp/imar_plan_autosave.json"


def _auto_save():
    """Session state'i /tmp'ye otomatik kaydet.

    # GÜVENLİK: API key'ler kaydedilmez. Sadece parsel/imar verileri yazılır.
    # Önbellek: Yan etkili fonksiyon, @st.cache_data KULLANILMAZ.
    """
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
        # GÜVENLİK: API key'ler /tmp'ye kaydedilmez — sadece session'da tutulur.

        with open(_AUTOSAVE_PATH, "w") as f:
            _json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def _auto_load():
    """Sayfa yenilendiğinde /tmp'den otomatik yükle.

    # Önbellek: Bu fonksiyon oturum durumuna bağlıdır, @st.cache_data KULLANILMAZ.
    """
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

        # GÜVENLİK: API key'ler /tmp'den yüklenmez — sadece st.secrets veya kullanıcı girişi.

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
        "9_render":       "🎨 [9] Fotogerçekçi Render",
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

    st.markdown("### 📖 YARDIM")
    if st.button("📖 Kullanım Kılavuzu", key="nav_kilavuz", use_container_width=True,
                 type="primary" if st.session_state.aktif_sayfa == "kilavuz" else "secondary"):
        st.session_state.aktif_sayfa = "kilavuz"
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

    st.caption("v2.0 — Profesyonel SaaS Platformu")

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
                        text = text.strip()
                        try:
                            parsed = json.loads(text)
                        except json.JSONDecodeError as je:
                            st.error(f"AI geçersiz JSON döndürdü: {je}")
                            st.code(text[:500], language="text")
                            st.stop()

                        # Parsed sonucu bina programına dönüştür
                        st.success("✅ AI analizi tamamlandı!")
                        st.json(parsed)
                        st.info("Yukarıdaki sonucu Manuel Giriş sekmesinden düzenleyebilirsiniz.")
                    except json.JSONDecodeError:
                        pass  # Zaten yukarıda ele alındı
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


def sayfa_kilavuz():
    """Kullanım Kılavuzu — Adım adım detaylı yönlendirme."""
    st.header("📖 Kullanım Kılavuzu")
    st.markdown("Bu kılavuz, İmar Plan Üretici uygulamasını adım adım nasıl kullanacağınızı açıklar.")

    # ── Genel Bakış ──
    with st.expander("🏠 Genel Bakış — Uygulama Nedir?", expanded=True):
        st.markdown("""
**İmar Uyumlu Kat Planı Üretici**, Türkiye'ye özgü parsel ölçüleri ve imar parametrelerinden
başlayarak kat planları üreten kapsamlı bir platformdur.

**Ne Yapabilirsiniz?**
- Parsel geometrinizi girerek imar hesaplamalarını otomatik yapabilirsiniz
- 5 farklı layout tipinde profesyonel kat planları üretebilirsiniz
- 3D bina modeli oluşturabilirsiniz
- Mali fizibilite ve Monte Carlo risk analizi yapabilirsiniz
- Deprem risk analizi ve enerji performans hesabı yapabilirsiniz
- SVG, DXF (AutoCAD) ve PDF formatlarında dışa aktarabilirsiniz
- AI (Claude + Grok) ile doğal dil komutlarıyla plan üretebilirsiniz

**Önerilen İş Akışı:** Sayfaları 1'den 25'e doğru sırayla takip edin.
        """)

    # ── ADIM 1 ──
    with st.expander("📍 ADIM 1 — Parsel Girişi (Sayfa 1)"):
        st.markdown("""
### Parsel Geometrinizi Tanımlayın

**Manuel Giriş Sekmesi:**
1. **Parsel Şekli** seçin: Dikdörtgen, Dörtgen, Beşgen, Altıgen veya Düzensiz
2. **Kuzey Yönü** seçin (ön cephe yönü)
3. Dikdörtgen için **En** ve **Boy** değerlerini metre cinsinden girin
   - Örnek: En = 22m, Boy = 28m → 616 m² parsel
4. Çokgen parseller için kenar uzunluklarını ve açıları girin
5. **"Parseli Oluştur"** butonuna tıklayın

**TKGM Otomatik Sekmesi:**
1. İl, İlçe, Mahalle bilgilerini seçin
2. Ada ve Parsel numarasını girin (örnek: Ada 1301, Parsel 7)
3. **"Parsel Sorgula"** butonuna tıklayın
4. TKGM API'den otomatik olarak parsel sınırları çekilir

**Sonuç:** Sağ tarafta parsel alan, çevre, köşe sayısı ve çizimi görüntülenir.
        """)

    # ── ADIM 2 ──
    with st.expander("🗺️ ADIM 2 — Konum & Çevre Analizi (Sayfa 2)"):
        st.markdown("""
### Konumunuzu Belirleyin

1. **Enlem ve Boylam** değerlerini girin veya hızlı şehir seçimi yapın
2. Harita üzerinde parselin konumunu görün
3. **"Güneş Analizi Yap"** butonuna tıklayarak:
   - En iyi cephe yönünü öğrenin (genellikle güney)
   - Yıllık güneş saatini hesaplayın
   - Cephe bazlı güneş dağılımını görün
   - Salon ve balkon için optimum yön önerileri alın

**İpucu:** Güneş analizi sonuçları, kat planı üretiminde salon ve balkon yönünü
otomatik olarak optimize etmek için kullanılır.
        """)

    # ── ADIM 3 ──
    with st.expander("📐 ADIM 3 — İmar Bilgileri (Sayfa 3)"):
        st.markdown("""
### Belediye İmar Parametrelerini Girin

**Temel Parametreler:**
1. **Kat Adedi** — Belediye imar planında izin verilen kat sayısı (örnek: 4)
2. **İnşaat Nizamı** — A (Ayrık), B (Bitişik) veya BL (Blok)
3. **TAKS** — Taban Alanı Kat Sayısı (örnek: 0.35 = parselin %35'i)
4. **KAKS / Emsal** — Toplam inşaat alanı oranı (örnek: 1.40)

**Çekme Mesafeleri:**
5. **Ön Bahçe** — Yoldan minimum mesafe (genellikle 5m)
6. **Yan Bahçe** — Komşu parselden minimum mesafe (genellikle 3m)
7. **Arka Bahçe** — 0 girilirse H/2 kuralı otomatik uygulanır (Yönetmelik Madde 6)

**Ek Gereksinimler:**
8. Asansör (4+ katta otomatik zorunlu), Sığınak, Otopark seçenekleri

**"İmar Bilgilerini Kaydet"** butonuna tıklayın.

**Nereden Bulunur:** Bu bilgileri belediyenizin e-imar uygulamasından veya
imar müdürlüğünden alabilirsiniz.
        """)

    # ── ADIM 4 ──
    with st.expander("📊 ADIM 4 — Hesaplama Sonuçları (Sayfa 4)"):
        st.markdown("""
### Otomatik Hesaplama Sonuçlarını İnceleyin

Bu sayfa parsel + imar bilgilerinden otomatik hesaplama yapar:

**Görüntülenen Metrikler:**
- **Parsel Alanı** — Girdiğiniz parselin toplam alanı
- **Maks. Taban Alanı** — TAKS sınırına göre bina oturumu
- **Toplam İnşaat Alanı** — KAKS × parsel alanı
- **Kat Başı Net Alan** — Dairelere kalan alan (ortak alanlar düşülmüş)
- **Emsal Harici Toplam** — Sığınak, otopark, merdiven, asansör, giriş holü

**Görselleştirmeler:**
- Ortak alan dağılımı pasta grafiği
- Parsel + yapılaşma alanı üst üste çizimi

**Uyarılar:** Çekme mesafeleri, KAKS/TAKS uyumsuzluğu, bina yüksekliği
limiti gibi sorunlar otomatik tespit edilir.
        """)

    # ── ADIM 5 ──
    with st.expander("🏠 ADIM 5 — Daire Bölümleme (Sayfa 5)"):
        st.markdown("""
### Daire Tipini ve Oda Programını Belirleyin

**Manuel Giriş:**
1. **Kat başına daire sayısı** seçin (1-8 arası)
2. **Daire tipi** seçin (1+1, 2+1, 3+1, 4+1, 5+1)
3. Her daire için önerilen alan otomatik hesaplanır
4. **"Bina Programını Oluştur"** butonuna tıklayın
5. Oda alanlarını tabloda düzenleyebilirsiniz
6. Her oda için minimum alan kontrolü yapılır (İmar Kanunu'na göre)

**AI ile Doğal Dil:**
1. API Key'inizi sidebar'dan girin
2. Doğal dille daire programınızı yazın:
   - *"Her katta 2 daire, 3+1, salon 30m², yatak odaları 15m²"*
3. AI analiz edip JSON formatında program oluşturur

**Minimum Alan Kontrolleri:** Salon ≥16m², Yatak ≥9m², Mutfak ≥5m², Banyo ≥3.5m²
        """)

    # ── ADIM 6 ──
    with st.expander("📋 ADIM 6 — Kat Planı Üretimi (Sayfa 6)"):
        st.markdown("""
### Profesyonel Kat Planları Üretin

**Profesyonel Üretim (API key gerektirmez):**
1. **Daire Tipi** ve **Güneş Yönü** seçin
2. **Alternatif Sayısı** belirleyin (2-4 arası)
3. **Hedef Daire Alanı** girin
4. **"Profesyonel Plan Üret"** butonuna tıklayın
5. Her plan 0-100 arası puanlanır (11 kriter)

**5 Layout Tipi:**
- Merkez Koridor (klasik Türk dairesi)
- L-Şekilli Koridor
- T-Şekilli Koridor
- Kısa Koridor (kompakt)
- Açık Plan (salon + mutfak birleşik)

**Puanlama Kriterleri:** Oda boyut uyumu, bitişiklik, dış cephe erişimi,
ıslak hacim gruplaması, güneş optimizasyonu, pencere/zemin oranı

**Plan Seçimi:** Beğendiğiniz planın altındaki **"Plan Seç"** butonuna tıklayın.

**Dışa Aktarma:** SVG ve DXF formatında indirme butonları her planın altında yer alır.

**AI Destekli Üretim:** Claude + Grok dual AI motoru ile 4 alternatif üretir,
çapraz değerlendirme yapar, en iyi 3'ü seçer.
        """)

    # ── ADIM 7 ──
    with st.expander("🤖 ADIM 7 — AI İyileştirme & Tefriş (Sayfa 7)"):
        st.markdown("""
### Mobilya Yerleştirme ve AI İyileştirme

1. Seçili plan otomatik yüklenir
2. **"Mobilya Yerleştir"** butonuna tıklayın
3. Her oda tipi için uygun mobilyalar otomatik yerleştirilir:
   - Salon: koltuk takımı, TV ünitesi, sehpa
   - Yatak odası: yatak, komodin, dolap
   - Mutfak: tezgah, ocak, buzdolabı, masa
   - Banyo: küvet/duş, lavabo, klozet
4. Mobilya listesi sağ panelde görüntülenir
5. Plan + mobilya birlikte çizilir
        """)

    # ── ADIM 8 ──
    with st.expander("🏗️ ADIM 8 — 3D Görselleştirme (Sayfa 8)"):
        st.markdown("""
### İnteraktif 3D Bina Modeli

1. Seçili plan otomatik yüklenir (yoksa demo plan gösterilir)
2. **Kat Sayısı** ayarlayın
3. **Çatı Tipi** seçin: Kırma (eğimli) veya Teras (düz)
4. **Patlak Görünüm** ile katları ayrı ayrı görün
5. **Kat Filtre** ile tek bir katı inceleyin
6. Fare ile döndürme, yakınlaştırma, kaydırma yapabilirsiniz

**3D Modelde Görünenler:**
- Duvarlar (dış/iç farklı renk)
- Pencereler (cam yüzey + çerçeve)
- Kapılar
- Merdiven (basamak detayı)
- Balkon (korkuluk dikmeleri)
- Çatı (kırma veya teras)
- Parsel zemin alanı
        """)

    # ── ADIM 9-10 ──
    with st.expander("💰 ADIM 9 — Mali Fizibilite (Sayfa 10)"):
        st.markdown("""
### Yatırım Fizibilite Analizi

**Parametreleri Girin:**
1. **İl** seçin (bölgesel maliyet farkı uygulanır)
2. **Yapı Kalitesi** seçin: Ekonomik / Orta / Lüks
3. **Arsa Maliyeti** girin (₺)
4. **m² Satış Fiyatı** girin (₺)
5. **"Fizibilite Hesapla"** butonuna tıklayın

**Sonuçlar:**
- Toplam Maliyet / Gelir / Kâr-Zarar
- Kâr Marjı (%) ve ROI (%)
- Başabaş m² satış fiyatı
- Kârlılık endeksi ve yatırım geri dönüş süresi
- Maliyet dağılım grafiği

**Duyarlılık Analizi:** Maliyet ve satış fiyatındaki değişimlerin
kâr marjına etkisini 4×5 ısı haritasında görün.

**Monte Carlo Simülasyonu:**
1. Maliyet ve gelir belirsizlik oranlarını ayarlayın
2. **"Simülasyon Çalıştır"** butonuna tıklayın (5000 senaryo)
3. Zarar olasılığını, P5/P50/P95 değerlerini ve histogram grafiğini görün

**PDF Rapor:** Hesaplama sonrası **"📄 Fizibilite Raporu İndir"** butonu ile
profesyonel PDF rapor indirin.
        """)

    # ── ADIM 10 ──
    with st.expander("🔬 ADIM 10 — Deprem Risk Analizi (Sayfa 11)"):
        st.markdown("""
### TBDY 2018 Deprem Risk Değerlendirmesi

1. **Enlem/Boylam** girin (veya konum sayfasından aktarılır)
2. **Kat Sayısı** girin
3. **Zemin Sınıfı** seçin:
   - ZA: Sağlam kaya
   - ZB: Kaya
   - ZC: Çok sıkı kum/sert kil (en yaygın)
   - ZD: Sıkı kum/katı kil
   - ZE: Yumuşak zemin
4. **"Deprem Analizi Yap"** butonuna tıklayın

**Sonuçlar:**
- Risk seviyesi (Düşük / Orta / Yüksek / Çok Yüksek)
- Ss (kısa periyot) ve S1 (1sn periyot) ivme değerleri
- Taşıyıcı sistem önerisi (Çerçeve, Perde, Tünel Kalıp vb.)
- Kolon grid önerisi
- Detaylı analiz tablosu
        """)

    # ── ADIM 11 ──
    with st.expander("⚡ ADIM 11 — Enerji Performans (Sayfa 12)"):
        st.markdown("""
### Bina Enerji Kimlik Belgesi Tahmini

1. **Duvar Yalıtımı** seçin (5cm EPS → 12cm XPS)
2. **Pencere Tipi** seçin (Tek cam → Low-E)
3. **Çatı Yalıtımı** ve **Isıtma Sistemi** seçin
4. **Pencere/Duvar Oranı** ayarlayın (0.15 - 0.50)
5. **"Enerji Hesapla"** butonuna tıklayın

**Sonuçlar:**
- Enerji sınıfı (A-G) renkli gösterge
- Yıllık ısıtma/soğutma tüketimi (kWh/m²·yıl)
- Yıllık enerji maliyeti (₺)
- İyileştirme önerileri
        """)

    # ── Agentler ──
    with st.expander("🤖 ADIM 12 — Otonom Agentler (Sayfa 23-25)"):
        st.markdown("""
### Agent Sistemi ile Toplu Analiz

**Ajan Kontrol Paneli (Sayfa 23):**
1. 4 farklı ajan ve 1 orkestratör bulunur
2. **"Tüm Ajanları Çalıştır"** butonuna tıklayın
3. İlerleme çubuğu ile durumu takip edin

**Ajanlar:**
- **Plan Optimizasyon** — 200 plan varyasyonu üretir, en iyilerini seçer
- **Maliyet Optimizasyon** — 4 yapı sistemi × 3 malzeme karşılaştırır
- **Daire Karması** — 2+1/3+1/4+1 kombinasyonlarını kârlılığa göre optimize eder
- **Toplu Fizibilite** — 8 farklı parseli toplu analiz eder

**Fırsat Merkezi (Sayfa 24):** Ajan sonuçlarından en kârlı fırsatları listeler
**Piyasa İstihbarat (Sayfa 25):** Plan kalite istatistikleri ve aksiyon önerileri
        """)

    # ── API Ayarları ──
    with st.expander("🔑 API Ayarları"):
        st.markdown("""
### AI Özelliklerini Aktifleştirme

Uygulama API key olmadan da çalışır (algoritmik plan üretimi).
AI destekli özellikler için:

1. **Claude API Key:** [console.anthropic.com](https://console.anthropic.com) adresinden alın
2. **Grok API Key:** [console.x.ai](https://console.x.ai) adresinden alın
3. Sidebar'daki **"API Ayarları"** bölümünden girin

**API Key olmadan çalışan özellikler:**
- Tüm imar hesaplamaları
- Profesyonel plan üretimi (5 layout tipi)
- 3D görselleştirme
- Mali fizibilite ve Monte Carlo
- Deprem / enerji / güneş analizi
- Agent sistemi
- SVG / DXF / PDF export

**API Key gerektiren özellikler:**
- AI destekli plan üretimi (Dual Engine)
- Doğal dil daire bölümleme
- Fotogerçekçi render
- AI plan iyileştirme
        """)

    # ── Sık Sorulan Sorular ──
    with st.expander("❓ Sık Sorulan Sorular"):
        st.markdown("""
**S: TAKS ve KAKS değerlerini nereden bulurum?**
C: Belediyenizin e-imar uygulamasından veya imar müdürlüğünden temin edebilirsiniz.

**S: Arka bahçe mesafesi nedir?**
C: 0 girerseniz otomatik olarak H/2 kuralı uygulanır (bina yüksekliğinin yarısı).

**S: Plan puanı ne anlama gelir?**
C: 0-100 arası bir değerdir. 11 kriter üzerinden değerlendirilir:
oda boyutları, bitişiklik, dış cephe, ıslak hacim gruplaması, güneş yönü,
koridor verimliliği, pencere/zemin oranı, yapısal grid, yönetmelik uyumu.

**S: DXF dosyasını nerede açabilirim?**
C: AutoCAD, LibreCAD, DraftSight gibi CAD yazılımlarında açabilirsiniz.

**S: API key güvenliği nasıl sağlanır?**
C: API key'ler sadece oturum süresince bellekte tutulur, diske kaydedilmez.

**S: Uygulama hangi yönetmeliklere uyar?**
C: Planlı Alanlar İmar Yönetmeliği (03.07.2017/30113) ve TBDY 2018.
        """)


# ── Placeholder'lar (Dış API gerektiren sayfalar) ──
def placeholder_sayfa(baslik, faz, aciklama=""):
    st.header(baslik)
    st.info(f"Bu sayfa **{faz}**'da geliştirilecektir. Dış servis entegrasyonu gerektirir.")
    if aciklama:
        st.markdown(aciklama)

def sayfa_whatsapp():
    """Sayfa 19 — WhatsApp Bot yapılandırma ve mesaj simülasyonu."""
    st.header("📱 WhatsApp Bot")

    st.markdown("""
    WhatsApp üzerinden sahadan hızlı fizibilite sorgusu yapılabilir.
    Entegrasyon için **Green API** veya **Twilio** hesabı gerekir.
    """)

    # API yapılandırma
    with st.expander("API Yapılandırma", expanded=False):
        provider = st.selectbox("Servis Sağlayıcı", ["Green API", "Twilio"], key="wa_provider")
        if provider == "Green API":
            st.text_input("Instance ID", type="password", key="wa_instance")
            st.text_input("API Token", type="password", key="wa_token")
        else:
            st.text_input("Account SID", type="password", key="wa_sid")
            st.text_input("Auth Token", type="password", key="wa_auth")
        st.caption("API bilgileri sadece bu oturumda tutulur, kaydedilmez.")

    # Mesaj simülasyonu
    st.subheader("Mesaj Simülasyonu")
    st.info("API yapılandırılmadan demo modda mesaj simülasyonu yapabilirsiniz.")

    ornek_mesajlar = [
        "Ankara Çankaya'da 600m² parsel, 4 kat TAKS 0.35 KAKS 1.40 fizibilite hesapla",
        "İstanbul Kadıköy 450m² arsa ne kadar kâr getirir?",
        "3+1 daire maliyeti nedir Ankara Etimesgut?",
    ]
    secili = st.selectbox("Örnek Mesaj", ornek_mesajlar, key="wa_ornek")

    mesaj = st.text_input("Mesaj Girin", value=secili, key="wa_mesaj")

    if st.button("📤 Simüle Et", type="primary", key="wa_gonder"):
        with st.spinner("Analiz ediliyor..."):
            # Basit anahtar kelime analizi
            yanit = _whatsapp_demo_yanit(mesaj)
            st.session_state.wa_yanit = yanit

    if "wa_yanit" in st.session_state:
        st.markdown("---")
        st.markdown("**🤖 Bot Yanıtı:**")
        st.success(st.session_state.wa_yanit)

    # Mesaj geçmişi
    st.markdown("---")
    st.subheader("Mesaj Geçmişi")
    if "wa_gecmis" not in st.session_state:
        st.session_state.wa_gecmis = []
    if "wa_yanit" in st.session_state and mesaj:
        kayit = {"mesaj": mesaj, "yanit": st.session_state.wa_yanit}
        if not st.session_state.wa_gecmis or st.session_state.wa_gecmis[-1] != kayit:
            st.session_state.wa_gecmis.append(kayit)
    for g in reversed(st.session_state.wa_gecmis[-10:]):
        st.markdown(f"📩 **{g['mesaj']}**")
        st.markdown(f"🤖 {g['yanit']}")
        st.markdown("---")


def _whatsapp_demo_yanit(mesaj: str) -> str:
    """WhatsApp demo: basit anahtar kelime bazlı yanıt üretici."""
    mesaj_lower = mesaj.lower()
    if "fizibilite" in mesaj_lower or "kâr" in mesaj_lower or "kar" in mesaj_lower:
        return (
            "📊 Hızlı Fizibilite Tahmini:\n"
            "• Tahmini inşaat maliyeti: ~₺25-30M\n"
            "• Tahmini satış geliri: ~₺35-40M\n"
            "• Kâr marjı: %15-25\n\n"
            "Detaylı analiz için uygulamamıza girin: [link]"
        )
    elif "maliyet" in mesaj_lower or "fiyat" in mesaj_lower:
        return (
            "💰 Maliyet Tahmini:\n"
            "• Orta kalite konut: ₺28.000-35.000/m²\n"
            "• Lüks konut: ₺42.000-55.000/m²\n"
            "• Arsa maliyeti hariç\n\n"
            "Bölgeye özel fiyat için il/ilçe belirtin."
        )
    elif "parsel" in mesaj_lower or "arsa" in mesaj_lower:
        return (
            "📍 Parsel Analizi:\n"
            "TKGM üzerinden parsel sorgulaması yapabiliriz.\n"
            "Lütfen il, ilçe, ada ve parsel numarasını gönderin.\n"
            "Örnek: Ankara Çankaya 1301 ada 7 parsel"
        )
    else:
        return (
            "Merhaba! İmar Plan Üretici Bot'a hoş geldiniz.\n\n"
            "Şu komutları kullanabilirsiniz:\n"
            "• 'fizibilite' — Hızlı fizibilite tahmini\n"
            "• 'maliyet' — İnşaat maliyet tahmini\n"
            "• 'parsel' — TKGM parsel sorgusu\n\n"
            "Örnek: 'Ankara 600m² parsel fizibilite hesapla'"
        )


def sayfa_veri():
    """Sayfa 20 — Veri Güncelleme ve dış kaynak entegrasyonu."""
    st.header("🔄 Veri Güncelleme")

    st.markdown("Dış kaynaklardan güncel veri çekme ve yerel veritabanını güncelleme.")

    # TCMB Döviz
    st.subheader("💱 TCMB Döviz Kurları")
    if st.button("Döviz Kurlarını Güncelle", key="veri_doviz"):
        with st.spinner("TCMB'den veri çekiliyor..."):
            try:
                import requests
                resp = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=10)
                if resp.status_code == 200:
                    # Basit XML parse
                    content = resp.text
                    import re
                    usd_match = re.search(r'<Currency.*?Kod="USD".*?<BanknoteSelling>([\d.,]+)', content, re.DOTALL)
                    eur_match = re.search(r'<Currency.*?Kod="EUR".*?<BanknoteSelling>([\d.,]+)', content, re.DOTALL)
                    usd = float(usd_match.group(1).replace(",", ".")) if usd_match else 0
                    eur = float(eur_match.group(1).replace(",", ".")) if eur_match else 0
                    st.session_state.doviz = {"USD": usd, "EUR": eur}
                    st.success("Döviz kurları güncellendi!")
                else:
                    st.warning("TCMB'ye erişilemedi. Demo veriler gösteriliyor.")
                    st.session_state.doviz = {"USD": 36.50, "EUR": 39.80}
            except Exception:
                st.session_state.doviz = {"USD": 36.50, "EUR": 39.80}
                st.info("TCMB erişimi başarısız. Demo veriler kullanılıyor.")

    if "doviz" in st.session_state:
        col1, col2 = st.columns(2)
        col1.metric("USD/TRY", f"₺{st.session_state.doviz['USD']:.2f}")
        col2.metric("EUR/TRY", f"₺{st.session_state.doviz['EUR']:.2f}")

    # İnşaat Maliyet Endeksi
    st.markdown("---")
    st.subheader("🏗️ İnşaat Maliyet Endeksi")
    import pandas as pd
    endeks_data = {
        "Dönem": ["2025 Q1", "2025 Q2", "2025 Q3", "2025 Q4", "2026 Q1"],
        "Endeks": [842.5, 871.3, 895.7, 923.1, 948.6],
        "Değişim (%)": ["+3.8", "+3.4", "+2.8", "+3.1", "+2.8"],
    }
    st.dataframe(pd.DataFrame(endeks_data), hide_index=True, use_container_width=True)
    st.caption("Kaynak: TÜİK İnşaat Maliyet Endeksi (demo veriler)")

    # Bölgesel Fiyatlar
    st.markdown("---")
    st.subheader("📊 Bölgesel m² Satış Fiyatları")
    from config.cost_defaults import get_iller
    iller = get_iller()
    secili_il = st.selectbox("İl Seçin", iller, key="veri_il")

    fiyat_data = {
        "Daire Tipi": ["1+1", "2+1", "3+1", "4+1"],
        "Ort. m² Fiyat (₺)": ["35.000", "38.000", "42.000", "48.000"],
        "Değişim (Yıllık)": ["+18%", "+15%", "+12%", "+10%"],
    }
    st.dataframe(pd.DataFrame(fiyat_data), hide_index=True, use_container_width=True)
    st.caption(f"Kaynak: {secili_il} bölgesi tahmini fiyatlar (demo veriler)")

def sayfa_crm():
    """CRM Sayfası — Müşteri ve proje takibi."""
    st.header("CRM — Müşteri ve Proje Takibi")

    from database.db import get_engine
    try:
        from sqlalchemy import text
        engine = get_engine()
    except Exception:
        engine = None

    # Müşteri ekleme formu
    with st.expander("Yeni Müşteri Ekle", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            mus_ad = st.text_input("Ad Soyad", key="crm_ad")
            mus_tel = st.text_input("Telefon", key="crm_tel")
            mus_email = st.text_input("E-posta", key="crm_email")
        with col2:
            mus_tip = st.selectbox("Müşteri Tipi",
                                    ["Bireysel", "Kurumsal", "Müteahhit"],
                                    key="crm_tip")
            mus_durum = st.selectbox("Durum",
                                      ["Aday", "Görüşme", "Teklif", "Sözleşme", "Tamamlandı"],
                                      key="crm_durum")
            mus_not = st.text_area("Notlar", key="crm_not", height=68)

        if st.button("Müşteri Kaydet", type="primary", key="crm_kaydet"):
            if not mus_ad:
                st.warning("Ad Soyad zorunludur.")
            else:
                if "crm_musteriler" not in st.session_state:
                    st.session_state.crm_musteriler = []
                st.session_state.crm_musteriler.append({
                    "ad": mus_ad, "tel": mus_tel, "email": mus_email,
                    "tip": mus_tip, "durum": mus_durum, "not": mus_not,
                })
                st.success(f"Müşteri eklendi: {mus_ad}")
                st.rerun()

    # Proje ekleme
    with st.expander("Yeni Proje Ekle", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            prj_ad = st.text_input("Proje Adı", key="crm_prj_ad")
            prj_il = st.text_input("İl/İlçe", key="crm_prj_il")
        with col2:
            prj_durum = st.selectbox("Proje Durumu",
                                      ["Fizibilite", "Tasarım", "Ruhsat", "İnşaat", "Teslim"],
                                      key="crm_prj_durum")
            prj_butce = st.number_input("Bütçe (TL)", 0, 100_000_000, 5_000_000,
                                         step=100_000, key="crm_prj_butce")

        if st.button("Proje Kaydet", type="primary", key="crm_prj_kaydet"):
            if not prj_ad:
                st.warning("Proje adı zorunludur.")
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
    st.subheader("Müşteri Listesi")
    musteriler = st.session_state.get("crm_musteriler", [])
    if musteriler:
        import pandas as pd
        df = pd.DataFrame(musteriler)
        st.dataframe(df, use_container_width=True)

        # Kanban görünüm
        st.subheader("Kanban Görünüm")
        durumlar = ["Aday", "Görüşme", "Teklif", "Sözleşme", "Tamamlandı"]
        cols = st.columns(len(durumlar))
        for i, durum in enumerate(durumlar):
            with cols[i]:
                st.markdown(f"**{durum}**")
                filtered = [m for m in musteriler if m["durum"] == durum]
                for m in filtered:
                    # GÜVENLİK: Kullanıcı girdisi HTML'e eklenmeden önce temizlenir (XSS önlemi)
                    import html as _html_mod
                    _safe_ad = _html_mod.escape(str(m['ad']))
                    _safe_tel = _html_mod.escape(str(m.get('tel', '')))
                    st.markdown(
                        f"<div style='background:#f0f0f0; padding:8px; "
                        f"border-radius:4px; margin:4px 0; font-size:12px;'>"
                        f"<b>{_safe_ad}</b><br>{_safe_tel}</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("Henüz müşteri eklenmedi. Yukarıdaki formdan ekleyebilirsiniz.")

    # Proje listesi
    st.subheader("Proje Listesi")
    projeler = st.session_state.get("crm_projeler", [])
    if projeler:
        import pandas as pd
        df_p = pd.DataFrame(projeler)
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("Henüz proje eklenmedi.")


def sayfa_workflow():
    """İş Akışı Motoru — Görev zamanlama ve workflow editor."""
    st.header("İş Akışı Motoru")

    # Hazır şablonlar
    st.subheader("Hazır İş Akışı Şablonları")

    sablonlar = {
        "Standart Konut Projesi": [
            {"gorev": "Parsel analizi", "sure_gun": 2, "bagimllik": None},
            {"gorev": "İmar parametreleri belirleme", "sure_gun": 1, "bagimllik": "Parsel analizi"},
            {"gorev": "Fizibilite raporu", "sure_gun": 3, "bagimllik": "İmar parametreleri belirleme"},
            {"gorev": "Kat planı tasarımı", "sure_gun": 5, "bagimllik": "Fizibilite raporu"},
            {"gorev": "3D modelleme", "sure_gun": 3, "bagimllik": "Kat planı tasarımı"},
            {"gorev": "Yapı ruhsatı başvurusu", "sure_gun": 10, "bagimllik": "Kat planı tasarımı"},
            {"gorev": "İnşaat başlangıcı", "sure_gun": 0, "bagimllik": "Yapı ruhsatı başvurusu"},
        ],
        "Hızlı Fizibilite": [
            {"gorev": "Parsel seçimi", "sure_gun": 1, "bagimllik": None},
            {"gorev": "Otomatik hesaplama", "sure_gun": 0, "bagimllik": "Parsel seçimi"},
            {"gorev": "Maliyet analizi", "sure_gun": 1, "bagimllik": "Otomatik hesaplama"},
            {"gorev": "Rapor oluşturma", "sure_gun": 1, "bagimllik": "Maliyet analizi"},
        ],
        "Tam Proje Süreci": [
            {"gorev": "Arazi keşfesi", "sure_gun": 3, "bagimllik": None},
            {"gorev": "Jeolojik etüt", "sure_gun": 15, "bagimllik": "Arazi keşfesi"},
            {"gorev": "Mimari proje", "sure_gun": 30, "bagimllik": "Jeolojik etüt"},
            {"gorev": "Statik proje", "sure_gun": 20, "bagimllik": "Mimari proje"},
            {"gorev": "Tesisat projeleri", "sure_gun": 15, "bagimllik": "Mimari proje"},
            {"gorev": "Ruhsat süreci", "sure_gun": 30, "bagimllik": "Statik proje"},
            {"gorev": "İnşaat (kaba)", "sure_gun": 120, "bagimllik": "Ruhsat süreci"},
            {"gorev": "İnşaat (ince)", "sure_gun": 90, "bagimllik": "İnşaat (kaba)"},
            {"gorev": "İskân", "sure_gun": 30, "bagimllik": "İnşaat (ince)"},
        ],
    }

    sablon_sec = st.selectbox("Şablon Seç", list(sablonlar.keys()),
                               key="wf_sablon")

    if st.button("Şablonu Yükle", type="primary", key="wf_yukle"):
        st.session_state.wf_gorevler = list(sablonlar[sablon_sec])
        st.success(f"Şablon yüklendi: {sablon_sec}")

    # Görev listesi
    gorevler = st.session_state.get("wf_gorevler", [])

    if gorevler:
        st.subheader("Görev Listesi")
        import pandas as pd
        df = pd.DataFrame(gorevler)
        st.dataframe(df, use_container_width=True)

        # Basit Gantt görünümü
        st.subheader("Zaman Çizelgesi")
        cumulative_day = 0
        for g in gorevler:
            days = g["sure_gun"]
            bar_width = max(days * 3, 10)
            left_offset = cumulative_day * 3
            # GÜVENLİK: Kullanıcı girdisi HTML'e eklenmeden önce temizlenir (XSS önlemi)
            import html as _html_mod
            _safe_gorev = _html_mod.escape(str(g['gorev']))
            st.markdown(
                f"<div style='display:flex; align-items:center; margin:2px 0;'>"
                f"<div style='width:200px; font-size:11px;'>{_safe_gorev}</div>"
                f"<div style='margin-left:{left_offset}px; background:#1E88E5; "
                f"height:18px; width:{bar_width}px; border-radius:3px; "
                f"color:white; font-size:10px; padding:1px 4px;'>"
                f"{days}g</div></div>",
                unsafe_allow_html=True,
            )
            cumulative_day += days

        st.caption(f"Toplam tahmini süre: {sum(g['sure_gun'] for g in gorevler)} gün")

    # Manuel görev ekleme
    with st.expander("Görev Ekle", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            yeni_gorev = st.text_input("Görev Adı", key="wf_yeni_gorev")
        with col2:
            yeni_sure = st.number_input("Süre (gün)", 0, 365, 5, key="wf_yeni_sure")
        with col3:
            mevcut = [g["gorev"] for g in gorevler] if gorevler else []
            yeni_bag = st.selectbox("Bağımlılık",
                                     [None] + mevcut, key="wf_yeni_bag")

        if st.button("Görev Ekle", key="wf_ekle"):
            if yeni_gorev:
                if "wf_gorevler" not in st.session_state:
                    st.session_state.wf_gorevler = []
                st.session_state.wf_gorevler.append({
                    "gorev": yeni_gorev,
                    "sure_gun": yeni_sure,
                    "bagimllik": yeni_bag,
                })
                st.success(f"Görev eklendi: {yeni_gorev}")
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
    "kilavuz":        sayfa_kilavuz,
}

# ── Progress indicator ──
try:
    from utils.navigation import render_progress_bar, render_next_step_button
    render_progress_bar()
except Exception:
    pass

# Aktif sayfayı göster — hata yakalama ile sarmalanmış
sayfa_fonksiyonu = SAYFA_MAP.get(st.session_state.aktif_sayfa, sayfa_parsel)
try:
    sayfa_fonksiyonu()
except Exception as e:
    import logging as _logging
    _logging.getLogger(__name__).exception("Sayfa yüklenirken hata: %s", e)
    st.error(f"Sayfa yüklenirken hata oluştu: {e}")
    st.info("Lütfen sayfayı yenileyin veya farklı parametrelerle tekrar deneyin.")
    # Geliştirme modunda detaylı hata bilgisi göster
    if os.environ.get("DEBUG", "").lower() in ("1", "true"):
        import traceback
        st.code(traceback.format_exc(), language="text")

# ── Sonraki Adım butonu ──
try:
    render_next_step_button(st.session_state.aktif_sayfa)
except Exception:
    pass

# ── Profesyonel alt bilgi — sürüm ve ortam bilgisi ──
_db_tipi = "PostgreSQL (Supabase)" if os.environ.get("SUPABASE_DB_URL") else "SQLite (yerel)"
st.markdown(
    '<div class="app-footer">'
    '<strong>İmar Plan Üretici v2.0</strong> — Profesyonel İmar Uyumlu Kat Planı Üretim Platformu<br>'
    f'Veritabanı: {_db_tipi} · Python 3.11 · Streamlit<br>'
    '© 2026 Tüm hakları saklıdır.'
    '</div>',
    unsafe_allow_html=True,
)

# ── Her render sonrası otomatik kaydet ──
_auto_save()
