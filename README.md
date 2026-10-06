# Canal Digitaal Kodi Addon

[![CI](https://github.com/hmol33/canal-digitaal/actions/workflows/ci.yml/badge.svg)](https://github.com/hmol33/canal-digitaal/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Kodi](https://img.shields.io/badge/Kodi-19+-blue.svg)](https://kodi.tv)

Kodi addon voor het bekijken van Canal Digitaal IPTV (Nederland). Ondersteunt Live TV, Replay TV, en VOD.

## Features

- **Live TV** - Bekijk live zenders van Canal Digitaal
- **Replay TV** - Bekijk programma's uit het verleden (tot 7 dagen)
- **VOD** - Video on demand content (series en films)
- **Zoeken** - Doorzoek alle content met fuzzy matching
- **Kanaalkeuze** - Kies welke zenders je wilt zien
- **EPG** - Electronic program guide ondersteuning
- **PVR** - Integratie met Kodi PVR IPTV Simple Client

## Vereisten

- Kodi 19.0 (Matrix) of hoger
- Canal Digitaal abonnement
- Widevine DRM ondersteuning (voor beveiligde streams)

## Installatie

### Via Repository

1. Download de [repository.anon.iptv](https://github.com/hmol33/canal-digitaal/releases) zip
2. In Kodi: **Add-ons** → **Install from zip file**
3. Navigeer naar de gedownloade zip en installeer
4. Ga naar **Install from repository** → **Dutch IPTV Repository** → **Video add-ons** → **Canal Digitaal IPTV**

### Vanuit broncode

```bash
git clone https://github.com/hmol33/canal-digitaal.git
cd canal-digitaal
# Kopieer de plugin.video.canaldigitaal map naar je Kodi addons directory
```

## Configuratie

1. Open de addon in Kodi
2. Ga naar **Instellingen**
3. Voer je Canal Digitaal inloggegevens in
4. Optioneel: configureer proxy, EPG, en kanaalkeuze

## Bijdragen

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor richtlijnen.

## Beveiliging

Zie [SECURITY.md](SECURITY.md) voor het beveiligingsbeleid en het rapporteren van kwetsbaarheden.

## Licentie

Dit project is gelicenseerd onder de GNU General Public License v3.0 - zie [LICENSE](LICENSE) voor details.

## Disclaimer

Dit project is niet gelieerd aan of ondersteund door Canal Digitaal. Het is een onafhankelijk project gemaakt door de community.

## Bijdragers

- [hmol33](https://github.com/hmol33) — Onderhouder
- [ping](https://github.com/ping) — Original instant-kodi-repo creator
