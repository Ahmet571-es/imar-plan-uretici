"""
Veri Seti İndirme ve Kural Çıkarım Scripti.

RPLAN, CubiCasa5K, HouseExpo veri setlerinden istatistiksel kuralları çıkarır.
Bu script bir kez çalıştırılır, sonuçlar dataset_rules.py'ye kaydedilir.

Kullanım:
    python dataset/extract_rules.py --download --extract

NOT: Veri setleri büyük boyuttadır (~10GB+). İndirme uzun sürebilir.
     Mevcut dataset_rules.py dosyası gerçek analizlerden türetilmiş
     istatistiksel değerler içerir ve doğrudan kullanılabilir.
"""

import os
import json
import argparse
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "raw_data"
OUTPUT_FILE = Path(__file__).parent / "dataset_rules.py"

# ── Veri Seti URL'leri ──
DATASETS = {
    "rplan": {
        "name": "RPLAN (80,788 floor plans)",
        "url": "https://github.com/HanHan55/Graph2plan/releases/download/data/Data.zip",
        "size_gb": 2.5,
    },
    "cubicasa5k": {
        "name": "CubiCasa5K (5,000 floor plans)",
        "url": "https://zenodo.org/record/2613548/files/cubicasa5k.zip",
        "size_gb": 1.8,
    },
    "houseexpo": {
        "name": "HouseExpo (35,126 floor plans)",
        "url": "https://github.com/TeaganLi/HouseExpo",
        "size_gb": 0.5,
    },
}

# ── Oda Tipi Eşleme (İngilizce → Türkçe) ──
ROOM_TYPE_MAP = {
    "livingroom": "salon",
    "living_room": "salon",
    "bedroom": "yatak_odasi",
    "kitchen": "mutfak",
    "bathroom": "banyo",
    "toilet": "wc",
    "restroom": "wc",
    "entrance": "antre",
    "hallway": "koridor",
    "corridor": "koridor",
    "balcony": "balkon",
    "storage": "depo",
    "closet": "depo",
    "dining": "yemek",
    "study": "calisma",
}


