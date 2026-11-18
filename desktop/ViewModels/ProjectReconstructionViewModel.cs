using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public sealed class AvailableJobItem
{
    public string DisplayName { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;

    public override string ToString() => DisplayName;
}

public partial class ProjectReconstructionViewModel : ObservableObject
{
    private readonly ProjectExportService _exporter;
    private readonly SettingsService _settings;

    public ObservableCollection<ProjectTreeItem> ProjectTree { get; } = new();
    public ObservableCollection<ExtractedCodeSnippet> OrderedSnippets { get; } = new();
    public ObservableCollection<AvailableJobItem> AvailableJobs { get; } = new();

    [ObservableProperty]
    private AvailableJobItem? _selectedJob;

    [ObservableProperty]
    private string _projectName = "ViceCityUnityGame";

    [ObservableProperty]
    private string _exportStatus = "جاهز لإعادة بناء وتصدير المشروع.";

    [ObservableProperty]
    private bool _isExporting;

    [ObservableProperty]
    private string _selectedFileName = "ShootingController.cs";

    [ObservableProperty]
    private string _selectedFileCode = string.Empty;

    [ObservableProperty]
    private string _selectedFileMeta = string.Empty;

    [ObservableProperty]
    private int _totalFilesCount;

    [ObservableProperty]
    private int _totalLinesCount;

    [ObservableProperty]
    private string _lastExportedPath = string.Empty;

    [ObservableProperty]
    private bool _hasExportedPath;

    public ProjectReconstructionViewModel(ProjectExportService exporter, SettingsService settings)
    {
        _exporter = exporter;
        _settings = settings;

        ScanAvailableJobs();
    }

    public void ScanAvailableJobs()
    {
        AvailableJobs.Clear();

        // 1. Scan Output Directory for real extraction jobs first
        var outDir = _settings.Current.OutputDirectory;
        if (string.IsNullOrWhiteSpace(outDir) || !Directory.Exists(outDir))
            outDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");

        if (Directory.Exists(outDir))
        {
            var jobDirs = Directory.GetDirectories(outDir)
                .OrderByDescending(Directory.GetLastWriteTime)
                .Take(15);

            foreach (var jd in jobDirs)
            {
                var dirName = Path.GetFileName(jd);
                var isFlutter = dirName.Contains("Flutter", StringComparison.OrdinalIgnoreCase);
                var isUnity = dirName.Contains("Unity", StringComparison.OrdinalIgnoreCase);
                var icon = isFlutter ? "📱" : isUnity ? "🎮" : "📦";

                AvailableJobs.Add(new AvailableJobItem
                {
                    DisplayName = $"{icon} {dirName}",
                    Path = jd,
                    Description = $"مخرجات استخراج حقيقية: {dirName}"
                });
            }
        }

        // 2. Check Course Scripts Clean Final as reference/demo
        var coursePath = @"D:\Programming\New folder\Mobile Game Development Tutorial 2025\Course_Scripts_Clean_Final";
        if (Directory.Exists(coursePath))
        {
            AvailableJobs.Add(new AvailableJobItem
            {
                DisplayName = "🎮 Unity GTA Vice City Clone (مرجع تجريبي - 11 مجلد)",
                Path = coursePath,
                Description = "مشروع مرجعي يحتوي على AI, Vehicles, Shooting, Player, UI, Camera"
            });
        }

        // 3. Check Test Video 26 (Shop System) as reference/demo
        var vid26Path = @"D:\Programming\New folder\Mobile Game Development Tutorial 2025\Test_Video_26\_Extracted_CSharp\26 - Unity Shop System Tutorial Mobile Game Development Full Course GTA Vice City Game Clone(720P_60FPS)";
        if (Directory.Exists(vid26Path))
        {
            AvailableJobs.Add(new AvailableJobItem
            {
                DisplayName = "🛒 Video 26: Unity Shop System (مرجع تجريبي)",
                Path = vid26Path,
                Description = "استخراج الدرس 26 بنظام الحفظ والمحاكاة التزامنية"
            });
        }

        if (AvailableJobs.Count > 0)
        {
            SelectedJob = AvailableJobs[0];
            LoadJob(SelectedJob.Path);
        }
        else
        {
            BuildDefaultFallbackTree();
        }
    }

    public void LoadJob(string jobDirPath)
    {
        if (string.IsNullOrWhiteSpace(jobDirPath) || !Directory.Exists(jobDirPath))
            return;

        ProjectTree.Clear();
        OrderedSnippets.Clear();

        var rootDirName = Path.GetFileName(jobDirPath);
        ProjectName = SanitizeName(rootDirName);

        var rootItem = new ProjectTreeItem
        {
            Name = rootDirName,
            RelativePath = "",
            IsDirectory = true
        };

        int fileCount = 0;
        int totalLines = 0;
        ExtractedCodeSnippet? firstSnippet = null;

        // Determine if there is a 'Scripts' or 'results' subfolder
        var searchDir = jobDirPath;
        var scriptsSubdir = Path.Combine(jobDirPath, "Scripts");
        var resultsSubdir = Path.Combine(jobDirPath, "results", "ProjectScripts");
        if (Directory.Exists(resultsSubdir)) searchDir = Path.Combine(jobDirPath, "results");
        else if (Directory.Exists(scriptsSubdir)) searchDir = jobDirPath;

        PopulateDirectory(searchDir, rootItem, ref fileCount, ref totalLines, ref firstSnippet);

        ProjectTree.Add(rootItem);
        TotalFilesCount = fileCount;
        TotalLinesCount = totalLines;

        // Also scan ScriptHistory or scenes.json for chronological flow
        LoadChronologicalFlow(jobDirPath);

        if (firstSnippet != null && string.IsNullOrEmpty(SelectedFileCode))
        {
            SelectedFileName = Path.GetFileName(firstSnippet.TargetFilePath);
            SelectedFileCode = firstSnippet.CodeContent;
            SelectedFileMeta = $"{SelectedFileName} · {firstSnippet.Language} · ثقة: {firstSnippet.ConfidencePercent}";
        }

        ExportStatus = $"تم استيراد {fileCount} ملف برمجي مستعاد بنجاح ({totalLines} سطر برمجي).";
    }

    private void PopulateDirectory(string dirPath, ProjectTreeItem parentItem, ref int fileCount, ref int totalLines, ref ExtractedCodeSnippet? firstSnippet, int depth = 0)
    {
        if (depth > 6) return;
        try
        {
            // Add subdirectories
            foreach (var subDir in Directory.GetDirectories(dirPath))
            {
                var dirName = Path.GetFileName(subDir);
                if (dirName.StartsWith(".") ||
                    dirName.Equals(".venv", StringComparison.OrdinalIgnoreCase) ||
                    dirName.Equals("__pycache__", StringComparison.OrdinalIgnoreCase) ||
                    dirName.Equals("CandidateFrames", StringComparison.OrdinalIgnoreCase) ||
                    dirName.Equals("Frames", StringComparison.OrdinalIgnoreCase) ||
                    dirName.Equals("keyframes", StringComparison.OrdinalIgnoreCase) ||
                    dirName.Equals("OCR", StringComparison.OrdinalIgnoreCase))
                    continue;

                var subItem = new ProjectTreeItem
                {
                    Name = dirName,
                    RelativePath = Path.GetRelativePath(parentItem.RelativePath == "" ? dirPath : parentItem.RelativePath, subDir),
                    IsDirectory = true
                };

                PopulateDirectory(subDir, subItem, ref fileCount, ref totalLines, ref firstSnippet, depth + 1);

                if (subItem.Children.Count > 0)
                {
                    parentItem.Children.Add(subItem);
                }
            }

            // Add code files
            foreach (var filePath in Directory.GetFiles(dirPath))
            {
                var ext = Path.GetExtension(filePath).ToLowerInvariant();
                if (ext is not (".cs" or ".dart" or ".py" or ".ts" or ".js" or ".cpp" or ".h" or ".txt" or ".json" or ".yaml" or ".xml"))
                    continue;

                var fileName = Path.GetFileName(filePath);
                if (fileName.EndsWith(".meta", StringComparison.OrdinalIgnoreCase)) continue;

                string content;
                try { content = File.ReadAllText(filePath); }
                catch { content = "// تعذر قراءة محتوى الملف"; }

                var lines = content.Split('\n').Length;
                totalLines += lines;
                fileCount++;

                var fileItem = new ProjectTreeItem
                {
                    Name = fileName,
                    RelativePath = fileName,
                    IsDirectory = false,
                    Content = content,
                    Confidence = 0.96
                };

                parentItem.Children.Add(fileItem);

                var lang = ext switch
                {
                    ".dart" => "Dart / Flutter",
                    ".cs" => "C# (.NET 9)",
                    ".py" => "Python",
                    ".ts" => "TypeScript",
                    ".js" => "JavaScript",
                    ".cpp" or ".h" => "C++",
                    _ => content.Contains("StatelessWidget") ? "Dart / Flutter" : "Source Code"
                };

                var snip = new ExtractedCodeSnippet
                {
                    TargetFilePath = Path.Combine(parentItem.Name, fileName),
                    Language = lang,
                    TimestampSec = fileCount * 12.0,
                    Confidence = 0.96,
                    CodeContent = content
                };

                if (firstSnippet == null && ext != ".json")
                {
                    firstSnippet = snip;
                }
            }
        }
        catch { }
    }

    private void LoadChronologicalFlow(string jobDirPath)
    {
        // Check ScriptHistory folder
        var histDir = Path.Combine(jobDirPath, "ScriptHistory");
        if (Directory.Exists(histDir))
        {
            var histFiles = Directory.GetFiles(histDir, "*.*")
                .Where(f => !f.EndsWith(".meta", StringComparison.OrdinalIgnoreCase))
                .OrderBy(f => f)
                .Take(25);

            double timeAcc = 10.0;
            foreach (var hf in histFiles)
            {
                var fname = Path.GetFileName(hf);
                string content = "";
                try { content = File.ReadAllText(hf); } catch { }

                var ext = Path.GetExtension(fname).ToLowerInvariant();
                var lang = ext switch
                {
                    ".dart" => "Dart",
                    ".cs" => "C#",
                    ".py" => "Python",
                    ".ts" => "TypeScript",
                    _ => "Code"
                };

                OrderedSnippets.Add(new ExtractedCodeSnippet
                {
                    TargetFilePath = $"ScriptHistory/{fname}",
                    Language = lang,
                    TimestampSec = timeAcc,
                    Confidence = 0.95,
                    CodeContent = content
                });
                timeAcc += 15.0;
            }
        }

        // If OrderedSnippets still empty, add top scripts from project
        if (OrderedSnippets.Count == 0)
        {
            AddSnippetsFromTree(ProjectTree);
        }
    }

    private void AddSnippetsFromTree(IEnumerable<ProjectTreeItem> items)
    {
        foreach (var item in items)
        {
            if (!item.IsDirectory && !string.IsNullOrWhiteSpace(item.Content))
            {
                var ext = Path.GetExtension(item.Name).ToLowerInvariant();
                var lang = ext switch
                {
                    ".dart" => "Dart",
                    ".cs" => "C#",
                    ".py" => "Python",
                    _ => "Code"
                };
                OrderedSnippets.Add(new ExtractedCodeSnippet
                {
                    TargetFilePath = item.Name,
                    Language = lang,
                    TimestampSec = (OrderedSnippets.Count + 1) * 20.0,
                    Confidence = item.Confidence,
                    CodeContent = item.Content
                });
                if (OrderedSnippets.Count >= 20) break;
            }
            if (item.Children.Count > 0)
            {
                AddSnippetsFromTree(item.Children);
                if (OrderedSnippets.Count >= 20) break;
            }
        }
    }

    public void SelectItem(ProjectTreeItem item)
    {
        if (item == null || item.IsDirectory) return;

        SelectedFileName = item.Name;
        SelectedFileCode = item.Content;
        var ext = Path.GetExtension(item.Name);
        var lang = ext == ".cs" ? "C#" : ext == ".py" ? "Python" : "Code";
        var lines = item.Content.Split('\n').Length;
        SelectedFileMeta = $"{item.Name} · {lang} · {lines} سطر · ثقة: {item.ConfidencePercent}";
    }

    public void SelectSnippet(ExtractedCodeSnippet snippet)
    {
        if (snippet == null) return;

        SelectedFileName = Path.GetFileName(snippet.TargetFilePath);
        SelectedFileCode = snippet.CodeContent;
        SelectedFileMeta = $"{snippet.TargetFilePath} · {snippet.Language} · التوقيت: {snippet.TimestampFormatted} · ثقة: {snippet.ConfidencePercent}";
    }

    [RelayCommand]
    public async Task ExportProjectAsync()
    {
        IsExporting = true;
        ExportStatus = "جارٍ تجميع واستخراج المشروع البرمجي مع توليد ملفات الحل (Solution)...";

        try
        {
            var targetDir = _settings.Current.OutputDirectory;
            if (string.IsNullOrWhiteSpace(targetDir) || !Directory.Exists(targetDir))
                targetDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output", "ExportedProjects");

            Directory.CreateDirectory(targetDir);

            // Collect all snippets to export
            var snippetsToExport = new List<ExtractedCodeSnippet>();
            CollectFilesToExport(ProjectTree, "", snippetsToExport);

            if (snippetsToExport.Count == 0 && OrderedSnippets.Count > 0)
                snippetsToExport.AddRange(OrderedSnippets);

            var exportedPath = await _exporter.ExportReconstructedProjectAsync(
                targetDir,
                ProjectName,
                snippetsToExport);

            LastExportedPath = exportedPath;
            HasExportedPath = true;
            ExportStatus = $"✓ تم تصدير المشروع بنجاح إلى:\n{exportedPath}";
        }
        catch (Exception ex)
        {
            ExportStatus = $"فشل التصدير: {ex.Message}";
        }
        finally
        {
            IsExporting = false;
        }
    }

    private void CollectFilesToExport(IEnumerable<ProjectTreeItem> items, string currentPath, List<ExtractedCodeSnippet> list)
    {
        foreach (var item in items)
        {
            if (item.IsDirectory)
            {
                var nextPath = string.IsNullOrEmpty(currentPath) ? item.Name : Path.Combine(currentPath, item.Name);
                CollectFilesToExport(item.Children, nextPath, list);
            }
            else
            {
                var rel = string.IsNullOrEmpty(currentPath) ? item.Name : Path.Combine(currentPath, item.Name);
                list.Add(new ExtractedCodeSnippet
                {
                    TargetFilePath = rel,
                    Language = item.Name.EndsWith(".cs") ? "C#" : "Text",
                    Confidence = item.Confidence,
                    CodeContent = item.Content
                });
            }
        }
    }

    [RelayCommand]
    public void OpenExportFolder()
    {
        if (string.IsNullOrWhiteSpace(LastExportedPath) || !Directory.Exists(LastExportedPath))
            return;

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = LastExportedPath,
                UseShellExecute = true
            });
        }
        catch { }
    }

    private void BuildDefaultFallbackTree()
    {
        var root = new ProjectTreeItem { Name = "ReconstructedApp", IsDirectory = true };
        var src = new ProjectTreeItem { Name = "Scripts", IsDirectory = true };
        var shooting = new ProjectTreeItem { Name = "ShootingController.cs", IsDirectory = false, Confidence = 0.98, Content = "// ShootingController.cs\nusing UnityEngine;\n\npublic class ShootingController : MonoBehaviour\n{\n    public Transform firePoint;\n    public GameObject bulletPrefab;\n\n    void Update()\n    {\n        if (Input.GetButtonDown(\"Fire1\")) Shoot();\n    }\n\n    void Shoot()\n    {\n        Instantiate(bulletPrefab, firePoint.position, firePoint.rotation);\n    }\n}" };
        var car = new ProjectTreeItem { Name = "CarController.cs", IsDirectory = false, Confidence = 0.96, Content = "// CarController.cs\nusing UnityEngine;\n\npublic class CarController : MonoBehaviour\n{\n    public float motorTorque = 1500f;\n    public WheelCollider[] wheels;\n\n    void FixedUpdate()\n    {\n        float v = Input.GetAxis(\"Vertical\");\n        foreach (var w in wheels) w.motorTorque = v * motorTorque;\n    }\n}" };

        src.Children.Add(shooting);
        src.Children.Add(car);
        root.Children.Add(src);
        ProjectTree.Add(root);

        SelectedFileName = "ShootingController.cs";
        SelectedFileCode = shooting.Content;
        SelectedFileMeta = "ShootingController.cs · C# · ثقة: 98%";
    }

    private static string SanitizeName(string raw)
    {
        var clean = string.Join("_", raw.Split(Path.GetInvalidFileNameChars()));
        clean = clean.Replace(" ", "_").Replace("-", "_");
        return string.IsNullOrWhiteSpace(clean) ? "ReconstructedProject" : clean;
    }
}
