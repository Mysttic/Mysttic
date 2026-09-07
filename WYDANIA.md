# Jak podłączyć projekt do tej strony

To repozytorium pełni dwie role: jest wizytówką profilu i miejscem, z którego
ludzie pobierają moje aplikacje. Kod aplikacji leży w prywatnych
repozytoriach, tutaj trafiają wyłącznie gotowe pliki wydań i strony, które je
pokazują.

Ten dokument opisuje, co musi zrobić projekt, żeby jego wydania lądowały tutaj
same. Wzorem jest Chatt, który chodzi tak od wersji 0.6.1.

## Jak to działa w całości

1. Projekt buduje i publikuje wydanie u siebie, tak jak dotąd. Tam zostaje
   pełna historia wydań.
2. Zaraz potem osobny job kopiuje te same pliki tutaj, pod tagiem
   z przedrostkiem projektu.
3. Po udanej kopii kasuje starsze wydania tego samego projektu razem z tagami.
   Na stronie stoi jedna wersja, najnowsza.
4. Strona projektu odpytuje API przy każdym wejściu i wypełnia się sama, więc
   publikacja wydania nie wymaga żadnego commita tutaj.

## Kontrakt

Trzy rzeczy czyta więcej niż jeden program, więc zmiana którejkolwiek psuje coś
poza samą stroną.

### 1. Tag z przedrostkiem projektu

```
chatt-v0.6.2
skaner-v2.0.1
```

Przedrostek jest obowiązkowy. `GET /releases/latest` zwraca najnowsze wydanie
w całym repozytorium, bez względu na to, której aplikacji dotyczy, więc bez
przedrostka Chatt zobaczyłby wydanie skanera jako swoje. Wszystko, co czyta
wydania, filtruje po tym przedrostku i bierze pierwsze z listy.

### 2. Nazwy plików z numerem wersji i platformą

```
<projekt>-<wersja>-<platforma>.<rozszerzenie>
```

Chatt:

```
chatt-0.6.2-windows-instalator.exe
chatt-0.6.2-windows.zip
chatt-0.6.2-android.apk
```

Strona dopasowuje pliki po końcówce nazwy, tak samo robi aktualizacja
w aplikacji. Nazwy plików są stałym elementem, nie szczegółem wydania.

### 3. Opis: numer i adres strony

```
Chatt 0.6.2

https://mysttic.github.io/Mysttic/chatt/
```

Tyle. Opisy generowane z historii pull requestów prowadzą do prywatnego
repozytorium, więc czytelnik dostaje 404. Ten sam tekst pokazuje się na karcie
aktualizacji w aplikacji, jeśli projekt ma taką funkcję.

## Co zrobić po stronie projektu

### Sekret z poświadczeniem

Domyślny `GITHUB_TOKEN` sięga wyłącznie do repozytorium, w którym chodzi
workflow, więc kopiowanie tutaj potrzebuje własnego tokenu.

1. https://github.com/settings/personal-access-tokens, token drobnoziarnisty.
2. Właściciel `Mysttic`, dostęp tylko do repozytorium `Mysttic/Mysttic`.
3. Uprawnienie **Contents: Read and write**.
4. W repozytorium projektu: *Settings, Secrets and variables, Actions, New
   repository secret*, nazwa `HUB_TOKEN`.

Token ma datę ważności. Kiedy wygaśnie, job zatrzyma się z czytelnym błędem,
a wydanie w repozytorium projektu zostanie na miejscu.

### Job w workflow wydania

Do wstawienia po jobie, który publikuje wydanie u siebie. Do zmiany są cztery
wartości na górze: `PROJEKT`, `STRONA`, `NAZWA` i liczba plików w kroku
sprawdzającym.

