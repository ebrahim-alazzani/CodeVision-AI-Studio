"""
ACE (Alignment-based Consensus Estimator) Code Aligner.

Consolidates noisy per-frame OCR into a single coherent code document using:
1. Needleman-Wunsch Dynamic Programming alignment with free/cheap skips for
   vertical scrolling and frame line inserts for live typing.
2. Temporal observation tracking (text, confidence, timestamp, indentation).
3. Recency-weighted medoid consensus scoring and character-level voting.
4. Accurate indentation calculation, snapping, and syntactic reconstruction.

Inspired by video2code ACE consensus architecture.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from collections import Counter
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class LineObservation:
    """Represents a single observation of a code line in a frame."""
    text: str
    conf: float = 1.0
    t: float = 0.0
    indent: int = 0
    stripped: str = ""
    frame_idx: Optional[int] = None

    def __post_init__(self):
        if not self.stripped:
            self.stripped = self.text.strip()
        if self.indent == 0 and self.text:
            self.indent = ACEAligner.calculate_indentation(self.text)


@dataclass
class DocumentLine:
    """Represents an aligned line in the growing consolidated code document."""
    line_id: int
    best_text: str
    observations: List[LineObservation] = field(default_factory=list)
    indent: int = 0
    agreement: float = 1.0
    first_seen_t: float = 0.0
    last_seen_t: float = 0.0

    def add_observation(self, obs: LineObservation) -> None:
        self.observations.append(obs)
        if len(self.observations) == 1:
            self.first_seen_t = obs.t
        self.last_seen_t = max(self.last_seen_t, obs.t)


class ACEAligner:
    """
    ACE Code Aligner for temporal multi-frame code reconstruction.
    
    Handles:
    - Vertical scrolling via asymmetric free/cheap doc-line skips.
    - Live typing via frame-line insertions and recency-weighted consensus.
    - OCR jitter and misreads via character-level majority voting.
    - Indentation normalization and scope-based syntactic recovery.
    """

    def __init__(
        self,
        min_sim: float = 0.60,
        skip_cost: float = -0.05,
        ins_cost: float = -0.40,
        default_indent_size: int = 4,
        snap_indent: bool = True
    ):
        """
        Initialize the ACE aligner.

        Args:
            min_sim: Minimum fuzzy similarity threshold for matching lines (0.0 to 1.0).
            skip_cost: Score penalty for skipping a document line (scrolling).
            ins_cost: Score penalty for inserting a new line (typing / addition).
            default_indent_size: Standard indentation step (typically 4 or 2).
            snap_indent: Whether to snap indentation to multiples of default_indent_size.
        """
        self.min_sim = min_sim
        self.skip_cost = skip_cost
        self.ins_cost = ins_cost
        self.default_indent_size = default_indent_size
        self.snap_indent = snap_indent

        self.document: List[DocumentLine] = []
        self._next_line_id: int = 1
        self._t_max: float = 1.0

    def reset(self) -> None:
        """Clear the accumulated document and reset state."""
        self.document.clear()
        self._next_line_id = 1
        self._t_max = 1.0

    @staticmethod
    def calculate_indentation(line: str, tab_size: int = 4) -> int:
        """Calculate the leading whitespace indentation count, converting tabs."""
        match = re.match(r"^([ \t]*)", line)
        if not match:
            return 0
        ws = match.group(1)
        expanded = ws.replace("\t", " " * tab_size)
        return len(expanded)

    @staticmethod
    def line_similarity(a: str, b: str, ignore_indent: bool = True) -> float:
        """
        Compute hybrid character- and token-level similarity ratio between two code lines.
        
        Args:
            a: First line.
            b: Second line.
            ignore_indent: When True, compares stripped text to resist indent jitter.
        """
        sa = a.strip() if ignore_indent else a
        sb = b.strip() if ignore_indent else b
        if sa == sb:
            return 1.0
        if not sa and not sb:
            return 1.0
        if not sa or not sb:
            return 0.0

        char_sim = SequenceMatcher(None, sa, sb, autojunk=False).ratio()

        tokens_a = re.findall(r'[A-Za-z0-9_]+', sa)
        tokens_b = re.findall(r'[A-Za-z0-9_]+', sb)
        if not tokens_a or not tokens_b:
            return char_sim

        intersection = len(set(tokens_a) & set(tokens_b))
        union = len(set(tokens_a) | set(tokens_b))
        tok_sim = intersection / union if union > 0 else 0.0

        # Short lines (< 25 chars) with low token overlap are typically different statements
        if max(len(sa), len(sb)) < 25 and tok_sim < 0.5:
            return min(char_sim, tok_sim)

        return 0.6 * char_sim + 0.4 * tok_sim

    def _align_dp(
        self,
        doc_lines: List[DocumentLine],
        frame_lines: List[LineObservation]
    ) -> List[Tuple[str, Optional[int], Optional[int]]]:
        """
        Needleman-Wunsch DP alignment between current document lines and frame lines.

        Returns list of operations: (op_type, doc_idx, frame_idx)
        op_type in ("match", "ins", "skip")
        """
        n, m = len(doc_lines), len(frame_lines)
        if n == 0:
            return [("ins", None, j) for j in range(m)]

        # S[i][j]: DP score matrix of size (n+1) x (m+1)
        # B[i][j]: Backtrack pointer matrix
        S = [[0.0] * (m + 1) for _ in range(n + 1)]
        B = [[None] * (m + 1) for _ in range(n + 1)]

        # Leading doc lines not visible (due to vertical scrolling downward): free skip
        for i in range(1, n + 1):
            S[i][0] = 0.0
            B[i][0] = "skip"

        # Frame lines inserted before any doc lines: penalty
        for j in range(1, m + 1):
            S[0][j] = S[0][j - 1] + self.ins_cost
            B[0][j] = "ins"

        # Fill DP matrix
        for i in range(1, n + 1):
            doc_line = doc_lines[i - 1]
            for j in range(1, m + 1):
                frame_line = frame_lines[j - 1]
                s = self.line_similarity(doc_line.best_text, frame_line.text)

                cand = [
                    (S[i - 1][j] + self.skip_cost, "skip"),
                    (S[i][j - 1] + self.ins_cost, "ins")
                ]
                if s >= self.min_sim:
                    # Reward based on similarity match
                    match_score = S[i - 1][j - 1] + (s - self.min_sim + 0.1)
                    cand.append((match_score, "match"))

                S[i][j], B[i][j] = max(cand)

        # Trailing doc lines not visible (due to vertical scrolling upward):
        # find the best end cell in the last column
        best_i = max(range(n + 1), key=lambda k: S[k][m])
        i = best_i
        j = m
        ops = []

        while j > 0 or i > 0:
            if i == 0:
                ops.append(("ins", None, j - 1))
                j -= 1
                continue
            if j == 0:
                break
            op = B[i][j]
            if op == "match":
                ops.append(("match", i - 1, j - 1))
                i -= 1
                j -= 1
            elif op == "skip":
                i -= 1
            else:  # ins
                ops.append(("ins", i, j - 1))
                j -= 1

        return ops[::-1]

    def _best_text_and_indent(
        self,
        observations: List[LineObservation]
    ) -> Tuple[str, int, float, List[str]]:
        """
        Compute the optimal consolidated text and indentation for a line.

        Uses:
        - Confidence and recency weighted candidate scoring.
        - Per-character majority voting among same-length top candidates.
        - Confidence-weighted indentation calculation.
        """
        if not observations:
            return "", 0, 1.0, []

        if len(observations) == 1:
            obs = observations[0]
            indent = obs.indent
            if self.snap_indent and self.default_indent_size > 0:
                level = round(indent / self.default_indent_size)
                indent = level * self.default_indent_size
            return obs.text, indent, 1.0, [obs.text]

        t_max = self._t_max if self._t_max > 0 else 1.0

        # Unique candidate texts
        cands = {o.text: 0.0 for o in observations}
        scored = []
        for c in cands:
            sc = 0.0
            for o in observations:
                # Recency factor: later frames are more likely to contain completed typing
                rec = 1.0 + 0.5 * (o.t / t_max)
                sc += o.conf * rec * self.line_similarity(c, o.text, ignore_indent=False)
            scored.append((sc, c))

        scored.sort(reverse=True)
        top = scored[0][1]

        # Per-character majority vote among candidates of same length
        same_len = [o for o in observations if len(o.text) == len(top)]
        if len(same_len) >= 3:
            voted_chars = []
            for k in range(len(top)):
                cnt = Counter()
                for o in same_len:
                    cnt[o.text[k]] += o.conf
                most_common = cnt.most_common(1)
                voted_chars.append(most_common[0][0] if most_common else top[k])
            voted = "".join(voted_chars)
            if self.line_similarity(voted, top, ignore_indent=False) > 0.85:
                top = voted

        # Calculate consensus indentation
        total_weight = sum(o.conf for o in observations) or 1.0
        weighted_indent = sum(o.indent * o.conf for o in observations) / total_weight
        if self.snap_indent and self.default_indent_size > 0:
            level = round(weighted_indent / self.default_indent_size)
            final_indent = level * self.default_indent_size
        else:
            final_indent = int(round(weighted_indent))

        # Re-attach normalized indentation if top text had indentation
        top_stripped = top.strip()
        if top_stripped:
            top_reconstructed = (" " * final_indent) + top_stripped
        else:
            top_reconstructed = ""

        # Agreement score: mean similarity between chosen text and all observations
        agree = sum(self.line_similarity(top, o.text, ignore_indent=True) for o in observations) / len(observations)
        top_candidates = [c for _, c in scored[:4]]

        return top_reconstructed, final_indent, agree, top_candidates

    def add_frame(
        self,
        lines: List[Union[str, Dict[str, Any], LineObservation]],
        timestamp: float = 0.0,
        confidences: Optional[List[float]] = None,
        frame_idx: Optional[int] = None
    ) -> None:
        """
        Align and merge a new frame of OCR code lines into the growing document.

        Args:
            lines: List of code lines (strings, dicts, or LineObservation).
            timestamp: Frame presentation time in seconds.
            confidences: Optional list of float confidences (0.0 to 1.0).
            frame_idx: Optional sequential frame number.
        """
        self._t_max = max(self._t_max, timestamp)

        # Normalize incoming lines to LineObservation objects
        frame_obs: List[LineObservation] = []
        for idx, item in enumerate(lines):
            if isinstance(item, LineObservation):
                obs = item
            elif isinstance(item, dict):
                text = item.get("text", "")
                conf = float(item.get("conf", 1.0))
                t = float(item.get("t", timestamp))
                obs = LineObservation(
                    text=text,
                    conf=conf,
                    t=t,
                    indent=self.calculate_indentation(text, self.default_indent_size),
                    frame_idx=frame_idx
                )
            else:
                text = str(item)
                conf = confidences[idx] if confidences and idx < len(confidences) else 1.0
                obs = LineObservation(
                    text=text,
                    conf=conf,
                    t=timestamp,
                    indent=self.calculate_indentation(text, self.default_indent_size),
                    frame_idx=frame_idx
                )

            if obs.text.strip():  # ignore empty noise lines
                frame_obs.append(obs)

        if not frame_obs:
            return

        def create_doc_line(obs: LineObservation) -> DocumentLine:
            doc_line = DocumentLine(
                line_id=self._next_line_id,
                best_text=obs.text,
                observations=[obs],
                indent=obs.indent,
                agreement=1.0,
                first_seen_t=obs.t,
                last_seen_t=obs.t
            )
            self._next_line_id += 1
            return doc_line

        # Initial frame forms the base document
        if not self.document:
            for obs in frame_obs:
                self.document.append(create_doc_line(obs))
            return

        # Perform Needleman-Wunsch DP alignment
        ops = self._align_dp(self.document, frame_obs)

        pending_inserts: Dict[int, List[int]] = {}
        matched_doc_to_frame: Dict[int, int] = {}

        for kind, i, j in ops:
            if kind == "match":
                if i is not None and j is not None:
                    matched_doc_to_frame[i] = j
            elif kind == "ins":
                if i is not None and j is not None:
                    pending_inserts.setdefault(i, []).append(j)

        # Construct updated document with insertions and matches
        new_document: List[DocumentLine] = []

        # Leading insertions (before all existing document lines)
        head_inserts = [j for (k, i, j) in ops if k == "ins" and i is None and j is not None]
        for j in head_inserts:
            new_document.append(create_doc_line(frame_obs[j]))

        # Process each document line and subsequent insertions
        for di, dline in enumerate(self.document):
            if di in matched_doc_to_frame:
                obs = frame_obs[matched_doc_to_frame[di]]
                dline.add_observation(obs)
                best_txt, best_indent, agree, _ = self._best_text_and_indent(dline.observations)
                dline.best_text = best_txt
                dline.indent = best_indent
                dline.agreement = agree

            new_document.append(dline)

            # Insert any pending lines anchored after this line (di + 1)
            for j in pending_inserts.get(di + 1, []):
                new_document.append(create_doc_line(frame_obs[j]))

        self.document = new_document

    def add_frames(self, frames: List[Dict[str, Any]]) -> None:
        """
        Process a batch of chronological frames.
        Each frame should be a dict: {"t": float, "lines": [...]}
        """
        frames_sorted = sorted(frames, key=lambda f: f.get("t", 0.0))
        for idx, fr in enumerate(frames_sorted):
            t = fr.get("t", float(idx))
            lines = fr.get("lines", [])
            confidences = fr.get("confidences")
            self.add_frame(lines, timestamp=t, confidences=confidences, frame_idx=idx)

    def reconstruct_syntactic_indentation(
        self,
        lines: List[str],
        indent_size: Optional[int] = None
    ) -> List[str]:
        """
        Syntactically reconstruct indentation for flattened code lines
        by tracking block nesting (braces, Python colons, parentheses).
        """
        step = indent_size or self.default_indent_size
        result: List[str] = []
        current_depth = 0

        for raw_line in lines:
            trimmed = raw_line.strip()
            if not trimmed:
                result.append("")
                continue

            # Check if line begins with a dedenting construct
            starts_with_dedent = bool(
                re.match(r"^([\}\]\)]|\belse\b|\belif\b|\bcatch\b|\bfinally\b|\bend\b)", trimmed)
            )
            if starts_with_dedent and current_depth > 0:
                current_depth -= 1

            prefix = " " * (current_depth * step)
            result.append(prefix + trimmed)

            # Analyze line ending or block openings
            ends_with_colon = trimmed.endswith(":")
            open_braces = len(re.findall(r"[\{\[\(]", trimmed))
            close_braces = len(re.findall(r"[\}\]\)]", trimmed))
            net_braces = open_braces - close_braces

            if ends_with_colon:
                current_depth += 1
            elif net_braces > 0:
                current_depth += net_braces
            elif net_braces < 0 and not starts_with_dedent:
                current_depth = max(0, current_depth + net_braces)

        return result

    def get_document_lines(
        self,
        reconstruct_syntactic_if_flattened: bool = True
    ) -> List[str]:
        """
        Get the consolidated list of code lines.

        Args:
            reconstruct_syntactic_if_flattened: If leading indentation was mostly lost,
                reconstruct it syntactically.
        """
        if not self.document:
            return []

        raw_lines = [d.best_text for d in self.document]

        # Check if original lines have meaningful indentation
        non_empty = [l for l in raw_lines if l.strip()]
        if not non_empty:
            return raw_lines

        lines_with_indent = sum(1 for l in non_empty if re.match(r"^\s{2,}|\t", l))
        indent_ratio = lines_with_indent / len(non_empty)

        if indent_ratio < 0.25 and reconstruct_syntactic_if_flattened:
            return self.reconstruct_syntactic_indentation(raw_lines, self.default_indent_size)

        return raw_lines

    def get_consolidated_code(
        self,
        reconstruct_syntactic_if_flattened: bool = True
    ) -> str:
        """Return the consolidated code as a single string."""
        lines = self.get_document_lines(reconstruct_syntactic_if_flattened)
        return "\n".join(lines)

    def get_uncertainty_report(
        self,
        min_agreement: float = 0.90,
        min_mean_conf: float = 0.60
    ) -> List[Dict[str, Any]]:
        """
        Generate an uncertainty report identifying lines that had low agreement,
        low confidence, or single observations across frames.
        """
        report = []
        for k, d in enumerate(self.document, 1):
            n = len(d.observations)
            mean_conf = sum(o.conf for o in d.observations) / n if n > 0 else 0.0
            _, _, agree, cands = self._best_text_and_indent(d.observations)

            if n == 1 or agree < min_agreement or mean_conf < min_mean_conf:
                report.append({
                    "line_number": k,
                    "chosen_text": d.best_text,
                    "observations_count": n,
                    "agreement": round(agree, 3),
                    "mean_confidence": round(mean_conf, 3),
                    "candidates": cands,
                    "first_seen_t": d.first_seen_t,
                    "last_seen_t": d.last_seen_t,
                })
        return report
