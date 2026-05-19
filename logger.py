"""
logger.py  –  QR Kod Kayıt Modülü
===================================
Okunan QR kodlarını CSV ve TXT dosyalarına kaydeder.
Oturum boyunca aynı veriyi tekrar kaydetmez (duplicate filtreleme).
"""

import csv
import os
from datetime import datetime
from threading import Lock
from typing import List, Optional

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class QRLogger:
    """
    Thread-safe QR kod kaydedicisi.

    Dosyalar:
        logs/qr_log_YYYYMMDD.csv   → yapısal CSV kaydı
        logs/qr_log_YYYYMMDD.txt   → okunabilir metin kaydı

    Aynı (data, type) çifti oturum boyunca bir kez kaydedilir.
    """

    CSV_HEADER = ["timestamp", "type", "data", "session_id"]

    def __init__(self, session_id: Optional[str] = None):
        os.makedirs(LOG_DIR, exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.session_id = session_id or datetime.now().strftime("%H%M%S")
        self.csv_path = os.path.join(LOG_DIR, f"qr_log_{today}.csv")
        self.txt_path = os.path.join(LOG_DIR, f"qr_log_{today}.txt")
        self._seen: set = set()
        self._lock = Lock()
        self._ensure_csv_header()

    # ------------------------------------------------------------------ #

    def _ensure_csv_header(self):
        """CSV dosyası yoksa başlık satırını yazar."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.CSV_HEADER).writeheader()

    # ------------------------------------------------------------------ #

    def log(self, results) -> list:
        """
        Yeni (daha önce görülmemiş) sonuçları kaydeder.
        Kaydedilen sonuçların listesini döner.
        """
        new_results = []
        with self._lock:
            for r in results:
                key = (r.data, r.qr_type)
                if key in self._seen:
                    continue
                self._seen.add(key)
                new_results.append(r)
                self._write_csv(r)
                self._write_txt(r)
        return new_results

    def _write_csv(self, r):
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writerow({
                "timestamp": r.timestamp,
                "type": r.qr_type,
                "data": r.data,
                "session_id": self.session_id,
            })

    def _write_txt(self, r):
        with open(self.txt_path, "a", encoding="utf-8") as f:
            f.write(f"[{r.timestamp}] [{r.qr_type}] {r.data}\n")

    # ------------------------------------------------------------------ #

    def all_saved(self) -> List[dict]:
        """Bu oturumda kaydedilen tüm sonuçları döner."""
        rows = []
        if not os.path.exists(self.csv_path):
            return rows
        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("session_id") == self.session_id:
                    rows.append(row)
        return rows

    @property
    def total_saved(self) -> int:
        return len(self._seen)
