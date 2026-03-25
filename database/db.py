"""
Database Bağlantı Yönetimi — Supabase PostgreSQL + SQLite Fallback.

Supabase bağlantısı varsa PostgreSQL kullanılır (kalıcı, Cloud uyumlu).
Yoksa SQLite fallback (/tmp, ephemeral) devreye girer.

Supabase bağlantısı için:
  - Streamlit Cloud: Settings > Secrets > SUPABASE_DB_URL
  - Lokal: .streamlit/secrets.toml veya SUPABASE_DB_URL env var

  Format: postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
"""

import os
import logging
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Boolean, Text, event,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator, TEXT
import json

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# JSON uyumlu tip — PostgreSQL ve SQLite'da çalışır
# ═══════════════════════════════════════════════════════════════

class JSONEncodedDict(TypeDecorator):
    """JSON verisini TEXT olarak saklar — her DB'de çalışır."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return "{}"

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}


# ═══════════════════════════════════════════════════════════════
# Bağlantı URL'si — Supabase > Env > SQLite sırasıyla
# ═══════════════════════════════════════════════════════════════

def _resolve_database_url() -> tuple[str, str]:
    """Veritabanı URL'sini belirler.

    Returns:
        (database_url, backend_type)  — backend_type: "postgresql" | "sqlite"
    """
    # 1. Streamlit secrets
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_DB_URL", "")
        if url and url.startswith("postgresql"):
            logger.info("Supabase PostgreSQL baglantisi (st.secrets)")
            return url, "postgresql"
    except Exception:
        pass

    # 2. Environment variable
    url = os.environ.get("SUPABASE_DB_URL", "")
    if url and url.startswith("postgresql"):
        logger.info("Supabase PostgreSQL baglantisi (env)")
        return url, "postgresql"

    # 3. Genel DATABASE_URL env
    url = os.environ.get("DATABASE_URL", "")
    if url and ("postgresql" in url or "postgres" in url):
        # Heroku/Railway tarzı postgres:// → postgresql:// düzeltmesi
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        logger.info("PostgreSQL baglantisi (DATABASE_URL)")
        return url, "postgresql"

    # 4. SQLite fallback
    import platform
    _is_cloud = platform.processor() == "" or os.environ.get("STREAMLIT_SHARING_MODE")

    if _is_cloud or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK):
        db_dir = "/tmp/imar_plan_db"
    else:
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")

    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "imar_plan.db")
    logger.info(f"SQLite fallback: {db_path}")
    return f"sqlite:///{db_path}", "sqlite"


DATABASE_URL, DB_BACKEND = _resolve_database_url()


# ═══════════════════════════════════════════════════════════════
# SQLAlchemy Engine
# ═══════════════════════════════════════════════════════════════

def _create_engine():
    """Backend'e uygun engine oluşturur."""
    if DB_BACKEND == "postgresql":
        return create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            connect_args={"connect_timeout": 10},
        )
    else:
        eng = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "timeout": 15},
        )

        @event.listens_for(eng, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

        return eng


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ═══════════════════════════════════════════════════════════════
# ORM Modelleri
# ═══════════════════════════════════════════════════════════════

class Musteri(Base):
    """CRM müşteri kaydı."""
    __tablename__ = "musteriler"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_soyad = Column(String(200), nullable=False)
    telefon = Column(String(20), default="")
    email = Column(String(100), default="")
    musteri_tipi = Column(String(30), default="Bireysel")
    durum = Column(String(30), default="Aday")
    notlar = Column(Text, default="")
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    durum = Column(String(50), default="Fizibilite")
    butce = Column(Float, default=0.0)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notlar = Column(Text, default="")
    veri_json = Column(JSONEncodedDict, default=dict)


class FiyatVerisi(Base):
    """İlçe bazlı fiyat verisi."""
    __tablename__ = "fiyat_verileri"

    id = Column(Integer, primary_key=True, autoincrement=True)
    il = Column(String(50))
    ilce = Column(String(50))
    daire_tipi = Column(String(10))
    m2_fiyat = Column(Float)
    kaynak = Column(String(50))
    tarih = Column(DateTime, default=datetime.utcnow)


class ImarCache(Base):
    """İmar bilgisi cache."""
    __tablename__ = "imar_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    il = Column(String(50))
    ilce = Column(String(50))
    ada = Column(String(20))
    parsel_no = Column(String(20))
    imar_verisi = Column(JSONEncodedDict, default=dict)
    son_sorgu = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# DB İşlemleri
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Veritabanı tablolarını oluşturur (yoksa)."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Tablolar olusturuldu ({DB_BACKEND})")
    except Exception as e:
        logger.error(f"Tablo olusturma hatasi: {e}")


