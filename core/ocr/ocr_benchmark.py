"""
CodeVision Phase 4: Code OCR Benchmark & Accuracy Evaluator.
Computes Character Error Rate (CER), Word Error Rate (WER), and Syntax Preservation.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List
from core.ocr.code_token_normalizer import CodeTokenNormalizer, compute_cer, compute_wer


@dataclass
class BenchmarkItem:
    name: str
    language: str
    ground_truth: str
    raw_ocr: str
    raw_cer: float
    raw_wer: float
    normalized_text: str
    improved_cer: float
    improved_wer: float
    cer_improvement_pct: float


@dataclass
class BenchmarkSuiteResult:
    total_samples: int
    mean_raw_cer: float
    mean_improved_cer: float
    mean_raw_wer: float
    mean_improved_wer: float
    overall_cer_reduction_pct: float
    items: List[BenchmarkItem]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["items"] = [asdict(item) for item in self.items]
        return data


class CodeOCRBenchmark:
    def __init__(self):
        self.normalizer = CodeTokenNormalizer(strip_gutters=True)

    def evaluate_sample(self, name: str, language: str, ground_truth: str, raw_ocr: str) -> BenchmarkItem:
        raw_cer = compute_cer(ground_truth, raw_ocr)
        raw_wer = compute_wer(ground_truth, raw_ocr)

        norm_res = self.normalizer.normalize(raw_ocr, language_hint=language)
        improved_cer = compute_cer(ground_truth, norm_res.cleaned_code)
        improved_wer = compute_wer(ground_truth, norm_res.cleaned_code)

        cer_improvement = ((raw_cer - improved_cer) / raw_cer * 100.0) if raw_cer > 0 else 0.0

        return BenchmarkItem(
            name=name,
            language=language,
            ground_truth=ground_truth,
            raw_ocr=raw_ocr,
            raw_cer=round(raw_cer, 4),
            raw_wer=round(raw_wer, 4),
            normalized_text=norm_res.cleaned_code,
            improved_cer=round(improved_cer, 4),
            improved_wer=round(improved_wer, 4),
            cer_improvement_pct=round(cer_improvement, 2),
        )

    def run_standard_suite(self) -> BenchmarkSuiteResult:
        """Runs the standard evaluation suite covering Flutter, Python, C#, TypeScript, and C++."""
        samples = [
            (
                "Flutter Widget Build",
                "Dart",
                "@override\nWidget build(BuildContext context) => Scaffold();",
                "1 | @overrlde\n2 | Widqet build(Buildcontext context) = > Scaffold();"
            ),
            (
                "Python Async Function",
                "Python",
                "async def fetch_user(user_id: int):\n    return self.db.query(user_id)",
                "01: asyne def fetch_user(user_id: int):\n02:     retum se1f.db.query(user_id)"
            ),
            (
                "C# Unity MonoBehaviour",
                "C#",
                "using UnityEngine;\npublic class GameManager : MonoBehaviour {\n    void Start() {}\n}",
                "using UnityEnqine;\npubllc class GameManager : MonoBehavlour {\n    vold Start() {}\n}"
            ),
            (
                "TypeScript Arrow Logic",
                "TypeScript",
                "const calculate = (a: number, b: number) => a !== b && a <= 10;",
                "constt calculate = (a: number, b: number) = > a ! = b & & a < = 10;"
            ),
            (
                "C++ Scope Resolution",
                "C++",
                "std::cout << obj->getName() << std::endl;",
                "std : : cout << obj - > getName() << std : : endl;"
            )
        ]

        items = []
        for name, lang, gt, raw in samples:
            item = self.evaluate_sample(name, lang, gt, raw)
            items.append(item)

        m_raw_cer = sum(it.raw_cer for it in items) / len(items)
        m_imp_cer = sum(it.improved_cer for it in items) / len(items)
        m_raw_wer = sum(it.raw_wer for it in items) / len(items)
        m_imp_wer = sum(it.improved_wer for it in items) / len(items)
        cer_reduc = ((m_raw_cer - m_imp_cer) / m_raw_cer * 100.0) if m_raw_cer > 0 else 0.0

        return BenchmarkSuiteResult(
            total_samples=len(items),
            mean_raw_cer=round(m_raw_cer, 4),
            mean_improved_cer=round(m_imp_cer, 4),
            mean_raw_wer=round(m_raw_wer, 4),
            mean_improved_wer=round(m_imp_wer, 4),
            overall_cer_reduction_pct=round(cer_reduc, 2),
            items=items
        )


if __name__ == "__main__":
    benchmark = CodeOCRBenchmark()
    res = benchmark.run_standard_suite()
    print(f"Total evaluated: {res.total_samples}")
    print(f"Mean CER: {res.mean_raw_cer*100:.1f}% -> {res.mean_improved_cer*100:.1f}% (Reduction: {res.overall_cer_reduction_pct:.1f}%)")
    print(f"Mean WER: {res.mean_raw_wer*100:.1f}% -> {res.mean_improved_wer*100:.1f}%")
