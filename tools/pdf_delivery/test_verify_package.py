from pathlib import Path
import hashlib,tempfile,unittest
from verify_package import verify,contained_file
class VerificationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  (self.root/'file.txt').write_bytes(b'abc')
  self.row={'file':'file.txt','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
 def tearDown(self):self.tmp.cleanup()
 def check(self,row):return verify(self.root,{'files':[row]})
 def test_valid(self):self.assertEqual(self.check(self.row),[])
 def test_changed_bytes(self):
  (self.root/'file.txt').write_bytes(b'abd');self.assertTrue(self.check(self.row))
 def test_wrong_length(self):self.assertTrue(self.check({**self.row,'bytes':4}))
 def test_absent(self):self.assertTrue(self.check({**self.row,'file':'missing.txt'}))
 def test_absolute(self):self.assertTrue(self.check({**self.row,'file':'/tmp/file.txt'}))
 def test_traversal(self):self.assertTrue(self.check({**self.row,'file':'../file.txt'}))
 def test_windows_path(self):self.assertTrue(self.check({**self.row,'file':'C:/file.txt'}))
 def test_backslash(self):self.assertTrue(self.check({**self.row,'file':'folder\\file.txt'}))
 def test_font(self):self.assertTrue(self.check({**self.row,'file':'font.OTF'}))
 def test_bad_hash(self):self.assertTrue(self.check({**self.row,'sha256':'abc'}))
 def test_bool_size(self):self.assertTrue(self.check({**self.row,'bytes':True}))
 def test_nonstring_name(self):self.assertTrue(self.check({**self.row,'file':None}))
 def test_duplicate(self):self.assertTrue(verify(self.root,{'files':[self.row,self.row]}))
 def test_empty(self):self.assertTrue(verify(self.root,{'files':[]}))
 def test_bad_entry(self):self.assertTrue(verify(self.root,{'files':[None]}))
 def test_symlink_escape(self):
  with tempfile.TemporaryDirectory() as other:
   dest=Path(other)/'target';dest.write_bytes(b'abc');(self.root/'link.txt').symlink_to(dest)
   self.assertTrue(self.check({**self.row,'file':'link.txt'}))
if __name__=='__main__':unittest.main(verbosity=2)
