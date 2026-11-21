# BGXAI — выбор оружия: R3 native ITM/SPL/2DA (21.11.2026)

## Текущий статус CODE / TEST / DEPLOY / LIVE

- **CODE:** написан отдельный `BGXAI_WEAPON_NATIVE_ITM_R3_RO.py` (18 641 байт), который берёт **реальные resref** из уже записанного `BGXAI_WEAPON_SLOTS_RAW_R2.jsonl`, читает в текущей установленной игре `chitin.key` и необходимые ресурсы из `override` либо BIFF. Обрабатывает BIFF V1, BIF V1.0, BIFC V1.0 (ограничение на распаковку); извлекает ITM V1 (общие поля/способности/equipped и ability effects), связанные SPL V1 по opcode 146 и `WSPATCK.2DA`/`CLSWPBON.2DA`. Все поля — read-only, никакого начисления итогового APR поверх движка, приказов и переключения.
- **TEST:** 30/30 локальных независимых тестов R3 (в том числе фикстуры из **подлинных** SW1H04.ITM, STAF01.ITM и SW1H04.SPL из сохранённого ZIP; синтетические KEY/BIFF, BIF/BIFC, защиты от подмены/порчи и парсинг 2DA). 35/35 локальных Python-тестов старого R2-guarded+collector и нового пункта меню R3. Итого **65/65 OFFLINE PASS**; Windows `chitin.key` / реальный BIF R3 ещё не тестировались.
- **DEPLOY:** R3-модуль в игру НЕ установлен и не нужен для read-only аудита. Опубликован код/пин обновлятора, не были изменены BCS, Lua из override, WeiDU, R1.1, R2, BGXRANGED6 V6, EPS, сейвы. Уже ранее установленный R1.1 и R2 показали LIVE данные (R2 10 snapshots, 0 malformed).
- **LIVE R3:** НЕ выполнен. Без актуальных ITM для BOW05, AROW01, SHLD03A, полной экипировки, class/kit proficiency, активных бафов, EPS/manual queue и target defenses **никакого разрешения на выбор оружия**. `dispatchAuthorized=false`.

## Доказано на старом ZIP от пользователя, а НЕ на нынешних игровых ресурсах

Библиотека: `/BALDURS_GATE_EET_AI/SOURCES/BG_EET_AUDIT_01_MAGIC.zip`, SHA256 `515774b8627f1d159e694035f6b1b090f57eeccaa9d04e0df3e2dc31224635b8`. В нём 5 804 ITM и 3 458 SPL, в том числе:

- `SW1H04.ITM` — основной melee ability: **1d8**, reach **1**, speed **5**, THAC0 bonus **0**, damage bonus **0**. Equipping effects: opcode **7** ×3. При ударе ability effect opcode **146**, ресурс **SW1H04.SPL**. В linked SPL реально есть эффекты opcode **318, 112, 122, 139**. Их семантика и фактическое применение/полный ожидаемый урон **НЕ оценены**, поэтому нельзя выбирать по одному 1d8.
- `STAF01.ITM` — melee ability **1d6**, reach **2**, speed **4**, THAC0 bonus **0**, damage bonus **0**. Equipping effects opcode **7** ×5. Полная эффективность НЕ доказана.
- `BOW05.ITM`, `AROW01.ITM`, `SHLD03A.ITM` в данном ZIP **нет**. Не смешивать с `BDBOW05`, `BDAROW01` или любыми похожими именами.
- `CLSWPBON.2DA` в старом ZIP разобран: 77 строк; в строке `FIGHTER` стоит `GETS_PROF_APR=1`. Это **архивное** значение, не текущее подтверждение класса персонажа и не повод прибавлять APR повторно. `WSPATCK.2DA` отсутствует в этом ZIP и ранее отсутствовал в current game override; R3 сможет искать его по `chitin.key`.

`BGXAI_WEAPON_ITM_ARCHIVE_R3_SOURCE_SNAPSHOT.json` сохранён в Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/` и отдельным локальным файлом. Его статус — `ITM_NATIVE_PARTIAL_HOLD`; это корректно.

## Единый обновлятор и следующий необходимый тест

Существующий у пользователя `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` не заменяется. GitHub `bg-eet-ai` закреплённый immutable commit **`e0f606a6b780d1eef1b77a8f5f204db927dc5a0c`**; `BGXAI/BGXAI_SYNC.ps1` SHA256 **`be239cfabfa6efe1bdd651264231d14afc7e05783b6800cf0487f0992dafe595`**, **79 967 байт** (меньше ограничения 80 000). Bootstrap pin GitHub commit **`7181d3a7712a0aff0eb8f74034f97c5c34658076`**. Пакет 159 содержит пять SHA-verified файлов, проверка 5/5 PASS; действующий `M_BGXWP.lua` и `M_BGXW2.lua` **не менялись**.

**Один шаг пользователя только после завершения игры:** запустить привычный `BGXAI_UPDATE.cmd` и выбрать **159 → 7 → 6**. Это READ ONLY извлечение актуальных ITM/SPL/2DA и создание отчёта **только** в `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_WEAPON_NATIVE_ITM_R3.json`. Игра/InfinityLoader/WeiDU должны быть закрыты. Сразу после запуска прислать этот JSON; если вывод `R3_READONLY_HOLD`, `BGXW2_STOP` или файла нет — прислать один `BGXW2_SETUP_R2.json` и текст ошибки, не повторяя старые установки.

**Ни повторения 158, ни R1/R2 install/preflight/live test не требуется.** R3 не читает во время боя; использует ранее полученный игровой лог R2, а на компьютере читает только данные установленных ITM из файлов ресурсов. Главное продолжение после результата R3: привязка реального launcher+ammo+ability и активных характеристик без двойного APR, затем EPS/manual protected action boundary; только тогда source-only скоринг и разрешённый исполнитель.

## Источники форматов

- IESDP ITM V1: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/itm_v1.htm
- IESDP SPL V1: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/spl_v1.htm
- IESDP KEY V1: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/key_v1.htm
- IESDP BIFF V1/BIFC: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/bif_v1.htm
