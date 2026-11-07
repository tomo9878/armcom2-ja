using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;

namespace JaPatcher
{
    /// <summary>
    /// PyInstaller の exe（末尾の CArchive）の起動スクリプト armcom2 を、
    /// exec(compile(open('ja\\boot.py','rb').read(), 'ja\\boot.py', 'exec')) だけのコードに差し替える。
    /// tools\patch_exe.py の C# 版。ほかの中身はバイト単位でそのまま並べ直す。
    /// </summary>
    public static class ExePatcher
    {
        private static readonly byte[] Cookie = { (byte)'M', (byte)'E', (byte)'I', 0x0c, 0x0b, 0x0a, 0x0b, 0x0e };
        private const int CookieLen = 88;
        private const string Entry = "armcom2";

        private sealed class TocEntry
        {
            public int EntryLen; public byte[] RawName; public string Name;
            public byte[] Data; public int ULen; public byte Flag; public byte Type;
        }

        /// <summary>Python 3.6 の marshal 形式で書いた差し替えコード</summary>
        public static readonly byte[] Stub = BuildStub();

        public static bool IsPatched(byte[] exe)
        {
            var e = ReadToc(exe, out _, out _).FirstOrDefault(t => t.Name == Entry && t.Type == (byte)'s');
            if (e == null) throw new Exception("armcom2.exe の中に起動スクリプトが見つかりません（対応していない版です）");
            byte[] code = e.Flag != 0 ? Inflate(e.Data) : e.Data;
            return code.SequenceEqual(Stub);
        }

        public static byte[] Patch(byte[] exe)
        {
            var toc = ReadToc(exe, out int start, out byte[] cookie);
            var body = new MemoryStream();
            var tocBytes = new MemoryStream();
            bool done = false;
            foreach (var e in toc)
            {
                if (e.Name == Entry && e.Type == (byte)'s')
                {
                    e.Data = e.Flag != 0 ? Deflate(Stub) : Stub;
                    e.ULen = Stub.Length;
                    done = true;
                }
                WriteBE(tocBytes, e.EntryLen); WriteBE(tocBytes, (int)body.Length); WriteBE(tocBytes, e.Data.Length); WriteBE(tocBytes, e.ULen);
                tocBytes.WriteByte(e.Flag); tocBytes.WriteByte(e.Type); tocBytes.Write(e.RawName, 0, e.RawName.Length);
                body.Write(e.Data, 0, e.Data.Length);
            }
            if (!done) throw new Exception("armcom2.exe の中に起動スクリプトが見つかりません");
            int tocPos = (int)body.Length;
            body.Write(tocBytes.ToArray(), 0, (int)tocBytes.Length);
            int pkgLen = (int)body.Length + CookieLen;
            var outp = new MemoryStream();
            outp.Write(exe, 0, start);
            body.WriteTo(outp);
            outp.Write(cookie, 0, 8);
            WriteBE(outp, pkgLen); WriteBE(outp, tocPos); WriteBE(outp, (int)tocBytes.Length);
            outp.Write(cookie, 20, CookieLen - 20);   // Python のバージョンと DLL 名はそのまま
            return outp.ToArray();
        }

        private static List<TocEntry> ReadToc(byte[] d, out int start, out byte[] cookie)
        {
            int ci = LastIndexOf(d, Cookie);
            if (ci < 0) throw new Exception("armcom2.exe が PyInstaller 形式ではありません（対応していない版です）");
            cookie = d.Skip(ci).Take(CookieLen).ToArray();
            int pkgLen = ReadBE(d, ci + 8), tocPos = ReadBE(d, ci + 12), tocLen = ReadBE(d, ci + 16);
            start = d.Length - pkgLen;
            var list = new List<TocEntry>();
            int p = start + tocPos, end = p + tocLen;
            while (p < end)
            {
                int len = ReadBE(d, p), pos = ReadBE(d, p + 4), clen = ReadBE(d, p + 8), ulen = ReadBE(d, p + 12);
                var raw = d.Skip(p + 18).Take(len - 18).ToArray();
                list.Add(new TocEntry
                {
                    EntryLen = len, RawName = raw, Name = Encoding.UTF8.GetString(raw).TrimEnd('\0'),
                    Data = d.Skip(start + pos).Take(clen).ToArray(), ULen = ulen, Flag = d[p + 16], Type = d[p + 17],
                });
                p += len;
            }
            return list;
        }

