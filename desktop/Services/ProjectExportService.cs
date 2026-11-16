using System.IO;
using System.Text;
using CodeVision.Desktop.Models;

namespace CodeVision.Desktop.Services;

public sealed class ProjectExportService
{
    private readonly LoggingService _logger;

    public ProjectExportService(LoggingService logger)
    {
        _logger = logger;
    }

    public async Task<string> ExportReconstructedProjectAsync(
        string targetDirectory,
        string projectName,
        IEnumerable<ExtractedCodeSnippet> snippets,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(targetDirectory))
            throw new ArgumentException("مسار مجلد التصدير فارغ.", nameof(targetDirectory));

        var cleanProjectName = string.Join("_", projectName.Split(Path.GetInvalidFileNameChars()));
        if (string.IsNullOrWhiteSpace(cleanProjectName)) cleanProjectName = "ReconstructedApp";

        var projectFolder = Path.Combine(targetDirectory, cleanProjectName);
        Directory.CreateDirectory(projectFolder);

        _logger.Info($"Exporting reconstructed project to: {projectFolder}");

        var reportSb = new StringBuilder();
        reportSb.AppendLine($"# تقرير إعادة بناء وتصدير المشروع · CodeVision Studio Cyber Edition");
        reportSb.AppendLine($"**اسم المشروع:** {cleanProjectName}");
        reportSb.AppendLine($"**تاريخ التصدير:** {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        reportSb.AppendLine($"**محرك إعادة البناء:** SequenceMatcher + Unity Categorizer v5.0");
        reportSb.AppendLine();
        reportSb.AppendLine("## قائمة الملفات المستعادة والأدلة البرمجية:");
        reportSb.AppendLine();

        bool hasUnity = false;
        bool hasCSharp = false;

        // Write source files
        foreach (var snippet in snippets)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var relativePath = string.IsNullOrWhiteSpace(snippet.TargetFilePath) ? "Program.cs" : snippet.TargetFilePath;
            
            // Clean relative path
            relativePath = relativePath.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
            var fullPath = Path.Combine(projectFolder, relativePath);

            var dir = Path.GetDirectoryName(fullPath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

            await File.WriteAllTextAsync(fullPath, snippet.CodeContent, Encoding.UTF8, cancellationToken);

            if (snippet.CodeContent.Contains("MonoBehaviour") || snippet.CodeContent.Contains("UnityEngine"))
                hasUnity = true;
            if (snippet.Language.Contains("C#") || relativePath.EndsWith(".cs"))
                hasCSharp = true;

            reportSb.AppendLine($"- **الملف:** `{relativePath}`");
            reportSb.AppendLine($"  - اللغة: {snippet.Language}");
            reportSb.AppendLine($"  - توقيت الفيديو: {snippet.TimestampFormatted}");
            reportSb.AppendLine($"  - درجة الثقة: {snippet.ConfidencePercent}");
            if (snippet.Confidence < 0.85)
            {
                reportSb.AppendLine($"  - ⚠️ *تنبيه:* مقطع ثقته منخفضة نسبياً، يرجى مراجعته يدوياً.");
            }
            reportSb.AppendLine();
        }

        // Generate C# project file if C# snippets present
        if (hasCSharp)
        {
            var csprojPath = Path.Combine(projectFolder, $"{cleanProjectName}.csproj");
            var csprojXml = $@"<Project Sdk=""Microsoft.NET.Sdk"">
  <PropertyGroup>
    <OutputType>Library</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>{cleanProjectName}</RootNamespace>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
</Project>";
            await File.WriteAllTextAsync(csprojPath, csprojXml, Encoding.UTF8, cancellationToken);

            // Generate Visual Studio Solution .sln
            var slnGuid = Guid.NewGuid().ToString("B").ToUpper();
            var projGuid = Guid.NewGuid().ToString("B").ToUpper();
            var slnContent = $@"Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project(""{slnGuid}"") = ""{cleanProjectName}"", ""{cleanProjectName}.csproj"", ""{projGuid}""
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{projGuid}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{projGuid}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{projGuid}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{projGuid}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
EndGlobal
";
            var slnPath = Path.Combine(projectFolder, $"{cleanProjectName}.sln");
            await File.WriteAllTextAsync(slnPath, slnContent, Encoding.UTF8, cancellationToken);
        }

        // Write verification report
        reportSb.AppendLine($"**البيئة المستهدفة:** {(hasUnity ? "محرك ألعاب Unity (Scripts & Components)" : "بيئة .NET 9 القياسية")}");
        var reportPath = Path.Combine(projectFolder, "RECONSTRUCTION_REPORT.md");
        await File.WriteAllTextAsync(reportPath, reportSb.ToString(), Encoding.UTF8, cancellationToken);

        _logger.Info($"Project exported successfully with {snippets.Count()} files to {projectFolder}.");
        return projectFolder;
    }
}
