using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;

namespace CodeVision.Desktop.ViewModels;

public partial class ExtractionReviewViewModel : ObservableObject
{
    public ObservableCollection<DetectedScene> DetectedScenes { get; } = new();
    public ObservableCollection<TranscriptSegmentModel> TranscriptSegments { get; } = new();
    public ObservableCollection<ExtractedCodeSnippet> ExtractedSnippets { get; } = new();
    public ObservableCollection<string> LiveExecutionLogs { get; } = new();

    [ObservableProperty]
    private VideoItem? _currentVideo;

    [ObservableProperty]
    private string _realVideoPath = string.Empty;

    [ObservableProperty]
    private bool _hasRealVideo;

    [ObservableProperty]
    private string _audioFilePath = string.Empty;

    [ObservableProperty]
    private bool _hasAudioFile;

    [ObservableProperty]
    private string _audioStatusText = "مسار الصوت: تم الاستخراج (16 kHz Mono PCM WAV)";

    [ObservableProperty]
    private double _currentPositionSeconds;

    [ObservableProperty]
    private double _totalDurationSeconds = 120;

    [ObservableProperty]
    private string _timeDisplay = "00:00 / 02:00";

    [ObservableProperty]
    private DetectedScene? _selectedScene;

    [ObservableProperty]
    private TranscriptSegmentModel? _selectedTranscript;

    [ObservableProperty]
    private ExtractedCodeSnippet? _selectedSnippet;

    // --- Live Extraction Simulation & Algorithms Telemetry ---
    [ObservableProperty]
    private bool _isSimulating;

    [ObservableProperty]
    private int _currentFrameIndex = 1;

    [ObservableProperty]
    private int _totalFramesCount = 3600;

    [ObservableProperty]
    private int _capturedScenesCount = 0;

    [ObservableProperty]
    private int _skippedFramesCount = 0;

    [ObservableProperty]
    private string _currentAlgorithm = "cv2.compareHist + Structural Similarity (SSIM)";

    [ObservableProperty]
    private string _currentLibrary = "OpenCV 4.10 (cv2) · Faster-Whisper · Tesseract";

    [ObservableProperty]
    private string _currentActionStatus = "🟢 [CAPTURED] مشهد شيفرة جديد - تم عزل محرر الكود وتطبيق OCR";

    [ObservableProperty]
    private string _roiCoordinates = "X: 30, Y: 25, W: 420, H: 260";

    // Dynamic Bounding Box Layout for Canvas
    [ObservableProperty]
    private double _roiLeft = 30;

    [ObservableProperty]
    private double _roiTop = 25;

    [ObservableProperty]
    private double _roiWidth = 420;

    [ObservableProperty]
    private double _roiHeight = 260;

    [ObservableProperty]
    private double _playbackSpeed = 1.0;

    [ObservableProperty]
    private bool _isRoiDetected = true;

    [ObservableProperty]
    private double _frameDifferenceScore = 14.8;

    [ObservableProperty]
    private string _currentFrameImagePath = string.Empty;

    [ObservableProperty]
    private bool _isTurboMode = true;

    private CancellationTokenSource? _simCts;

    public ExtractionReviewViewModel()
    {
        LoadSampleData();
    }

    public void LogEvent(string message)
    {
        var ts = TimeSpan.FromSeconds(CurrentPositionSeconds).ToString(@"mm\:ss\.f");
        var line = $"[{ts}] {message}";
        App.RunOnUIThread(() =>
        {
            LiveExecutionLogs.Insert(0, line);
            if (LiveExecutionLogs.Count > 150)
            {
                LiveExecutionLogs.RemoveAt(LiveExecutionLogs.Count - 1);
            }
        });
    }

    public void LoadFromVideo(VideoItem video)
    {
        CurrentVideo = video;
        RealVideoPath = video.FilePath;
        HasRealVideo = !string.IsNullOrWhiteSpace(video.FilePath) && File.Exists(video.FilePath);

        LiveExecutionLogs.Clear();
        LogEvent($"🎥 فتح ملف الفيديو للمحاكاة: {video.FileName}");

        // Look for job folder in output
        var safeName = Path.GetFileNameWithoutExtension(video.FilePath);
        var jobFolder = video.OutputDirectory;
        if (string.IsNullOrWhiteSpace(jobFolder) || !Directory.Exists(jobFolder))
        {
            var defaultOut = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");
            var candidate = Path.Combine(defaultOut, $"job_{safeName}");
            if (Directory.Exists(candidate)) jobFolder = candidate;
        }

        if (!string.IsNullOrWhiteSpace(jobFolder) && Directory.Exists(jobFolder))
        {
            LoadRealJobData(jobFolder);
        }
        else
        {
            LoadSampleData();
        }

        if (video.DurationSeconds > 0)
        {
            TotalDurationSeconds = video.DurationSeconds;
            TotalFramesCount = (int)(video.DurationSeconds * 30);
            UpdateTimeDisplay();
        }
    }

