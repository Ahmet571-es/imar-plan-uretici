# Değişiklik Günlüğü

Bu proje [Anlamlı Sürümleme (Semantic Versioning)](https://semver.org/lang/tr/) standardını izler.

---

## [1.2.0] - 2026-03-25

### AŞAMA 3-4: Profesyonelleştirme

#### Eklenenler
- **Test altyapısı:** `tests/` dizini oluşturuldu; 111 pytest testi yazıldı
  - `test_imar_hesaplama.py` — İmar ve parsel hesaplama testleri
  - `test_finansal.py` — Maliyet, gelir ve fizibilite testleri
  - `test_floor_plan.py` — Kat planı üretim ve puanlama testleri
  - `test_konum.py` — Harita, güneş ve konum analizi testleri
  - `test_agents.py` — Ajan sistemi testleri
  - `conftest.py` — Ortak pytest fixture'ları (parsel ve imar parametreleri)
- **`pyproject.toml`:** Pytest ve Ruff yapılandırması merkezi dosyaya taşındı
- **`agents/` modülü:** Otonom ajan sistemi eklendi
  - `base_agent.py` — Temel ajan sınıfı (`BaseAgent`, `AgentMessage`, `AgentRun`)
  - `orchestrator.py` — Orkestratör ajan (`OrkestatorAjani`)
  - `plan_optimizasyon.py` — Plan optimizasyon ajanı
  - `maliyet_optimizasyon.py` — Maliyet optimizasyon ajanı
  - `daire_karmasi.py` — Daire karması optimizasyon ajanı
  - `toplu_fizibilite.py` — Toplu fizibilite analizi ajanı
  - `agent_config.py` — Ajan yapılandırması ve varsayılan parametreler
  - `agent_dashboard.py` — Ajan durum paneli (Streamlit)
- **`pages/` modülü:** Streamlit çok sayfalı yapı ayrıştırıldı
  - `pages_design.py`, `pages_analysis.py`, `pages_other.py`
- **`utils/safe_import.py`:** Opsiyonel bağımlılıklar için güvenli import yardımcısı
- **`analysis/parcel_comparison.py`:** Parsel karşılaştırma analizi

#### Değiştirildi
- `utils/constants.py` genişletildi: emsal harici alan sabitleri (`EMSAL_HARICI_*`), yangın güvenliği sabitleri, hava bacası ve ışıklık sabitleri eklendi
- `app.py` refactor edildi; sayfa mantığı `pages/` modülüne taşındı

#### Düzeltildi
- Emsal harici alan hesabında merdiven evi ve asansör kuyu alanı tutarsızlıkları giderildi
- Küçük parsellerde çekme mesafesi sonrası negatif alan üretimi engellendi

---

## [1.1.0] - 2026-02-10

### FAZ 1-7: Temel İmplementasyon

#### Eklenenler
- **FAZ 1 — Parsel ve İmar Modülü:**
  - `core/parcel.py` — Dikdörtgen, dörtgen, beşgen, altıgen ve düzensiz parsel geometrisi
  - `core/zoning.py` — TAKS/KAKS, çekme mesafeleri, imar parametreleri doğrulama
  - `core/apartment_divider.py` — 1+1–5+1 daire bölümleme şablonları
  - `utils/constants.py` — Duvar kalınlıkları, kapı/pencere/merdiven ölçüleri, imar varsayılanları
  - `utils/geometry_helpers.py` — Shapely tabanlı geometri yardımcıları
  - `utils/validation.py` — Girdi doğrulama
  - `config/turkish_building_codes.py` — Planlı Alanlar İmar Yönetmeliği kuralları
  - `config/room_defaults.py` — Oda tipi varsayılan boyutları
  - `config/cost_defaults.py` — İnşaat maliyet varsayılanları
- **FAZ 2 — Veri Seti Kuralları:**
  - `dataset/dataset_rules.py` — 80.000+ plan istatistiksel kuralları
  - `dataset/extract_rules.py` — Kural çıkarma motoru
- **FAZ 3 — Dual AI Plan Üretim Motoru:**
  - `ai/claude_planner.py` — Anthropic Claude plan üretici
  - `ai/grok_planner.py` — OpenAI (Grok) plan üretici
  - `ai/dual_ai_engine.py` — İki AI çıktısını birleştiren motor
  - `ai/consensus.py` — Konsensüs ve en iyi plan seçimi
  - `ai/cross_review.py` — Çapraz inceleme mekanizması
  - `ai/render_generator.py` — Fotogerçekçi render üretici
- **FAZ 4 — İteratif İyileştirme:**
  - `core/floor_plan_generator.py` — Plan üretici ve iyileştirme döngüsü
  - `core/furniture_placer.py` — Otomatik mobilya yerleştirme
  - `core/plan_scorer.py` — Plan puanlama motoru
  - `config/furniture_library.py` — Mobilya kütüphanesi
- **FAZ 5 — 3D Görselleştirme:**
  - `visualization_3d/building_model.py` — Plotly 3D bina modeli
- **FAZ 6 — Harita ve Güneş Analizi:**
  - `map/location_picker.py` — Folium tabanlı konum seçici
  - `analysis/sun_analysis.py` — Güneş açısı ve gölge analizi
  - `drawing/plan_renderer_matplotlib.py` — Matplotlib plan çizici
- **FAZ 7 — Mali Analiz ve Belgeler:**
  - `analysis/cost_estimator.py` — İnşaat maliyet tahmini
  - `analysis/revenue_estimator.py` — Satış geliri tahmini
  - `analysis/feasibility.py` — Fizibilite analizi ve duyarlılık
  - `analysis/earthquake_risk.py` — AFAD + TBDY 2018 deprem risk analizi
  - `analysis/energy_performance.py` — A–G enerji sınıfı tahmini
  - `analysis/construction_timeline.py` — Gantt chart inşaat takvimi
  - `legal/kat_irtifaki.py` — Kat irtifakı belgesi taslağı
  - `legal/ruhsat_paketi.py` — Ruhsat paketi taslağı
  - `export/pdf_exporter.py`, `export/svg_exporter.py`, `export/dxf_exporter.py` — Çoklu format dışa aktarma
  - `export/feasibility_report.py` — Fizibilite raporu (PDF)
  - `database/db.py` — SQLAlchemy + SQLite proje veritabanı
  - `core/tkgm_api.py` — TKGM parsel sorgulama entegrasyonu

#### Değiştirildi
- `app.py` — 25 sayfalı Streamlit uygulaması olarak yapılandırıldı

---

## [1.0.0] - 2026-01-15

### İlk Sürüm

#### Eklenenler
- Temel Streamlit uygulama iskelet yapısı
- Dikdörtgen parsel girişi ve basit TAKS/KAKS hesaplama
- `requirements.txt` bağımlılık listesi
- MIT lisansı
