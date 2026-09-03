import unittest
from unittest.mock import patch

from legends_sa3.doctor import run_doctor


class DoctorTests(unittest.TestCase):
    def test_doctor_reports_platform_and_cuda_backend(self):
        with patch(
            "legends_sa3.doctor.detect_torch",
            return_value=(True, True, False, "Test GPU", 24.0),
        ), patch("legends_sa3.doctor.platform.system", return_value="Windows"), patch(
            "legends_sa3.doctor.platform.machine", return_value="AMD64"
        ), patch("legends_sa3.doctor.platform.python_version", return_value="3.12.1"), patch(
            "legends_sa3.doctor.shutil.which", return_value="tool"
        ):
            report = run_doctor()
        self.assertEqual(report.platform, "windows")
        self.assertEqual(report.architecture, "amd64")
        self.assertEqual(report.local_medium_backend, "cuda")
        self.assertTrue(report.ffmpeg)

    def test_doctor_reports_mps_without_claiming_mps_generation(self):
        with patch(
            "legends_sa3.doctor.detect_torch",
            return_value=(True, False, True, None, None),
        ), patch("legends_sa3.doctor.platform.system", return_value="Darwin"), patch(
            "legends_sa3.doctor.platform.machine", return_value="arm64"
        ), patch("legends_sa3.doctor.platform.python_version", return_value="3.12.1"), patch(
            "legends_sa3.doctor.shutil.which", return_value=None
        ):
            report = run_doctor()
        self.assertEqual(report.platform, "darwin")
        self.assertTrue(report.mps)
        self.assertEqual(report.local_medium_backend, "cpu")


if __name__ == "__main__":
    unittest.main()
