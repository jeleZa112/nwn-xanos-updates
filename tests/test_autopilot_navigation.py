"""Offline navigation-policy checks: never imports Windows / Roblox code."""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "roblox_monitor.py"
MODULE = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
NAMES = {"AutoPilotNavigationGoal", "AutoPilotPadReselect",
         "AutoPilotPolicy", "AutoPilotVisualReadyLock"}
classes = [node for node in MODULE.body
           if isinstance(node, ast.ClassDef) and node.name in NAMES]
assert {node.name for node in classes} == NAMES, "Missing navigation class"
scope = {}
exec(compile(ast.fix_missing_locations(ast.Module(
    body=classes, type_ignores=[])), str(SOURCE), "exec"), scope)

Goal = scope["AutoPilotNavigationGoal"]
Reselect = scope["AutoPilotPadReselect"]
Policy = scope["AutoPilotPolicy"]
Visual = scope["AutoPilotVisualReadyLock"]


def sign(kind, x, confidence=0.9):
    return {"status": kind, "center_x": x, "confidence": confidence}


class NavigationTests(unittest.TestCase):
    def test_one_identity_across_text_and_flow(self):
        g = Goal()
        self.assertTrue(g.lock(.39, 0))
        self.assertAlmostEqual(g.track(.385, .5, [], "FLOW", .89), .385)
        self.assertAlmostEqual(g.track(.405, 1., [], "READY"), .405)
        self.assertEqual(g.source, "READY")

    def test_no_jump_to_distant_ready(self):
        g = Goal()
        g.lock(.39, 0)
        self.assertIsNone(g.track(.75, 1, [], "READY"))
        self.assertAlmostEqual(g.x, .39)

    def test_low_quality_flow_does_not_move_target(self):
        g = Goal()
        g.lock(.39, 0)
        self.assertIsNone(g.track(.40, 1, [], "FLOW", .60))
        self.assertAlmostEqual(g.x, .39)

    def test_busy_near_old_or_new_target_blocks_both_sources(self):
        g = Goal()
        g.lock(.39, 0)
        busy = [sign("CREATING_SIGN", .40, .9)]
        self.assertIsNone(g.track(.40, 1, busy, "FLOW", .99))
        self.assertIsNone(g.track(.40, 1, busy, "READY"))
        self.assertAlmostEqual(g.x, .39)

    def test_a_distant_busy_does_not_block(self):
        g = Goal()
        g.lock(.39, 0)
        self.assertAlmostEqual(
            g.track(.40, 1, [sign("COUNTDOWN_SIGN", .8)], "FLOW", .91), .4)

    def test_busy_requires_confirmation(self):
        r = Reselect()
        signs = [sign("COUNTDOWN_SIGN", .39)]
        self.assertEqual(r.check(signs, .39, 0)[0], "WAIT")
        self.assertEqual(r.check(signs, .39, .5)[0], "RESELECT")

    def test_missing_label_is_not_immediately_busy(self):
        r = Reselect()
        self.assertEqual(r.check([], .39, 0)[0], "WAIT")
        self.assertEqual(r.check([], .39, 5.5)[0], "WAIT")
        # Grace requires both elapsed time and sufficient sampled misses.
        result = None
        for i in range(10):
            result = r.check([], .39, 6+i*.5)[0]
            if result == "RESELECT": break
        self.assertEqual(result, "RESELECT")

    def test_resel_exclusion_has_separate_budget(self):
        r = Reselect()
        self.assertTrue(r.begin_reselection(.39, 5., "TRACKED_PAD_BUSY_OR_COUNTDOWN"))
        self.assertEqual(r.reselections, 1)
        self.assertTrue(r.begin_reselection(.39, 6., "READY_UNSEEN_FOR_5S"))
        self.assertEqual(r.reselections, 1)
        self.assertEqual(r.lost_reacquisitions, 1)

    def test_short_flow_pulse_accounts_actual_duration(self):
        p = Policy()
        p.reset_lobby(0.)
        action, key, duration = p.lobby_movement(.39, 1., duration_override=.12)
        self.assertEqual(action, "KEY")
        self.assertEqual(key, "W")
        self.assertAlmostEqual(duration, .12)
        self.assertAlmostEqual(p.move_seconds, .12)

    def test_flow_pulse_budget_is_not_reset_by_new_seed(self):
        v = Visual()
        self.assertEqual(v.fallback_pulses, 0)
        for i in range(v.MAX_FALLBACK_PULSES):
            self.assertTrue(v.used_fallback_pulse())
        self.assertFalse(v.used_fallback_pulse())
        self.assertEqual(v.fallback_pulses, 6)


if __name__ == "__main__":
    unittest.main()
