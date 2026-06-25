import tempfile
import unittest
from pathlib import Path

from sts2_ai_stream.steam import inspect_appmanifest


class SteamManifestTest(unittest.TestCase):
    def test_extracts_manifest_values(self):
        text = '''
"AppState"
{
    "appid"        "2868840"
    "name"         "Slay the Spire 2"
    "buildid"      "12345"
    "UserConfig"
    {
        "betakey"  "public-beta"
    }
}
'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "appmanifest_2868840.acf"
            path.write_text(text, encoding="utf-8")
            result = inspect_appmanifest(path)
        self.assertTrue(result["exists"])
        self.assertEqual(result["appid"], "2868840")
        self.assertEqual(result["buildid"], "12345")
        self.assertEqual(result["betakey"], "public-beta")


if __name__ == "__main__":
    unittest.main()