```yaml
  witryna:
    name: Kopia na stronę
    needs: [wersja, wydanie]
    if: needs.wersja.outputs.wydajemy == 'true'
    runs-on: ubuntu-latest
    env:
      HUB: Mysttic/Mysttic
      PROJEKT: chatt
      NAZWA: Chatt
      STRONA: https://mysttic.github.io/Mysttic/chatt/
      WERSJA: ${{ needs.wersja.outputs.wersja }}
      TAG: ${{ needs.wersja.outputs.tag }}
      TAG_HUB: chatt-v${{ needs.wersja.outputs.wersja }}
    steps:
      - name: Poświadczenie do repozytorium z witryną
        env:
          HUB_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -uo pipefail
          if [ -z "${HUB_TOKEN:-}" ]; then
            echo "::error::Brak sekretu HUB_TOKEN. Wydanie $TAG powstało, kopia na stronę nie."
            echo "::error::Potrzebny token osobisty z uprawnieniem Contents: read and write do $HUB."
            exit 1
          fi

      - name: Pliki z wydania
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          mkdir -p kopia
          gh release download "$TAG" --repo "$GITHUB_REPOSITORY" \
            --dir kopia --pattern "$PROJEKT-*"
          ls -la kopia
          if [ "$(ls -1 kopia | wc -l)" -ne 3 ]; then
            echo "::error::Spodziewałem się trzech plików w wydaniu $TAG."
            exit 1
          fi

      - name: Opis wydania
        run: |
          set -euo pipefail
          {
            echo "$NAZWA $WERSJA"
            echo
            echo "$STRONA"
          } > opis.md
          cat opis.md

      - name: Wydanie na stronie
        env:
          GH_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -euo pipefail
          if gh release view "$TAG_HUB" --repo "$HUB" >/dev/null 2>&1; then
            gh release delete "$TAG_HUB" --repo "$HUB" --cleanup-tag --yes
          fi
          gh release create "$TAG_HUB" kopia/* \
            --repo "$HUB" \
            --title "$NAZWA $WERSJA" \
            --notes-file opis.md \
            --target master

      - name: Strona trzyma jedną wersję
        env:
          GH_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -euo pipefail
          gh release list --repo "$HUB" --limit 100 --json tagName -q '.[].tagName' \
            | { grep -E "^$PROJEKT-v" || true; } \
            | { grep -vxF "$TAG_HUB" || true; } \
            | while read -r stary; do
                echo "Kasuję $stary"
                gh release delete "$stary" --repo "$HUB" --cleanup-tag --yes
              done
          echo "Na stronie zostaje $TAG_HUB" >> "$GITHUB_STEP_SUMMARY"
```

Kolejność ma znaczenie: nowe wydanie powstaje przed skasowaniem starych, więc
strona ani przez chwilę nie stoi pusta. Filtr po `^$PROJEKT-v` pilnuje, żeby
kasowanie nie ruszyło wydań pozostałych projektów.

## Co zrobić tutaj

Katalog `<projekt>/` z własnym `index.html` i grafikami, w układzie takim jak
`chatt/`. Wspólny arkusz stylów leży w `assets/style.css`, więc podstrona
podpina go przez `../assets/style.css`. Na górze skryptu w `index.html` stoją
dwie stałe do ustawienia:

```js
const REPO = 'Mysttic/Mysttic';
const PRZEDROSTEK = 'chatt-v';
```

Do tego kafle z wzorcami nazw plików:

```js
const KAFLE = [
  { id: 'exe', wzor: /-windows-instalator\.exe$/ },
  { id: 'zip', wzor: /-windows\.zip$/ },
  { id: 'apk', wzor: /-android\.apk$/ },
];
```

Nowy projekt dochodzi też jako karta w `index.html` w korzeniu.

## Aktualizacja z poziomu aplikacji

Jeśli aplikacja ma sama pytać o nowe wydanie, pyta dokładnie tak jak strona:

```
GET https://api.github.com/repos/Mysttic/Mysttic/releases?per_page=30
Accept: application/vnd.github+json
```

Dalej: odsiać `draft` i `prerelease`, zostawić tagi z przedrostkiem projektu,
wziąć pierwsze, z `assets[]` wybrać plik dla swojej platformy po nazwie.

Trzy rzeczy warto mieć na uwadze:

- **Adres `/releases/latest` nie nadaje się tutaj.** Zwraca najnowsze wydanie
  w całym repozytorium, więc przy dwóch projektach zacznie kłamać.
- **Limit bez logowania to 60 zapytań na godzinę na adres IP.** Pytanie raz na
  dobę mieści się w tym z zapasem.
- **Awaria ma być cicha.** Timeout, brak sieci i zmieniony kształt odpowiedzi
  kończą się komunikatem, a aplikacja pracuje dalej.

Zmiana schematu tagów albo nazw plików zepsuje aktualizacje u ludzi, którzy
mają już aplikację zainstalowaną, a dowiedzą się o tym dopiero wtedy, gdy
przestanie im działać. Jeżeli coś tu ma się zmienić, najpierw wychodzi wersja
czytająca nowy schemat, potem zmienia się schemat.

## Lista kontrolna

- [ ] token `HUB_TOKEN` w sekretach repozytorium projektu;
- [ ] job `witryna` w workflow wydania, z ustawionymi `PROJEKT`, `NAZWA`
      i `STRONA`;
- [ ] tagi z przedrostkiem `<projekt>-v`;
- [ ] nazwy plików z numerem wersji i platformą;
- [ ] katalog `<projekt>/` z podstroną, z ustawionymi `REPO`, `PRZEDROSTEK`
      i `KAFLE`;
- [ ] karta projektu w `index.html` w korzeniu;
- [ ] po pierwszym wydaniu: strona pokazuje numer i pobiera pliki, a stare
      wydania tego projektu zniknęły z listy wydań.
