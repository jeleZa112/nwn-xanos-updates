# Roblox V3.8.1 — разбор AUTOPILOT_LOG(9).txt, 12.11.2026

## Входящий игровой лог
ROBLOX AUTOPILOT V3.8.0, 22:20:50–22:21:47. Foreground SendInput работает: SPAWN_MOTION shift=12.48; затем NAV D x=.696/.658/.618 (подтверждённое движение), NAV W x=.58/.59. В 22:21:07 READY_TEMPORARILY_HIDDEN; в 22:21:12 PAD_RESELECT READY_UNSEEN_FOR_5S, old_x=.59, confirmed_busy=0, visual_reacquire=1/3. В 22:21:14, 22:21:17, 22:21:24, 22:21:29, 22:21:32, 22:21:35, 22:21:39, 22:21:42 детектор неоднократно видел READY_SIGN x=.606 confidence=.621 (frame 1922x1048), но AutoPilotPolicy.ready_sign требовал confidence >=.65. После 30s STOP NO_FREE_PAD_AFTER_30S_RESELECT. Попытки нажать Create нет, матча нет.

## Исправление V3.8.1
Normal initial lobby lock unchanged: READY >=.65, 3 of 6 consecutive/sampled frames; reselect-only permits READY confidence >=.60 with 4 matching samples of 6 and max horizontal spread .055, tolerance to match .045. Existing BUSY veto COUNTDOWN/CREATING remains; one weak detection never causes movement. В AutoPilotVisualReadyLock.seed начальный минимум .60, но лишь после полной стабильной селекции. Для NAV проверки уже выбранного знака порог .60, а AutoPilotNavigationGoal продолжает запрещать скачки на другую площадку и источники низкокачественного FLOW.

## Верификация
GitHub Actions run 43247850013 — success. Добавлены 5 регрессионных тестов: повторные .621 lock, normal-mode rejection, нестабильное положение, BUSY запрет, <.60 отклонение; плюс прежние 13 тестов навигации и синтаксис. Итого 18 тестов. Это только офлайн-проверки и не подтверждает успешное создание матча.

## Дальше
Один обычный запуск ROBLOX_UPDATE.cmd → 15 → YES; Roblox активен. Не просить видео и множественные тесты. Критерий успеха ближайшего этапа — подтверждённое меню создания City / 1 / Hard, затем нажатие Create только после проверки параметров.