def get_session():
    """Yeni bir DB oturumu döndürür."""
    return SessionLocal()


def get_engine():
    """Engine nesnesini döndürür."""
    return engine


def get_backend_info() -> dict:
    """Aktif veritabanı bilgilerini döndürür."""
    return {
        "backend": DB_BACKEND,
        "kalici": DB_BACKEND == "postgresql",
        "url_masked": DATABASE_URL[:30] + "..." if len(DATABASE_URL) > 30 else DATABASE_URL,
    }


# ═══════════════════════════════════════════════════════════════
# CRM CRUD İşlemleri
# ═══════════════════════════════════════════════════════════════

def musteri_ekle(ad_soyad: str, telefon: str = "", email: str = "",
                 musteri_tipi: str = "Bireysel", durum: str = "Aday",
                 notlar: str = "") -> int | None:
    """Yeni müşteri ekler, id döndürür."""
    try:
        session = get_session()
        m = Musteri(
            ad_soyad=ad_soyad, telefon=telefon, email=email,
            musteri_tipi=musteri_tipi, durum=durum, notlar=notlar,
        )
        session.add(m)
        session.commit()
        mid = m.id
        session.close()
        return mid
    except Exception as e:
        logger.error(f"Musteri ekleme hatasi: {e}")
        return None


def musteri_listele() -> list[dict]:
    """Tüm müşterileri listeler."""
    try:
        session = get_session()
        rows = session.query(Musteri).order_by(Musteri.olusturma_tarihi.desc()).all()
        result = []
        for r in rows:
            result.append({
                "id": r.id, "ad": r.ad_soyad, "tel": r.telefon,
                "email": r.email, "tip": r.musteri_tipi,
                "durum": r.durum, "not": r.notlar,
                "tarih": r.olusturma_tarihi.strftime("%d.%m.%Y") if r.olusturma_tarihi else "",
            })
        session.close()
        return result
    except Exception as e:
        logger.error(f"Musteri listeleme hatasi: {e}")
        return []


def musteri_durum_guncelle(musteri_id: int, yeni_durum: str) -> bool:
    """Müşteri durumunu günceller."""
    try:
        session = get_session()
        m = session.query(Musteri).filter_by(id=musteri_id).first()
        if m:
            m.durum = yeni_durum
            m.guncelleme_tarihi = datetime.utcnow()
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception as e:
        logger.error(f"Durum guncelleme hatasi: {e}")
        return False


def musteri_sil(musteri_id: int) -> bool:
    """Müşteriyi siler."""
    try:
        session = get_session()
        m = session.query(Musteri).filter_by(id=musteri_id).first()
        if m:
            session.delete(m)
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception as e:
        logger.error(f"Musteri silme hatasi: {e}")
        return False


def proje_ekle(proje_adi: str, il: str = "", durum: str = "Fizibilite",
               butce: float = 0.0) -> int | None:
    """Yeni proje ekler, id döndürür."""
    try:
        session = get_session()
        p = Proje(proje_adi=proje_adi, il=il, durum=durum, butce=butce)
        session.add(p)
        session.commit()
        pid = p.id
        session.close()
        return pid
    except Exception as e:
        logger.error(f"Proje ekleme hatasi: {e}")
        return None


def proje_listele() -> list[dict]:
    """Tüm projeleri listeler."""
    try:
        session = get_session()
        rows = session.query(Proje).order_by(Proje.olusturma_tarihi.desc()).all()
        result = []
        for r in rows:
            result.append({
                "id": r.id, "ad": r.proje_adi, "il": r.il,
                "durum": r.durum, "butce": r.butce,
                "tarih": r.olusturma_tarihi.strftime("%d.%m.%Y") if r.olusturma_tarihi else "",
            })
        session.close()
        return result
    except Exception as e:
        logger.error(f"Proje listeleme hatasi: {e}")
        return []


# Uygulama başlangıcında tabloları oluştur
init_db()
