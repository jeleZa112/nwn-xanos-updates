# BGXAI R33 — использовать уже существующие R31/R4 profили, без второго наблюдателя

## РЕЛИЗ 25.11.2026: Р33 ПУНКТ 172 ОПУБЛИКОВАН — УСТАНОВКА НЕ ВЫПОЛНЕНА

**Уточнение к нижним историческим разделам:** теперь source-only R33 поставлен в **существующий один `BGXAI_UPDATE.cmd` (меню 172)** без изменения самого CMD. Это публикация проверенного установщика, **не** изменение установленной игры; R31 продолжает работать и уже прошёл 12/12 live samples. Старые ниже фразы «не интегрирован» описывают состояние ДО этого релиза.

**Проверенная публикация:** `BGXAI/BGXAI_SYNC.ps1`, 79 874 байта, SHA256 `4f04b43f69d4171e2686f017d334eac69f91d9389a18122110c2bfd44a2d5663`, immutable commit `f383ad5ca3515f6fc166ca1a2337a88f9d2cad49`, `BGXAI/fox_new/BOOTSTRAP_PIN.json`. Меню 1–171 byte-for-byte сохранены. Новый пункт `172` предлагает `1=RO preflight, 2=typed install, 3=status, 4=typed last-only rollback, 5=capture`.

**Артефакты:** кандидат `M_BGXR27_R33_SOURCE_ONLY.lua` 49 438 байт, SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`; guard `R33_GUARDED_SOURCE_ONLY.py` 22 132 байта, SHA256 `0815d173b276c0f990eb3ab66ac6f8f614a9a0f0f59fc301f94f5f8c890be653`. Путь `R33_RELEASE_VERDICT_20261125.json` содержит все контрольные значения.

**[GitHub Actions 45647273764](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45647273764) = SUCCESS во всех 5 задачах**, включая Win+Linux guard-mock, реальный разбор TP2 WeiDU 251 на Win+Linux, PS5.1 AST, SHA-проверку pinned source и неизменность исходного CMD/старых меню. Значит: **CODE/TEST/RELEASE PASS**, но **DEPLOY/LIVE R33 NO**.

**Без повторного лишнего запуска:** при закрытой игре запускать только старый `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → `172` → `2`. Guard сам выполнит read-only preflight, затем предложит ввести `INSTALL_BGXAI_R33_PASSIVE_PROF_AFTER_R31`. ENTER вместо точной строки отменяет установку. При STOP — не повторять, прислать один `BGXAI_R33_INSTALL_*.json`. При PASS — прислать тот же JSON; тогда один игровой capture `172 → 5` после согласования теста. Смена оружия пока **не** разрешена этим модулем.

**Безопасность:** R31 должен быть последним компонентом 151, после установки R33 — последний 152. Меняется только `override/M_BGXR27.lua` через новый WeiDU компонент; другие BCS, EPS/EEex, сейвы, BG Voice RU/BG_EET_RU не меняются. Внешняя SHA backup и last-only rollback при отдельном токене `ROLLBACK_BGXAI_R33_PASSIVE_PROF_ONLY`, но никаких автоматических откатов.

---

## Состояние 25.11.2026

**CODE / TEST / CI:** PASS. **DEPLOY / LIVE R33:** NO. R31 остаётся реально установленным и подтверждённым наблюдателем (12/12 событий). R33 не устанавливался, не менял EET, WeiDU, EPS, BG Voice RU, BG_EET_RU или сейвы.

Источник R31/EEex x64:
- [R31 исходник](../R31_R27V3_PASSIVE_SOURCE_20261125/M_BGXR27_R31_SOURCE_ONLY.lua) SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`, 47550 байт.
- R31 R4 уже использует `EEex_Sprite_GetActiveStats` дважды в одном вызове и читает `m_nLevel1`, `m_nLevel2`, `m_nLevel3`, `m_nKit`, а также полный массив `m_nProficiency*` (stat IDs 89–115 и extras 116–134). Новый `R33` **не повторяет эти engine reads**; только берёт существующий объект `r4.fields` и сериализует его.
- `m_typeAI.m_Class` — не класс из `CLSWPBON.2DA` и не подтверждение права дуала. R33 берёт только raw AI-class, до и после наблюдения; если изменился — HOLD. Основание поля: [EEex-Docs CG — CGameObject.m_typeAI](https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20%28x64%29/CG/index.rst), [EEex-Docs CA — CAIObjectType.m_Class](https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20%28x64%29/CA/index.rst), [CDerivedStats](https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20%28x64%29/CD/index.rst).

### Реальное изменение в подготовленном кандидате

`build_r33_r31_reuse_prof_ro.py` проверяет точный SHA старого исходника и применяет ограниченные exact-match замены в оперативной памяти. Результат **49 438 байт**, SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`. Полученный Lua существует только во временной папке CI; установленный `override/M_BGXR27.lua` не меняется. Проверяются неизменность числа listener registrations, отсутствие новых engine actions, неизменность R31 оригинала, запрет записи в `override`/EEex.

В сообщение уже существующего события `R27_SINGLE_CALLBACK` после стабильного double-read добавлены:
- `levelsAndKitRaw`: 3 уровня + kit RAW;
- `aiObjectClassRawCandidate`: опциональный AI-CLASS RAW;
- `proficiencyStat89to134Raw`: упорядоченный массив из 46 raw значений, `null` при недоступности; `i=1` соответствует стату ID 89;
- постоянные `classRowVerified=false`, `weaponToProficiencyVerified=false`, `activeDualMultiClassVerified=false`, `actorPipsVerified=false`, `alternativeAPRVerified=false`, `dispatchAuthorized=false`.

**Никаких выводов о смене оружия из raw очереди = 0**, несмотря на реальный `actionRaw=3` в R31. Никаких дублей APR от WSPATCK поверх финальных игровых статов.

### Тесты и результат

[GitHub Actions №45645196992](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45645196992) **SUCCESS** в трёх задачах:
- Windows Python 3.12 source-only SHA exact generator + unit;
- Ubuntu Python 3.12 то же;
- Lua 5.3 / Lua 5.4 / LuaJIT: идентификаторы 90 long sword, 104 long bow, 105 short bow, 116 extra, один listener, `orders=0`, нестабильные профили/класс приводят к HOLD, повторная загрузка скрипта не регистрирует второй listener.

Первые два ошибочных CI-запуска исправлены только в тестах: LF/CRLF Windows при записи временного файла, тестовая подмена сохранённой EEex-функции после регистрации. ПРАВИЛО: регистрируемый R31 pilot фиксирует ссылку на EEex API при загрузке — изменение global функции после загрузки не меняет callback. Это полезно для проектирования реального runtime.

### Следующая не выполненная стадия

Нужен один guarded, LAST-ONLY, SHA-verified R31→R33 WeiDU upgrade через единственный `BGXAI_UPDATE.cmd`, с отдельным typed consent, внешним backup и независимым runtime test. **Сейчас интеграции в обновлятор, разрешения установки и LIVE R33 нет.** Даже после такой проверки R33 не устанавливает weapon priority: обязательны item ability→proficiency mapping для всех quickslot, class/kit/multiclass/dual semantics, временные статусы и **фактический final-effective APR для каждого альтернативного слота**.
