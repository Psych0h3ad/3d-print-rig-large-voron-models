"""Build the pinned native community printer web assets."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
MAX_PUBLISHED_BYTES=970_000_000
def main():
 if sys.flags.optimize:raise ValueError('Run with explicit nonoptimized asset-integrity guards')
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();target=a.output.resolve()
 if target.exists()or target.is_relative_to(ROOT/'site'):raise ValueError('Use a new build directory')
 source=ROOT/'site';index=json.loads((source/'ASSET_INDEX.json').read_text(encoding='utf-8'));expected={v['path']for v in index['files'].values()}|{'ASSET_INDEX.json','NOTICE.txt'}
 if {f.relative_to(source).as_posix()for f in source.rglob('*')if f.is_file()}!=expected:raise ValueError('Asset index does not match source files')
 total=0
 for r in index['files'].values():
  f=(source/r['path']).resolve()
  if not f.is_relative_to(source.resolve())or f.stat().st_size!=r['bytes']:raise ValueError('Asset escaped source or changed size: '+r['path'])
  with f.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if digest!=r['sha256']:raise ValueError('Asset checksum changed: '+r['path'])
  total+=r['bytes']
 published_bytes=total+(source/'ASSET_INDEX.json').stat().st_size+(source/'NOTICE.txt').stat().st_size
 if published_bytes>=MAX_PUBLISHED_BYTES:raise ValueError('Published site exceeds the conservative 970 MB budget')
 shutil.copytree(source,target);(target/'.nojekyll').touch();print(f'Built {len(expected)} community printer files ({published_bytes:,} published bytes).')
if __name__=='__main__':main()
