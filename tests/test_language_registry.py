import unittest

from languages.builtin import create_default_registry
from languages.models import LanguageProfile
from languages.registry import LanguageRegistry


class LanguageRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = create_default_registry()

    def test_initial_registry_has_fifteen_profiles(self):
        self.assertEqual(15, len(self.registry.profiles))

    def test_detects_unambiguous_extension(self):
        match = self.registry.detect("lesson/main.py")
        self.assertIsNotNone(match)
        self.assertEqual("python", match.profile.language_id)
        self.assertGreaterEqual(match.confidence, 0.9)

    def test_detect_extension_refuses_ambiguous_header(self):
        self.assertIsNone(self.registry.detect_extension("header.h"))

    def test_content_can_disambiguate_header(self):
        match = self.registry.detect("header.h", "#include <iostream>\nstd::cout << 1;")
        self.assertIsNotNone(match)
        self.assertEqual("cpp", match.profile.language_id)

    def test_detects_python_by_content_without_extension(self):
        match = self.registry.detect(source="from pathlib import Path\n\ndef greet(name):\n    return name")
        self.assertIsNotNone(match)
        self.assertEqual("python", match.profile.language_id)

    def test_unknown_content_abstains(self):
        self.assertIsNone(self.registry.detect("notes.txt", "hello there"))

    def test_register_is_case_insensitive_and_extension_normalized(self):
        registry = LanguageRegistry()
        registry.register(LanguageProfile("Example", "Example", ("EX",)))
        self.assertEqual("example", registry.detect("file.ex").profile.language_id)

    def test_duplicate_language_registration_fails(self):
        with self.assertRaises(ValueError):
            self.registry.register(LanguageProfile("PYTHON", "Python", ("py",)))


if __name__ == "__main__":
    unittest.main()
