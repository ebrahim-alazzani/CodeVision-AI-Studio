using System;
using System.IO;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.ApplicationModel.DataTransfer;
using CodeVision.Desktop.Models;
using CodeVision.Desktop.ViewModels;

namespace CodeVision.Desktop.Views;

public sealed partial class ProjectReconstructionPage : Page
{
    public ProjectReconstructionViewModel? ViewModel { get; set; }
    private bool _isSyncingTree;

    public ProjectReconstructionPage()
    {
        InitializeComponent();
    }

    public void Initialize(ProjectReconstructionViewModel vm)
    {
        ViewModel = vm;

        JobSelector.ItemsSource = vm.AvailableJobs;
        JobSelector.SelectedItem = vm.SelectedJob;

        OrderedSnippetsList.ItemsSource = vm.OrderedSnippets;
        ProjectNameBox.Text = vm.ProjectName;
        ExportStatusLabel.Text = vm.ExportStatus;
        TotalFilesLabel.Text = vm.TotalFilesCount.ToString();
        TotalLinesLabel.Text = vm.TotalLinesCount.ToString();

        SelectedFileNameLabel.Text = vm.SelectedFileName;
        SelectedFileMetaLabel.Text = vm.SelectedFileMeta;
        CodeDisplayBox.Text = vm.SelectedFileCode;

        OpenExportFolderBtn.Visibility = vm.HasExportedPath ? Visibility.Visible : Visibility.Collapsed;

        SyncTreeView();

        vm.PropertyChanged += (_, e) =>
        {
            App.RunOnUIThread(() =>
            {
                if (e.PropertyName == nameof(ProjectReconstructionViewModel.ExportStatus))
                    ExportStatusLabel.Text = vm.ExportStatus;
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.ProjectName))
                    ProjectNameBox.Text = vm.ProjectName;
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.TotalFilesCount))
                    TotalFilesLabel.Text = vm.TotalFilesCount.ToString();
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.TotalLinesCount))
                    TotalLinesLabel.Text = vm.TotalLinesCount.ToString();
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.SelectedFileName))
                    SelectedFileNameLabel.Text = vm.SelectedFileName;
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.SelectedFileMeta))
                    SelectedFileMetaLabel.Text = vm.SelectedFileMeta;
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.SelectedFileCode))
                    CodeDisplayBox.Text = vm.SelectedFileCode;
                else if (e.PropertyName == nameof(ProjectReconstructionViewModel.HasExportedPath))
                    OpenExportFolderBtn.Visibility = vm.HasExportedPath ? Visibility.Visible : Visibility.Collapsed;
            });
        };

        ProjectNameBox.TextChanged += (_, _) =>
        {
            if (ViewModel != null)
                ViewModel.ProjectName = ProjectNameBox.Text;
        };
    }

    private void SyncTreeView()
    {
        if (ViewModel == null || _isSyncingTree) return;
        _isSyncingTree = true;

        try
        {
            ProjectTreeView.RootNodes.Clear();
            foreach (var rootItem in ViewModel.ProjectTree)
            {
                var node = CreateTreeNode(rootItem);
                ProjectTreeView.RootNodes.Add(node);
            }
        }
        catch { }
        finally
        {
            _isSyncingTree = false;
        }
    }

    private TreeViewNode CreateTreeNode(ProjectTreeItem item)
    {
        var node = new TreeViewNode
        {
            Content = item,
            IsExpanded = true
        };

        foreach (var child in item.Children)
        {
            node.Children.Add(CreateTreeNode(child));
        }

        return node;
    }

    private void ProjectTreeView_ItemInvoked(TreeView sender, TreeViewItemInvokedEventArgs args)
    {
        ProjectTreeItem? item = null;
        if (args.InvokedItem is TreeViewNode node && node.Content is ProjectTreeItem treeItem)
        {
            item = treeItem;
        }
        else if (args.InvokedItem is ProjectTreeItem directItem)
        {
            item = directItem;
        }

        if (item != null && ViewModel != null)
        {
            ViewModel.SelectItem(item);
        }
    }

    private void OrderedSnippetsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (OrderedSnippetsList.SelectedItem is ExtractedCodeSnippet snippet && ViewModel != null)
        {
            ViewModel.SelectSnippet(snippet);
        }
    }

    private void JobSelector_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (JobSelector.SelectedItem is AvailableJobItem job && ViewModel != null)
        {
            ViewModel.SelectedJob = job;
            ViewModel.LoadJob(job.Path);
            SyncTreeView();
        }
    }

    private void RefreshJobsBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel == null) return;
        ViewModel.ScanAvailableJobs();
        JobSelector.SelectedItem = ViewModel.SelectedJob;
        SyncTreeView();
    }

    private async void ExportProjectBtn_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel == null) return;
        ViewModel.ProjectName = ProjectNameBox.Text;
        await ViewModel.ExportProjectAsync();
    }

    private void OpenExportFolderBtn_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.OpenExportFolder();
    }

    private void CopyCodeBtn_Click(object sender, RoutedEventArgs e)
    {
        var code = CodeDisplayBox.Text;
        if (string.IsNullOrEmpty(code)) return;

        try
        {
            var dp = new DataPackage();
            dp.SetText(code);
            Clipboard.SetContent(dp);
            ExportStatusLabel.Text = $"✓ تم نسخ محتوى {SelectedFileNameLabel.Text} إلى الحافظة بنجاح!";
        }
        catch (Exception ex)
        {
            ExportStatusLabel.Text = $"فشل النسخ إلى الحافظة: {ex.Message}";
        }
    }
}