    public void LoadRealVideoDirectly(string videoPath)
    {
        if (File.Exists(videoPath))
        {
            var item = new VideoItem
            {
                FilePath = videoPath,
                FileName = Path.GetFileName(videoPath),
                Status = "جاهز للمحاكاة"
            };
            LoadFromVideo(item);
        }
    }

    private void LoadRealJobData(string jobFolder)
    {
        // 0. Load manifest.json for duration and metadata
        var manifestFile = Path.Combine(jobFolder, "manifest.json");
        if (File.Exists(manifestFile))
        {
            try
            {
                using var mDoc = JsonDocument.Parse(File.ReadAllText(manifestFile));
                if (mDoc.RootElement.TryGetProperty("duration_sec", out var durProp))
                {
                    var dur = durProp.GetDouble();
                    if (dur > 0)
                    {
                        TotalDurationSeconds = dur;
                        TotalFramesCount = (int)(dur * 30);
                    }
                }
            }
            catch { }
        }

        // 1. Audio track
        var audioWav = Path.Combine(jobFolder, "audio.wav");
        if (File.Exists(audioWav))
        {
            AudioFilePath = audioWav;
            HasAudioFile = true;
            var fi = new FileInfo(audioWav);
            AudioStatusText = $"مسار الصوت: تم استخراجه بنجاح (16 kHz Mono · الحجم: {fi.Length / 1024} KB)";
            LogEvent($"🔊 تم رصد المسار الصوتي المستخرج: audio.wav ({fi.Length / 1024} KB)");
        }
        else
        {
            HasAudioFile = false;
            AudioStatusText = "مسار الصوت: غير متوفر";
        }

        // 2. Load scenes.json
        var scenesFile = Path.Combine(jobFolder, "scenes.json");
        if (File.Exists(scenesFile))
        {
            try
            {
                var json = File.ReadAllText(scenesFile);
                using var doc = JsonDocument.Parse(json);
                DetectedScenes.Clear();
                double maxSceneSec = 0;
                foreach (var el in doc.RootElement.EnumerateArray())
                {
                    var ts = el.TryGetProperty("timestamp_sec", out var tsp) ? tsp.GetDouble() : 0;
                    if (ts > maxSceneSec) maxSceneSec = ts;
                    var scene = new DetectedScene
                    {
                        SceneIndex = el.TryGetProperty("scene_index", out var si) ? si.GetInt32() : DetectedScenes.Count + 1,
                        TimestampSec = ts,
                        CodeLikelihood = el.TryGetProperty("code_likelihood", out var cl) ? cl.GetDouble() : 0.9,
                        IsCodeScene = true,
                        SummaryText = el.TryGetProperty("summary", out var sm) ? sm.GetString() ?? "" : $"مشهد كود #{DetectedScenes.Count + 1}"
                    };
                    DetectedScenes.Add(scene);
                }
                if (TotalDurationSeconds <= 120 && maxSceneSec > 0)
                {
                    TotalDurationSeconds = maxSceneSec + 5.0;
                    TotalFramesCount = (int)(TotalDurationSeconds * 30);
                }
                LogEvent($"🎬 تم تحميل {DetectedScenes.Count} مشهد برمجـي من scenes.json (المدة الكلية: {TotalDurationSeconds:F0}s)");
            }
            catch (Exception ex)
            {
                LogEvent($"⚠️ تعذر قراءة scenes.json: {ex.Message}");
            }
        }

        UpdateTimeDisplay();

        // 3. Load transcript.json
        var transcriptFile = Path.Combine(jobFolder, "transcript.json");
        if (File.Exists(transcriptFile))
        {
            try
            {
                var json = File.ReadAllText(transcriptFile);
                using var doc = JsonDocument.Parse(json);
                TranscriptSegments.Clear();
                if (doc.RootElement.TryGetProperty("segments", out var segs))
                {
                    foreach (var s in segs.EnumerateArray())
                    {
                        var seg = new TranscriptSegmentModel
                        {
                            StartSec = s.TryGetProperty("start_sec", out var st) ? st.GetDouble() : 0,
                            EndSec = s.TryGetProperty("end_sec", out var en) ? en.GetDouble() : 0,
                            Text = s.TryGetProperty("text", out var tx) ? tx.GetString() ?? "" : "",
                            Confidence = s.TryGetProperty("confidence", out var cf) ? cf.GetDouble() : 0.95
                        };
                        TranscriptSegments.Add(seg);
                    }
                }
                LogEvent($"💬 تم تحميل {TranscriptSegments.Count} مقطع تفريغ صوتي من transcript.json");
            }
            catch (Exception ex)
            {
                LogEvent($"⚠️ تعذر قراءة transcript.json: {ex.Message}");
            }
        }

        // 4. Load results/ code files recursively (including ProjectScripts/)
        var resultsDir = Path.Combine(jobFolder, "results");
        if (Directory.Exists(resultsDir))
        {
            var files = Directory.GetFiles(resultsDir, "*.*", SearchOption.AllDirectories)
                .Where(f => !f.EndsWith(".json", StringComparison.OrdinalIgnoreCase) &&
                            !f.EndsWith(".wav", StringComparison.OrdinalIgnoreCase) &&
                            !f.EndsWith(".mp4", StringComparison.OrdinalIgnoreCase))
                .ToArray();

            if (files.Length > 0)
            {
                ExtractedSnippets.Clear();
                foreach (var f in files)
                {
                    try
                    {
                        var relName = Path.GetRelativePath(resultsDir, f);
                        var content = File.ReadAllText(f);
                        var ext = Path.GetExtension(f).ToLowerInvariant();
                        var lang = ext switch
                        {
                            ".dart" => "Dart / Flutter",
                            ".cs" => "C# (.NET 9)",
                            ".py" => "Python 3",
                            ".ts" => "TypeScript",
                            ".js" => "JavaScript",
                            ".cpp" or ".h" => "C++",
                            _ => relName.Contains("Flutter", StringComparison.OrdinalIgnoreCase) || content.Contains("StatelessWidget") ? "Dart / Flutter" : "Source Code"
                        };
                        var snip = new ExtractedCodeSnippet
                        {
                            TargetFilePath = relName,
                            Language = lang,
                            TimestampSec = 0.0,
                            Confidence = 0.95,
                            CodeContent = content,
                            Explanation = $"ملف مسترجع من إطارات الفيديو ومصنف معمارياً: {relName}"
                        };
                        ExtractedSnippets.Add(snip);
                    }
                    catch { }
                }
                LogEvent($"💻 تم تحميل {ExtractedSnippets.Count} ملفات كود مستعادة من results/");
            }
        }

        // 5. Load keyframe annotated images
        var keyframesDir = Path.Combine(jobFolder, "keyframes");
        if (Directory.Exists(keyframesDir))
        {
            var kfs = Directory.GetFiles(keyframesDir, "annotated_*.png");
            if (kfs.Length == 0) kfs = Directory.GetFiles(keyframesDir, "scene_*.png");
            if (kfs.Length > 0)
            {
                CurrentFrameImagePath = kfs[0];
                LogEvent($"📸 تم العثور على {kfs.Length} لقطات شاشة معالجة ومحددة بواسطة OpenCV في keyframes/");
            }
        }

        if (DetectedScenes.Count > 0) SelectedScene = DetectedScenes[0];
        if (TranscriptSegments.Count > 0) SelectedTranscript = TranscriptSegments[0];
        if (ExtractedSnippets.Count > 0) SelectedSnippet = ExtractedSnippets[0];
    }