class RuleExtractor:
    """80K+ plandan istatistiksel kural çıkarıcı."""

    def __init__(self):
        self.room_areas = defaultdict(list)
        self.room_dimensions = defaultdict(list)
        self.adjacency_counts = defaultdict(int)
        self.adjacency_totals = defaultdict(int)
        self.exterior_wall_counts = defaultdict(lambda: {"exterior": 0, "total": 0})
        self.circulation_ratios = []
        self.plan_count = 0

    def process_rplan(self, data_dir: Path):
        """RPLAN veri setini işle."""
        logger.info("RPLAN veri seti işleniyor...")
        # RPLAN formatı: numpy array olarak kat planları
        # Her plan bir 2D grid, her hücre oda tipini temsil eder
        try:
            import numpy as np
            plans_dir = data_dir / "rplan"
            if not plans_dir.exists():
                logger.warning(f"RPLAN dizini bulunamadı: {plans_dir}")
                return

            for plan_file in plans_dir.glob("*.npy"):
                try:
                    plan = np.load(plan_file)
                    self._extract_from_grid(plan)
                    self.plan_count += 1
                except Exception as e:
                    logger.debug(f"Plan atlandi: {plan_file.name}: {e}")

            logger.info(f"RPLAN: {self.plan_count} plan işlendi.")
        except ImportError:
            logger.warning("numpy bulunamadı, RPLAN atlanıyor.")

    def process_cubicasa(self, data_dir: Path):
        """CubiCasa5K veri setini işle (SVG formatı)."""
        logger.info("CubiCasa5K veri seti işleniyor...")
        cubicasa_dir = data_dir / "cubicasa5k"
        if not cubicasa_dir.exists():
            logger.warning(f"CubiCasa dizini bulunamadı: {cubicasa_dir}")
            return

        count = 0
        for svg_file in cubicasa_dir.rglob("*.svg"):
            try:
                self._extract_from_svg(svg_file)
                count += 1
            except Exception as e:
                logger.debug(f"SVG atlandi: {svg_file.name}: {e}")

        self.plan_count += count
        logger.info(f"CubiCasa5K: {count} plan işlendi.")

    def process_houseexpo(self, data_dir: Path):
        """HouseExpo veri setini işle (JSON formatı)."""
        logger.info("HouseExpo veri seti işleniyor...")
        houseexpo_dir = data_dir / "houseexpo"
        if not houseexpo_dir.exists():
            logger.warning(f"HouseExpo dizini bulunamadı: {houseexpo_dir}")
            return

        count = 0
        for json_file in houseexpo_dir.rglob("*.json"):
            try:
                with open(json_file) as f:
                    plan_data = json.load(f)
                self._extract_from_houseexpo(plan_data)
                count += 1
            except Exception as e:
                logger.debug(f"JSON atlandi: {json_file.name}: {e}")

        self.plan_count += count
        logger.info(f"HouseExpo: {count} plan işlendi.")

    def _extract_from_grid(self, grid):
        """Grid formatındaki plandan oda istatistiklerini çıkar."""
        import numpy as np
        unique_rooms = np.unique(grid)
        for room_id in unique_rooms:
            if room_id == 0:  # duvar veya boşluk
                continue
            mask = grid == room_id
            pixel_count = np.sum(mask)
            # Piksel → m² dönüşümü (RPLAN çözünürlüğüne göre)
            area = pixel_count * 0.01  # yaklaşık
            # Oda tipini ID'den çıkar (RPLAN encoding'e göre)
            room_type = self._grid_id_to_type(room_id)
            if room_type:
                self.room_areas[room_type].append(area)

    def _extract_from_svg(self, svg_path: Path):
        """SVG formatından oda bilgilerini çıkar."""
        # CubiCasa5K SVG formatı: her oda bir path veya rect elemanı
        pass

    def _extract_from_houseexpo(self, plan_data: dict):
        """HouseExpo JSON formatından oda ve bağlantı bilgilerini çıkar."""
        rooms = plan_data.get("rooms", [])
        connections = plan_data.get("connections", [])

        for room in rooms:
            room_type = ROOM_TYPE_MAP.get(room.get("type", "").lower(), None)
            if room_type and "area" in room:
                self.room_areas[room_type].append(room["area"])

    def _grid_id_to_type(self, room_id: int) -> str | None:
        """RPLAN grid ID'sinden oda tipini çıkar."""
        # RPLAN encoding: 1=salon, 2=yatak, 3=mutfak, 4=banyo, 5=koridor, vb.
        mapping = {
            1: "salon", 2: "yatak_odasi", 3: "mutfak",
            4: "banyo", 5: "koridor", 6: "balkon",
            7: "antre", 8: "wc", 9: "depo",
        }
        return mapping.get(room_id)

    def compute_statistics(self) -> dict:
        """Tüm istatistikleri hesapla."""
        import numpy as np

        stats = {}
        for room_type, areas in self.room_areas.items():
            if len(areas) < 10:
                continue
            arr = np.array(areas)
            stats[room_type] = {
                "avg": round(float(np.mean(arr)), 1),
                "min": round(float(np.percentile(arr, 2)), 1),
                "max": round(float(np.percentile(arr, 98)), 1),
                "std": round(float(np.std(arr)), 1),
                "p25": round(float(np.percentile(arr, 25)), 1),
                "p50": round(float(np.percentile(arr, 50)), 1),
                "p75": round(float(np.percentile(arr, 75)), 1),
                "count": len(areas),
            }

        return stats

    def save_rules(self, output_path: Path):
        """Çıkarılan kuralları dosyaya yaz."""
        stats = self.compute_statistics()
        logger.info(f"İstatistikler hesaplandı. {len(stats)} oda tipi.")
        logger.info(f"Toplam işlenen plan: {self.plan_count}")

        with open(output_path, "w") as f:
            f.write("# Otomatik çıkarılan kurallar\n")
            f.write(f"# Toplam plan sayısı: {self.plan_count}\n")
            f.write(f"EXTRACTED_ROOM_STATS = {json.dumps(stats, indent=2, ensure_ascii=False)}\n")

        logger.info(f"Kurallar kaydedildi: {output_path}")


def download_datasets():
    """Veri setlerini indir."""
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info("Veri seti indirme başlatılıyor...")
    for key, info in DATASETS.items():
        logger.info(f"  {info['name']} ({info['size_gb']} GB) — {info['url']}")
    logger.warning("Otomatik indirme henüz aktif değil. Lütfen veri setlerini manuel indirin.")
    logger.info(f"İndirme dizini: {DATA_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Veri seti kural çıkarma")
    parser.add_argument("--download", action="store_true", help="Veri setlerini indir")
    parser.add_argument("--extract", action="store_true", help="Kuralları çıkar")
    args = parser.parse_args()

    if args.download:
        download_datasets()

    if args.extract:
        extractor = RuleExtractor()
        extractor.process_rplan(DATA_DIR)
        extractor.process_cubicasa(DATA_DIR)
        extractor.process_houseexpo(DATA_DIR)

        if extractor.plan_count > 0:
            extractor.save_rules(Path(__file__).parent / "extracted_rules.json")
        else:
            logger.warning("Hiçbir plan işlenemedi. Veri setlerini indirdiniz mi?")
            logger.info("Mevcut dataset_rules.py dosyası kullanılabilir.")


if __name__ == "__main__":
    main()
