using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Imaging;
using Microsoft.Extensions.DependencyInjection;
using CodeVision.Desktop.ViewModels;
using CodeVision.Desktop.Views;
using CodeVision.Desktop.Services;
using CodeVision.Desktop.Models;
using WinRT.Interop;
using Microsoft.UI;
using Microsoft.UI.Windowing;

namespace CodeVision.Desktop;

public sealed partial class MainWindow : Window
{
    private readonly IServiceProvider _services;
    private readonly MainViewModel _mainViewModel;
    private AppWindow? _appWindow;

    public MainWindow() : this(App.Services, App.Services.GetRequiredService<MainViewModel>())
    {
    }

    public MainWindow(IServiceProvider services, MainViewModel mainViewModel)
    {
        InitializeComponent();
        _services = services;
        _mainViewModel = mainViewModel;

        Title = "CodeVision Studio · AI Code Reconstruction (Cyber Edition)";

        // Configure seamless TitleBar with custom caption buttons
        SetupTitleBar();

        // Set initial theme
        ApplyTheme(_mainViewModel.IsDarkTheme);

        // Navigate to Dashboard initially
        NavigateToPage("dashboard");

        if (Environment.GetCommandLineArgs().Any(a => a.Equals("--capture-screenshots", StringComparison.OrdinalIgnoreCase)))
        {
            this.DispatcherQueue.TryEnqueue(async () =>
            {
                await Task.Delay(2000);
                await CaptureAllScreenshotsAsync();
                Environment.Exit(0);
            });
        }
    }

    private void SetupTitleBar()
    {
        try
        {
            ExtendsContentIntoTitleBar = true;
            SetTitleBar(AppTitleBar);

            var hwnd = WindowNative.GetWindowHandle(this);
            var windowId = Win32Interop.GetWindowIdFromWindow(hwnd);
            _appWindow = AppWindow.GetFromWindowId(windowId);

            if (_appWindow != null && AppWindowTitleBar.IsCustomizationSupported())
            {
                var titleBar = _appWindow.TitleBar;
                titleBar.ExtendsContentIntoTitleBar = true;
                UpdateTitleBarTheme(_mainViewModel.IsDarkTheme);
            }
        }
        catch
        {
            // Fallback for older builds
        }
    }

    private void UpdateTitleBarTheme(bool isDark)
    {
        if (_appWindow != null && AppWindowTitleBar.IsCustomizationSupported())
        {
            var titleBar = _appWindow.TitleBar;

            // Transparent background for seamless glass look
            titleBar.ButtonBackgroundColor = Windows.UI.Color.FromArgb(0, 0, 0, 0);
            titleBar.ButtonInactiveBackgroundColor = Windows.UI.Color.FromArgb(0, 0, 0, 0);

            // Button foreground icons (white/cyan in dark, slate in light)
            titleBar.ButtonForegroundColor = isDark
                ? Windows.UI.Color.FromArgb(255, 241, 239, 234)
                : Windows.UI.Color.FromArgb(255, 15, 23, 42);

            titleBar.ButtonInactiveForegroundColor = isDark
                ? Windows.UI.Color.FromArgb(160, 148, 163, 184)
                : Windows.UI.Color.FromArgb(160, 100, 116, 139);

            // Hover effects with Halvo cyan glow
            titleBar.ButtonHoverBackgroundColor = isDark
                ? Windows.UI.Color.FromArgb(40, 95, 216, 196)
                : Windows.UI.Color.FromArgb(40, 14, 165, 233);

            titleBar.ButtonHoverForegroundColor = Windows.UI.Color.FromArgb(255, 95, 216, 196);
            titleBar.ButtonPressedBackgroundColor = Windows.UI.Color.FromArgb(80, 95, 216, 196);
        }
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.IsSettingsSelected)
        {
            NavigateToPage("settings");
            return;
        }

