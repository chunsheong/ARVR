import unittest

from arvr.hud import HUDController, SOPStep


class HUDControllerTest(unittest.TestCase):
    def test_step_progress_advances_only_when_detected(self) -> None:
        hud = HUDController([SOPStep("step 1"), SOPStep("step 2")])

        first = hud.process_frame(frame=object(), step_detected=False)
        self.assertEqual(first.completed_steps, 0)
        self.assertEqual(first.current_step, "step 1")

        second = hud.process_frame(frame=object(), step_detected=True)
        self.assertEqual(second.completed_steps, 1)
        self.assertEqual(second.current_step, "step 2")

    def test_completion_returns_no_current_step(self) -> None:
        hud = HUDController([SOPStep("step 1")])

        done = hud.process_frame(frame=object(), step_detected=True)
        self.assertEqual(done.completed_steps, 1)
        self.assertIsNone(done.current_step)
        self.assertEqual(done.overlay_color, "black")


if __name__ == "__main__":
    unittest.main()