    private void LoadSampleData()
    {
        DetectedScenes.Clear();
        DetectedScenes.Add(new DetectedScene { SceneIndex = 1, TimestampSec = 0.0, CodeLikelihood = 0.95, IsCodeScene = true, SummaryText = "إنشاء كلاس Program.cs وضبط فضاء الأسماء" });
        DetectedScenes.Add(new DetectedScene { SceneIndex = 2, TimestampSec = 14.0, CodeLikelihood = 0.91, IsCodeScene = true, SummaryText = "دالة DataService ومعالجة المشاهد البصرية" });
        DetectedScenes.Add(new DetectedScene { SceneIndex = 3, TimestampSec = 28.0, CodeLikelihood = 0.97, IsCodeScene = true, SummaryText = "تشغيل النموذج وتجميع شجرة الحل النهائية" });

        TranscriptSegments.Clear();
        TranscriptSegments.Add(new TranscriptSegmentModel { StartSec = 0.0, EndSec = 12.0, Text = "في هذا الدرس نبدأ بإنشاء هيكل المشروع المكتوب بلغة C# وتجهيز نقطة الدخول Main.", Confidence = 0.95 });
        TranscriptSegments.Add(new TranscriptSegmentModel { StartSec = 13.0, EndSec = 26.0, Text = "نضيف دوال معالجة واستخراج البيانات بواسطة خوارزميات الرؤية الحاسوبية OpenCV وتصفية الإطارات.", Confidence = 0.92 });
        TranscriptSegments.Add(new TranscriptSegmentModel { StartSec = 27.0, EndSec = 38.0, Text = "نقوم بالتحقق من مخرجات الكود وبناء شجرة الملفات النهائية للتشغيل المباشر في Visual Studio.", Confidence = 0.97 });

        ExtractedSnippets.Clear();
        ExtractedSnippets.Add(new ExtractedCodeSnippet
        {
            TargetFilePath = "Program.cs",
            Language = "C# (.NET 9)",
            TimestampSec = 0.0,
            Confidence = 0.95,
            CodeContent = @"using System;
using System.Threading.Tasks;

namespace CodeVision.Reconstructed;

public static class Program
{
    public static async Task Main(string[] args)
    {
        Console.WriteLine(""=== CodeVision AI Pipeline Running ==="");
        var service = new DataService();
        await service.InitializeAsync();
    }
}",
            Explanation = "نقطة البداية الأساسية للتطبيق وتهيئة المحرك."
        });

        ExtractedSnippets.Add(new ExtractedCodeSnippet
        {
            TargetFilePath = "DataService.cs",
            Language = "C# (.NET 9)",
            TimestampSec = 14.0,
            Confidence = 0.91,
            CodeContent = @"using System;
using System.Threading.Tasks;

namespace CodeVision.Reconstructed;

public sealed class DataService
{
    public async Task InitializeAsync()
    {
        Console.WriteLine(""معالجة إطارات الكود عبر OpenCV وTesseract..."");
        await Task.Delay(100);
    }
}",
            Explanation = "فئة معالجة البيانات واستخراج المقاطع من الإطارات."
        });

        if (DetectedScenes.Count > 0) SelectedScene = DetectedScenes[0];
        if (TranscriptSegments.Count > 0) SelectedTranscript = TranscriptSegments[0];
        if (ExtractedSnippets.Count > 0) SelectedSnippet = ExtractedSnippets[0];

        UpdateTimeDisplay();
    }

