# The 2023 DVSA zip uses Deflate64, which Python zipfile cannot open. Usage: python 0_unzip_2023_deflate64.py <zip> <output.csv>
import struct, inflate64, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src,'rb') as f, open(dst,'wb') as o:
    h=f.read(30); assert h[:4]==b'PK\x03\x04'
    method=struct.unpack('<H',h[8:10])[0]; n,m=struct.unpack('<HH',h[26:30]); assert method==9
    f.read(n+m)
    d=inflate64.Inflater()
    while True:
        b=f.read(1<<20)
        if not b: break
        o.write(d.inflate(b))
        if d.eof: break
