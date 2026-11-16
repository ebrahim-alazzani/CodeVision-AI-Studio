using CommunityToolkit.Mvvm.ComponentModel;

namespace CodeVision.Desktop.Models;

public partial class VideoItem : ObservableObject
{
    [ObservableProperty]
    private string _id = Guid.NewGuid().ToString("N");

    [ObservableProperty]
    private string _filePath = string.Empty;

    [ObservableProperty]
    private string _fileName = string.Empty;

    [ObservableProperty]
    private string _durationString = "00:00";

    [ObservableProperty]
    private double _durationSeconds;

    [ObservableProperty]
    private string _status = "جاهز";

    [ObservableProperty]
    private int _progressPercentage;

    [ObservableProperty]
    private int _detectedScenesCount;

    [ObservableProperty]
    private int _extractedFilesCount;

    [ObservableProperty]
    private double _averageConfidence;

    [ObservableProperty]
    private string _detectedLanguage = "C#";

    [ObservableProperty]
    private string _outputDirectory = string.Empty;

    [ObservableProperty]
    private bool _isSelected;
}