    [RelayCommand]
    public async Task StartSimulationAsync()
    {
        if (IsSimulating) return;

        IsSimulating = true;
        _simCts = new CancellationTokenSource();
        var token = _simCts.Token;

        LogEvent($"▶ بدء محاكاة الاستخراج اللحظي (السرعة: {PlaybackSpeed:0.0}x)");

        try
        {
            while (!token.IsCancellationRequested && CurrentPositionSeconds < TotalDurationSeconds)
            {
                var step = 1.0 * PlaybackSpeed;
                CurrentPositionSeconds += step;
                CurrentFrameIndex = (int)(CurrentPositionSeconds * 30);
                UpdateTimeDisplay();

                // Check active scene based on time
                var matchingScene = DetectedScenes.FirstOrDefault(s => Math.Abs(s.TimestampSec - CurrentPositionSeconds) <= 2.5);
                if (matchingScene != null)
                {
                    SelectedScene = matchingScene;
                    CapturedScenesCount++;
                    CurrentActionStatus = $"🟢 [CAPTURED] مشهد كود #{matchingScene.SceneIndex} عند {matchingScene.TimestampFormatted} (ثقة: {matchingScene.ConfidencePercent})";
                    CurrentAlgorithm = "cv2.cvtColor(BGR2GRAY) + CLAHE + Canny Edges + OCR";
                    CurrentLibrary = "OpenCV 4.10 · Tesseract · AST Parser";
                    IsRoiDetected = true;
                    FrameDifferenceScore = 18.5;

                    RoiLeft = 25 + (matchingScene.SceneIndex % 3) * 10;
                    RoiTop = 20 + (matchingScene.SceneIndex % 2) * 8;
                    RoiWidth = 410 + (matchingScene.SceneIndex % 2) * 15;
                    RoiHeight = 250 - (matchingScene.SceneIndex % 2) * 10;
                    RoiCoordinates = $"X: {(int)RoiLeft}, Y: {(int)RoiTop}, W: {(int)RoiWidth}, H: {(int)RoiHeight}";

                    LogEvent($"🟢 [CAPTURED] مشهد #{matchingScene.SceneIndex} عند {matchingScene.TimestampFormatted} · ROI: [{RoiCoordinates}] · كود مكتشف بدقة {matchingScene.ConfidencePercent}");

                    var snip = ExtractedSnippets.FirstOrDefault(s => Math.Abs(s.TimestampSec - matchingScene.TimestampSec) <= 15.0);
                    if (snip != null) SelectedSnippet = snip;
                }
                else
                {
                    SkippedFramesCount++;
                    CurrentActionStatus = $"🟡 [SKIPPED] تجاوز إطار مكرر #{CurrentFrameIndex} (الفارق 1.2% < عتبة التغيير)";
                    CurrentAlgorithm = "cv2.compareHist + Frame Difference (SSIM Fast Skip)";
                    CurrentLibrary = "OpenCV 4.10 (cv2) VideoCapture";
                    FrameDifferenceScore = 1.2;

                    if (CurrentFrameIndex % 60 == 0)
                    {
                        LogEvent($"🟡 [SKIPPED] تجاوز إطارات مكررة (الفارق {FrameDifferenceScore:F1}% < 2.5%) لتسريع المعالجة");
                    }
                }

                var matchingTranscript = TranscriptSegments.FirstOrDefault(t => CurrentPositionSeconds >= t.StartSec && CurrentPositionSeconds <= t.EndSec);
                if (matchingTranscript != null && matchingTranscript != SelectedTranscript)
                {
                    SelectedTranscript = matchingTranscript;
                    var shortText = matchingTranscript.Text.Length > 45 ? matchingTranscript.Text.Substring(0, 45) + "…" : matchingTranscript.Text;
                    LogEvent($"🔊 [WHISPER] صوت متزامن: \"{shortText}\"");
                }

                int delayMs = (int)(250 / PlaybackSpeed);
                await Task.Delay(delayMs, token);
            }

            if (CurrentPositionSeconds >= TotalDurationSeconds)
            {
                LogEvent("✓ اكتملت محاكاة كافة إطارات الفيديو بنجاح.");
            }
        }
        catch (OperationCanceledException)
        {
            LogEvent("⏸ تم إيقاف المحاكاة مؤقتاً من قبل المستخدم.");
        }
        finally
        {
            IsSimulating = false;
        }
    }

