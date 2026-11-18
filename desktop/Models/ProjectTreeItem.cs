using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;

namespace CodeVision.Desktop.Models;

public partial class ProjectTreeItem : ObservableObject
{
    [ObservableProperty]
    private string _name = string.Empty;

    [ObservableProperty]
    private string _relativePath = string.Empty;

    [ObservableProperty]
    private bool _isDirectory;

    [ObservableProperty]
    private string _content = string.Empty;

    [ObservableProperty]
    private double _confidence = 1.0;

    public string ConfidencePercent => $"{Math.Round(Confidence * 100, 1)}%";

    public string IconGlyph => IsDirectory ? "\uE8B7" : "\uE943";

    public override string ToString() => Name;

    public ObservableCollection<ProjectTreeItem> Children { get; } = new();
}
