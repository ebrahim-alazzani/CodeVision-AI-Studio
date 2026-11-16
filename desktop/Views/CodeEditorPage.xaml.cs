using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CodeVision.Desktop.ViewModels;

namespace CodeVision.Desktop.Views;

public sealed partial class CodeEditorPage : Page
{
    public CodeEditorViewModel? ViewModel { get; set; }

    public CodeEditorPage()
    {
        InitializeComponent();
    }

    public void Initialize(CodeEditorViewModel vm)
    {
        ViewModel = vm;
        FilesListView.ItemsSource = vm.Snippets;
        LanguageCombo.ItemsSource = vm.SupportedLanguages;
        LanguageCombo.SelectedIndex = 0;

        EditorBox.Text = vm.CurrentCode;
        EditorStatusLabel.Text = vm.StatusNotification;

        FilesListView.SelectionChanged += (_, _) =>
        {
            if (FilesListView.SelectedItem is Models.ExtractedCodeSnippet snip)
            {
                vm.SelectedSnippet = snip;
                EditorBox.Text = snip.CodeContent;
                EditorStatusLabel.Text = vm.StatusNotification;
            }
        };

        EditorBox.TextChanged += (_, _) =>
        {
            vm.CurrentCode = EditorBox.Text;
        };
    }

    private void SaveBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel is null) return;
        ViewModel.CurrentCode = EditorBox.Text;
        ViewModel.SaveCurrentSnippet();
        EditorStatusLabel.Text = ViewModel.StatusNotification;
    }

    private void AddFileBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel is null) return;
        ViewModel.AddNewFile();
        EditorBox.Text = ViewModel.CurrentCode;
        EditorStatusLabel.Text = ViewModel.StatusNotification;
    }
}
