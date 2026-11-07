using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;

namespace JaPatcher
{
    /// <summary>
    /// Armoured Commander II 日本語化ツール。
    /// ゲームのファイルは配らず、遊ぶ人の PC にある元のファイルから日本語化に必要なものを作る:
    ///   1. armcom2.exe（PyInstaller）の起動スクリプトだけを「ja\boot.py を実行する」小さなコードに差し替える（元は armcom2.exe.jabak）
    ///   2. ja\ に boot.py と訳の表をコピーする（ゲームのソースは起動時に boot.py がメモリ上で直す）
    ///   3. ゲームのフォント画像（data\c64_*_ext.png）の下に、Windows の MS ゴシックで描いた日本語の字を足して ja\font_NN.png を作る
    /// --restore で元に戻す。
    /// </summary>
    public static class Program
    {
        private const string GameFolder = "Armoured Commander II";
        private const string ExeName = "armcom2.exe";
        private static readonly string BaseDir = AppDomain.CurrentDomain.BaseDirectory;
        private static StreamWriter _log;

        public static int Main(string[] args)
        {
            Console.OutputEncoding = Encoding.UTF8;
            Console.Title = "Armoured Commander II 日本語化";
            int code = 0;
            try
            {
                try { _log = new StreamWriter(Path.Combine(BaseDir, "patch-log.txt"), false, new UTF8Encoding(false)); } catch { }
                code = Run(args);
            }
            catch (UnauthorizedAccessException e)
            {
                Log("");
                Log("エラー: ファイルに書き込めませんでした。");
                Log("  ArmCom2_JA.exe を右クリック →「管理者として実行」で試してください。");
                Log("  詳細: " + e.Message);
                code = 1;
            }
            catch (Exception e)
            {
                Log("");
                Log("エラー: " + e.Message);
                if (_log != null) _log.WriteLine(e.ToString());
                code = 1;
            }
            if (_log != null) _log.Dispose();
            if (!args.Contains("--no-pause"))
            {
                Console.WriteLine();
                Console.WriteLine("Enter キーで閉じます。");
                Console.ReadLine();
            }
            return code;
        }

        public static void Log(string s)
        {
            Console.WriteLine(s);
            if (_log != null) _log.WriteLine(s);
        }

        private static int Run(string[] args)
        {
            bool restore = args.Contains("--restore");
            Log("=== Armoured Commander II 日本語化" + (restore ? "（元に戻す）" : "") + " ===");
            Log("");
            string gameDir = GameLocator.Find(GameFolder, ExeName, args);
            Log("ゲーム: " + gameDir);
            WaitGameClosed();

            string exe = Path.Combine(gameDir, ExeName);
            string backup = exe + ".jabak";
            string jaDir = Path.Combine(gameDir, "ja");
            return restore ? Restore(exe, backup, jaDir) : Patch(gameDir, exe, backup, jaDir);
        }

        private static int Patch(string gameDir, string exe, string backup, string jaDir)
        {
            if (!File.Exists(Path.Combine(gameDir, "src", "armcom2.py")))
                throw new Exception(@"ゲームの src\armcom2.py が見つかりません。Steam で「ファイルの整合性を確認」してから実行してください。");

            // 1. exe
            byte[] current = File.ReadAllBytes(exe);
            if (ExePatcher.IsPatched(current))
            {
                Log("1/3 exe: すでに日本語化済みです（そのまま）");
            }
            else
            {
                File.WriteAllBytes(backup, current);   // ゲーム更新で exe が戻った場合も、新しい exe をバックアップし直す
                File.WriteAllBytes(exe, ExePatcher.Patch(current));
                Log("1/3 exe: 起動部分を差し替えました（元の exe は " + Path.GetFileName(backup) + "）");
            }

            // 2. ja フォルダ
            string src = Path.Combine(BaseDir, "ja");
            if (!Directory.Exists(src)) throw new Exception("同じフォルダに ja フォルダがありません。ZIP を全部展開してから実行してください。");
            Directory.CreateDirectory(jaDir);
            foreach (string f in Directory.GetFiles(src))
                File.Copy(f, Path.Combine(jaDir, Path.GetFileName(f)), true);
            Log("2/3 訳の表と起動スクリプトをコピーしました");

            // 3. フォント
            // 先頭は全角スペース（U+3000）。Trim() すると消えて字の位置が1つずれるので改行だけ取る
            string chars = File.ReadAllText(Path.Combine(jaDir, "font_chars.txt"), Encoding.UTF8).TrimEnd('\r', '\n');
            foreach (int size in new[] { 8, 12, 16 })
            {
                string basePng = Path.Combine(gameDir, "data", string.Format("c64_{0}x{0}_ext.png", size));
                FontBuilder.Build(basePng, chars, size, Path.Combine(jaDir, string.Format("font_{0}.png", size)));
            }
            Log("3/3 日本語フォントを作りました（" + chars.Length + "字、" + FontBuilder.FontName + "）");
            Log("");
            Log("完了しました。ゲームを起動してください。");
            Log("ゲームの設定でフォントサイズを 16x16 にすると読みやすくなります。");
            return 0;
        }

        private static int Restore(string exe, string backup, string jaDir)
        {
            if (File.Exists(backup))
            {
                File.Copy(backup, exe, true);
                File.Delete(backup);
                Log("exe を元に戻しました");
            }
            else if (ExePatcher.IsPatched(File.ReadAllBytes(exe)))
            {
                throw new Exception("バックアップ（armcom2.exe.jabak）がありません。Steam で「ファイルの整合性を確認」すると元に戻ります。");
            }
            else
            {
                Log("exe は日本語化されていません（そのまま）");
            }
            if (Directory.Exists(jaDir))
            {
                Directory.Delete(jaDir, true);
                Log("ja フォルダを消しました");
            }
            Log("");
            Log("元に戻しました。");
            return 0;
        }

        private static void WaitGameClosed()
        {
            while (Process.GetProcessesByName("armcom2").Length > 0)
            {
                Log("ゲームが起動中です。ゲームを終了してから Enter キーを押してください。");
                if (Console.ReadLine() == null) throw new Exception("ゲームが起動中のため中止しました");
            }
        }
    }
}
