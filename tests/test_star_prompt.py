import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from core import star_prompt
from core.star_prompt import (
    CHOICE_LATER,
    CHOICE_NEVER,
    CHOICE_STAR,
    ISSUES_URL,
    REMIND_AFTER_LAUNCHES,
    REPO_URL,
    STATUS_DECLINED,
    STATUS_PENDING,
    STATUS_STARRED,
    StarPrompt,
    open_url,
    run_star_prompt,
)


class StarPromptTestCase(unittest.TestCase):
    """Gives every test its own state file in a temporary folder."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "star_prompt.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def new_prompt(self) -> StarPrompt:
        return StarPrompt(self.state_file)

    def write_state(self, text: str) -> None:
        self.state_file.write_text(text, encoding="utf-8")


class TestStarPromptState(StarPromptTestCase):
    def test_fresh_install_is_not_due_before_the_first_launch(self):
        self.assertFalse(self.new_prompt().is_due())

    def test_first_launch_is_due(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        self.assertTrue(prompt.is_due())

    def test_launch_count_is_saved(self):
        self.new_prompt().register_launch()
        self.new_prompt().register_launch()
        self.assertEqual(self.new_prompt().state["launch_count"], 2)

    def test_star_is_never_asked_again(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        prompt.record_choice(CHOICE_STAR)
        self.assertEqual(prompt.state["status"], STATUS_STARRED)
        for _ in range(50):
            prompt.register_launch()
            self.assertFalse(prompt.is_due())

    def test_never_is_never_asked_again(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        prompt.record_choice(CHOICE_NEVER)
        self.assertEqual(prompt.state["status"], STATUS_DECLINED)
        for _ in range(50):
            prompt.register_launch()
            self.assertFalse(prompt.is_due())

    def test_later_waits_the_configured_number_of_launches(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        prompt.record_choice(CHOICE_LATER)
        self.assertEqual(prompt.state["status"], STATUS_PENDING)
        for _ in range(REMIND_AFTER_LAUNCHES - 1):
            prompt.register_launch()
            self.assertFalse(prompt.is_due())
        prompt.register_launch()
        self.assertTrue(prompt.is_due())

    def test_closing_the_dialog_counts_as_later(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        prompt.record_choice("something unexpected")
        self.assertEqual(prompt.state["status"], STATUS_PENDING)
        self.assertFalse(prompt.is_due())

    def test_answer_survives_a_restart(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        prompt.record_choice(CHOICE_NEVER)
        self.assertEqual(self.new_prompt().state["status"], STATUS_DECLINED)

    def test_state_file_is_valid_json(self):
        prompt = self.new_prompt()
        prompt.register_launch()
        saved = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["launch_count"], 1)
        self.assertEqual(saved["status"], STATUS_PENDING)


class TestStarPromptDamagedState(StarPromptTestCase):
    def test_corrupt_file_falls_back_to_defaults(self):
        self.write_state("{not json")
        prompt = self.new_prompt()
        self.assertEqual(prompt.state, star_prompt.DEFAULT_STATE)

    def test_non_object_file_falls_back_to_defaults(self):
        self.write_state("[1, 2, 3]")
        self.assertEqual(self.new_prompt().state, star_prompt.DEFAULT_STATE)

    def test_wrong_types_are_ignored(self):
        self.write_state(
            json.dumps(
                {
                    "launch_count": "many",
                    "status": "bogus",
                    "next_prompt_at": -4,
                }
            )
        )
        self.assertEqual(self.new_prompt().state, star_prompt.DEFAULT_STATE)

    def test_boolean_is_not_accepted_as_a_count(self):
        self.write_state(json.dumps({"launch_count": True}))
        self.assertEqual(self.new_prompt().state["launch_count"], 0)

    def test_valid_fields_are_kept_when_others_are_damaged(self):
        self.write_state(
            json.dumps({"launch_count": 7, "status": STATUS_STARRED, "next_prompt_at": None})
        )
        state = self.new_prompt().state
        self.assertEqual(state["launch_count"], 7)
        self.assertEqual(state["status"], STATUS_STARRED)
        self.assertEqual(state["next_prompt_at"], 1)

    def test_unknown_keys_are_dropped(self):
        self.write_state(json.dumps({"launch_count": 3, "extra": "x"}))
        self.assertNotIn("extra", self.new_prompt().state)

    def test_save_failure_does_not_raise(self):
        # The parent of the state file is a file, so the folder cannot be made.
        blocker = Path(self.temp_dir) / "blocker"
        blocker.write_text("x", encoding="utf-8")
        prompt = StarPrompt(blocker / "star_prompt.json")
        prompt.register_launch()
        self.assertEqual(prompt.state["launch_count"], 1)

    def test_defaults_are_not_shared_between_instances(self):
        first = self.new_prompt()
        first.state["launch_count"] = 99
        self.assertEqual(star_prompt.DEFAULT_STATE["launch_count"], 0)


class TestRunStarPrompt(StarPromptTestCase):
    def test_asks_on_the_first_launch(self):
        ask = mock.Mock(return_value=CHOICE_LATER)
        result = run_star_prompt(ask, self.new_prompt())
        ask.assert_called_once_with()
        self.assertEqual(result, CHOICE_LATER)

    def test_does_not_ask_on_the_second_launch_after_later(self):
        run_star_prompt(mock.Mock(return_value=CHOICE_LATER), self.new_prompt())
        ask = mock.Mock()
        result = run_star_prompt(ask, self.new_prompt())
        ask.assert_not_called()
        self.assertIsNone(result)

    def test_asks_again_once_the_wait_is_over(self):
        run_star_prompt(mock.Mock(return_value=CHOICE_LATER), self.new_prompt())
        ask = mock.Mock(return_value=CHOICE_NEVER)
        for _ in range(REMIND_AFTER_LAUNCHES - 1):
            self.assertIsNone(run_star_prompt(ask, self.new_prompt()))
        self.assertEqual(run_star_prompt(ask, self.new_prompt()), CHOICE_NEVER)
        ask.assert_called_once_with()

    def test_star_answer_stops_all_later_requests(self):
        run_star_prompt(mock.Mock(return_value=CHOICE_STAR), self.new_prompt())
        ask = mock.Mock()
        for _ in range(REMIND_AFTER_LAUNCHES * 3):
            run_star_prompt(ask, self.new_prompt())
        ask.assert_not_called()

    def test_every_run_counts_a_launch(self):
        ask = mock.Mock(return_value=CHOICE_LATER)
        for _ in range(4):
            run_star_prompt(ask, self.new_prompt())
        self.assertEqual(self.new_prompt().state["launch_count"], 4)

    def test_uses_the_default_state_file_when_none_is_given(self):
        with mock.patch.object(star_prompt, "STATE_FILE", self.state_file):
            run_star_prompt(mock.Mock(return_value=CHOICE_NEVER))
        self.assertTrue(self.state_file.exists())
        self.assertEqual(self.new_prompt().state["status"], STATUS_DECLINED)


class TestLinks(unittest.TestCase):
    def test_repo_url_points_at_the_project(self):
        self.assertTrue(REPO_URL.startswith("https://github.com/r00tmebaby/"))
        self.assertTrue(ISSUES_URL.startswith(REPO_URL))

    def test_open_url_reports_success(self):
        with mock.patch.object(star_prompt.webbrowser, "open", return_value=True) as opened:
            self.assertTrue(open_url(REPO_URL))
        opened.assert_called_once_with(REPO_URL)

    def test_open_url_reports_failure(self):
        with mock.patch.object(star_prompt.webbrowser, "open", return_value=False):
            self.assertFalse(open_url(REPO_URL))

    def test_open_url_never_raises(self):
        with mock.patch.object(star_prompt.webbrowser, "open", side_effect=OSError("no browser")):
            self.assertFalse(open_url(REPO_URL))


if __name__ == "__main__":
    unittest.main()
