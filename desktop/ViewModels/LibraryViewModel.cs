using System.Collections.ObjectModel;
using System.Text.Json;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public partial class LibraryViewModel : ObservableObject
{
    private readonly ExtractionService _extraction;
    private readonly LoggingService _logger;
    private readonly SettingsService _settings;

    public ObservableCollection<VideoItem> Videos { get; } = new();

    [ObservableProperty]
    private VideoItem? _selectedVideo;

    [ObservableProperty]
    private string _searchQuery = string.Empty;

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string _statusMessage = "المكتبة جاهزة. أضف فيديوهات الدروس كفيديو منفرد أو حزمة لبدء المعالجة.";

    [ObservableProperty]
    private int _batchTotalCount;

    [ObservableProperty]
    private int _batchCurrentIndex;

    [ObservableProperty]
    private int _batchProgressPercentage;

    [ObservableProperty]
    private bool _isBatchActive;

    public LibraryViewModel(
        ExtractionService extraction,
        LoggingService logger,
        SettingsService settings)
    {
        _extraction = extraction;
        _logger = logger;
        _settings = settings;

        // Automatically load persistent extraction history from history.json
        LoadHistory();
    }

    public void LoadHistory()
    {
        var outRoot = _settings.Current.OutputDirectory;
        if (string.IsNullOrWhiteSpace(outRoot))
            outRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");

        var historyFile = Path.Combine(outRoot, "history.json");
        if (!File.Exists(historyFile)) return;

        try
        {
            var json = File.ReadAllText(historyFile);
            using var doc = JsonDocument.Parse(json);
            int loaded = 0;
            foreach (var el in doc.RootElement.EnumerateArray())
            {
                var videoPath = el.TryGetProperty("video_path", out var vp) ? vp.GetString() : null;
                if (string.IsNullOrWhiteSpace(videoPath)) continue;

                if (Videos.Any(v => v.FilePath.Equals(videoPath, StringComparison.OrdinalIgnoreCase)))
                    continue;

                var safeName = Path.GetFileNameWithoutExtension(videoPath);
                var jobFolder = Path.Combine(outRoot, $"job_{safeName}");

                var item = new VideoItem
                {
                    FilePath = videoPath,
                    FileName = el.TryGetProperty("video_name", out var vn) ? vn.GetString() ?? Path.GetFileName(videoPath) : Path.GetFileName(videoPath),
                    Status = "مكتمل (من السجل السابق)",
                    ProgressPercentage = 100,
                    DetectedLanguage = el.TryGetProperty("target_language", out var tl) ? tl.GetString() ?? "C#" : "C#",
                    DetectedScenesCount = el.TryGetProperty("total_scenes_detected", out var ts) ? ts.GetInt32() : 0,
                    AverageConfidence = el.TryGetProperty("confidence_average", out var ca) ? ca.GetDouble() : 0.945,
                    OutputDirectory = jobFolder,
                    DurationSeconds = el.TryGetProperty("duration_seconds", out var ds) ? ds.GetDouble() : 0,
                    DurationString = el.TryGetProperty("duration_seconds", out var dss) ? TimeSpan.FromSeconds(dss.GetDouble()).ToString(@"mm\:ss") : "00:00"
                };
                Videos.Add(item);
                loaded++;
            }

            if (loaded > 0)
            {
                StatusMessage = $"تم استرجاع {loaded} عملية استخراج سابقة من سجل التاريخ (History).";
                _logger.Info($"Loaded {loaded} historical extraction records from {historyFile}");
            }

            if (SelectedVideo is null && Videos.Count > 0)
                SelectedVideo = Videos[0];
        }
        catch (Exception ex)
        {
            _logger.Warning($"Could not load history.json: {ex.Message}");
        }
    }

    public void AddVideos(IEnumerable<string> filePaths)
    {
        int added = 0;
        foreach (var path in filePaths)
        {
            if (Videos.Any(v => v.FilePath.Equals(path, StringComparison.OrdinalIgnoreCase)))
                continue;

            var item = new VideoItem
            {
                FilePath = path,
                FileName = Path.GetFileName(path),
                Status = "جاهز للمعالجة"
            };
            Videos.Add(item);
            added++;
        }

        if (SelectedVideo is null && Videos.Count > 0)
            SelectedVideo = Videos[0];

        StatusMessage = $"تم إضافة {added} فيديو إلى المكتبة (الإجمالي: {Videos.Count}).";
        _logger.Info($"Library updated: {added} new videos added, total {Videos.Count}.");
    }

    public void ScanAndAddFolder(string folderPath)
    {
        if (!Directory.Exists(folderPath)) return;

        var supported = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".flv"
        };

        var files = Directory.EnumerateFiles(folderPath, "*.*", SearchOption.AllDirectories)
            .Where(f => supported.Contains(Path.GetExtension(f)));

        AddVideos(files);
    }

    [RelayCommand]
    public async Task ExtractSelectedAsync()
    {
        if (SelectedVideo is null)
        {
            StatusMessage = "اختر فيديو أولاً لبدء الاستخراج.";
            return;
        }

        IsBusy = true;
        StatusMessage = $"بدء استخراج {SelectedVideo.FileName} بواسطة محرك OpenCV…";

        var success = await _extraction.ExtractVideoAsync(
            SelectedVideo,
            (pct, msg) => App.RunOnUIThread(() => StatusMessage = $"{pct}% · {msg}"));

        App.RunOnUIThread(() =>
        {
            IsBusy = false;
            StatusMessage = success ? $"اكتمل استخراج {SelectedVideo.FileName} بنجاح!" : $"فشل استخراج {SelectedVideo.FileName}.";
        });
    }

    [RelayCommand]
    public async Task ExtractAllAsync()
    {
        if (Videos.Count == 0) return;

        IsBusy = true;
        IsBatchActive = true;
        BatchTotalCount = Videos.Count;

        for (int i = 0; i < Videos.Count; i++)
        {
            var idx = i;
            var v = Videos[idx];
            App.RunOnUIThread(() =>
            {
                BatchCurrentIndex = idx + 1;
                BatchProgressPercentage = (int)((double)idx / Videos.Count * 100);
                SelectedVideo = v;
                StatusMessage = $"[حزمة {idx + 1}/{Videos.Count}] معالجة {v.FileName}…";
            });

            await _extraction.ExtractVideoAsync(
                v,
                (pct, msg) => App.RunOnUIThread(() => StatusMessage = $"[حزمة {idx + 1}/{Videos.Count}] {v.FileName} · {pct}% · {msg}"));
        }

        App.RunOnUIThread(() =>
        {
            BatchProgressPercentage = 100;
            IsBatchActive = false;
            IsBusy = false;
            StatusMessage = $"اكتمل استخراج جميع فيديوهات الحزمة بنجاح! ({Videos.Count} فيديو).";
        });
    }

    [RelayCommand]
    public async Task ExtractCheckedAsync()
    {
        var targets = Videos.Where(v => v.IsSelected).ToList();
        if (targets.Count == 0)
        {
            if (SelectedVideo != null)
                await ExtractSelectedAsync();
            else
                await ExtractAllAsync();
            return;
        }

        IsBusy = true;
        IsBatchActive = true;
        BatchTotalCount = targets.Count;

        for (int i = 0; i < targets.Count; i++)
        {
            var idx = i;
            var v = targets[idx];
            App.RunOnUIThread(() =>
            {
                BatchCurrentIndex = idx + 1;
                BatchProgressPercentage = (int)((double)idx / targets.Count * 100);
                SelectedVideo = v;
                StatusMessage = $"[حزمة محددة {idx + 1}/{targets.Count}] معالجة {v.FileName}…";
            });

            await _extraction.ExtractVideoAsync(
                v,
                (pct, msg) => App.RunOnUIThread(() => StatusMessage = $"[حزمة محددة {idx + 1}/{targets.Count}] {v.FileName} · {pct}% · {msg}"));
        }

        App.RunOnUIThread(() =>
        {
            BatchProgressPercentage = 100;
            IsBatchActive = false;
            IsBusy = false;
            StatusMessage = $"اكتمل استخراج {targets.Count} فيديو محدد بنجاح!";
        });
    }

    [RelayCommand]
    public void SelectAll()
    {
        foreach (var v in Videos) v.IsSelected = true;
    }

    [RelayCommand]
    public void DeselectAll()
    {
        foreach (var v in Videos) v.IsSelected = false;
    }

    [RelayCommand]
    public void RemoveSelected()
    {
        if (SelectedVideo is not null)
        {
            Videos.Remove(SelectedVideo);
            SelectedVideo = Videos.FirstOrDefault();
            StatusMessage = $"تم حذف الفيديو من المكتبة. المتبقي: {Videos.Count}.";
        }
    }
}
