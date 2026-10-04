# canal-digitaal

<img src="https://img.shields.io/github/stars/hmol33/canal-digitaal?style=flat-square&color=blue" alt="Stars">
<img src="https://img.shields.io/github/forks/hmol33/canal-digitaal?style=flat-square&color=green" alt="Forks">
<img src="https://img.shields.io/github/license/hmol33/canal-digitaal?style=flat-square" alt="License">
<img src="https://github.com/hmol33/canal-digitaal/workflows/CI/badge.svg" alt="CI">

Almost "Instant" Kodi Addon Repository — auto genereert je persoonlijke Kodi addon repository gehost op GitHub.

## Installatie

### Vereisten

- Bash omgeving
- Git
- Python 3.x
- GitHub account

### Installatie

1. Maak een nieuwe GitHub repository aan met de bestanden uit deze repo of fork deze repo
2. Voeg je addon source code toe in de `src/` folder
3. Commit en push:

```bash
git add -A .
git push
```

4. Schakel GitHub Pages in bij je repo instellingen (Settings → Pages → Source: gh-pages branch)

## Gebruik

Na installatie wordt je persoonlijke Kodi addon repository automatisch gegenereerd op:

```
https://your_user_name.github.io/your_repo_name/
```

De repository wordt automatisch bijgewerkt elke keer dat je je addon code update.

## CI/CD

Deze repo gebruikt GitHub Actions voor continuous integration. De workflow:
- Valideert Python scripts (py_compile)
- Valideert config.json
- Controleert shell script syntax (bash -n)
- Deployed automatisch naar GitHub Pages bij elke push naar master

## Bijdragers

- [hmol33](https://github.com/hmol33) — Onderhouder
- [ping](https://github.com/ping) — Original instant-kodi-repo creator

## Licentie

GPL-3.0 — zie [LICENSE](LICENSE) voor details.

## Features
- Auto genereert je persoonlijke Kodi addon repository gehost op GitHub
- Auto updates elke keer dat je je addon code update
- Auto genereert een repository addon zip voor je nieuwe persoonlijke repository
- GitHub Actions CI/CD pipeline
- Python 3 compatibel
- Structured logging met timestamps
- Error handling met duidelijke foutmeldingen
- Input validatie voor alle build scripts

## Demo

[Demo](https://ping.github.io/instant-kodi-repo/)
