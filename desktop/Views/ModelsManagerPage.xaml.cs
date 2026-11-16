using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;

namespace CodeVision.Desktop.Views;

public sealed partial class ModelsManagerPage : Page
{
    public ModelsManagerViewModel? ViewModel { get; set; }

    public ModelsManagerPage()
    {
        InitializeComponent();
    }

    public void Initialize(ModelsManagerViewModel vm)
    {
        ViewModel = vm;
        ModelsListView.ItemsSource = vm.Models;
        ModelsStatusLabel.Text = vm.Status;

        UpdateSelectedDisplay();

        ModelsListView.SelectionChanged += (_, _) =>
        {
            if (ModelsListView.SelectedItem is Models.ModelInfo m)
            {
                vm.SelectedModel = m;
                UpdateSelectedDisplay();
            }
        };

        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(ModelsManagerViewModel.Status))
                ModelsStatusLabel.Text = vm.Status;
        };
    }

    private void UpdateSelectedDisplay()
    {
        if (ViewModel?.SelectedModel is not null)
        {
            var m = ViewModel.SelectedModel;
            ModelTitleLabel.Text = $"{m.Name} (v{m.Version})";
            AccLabel.Text = $"{(m.Accuracy * 100):F1}%";
            PrecLabel.Text = $"{(m.Precision * 100):F1}%";
            RecallLabel.Text = $"{(m.Recall * 100):F1}%";
            F1Label.Text = $"{(m.F1Score * 100):F1}%";
            WeightsPathLabel.Text = $"مسار الأوزان: {m.WeightsPath}";
            ActiveStatusLabel.Text = m.IsActiveInRuntime ? "✓ هذا هو النموذج النشط حالياً في Runtime" : "غير نشط";
            ActiveStatusLabel.Foreground = m.IsActiveInRuntime ? new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 16, 185, 129)) : new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 156, 163, 175));
        }
    }

    private void SetActiveBtn_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.SetActiveModel();
        UpdateSelectedDisplay();
    }
}
