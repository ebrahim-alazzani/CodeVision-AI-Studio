using CommunityToolkit.Mvvm.ComponentModel;

namespace CodeVision.Desktop.Models;

public partial class TrainingConfig : ObservableObject
{
    [ObservableProperty]
    private string _modelName = "CodeVision-CNN-Classifier-v2";

    [ObservableProperty]
    private string _datasetPath = string.Empty;

    [ObservableProperty]
    private int _epochs = 25;

    [ObservableProperty]
    private int _batchSize = 32;

    [ObservableProperty]
    private double _learningRate = 0.001;

    [ObservableProperty]
    private double _trainSplit = 0.70;

    [ObservableProperty]
    private double _valSplit = 0.15;

    [ObservableProperty]
    private double _testSplit = 0.15;

    [ObservableProperty]
    private string _optimizer = "Adam";

    [ObservableProperty]
    private string _lossFunction = "CrossEntropyLoss";

    [ObservableProperty]
    private bool _enableDataAugmentation = true;
}
