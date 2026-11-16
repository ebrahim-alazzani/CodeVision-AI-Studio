using System.IO;
using Microsoft.UI.Xaml;
using Microsoft.Extensions.DependencyInjection;
using CodeVision.Desktop.Services;
using CodeVision.Desktop.ViewModels;
using CodeVision.Desktop.Views;

namespace CodeVision.Desktop;

public partial class App : Application
{
    public static Window MainWindow { get; private set; } = null!;
    public static IServiceProvider Services { get; private set; } = null!;

    public static void RunOnUIThread(Action action)
    {
        if (MainWindow?.DispatcherQueue is { } queue)
        {
            if (queue.HasThreadAccess)
            {
                action();
            }
            else
            {
                queue.TryEnqueue(() => action());
            }
        }
        else
        {
            action();
        }
    }

    public App()
    {
        InitializeComponent();
        Services = ConfigureServices();

        UnhandledException += (s, e) =>
        {
            try
            {
                var logPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "startup_error.log");
                File.AppendAllText(logPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {e.Message}\n{e.Exception}\n");
            }
            catch { }
        };
    }

    private static IServiceProvider ConfigureServices()
    {
        var services = new ServiceCollection();

        // Core Services
        services.AddSingleton<SettingsService>();
        services.AddSingleton<LoggingService>();
        services.AddSingleton<PythonEngineService>();
        services.AddSingleton<ExtractionService>();
        services.AddSingleton<TrainingLabService>();
        services.AddSingleton<ProjectExportService>();

        // ViewModels
        services.AddSingleton<MainViewModel>();
        services.AddSingleton<LibraryViewModel>();
        services.AddSingleton<ExtractionReviewViewModel>();
        services.AddSingleton<CodeEditorViewModel>();
        services.AddSingleton<ProjectReconstructionViewModel>();
        services.AddSingleton<TrainingLabViewModel>();
        services.AddSingleton<ModelsManagerViewModel>();
        services.AddSingleton<SettingsViewModel>();

        // Views
        services.AddTransient<DashboardPage>();
        services.AddTransient<LibraryPage>();
        services.AddTransient<ExtractionReviewPage>();
        services.AddTransient<CodeEditorPage>();
        services.AddTransient<ProjectReconstructionPage>();
        services.AddTransient<TrainingLabPage>();
        services.AddTransient<ModelsManagerPage>();
        services.AddTransient<SettingsPage>();

        services.AddSingleton<MainWindow>();

        return services.BuildServiceProvider();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        MainWindow = Services.GetRequiredService<MainWindow>();
        MainWindow.Activate();
    }
}
