"""Check dotenv discovery without loading real credentials or calling APIs."""
import os
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch


class SettingsTests(unittest.TestCase):
    def test_dotenv_discovery_and_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backend = root / "backend"
            app = backend / "app"
            app.mkdir(parents=True)
            config = app / "config.py"
            shutil.copyfile(Path(__file__).resolve().parents[1] / "config.py", config)
            (backend / ".env").write_text("OPENAI_API_KEY=dotenv-test-value\n", encoding="utf-8")
            (root / ".env").write_text("OPENAI_API_KEY=wrong-file\n", encoding="utf-8")

            original_directory = Path.cwd()
            try:
                with patch.dict(os.environ, {}, clear=True):
                    for directory in (root, backend, app):
                        with self.subTest(directory=directory.name):
                            os.chdir(directory)
                            settings = runpy.run_path(str(config))["settings"]
                            self.assertEqual(settings.OPENAI_API_KEY, "dotenv-test-value")

                    os.environ["OPENAI_API_KEY"] = "environment-test-value"
                    settings = runpy.run_path(str(config))["settings"]
                    self.assertEqual(settings.OPENAI_API_KEY, "environment-test-value")
            finally:
                os.chdir(original_directory)


if __name__ == "__main__":
    unittest.main()
