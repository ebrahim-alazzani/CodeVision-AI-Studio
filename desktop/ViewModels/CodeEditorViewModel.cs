using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;

namespace CodeVision.Desktop.ViewModels;

public partial class CodeEditorViewModel : ObservableObject
{
    public ObservableCollection<ExtractedCodeSnippet> Snippets { get; } = new();

    public string[] SupportedLanguages { get; } = new[]
    {
        "C#", "Python", "Dart / Flutter", "TypeScript", "JavaScript", "C++", "HTML/CSS", "SQL", "Rust", "Go"
    };

    [ObservableProperty]
    private ExtractedCodeSnippet? _selectedSnippet;

    [ObservableProperty]
    private string _currentCode = string.Empty;

    [ObservableProperty]
    private string _statusNotification = "المحرر جاهز للتعديل.";

    public CodeEditorViewModel()
    {
        LoadDefaultSnippet();
    }

    private void LoadDefaultSnippet()
    {
        var sample = new ExtractedCodeSnippet
        {
            TargetFilePath = "Program.cs",
            Language = "C#",
            TimestampSec = 14.5,
            Confidence = 0.96,
            CodeContent = @"// CodeVision Interactive Editor
using System;

namespace CodeVision.Reconstruction;

public static class EntryPoint
{
    public static void Main()
    {
        Console.WriteLine(""Ready to build project from video lessons."");
    }
}"
        };

        Snippets.Add(sample);
        SelectedSnippet = sample;
        CurrentCode = sample.CodeContent;
    }

    partial void OnSelectedSnippetChanged(ExtractedCodeSnippet? value)
    {
        if (value is not null)
        {
            CurrentCode = value.CodeContent;
            StatusNotification = $"تم تحميل: {value.TargetFilePath} ({value.Language})";
        }
    }

    [RelayCommand]
    public void SaveCurrentSnippet()
    {
        if (SelectedSnippet is not null)
        {
            SelectedSnippet.CodeContent = CurrentCode;
            SelectedSnippet.IsReviewed = true;
            StatusNotification = $"✓ تم حفظ التعديلات لـ {SelectedSnippet.TargetFilePath} في الذاكرة.";
        }
    }

    [RelayCommand]
    public void AddNewFile()
    {
        var newFile = new ExtractedCodeSnippet
        {
            TargetFilePath = $"NewFile_{Snippets.Count + 1}.cs",
            Language = "C#",
            Confidence = 1.0,
            CodeContent = "// New file created in CodeVision Studio\n"
        };
        Snippets.Add(newFile);
        SelectedSnippet = newFile;
        StatusNotification = $"تمت إضافة ملف جديد: {newFile.TargetFilePath}";
    }
}
