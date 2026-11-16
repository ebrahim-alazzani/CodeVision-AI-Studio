using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public partial class ModelsManagerViewModel : ObservableObject
{
    private readonly TrainingLabService _trainingLab;
    private readonly SettingsService _settings;

    public ObservableCollection<ModelInfo> Models { get; } = new();

    [ObservableProperty]
    private ModelInfo? _selectedModel;

    [ObservableProperty]
    private string _status = "إدارة النماذج والبيانات جاهزة.";

    public ModelsManagerViewModel(TrainingLabService trainingLab, SettingsService settings)
    {
        _trainingLab = trainingLab;
        _settings = settings;
        LoadModels();
    }

    public void LoadModels()
    {
        Models.Clear();
        var list = _trainingLab.GetInstalledModels();
        foreach (var m in list) Models.Add(m);

        SelectedModel = Models.FirstOrDefault(m => m.IsActiveInRuntime) ?? Models.FirstOrDefault();
    }

    [RelayCommand]
    public void SetActiveModel()
    {
        if (SelectedModel is not null)
        {
            foreach (var m in Models) m.IsActiveInRuntime = (m.Id == SelectedModel.Id);
            _settings.Current.ActiveModelId = SelectedModel.Id;
            _settings.SaveSettings(_settings.Current);
            Status = $"✓ النموذج النشط في Runtime الآن: {SelectedModel.Name}";
        }
    }
}
