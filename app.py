"""
app.py  –  Flask Web Sunucusu
==============================
Web ve mobil tarayıcılardan QR kod okuma için REST API + HTML arayüzü.

Endpoint'ler:
  GET  /                  → Arayüz (index.html)
  POST /api/decode        → Base64 görüntü alır, QR sonuçlarını JSON döner
  GET  /api/history       → Bu oturumda kaydedilen tüm QR kodları
  GET  /api/export/csv    → CSV dosyasını indir
  GET  /api/export/txt    → TXT dosyasını indir
"""

import base64
import io
import os
import sys

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_file

# Modülleri aynı klasörden içe aktar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import LOG_DIR, QRLogger
from qr_detector import QRDetector

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# Oturum genelinde tek bir logger örneği
_logger = QRLogger()


# ------------------------------------------------------------------ #
#  Yardımcı                                                            #
# ------------------------------------------------------------------ #

def _decode_b64_image(b64_string: str) -> np.ndarray:
    """Base64 veri URI ya da ham base64 stringini OpenCV frame'e çevirir."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Görüntü çözümlenemedi.")
    return frame


# ------------------------------------------------------------------ #
#  Route'lar                                                           #
# ------------------------------------------------------------------ #

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/decode", methods=["POST"])
def decode():
    """
    Body (JSON): { "image": "<base64 data URI>" }
    Response:    { "results": [ { "data":..., "type":..., "timestamp":... } ] }
    """
    payload = request.get_json(silent=True)
    if not payload or "image" not in payload:
        return jsonify({"error": "Eksik 'image' alanı"}), 400

    try:
        frame = _decode_b64_image(payload["image"])
    except Exception as e:
        return jsonify({"error": str(e)}), 422

    results = QRDetector.detect_image(frame)
    _logger.log(results)

    return jsonify({
        "results": [r.to_dict() for r in results],
        "count": len(results),
        "total_saved": _logger.total_saved,
    })


@app.route("/api/history")
def history():
    """Bu oturumda kaydedilen tüm QR kodları."""
    return jsonify({
        "history": _logger.all_saved(),
        "total": _logger.total_saved,
    })


@app.route("/api/export/csv")
def export_csv():
    """Günlük CSV dosyasını indir."""
    path = _logger.csv_path
    if not os.path.exists(path):
        return jsonify({"error": "Henüz kayıt yok"}), 404
    return send_file(path, as_attachment=True,
                     download_name="qr_kodlar.csv", mimetype="text/csv")


@app.route("/api/export/txt")
def export_txt():
    """Günlük TXT dosyasını indir."""
    path = _logger.txt_path
    if not os.path.exists(path):
        return jsonify({"error": "Henüz kayıt yok"}), 404
    return send_file(path, as_attachment=True,
                     download_name="qr_kodlar.txt", mimetype="text/plain")


# ------------------------------------------------------------------ #
#  Başlangıç                                                           #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    # Mobil tarayıcılar getUserMedia için HTTPS zorunlu kılar.
    # 'adhoc' → pyopenssl ile geçici self-signed sertifika üretir.
    app.run(host="0.0.0.0", port=5050, debug=True, ssl_context="adhoc")
