"""R3 new read-only entry tests; does not use Windows, WeiDU or game files."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import BGXW2_OBSERVER_GUARDED as m
import BGXAI_WEAPON_NATIVE_ITM_R3_RO as r3

class R3Menu(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'not-a-game'
        self.root.mkdir()
    def test_option_6_readonly_runs_only_if_r2_is_installed(self):
        ret={'status':'ITM_NATIVE_ALL_ITEMS_RAW_READ','game_modified':False,
             'weapon_switch_authorized':False}
        with mock.patch('builtins.input',return_value='6'),\
             mock.patch.object(m,'check_processes') as guard,\
             mock.patch.object(m,'status',return_value={'status':'BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT'}),\
             mock.patch.object(r3,'native_run',return_value=ret) as native,\
             mock.patch.object(m,'report') as report:
            self.assertEqual(m.menu(self.root),0)
            guard.assert_called_once();native.assert_called_once_with(self.root)
            report.assert_called_once_with(ret)
    def test_option_6_refuses_r2_missing_before_reading_game(self):
        with mock.patch('builtins.input',return_value='6'),\
             mock.patch.object(m,'check_processes'),\
             mock.patch.object(m,'status',return_value={'status':'BGXW2_NOT_INSTALLED'}),\
             mock.patch.object(r3,'native_run') as native,\
             mock.patch.object(m,'report'):
            self.assertEqual(m.menu(self.root),2)
            native.assert_not_called()
    def test_option_6_respects_process_guard(self):
        with mock.patch('builtins.input',return_value='6'),\
             mock.patch.object(m,'check_processes',side_effect=ValueError('GAME_RUNNING')) as guard,\
             mock.patch.object(m,'status') as status,\
             mock.patch.object(r3,'native_run') as native,\
             mock.patch.object(m,'report'):
            self.assertEqual(m.menu(self.root),2)
            guard.assert_called_once();status.assert_not_called();native.assert_not_called()

if __name__=='__main__':unittest.main()
