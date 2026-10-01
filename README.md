# canal-digitaal

<img src="https://img.shields.io/github/stars/hmol33/canal-digitaal?style=flat-square&color=blue" alt="Stars">
<img src="https://img.shields.io/github/forks/hmol33/canal-digitaal?style=flat-square&color=green" alt="Forks">
<img src="https://img.shields.io/github/license/hmol33/canal-digitaal?style=flat-square" alt="License">

Almost "Instant" Kodi Addon Repository — auto genereert je persoonlijke Kodi addon repository gehost op GitHub.

## Installatie

### Vereisten

- Bash omgeving
- Git
- Travis CI account

### Installatie

1. Maak een nieuwe GitHub repository aan met de bestanden uit deze repo of fork deze repo
2. Maak een account aan op [Travis CI](https://travis-ci.org) en voeg je project toe
3. Clone je repo lokaal:

```bash
git clone git@github.com:YOUR_USER_NAME/YOUR_REPO_NAME.git my_kodi_repo
cd my_kodi_repo
```

4. Genereer een GitHub deploy key:

```bash
ssh-keygen -q -t rsa -b 4096 -C 'put-your-repo-name-here' -f deploy_key -N ''
```

5. Voeg `deploy_key.pub` toe als Deploy key in je repo instellingen (met write access)
6. Installeer de [Travis CLI](https://github.com/travis-ci/travis.rb#installation) en login:

```bash
travis login
```

7. Versleutel je deploy key:

```bash
travis encrypt-file deploy_key .github/deploy_key.enc
```

8. Voeg je addon source code toe in de `src/` folder
9. Commit en push:

```bash
git add -A .
git push
```

## Gebruik

Na installatie wordt je persoonlijke Kodi addon repository automatisch gegenereerd op:

```
https://your_user_name.github.io/your_repo_name/
```

De repository wordt automatisch bijgewerkt elke keer dat je je addon code update.

## Bijdragers

- [hmol33](https://github.com/hmol33) — Onderhouder
- [ping](https://github.com/ping) — Original instant-kodi-repo creator

## Licentie

GPL-3.0 — zie [LICENSE](LICENSE) voor details.

## Features

- Auto genereert je persoonlijke Kodi addon repository gehost op GitHub
- Auto updates elke keer dat je je addon code update
- Auto genereert een repository addon zip voor je nieuwe persoonlijke repository

## Demo

[Demo](https://ping.github.io/instant-kodi-repo/)
