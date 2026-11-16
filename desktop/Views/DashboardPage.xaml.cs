using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.Views;

public sealed partial class DashboardPage : Page
{
    private ExtractionReviewViewModel? _reviewViewModel;
    private LibraryViewModel? _libraryViewModel;
    private LoggingService? _logger;

    public DashboardPage()
    {
        InitializeComponent();
    }

    public void Initialize(ExtractionReviewViewModel reviewViewModel, LibraryViewModel libraryViewModel, LoggingService logger)
    {
        _reviewViewModel = reviewViewModel;
        _libraryViewModel = libraryViewModel;
        _logger = logger;

        UpdateMetrics();
    }

    private void UpdateMetrics()
    {
        if (_reviewViewModel != null)
        {
            ScenesCountMetric.Text = $"{_reviewViewModel.DetectedScenes.Count} مشهد برمجـي";
            FilesCountMetric.Text = $"{_reviewViewModel.ExtractedSnippets.Count} ملف كـود";
        }
    }

    private async void BtnNewSingleVideo_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new AddVideoDialog
        {
            XamlRoot = this.XamlRoot
        };
        var res = await dialog.ShowAsync();
        if ((res == ContentDialogResult.Primary || res == ContentDialogResult.Secondary) && dialog.SelectedVideoPaths.Count > 0)
        {
            _libraryViewModel?.AddVideos(dialog.SelectedVideoPaths);
            if (App.MainWindow is MainWindow mw)
            {
                mw.NavigateToPage("library");
            }
            if (res == ContentDialogResult.Primary && dialog.StartImmediately && _libraryViewModel != null)
            {
                await _libraryViewModel.ExtractSelectedAsync();
            }
        }
    }

    private async void BtnNewBatchVideos_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new AddVideoDialog
        {
            XamlRoot = this.XamlRoot
        };
        // Set mode to batch
        dialog.SetBatchMode(true);

        var res = await dialog.ShowAsync();
        if ((res == ContentDialogResult.Primary || res == ContentDialogResult.Secondary) && dialog.SelectedVideoPaths.Count > 0)
        {
            _libraryViewModel?.AddVideos(dialog.SelectedVideoPaths);
            if (App.MainWindow is MainWindow mw)
            {
                mw.NavigateToPage("library");
            }
            if (res == ContentDialogResult.Primary && dialog.StartImmediately && _libraryViewModel != null)
            {
                await _libraryViewModel.ExtractAllAsync();
            }
        }
    }

    private async void BtnLogs_Click(object sender, RoutedEventArgs e)
    {
        if (_logger != null)
        {
            var dialog = new DiagnosticsDialog(_logger)
            {
                XamlRoot = this.XamlRoot
            };
            await dialog.ShowAsync();
        }
    }

    private void CardStudio_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("review");
    }

    private void CardLibrary_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("library");
    }

    private void CardEditor_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("editor");
    }

    private void CardReconstruct_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("reconstruct");
    }

    private void CardTraining_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("training");
    }

    private void CardModels_PointerPressed(object sender, Microsoft.UI.Xaml.Input.PointerRoutedEventArgs e)
    {
        (App.MainWindow as MainWindow)?.NavigateToPage("models");
    }
}
