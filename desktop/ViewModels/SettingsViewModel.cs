using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public partial class SettingsViewModel : ObservableObject
{
    private readonly SettingsService _settings;
    private readonly LoggingService _logger;

    [ObservableProperty]
    private string _pythonPath;

    [ObservableProperty]
    private string _ffmpegPath;

    [ObservableProperty]
    private string _outputDirectory;

    [ObservableProperty]
    private string _datasetsDirectory;

    [ObservableProperty]
    private string _modelsDirectory;

    [ObservableProperty]
    private string _selectedTheme;

    [ObservableProperty]
    private string _recentLogs = string.Empty;

    [ObservableProperty]
    private string _saveMessage = string.Empty;

    public string[] AvailableThemes { get; } = new[] { "Dark", "Light" };

    public SettingsViewModel(SettingsService settings, LoggingService logger)
    {
        _settings = settings;
        _logger = logger;

        var c = _settings.Current;
        _pythonPath = c.PythonPath;
        _ffmpegPath = c.FfmpegPath;
        _outputDirectory = c.OutputDirectory;
        _datasetsDirectory = c.DatasetsDirectory;
        _modelsDirectory = c.ModelsDirectory;
        _selectedTheme = c.Theme;

        RefreshLogs();
    }

    [RelayCommand]
    public void SaveSettings()
    {
        var c = _settings.Current;
        c.PythonPath = PythonPath;
        c.FfmpegPath = FfmpegPath;
        c.OutputDirectory = OutputDirectory;
        c.DatasetsDirectory = DatasetsDirectory;
        c.ModelsDirectory = ModelsDirectory;
        c.Theme = SelectedTheme;

        _settings.SaveSettings(c);
        _logger.Info("User updated settings successfully.");
        SaveMessage = "✓ تم حفظ الإعدادات بنجاح.";
    }

    [RelayCommand]
    public void AutoDetectAnaconda()
    {
        var anaconda = @"C:\Users\ibral\anaconda3\python.exe";
        if (File.Exists(anaconda))
        {
            PythonPath = anaconda;
            SaveMessage = "✓ تم اكتشاف بايثون Anaconda بنجاح!";
        }
        else
        {
            SaveMessage = "لم يتم العثور على مسار Anaconda الافتراضي.";
        }
    }

    [RelayCommand]
    public void RefreshLogs()
    {
        RecentLogs = _logger.ReadRecentLogs(150);
    }
}
