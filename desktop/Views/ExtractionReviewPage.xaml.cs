using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Windows.ApplicationModel.DataTransfer;
using Windows.Media.Core;
using System.IO;
using CodeVision.Desktop.ViewModels;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.Views;

public sealed partial class ExtractionReviewPage : Page
{
    private ExtractionReviewViewModel? _viewModel;

    public ExtractionReviewPage()
    {
        InitializeComponent();
    }

    public void Initialize(ExtractionReviewViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = _viewModel;

        ScenesList.ItemsSource = _viewModel.DetectedScenes;
        LiveLogsList.ItemsSource = _viewModel.LiveExecutionLogs;
        TranscriptsListView.ItemsSource = _viewModel.TranscriptSegments;

        if (_viewModel.HasRealVideo && File.Exists(_viewModel.RealVideoPath))
        {
            LoadVideoIntoPlayer(_viewModel.RealVideoPath);
        }

        _viewModel.PropertyChanged += (s, e) =>
        {
            DispatcherQueue.TryEnqueue(() =>
            {
                if (e.PropertyName == nameof(ExtractionReviewViewModel.TimeDisplay))
                {
                    TimeLabel.Text = _viewModel.TimeDisplay;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentFrameIndex))
                {
                    FrameCounterLabel.Text = $"Frame: {_viewModel.CurrentFrameIndex} / {_viewModel.TotalFramesCount}";
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentPositionSeconds))
                {
                    TimelineSlider.Value = _viewModel.CurrentPositionSeconds;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentActionStatus))
                {
                    ActionStatusLabel.Text = _viewModel.CurrentActionStatus;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentAlgorithm))
                {
                    AlgorithmLabel.Text = _viewModel.CurrentAlgorithm;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentLibrary))
                {
                    LibraryLabel.Text = _viewModel.CurrentLibrary;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.RoiCoordinates))
                {
                    RoiLabel.Text = $"ROI: [{_viewModel.RoiCoordinates}]";
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.AudioStatusText))
                {
                    AudioStatusLabel.Text = _viewModel.AudioStatusText;
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.RoiLeft) ||
                         e.PropertyName == nameof(ExtractionReviewViewModel.RoiTop) ||
                         e.PropertyName == nameof(ExtractionReviewViewModel.RoiWidth) ||
                         e.PropertyName == nameof(ExtractionReviewViewModel.RoiHeight))
                {
                    Canvas.SetLeft(BoundingBoxOverlay, _viewModel.RoiLeft);
                    Canvas.SetTop(BoundingBoxOverlay, _viewModel.RoiTop);
                    BoundingBoxOverlay.Width = Math.Max(50, _viewModel.RoiWidth);
                    BoundingBoxOverlay.Height = Math.Max(30, _viewModel.RoiHeight);
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.RealVideoPath))
                {
                    if (!string.IsNullOrWhiteSpace(_viewModel.RealVideoPath) && File.Exists(_viewModel.RealVideoPath))
                    {
                        LoadVideoIntoPlayer(_viewModel.RealVideoPath);
                    }
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.SelectedTranscript))
                {
                    if (_viewModel.SelectedTranscript != null)
                    {
                        SpeechTranscriptLabel.Text = _viewModel.SelectedTranscript.Text;
                    }
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.SelectedSnippet))
                {
                    UpdateSnippetDisplay();
                }
                else if (e.PropertyName == nameof(ExtractionReviewViewModel.CurrentFrameImagePath))
                {
                    if (!string.IsNullOrWhiteSpace(_viewModel.CurrentFrameImagePath) && File.Exists(_viewModel.CurrentFrameImagePath))
                    {
                        KeyframeSnapshotImage.Source = new Microsoft.UI.Xaml.Media.Imaging.BitmapImage(new Uri(_viewModel.CurrentFrameImagePath));
                        KeyframeSnapshotImage.Visibility = Visibility.Visible;
                        NoVideoPlaceholder.Visibility = Visibility.Collapsed;
                    }
                }
            });
        };

        UpdateSnippetDisplay();
    }

    private void LoadVideoIntoPlayer(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                RealVideoPlayer.Source = MediaSource.CreateFromUri(new Uri(path));
                RealVideoPlayer.Visibility = Visibility.Visible;
                NoVideoPlaceholder.Visibility = Visibility.Collapsed;

                if (RealVideoPlayer.MediaPlayer?.PlaybackSession != null && _viewModel != null)
                {
                    RealVideoPlayer.MediaPlayer.PlaybackSession.PlaybackRate = _viewModel.PlaybackSpeed;
                }
            }
        }
        catch { }
    }

    private void UpdateSnippetDisplay()
    {
        if (_viewModel?.SelectedSnippet != null)
        {
            SnippetFileLabel.Text = _viewModel.SelectedSnippet.TargetFilePath;
            SnippetLangBadge.Text = _viewModel.SelectedSnippet.Language;
            SnippetConfidenceLabel.Text = $"درجة الثقة: {_viewModel.SelectedSnippet.Confidence:P0} · التوقيت: {_viewModel.SelectedSnippet.TimestampFormatted}";
            CodePreviewBox.Text = _viewModel.SelectedSnippet.CodeContent;
            SnippetExplanationLabel.Text = _viewModel.SelectedSnippet.Explanation;
        }
    }

    // --- Tab Switching Logic ---
    private void TabBtnLogs_Click(object sender, RoutedEventArgs e)
    {
        ShowTab("logs");
    }

    private void TabBtnCode_Click(object sender, RoutedEventArgs e)
    {
        ShowTab("code");
    }

    private void TabBtnTranscript_Click(object sender, RoutedEventArgs e)
    {
        ShowTab("transcript");
    }

    private void TabBtnAudio_Click(object sender, RoutedEventArgs e)
    {
        ShowTab("audio");
    }

    private void ShowTab(string tab)
    {
        PaneLiveLogs.Visibility = tab == "logs" ? Visibility.Visible : Visibility.Collapsed;
        PaneCode.Visibility = tab == "code" ? Visibility.Visible : Visibility.Collapsed;
        PaneTranscript.Visibility = tab == "transcript" ? Visibility.Visible : Visibility.Collapsed;
        PaneAudio.Visibility = tab == "audio" ? Visibility.Visible : Visibility.Collapsed;

        // Reset backgrounds
        TabBtnLogs.ClearValue(Button.BackgroundProperty);
        TabBtnLogs.ClearValue(Button.ForegroundProperty);
        TabBtnCode.ClearValue(Button.BackgroundProperty);
        TabBtnCode.ClearValue(Button.ForegroundProperty);
        TabBtnTranscript.ClearValue(Button.BackgroundProperty);
        TabBtnTranscript.ClearValue(Button.ForegroundProperty);
        TabBtnAudio.ClearValue(Button.BackgroundProperty);
        TabBtnAudio.ClearValue(Button.ForegroundProperty);

        var activeBg = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["HalvoGradientCyanBlue"];
        var activeFg = (Microsoft.UI.Xaml.Media.Brush)new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 11, 15, 21));

        switch (tab)
        {
            case "logs":
                TabBtnLogs.Background = activeBg;
                TabBtnLogs.Foreground = activeFg;
                break;
            case "code":
                TabBtnCode.Background = activeBg;
                TabBtnCode.Foreground = activeFg;
                break;
            case "transcript":
                TabBtnTranscript.Background = activeBg;
                TabBtnTranscript.Foreground = activeFg;
                break;
            case "audio":
                TabBtnAudio.Background = activeBg;
                TabBtnAudio.Foreground = activeFg;
                break;
        }
    }

    private void ClearLogsBtn_Click(object sender, RoutedEventArgs e)
    {
        _viewModel?.LiveExecutionLogs.Clear();
    }

    private void TranscriptsListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_viewModel != null && TranscriptsListView.SelectedItem is TranscriptSegmentModel seg)
        {
            _viewModel.SeekToSeconds(seg.StartSec);
            if (RealVideoPlayer.MediaPlayer?.PlaybackSession != null)
            {
                try
                {
                    RealVideoPlayer.MediaPlayer.PlaybackSession.Position = TimeSpan.FromSeconds(seg.StartSec);
                }
                catch { }
            }
        }
    }

    private async void PlaySimBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel != null)
        {
            if (_viewModel.HasRealVideo && RealVideoPlayer.MediaPlayer != null)
            {
                try
                {
                    RealVideoPlayer.MediaPlayer.Play();
                }
                catch { }
            }

            await _viewModel.StartSimulationAsync();
        }
    }

    private void PauseSimBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel != null)
        {
            if (RealVideoPlayer.MediaPlayer != null)
            {
                try
                {
                    RealVideoPlayer.MediaPlayer.Pause();
                }
                catch { }
            }

            _viewModel.PauseSimulation();
        }
    }

    private void NextFrameBtn_Click(object sender, RoutedEventArgs e)
    {
        _viewModel?.NextFrame();
    }

    private void PlaybackSpeedCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_viewModel == null || PlaybackSpeedCombo == null) return;

        double speed = PlaybackSpeedCombo.SelectedIndex switch
        {
            0 => 0.5,
            1 => 1.0,
            2 => 2.0,
            _ => 1.0
        };

        _viewModel.PlaybackSpeed = speed;

        if (RealVideoPlayer.MediaPlayer?.PlaybackSession != null)
        {
            try
            {
                RealVideoPlayer.MediaPlayer.PlaybackSession.PlaybackRate = speed;
            }
            catch { }
        }
    }

    private void LoadRealVideoBtn_Click(object sender, RoutedEventArgs e)
    {
        var videoPath = NativeFileDialogs.PickSingleVideoFile();
        if (!string.IsNullOrWhiteSpace(videoPath) && File.Exists(videoPath))
        {
            _viewModel?.LoadRealVideoDirectly(videoPath);
            LoadVideoIntoPlayer(videoPath);
        }
    }

    private void TimelineSlider_ValueChanged(object sender, RangeBaseValueChangedEventArgs e)
    {
        if (_viewModel != null && Math.Abs(_viewModel.CurrentPositionSeconds - e.NewValue) > 1.5)
        {
            _viewModel.SeekToSeconds(e.NewValue);

            if (RealVideoPlayer.MediaPlayer?.PlaybackSession != null)
            {
                try
                {
                    RealVideoPlayer.MediaPlayer.PlaybackSession.Position = TimeSpan.FromSeconds(e.NewValue);
                }
                catch { }
            }
        }
    }

    private void ScenesList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_viewModel != null && ScenesList.SelectedItem is DetectedScene scene)
        {
            _viewModel.SeekToSeconds(scene.TimestampSec);

            if (RealVideoPlayer.MediaPlayer?.PlaybackSession != null)
            {
                try
                {
                    RealVideoPlayer.MediaPlayer.PlaybackSession.Position = TimeSpan.FromSeconds(scene.TimestampSec);
                }
                catch { }
            }
        }
    }

    private void CopyCodeBtn_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrWhiteSpace(CodePreviewBox.Text))
        {
            var dp = new DataPackage();
            dp.SetText(CodePreviewBox.Text);
            Clipboard.SetContent(dp);
        }
    }
}
