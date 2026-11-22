# BGXAI R13 — штатный пункт 161 для пассивного чтения защиты цели

Дата: 22.11.2026. Режим: R13 `CODE/TEST PASS`, `DEPLOY NOT YET`, `LIVE NOT YET`.

## Исходная причина

Пользователь успешно выполнил `160` V3: `CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED`; базовая EEex, R1/R2/R4 на месте, необязательный `B3AttackInfo.lua` отсутствует. Ставить Attack Info для BGXAI не требуется.

## Новое

R13 получает 8 необработанных защитных статов текущей цели через `EEex_Sprite_GetActiveStats(target)` и `EEex_GameObject_Get(targetID)` из начатого действия. Два чтения должны совпасть; проверяются source/target/action/selected slot/ability, при дрейфе `HOLD`. `R13` не знает точного иммунитета/вероятности попадания, не знает APR другого слота и не разрешает выбирать оружие.

Изолированный `M_BGXTDEF13.lua` регистрирует только один новый **пассивный** listener с лимитом 64 событий, использует внешнюю папку отчётов или console fallback. R4/EPS/V6 не переписываются. Установка только отдельным WeiDU компонентом `BGXTDEF13` с внешним backup и typed approval.

## Фактические тесты

- `test_r13.lua`: 33/33 PASS.
- `test_r13_runtime.lua`: 14/14 PASS.
- `test_r13_guarded.py`: 26/26 PASS.
- Windows CI `test_menu161.py`: 10/10 PASS, все старые 1..160 обработчики сохранены обратимым преобразованием, native PowerShell 5.1/7 AST PASS.
- Новый единый sync-кандидат 79 610 байт, SHA256 (Windows) `5740c40cb876b69e664a930b32f089a3431b4a9218537ce9d95b9997095ee2b5`.
- GitHub CI: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45045387527

## Что потребуется пользователю после публикации PIN

1. Закрыть Baldur’s Gate и InfinityLoader (не удалять файлы).
2. Запустить только `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.
3. В главном меню выбрать **161**, во вложенном меню выбрать **2 (READ-ONLY preflight)**.
4. Прислать JSON/консоль целиком. Сведения о `currentWeiDULast` нужны, чтобы планировать только last-only rollback.
5. Не выбирать **3 (install)** и не вводить `INSTALL_BGXAI_R13_PASSIVE_TARGET`, пока не будет отдельного согласия на живой тест.

## Не изменять

BG Voice RU, BG_EET_RU, R1/R2/R4, EPS18.4, V6, WeiDU.log и игровые сохранения. R13 источник не выдаёт синтетические прогнозы за LIVE. Правило автоматического продолжения после успешного PASS — постоянно.
