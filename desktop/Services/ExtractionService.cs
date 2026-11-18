using System.IO;
using System.Text.Json;
using CodeVision.Desktop.Models;

namespace CodeVision.Desktop.Services;

public sealed class ExtractionService
{
    private readonly PythonEngineService _python;
    private readonly SettingsService _settings;
    private readonly LoggingService _logger;

    public ExtractionService(
        PythonEngineService python,
        SettingsService settings,
        LoggingService logger)
    {
        _python = python;
        _settings = settings;
        _logger = logger;
    }

    public async Task<bool> ExtractVideoAsync(
        VideoItem video,
        Action<int, string>? onProgress,
        CancellationToken cancellationToken = default)
    {
        video.Status = "جارٍ الاستخراج…";
        video.ProgressPercentage = 5;
        onProgress?.Invoke(5, "بدء تهيئة بيئة الاستخراج ومحرك OpenCV…");

        var outRoot = _settings.Current.OutputDirectory;
        if (string.IsNullOrWhiteSpace(outRoot))
            outRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");
        Directory.CreateDirectory(outRoot);

        var scriptPath = _settings.Current.EngineScriptPath;
        if (string.IsNullOrWhiteSpace(scriptPath) || !File.Exists(scriptPath))
        {
            scriptPath = @"e:\New folder (3)\CodeVisionPhase1\core\video_pipeline.py";
        }

        try
        {
            _logger.Info($"Running Real Video Pipeline for '{video.FileName}' using script '{scriptPath}'");

            var safeLang = string.IsNullOrWhiteSpace(video.DetectedLanguage) ? "auto" : video.DetectedLanguage;
            var cliArgs = $"\"{video.FilePath}\" \"{outRoot}\" --language \"{safeLang}\" --sample_sec 2.0";

            var exitCode = await _python.RunScriptAsync(scriptPath, cliArgs, line =>
            {
                if (line.StartsWith("PROGRESS:", StringComparison.OrdinalIgnoreCase))
                {
                    // Format: PROGRESS: 45 | [CAPTURED] ...
                    var parts = line.Substring(9).Split('|', 2);
                    if (parts.Length > 0 && int.TryParse(parts[0].Trim(), out var pct))
                    {
                        var msg = parts.Length > 1 ? parts[1].Trim() : line;
                        App.RunOnUIThread(() =>
                        {
                            video.ProgressPercentage = pct;
                            onProgress?.Invoke(pct, msg);
                        });
                    }
                }
                else
                {
                    App.RunOnUIThread(() =>
                    {
                        onProgress?.Invoke(video.ProgressPercentage, line);
                    });
                }
            }, cancellationToken);

            if (exitCode == 0)
            {
                var safeName = Path.GetFileNameWithoutExtension(video.FilePath);
                var jobFolder = Path.Combine(outRoot, $"job_{safeName}");

                int detectedScenes = 0;
                var scenesFile = Path.Combine(jobFolder, "scenes.json");
                if (File.Exists(scenesFile))
                {
                    try
                    {
                        var json = File.ReadAllText(scenesFile);
                        using var doc = JsonDocument.Parse(json);
                        detectedScenes = doc.RootElement.GetArrayLength();
                    }
                    catch { }
                }

                int extractedFiles = 0;
                var resultsDir = Path.Combine(jobFolder, "results");
                if (Directory.Exists(resultsDir))
                {
                    extractedFiles = Directory.GetFiles(resultsDir).Length;
                }

                double avgConfidence = 0.0;
                var manifestFile = Path.Combine(jobFolder, "manifest.json");
                if (File.Exists(manifestFile))
                {
                    try
                    {
                        using var mDoc = JsonDocument.Parse(File.ReadAllText(manifestFile));
                        if (mDoc.RootElement.TryGetProperty("average_confidence", out var confProp))
                        {
                            avgConfidence = confProp.GetDouble();
                        }
                    }
                    catch { }
                }

                App.RunOnUIThread(() =>
                {
                    video.OutputDirectory = jobFolder;
                    video.DetectedScenesCount = detectedScenes;
                    video.ExtractedFilesCount = extractedFiles;
                    video.ProgressPercentage = 100;
                    video.Status = "مكتمل";
                    video.AverageConfidence = avgConfidence;
                    onProgress?.Invoke(100, $"اكتمل استخراج {video.FileName} بنجاح ({extractedFiles} ملفات مستعادة · الثقة: {(avgConfidence * 100):F1}%).");
                });

                _logger.Info($"Successfully completed extraction for {video.FileName}: {detectedScenes} scenes, {extractedFiles} files.");
                return true;
            }
            else
            {
                App.RunOnUIThread(() =>
                {
                    video.Status = "فشل الاستخراج";
                    onProgress?.Invoke(0, $"فشل كود خروج العملية (Exit Code: {exitCode})");
                });
                return false;
            }
        }
        catch (OperationCanceledException)
        {
            App.RunOnUIThread(() =>
            {
                video.Status = "تم الإلغاء";
                onProgress?.Invoke(0, "تم إلغاء عملية الاستخراج.");
            });
            return false;
        }
        catch (Exception ex)
        {
            App.RunOnUIThread(() =>
            {
                video.Status = "فشل الاستخراج";
                onProgress?.Invoke(0, $"خطأ: {ex.Message}");
            });
            _logger.Error($"Failed extraction for {video.FileName}", ex);
            return false;
        }
    }
}
