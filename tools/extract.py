# PyInstaller (Python 3.6) の armcom2.exe から CArchive の中身と PYZ を取り出す
import struct, zlib, marshal, sys, os
exe, out = sys.argv[1], sys.argv[2]
d = open(exe, 'rb').read()
ci = d.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
magic, pkglen, tocpos, toclen, pyver, pylib = struct.unpack('!8sIIII64s', d[ci:ci+88])
start = len(d) - pkglen
p = start + tocpos; end = p + toclen
toc = []
while p < end:
    ln, pos, clen, ulen, flag, typ = struct.unpack('!IIIIBc', d[p:p+18])
    name = d[p+18:p+ln].rstrip(b'\0').decode()
    toc.append((name, start+pos, clen, ulen, flag, typ.decode())); p += ln
os.makedirs(out, exist_ok=True)
for name, pos, clen, ulen, flag, typ in toc:
    data = d[pos:pos+clen]
    if flag: data = zlib.decompress(data)
    print(typ, name, clen, ulen)
    fn = os.path.join(out, name.replace('/', '_') + ('.bin' if typ in 'sm' else ''))
    open(fn, 'wb').write(data)
# PYZ
pyz = [t for t in toc if t[5] == 'z'][0]
data = open(os.path.join(out, pyz[0].replace('/', '_')), 'rb').read()
assert data[:4] == b'PYZ\0'
tocoff = struct.unpack('!i', data[8:12])[0]
# TOC is marshal of a list of (name, (ispkg, pos, len)) -- 3.6 marshal of simple types is readable by modern marshal
ptoc = marshal.loads(data[tocoff:])
names = [n for n, _ in ptoc]
print('PYZ modules', len(names))
open(os.path.join(out, 'pyz_modules.txt'), 'w').write('\n'.join(sorted(names)))
