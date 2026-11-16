using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.Views;

public sealed partial class LibraryPage : Page
{
    private LibraryViewModel? _viewModel;

    public LibraryPage()
    {
        InitializeComponent();
    }

    public void Initialize(LibraryViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = _viewModel;
        VideosListView.ItemsSource = _viewModel.Videos;

        _viewModel.PropertyChanged += (s, e) =>
        {
            DispatcherQueue.TryEnqueue(() =>
            {
                if (e.PropertyName == nameof(LibraryViewModel.StatusMessage))
                {
                    StatusLabel.Text = _viewModel.StatusMessage;
                }
                else if (e.PropertyName == nameof(LibraryViewModel.IsBatchActive))
                {
                    BatchStatusBanner.Visibility = _viewModel.IsBatchActive ? Visibility.Visible : Visibility.Collapsed;
                }
                else if (e.PropertyName == nameof(LibraryViewModel.BatchProgressPercentage))
                {
                    BatchTotalProgress.Value = _viewModel.BatchProgressPercentage;
                    BatchPercentText.Text = $"{_viewModel.BatchProgressPercentage}%";
                }
                else if (e.PropertyName == nameof(LibraryViewModel.BatchCurrentIndex))
                {
                    BatchTitleText.Text = $"جاري معالجة الحزمة: ({_viewModel.BatchCurrentIndex} من {_viewModel.BatchTotalCount})…";
                }
            });
        };

        UpdateCountLabel();
        _viewModel.Videos.CollectionChanged += (s, e) => DispatcherQueue.TryEnqueue(UpdateCountLabel);
    }

    private void UpdateCountLabel()
    {
        if (_viewModel != null)
        {
            CountLabel.Text = $"{_viewModel.Videos.Count} فيديوهات في القائمة";
        }
    }

    private async void AddVideosBtn_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new AddVideoDialog
        {
            XamlRoot = this.XamlRoot
        };
        var res = await dialog.ShowAsync();
        if ((res == ContentDialogResult.Primary || res == ContentDialogResult.Secondary) && dialog.SelectedVideoPaths.Count > 0)
        {
            _viewModel?.AddVideos(dialog.SelectedVideoPaths);
            if (res == ContentDialogResult.Primary && dialog.StartImmediately && _viewModel != null)
            {
                if (dialog.SelectedVideoPaths.Count == 1)
                    await _viewModel.ExtractSelectedAsync();
                else
                    await _viewModel.ExtractAllAsync();
            }
        }
    }

    private void ImportFolderBtn_Click(object sender, RoutedEventArgs e)
    {
        var folder = CodeVision.Desktop.Services.NativeFileDialogs.PickFolder("اختر مجلد الفيديوهات لإضافته للمكتبة");
        if (!string.IsNullOrWhiteSpace(folder))
        {
            _viewModel?.ScanAndAddFolder(folder);
        }
    }

    private async void ExtractSelectedBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel != null)
        {
            await _viewModel.ExtractSelectedAsync();
        }
    }

    private async void ExtractAllBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel != null)
        {
            await _viewModel.ExtractAllAsync();
        }
    }

    private void SelectAllBtn_Click(object sender, RoutedEventArgs e)
    {
        _viewModel?.SelectAll();
    }

    private void DeselectAllBtn_Click(object sender, RoutedEventArgs e)
    {
        _viewModel?.DeselectAll();
    }

    private void DeleteVideoBtn_Click(object sender, RoutedEventArgs e)
    {
        _viewModel?.RemoveSelected();
    }

    private void SearchInput_QuerySubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        if (_viewModel == null) return;
        var query = sender.Text?.Trim() ?? string.Empty;
        if (string.IsNullOrEmpty(query))
        {
            VideosListView.ItemsSource = _viewModel.Videos;
        }
        else
        {
            VideosListView.ItemsSource = _viewModel.Videos
                .Where(v => v.FileName.Contains(query, StringComparison.OrdinalIgnoreCase) ||
                            v.DetectedLanguage.Contains(query, StringComparison.OrdinalIgnoreCase))
                .ToList();
        }
    }

    private void VideosListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_viewModel != null && VideosListView.SelectedItem is VideoItem item)
        {
            _viewModel.SelectedVideo = item;
        }
    }

    private void OpenInStudioBtn_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is VideoItem video)
        {
            if (App.MainWindow is MainWindow mainWindow)
            {
                mainWindow.NavigateToReviewWithVideo(video);
            }
        }
    }
}
