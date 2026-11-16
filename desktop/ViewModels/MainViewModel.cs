using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.ViewModels;

public partial class MainViewModel : ObservableObject
{
    private readonly SettingsService _settings;
    private readonly LoggingService _logger;

    [ObservableProperty]
    private string _currentPageTag = "library";

    [ObservableProperty]
    private string _pageTitle = "المكتبة وإدارة المشاريع";

    [ObservableProperty]
    private string _statusText = "CodeVision Studio جاهز للعمل.";

    [ObservableProperty]
    private bool _isDarkTheme = true;

    public LibraryViewModel Library { get; }
    public ExtractionReviewViewModel ExtractionReview { get; }
    public CodeEditorViewModel CodeEditor { get; }
    public ProjectReconstructionViewModel ProjectReconstruction { get; }
    public TrainingLabViewModel TrainingLab { get; }
    public ModelsManagerViewModel ModelsManager { get; }
    public SettingsViewModel Settings { get; }

    public MainViewModel(
        SettingsService settings,
        LoggingService logger,
        LibraryViewModel library,
        ExtractionReviewViewModel extractionReview,
        CodeEditorViewModel codeEditor,
        ProjectReconstructionViewModel projectReconstruction,
        TrainingLabViewModel trainingLab,
        ModelsManagerViewModel modelsManager,
        SettingsViewModel settingsVm)
    {
        _settings = settings;
        _logger = logger;
        Library = library;
        ExtractionReview = extractionReview;
        CodeEditor = codeEditor;
        ProjectReconstruction = projectReconstruction;
        TrainingLab = trainingLab;
        ModelsManager = modelsManager;
        Settings = settingsVm;

        IsDarkTheme = _settings.Current.Theme == "Dark";
    }

    [RelayCommand]
    public void Navigate(string tag)
    {
        CurrentPageTag = tag;
        PageTitle = tag switch
        {
            "library" => "المكتبة والمشاريع المستوردة",
            "review" => "الاستخراج والمراجعة الزمنية والأدلة",
            "editor" => "محرر الشيفرة والملفات",
            "reconstruction" => "إعادة بناء شجرة المشروع والتصدير",
            "training" => "مختبر التدريب (Training Lab)",
            "models" => "إدارة النماذج والبيانات",
            "settings" => "الإعدادات والسجلات والتشخيص",
            _ => "CodeVision Studio"
        };
    }

    [RelayCommand]
    public void ToggleTheme()
    {
        IsDarkTheme = !IsDarkTheme;
        _settings.Current.Theme = IsDarkTheme ? "Dark" : "Light";
        _settings.SaveSettings(_settings.Current);
    }
}
