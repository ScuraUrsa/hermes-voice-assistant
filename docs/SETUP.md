# Instrukcja Konfiguracji — Hermes Voice Assistant

> Kompletny przewodnik krok po kroku od zera do w pełni działającego asystenta głosowego.

---

## Zakładka 0 — Tailscale (Instalacja)

### Na VM (Ubuntu Server)

```bash
# 1. Zainstaluj Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Uruchom i uwierzytelnij
sudo tailscale up

# Otwórz link wyświetlony w terminalu, zaloguj się przez GitHub/Google/Microsoft
# Po zalogowaniu VM pojawi się w sieci Tailscale

# 3. Sprawdź status i adres IP
tailscale status
tailscale ip -4
# Przykładowy output: 100.x.x.x
```

### Na Android (telefon)

```bash
# 1. Zainstaluj Tailscale z Google Play Store
#    Szukaj: "Tailscale" (oficjalna aplikacja)

# 2. Otwórz aplikację, zaloguj się tym samym kontem co VM

# 3. Włącz VPN — telefon dostanie adres 100.x.x.y

# 4. (Opcjonalnie) Włącz "Use Tailscale DNS" w ustawieniach
#    dla MagicDNS (nazwy zamiast IP)
```

### Sprawdzenie połączenia

Na telefonie (lub z VM) sprawdź, czy urządzenia się widzą:

```bash
# Z VM: ping do telefonu
ping 100.x.x.y

# Z telefonu (przez termux lub aplikację): ping do VM
# W aplikacji Tailscale: zobacz listę urządzeń
```

---

## Krok 1 — Test połączenia Tailscale

Upewnij się, że urządzenia komunikują się przez Tailscale:

```bash
# 1. Sprawdź oba urządzenia są widoczne
tailscale status

# Output powinien pokazać:
# 100.x.x.x   nazwa-vm        username@   linux   -
# 100.x.x.y   nazwa-telefon    username@   android -

# 2. Test ping między urządzeniami
ping -c 4 100.x.x.y    # z VM ping do telefonu

# 3. Test HTTP (jeśli Open WebUI już działa)
curl -s http://100.x.x.x:3000 | head -5
```

> **UWAGA:** Jeśli ping nie działa, sprawdź:
> - Oba urządzenia są zalogowane do tego samego konta Tailscale
> - Tailscale VPN jest włączony na telefonie
> - Firewall na VM nie blokuje ruchu Tailscale (`ufw status`)

---

## Krok 2 — Konfiguracja Open WebUI Voice Mode

### 2.1 Uruchom Open WebUI (jeśli jeszcze nie działa)

```bash
# Docker (zalecane)
docker run -d \
  --name open-webui \
  -p 3000:3000 \
  -v open-webui-data:/app/backend/data \
  -e WEBUI_SECRET_KEY=tajny-klucz \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:main

# Lub przez docker-compose
```

### 2.2 Skonfiguruj STT (Whisper)

1. Otwórz Open WebUI: `http://100.x.x.x:3000`
2. Zaloguj się (pierwsze konto = admin)
3. Przejdź do: **Settings (koło zębate) → Audio → Speech-to-Text**
4. Wybierz dostawcę:
   - **Whisper (lokalny):** `whisper-large-v3` — działa od razu, bez klucza API
   - **OpenAI Whisper API:** wymaga klucza API OpenAI

5. **Ustawienia lokalnego Whisper:**
   - Model: `whisper-large-v3` (najlepsza jakość)
   - Language: `pl` (polski) — wymagane dla dokładności
   - Auto-detect silence: ✅ włączone

### 2.3 Skonfiguruj TTS (ElevenLabs lub lokalny)

#### Opcja A: ElevenLabs TTS (chmurowy, wysoka jakość)

1. Wejdź na: https://elevenlabs.io → zarejestruj się
2. Utwórz API Key w ustawieniach profilu
3. W Open WebUI: **Settings → Audio → Text-to-Speech**
4. Dostawca: **ElevenLabs**
5. Wklej klucz API
6. Wybierz głos:
   - `21m00Tcm4TlvDq8ikWAM` — Rachel (domyślny, angielski)
   - `pNInz6obpgDQGcFmaJgB` — Adam
   - Dla polskiego: przetestuj różne głosy lub dodaj custom voice
7. Model: `eleven_multilingual_v2` (obsługuje polski)
8. Stability: 0.5, Similarity: 0.75

#### Opcja B: Piper TTS (lokalny, przez Wyoming)

```bash
# Uruchom Wyoming Piper jako osobny kontener
docker run -d \
  --name wyoming-piper \
  -p 10200:10200 \
  --restart unless-stopped \
  ghcr.io/rhasspy/wyoming-piper:master \
  --voice pl_PL-darkvoice-medium
```

Następnie w Open WebUI wskaż URL: `http://localhost:10200`

### 2.4 Włącz Voice Mode

1. **Settings → Interface → Voice Mode**
2. Włącz: **Enable Voice Mode**
3. Ustaw:
   - Auto-send: ✅ (automatycznie wysyła po wykryciu ciszy)
   - Silence threshold: 500ms (lub dostosuj)
   - Push-to-talk: wyłączone (pełny voice mode)
4. **Zapisz zmiany**

---

## Krok 3 — Otwórz Open WebUI z telefonu przez Tailscale

1. **Na telefonie:** upewnij się, że Tailscale VPN jest włączony
2. **Otwórz przeglądarkę** → wpisz: `http://100.x.x.x:3000`
   - gdzie `100.x.x.x` to Tailscale IP Twojej VM
3. Zaloguj się tym samym kontem co na komputerze
4. Powinieneś zobaczyć interfejs Open WebUI

