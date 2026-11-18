"""
Unit tests for ACE (Alignment-based Consensus Estimator) Code Aligner.
"""

import unittest
from core.reconstruction.ace_aligner import ACEAligner, LineObservation, DocumentLine


class ACEAlignerTests(unittest.TestCase):
    def setUp(self):
        self.aligner = ACEAligner(min_sim=0.6, default_indent_size=4)

    def test_identical_frames_alignment(self):
        """Identical frames across time should align perfectly without duplicate lines."""
        lines = [
            "public class PlayerController : MonoBehaviour",
            "{",
            "    public float speed = 5.0f;",
            "    void Update()",
            "    {",
            "        Move();",
            "    }",
            "}"
        ]

        self.aligner.add_frame(lines, timestamp=1.0)
        self.aligner.add_frame(lines, timestamp=2.0)
        self.aligner.add_frame(lines, timestamp=3.0)

        doc_lines = self.aligner.get_document_lines()
        self.assertEqual(len(lines), len(doc_lines))
        self.assertEqual(lines, doc_lines)

        # Agreement across all lines should be 1.0
        for doc_line in self.aligner.document:
            self.assertEqual(3, len(doc_line.observations))
            self.assertAlmostEqual(1.0, doc_line.agreement, places=2)

    def test_vertical_scrolling_downward(self):
        """
        Scrolling down causes top lines to disappear and bottom lines to appear.
        ACE DP aligner should skip top lines cheaply and append new lines without duplication.
        """
        # Document lines 1 through 10
        frame1 = [
            "using UnityEngine;",
            "using System.Collections;",
            "public class Weapon : MonoBehaviour",
            "{",
            "    public int damage = 20;",
            "    public float fireRate = 0.5f;",
            "    private float nextFire = 0.0f;"
        ]

        # User scrolled down: lines 1-2 disappeared from view, new lines 8-10 appeared
        frame2 = [
            "public class Weapon : MonoBehaviour",
            "{",
            "    public int damage = 20;",
            "    public float fireRate = 0.5f;",
            "    private float nextFire = 0.0f;",
            "    void Shoot()",
            "    {",
            "        RaycastHit hit;",
            "    }"
        ]

        self.aligner.add_frame(frame1, timestamp=1.0)
        self.aligner.add_frame(frame2, timestamp=2.5)

        doc_lines = self.aligner.get_document_lines()

        # Should contain all lines from frame1 plus the newly scrolled-in lines from frame2
        expected = [
            "using UnityEngine;",
            "using System.Collections;",
            "public class Weapon : MonoBehaviour",
            "{",
            "    public int damage = 20;",
            "    public float fireRate = 0.5f;",
            "    private float nextFire = 0.0f;",
            "    void Shoot()",
            "    {",
            "        RaycastHit hit;",
            "    }"
        ]
        self.assertEqual(expected, doc_lines)

    def test_vertical_scrolling_upward(self):
        """
        Scrolling upward causes bottom lines to disappear and top lines to be revealed.
        ACE should prepend newly visible top lines properly.
        """
        frame1 = [
            "    void Start()",
            "    {",
            "        InitHealth();",
            "    }"
        ]

        frame2 = [
            "public class Enemy : MonoBehaviour",
            "{",
            "    public int maxHealth = 100;",
            "    void Start()",
            "    {",
            "        InitHealth();",
            "    }"
        ]

        self.aligner.add_frame(frame1, timestamp=1.0)
        self.aligner.add_frame(frame2, timestamp=2.0)

        doc_lines = self.aligner.get_document_lines()
        self.assertEqual("public class Enemy : MonoBehaviour", doc_lines[0])
        self.assertEqual("{", doc_lines[1])
        self.assertEqual("    public int maxHealth = 100;", doc_lines[2])
        self.assertEqual("    void Start()", doc_lines[3])

    def test_live_typing_progressive_evolution(self):
        """
        As the instructor types code, incomplete lines are updated to final form
        thanks to recency and confidence weighting.
        """
        # Frame 1: typing begins
        f1 = [
            "public class MathHelper",
            "{",
            "    public int Calculate("
        ]
        # Frame 2: arguments typed
        f2 = [
            "public class MathHelper",
            "{",
            "    public int Calculate(int a, int b)"
        ]
        # Frame 3: body typed
        f3 = [
            "public class MathHelper",
            "{",
            "    public int Calculate(int a, int b)",
            "    {",
            "        return a + b;",
            "    }",
            "}"
        ]

        self.aligner.add_frame(f1, timestamp=1.0)
        self.aligner.add_frame(f2, timestamp=3.0)
        self.aligner.add_frame(f3, timestamp=6.0)

        doc_lines = self.aligner.get_document_lines()
        # The method declaration line must be the completed line, not the partial prefix
        self.assertIn("    public int Calculate(int a, int b)", doc_lines)
        self.assertNotIn("    public int Calculate(", doc_lines)
        self.assertIn("        return a + b;", doc_lines)

    def test_middle_line_insertion(self):
        """Inserting a line between existing lines in a subsequent frame."""
        f1 = [
            "int x = 1;",
            "int z = 3;"
        ]
        f2 = [
            "int x = 1;",
            "int y = 2;",
            "int z = 3;"
        ]

        self.aligner.add_frame(f1, timestamp=1.0)
        self.aligner.add_frame(f2, timestamp=2.0)

        doc_lines = self.aligner.get_document_lines()
        self.assertEqual(["int x = 1;", "int y = 2;", "int z = 3;"], doc_lines)

    def test_calculate_indentation(self):
        """Accurate computation of leading whitespace indentation."""
        self.assertEqual(0, ACEAligner.calculate_indentation("public void Foo()"))
        self.assertEqual(4, ACEAligner.calculate_indentation("    int x = 1;"))
        self.assertEqual(8, ACEAligner.calculate_indentation("        return x;"))
        # Tab converted to 4 spaces
        self.assertEqual(4, ACEAligner.calculate_indentation("\tint x = 1;", tab_size=4))
        self.assertEqual(8, ACEAligner.calculate_indentation("\t\tint x = 1;", tab_size=4))

    def test_indentation_snapping_and_preservation(self):
        """OCR jitter in leading spaces (e.g. 3 spaces or 5 spaces) snaps to 4."""
        # 3 spaces OCR jitter
        f1 = ["   int x = 10;"]
        # 4 spaces
        f2 = ["    int x = 10;"]
        # 5 spaces OCR jitter
        f3 = ["     int x = 10;"]

        self.aligner.add_frame(f1, timestamp=1.0)
        self.aligner.add_frame(f2, timestamp=2.0)
        self.aligner.add_frame(f3, timestamp=3.0)

        doc_lines = self.aligner.get_document_lines()
        self.assertEqual(1, len(doc_lines))
        # Snapped to standard 4 spaces
        self.assertEqual("    int x = 10;", doc_lines[0])

    def test_syntactic_indentation_reconstruction(self):
        """When OCR strips all leading whitespace, syntax structure restores indentation."""
        flattened = [
            "public class Player",
            "{",
            "void Move()",
            "{",
            "if (canMove)",
            "{",
            "transform.Translate(Vector3.forward);",
            "}",
            "}",
            "}"
        ]

        reconstructed = self.aligner.reconstruct_syntactic_indentation(flattened, indent_size=4)
        self.assertEqual("public class Player", reconstructed[0])
        self.assertEqual("{", reconstructed[1])
        self.assertEqual("    void Move()", reconstructed[2])
        self.assertEqual("    {", reconstructed[3])
        self.assertEqual("        if (canMove)", reconstructed[4])
        self.assertEqual("        {", reconstructed[5])
        self.assertEqual("            transform.Translate(Vector3.forward);", reconstructed[6])
        self.assertEqual("        }", reconstructed[7])
        self.assertEqual("    }", reconstructed[8])
        self.assertEqual("}", reconstructed[9])

    def test_per_character_majority_voting(self):
        """Minor OCR typos across frames resolved by character-level majority vote."""
        # Frame 1 has typo: 'l' instead of 'i'
        f1 = [{"text": "public class MonoBehaviour", "conf": 0.7, "t": 1.0}]
        # Frame 2 and 3 have correct spelling
        f2 = [{"text": "public class MonoBehaviour", "conf": 0.95, "t": 2.0}]
        f3 = [{"text": "public class MonoBehaviour", "conf": 0.95, "t": 3.0}]

        self.aligner.add_frame(f1)
        self.aligner.add_frame(f2)
        self.aligner.add_frame(f3)

        doc_lines = self.aligner.get_document_lines()
        self.assertEqual("public class MonoBehaviour", doc_lines[0])

    def test_uncertainty_report(self):
        """Report captures low confidence or single observation lines."""
        f1 = [
            {"text": "int confirmed = 1;", "conf": 0.95, "t": 1.0},
            {"text": "int lowConf = 2;", "conf": 0.30, "t": 1.0}
        ]
        f2 = [
            {"text": "int confirmed = 1;", "conf": 0.95, "t": 2.0}
        ]

        self.aligner.add_frame(f1)
        self.aligner.add_frame(f2)

        report = self.aligner.get_uncertainty_report(min_agreement=0.90, min_mean_conf=0.60)
        self.assertGreaterEqual(len(report), 1)
        reported_texts = [r["chosen_text"] for r in report]
        self.assertIn("int lowConf = 2;", reported_texts)

    def test_line_merger_ace_integration(self):
        """LineMerger.merge_ace properly invokes ACEAligner."""
        from core.reconstruction.line_merger import LineMerger
        merger = LineMerger()
        f1 = ["int a = 1;", "int b = 2;"]
        f2 = ["int b = 2;", "int c = 3;"]
        merged = merger.merge_ace([f1, f2], timestamps=[1.0, 2.0])
        self.assertEqual(["int a = 1;", "int b = 2;", "int c = 3;"], merged)


if __name__ == "__main__":
    unittest.main()
