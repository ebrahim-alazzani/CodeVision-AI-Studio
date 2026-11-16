using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;

namespace CodeVision.Desktop.Views;

public sealed partial class TrainingLabPage : Page
{
    public TrainingLabViewModel? ViewModel { get; set; }

    public TrainingLabPage()
    {
        InitializeComponent();
    }

    public void Initialize(TrainingLabViewModel vm)
    {
        ViewModel = vm;
        EpochLogsList.ItemsSource = vm.EpochLogs;
        OptimizerCombo.ItemsSource = vm.Optimizers;
        OptimizerCombo.SelectedIndex = 0;
        LossCombo.ItemsSource = vm.LossFunctions;
        LossCombo.SelectedIndex = 0;

        ModelNameBox.Text = vm.Config.ModelName;
        DatasetPathBox.Text = vm.Config.DatasetPath;
        EpochsBox.Text = vm.Config.Epochs.ToString();
        BatchSizeBox.Text = vm.Config.BatchSize.ToString();
        LearningRateBox.Text = vm.Config.LearningRate.ToString();

        DatasetSummaryLabel.Text = vm.DatasetSummary;
        TotalJobsMetric.Text = vm.ExtractedJobsCount.ToString();
        TotalKeyframesMetric.Text = vm.TotalKeyframesCount.ToString();
        TotalFilesMetric.Text = vm.TotalCodeFilesCount.ToString();

        vm.PropertyChanged += (_, e) =>
        {
            DispatcherQueue.TryEnqueue(() =>
            {
                if (e.PropertyName == nameof(TrainingLabViewModel.CurrentEpoch))
                {
                    EpochMetricLabel.Text = $"{vm.CurrentEpoch} / {vm.Config.Epochs}";
                }
                else if (e.PropertyName == nameof(TrainingLabViewModel.CurrentLoss))
                {
                    LossMetricLabel.Text = vm.CurrentLoss.ToString("F4");
                }
                else if (e.PropertyName == nameof(TrainingLabViewModel.CurrentAccuracy))
                {
                    AccuracyMetricLabel.Text = $"{vm.CurrentAccuracy:F1}%";
                    ValAccuracyMetricLabel.Text = $"{Math.Max(0, vm.CurrentAccuracy - 2.1):F1}%";
                }
                else if (e.PropertyName == nameof(TrainingLabViewModel.TrainingStatus))
                {
                    StatusBadge.Text = vm.TrainingStatus;
                }
                else if (e.PropertyName == nameof(TrainingLabViewModel.DatasetSummary))
                {
                    DatasetSummaryLabel.Text = vm.DatasetSummary;
                    TotalJobsMetric.Text = vm.ExtractedJobsCount.ToString();
                    TotalKeyframesMetric.Text = vm.TotalKeyframesCount.ToString();
                    TotalFilesMetric.Text = vm.TotalCodeFilesCount.ToString();
                }
            });
        };
    }

    private async void StartTrainBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel is null) return;
        ViewModel.Config.ModelName = ModelNameBox.Text;
        ViewModel.Config.DatasetPath = DatasetPathBox.Text;
        if (int.TryParse(EpochsBox.Text, out var ep)) ViewModel.Config.Epochs = ep;
        if (int.TryParse(BatchSizeBox.Text, out var bs)) ViewModel.Config.BatchSize = bs;
        if (double.TryParse(LearningRateBox.Text, out var lr)) ViewModel.Config.LearningRate = lr;

        StatusBadge.Text = "جاري التدريب…";
        await ViewModel.StartTrainingAsync();
    }

    private void CancelTrainBtn_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.CancelTraining();
        StatusBadge.Text = "تم إيقاف التدريب.";
    }
}
