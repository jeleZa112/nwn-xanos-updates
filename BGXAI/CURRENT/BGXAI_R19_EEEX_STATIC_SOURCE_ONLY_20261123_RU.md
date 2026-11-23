# BGXAI — R19 статическая проверка EEex v1.1.7 (23.11.2026)

**Предыдущая игровая база:** R13.2/TD15 установлена, в реальном бою четырежды прочитала девять сырых полей защиты цели. R16 и R17 — исходные офлайн-модули по слотам и боеприпасам; R18 — прототип on-demand чтения `getAbility` / `getLauncher`, 58/58 тестов CI PASS, но НЕ установлен. В игре ничего не меняли.

**Результат R19:** подготовлен автономный исходный Python-аудитор `BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py` для проверки **точных установленных** `EEex_Resource.lua`, `EEex_Sprite.lua`, `EEex_Action.lua` относительно официальных Git blob SHA тега `Bubb13/EEex v1.1.7`. Он различает raw exact match, нормализованное LF-соответствие, локальную вариацию с теми же callsites и `HOLD`. Проверяет bootstrap и chitin.key. Lua-лексер исключает ложные методы в комментариях и строках. Нет записи файлов/изменения игры/регистрации слушателя/независимого CMD/доступа к памяти.

**Критическое ограничение:** upstream `CItem.getAbility()` разыменовывает `item.pRes.pHeader` и вызывает `getAbility(index)`, который рассчитывает native ability address. Проверка статического кода **не доказывает**, что native resource загружен и handle жизнеспособен. `sprite:getLauncher` тоже требует валидного native handle. Даже абсолютный SHA match НЕ разрешает выполнение R18 в игре. Активные эффекты, полный APR других слотов и EPS/manual boundary тоже не подтверждены.

**Подтверждённые факты:** official Git blob SHA `EEex_Resource.lua=5ecd3c2f9e9bcc6cbd317653fc057a06d956916b`, `EEex_Sprite.lua=b2d8d930c47785737bd30dad08e9f35a9d859578`, `EEex_Action.lua=e7543274ed066b5abe3c58262105212f208d1595`; SHA получены из **tag v1.1.7** GitHub, не из установленного пользователя. Точное installed сравнение **не выполнялось**, не нужно придумывать его результат.

**Тесты:** 36/36 локальных Python fixtures PASS; отдельный Windows/Linux CI запускается при публикации; не объявлять его успешным до фактического результата. 

**Стадии:** R19 CODE=готово; OFFLINE TEST=PASS; INSTALLED_EEEX_AUDIT=NOT RUN; DEPLOY=NO; LIVE=NO; WEAPON_SWITCH=OFF. TD15 установлен и ранее LIVE проверен. Сохранить в `BGXAI/BUILD/R19_INSTALLED_EEEX_STATIC_RO_20261123` и `BGXAI/CURRENT`; обновить `00_AUTO_CONTINUE_READ_FIRST.md` после CI.

**Следующий узкий шаг:** встроить **только статическую read-only проверку** в существующий `BGXAI_UPDATE.cmd` после безопасной регрессии, если это нужно для запуска на пользовательской машине. Не запускать подозрительный pointer-dereference и не создавать параллельный updater. Ранкер V1/V2/V5 и NONINTERRUPT уже существуют: не переделывать и не выдавать сканер за рабочее переключение оружия.

## 23.11.2026 — R19 INDEPENDENT CI COMPLETE

- Windows GitHub Actions: **36/36 PASS**; SHA256 and no-dispatch checks PASS.
- Linux GitHub Actions: **36/36 PASS**; SHA256 and no-dispatch checks PASS.
- Successful run: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45145353551
- Source commit: 949284619e6367f2197c700f34ddf707a6f6625f.
- **R19 CODE/TEST PASS; installed EEex NOT SCANNED; DEPLOY NO; LIVE NO.** TD15 remains unchanged.
