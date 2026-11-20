"""
Unit tests for core.reconstruction.script_categorizer (Phase 5).
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from core.reconstruction.script_categorizer import ScriptCategorizer


class TestScriptCategorizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_category_heuristics(self):
        self.assertEqual(ScriptCategorizer.get_category("PlayerController"), "Controllers")
        self.assertEqual(ScriptCategorizer.get_category("UserModel"), "Models")
        self.assertEqual(ScriptCategorizer.get_category("AuthService"), "Services")
        self.assertEqual(ScriptCategorizer.get_category("ResponsiveDesignScreen"), "UI")
        self.assertEqual(ScriptCategorizer.get_category("StringHelper"), "Utils")
        self.assertEqual(ScriptCategorizer.get_category("GameConfig"), "Config")

    def test_flutter_export_scaffolding(self):
        scripts = {
            "ResponsiveDesignScreen": "import 'package:flutter/material.dart';\nclass ResponsiveDesignScreen extends StatelessWidget {}",
            "CustomButtonWidget": "class CustomButtonWidget extends StatelessWidget {}"
        }

        written = ScriptCategorizer.organize_export(scripts, self.temp_dir, extension=".dart")
        base = self.temp_dir / "ProjectScripts"

        self.assertTrue((base / "pubspec.yaml").exists())
        self.assertTrue((base / "lib" / "main.dart").exists())
        self.assertTrue((base / "lib" / "screens" / "ResponsiveDesignScreen.dart").exists())
        self.assertTrue((base / "lib" / "widgets" / "CustomButtonWidget.dart").exists())

    def test_csharp_export_scaffolding(self):
        scripts = {
            "GameManager": "using UnityEngine;\npublic class GameManager : MonoBehaviour {}",
            "PlayerMovement": "public class PlayerMovement : MonoBehaviour {}"
        }

        written = ScriptCategorizer.organize_export(scripts, self.temp_dir, extension=".cs")
        base = self.temp_dir / "ProjectScripts"

        self.assertTrue((base / "ReconstructedApp.csproj").exists())
        self.assertTrue((base / "Assets" / "Scripts" / "Services" / "GameManager.cs").exists())
        self.assertTrue((base / "Assets" / "Scripts" / "Player" / "PlayerMovement.cs").exists())


if __name__ == "__main__":
    unittest.main()
