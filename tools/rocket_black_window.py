# Rocket window glass -> black (base colour) and not metallic, a bit glossy (metal/rough map), rewritten into the GLB.
# Usage: py -3.10 tools/rocket_black_window.py "C:/Users/ahmma/Downloads/Pash 3D/props/optimized/space_rocket.glb" models/space_rocket.glb
import sys,json,struct,io
import numpy as np
from PIL import Image
src,dst=sys.argv[1],sys.argv[2];b=open(src,'rb').read()
jl=struct.unpack('<I',b[12:16])[0];J=json.loads(b[20:20+jl]);bin0=20+jl+8;binl=struct.unpack('<I',b[20+jl:24+jl])[0];BIN=b[bin0:bin0+binl]
img=lambda i:(lambda v:np.array(Image.open(io.BytesIO(BIN[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGB')).astype(float))(J['bufferViews'][J['images'][i]['bufferView']])
m=J['materials'][0]['pbrMetallicRoughness'];src_=lambda t:t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));ci=src_(J['textures'][m['baseColorTexture']['index']]);mi=src_(J['textures'][m['metallicRoughnessTexture']['index']])
a=img(ci);k=np.clip((np.minimum(a[...,1],a[...,2])-a[...,0]-20)/40,0,1)[...,None]
from scipy import ndimage
k=np.maximum(k,ndimage.grey_dilation(k[...,0],size=5)[...,None]*(np.minimum(a[...,1],a[...,2])>a[...,0]+5)[...,None]) # catch the pale rim of the glass too
a=a*(1-k)+np.array([14,16,22])*k
t=img(mi);t=t*(1-k)+np.array([255,70,0])*k   # glTF: G = roughness (glossy), B = metal (none)
enc=lambda x:(lambda o:(Image.fromarray(x.astype(np.uint8)).save(o,'WEBP',quality=90),o.getvalue())[1])(io.BytesIO())
new={J['images'][ci]['bufferView']:enc(a),J['images'][mi]['bufferView']:enc(t)};parts=[];off=0
for i,v in enumerate(J['bufferViews']):
    d=new.get(i) or BIN[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    v['byteOffset']=off;v['byteLength']=len(d);parts.append(d+b'\0'*(-len(d)%4));off+=len(parts[-1])
nb=b''.join(parts);J['buffers'][0]['byteLength']=len(nb)
js=json.dumps(J,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
open(dst,'wb').write(b'glTF'+struct.pack('<II',2,28+len(js)+len(nb))+struct.pack('<I',len(js))+b'JSON'+js+struct.pack('<I',len(nb))+b'BIN\0'+nb)
print('ok glass px',int((k[...,0]>.5).sum()))
