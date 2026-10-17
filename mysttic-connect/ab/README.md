# Mysttic Connect obok Mirth Connect 4.5.2

Nagrania i prezentacja pokazane na [stronie Mysttic Connect](../) (sekcja „Obok oryginału: Mirth
Connect 4.5.2”). Nagrane 16 października 2026 skryptem, który steruje oboma Administratorami w tej
samej chwili, wysyła do obu silników te same komunikaty i porównuje wyniki regułami automatycznego
testu A/B; nic nie jest poprawiane ręcznie.

| Strona | Obraz Docker |
|---|---|
| lewa | oficjalny obraz Mirth Connect 4.5.2, skrót `sha256:4afa295cfe7c5ffd596efee69594157fea87202e33d66bb4a98a52db4598f836` |
| prawa | Mysttic Connect 1.2.1, `ghcr.io/mysttic/mysttic-connect:1.2.1`, skrót `sha256:0df9fc7984437cf125a9c007845fb46398f23a0fff693cbc9d0214761318fb57` |

Mysttic Connect 1.3.0, wydanie na stronie, ma ten sam silnik: jego zmiany dotyczą Administratora,
instalatora Windows i Server Managera, nie przetwarzania komunikatów.

| Plik | Czas | Wynik porównania |
|---|---|---|
| `01-import-kanalu.mp4` | 1:29 | identyczne |
| `02-hl7-mllp-ack.mp4` | 1:20 | identyczne |
| `03-http-do-pliku.mp4` | 1:52 | identyczne; różni się tylko nazwa produktu w domyślnym nagłówku `User-Agent` |
| `04-skrypt-javascript.mp4` | 1:48 | identyczne |
| `05-dashboard-i-wiadomosci.mp4` | 1:21 | identyczne; różni się tylko nazwa produktu w domyślnym nagłówku `User-Agent` |
| `mysttic-connect-1.2.1-ab.pdf`, `.pptx` | 23 slajdy | te same plansze i zrzuty |

Klipy mają 1920x1080, H.264, napisy po polsku, bez dźwięku. `<klip>.jpg` to kadr z nagrania (plakat
na stronie), `<klip>-result.jpg` jego plansza końcowa. `SHA256SUMS` wymienia nagrania i prezentację.

Mirth Connect jest znakiem towarowym NextGen Healthcare, Inc. Mysttic Connect jest niezależnym
projektem, niezwiązanym z NextGen Healthcare ani przez nią niepopieranym. Lewa strona każdego nagrania
pokazuje oficjalny obraz Docker Mirth Connect 4.5.2 bez zmian; widoczne na niej nazwy i logo należą
do ich właścicieli.
