using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace JaPatcher
{
    /// <summary>ゲームフォルダを探す。引数 → ツールの場所（ゲームフォルダの中に展開した場合）→ Steam のライブラリ → 手入力の順。</summary>
    public static class GameLocator
    {
        public static string Find(string steamFolder, string exeName, string[] args)
        {
            foreach (var a in args.Where(a => !a.StartsWith("--")))
                if (File.Exists(Path.Combine(a, exeName))) return Path.GetFullPath(a);

            for (var d = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory); d != null; d = d.Parent)
                if (File.Exists(Path.Combine(d.FullName, exeName))) return d.FullName;

            foreach (var lib in SteamLibraries())
            {
                var dir = Path.Combine(lib, "steamapps", "common", steamFolder);
                if (File.Exists(Path.Combine(dir, exeName))) return dir;
            }

            while (true)
            {
                Program.Log("ゲームのフォルダが見つかりませんでした。" + exeName + " のあるフォルダを入力してください:");
                var line = (Console.ReadLine() ?? "").Trim().Trim('"');
                if (line == "") throw new Exception("中止しました");
                if (File.Exists(Path.Combine(line, exeName))) return line;
            }
        }

        private static IEnumerable<string> SteamLibraries()
        {
            var roots = new List<string>();
            foreach (var (hive, key, name) in new[]
            {
                (Registry.CurrentUser, @"Software\Valve\Steam", "SteamPath"),
                (Registry.LocalMachine, @"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                (Registry.LocalMachine, @"SOFTWARE\Valve\Steam", "InstallPath"),
            })
            {
                try
                {
                    if (hive.OpenSubKey(key)?.GetValue(name) is string p && p != "") roots.Add(p.Replace('/', '\\'));
                }
                catch { }
            }
            roots.Add(@"C:\Program Files (x86)\Steam");

            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var re = new Regex("\"path\"\\s+\"(.+?)\"");
            foreach (var root in roots)
            {
                if (seen.Add(root)) yield return root;
                var vdf = Path.Combine(root, "steamapps", "libraryfolders.vdf");
                if (!File.Exists(vdf)) continue;
                foreach (Match m in re.Matches(File.ReadAllText(vdf)))
                {
                    var lib = m.Groups[1].Value.Replace(@"\\", @"\");
                    if (seen.Add(lib)) yield return lib;
                }
            }
        }
    }
}