        if (args.SelectedItemContainer is NavigationViewItem selectedItem && selectedItem.Tag is string tag)
        {
            NavigateToPage(tag);
        }
    }

    public void NavigateToPage(string tag)
    {
        switch (tag.ToLowerInvariant())
        {
            case "dashboard":
                var dashPage = _services.GetRequiredService<DashboardPage>();
                dashPage.Initialize(
                    _services.GetRequiredService<ExtractionReviewViewModel>(),
                    _services.GetRequiredService<LibraryViewModel>(),
                    _services.GetRequiredService<LoggingService>());
                ContentFrame.Content = dashPage;
                break;

            case "library":
                var libPage = _services.GetRequiredService<LibraryPage>();
                libPage.Initialize(_services.GetRequiredService<LibraryViewModel>());
                ContentFrame.Content = libPage;
                break;

            case "review":
                var reviewPage = _services.GetRequiredService<ExtractionReviewPage>();
                reviewPage.Initialize(_services.GetRequiredService<ExtractionReviewViewModel>());
                ContentFrame.Content = reviewPage;
                break;

            case "editor":
                var editorPage = _services.GetRequiredService<CodeEditorPage>();
                editorPage.Initialize(_services.GetRequiredService<CodeEditorViewModel>());
                ContentFrame.Content = editorPage;
                break;

            case "reconstruct":
                var reconPage = _services.GetRequiredService<ProjectReconstructionPage>();
                reconPage.Initialize(_services.GetRequiredService<ProjectReconstructionViewModel>());
                ContentFrame.Content = reconPage;
                break;

            case "training":
                var trainPage = _services.GetRequiredService<TrainingLabPage>();
                trainPage.Initialize(_services.GetRequiredService<TrainingLabViewModel>());
                ContentFrame.Content = trainPage;
                break;

            case "models":
                var modelsPage = _services.GetRequiredService<ModelsManagerPage>();
                modelsPage.Initialize(_services.GetRequiredService<ModelsManagerViewModel>());
                ContentFrame.Content = modelsPage;
                break;

            case "settings":
                var setPage = _services.GetRequiredService<SettingsPage>();
                setPage.Initialize(_services.GetRequiredService<SettingsViewModel>());
                ContentFrame.Content = setPage;
                break;
        }

        // Sync NavView selection cleanly
        var targetItem = NavView.MenuItems.OfType<NavigationViewItem>().FirstOrDefault(i => i.Tag?.ToString() == tag);
        if (targetItem is not null && (NavView.SelectedItem as NavigationViewItem) != targetItem)
        {
            NavView.SelectedItem = targetItem;
        }
    }

    public void NavigateToReviewWithVideo(VideoItem video)
    {
        var reviewVm = _services.GetRequiredService<ExtractionReviewViewModel>();
        reviewVm.LoadFromVideo(video);
        var reviewPage = _services.GetRequiredService<ExtractionReviewPage>();
        reviewPage.Initialize(reviewVm);
        ContentFrame.Content = reviewPage;

        var targetItem = NavView.MenuItems.OfType<NavigationViewItem>().FirstOrDefault(i => i.Tag?.ToString() == "review");
        if (targetItem is not null)
        {
            NavView.SelectedItem = targetItem;
        }
    }

    private async void BtnNewExtraction_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new AddVideoDialog
        {
            XamlRoot = ContentFrame.XamlRoot
        };
        var result = await dialog.ShowAsync();
        var paths = dialog.SelectedVideoPaths;

        if ((result == ContentDialogResult.Primary || result == ContentDialogResult.Secondary) && paths.Count > 0)
        {
            var libVm = _services.GetRequiredService<LibraryViewModel>();
            libVm.AddVideos(paths);
            NavigateToPage("library");

            if (result == ContentDialogResult.Primary && dialog.StartImmediately)
            {
                if (paths.Count == 1)
                {
                    await libVm.ExtractSelectedAsync();
                }
                else
                {
                    await libVm.ExtractAllAsync();
                }
            }
        }
    }

    private async void BtnLiveLogs_Click(object sender, RoutedEventArgs e)
    {
        var logger = _services.GetRequiredService<LoggingService>();
        var dialog = new DiagnosticsDialog(logger)
        {
            XamlRoot = ContentFrame.XamlRoot
        };
        await dialog.ShowAsync();
    }

    private void ThemeToggleBtn_Click(object sender, RoutedEventArgs e)
    {
        _mainViewModel.ToggleTheme();
        ApplyTheme(_mainViewModel.IsDarkTheme);
    }

    private void ApplyTheme(bool isDark)
    {
        if (Content is FrameworkElement root)
        {
            root.RequestedTheme = isDark ? ElementTheme.Dark : ElementTheme.Light;
        }

        // Switch to CodeVision dedicated Cyber AI backgrounds
        try
        {
            var uri = isDark
                ? new Uri("ms-appx:///Assets/codevision_cyber_bg_dark.png")
                : new Uri("ms-appx:///Assets/codevision_cyber_bg_light.png");
            HalvoBackgroundImage.Source = new BitmapImage(uri);
        }
        catch
        {
            // Graceful fallback
        }

        // Update TitleBar caption button colors
        UpdateTitleBarTheme(isDark);

        ThemeToggleBtn.Content = isDark ? "☀" : "◐";
    }

    private async void BtnCaptureScreenshots_Click(object sender, RoutedEventArgs e)
    {
        BtnCaptureScreenshots.IsEnabled = false;
        try
        {
            var count = await CaptureAllScreenshotsAsync();
            var dialog = new ContentDialog
            {
                XamlRoot = this.Content.XamlRoot,
                Title = "✓ تم التقاط لقطات الواجهات الحية",
                Content = $"تم التقاط {count} لقطات حية للواجهات وحفظها بنجاح في:\nE:\\New folder (3)\\CodeVisionPhase1\\docs\\images",
                CloseButtonText = "إغلاق"
            };
            await dialog.ShowAsync();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine(ex);
        }
        finally
        {
            BtnCaptureScreenshots.IsEnabled = true;
        }
    }

    public async Task<int> CaptureAllScreenshotsAsync()
    {
        var targetDir = @"E:\New folder (3)\CodeVisionPhase1\docs\images";
        System.IO.Directory.CreateDirectory(targetDir);

        var pages = new[]
        {
            ("dashboard", "live_ui_dashboard.png"),
            ("review", "live_ui_simulation.png"),
            ("reconstruct", "live_ui_reconstruction.png"),
            ("training", "live_ui_training.png"),
            ("models", "live_ui_models.png")
        };

        int count = 0;
        foreach (var (tag, fileName) in pages)
        {
            NavigateToPage(tag);
            await Task.Delay(1200);

            try
            {
                var rtb = new RenderTargetBitmap();
                await rtb.RenderAsync(this.Content);
                var pixelBuffer = await rtb.GetPixelsAsync();
                var width = (uint)rtb.PixelWidth;
                var height = (uint)rtb.PixelHeight;

                if (width > 0 && height > 0)
                {
                    var outPath = System.IO.Path.Combine(targetDir, fileName);
                    using var fs = new System.IO.FileStream(outPath, System.IO.FileMode.Create);
                    var ras = System.IO.WindowsRuntimeStreamExtensions.AsRandomAccessStream(fs);
                    var encoder = await Windows.Graphics.Imaging.BitmapEncoder.CreateAsync(Windows.Graphics.Imaging.BitmapEncoder.PngEncoderId, ras);
                    
                    var reader = Windows.Storage.Streams.DataReader.FromBuffer(pixelBuffer);
                    var bytes = new byte[pixelBuffer.Length];
                    reader.ReadBytes(bytes);

                    encoder.SetPixelData(
                        Windows.Graphics.Imaging.BitmapPixelFormat.Bgra8,
                        Windows.Graphics.Imaging.BitmapAlphaMode.Premultiplied,
                        width,
                        height,
                        96,
                        96,
                        bytes);
                    await encoder.FlushAsync();
                    count++;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error capturing {tag}: {ex.Message}");
            }
        }

        NavigateToPage("dashboard");
        return count;
    }
}
