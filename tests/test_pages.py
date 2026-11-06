import importlib.util,json,tempfile,unittest
from pathlib import Path

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
checker=module('checker','scripts/check-site.py')

class PagesPaths(unittest.TestCase):
    def fixture(self,site,base):
        (site/'assets').mkdir()
        (site/'content.json').write_text(json.dumps({'projects':[],'posts':[]}))
        for name in ['app.js','content.js','styles.css','assets/picture.jpeg']:(site/name).write_text('test')
        (site/'index.html').write_text(f'<body data-content-url="{base}/content.json"><link href="{base}/styles.css"><script src="{base}/app.js"></script><img src="{base}/assets/picture.jpeg"></body>')
    def test_user_site_root(self):
        with tempfile.TemporaryDirectory() as folder:
            site=Path(folder);self.fixture(site,'');checker.check(site,'')
    def test_project_site_subpath(self):
        with tempfile.TemporaryDirectory() as folder:
            site=Path(folder);self.fixture(site,'/Portfolio');checker.check(site,'/Portfolio')
    def test_old_repository_path_rejected_after_rename(self):
        with tempfile.TemporaryDirectory() as folder:
            site=Path(folder);self.fixture(site,'/Portfolio')
            with self.assertRaisesRegex(AssertionError,'Wrong content URL'):checker.check(site,'')
    def test_old_stylesheet_path_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            site=Path(folder);self.fixture(site,'');page=site/'index.html';page.write_text(page.read_text().replace('/styles.css','/Portfolio/styles.css'))
            with self.assertRaisesRegex(AssertionError,'Broken asset'):checker.check(site,'')
if __name__=='__main__':unittest.main()
