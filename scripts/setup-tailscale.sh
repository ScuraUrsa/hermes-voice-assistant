#!/usr/bin/env bash
# =============================================================================
# setup-tailscale.sh — Automatyczny setup Tailscale na VM (Ubuntu/Debian)
# =============================================================================
# Ten skrypt:
#   1. Instaluje Tailscale (oficjalny skrypt instalacyjny)
#   2. Uruchamia usługę tailscaled
#   3. Uwierzytelnia urządzenie (wymaga interaktywnego logowania)
#   4. Wyświetla adres IP w sieci Tailscale
#   5. Konfiguruje firewall (UFW) jeśli potrzebne
#
# Użycie:
#   chmod +x setup-tailscale.sh
#   sudo ./setup-tailscale.sh
#
# Wymagania:
#   - Ubuntu 22.04+ / Debian 12+
#   - curl
#   - sudo / root
# =============================================================================

set -euo pipefail

# --- Kolory dla outputu ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# --- Sprawdzenie uprawnień ---
if [[ $EUID -ne 0 ]]; then
    err "Ten skrypt wymaga uprawnień roota. Użyj: sudo ./setup-tailscale.sh"
    exit 1
fi

# --- Wstępne sprawdzenia ---
info "Sprawdzanie wymagań..."

if ! command -v curl &>/dev/null; then
    warn "curl nie jest zainstalowany. Instaluję..."
    apt-get update && apt-get install -y curl
fi

if ! command -v systemctl &>/dev/null; then
    err "systemctl nie jest dostępny. Ten skrypt wymaga systemd."
    exit 1
fi

ok "Wymagania spełnione."

# --- Krok 1: Instalacja Tailscale ---
info "Instalacja Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
ok "Tailscale zainstalowany."

# --- Krok 2: Włączenie i uruchomienie usługi ---
info "Uruchamianie usługi tailscaled..."
systemctl enable tailscaled
systemctl start tailscaled

# Czekamy aż usługa wystartuje
sleep 2

if systemctl is-active --quiet tailscaled; then
    ok "Usługa tailscaled działa."
else
    err "Usługa tailscaled nie uruchomiła się. Sprawdź: journalctl -u tailscaled -n 20"
    exit 1
fi

# --- Krok 3: Uwierzytelnianie ---
info "Uruchamianie uwierzytelniania..."
info "Otwórz link poniżej w przeglądarce i zaloguj się swoim kontem."
info "Po zalogowaniu wróć do terminala."
echo ""
tailscale up

# Sprawdzenie czy uwierzytelnienie się powiodło
sleep 3

TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || true)

if [[ -n "$TAILSCALE_IP" ]]; then
    ok "Uwierzytelnienie udane!"
else
    err "Nie udało się uzyskać adresu IP Tailscale."
    err "Sprawdź: tailscale status"
    exit 1
fi

# --- Krok 4: Status i informacje ---
echo ""
info "=== Status Tailscale ==="
tailscale status

echo ""
info "=== Adres IP w sieci Tailscale ==="
echo "  IPv4: $TAILSCALE_IP"

# Pobierz nazwę hosta w MagicDNS jeśli dostępna
TAILSCALE_HOSTNAME=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.get('Self',{}).get('DNSName','brak').rstrip('.')))" 2>/dev/null || echo "brak")
if [[ "$TAILSCALE_HOSTNAME" != "brak" ]]; then
    echo "  DNS:  $TAILSCALE_HOSTNAME"
fi

# --- Krok 5: Konfiguracja firewalla (UFW) ---
if command -v ufw &>/dev/null && ufw status | grep -q "active"; then
    info "UFW jest aktywny. Sprawdzam reguły..."

    # Tailscale używa portu UDP 41641 (ale outbound, więc UFW domyślnie pozwala)
    if ! ufw status | grep -q "41641/udp"; then
        info "Dodawanie reguły dla Tailscale (UDP 41641)..."
        ufw allow 41641/udp comment 'Tailscale'
    fi

    # Upewnij się że Open WebUI i HA są dostępne tylko przez Tailscale
    # (to jest przykładowe — dostosuj do swoich potrzeb)
    warn "Upewnij się, że usługi (Open WebUI, Home Assistant) nasłuchują na tailscale0"
    warn "lub są zabezpieczone regułami UFW. Przykład:"
    echo "    ufw allow in on tailscale0 to any port 3000 proto tcp comment 'Open WebUI'"
    echo "    ufw allow in on tailscale0 to any port 8123 proto tcp comment 'Home Assistant'"

    ok "Firewall sprawdzony."
fi

# --- Podsumowanie ---
echo ""
echo "========================================="
echo -e "${GREEN}  ✅ Tailscale skonfigurowany!${NC}"
echo "========================================="
echo ""
echo "  Adres VM w sieci Tailscale:  ${TAILSCALE_IP}"
echo ""
echo "  Co dalej:"
echo "    1. Zainstaluj Tailscale na telefonie (Google Play)"
echo "    2. Zaloguj się tym samym kontem"
echo "    3. Otwórz http://${TAILSCALE_IP}:3000 (Open WebUI)"
echo "    4. Otwórz http://${TAILSCALE_IP}:8123 (Home Assistant)"
echo ""
echo "  Aby sprawdzić połączenie:"
echo "    tailscale status"
echo "    tailscale ping <adres-telefonu>"
echo ""