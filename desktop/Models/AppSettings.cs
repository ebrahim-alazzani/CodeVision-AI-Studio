namespace CodeVision.Desktop.Models;

public sealed class AppSettings
{
    public string PythonPath { get; set; } = @"C:\Python313\python.exe";
    public string FfmpegPath { get; set; } = "ffmpeg";
    public string EngineScriptPath { get; set; } = @"e:\New folder (3)\CodeVisionPhase1\core\video_pipeline.py";
    public string OutputDirectory { get; set; } = "";
    public string DatasetsDirectory { get; set; } = "";
    public string ModelsDirectory { get; set; } = "";
    public string ActiveModelId { get; set; } = "codevision-ocr-v1";
    public string Theme { get; set; } = "Dark";
    public string Language { get; set; } = "ar";
}
