using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.Views;

public sealed partial class AddVideoDialog : ContentDialog
{
    private readonly List<string> _batchFiles = new();

    public List<string> SelectedVideoPaths { get; } = new();
    public string? SelectedLanguage => (LanguageCombo.SelectedItem as ComboBoxItem)?.Content?.ToString();
    public bool StartImmediately => StartImmediatelySwitch.IsOn;

    public AddVideoDialog()
    {
        InitializeComponent();
        SavePathBox.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "output");
    }

    public void SetBatchMode(bool isBatch)
    {
        ModeSelector.SelectedIndex = isBatch ? 1 : 0;
    }

    private void ModeSelector_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ModeSelector.SelectedIndex == 0)
        {
            SingleVideoPanel.Visibility = Visibility.Visible;
            BatchVideoPanel.Visibility = Visibility.Collapsed;
        }
        else
        {
            SingleVideoPanel.Visibility = Visibility.Collapsed;
            BatchVideoPanel.Visibility = Visibility.Visible;
        }
    }

    private void BrowseVideo_Click(object sender, RoutedEventArgs e)
    {
        var path = NativeFileDialogs.PickSingleVideoFile();
        if (!string.IsNullOrWhiteSpace(path))
        {
            VideoPathBox.Text = path;
        }
    }

    private void BrowseFolder_Click(object sender, RoutedEventArgs e)
    {
        var folder = NativeFileDialogs.PickFolder("اختر مجلد دروس الفيديو التعليمية");
        if (!string.IsNullOrWhiteSpace(folder))
        {
            BatchFolderPathBox.Text = folder;
            ScanFolderForVideos(folder);
        }
    }

    private void BrowseMultiFiles_Click(object sender, RoutedEventArgs e)
    {
        var files = NativeFileDialogs.PickMultipleVideoFiles();
        if (files is not null && files.Count > 0)
        {
            _batchFiles.Clear();
            _batchFiles.AddRange(files);
            UpdateBatchListView();
        }
    }

    private void ScanFolderForVideos(string folderPath)
    {
        if (!Directory.Exists(folderPath)) return;

        var supported = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".flv"
        };

        var found = Directory.EnumerateFiles(folderPath, "*.*", SearchOption.TopDirectoryOnly)
            .Where(f => supported.Contains(Path.GetExtension(f)))
            .ToList();

        _batchFiles.Clear();
        _batchFiles.AddRange(found);
        UpdateBatchListView();
    }

    private void UpdateBatchListView()
    {
        BatchListView.ItemsSource = null;
        BatchListView.ItemsSource = _batchFiles;

        if (_batchFiles.Count > 0)
        {
            BatchCountSummary.Text = $"تم تحديد {_batchFiles.Count} فيديو في الحزمة جاهزة للاستخراج.";
            ClearBatchBtn.Visibility = Visibility.Visible;
        }
        else
        {
            BatchCountSummary.Text = "لم يتم العثور على ملفات فيديو متوافقة في المجلد.";
            ClearBatchBtn.Visibility = Visibility.Collapsed;
        }
    }

    private void ClearBatchBtn_Click(object sender, RoutedEventArgs e)
    {
        _batchFiles.Clear();
        UpdateBatchListView();
        BatchFolderPathBox.Text = string.Empty;
    }

    private void BrowseSavePath_Click(object sender, RoutedEventArgs e)
    {
        var folder = NativeFileDialogs.PickFolder("اختر مجلد إخراج المشاريع المستعادة");
        if (!string.IsNullOrWhiteSpace(folder))
        {
            SavePathBox.Text = folder;
        }
    }

    private void ContentDialog_PrimaryButtonClick(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        SelectedVideoPaths.Clear();

        if (ModeSelector.SelectedIndex == 0)
        {
            // Single video mode
            if (!string.IsNullOrWhiteSpace(VideoPathBox.Text) && File.Exists(VideoPathBox.Text.Trim()))
            {
                SelectedVideoPaths.Add(VideoPathBox.Text.Trim());
            }
            else
            {
                args.Cancel = true;
            }
        }
        else
        {
            // Batch video mode
            if (_batchFiles.Count > 0)
            {
                SelectedVideoPaths.AddRange(_batchFiles);
            }
            else
            {
                args.Cancel = true;
            }
        }
    }

    private void ContentDialog_SecondaryButtonClick(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        ContentDialog_PrimaryButtonClick(sender, args);
    }
}
