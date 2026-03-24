"""
Güvenli Import Yardımcısı — Opsiyonel kütüphaneleri lazy yükler,
yoksa fallback veya uyarı döndürür.
"""

import logging

logger = logging.getLogger(__name__)

_import_cache = {}


def safe_import(module_name: str, package_name: str = None):
    """Modülü güvenli import eder, yoksa None döndürür.

    Args:
        module_name: Import edilecek modül (ör: "folium").
        package_name: pip paket adı (ör: "folium"). Hata mesajında kullanılır.

    Returns:
        Modül veya None.
    """
    if module_name in _import_cache:
        return _import_cache[module_name]

    try:
        import importlib
        mod = importlib.import_module(module_name)
        _import_cache[module_name] = mod
        return mod
    except ImportError:
        pkg = package_name or module_name
        logger.info(f"'{module_name}' bulunamadı. Kurulum: pip install {pkg}")
        _import_cache[module_name] = None
        return None


def is_available(module_name: str) -> bool:
    """Modülün kurulu olup olmadığını kontrol eder."""
    mod = safe_import(module_name)
    return mod is not None


def require_or_warn(module_name: str, feature_name: str = "") -> bool:
    """Modül yoksa Streamlit uyarısı gösterir.

    Returns:
        True = modül mevcut, False = eksik.
    """
    if is_available(module_name):
        return True

    import streamlit as st
    feature = feature_name or module_name
    st.warning(f"⚠️ **{feature}** için `{module_name}` kütüphanesi gerekli. "
               f"Kurulum: `pip install {module_name}`")
    return False
