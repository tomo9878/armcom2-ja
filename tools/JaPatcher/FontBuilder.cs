using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;
using System.Linq;

namespace JaPatcher
{
    /// <summary>
    /// ゲームのフォント画像（16列×18行）の下に日本語の字を足した画像を作る（tools\build_font.py の C# 版）。
    /// 字は遊ぶ人の Windows のフォントで描く（フォントの画像は配らない）。MS ゴシックは 12/16px にビットマップがありくっきり出る。
    /// </summary>
    public static class FontBuilder
    {
        private const int Cols = 16, BaseRows = 18;
        private static readonly string[] Candidates = { "MS Gothic", "ＭＳ ゴシック", "BIZ UDGothic", "Yu Gothic", "Meiryo" };
        public static string FontName { get; private set; }

        private static string PickFont()
        {
            using (var installed = new InstalledFontCollection())
            {
                var names = installed.Families.Select(f => f.Name).ToList();
                foreach (var c in Candidates)
                    if (names.Contains(c)) return c;
            }
            throw new Exception("日本語フォント（MS ゴシックなど）が見つかりません。Windows の設定 → 言語 → 日本語の「補助フォント」を追加してください。");
        }

        public static void Build(string basePng, string chars, int size, string outPng)
        {
            if (FontName == null) FontName = PickFont();
            int rows = BaseRows + (chars.Length + Cols - 1) / Cols;
            using (var baseImg = new Bitmap(basePng))
            using (var img = new Bitmap(Cols * size, rows * size, PixelFormat.Format32bppArgb))
            using (var glyph = new Bitmap(size, size, PixelFormat.Format32bppArgb))
            using (var font = new Font(FontName, size, FontStyle.Regular, GraphicsUnit.Pixel))
            using (var fmt = (StringFormat)StringFormat.GenericTypographic.Clone())
            {
                using (var g = Graphics.FromImage(img))
                {
                    g.Clear(Color.Transparent);
                    g.CompositingMode = CompositingMode.SourceCopy;
                    g.DrawImage(baseImg, new Rectangle(0, 0, baseImg.Width, baseImg.Height));
                }
                fmt.FormatFlags |= StringFormatFlags.NoClip;
                for (int i = 0; i < chars.Length; i++)
                {
                    using (var g = Graphics.FromImage(glyph))
                    {
                        g.Clear(Color.Black);
                        g.TextRenderingHint = TextRenderingHint.SingleBitPerPixelGridFit;
                        g.DrawString(chars[i].ToString(), font, Brushes.White, 0, 0, fmt);
                    }
                    int n = Cols * BaseRows + i, ox = (n % Cols) * size, oy = (n / Cols) * size;
                    for (int y = 0; y < size; y++)
                        for (int x = 0; x < size; x++)
                            img.SetPixel(ox + x, oy + y, glyph.GetPixel(x, y).R > 127 ? Color.White : Color.Transparent);
                }
                img.Save(outPng, ImageFormat.Png);
            }
        }
    }
}
