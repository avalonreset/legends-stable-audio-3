import unittest

from legends_sa3.planning import build_mix_plan, recommend_track_seconds


class PlanningTests(unittest.TestCase):
    def test_4090_ten_hour_plan_matches_known_run(self):
        seconds = recommend_track_seconds(24)
        plan = build_mix_plan(hours=10, track_seconds=seconds, crossfade_seconds=12)
        self.assertEqual(seconds, 380)
        self.assertEqual(plan.track_count, 98)
        self.assertEqual(plan.final_seconds, 36076)

    def test_lower_vram_recommendations_are_conservative(self):
        self.assertEqual(recommend_track_seconds(8), 120)
        self.assertEqual(recommend_track_seconds(16), 240)
        self.assertEqual(recommend_track_seconds(None), 180)

    def test_crossfade_must_be_shorter_than_track(self):
        with self.assertRaises(ValueError):
            build_mix_plan(minutes=5, track_seconds=12, crossfade_seconds=12)


if __name__ == "__main__":
    unittest.main()

