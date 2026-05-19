"""
desktop.py  –  Masaüstü / Terminal Modu
=========================================
Web sunucusu olmadan doğrudan OpenCV penceresiyle kamerayı açar.
Birden fazla QR kod tespit edilince hepsini ekrana yazar ve kaydeder.

Kullanım:
    python desktop.py              # varsayılan kamera (index 0)
    python desktop.py --camera 1   # harici kamera
    python desktop.py --scale 0.5  # düşük güçlü cihaz için küçük frame
"""

import argparse
import sys
import os

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qr_detector import QRDetector
from logger import QRLogger


def main():
    parser = argparse.ArgumentParser(description="QR Kod Okuyucu – Masaüstü Modu")
    parser.add_argument("--camera", type=int, default=0, help="Kamera indeksi")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="Frame ölçeği (örn. 0.5 = yarı boyut)")
    args = parser.parse_args()

    detector = QRDetector(camera_index=args.camera, scale=args.scale)
    logger = QRLogger()

    print("=" * 55)
    print("  QR Kod Okuyucu – Masaüstü Modu")
    print("  Çıkmak için 'q' tuşuna basın veya Ctrl+C")
    print("=" * 55)

    try:
        for annotated_frame, results in detector.stream():
            # Yeni QR kodları kaydet ve terminale yaz
            new = logger.log(results)
            for r in new:
                print(f"  ✔ [{r.qr_type}] {r.data}")

            # Durum bilgisini frame üzerine ekle
            info = f"Okunan: {logger.total_saved}  |  Ekranda: {len(results)}"
            cv2.putText(annotated_frame, info, (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)

            cv2.imshow("QR Kod Okuyucu  (q = cikis)", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except RuntimeError as e:
        print(f"HATA: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        if logger.total_saved:
            print(f"\nToplam {logger.total_saved} QR kod kaydedildi.")
            print(f"  CSV : {logger.csv_path}")
            print(f"  TXT : {logger.txt_path}")
        else:
            print("\nHiçbir QR kod okunmadı.")


if __name__ == "__main__":
    main()
