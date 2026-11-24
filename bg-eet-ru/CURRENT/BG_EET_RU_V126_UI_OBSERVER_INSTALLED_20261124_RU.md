# BG_EET_RU — V126 UI-наблюдатель УСТАНОВЛЕН, ожидает игровую проверку

Дата пользовательского ZIP: `SEND_TO_CHATGPT_BG_EET_RU(20261124-164412).zip` от 24.11.2026, SHA256 `4c713887cf0f497bc09755594d081e801b9a76077f1e3613e1d6ce54b42c1291`. ZIP 133 уникальных файлов, CRC PASS.

**Новый существенный факт** из `63_V126_VISIBLE_ROW_OBSERVER.json`:
- `mode=install`
- `status=V126_VISIBLE_ROW_OBSERVER_INSTALLED_AWAITING_RUNTIME_UI_TEST` — реальная защищённая установка в пользовательской игре состоялась.
- `game_files_written=1`, только разрешённый патч `override/UI.MENU`. Исходный SHA `86ba0c4c36b33a97c4dd57f07ee344df6c2198f46f444f574c798791ad6f7a09`; кандидат SHA `bf78a54b77959ca8a47afe9d3c13da30340e1353cb7f77ebfc3a4959bbc240ac`.
- `native_hooks_installed=false`; `native_abi_verified=false`; `miss_weapon_verified=false`; `combat_row_join_verified=false`; `display_text_unchanged_by_probe=true`.
- `captured.status=NO_UI_ROW_CAPTURE_YET`, `rows=0`, `sources=[]`, `samples=[]`. **Это нормально сразу после установки**; сбор ещё не запускался, gameplay PASS нельзя утверждать.
- Предыдущие `62_V124_ONE_RUN_BOT.json`, `60_V121...`, `61_V122...` сохранены от V125 и не являются новой проверкой V128: `updater_version=125`, stage_count 14, hold_count 9. Эти HOLD не отменяют **успешный V126 install**.

## Ровно следующий пользовательский шаг
**НЕ повторять пункт 2, НЕ запускать снова полный аудит 1.**
1. Закрыть игру, InfinityLoader, если открыты.
2. Запустить единственный `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`, выбрать **4 — play**. Это вызывает `capture` и запускает `InfinityLoader.exe` с перенаправлением консоли.
3. Загрузить тестовый сейв, выполнить несколько попаданий и промахов (достаточно меча и лука), закрыть игру полностью, чтобы сбор завершился.
4. Прислать единственный `C:\Users\Drevo\Documents\BG_EET_RU\SEND_TO_CHATGPT_BG_EET_RU.zip`, проверить обновлённый `63_V126_VISIBLE_ROW_OBSERVER.json`: режим capture, status, `captured.rows`, sources и сообщения.
5. Если игра не стартует, UI изменился, `SAFE_STOP`, зависание, — прекратить тест, не форсировать; пункт 3 — exact UI rollback с separate typed approval после закрытия игры. Не выполнять rollback автоматически без необходимости.

UI helper пишет ограниченные метки `BG_EET_RU_V126_ROW` через Lua `print`; реальная маршрутизация в stdout InfinityLoader **пока не доказана**. Даже успешный UI row capture НЕ доказывает native CMessage → конкретная атака/промах → row; не приписывать оружие по соседству. BGXAI и BG Voice RU сохранять нетронутыми.
