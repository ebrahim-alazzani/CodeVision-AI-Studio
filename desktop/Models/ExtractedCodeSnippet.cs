using CommunityToolkit.Mvvm.ComponentModel;

namespace CodeVision.Desktop.Models;

public partial class ExtractedCodeSnippet : ObservableObject
{
    [ObservableProperty]
    private string _id = Guid.NewGuid().ToString("N");

    [ObservableProperty]
    private string _targetFilePath = "Program.cs";

    [ObservableProperty]
    private string _language = "C#";

    [ObservableProperty]
    private double _timestampSec;

    public string TimestampFormatted => TimeSpan.FromSeconds(TimestampSec).ToString(@"mm\:ss");

    [ObservableProperty]
    private double _confidence = 0.92;

    public string ConfidencePercent => $"{Math.Round(Confidence * 100, 1)}%";

    [ObservableProperty]
    private string _codeContent = string.Empty;

    [ObservableProperty]
    private string _explanation = string.Empty;

    [ObservableProperty]
    private bool _isReviewed;
}
