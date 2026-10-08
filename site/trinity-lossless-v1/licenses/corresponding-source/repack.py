# SPDX-License-Identifier: GPL-3.0-only
"""Exact Trinity GLB storage repack and accessor-only chunk recipe.

Input geometry is not simplified, quantized, repaired, omitted or transformed.
All embedded CAD retains its separate original authors and license conditions.
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import argparse
import collections
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

SOURCE_SHA = 'ff8557d93e9d3803b3e4ba2729d6fb947c4134c2e84098a653069ce337d2fcfb'
RESULT_SHA = 'f2478be82bef8b1f767a09320e4310c3c426df9246b45ed97992c8e903f6fde2'
MAX_CHUNK = 32 * 1024 * 1024
PAYLOAD_LIMIT = MAX_CHUNK - 256 * 1024
BLOCK = 4 * 1024 * 1024
DTYPES = {5126:'<f4',5125:'<u4',5123:'<u2'}
WIDTHS = {'VEC3':3,'SCALAR':1}

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def header(path):
    with Path(path).open('rb') as f:
        magic,version,total = struct.unpack('<4sII',f.read(12))
        assert magic==b'glTF' and version==2 and total==Path(path).stat().st_size
        size,kind=struct.unpack('<II',f.read(8));assert kind==0x4e4f534a
        g=json.loads(f.read(size))
        binary,kind=struct.unpack('<II',f.read(8));assert kind==0x004e4942
        offset=f.tell();assert offset+binary==total
    return g,offset,binary

def read(g,f,offset,ai):
    a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']]
    dtype=np.dtype(DTYPES[a['componentType']]);width=WIDTHS[a['type']]
    assert 'sparse' not in a and v['buffer']==0 and v.get('byteStride',dtype.itemsize*width)==dtype.itemsize*width
    f.seek(offset+v.get('byteOffset',0)+a.get('byteOffset',0))
    size=a['count']*width*dtype.itemsize
    value=f.read(size);assert len(value)==size
    return np.frombuffer(value,dtype=dtype).reshape(a['count'],width)

def glb(path,g,binary_path):
    size=Path(binary_path).stat().st_size
    j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode('utf-8');j+=b' '*((-len(j))%4)
    with Path(path).open('wb') as dst,Path(binary_path).open('rb') as src:
        dst.write(struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+size))
        dst.write(struct.pack('<II',len(j),0x4e4f534a));dst.write(j)
        dst.write(struct.pack('<II',size,0x004e4942))
        while b:=src.read(BLOCK):dst.write(b)

def repack(source_path,out):
    source_path=Path(source_path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert sha(source_path)==SOURCE_SHA
    source,offset,_=header(source_path)
    assert not any(source.get(k) for k in ('animations','skins','images','textures','extensionsUsed','extensionsRequired'))
    assert len(source['nodes'])==205 and len(source['meshes'])==205
    result=copy.deepcopy(source);result['accessors']=[];result['bufferViews']=[];result['buffers']=[{'byteLength':0}]
    current=0;binary=out/'repack-payload.bin'
    def emit(dst,array,original,component_type=None):
        nonlocal current
        pad=(-current)%4
        if pad:dst.write(b'\x00'*pad);current+=pad
        array=np.ascontiguousarray(array)
        vi=len(result['bufferViews'])
        result['bufferViews'].append(dict(buffer=0,byteOffset=current,byteLength=array.nbytes))
        dst.write(memoryview(array).cast('B'));current+=array.nbytes
        a={k:copy.deepcopy(v) for k,v in original.items() if k not in ('bufferView','byteOffset','count','componentType')}
        a.update(bufferView=vi,count=len(array),componentType=component_type or original['componentType'])
        ai=len(result['accessors']);result['accessors'].append(a)
        return ai
    with source_path.open('rb') as src,binary.open('wb') as dst:
        for mi,mesh in enumerate(source['meshes']):
            groups=collections.defaultdict(list)
            for pi,p in enumerate(mesh['primitives']):
                assert p.get('mode',4)==4 and set(p)<= {'attributes','indices','mode','material','extras'}
                groups[tuple(sorted(p['attributes'].items()))].append(pi)
            for signature,pis in groups.items():
                arrays=[(key,ai,read(source,src,offset,ai)) for key,ai in signature]
                count=len(arrays[0][2]);assert all(len(a)==count and np.isfinite(a).all() for _,_,a in arrays)
                assert all(source['accessors'][ai]['componentType']==5126 and source['accessors'][ai]['type']=='VEC3' for _,ai,_ in arrays)
                width=sum(a.dtype.itemsize*a.shape[1] for _,_,a in arrays)
                records=np.empty((count,width),dtype=np.uint8);start=0
                for _,_,array in arrays:
                    w=array.dtype.itemsize*array.shape[1];records[:,start:start+w]=array.view(np.uint8).reshape(count,w);start+=w
                unique,first,inverse=np.unique(records.view(f'V{width}').ravel(),return_index=True,return_inverse=True)
                unique_count=len(unique);del unique,records
                order=np.argsort(first);perm=np.empty(unique_count,dtype=np.int64);perm[order]=np.arange(unique_count,dtype=np.int64)
                inverse=perm[inverse];first=first[order];del order,perm
                ctype=5123 if unique_count<=65536 else 5125
                indices=sum(source['accessors'][mesh['primitives'][pi]['indices']]['count'] for pi in pis)
                unindexed=indices*width<unique_count*width+indices*(2 if ctype==5123 else 4)
                if unindexed:
                    for pi in pis:
                        p=mesh['primitives'][pi];q=result['meshes'][mi]['primitives'][pi]
                        ix=read(source,src,offset,p['indices']).ravel();attrs={}
                        assert ix.size%3==0 and int(ix.max(initial=0))<count
                        for key,ai,array in arrays:
                            expanded=array[ix];attrs[key]=emit(dst,expanded,source['accessors'][ai]);del expanded
                        q['attributes']=attrs;q.pop('indices');del ix
                else:
                    attrs={}
                    for key,ai,array in arrays:
                        compact=array[first];attrs[key]=emit(dst,compact,source['accessors'][ai]);del compact
                    for pi in pis:
                        p=mesh['primitives'][pi];q=result['meshes'][mi]['primitives'][pi]
                        ix=read(source,src,offset,p['indices']).ravel()
                        mapped=inverse[ix].astype('<u2' if ctype==5123 else '<u4')
                        metadata=copy.deepcopy(source['accessors'][p['indices']])
                        metadata['min']=[int(mapped.min(initial=unique_count-1))];metadata['max']=[int(mapped.max(initial=0))]
                        q['attributes']=attrs.copy();q['indices']=emit(dst,mapped.reshape(-1,1),metadata,ctype)
                        del ix,mapped
                del arrays,inverse,first
        pad=(-current)%4
        if pad:dst.write(b'\x00'*pad);current+=pad
    result['buffers'][0]['byteLength']=current
    path=out/'repacked.glb';glb(path,result,binary)
    assert sha(path)==RESULT_SHA
    return path

def chunk(path,out):
    path=Path(path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert sha(path)==RESULT_SHA
    source,offset,_=header(path)
    (out/'assembly.gltf.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
    with path.open('rb') as f:(out/'reassembly-prefix.bin').write_bytes(f.read(offset))
    binary=out/'chunk-payload.bin';payload=None;accessors=[];views=[];current=0;files=[]
    def begin():
        nonlocal payload,accessors,views,current
        payload=binary.open('wb');accessors=[];views=[];current=0
    def finish():
        nonlocal payload,current
        if payload is None:return
        pad=(-current)%4
        if pad:payload.write(b'\x00'*pad);current+=pad
        payload.close();payload=None
        g=dict(asset=copy.deepcopy(source['asset']),scene=0,scenes=[dict(nodes=[])],nodes=[],buffers=[dict(byteLength=current)],bufferViews=views,accessors=accessors,
               extras=dict(delivery_only=True,logical_nodes_in_manifest=True))
        target=out/f'chunk-{len(files):03d}.glb';glb(target,g,binary);assert target.stat().st_size<=MAX_CHUNK
        zipped=out/(target.name+'.gz')
        with target.open('rb') as src,zipped.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9) as dst:
            while value:=src.read(BLOCK):dst.write(value)
        files.append(target)
    with path.open('rb') as src:
        for a in source['accessors']:
            view=source['bufferViews'][a['bufferView']];dtype=np.dtype(DTYPES[a['componentType']]);width=WIDTHS[a['type']];item_bytes=dtype.itemsize*width;first=0
            while first<a['count']:
                if payload is None:begin()
                pad=(-current)%4;count=min(a['count']-first,(PAYLOAD_LIMIT-current-pad)//item_bytes)
                if count<1:finish();continue
                if pad:payload.write(b'\x00'*pad);current+=pad
                src.seek(offset+view.get('byteOffset',0)+a.get('byteOffset',0)+first*item_bytes)
                value=src.read(count*item_bytes);assert len(value)==count*item_bytes
                local=copy.deepcopy(a);local.update(count=count,bufferView=len(views));local.pop('byteOffset',None)
                array=np.frombuffer(value,dtype=dtype).reshape(count,width)
                if 'min' in local:local['min']=array.min(axis=0).tolist()
                if 'max' in local:local['max']=array.max(axis=0).tolist()
                views.append(dict(buffer=0,byteOffset=current,byteLength=len(value)));accessors.append(local)
                payload.write(value);current+=len(value);first+=count;del array,value
                if current>=PAYLOAD_LIMIT-12:finish()
    finish();assert len(files)==11
    return files

def validate_reference(out,reference):
    out=Path(out);reference=Path(reference)
    manifest=json.loads((reference/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['schema']=='trinity98-lossless-accessor-chunks-v1'
    for name in ('assembly','reassembly_prefix'):
        record=manifest[name];assert sha(out/record['path'])==record['sha256']
    for r in manifest['chunks']:
        f=r['file'];assert sha(out/f['path'])==f['sha256']
        assert sha(out/r['decoded_file'])==f['decoded_sha256']
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path)
    args=p.parse_args();path=repack(args.source,args.output);chunk(path,args.output)
    if args.reference:validate_reference(args.output,args.reference)
    print(RESULT_SHA)