        private static byte[] BuildStub()
        {
            // LOAD_NAME exec, compile, open / LOAD_CONST path, 'rb' / CALL 2 / LOAD_ATTR read / CALL 0 /
            // LOAD_CONST path, 'exec' / CALL 3 / CALL 1 / POP_TOP / LOAD_CONST None / RETURN_VALUE
            byte[] code = { 101, 0, 101, 1, 101, 2, 100, 0, 100, 1, 131, 2, 106, 3, 131, 0, 100, 0, 100, 2, 131, 3, 131, 1, 1, 0, 100, 3, 83, 0 };
            var m = new MemoryStream();
            m.WriteByte((byte)'c');
            foreach (int v in new[] { 0, 0, 0, 10, 0x40 }) WriteLE(m, v);
            MBytes(m, code);
            MTuple(m, "ja\\boot.py", "rb", "exec", null);
            MTuple(m, "exec", "compile", "open", "read");
            MTuple(m); MTuple(m); MTuple(m);
            MStr(m, "armcom2_ja_stub"); MStr(m, "<module>");
            WriteLE(m, 1);
            MBytes(m, new byte[0]);
            return m.ToArray();
        }

        private static void MBytes(Stream m, byte[] b) { m.WriteByte((byte)'s'); WriteLE(m, b.Length); m.Write(b, 0, b.Length); }
        private static void MStr(Stream m, string s) { var b = Encoding.UTF8.GetBytes(s); m.WriteByte((byte)'u'); WriteLE(m, b.Length); m.Write(b, 0, b.Length); }
        private static void MTuple(Stream m, params string[] items)
        {
            m.WriteByte((byte)'('); WriteLE(m, items.Length);
            foreach (var s in items) { if (s == null) m.WriteByte((byte)'N'); else MStr(m, s); }
        }

        // zlib 形式（2バイトのヘッダー＋deflate＋Adler-32）
        private static byte[] Deflate(byte[] data)
        {
            var m = new MemoryStream();
            m.WriteByte(0x78); m.WriteByte(0xDA);
            using (var z = new DeflateStream(m, CompressionLevel.Optimal, true)) z.Write(data, 0, data.Length);
            uint a = 1, b = 0;
            foreach (byte x in data) { a = (a + x) % 65521; b = (b + a) % 65521; }
            WriteBE(m, (int)((b << 16) | a));
            return m.ToArray();
        }

        private static byte[] Inflate(byte[] data)
        {
            using (var z = new DeflateStream(new MemoryStream(data, 2, data.Length - 2), CompressionMode.Decompress))
            using (var o = new MemoryStream()) { z.CopyTo(o); return o.ToArray(); }
        }

        private static int ReadBE(byte[] d, int p) => (d[p] << 24) | (d[p + 1] << 16) | (d[p + 2] << 8) | d[p + 3];
        private static void WriteBE(Stream s, int v) { s.WriteByte((byte)(v >> 24)); s.WriteByte((byte)(v >> 16)); s.WriteByte((byte)(v >> 8)); s.WriteByte((byte)v); }
        private static void WriteLE(Stream s, int v) { s.WriteByte((byte)v); s.WriteByte((byte)(v >> 8)); s.WriteByte((byte)(v >> 16)); s.WriteByte((byte)(v >> 24)); }

        private static int LastIndexOf(byte[] d, byte[] pat)
        {
            for (int i = d.Length - pat.Length; i >= 0; i--)
            {
                int j = 0;
                while (j < pat.Length && d[i + j] == pat[j]) j++;
                if (j == pat.Length) return i;
            }
            return -1;
        }
    }
}
