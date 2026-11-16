using System.Runtime.InteropServices;

namespace CodeVision.Desktop.Services;

public static class NativeFileDialogs
{
    [DllImport("user32.dll")]
    private static extern IntPtr GetActiveWindow();

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    private static IntPtr GetOwnerHwnd(IntPtr fallback)
    {
        var active = GetActiveWindow();
        if (active != IntPtr.Zero) return active;
        var fg = GetForegroundWindow();
        if (fg != IntPtr.Zero) return fg;
        return fallback;
    }

    public static string? PickSingleVideoFile(IntPtr parentHwnd = default)
    {
        try
        {
            var dialog = (IFileOpenDialog)new FileOpenDialogRCW();
            dialog.SetTitle("اختر ملف الفيديو التعليمي (CodeVision Video Lesson)");
            dialog.SetOptions(FOS.FOS_FORCEFILESYSTEM | FOS.FOS_FILEMUSTEXIST | FOS.FOS_PATHMUSTEXIST);

            var filters = new[]
            {
                new COMDLG_FILTERSPEC { pszName = "Video Files (*.mp4;*.mkv;*.mov;*.avi;*.webm)", pszSpec = "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.m4v;*.flv" },
                new COMDLG_FILTERSPEC { pszName = "All Files (*.*)", pszSpec = "*.*" }
            };
            dialog.SetFileTypes((uint)filters.Length, filters);

            var owner = GetOwnerHwnd(parentHwnd);
            var hr = dialog.Show(owner);
            if (hr != 0) return null; // Cancelled

            dialog.GetResult(out var item);
            item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH, out var path);
            return path;
        }
        catch
        {
            return null;
        }
    }

    public static List<string> PickMultipleVideoFiles(IntPtr parentHwnd = default)
    {
        var results = new List<string>();
        try
        {
            var dialog = (IFileOpenDialog)new FileOpenDialogRCW();
            dialog.SetTitle("اختر حزمة فيديوهات تعليمية (Batch Videos)");
            dialog.SetOptions(FOS.FOS_FORCEFILESYSTEM | FOS.FOS_FILEMUSTEXIST | FOS.FOS_PATHMUSTEXIST | FOS.FOS_ALLOWMULTISELECT);

            var filters = new[]
            {
                new COMDLG_FILTERSPEC { pszName = "Video Files (*.mp4;*.mkv;*.mov;*.avi;*.webm)", pszSpec = "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.m4v;*.flv" },
                new COMDLG_FILTERSPEC { pszName = "All Files (*.*)", pszSpec = "*.*" }
            };
            dialog.SetFileTypes((uint)filters.Length, filters);

            var owner = GetOwnerHwnd(parentHwnd);
            var hr = dialog.Show(owner);
            if (hr != 0) return results;

            dialog.GetResults(out var itemArray);
            itemArray.GetCount(out var count);
            for (uint i = 0; i < count; i++)
            {
                itemArray.GetItemAt(i, out var item);
                item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH, out var path);
                if (!string.IsNullOrWhiteSpace(path))
                {
                    results.Add(path);
                }
            }
        }
        catch
        {
        }
        return results;
    }

    public static string? PickFolder(string title = "اختر مجلد الفيديوهات أو مجلد حفظ المشروع", IntPtr parentHwnd = default)
    {
        try
        {
            var dialog = (IFileOpenDialog)new FileOpenDialogRCW();
            dialog.SetTitle(title);
            dialog.SetOptions(FOS.FOS_FORCEFILESYSTEM | FOS.FOS_PATHMUSTEXIST | FOS.FOS_PICKFOLDERS);

            var owner = GetOwnerHwnd(parentHwnd);
            var hr = dialog.Show(owner);
            if (hr != 0) return null; // Cancelled

            dialog.GetResult(out var item);
            item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH, out var path);
            return path;
        }
        catch
        {
            return null;
        }
    }

    #region COM Interop Definitions

    [ComImport]
    [Guid("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")]
    [ClassInterface(ClassInterfaceType.None)]
    private class FileOpenDialogRCW { }

    [ComImport]
    [Guid("d57c7288-d4ad-4768-be02-9d969532d960")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IFileOpenDialog
    {
        [PreserveSig] int Show(IntPtr parent);
        void SetFileTypes(uint cFileTypes, [In, MarshalAs(UnmanagedType.LPArray)] COMDLG_FILTERSPEC[] rgFilterSpec);
        void SetFileTypeIndex(uint iFileType);
        void GetFileTypeIndex(out uint piFileType);
        void Advise(IntPtr pfde, out uint pdwCookie);
        void Unadvise(uint dwCookie);
        void SetOptions(FOS fos);
        void GetOptions(out FOS pfos);
        void SetDefaultFolder(IShellItem psi);
        void SetFolder(IShellItem psi);
        void GetFolder(out IShellItem ppsi);
        void GetCurrentSelection(out IShellItem ppsi);
        void SetFileName([MarshalAs(UnmanagedType.LPWStr)] string pszName);
        void GetFileName([MarshalAs(UnmanagedType.LPWStr)] out string pszName);
        void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
        void SetOkButtonLabel([MarshalAs(UnmanagedType.LPWStr)] string pszText);
        void SetFileNameLabel([MarshalAs(UnmanagedType.LPWStr)] string pszLabel);
        void GetResult(out IShellItem ppsi);
        void AddPlace(IShellItem psi, int fdap);
        void SetDefaultExtension([MarshalAs(UnmanagedType.LPWStr)] string pszDefaultExtension);
        void Close(int hr);
        void SetClientGuid(ref Guid guid);
        void ClearClientData();
        void SetFilter(IntPtr pFilter);
        void GetResults(out IShellItemArray ppenum);
        void GetSelectedItems(out IShellItemArray ppsai);
    }

    [ComImport]
    [Guid("43826d1e-e718-42ee-bc55-a1e261c37bfe")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IShellItem
    {
        void BindToHandler(IntPtr pbc, ref Guid bhid, ref Guid riid, out IntPtr ppv);
        void GetParent(out IShellItem ppsi);
        void GetDisplayName(SIGDN sigdnName, [MarshalAs(UnmanagedType.LPWStr)] out string ppszName);
        void GetAttributes(uint sfgaoMask, out uint psfgaoAttribs);
        void Compare(IShellItem psi, uint hint, out int piOrder);
    }

    [ComImport]
    [Guid("b63ea76d-1f85-456f-a19c-48159efa858b")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IShellItemArray
    {
        void BindToHandler(IntPtr pbc, ref Guid rbhid, ref Guid riid, out IntPtr ppvOut);
        void GetPropertyStore(int flags, ref Guid riid, out IntPtr ppv);
        void GetPropertyDescriptionList(ref Guid keyType, ref Guid riid, out IntPtr ppv);
        void GetAttributes(int AttribFlags, uint sfgaoMask, out uint psfgaoAttribs);
        void GetCount(out uint pdwNumItems);
        void GetItemAt(uint dwIndex, out IShellItem ppsi);
        void EnumItems(out IntPtr ppenumShellItems);
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct COMDLG_FILTERSPEC
    {
        [MarshalAs(UnmanagedType.LPWStr)] public string pszName;
        [MarshalAs(UnmanagedType.LPWStr)] public string pszSpec;
    }

    [Flags]
    private enum FOS : uint
    {
        FOS_OVERWRITEPROMPT = 0x2,
        FOS_STRICTFILETYPES = 0x4,
        FOS_NOCHANGEDIR = 0x8,
        FOS_PICKFOLDERS = 0x20,
        FOS_FORCEFILESYSTEM = 0x40,
        FOS_ALLNONSTORAGEITEMS = 0x80,
        FOS_NOVALIDATE = 0x100,
        FOS_ALLOWMULTISELECT = 0x200,
        FOS_PATHMUSTEXIST = 0x800,
        FOS_FILEMUSTEXIST = 0x1000,
        FOS_CREATEPROMPT = 0x2000,
        FOS_SHAREAWARE = 0x4000,
        FOS_NOREADONLYRETURN = 0x8000,
        FOS_NOTESTFILECREATE = 0x10000,
        FOS_HIDEMRUPLACES = 0x20000,
        FOS_HIDEPINNEDPLACES = 0x40000,
        FOS_NODEREFERENCELINKS = 0x100000,
        FOS_OKBUTTONNEEDSINTERACTION = 0x200000,
        FOS_DONTADDTORECENT = 0x2000000,
        FOS_FORCESHOWHIDDEN = 0x10000000,
        FOS_DEFAULTNOMINIMODE = 0x20000000,
        FOS_FORCEPREVIEWPANEON = 0x40000000,
        FOS_SUPPORTSTREAMABLEITEMS = 0x80000000
    }

    private enum SIGDN : uint
    {
        SIGDN_FILESYSPATH = 0x80058000
    }

    #endregion
}
