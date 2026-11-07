# armcom2.exe（PyInstaller / Python 3.6）の起動スクリプト armcom2 を、
# 「ja\boot.py を読んで実行する」だけの小さなコードに差し替えた exe を作る。
# 使い方: python patch_exe.py <元の armcom2.exe> <出力先 exe>
# 元の exe は ArmouredCommander2\orig\armcom2.exe に保存してある。
import struct, zlib, sys

COOKIE = b'MEI\x0c\x0b\x0a\x0b\x0e'


# --- Python 3.6 の marshal 形式でコードオブジェクトを書く（最小限） ---
def m_int(n):
    return struct.pack('<i', n)

def m_obj(o):
    if o is None:
        return b'N'
    if isinstance(o, bytes):
        return b's' + m_int(len(o)) + o
    if isinstance(o, str):
        b = o.encode('utf8')
        return b'u' + m_int(len(b)) + b
    if isinstance(o, tuple):
        return b'(' + m_int(len(o)) + b''.join(m_obj(x) for x in o)
    raise TypeError(o)

def m_code(code, consts, names, filename, name, stacksize=10):
    return (b'c' + m_int(0) + m_int(0) + m_int(0) + m_int(stacksize) + m_int(0x40)
            + m_obj(code) + m_obj(consts) + m_obj(names) + m_obj(()) + m_obj(())
            + m_obj(()) + m_obj(filename) + m_obj(name) + m_int(1) + m_obj(b''))

# exec(compile(open('ja\\boot.py','rb').read(), 'ja\\boot.py', 'exec'))
LOAD_CONST, LOAD_NAME, LOAD_ATTR, CALL_FUNCTION, POP_TOP, RETURN_VALUE = 100, 101, 106, 131, 1, 83
ops = [
    (LOAD_NAME, 0), (LOAD_NAME, 1), (LOAD_NAME, 2),
    (LOAD_CONST, 0), (LOAD_CONST, 1), (CALL_FUNCTION, 2),
    (LOAD_ATTR, 3), (CALL_FUNCTION, 0),
    (LOAD_CONST, 0), (LOAD_CONST, 2), (CALL_FUNCTION, 3),
    (CALL_FUNCTION, 1), (POP_TOP, 0),
    (LOAD_CONST, 3), (RETURN_VALUE, 0),
]
STUB = m_code(bytes(b for op in ops for b in op),
              ('ja\\boot.py', 'rb', 'exec', None),
              ('exec', 'compile', 'open', 'read'),
              'armcom2_ja_stub', '<module>')


def main(src, dst):
    d = open(src, 'rb').read()
    ci = d.rfind(COOKIE)
    magic, pkglen, tocpos, toclen, pyver, pylib = struct.unpack('!8sIIII64s', d[ci:ci+88])
    start = len(d) - pkglen
    p, end = start + tocpos, start + tocpos + toclen
    entries = []
    while p < end:
        ln, pos, clen, ulen, flag, typ = struct.unpack('!IIIIBc', d[p:p+18])
        rawname = d[p+18:p+ln]
        name = rawname.rstrip(b'\0').decode()
        data = d[start+pos:start+pos+clen]
        if name == 'armcom2' and typ == b's':
            data = zlib.compress(STUB, 9) if flag else STUB
            ulen = len(STUB)
            print('armcom2 を差し替え', clen, '->', len(data))
        entries.append([rawname, ln, data, ulen, flag, typ])
        p += ln
    body = b''
    toc = b''
    for rawname, ln, data, ulen, flag, typ in entries:
        toc += struct.pack('!IIIIBc', ln, len(body), len(data), ulen, flag, typ) + rawname
        body += data
    newtocpos = len(body)
    pkg = body + toc
    newpkglen = len(pkg) + 88
    cookie = struct.pack('!8sIIII64s', magic, newpkglen, newtocpos, len(toc), pyver, pylib)
    open(dst, 'wb').write(d[:start] + pkg + cookie)
    print('書き出し', dst, len(d[:start] + pkg + cookie))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