> **Dla lepszego UX na telefonie:**
> - Dodaj do ekranu głównego: Menu przeglądarki → "Dodaj do ekranu głównego"
> - Nazwa: "Hermes Assistant"
> - Działa jak aplikacja (fullscreen, bez paska adresu)

---

## Krok 4 — Test voice mode

### Test podstawowy (z komputera / laptopa)

1. W Open WebUI kliknij ikonę mikrofonu obok pola tekstowego
2. Powiedz: "Włącz światło w salonie"
3. Sprawdź:
   - Czy audio jest nagrywane (fala dźwięku na UI)
   - Czy transkrypcja pojawia się w polu tekstowym
   - Czy model odpowiada
   - Czy odpowiedź jest odtwarzana głosowo

### Test z telefonu (przez Tailscale)

1. Otwórz Open WebUI na telefonie (`http://100.x.x.x:3000`)
2. Kliknij ikonę mikrofonu
3. Powiedz komendę
4. Sprawdź czy:
   - Audio przesyła się przez Tailscale (szybkość <50ms latency)
   - Transkrypcja jest poprawna (Whisper rozumie polski)
   - TTS odtwarza się na telefonie

### Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---------|-------------|
| Mikrofon nie działa | Sprawdź uprawnienia w przeglądarce (🔒 → Mikrofon: Allow) |
| STT nie rozumie polskiego | Ustaw `Language: pl` w Whispers; użyj `whisper-large-v3` |
| TTS nie działa | Sprawdź czy klucz ElevenLabs jest poprawny; port Wyoming jest otwarty |
| Opóźnienie audio | Tailscale powinien dać <20ms; sprawdź `tailscale ping` latency |
| Voice mode nie startuje | Wyłącz adblocki; użyj Chrome/Edge na Androidzie |

---

## Krok 5 (Future) — Home Assistant + Wyoming

> Ten krok opisuje pełną integrację z Home Assistant — do zrealizowania po skonfigurowaniu voice mode.

### 5.1 Uruchom Home Assistant

```bash
# Docker
docker run -d \
  --name homeassistant \
  -p 8123:8123 \
  -v /path/to/homeassistant:/config \
  --restart unless-stopped \
  ghcr.io/home-assistant/home-assistant:stable
```

### 5.2 Skonfiguruj Wyoming STT/TTS

```bash
# Wyoming STT (Whisper)
docker run -d \
  --name wyoming-whisper \
  -p 10300:10300 \
  --restart unless-stopped \
  ghcr.io/rhasspy/wyoming-whisper:master \
  --model large-v3 \
  --language pl

# Wyoming TTS (Piper) — jeśli nie uruchomiony wcześniej
docker run -d \
  --name wyoming-piper \
  -p 10200:10200 \
  --restart unless-stopped \
  ghcr.io/rhasspy/wyoming-piper:master \
  --voice pl_PL-darkvoice-medium
```

### 5.3 Konfiguracja Assist Pipeline w Home Assistant

Zobacz plik: [`config/home-assistant/configuration.yaml`](../config/home-assistant/configuration.yaml)

Sklonuj repozytorium lub skopiuj pliki konfiguracyjne do katalogu `/config` Home Assistanta, a następnie:

1. Dodaj `!secret openwebui_api_key` do `secrets.yaml` w katalogu Home Assistant
2. Zrestartuj Home Assistant
3. Przejdź do: **Settings → Voice Assistants → Assist → Add Pipeline**
4. Wybierz:
   - STT: Wyoming Whisper
   - Conversation agent: Hermes (OpenAI API)
   - TTS: Wyoming Piper / ElevenLabs
5. Zapisz i przetestuj: "Hey Hermes, włącz światło w salonie"

### 5.4 Integracja openWakeWord

```bash
# Dodaj openWakeWord do Home Assistant przez HACS lub:
# Settings → Add-ons → Wake Word Collection → Zainstaluj "openWakeWord"
```

Następnie:
1. **Settings → Voice Assistants → Wake Words → Add**
2. Nazwa: "Hey Hermes"
3. Model: openWakeWord (wbudowany)
4. Przypisz do pipeline'u Assist

### 5.5 Pełny przepływ (Home Assistant jako centrum)

```
Telefon → [Tailscale] → Home Assistant (Assist Pipeline)
                                  ↓
                          Wyoming STT (Whisper) → tekst
                                  ↓
                          Conversation Agent → Hermes API (Open WebUI)
                                  ↓
                          LLM Response / Intent Execution
                                  ↓
                          Wyoming TTS (Piper) → audio
                                  ↓
                          Odtwarzanie na telefonie przez Tailscale
```

---

## Podsumowanie

Po wykonaniu wszystkich kroków Twój system będzie:

1. **Dostępny zdalnie** przez Tailscale — bez otwartych portów
2. **Głosowy** — mów "Hey Hermes" i wydawaj komendy
3. **Wielojęzyczny** — Whisper rozumie polski, ElevenLabs mówi po polsku
4. **Rozszerzalny** — łatwo dodasz nowe automatyzacje w Home Assistant
5. **Prywatny** — lokalne modele STT/TTS, dane nie wychodzą z sieci

---

## Przydatne Komendy

```bash
# Tailscale
tailscale status                          # lista urządzeń
tailscale ip -4                           # własny adres
tailscale ping 100.x.x.x                  # test opóźnienia
tailscale up                              # (re)uwierzytelnij

# Docker
docker logs open-webui -f                 # logi Open WebUI
docker logs homeassistant -f              # logi Home Assistant
docker restart open-webui                 # restart

# Sieć
curl -s http://100.x.x.x:3000/api/health  # health check Open WebUI
curl -s http://100.x.x.x:8123             # sprawdź Home Assistant
```