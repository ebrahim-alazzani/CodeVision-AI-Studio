using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.ApplicationModel.DataTransfer;
using CodeVision.Desktop.Services;

namespace CodeVision.Desktop.Views;

public sealed partial class DiagnosticsDialog : ContentDialog
{
    private readonly LoggingService _logger;
    private readonly string _logFilePath;

    public DiagnosticsDialog(LoggingService logger)
    {
        InitializeComponent();
        _logger = logger;

        var logsDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "logs");
        _logFilePath = Path.Combine(logsDir, $"codevision_{DateTime.Now:yyyyMMdd}.log");
        LogPathText.Text = $"Log file path: {_logFilePath}";

        RefreshLogs();
    }

    private void RefreshLogs()
    {
        LogTextBox.Text = _logger.ReadRecentLogs(250);
    }

    private void Refresh_Click(object sender, RoutedEventArgs e)
    {
        RefreshLogs();
    }

    private void CopyPath_Click(object sender, RoutedEventArgs e)
    {
        var dp = new DataPackage();
        dp.SetText(_logFilePath);
        Clipboard.SetContent(dp);
    }

    private void Clear_Click(object sender, RoutedEventArgs e)
    {
        LogTextBox.Text = string.Empty;
    }
}
