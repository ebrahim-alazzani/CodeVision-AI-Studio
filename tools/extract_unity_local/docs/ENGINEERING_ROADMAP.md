# CodeVision engineering roadmap

## Current baseline

The current extractor samples video with FFmpeg, runs Tesseract per frame,
scores candidate code with C#-specific regular expressions, and reconstructs
C# scripts with `reconstruction/script_builder.py`. `core/models.py` contains
video, frame, OCR, snapshot, script, and report models. The CLI pipeline lives
in `codevision.py`. There is no existing automated test suite in this checkout.
`reconstruct_csharp.py` also imports `FrameMetadata`, which is absent from
`core/models.py`, and uses `re`, `difflib`, `os`, `glob`, and `sys` without
importing them.

## Target pipeline

Video/audio input -> visual scene and editor-region analysis -> OCR observations
with coordinates, timestamps, confidence, and source-frame provenance ->
language identification -> language-specific parsing -> temporal edits and file
history -> reconstructed project tree -> educational review and export.

OCR, language profiles, parsers, temporal reconstruction, and presentation must
remain separate components. Each stage should retain links to the source frame
and its timestamp so a learner can verify uncertain output.

## Phases

1. **Language foundation (implemented in this patch):** add a dependency-free
   profile model and registry, initial profiles for 15 languages, confidence
   and evidence, and tests. Existing C# processing remains unchanged.
2. **Observation model:** represent OCR text, bounding boxes, confidence,
   language candidates, timestamp, and original frame provenance.
3. **Visual/OCR improvements:** detect scene changes and code-editor regions;
   compare OCR engines and keep uncertain text reviewable.
4. **Language intelligence:** add parser adapters and syntax-aware validation
   incrementally, starting with languages represented in real course footage.
5. **Temporal reconstruction:** infer additions, edits, deletions, file names,
   and project structure from ordered observations.
6. **Educational workspace:** timeline, project tree, code editor, confidence
   review, and step-by-step playback.
7. **Evaluation and distribution:** labeled video benchmark, per-language OCR
   and reconstruction metrics, packaging, and user documentation.

## Acceptance criteria for phase 1

- A new language profile can be registered without changing OCR or C# modules.
- Unique file extensions are identified directly; ambiguous extensions abstain.
- Content matches return confidence and human-readable evidence.
- Unknown or tied candidates return no guess.
- Automated tests run independently of video files, FFmpeg, Tesseract, and
  network access.

## Limitations

The first registry is a metadata/heuristic foundation, not a deep-learning
model, parser, or guarantee of support for every syntax. The listed 15 languages
are initial candidates; validation against the actual course videos will guide
which language adapters are implemented next.
