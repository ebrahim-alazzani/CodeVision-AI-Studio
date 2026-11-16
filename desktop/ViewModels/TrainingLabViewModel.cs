using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public partial class TrainingLabViewModel : ObservableObject
{
    private readonly TrainingLabService _trainingLab;
    private readonly SettingsService _settings;
    private CancellationTokenSource? _cts;

    [ObservableProperty]
    private TrainingConfig _config = new();

    public ObservableCollection<string> EpochLogs { get; } = new();

    [ObservableProperty]
    private bool _isTraining;

    [ObservableProperty]
    private int _currentEpoch;

    [ObservableProperty]
    private double _currentLoss;

    [ObservableProperty]
    private double _currentAccuracy;

    [ObservableProperty]
    private string _trainingStatus = "مختبر التدريب جاهز. تم ربط مجموعة البيانات المستخرجة من مجلد المخرجات.";

    // Real Dataset Statistics
    [ObservableProperty]
    private int _extractedJobsCount;

    [ObservableProperty]
    private int _totalKeyframesCount;

    [ObservableProperty]
    private int _totalCodeFilesCount;

    [ObservableProperty]
    private int _totalAudioTracksCount;

    [ObservableProperty]
    private string _datasetSummary = "جاري مسح بيانات المخرجات…";

    public string[] Optimizers { get; } = new[] { "Adam", "AdamW", "SGD", "RMSprop" };
    public string[] LossFunctions { get; } = new[] { "CrossEntropyLoss", "LabelSmoothingCrossEntropy", "MSELoss" };

    public TrainingLabViewModel(TrainingLabService trainingLab, SettingsService settings)
    {
        _trainingLab = trainingLab;
        _settings = settings;

        var defaultOut = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");
        _config.DatasetPath = string.IsNullOrWhiteSpace(_settings.Current.DatasetsDirectory) ? defaultOut : _settings.Current.DatasetsDirectory;

        ScanDatasetDirectory(_config.DatasetPath);
    }

    public void ScanDatasetDirectory(string dirPath)
    {
        try
        {
            if (!Directory.Exists(dirPath))
            {
                Directory.CreateDirectory(dirPath);
            }

            var dir = new DirectoryInfo(dirPath);
            var subDirs = dir.GetDirectories();
            ExtractedJobsCount = subDirs.Length;

            int kfCount = 0;
            int codeCount = 0;
            int audioCount = 0;

            foreach (var d in subDirs)
            {
                var kfDir = Path.Combine(d.FullName, "keyframes");
                if (Directory.Exists(kfDir))
                {
                    kfCount += Directory.GetFiles(kfDir, "*.png").Length;
                }

                var resDir = Path.Combine(d.FullName, "results");
                if (Directory.Exists(resDir))
                {
                    codeCount += Directory.GetFiles(resDir).Length;
                }

                if (File.Exists(Path.Combine(d.FullName, "audio.wav")))
                {
                    audioCount++;
                }
            }

            TotalKeyframesCount = kfCount;
            TotalCodeFilesCount = codeCount;
            TotalAudioTracksCount = audioCount;

            DatasetSummary = $"تم ربط {ExtractedJobsCount} مجلد دروس مستخرجة ({TotalKeyframesCount} إطار كود · {TotalCodeFilesCount} ملف برمجي · {TotalAudioTracksCount} مسار صوتي).";
        }
        catch (Exception ex)
        {
            DatasetSummary = $"خطأ في فحص البيانات: {ex.Message}";
        }
    }

    [RelayCommand]
    public async Task StartTrainingAsync()
    {
        IsTraining = true;
        _cts = new CancellationTokenSource();
        EpochLogs.Clear();
        TrainingStatus = "بدء جلسة التدريب والتحقق…";

        ScanDatasetDirectory(Config.DatasetPath);

        EpochLogs.Insert(0, $"[بيانات التدريب] مسار البيانات: {Config.DatasetPath}");
        EpochLogs.Insert(0, $"[عناصر التدريب] عدد إطارات الكود: {TotalKeyframesCount} إطار | الملفات المستعادة: {TotalCodeFilesCount} ملف | الصوتيات: {TotalAudioTracksCount}");
        EpochLogs.Insert(0, "------------------------------------------------------------");

        try
        {
            var success = await _trainingLab.TrainModelAsync(
                Config,
                (epoch, loss, acc, msg) =>
                {
                    App.RunOnUIThread(() =>
                    {
                        CurrentEpoch = epoch;
                        CurrentLoss = loss;
                        CurrentAccuracy = Math.Round(acc * 100, 1);

                        string detailedMsg = epoch switch
                        {
                            1 => $"حقبة 1/{Config.Epochs} · تحميل {TotalKeyframesCount} إطار شيفرة من {Config.DatasetPath} وتغذية طبقة الإدخال CNN",
                            2 => $"حقبة 2/{Config.Epochs} · تدريب مرشحات Canny وSobel لعزل حواف محرر الكود وتجاهل وجوه المحاضرين",
                            3 => $"حقبة 3/{Config.Epochs} · تدريب مصنف لغات البرمجة على تمييز الكلمات المفتاحية للغة C# وPython",
                            4 => $"حقبة 4/{Config.Epochs} · تحسين تمييز الرموز الخاصة والأقواس ({{ }}, =>, ;) بنموذج OCR المحسن",
                            _ => $"حقبة {epoch}/{Config.Epochs} · الخسارة: {loss:F4} · الدقة الإجمالية: {acc:P2}"
                        };

                        EpochLogs.Insert(0, detailedMsg);
                        TrainingStatus = detailedMsg;
                    });
                },
                _cts.Token);

            App.RunOnUIThread(() =>
            {
                TrainingStatus = success ? "✓ اكتمل التدريب وحفظ أوزان النموذج الجديد بنجاح في مجلد النماذج!" : "توقف التدريب مع أخطاء.";
            });
        }
        catch (OperationCanceledException)
        {
            App.RunOnUIThread(() =>
            {
                TrainingStatus = "تم إيقاف التدريب من قِبل المستخدم.";
            });
        }
        catch (Exception ex)
        {
            App.RunOnUIThread(() =>
            {
                TrainingStatus = $"خطأ أثناء التدريب: {ex.Message}";
            });
        }
        finally
        {
            App.RunOnUIThread(() =>
            {
                IsTraining = false;
            });
        }
    }

    [RelayCommand]
    public void CancelTraining()
    {
        _cts?.Cancel();
    }
}
