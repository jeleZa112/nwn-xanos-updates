# Roblox V3.7.2 — живой лог 09.11.2026, 21:52

Из AUTOPILOT_LOG(7).txt: файл начинается `ROBLOX AUTOPILOT V3.7.0`, не 3.7.1. Foreground SendInput подтверждён, SPAWN_MOTION MOTION 7.87; READY x≈0.39 → NAV_VISUAL_FALLBACK W/A, MOTION 5.19/17.42. В 21:52:50 появился BUSY_SIGN_NEEDS_CONFIRMATION, после двух кадров `PAD_RESELECT TRACKED_PAD_BUSY_OR_COUNTDOWN` (busy=1/2). Затем были только COUNTDOWN_SIGN и CREATING_SIGN, но поиск оборвался `READY_SIGN_NOT_STABLE_12S` в 21:53:03, матча нет.

Причина: после PAD_RESELECT стадия LOBBY получала 12-секундный срок ожидания для первоначального поиска свободной площадки, хотя она только что стала занятой и могла освободиться. Исправление V3.7.2: отдельный 30-секундный таймер повторного поиска после перевыбора; ждать появления подтверждённой READY, не двигаться к BUSY; при истечении остановиться `NO_FREE_PAD_AFTER_30S_RESELECT`. Проверка HWND, F10, бюджет перемещений, BUSY veto и отсутствие повторного PostMessage сохранены. Пауза фокуса не расходует новый таймер.

Статус: код опубликован, реальные тесты V3.7.2 не выполнялись. Не требовать видео. Запуск прежний ROBLOX_UPDATE.cmd → 15 → YES, Roblox foreground. Если повторяется сбой, нужен только AUTOPILOT_LOG.txt. Нельзя считать создание матча подтверждённым.
