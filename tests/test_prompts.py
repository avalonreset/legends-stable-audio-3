import unittest

from legends_sa3.cli import build_parser
from legends_sa3.prompts import (
    NEGATIVE_PROMPT_INSTRUMENTAL,
    build_prompt,
    extract_bpm,
    list_presets,
    slugify_style,
)


class PromptTests(unittest.TestCase):
    def test_trip_hop_trance_preset_is_available(self):
        self.assertIn("trip-hop-trance", list_presets())

    def test_trip_hop_trance_preset_avoids_chill_positioning(self):
        prompt, bpm = build_prompt("trip-hop-trance", 1)

        self.assertGreaterEqual(bpm, 96)
        self.assertIn("trip hop trance", prompt)
        self.assertIn("breakbeat", prompt)
        self.assertNotIn("chill", prompt.lower())

    def test_freeform_style_does_not_pull_recipe_language(self):
        prompt, bpm = build_prompt(None, 1, style="trance hip hop jazz, smoky saxophone")

        self.assertEqual(bpm, 84)
        self.assertEqual(
            prompt,
            "TrackType: Music, VocalType: Instrumental, trance hip hop jazz, "
            "smoky saxophone, 84 BPM",
        )
        self.assertNotIn("lo-fi", prompt.lower())
        self.assertNotIn("trip hop trance", prompt.lower())

    def test_freeform_style_respects_explicit_bpm(self):
        prompt, bpm = build_prompt(None, 2, style="industrial jazz breaks at 112 BPM")

        self.assertEqual(bpm, 112)
        self.assertEqual(
            prompt,
            "TrackType: Music, VocalType: Instrumental, industrial jazz breaks at 112 BPM",
        )

    def test_free_time_prompt_can_omit_automatic_bpm(self):
        prompt, bpm = build_prompt(
            None,
            1,
            style="free-time glacial drone, slowly shifting bowed metal",
            omit_bpm=True,
        )

        self.assertIsNone(bpm)
        self.assertNotIn("BPM", prompt)

    def test_sfx_uses_current_tag_and_never_adds_music_or_bpm(self):
        prompt, bpm = build_prompt(
            None,
            1,
            style="TrackType: Sound Effect, one ceramic chime, sharp attack, short decay",
        )

        self.assertIsNone(bpm)
        self.assertTrue(prompt.startswith("TrackType: SFX"))
        self.assertNotIn("TrackType: Music", prompt)
        self.assertNotIn("BPM", prompt)

    def test_freeform_song_prompts_do_not_append_background_utility_language(self):
        for index in range(1, 7):
            prompt, _ = build_prompt(None, index, style="dark electro rock, live drums, baritone guitar")
            lowered = prompt.lower()
            self.assertNotIn("background-ready", lowered)
            self.assertNotIn("non-distracting", lowered)

    def test_freeform_prompt_adds_recommended_music_tags(self):
        instrumental_prompt, _ = build_prompt(None, 1, style="ambient techno instrumental", instrumental=True)
        vocal_prompt, _ = build_prompt(None, 1, style="ghost choir over ambient techno", instrumental=False)

        self.assertIn("TrackType: Music", instrumental_prompt)
        self.assertIn("VocalType: Instrumental", instrumental_prompt)
        self.assertIn("TrackType: Music", vocal_prompt)
        self.assertNotIn("VocalType: Instrumental", vocal_prompt)

    def test_user_supplied_music_tags_are_not_duplicated(self):
        prompt, _ = build_prompt(
            None,
            1,
            style="TrackType: Music, VocalType: Instrumental, Detroit techno, 130 BPM",
        )

        self.assertEqual(prompt.count("TrackType: Music"), 1)
        self.assertEqual(prompt.count("VocalType: Instrumental"), 1)

    def test_instrumental_negative_avoids_vocals_without_invoking_lyric_workflow(self):
        lowered = NEGATIVE_PROMPT_INSTRUMENTAL.lower()
        self.assertIn("vocals", lowered)
        self.assertIn("singing", lowered)
        self.assertIn("spoken words", lowered)
        self.assertNotIn("lyrics", lowered)

    def test_slugify_style_is_filename_safe(self):
        self.assertEqual(slugify_style("Trance / Hip Hop + Jazz!"), "trance-hip-hop-jazz")

    def test_extract_bpm(self):
        self.assertEqual(extract_bpm("dark garage 126 BPM with swung drums"), 126)
        self.assertIsNone(extract_bpm("dark garage with swung drums"))

    def test_generate_accepts_style_first_cli(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--model-dir",
                "models/stable-audio-3-medium",
                "--style",
                "trance hip hop jazz",
                "--minutes",
                "1",
                "--output",
                "out",
            ]
        )

        self.assertEqual(args.style, "trance hip hop jazz")
        self.assertIsNone(args.recipe)

    def test_prompt_and_generate_accept_omit_bpm(self):
        parser = build_parser()
        prompt_args = parser.parse_args(
            ["prompt", "--style", "free-time drone", "--omit-bpm"]
        )
        generate_args = parser.parse_args(
            [
                "generate",
                "--model-dir",
                "models/stable-audio-3-medium",
                "--style",
                "free-time drone",
                "--omit-bpm",
                "--minutes",
                "1",
                "--output",
                "out",
            ]
        )

        self.assertTrue(prompt_args.omit_bpm)
        self.assertTrue(generate_args.omit_bpm)

    def test_post_trained_medium_defaults_to_eight_steps_and_cfg_one(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--model-dir",
                "models/stable-audio-3-medium",
                "--style",
                "ambient techno",
                "--minutes",
                "1",
                "--output",
                "out",
            ]
        )

        self.assertEqual(args.steps, 8)
        self.assertEqual(args.cfg_scale, 1.0)

    def test_genre_alias_maps_to_recipe(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--model-dir",
                "models/stable-audio-3-medium",
                "--genre",
                "trip-hop-trance",
                "--minutes",
                "1",
                "--output",
                "out",
            ]
        )

        self.assertEqual(args.recipe, "trip-hop-trance")

    def test_generate_accepts_native_lora_args(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--model-dir",
                "models/stable-audio-3-medium",
                "--style",
                "industrial trance",
                "--minutes",
                "1",
                "--output",
                "out",
                "--lora-ckpt-path",
                "adapters/eisbach/model.safetensors",
                "--lora-ckpt-path",
                "adapters/other/model.safetensors",
                "--lora-strength",
                "0.75",
            ]
        )

        self.assertEqual(
            args.lora_ckpt_paths,
            ["adapters/eisbach/model.safetensors", "adapters/other/model.safetensors"],
        )
        self.assertEqual(args.lora_strength, 0.75)

    def test_lora_studio_import_cli(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "lora-studio",
                "import",
                "state/runs/my-style/5000.safetensors",
                "--name",
                "my-style",
                "--source-run",
                "my-style",
            ]
        )

        self.assertEqual(args.source, "state/runs/my-style/5000.safetensors")
        self.assertEqual(args.name, "my-style")
        self.assertEqual(args.source_run, "my-style")

    def test_lora_studio_install_is_clone_only_by_default(self):
        parser = build_parser()
        args = parser.parse_args(["lora-studio", "install"])

        self.assertFalse(args.run_underfit_install)
        self.assertFalse(args.with_setup)
        self.assertEqual(args.backend, "sa3")


if __name__ == "__main__":
    unittest.main()
