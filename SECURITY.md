# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

Als je een beveiligingslek vindt, neem dan contact op via:

- **GitHub**: Maak een [private security advisory](https://github.com/hmol33/canal-digitaal/security/advisories/new) aan
- **Email**: Stuur een email naar de maintainer

Verwacht een reactie binnen 48 uur. We nemen beveiligingslekken serieus en zullen deze zo snel mogelijk verhelpen.

## Known Security Considerations

- **Credentials**: Wachtwoorden worden lokaal opgeslagen in Kodi's settings. Gebruik unieke wachtwoorden.
- **API tokens**: Session tokens worden opgeslagen in Kodi's settings. Deze verlopen na 2 uur.
- **HTTPS**: Alle API communicatie gebruikt HTTPS.
- **DRM**: Widevine DRM wordt gebruikt voor beveiligde streams.

## Security Best Practices voor Gebruikers

1. Gebruik een sterk, uniek wachtwoord voor je Canal Digitaal account
2. Deel je inloggegevens nooit met anderen
3. Houd Kodi en de addon up-to-date
4. Gebruik alleen de officiële repository voor updates
