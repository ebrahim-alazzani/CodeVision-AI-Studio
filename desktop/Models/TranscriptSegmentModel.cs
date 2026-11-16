namespace CodeVision.Desktop.Models;

public sealed class TranscriptSegmentModel
{
    public double StartSec { get; set; }
    public double EndSec { get; set; }
    public string TimeRange => $"{TimeSpan.FromSeconds(StartSec):mm\\:ss} - {TimeSpan.FromSeconds(EndSec):mm\\:ss}";
    public string Text { get; set; } = string.Empty;
    public double? Confidence { get; set; }
    public string ConfidencePercent => Confidence.HasValue ? $"{Math.Round(Confidence.Value * 100, 1)}%" : "-";
}
