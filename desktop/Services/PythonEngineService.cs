using System.Diagnostics;
using System.IO;
using System.Text;

namespace CodeVision.Desktop.Services;

public sealed class PythonEngineService
{
    private readonly SettingsService _settings;
    private readonly LoggingService _logger;

    public PythonEngineService(SettingsService settings, LoggingService logger)
    {
        _settings = settings;
        _logger = logger;
    }

    public string FindPythonExecutable()
    {
        var configured = _settings.Current.PythonPath;
        if (!string.IsNullOrWhiteSpace(configured) && File.Exists(configured))
            return configured;

        var candidates = new[]
        {
            @"C:\Python313\python.exe",
            @"C:\Python312\python.exe",
            @"C:\Users\ibral\anaconda3\python.exe",
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "anaconda3", "python.exe"),
            "python.exe"
        };

        foreach (var c in candidates)
        {
            if (File.Exists(c)) return c;
        }

        return "python.exe";
    }

    public string FindEngineRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (Directory.Exists(Path.Combine(current.FullName, "core")) &&
                Directory.Exists(Path.Combine(current.FullName, "vision")))
            {
                return current.FullName;
            }
            current = current.Parent;
        }
        return Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));
    }

    public async Task<int> RunScriptAsync(
        string scriptNameOrCommand,
        string arguments,
        Action<string>? onOutputLine,
        CancellationToken cancellationToken = default)
    {
        var python = FindPythonExecutable();
        var root = FindEngineRoot();
        var fullScript = Path.Combine(root, scriptNameOrCommand);

        var scriptArg = File.Exists(fullScript)
            ? $"\"{fullScript}\""
            : (scriptNameOrCommand.StartsWith("\"") ? scriptNameOrCommand : $"\"{scriptNameOrCommand}\"");

        var psi = new ProcessStartInfo
        {
            FileName = python,
            Arguments = $"{scriptArg} {arguments}",
            WorkingDirectory = root,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        psi.Environment["PYTHONPATH"] = root;
        psi.Environment["PYTHONIOENCODING"] = "utf-8";
        psi.Environment["PYTHONUTF8"] = "1";
        _logger.Info($"Running: {psi.FileName} {psi.Arguments} in {psi.WorkingDirectory}");

        using var process = new Process { StartInfo = psi, EnableRaisingEvents = true };
        process.OutputDataReceived += (_, e) =>
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                _logger.Info($"[Python] {e.Data}");
                App.RunOnUIThread(() => onOutputLine?.Invoke(e.Data));
            }
        };
        process.ErrorDataReceived += (_, e) =>
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                _logger.Warning($"[Python Err] {e.Data}");
                App.RunOnUIThread(() => onOutputLine?.Invoke($"[ERR] {e.Data}"));
            }
        };

        try
        {
            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            using var reg = cancellationToken.Register(() =>
            {
                try { if (!process.HasExited) process.Kill(true); } catch { }
            });

            await process.WaitForExitAsync(cancellationToken);
            return process.ExitCode;
        }
        catch (OperationCanceledException)
        {
            _logger.Warning("Python process was cancelled by user.");
            return -1;
        }
        catch (Exception ex)
        {
            _logger.Error("Failed to execute python process", ex);
            onOutputLine?.Invoke($"Error: {ex.Message}");
            return -1;
        }
    }
}
