namespace CodeVision.Desktop.Models;

public sealed class ModelInfo
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = string.Empty;
    public string Version { get; set; } = "1.0.0";
    public string Architecture { get; set; } = "ResNet-18 / CodeOCR";
    public double Accuracy { get; set; }
    public double Precision { get; set; }
    public double Recall { get; set; }
    public double F1Score { get; set; }
    public string WeightsPath { get; set; } = string.Empty;
    public string CreatedDate { get; set; } = DateTime.Now.ToString("yyyy-MM-dd");
    public bool IsActiveInRuntime { get; set; }
}