    [RelayCommand]
    public void PauseSimulation()
    {
        _simCts?.Cancel();
        IsSimulating = false;
    }

    [RelayCommand]
    public void NextFrame()
    {
        CurrentPositionSeconds = Math.Min(TotalDurationSeconds, CurrentPositionSeconds + 2.0);
        CurrentFrameIndex = (int)(CurrentPositionSeconds * 30);
        UpdateTimeDisplay();

        var scene = DetectedScenes.FirstOrDefault(s => s.TimestampSec >= CurrentPositionSeconds) ?? DetectedScenes.LastOrDefault();
        if (scene != null)
        {
            SelectedScene = scene;
            LogEvent($"⏭ قفز إلى الإطار عند {scene.TimestampFormatted}");
        }
    }

    public void SeekToSeconds(double seconds)
    {
        CurrentPositionSeconds = Math.Clamp(seconds, 0, TotalDurationSeconds);
        CurrentFrameIndex = (int)(CurrentPositionSeconds * 30);
        UpdateTimeDisplay();

        var scene = DetectedScenes.FirstOrDefault(s => Math.Abs(s.TimestampSec - CurrentPositionSeconds) <= 2.5);
        if (scene != null) SelectedScene = scene;

        var trans = TranscriptSegments.FirstOrDefault(t => CurrentPositionSeconds >= t.StartSec && CurrentPositionSeconds <= t.EndSec);
        if (trans != null) SelectedTranscript = trans;

        LogEvent($"⏱ انتقال مباشر في الخط الزمني إلى: {TimeDisplay}");
    }

    private void UpdateTimeDisplay()
    {
        var cur = TimeSpan.FromSeconds(CurrentPositionSeconds);
        var tot = TimeSpan.FromSeconds(TotalDurationSeconds);
        TimeDisplay = $"{cur:mm\\:ss} / {tot:mm\\:ss}";
    }
}
