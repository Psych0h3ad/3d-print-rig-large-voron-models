"""Small source fixtures for the asset index/integrity gate, not model checks."""
from pathlib import Path
import hashlib,json,sys,tempfile,types,unittest
from unittest.mock import patch
import build_site as builder

class AssetIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.site=self.root/'site';self.site.mkdir();self.output=self.root/'built'
        self.body=b'Public integrity fixture';(self.site/'fixture.asset').write_bytes(self.body)
        self.index={'schema':'large-voron-assets-1','files':{'fixture':{'path':'fixture.asset','bytes':len(self.body),'sha256':hashlib.sha256(self.body).hexdigest()}}}
        (self.site/'NOTICE.txt').write_text('Fixture notices\n','utf8');self.write_index()
    def tearDown(self):self.tmp.cleanup()
    def write_index(self):(self.site/'ASSET_INDEX.json').write_text(json.dumps(self.index),'utf8')
    def run_build(self):
        with patch.object(builder,'ROOT',self.root),patch.object(sys,'argv',['build_site.py','--output',str(self.output)]):builder.main()
    def rejected(self,pattern):
        with self.assertRaisesRegex(ValueError,pattern):self.run_build()
        self.assertFalse(self.output.exists())
    def test_valid_index(self):
        self.run_build();self.assertEqual((self.output/'fixture.asset').read_bytes(),self.body);self.assertTrue((self.output/'.nojekyll').is_file())
    def test_changed_bytes(self):
        (self.site/'fixture.asset').write_bytes(b'X'+self.body[1:]);self.rejected('checksum changed')
    def test_changed_size(self):
        self.index['files']['fixture']['bytes']+=1;self.write_index();self.rejected('changed size')
    def test_changed_digest(self):
        self.index['files']['fixture']['sha256']='0'*64;self.write_index();self.rejected('checksum changed')
    def test_missing_body(self):
        (self.site/'fixture.asset').unlink();self.rejected('index does not match')
    def test_unindexed_body(self):
        (self.site/'unindexed.asset').write_bytes(b'Unindexed fixture');self.rejected('index does not match')
    def test_output_inside_source(self):
        self.output=self.site/'new';self.rejected('Use a new build directory')
    def test_fixture_over_budget(self):
        with patch.object(builder,'MAX_PUBLISHED_BYTES',1):self.rejected('conservative 970 MB budget')
    def test_optimized_guard(self):
        with patch.object(builder,'sys',types.SimpleNamespace(flags=types.SimpleNamespace(optimize=1))):self.rejected('nonoptimized')

if __name__=='__main__':unittest.main()
