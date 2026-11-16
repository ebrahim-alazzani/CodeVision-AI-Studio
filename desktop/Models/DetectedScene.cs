namespace CodeVision.Desktop.Models;

public sealed class DetectedScene
{
    public int SceneIndex { get; set; }
    public double TimestampSec { get; set; }
    public string TimestampFormatted => TimeSpan.FromSeconds(TimestampSec).ToString(@"mm\:ss");
    public double CodeLikelihood { get; set; }
    public string ConfidencePercent => $"{Math.Round(CodeLikelihood * 100, 1)}%";
    public bool IsCodeScene { get; set; }
    public string PreviewImagePath { get; set; } = string.Empty;
    public string SummaryText { get; set; } = string.Empty;
}
