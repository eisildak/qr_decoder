"""
qr_detector.py  –  QR Kod Tespit Motoru
========================================
OpenCV + pyzbar kullanarak tek bir görüntüde birden fazla
QR / barkod nesnesini tespit eder ve çözümler.
Web API ve masaüstü kamera modu her ikisi için de kullanılır.
"""

import cv2
import numpy as np
from pyzbar import pyzbar
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


@dataclass
class QRResult:
    """Tek bir QR kodunun çözümleme sonucunu tutar."""
    data: str
    qr_type: str          # QRCODE, CODE128, EAN13, vb.
    polygon: List[Tuple[int, int]]
    rect: Tuple[int, int, int, int]   # x, y, w, h
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __eq__(self, other):
        return isinstance(other, QRResult) and self.data == other.data

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "type": self.qr_type,
            "timestamp": self.timestamp,
        }


class QRDetector:
    """
    OpenCV kamera + pyzbar ile gerçek zamanlı çoklu QR kod dedektörü.

    Kullanım:
        detector = QRDetector(camera_index=0)
        for frame, results in detector.stream():
            for r in results:
                print(r.data)
        detector.release()
    """

    def __init__(self, camera_index: int = 0, scale: float = 1.0):
        self.camera_index = camera_index
        self.scale = scale          # Performans için frame küçültme oranı
        self._cap = None

    # ------------------------------------------------------------------
    # Kamera yönetimi
    # ------------------------------------------------------------------

    def open(self) -> bool:
        """Kamerayı açar; başarıysa True döner."""
        self._cap = cv2.VideoCapture(self.camera_index)
        return self._cap.isOpened()

    def release(self):
        if self._cap and self._cap.isOpened():
            self._cap.release()

    # ------------------------------------------------------------------
    # Çekirdek algılama
    # ------------------------------------------------------------------

    @staticmethod
    def detect_image(frame: np.ndarray, scale: float = 1.0) -> "List[QRResult]":
        """
        Statik metod: herhangi bir numpy frame üzerinde çalışır.
        Flask API ve masaüstü modu her ikisi de bu metodu kullanır.
        Birden fazla QR kod varsa hepsini döner.
        """
        if scale != 1.0:
            small = cv2.resize(frame, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_AREA)
        else:
            small = frame

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        decoded_objects = pyzbar.decode(gray)
        results: List[QRResult] = []
        inv = 1.0 / scale

        for obj in decoded_objects:
            try:
                data = obj.data.decode("utf-8", errors="replace").strip()
            except Exception:
                data = str(obj.data)

            polygon = [(int(p.x * inv), int(p.y * inv)) for p in obj.polygon]
            r = obj.rect
            rect_scaled = (int(r.left * inv), int(r.top * inv),
                           int(r.width * inv), int(r.height * inv))
            results.append(QRResult(data=data, qr_type=obj.type,
                                    polygon=polygon, rect=rect_scaled))
        return results

    def detect(self, frame: np.ndarray) -> "List[QRResult]":
        """Instance metodu: self.scale ile detect_image'i çağırır."""
        return QRDetector.detect_image(frame, self.scale)

    # ------------------------------------------------------------------
    # Görsel çizim
    # ------------------------------------------------------------------

    @staticmethod
    def draw(frame: np.ndarray, results: List[QRResult]) -> np.ndarray:
        """Tespit edilen QR kodların sınırlarını ve içeriğini frame üzerine çizer."""
        for r in results:
            pts = np.array(r.polygon, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

            x, y, w, h = r.rect
            label = f"[{r.qr_type}] {r.data[:60]}{'...' if len(r.data) > 60 else ''}"

            # Arka plan kutusu (okunabilirlik için)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame, (x, y - th - 8), (x + tw + 4, y), (0, 0, 0), -1)
            cv2.putText(
                frame, label,
                (x + 2, y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 0), 1, cv2.LINE_AA,
            )

        return frame

    # ------------------------------------------------------------------
    # Generator: sürekli kamera akışı
    # ------------------------------------------------------------------

    def stream(self):
        """
        Kamera açıkken her frame için (frame, results) üretir.
        Kamera kapalıysa StopIteration fırlatır.
        """
        if not self.open():
            raise RuntimeError(f"Kamera açılamadı (index={self.camera_index})")

        try:
            while True:
                ok, frame = self._cap.read()
                if not ok:
                    break
                results = self.detect(frame)
                annotated = self.draw(frame.copy(), results)
                yield annotated, results
        finally:
            self.release()
