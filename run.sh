#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
#  run.sh  –  QR Kod Okuyucu Başlatıcı
#  Kullanım:
#    chmod +x run.sh
#    ./run.sh web       → Flask web sunucusu (tarayıcı + mobil)
#    ./run.sh desktop   → Masaüstü OpenCV penceresi
# ─────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# macOS'ta zbar paylaşımlı kütüphanesi için yol
if command -v brew &>/dev/null; then
  ZBAR_LIB="$(brew --prefix zbar 2>/dev/null)/lib"
  export DYLD_LIBRARY_PATH="${ZBAR_LIB}:${DYLD_LIBRARY_PATH:-}"
fi

# Sanal ortam varsa etkinleştir
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

MODE="${1:-web}"

case "$MODE" in
  web)
    echo "🔒  HTTPS Web sunucusu başlatılıyor → https://localhost:5050"
    echo "    Aynı ağdaki telefon için: https://$(ipconfig getifaddr en0 2>/dev/null || hostname):5050"
    echo "    ⚠️  Tarayıcıda 'Güvenli değil' uyarısı çıkarsa → 'Gelişmiş > Devam et' seç"
    echo "    Durdurmak için Ctrl+C"
    python3 app.py
    ;;
  desktop)
    echo "🖥️   Masaüstü modu başlatılıyor…"
    python3 desktop.py "${@:2}"
    ;;
  *)
    echo "Kullanım: ./run.sh [web|desktop]"
    exit 1
    ;;
esac
