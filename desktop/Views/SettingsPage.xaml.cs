using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;

namespace CodeVision.Desktop.Views;

public sealed partial class SettingsPage : Page
{
    public SettingsViewModel? ViewModel { get; set; }

    public SettingsPage()
    {
        InitializeComponent();
    }

    public void Initialize(SettingsViewModel vm)
    {
        ViewModel = vm;
        PythonPathBox.Text = vm.PythonPath;
        FfmpegPathBox.Text = vm.FfmpegPath;
        OutputDirBox.Text = vm.OutputDirectory;
        DatasetsDirBox.Text = vm.DatasetsDirectory;
        ModelsDirBox.Text = vm.ModelsDirectory;
        LogsTextBox.Text = vm.RecentLogs;

        ThemeCombo.ItemsSource = vm.AvailableThemes;
        ThemeCombo.SelectedItem = vm.SelectedTheme;

        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(SettingsViewModel.SaveMessage))
                SaveNoticeLabel.Text = vm.SaveMessage;
            else if (e.PropertyName == nameof(SettingsViewModel.RecentLogs))
                LogsTextBox.Text = vm.RecentLogs;
            else if (e.PropertyName == nameof(SettingsViewModel.PythonPath))
                PythonPathBox.Text = vm.PythonPath;
        };
    }

    private void SaveSettingsBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel is null) return;
        ViewModel.PythonPath = PythonPathBox.Text;
        ViewModel.FfmpegPath = FfmpegPathBox.Text;
        ViewModel.OutputDirectory = OutputDirBox.Text;
        ViewModel.DatasetsDirectory = DatasetsDirBox.Text;
        ViewModel.ModelsDirectory = ModelsDirBox.Text;
        if (ThemeCombo.SelectedItem is string th) ViewModel.SelectedTheme = th;

        ViewModel.SaveSettings();
    }

    private void AutoDetectAnaconda_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.AutoDetectAnaconda();
    }

    private void RefreshLogsBtn_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.RefreshLogs();
    }
}
