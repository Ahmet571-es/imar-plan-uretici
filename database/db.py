"""
Veritabanı Bağlantı Yönetimi — SQLAlchemy ile SQLite veya PostgreSQL (Supabase).

GÜVENLİK NOTU: Tüm veritabanı işlemleri SQLAlchemy ORM üzerinden yapılmaktadır.
Ham SQL string birleştirmesi (string formatting) kullanılmamaktadır.
ORM parametrik sorgular ürettiğinden SQL injection riski yoktur.
PRAGMA komutları sabit değerlerdir ve kullanıcı girdisi içermez.

SUPABASE DESTEĞİ: SUPABASE_DB_URL ortam değişkeni varsa PostgreSQL kullanılır.
Yoksa yerel SQLite veritabanına düşülür. Geliştirme ortamında değişiklik gerekmez.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Supabase PostgreSQL veya yerel SQLite seçimi ──
SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL", "")

if SUPABASE_DB_URL:
    # Supabase PostgreSQL bağlantısı — üretim ortamı
    DATABASE_URL = SUPABASE_DB_URL
    _using_postgres = True
else:
    # Yerel SQLite — geliştirme ortamı
    # Streamlit Cloud'da proje klasörü salt okunur, /tmp kullanılır
    import platform
    _is_cloud = platform.processor() == "" or os.environ.get("STREAMLIT_SHARING_MODE")

    if _is_cloud or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK):
        DB_DIR = "/tmp/imar_plan_db"
    else:
        DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")

    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_DIR, "imar_plan.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    _using_postgres = False

# ── SQLAlchemy engine oluşturma ──
if _using_postgres:
    # PostgreSQL için bağlantı havuzu ayarları
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite için thread güvenliği ve zaman aşımı ayarları
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 15},
        pool_pre_ping=True,
    )

    # SQLite WAL modu — eşzamanlı erişim performansı için
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """SQLite PRAGMA ayarlarını bağlantı kurulduğunda uygula."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ── Modeller ──

class Proje(Base):
    """Proje kaydı."""
    __tablename__ = "projeler"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proje_adi = Column(String(200), default="Yeni Proje")
    il = Column(String(50), default="")
    ilce = Column(String(50), default="")
    mahalle = Column(String(100), default="")
    ada = Column(String(20), default="")
    parsel = Column(String(20), default="")
    parsel_alani = Column(Float, default=0.0)
    kat_sayisi = Column(Integer, default=4)
    taks = Column(Float, default=0.35)
    kaks = Column(Float, default=1.40)
    toplam_insaat = Column(Float, default=0.0)
    durum = Column(String(50), default="Ön Araştırma")
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notlar = Column(Text, default="")
    veri_json = Column(JSON, default=dict)  # Tüm proje verisi JSON olarak


class FiyatVerisi(Base):
    """İlçe bazlı fiyat verisi."""
    __tablename__ = "fiyat_verileri"

    id = Column(Integer, primary_key=True, autoincrement=True)
    il = Column(String(50))
    ilce = Column(String(50))
    daire_tipi = Column(String(10))  # "1+1", "2+1", vb.
    m2_fiyat = Column(Float)
    kaynak = Column(String(50))  # "sahibinden", "hepsiemlak", "tcmb"
    tarih = Column(DateTime, default=datetime.utcnow)


class ImarCache(Base):
    """İmar bilgisi cache."""
    __tablename__ = "imar_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    il = Column(String(50))
    ilce = Column(String(50))
    ada = Column(String(20))
    parsel_no = Column(String(20))
    imar_verisi = Column(JSON)
    son_sorgu = Column(DateTime, default=datetime.utcnow)


# ── Tablo oluşturma ──

def init_db():
    """Veritabanı tablolarını oluşturur."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Yeni bir DB oturumu döndürür."""
    return SessionLocal()


def get_engine():
    """SQLAlchemy engine nesnesini döndürür."""
    return engine


# Uygulama başlangıcında tabloları oluştur
init_db()
