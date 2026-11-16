using System.IO;

namespace CodeVision.Desktop.Services;

public sealed class LoggingService
{
    private readonly string _logFilePath;
    private readonly object _lock = new();

    public event Action<string>? LogMessageReceived;

    public LoggingService()
    {
        var logsDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CodeVision", "logs");
        Directory.CreateDirectory(logsDir);
        _logFilePath = Path.Combine(logsDir, $"codevision_{DateTime.Now:yyyyMMdd}.log");
    }

    public void Info(string message) => Log("INFO", message);
    public void Warning(string message) => Log("WARN", message);
    public void Error(string message, Exception? ex = null)
    {
        var fullMessage = ex is not null ? $"{message}\n{ex}" : message;
        Log("ERROR", fullMessage);
    }

    private void Log(string level, string message)
    {
        var formatted = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{level}] {message}";
        lock (_lock)
        {
            try { File.AppendAllText(_logFilePath, formatted + Environment.NewLine); }
            catch { }
        }
        LogMessageReceived?.Invoke(formatted);
    }

    public string ReadRecentLogs(int maxLines = 100)
    {
        lock (_lock)
        {
            try
            {
                if (!File.Exists(_logFilePath)) return string.Empty;
                var lines = File.ReadAllLines(_logFilePath);
                var takeCount = Math.Min(lines.Length, maxLines);
                return string.Join(Environment.NewLine, lines[^takeCount..]);
            }
            catch { return string.Empty; }
        }
    }
}
