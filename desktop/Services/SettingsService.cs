using System.IO;
using System.Text.Json;
using CodeVision.Desktop.Models;

namespace CodeVision.Desktop.Services;

public sealed class SettingsService
{
    private readonly string _settingsFilePath;
    private AppSettings _currentSettings;

    public AppSettings Current => _currentSettings;

    public SettingsService()
    {
        var appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision");
        Directory.CreateDirectory(appData);
        _settingsFilePath = Path.Combine(appData, "appsettings.json");
        _currentSettings = LoadSettings();
    }

    public AppSettings LoadSettings()
    {
        try
        {
            if (File.Exists(_settingsFilePath))
            {
                var json = File.ReadAllText(_settingsFilePath);
                var loaded = JsonSerializer.Deserialize<AppSettings>(json);
                if (loaded is not null)
                {
                    EnsureDefaults(loaded);
                    return loaded;
                }
            }
        }
        catch { }

        var defaults = new AppSettings();
        EnsureDefaults(defaults);
        SaveSettings(defaults);
        return defaults;
    }

    public void SaveSettings(AppSettings settings)
    {
        _currentSettings = settings;
        try
        {
            var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(_settingsFilePath, json);
        }
        catch { }
    }

    private static void EnsureDefaults(AppSettings s)
    {
        if (string.IsNullOrWhiteSpace(s.PythonPath) || !File.Exists(s.PythonPath))
        {
            if (File.Exists(@"C:\Python313\python.exe"))
                s.PythonPath = @"C:\Python313\python.exe";
            else if (File.Exists(@"C:\Users\ibral\anaconda3\python.exe"))
                s.PythonPath = @"C:\Users\ibral\anaconda3\python.exe";
        }

        if (string.IsNullOrWhiteSpace(s.EngineScriptPath) || !File.Exists(s.EngineScriptPath))
        {
            s.EngineScriptPath = @"e:\New folder (3)\CodeVisionPhase1\core\video_pipeline.py";
        }

        if (string.IsNullOrWhiteSpace(s.OutputDirectory))
        {
            s.OutputDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");
        }
        if (string.IsNullOrWhiteSpace(s.DatasetsDirectory))
        {
            s.DatasetsDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "datasets");
        }
        if (string.IsNullOrWhiteSpace(s.ModelsDirectory))
        {
            s.ModelsDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "models");
        }

        Directory.CreateDirectory(s.OutputDirectory);
        Directory.CreateDirectory(s.DatasetsDirectory);
        Directory.CreateDirectory(s.ModelsDirectory);
    }
}
