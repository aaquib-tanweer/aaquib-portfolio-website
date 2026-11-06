"""Check the exact deployment base path, assets, and private-file exclusions."""
import argparse,json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.paths=[];self.body={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='body':self.body=a
        if tag in ['script','img','link']:
            url=a.get('src') or a.get('href','')
            if url and not urlsplit(url).scheme and not url.startswith('//'):self.paths.append(urlsplit(url).path)

def check(site, baseurl=None):
    content=json.loads((site/'content.json').read_text())
    assert isinstance(content['projects'],list)
    for name in ['.portfolio-data','_private','_legacy','server.py','tests','node_modules','vendor','Gemfile','content-seed.json']:
        assert not (site/name).exists(),f'Private or source path leaked: {name}'
    index=Links();index.feed((site/'index.html').read_text())
    feed=index.body.get('data-content-url','')
    inferred=feed.removesuffix('/content.json')
    if baseurl is None:baseurl=inferred
    assert baseurl=='' or (baseurl.startswith('/') and not baseurl.endswith('/')), 'Invalid base URL.'
    assert feed==baseurl+'/content.json',f'Wrong content URL: {feed}; expected {baseurl}/content.json'
    assert 'data-admin-url' not in index.body, 'Owner login remains.'
    for removed in ['admin', 'admin.js', 'editor-config.json', 'github-store.mjs', 'blog', 'favicon.ico', 'favicon.png']:
        assert not (site/removed).exists(), f'Removed feature published: {removed}'
    for page in [site/'index.html']:
        parser=Links();parser.feed(page.read_text())
        for link in parser.paths:
            assert '{{' not in link and '{%' not in link,f'Unrendered asset URL: {link}'
            if link.startswith('/'):
                assert link.startswith(baseurl+'/'),f'Asset uses wrong base URL: {link}'
                target=site/unquote(link[len(baseurl)+1:])
            else:target=page.parent/unquote(link)
            assert target.is_file(),f'Broken asset {link} in {page}'
    for source in [site/'app.js',site/'content.js']:
        assert '/api/' not in source.read_text(),f'Backend route left in {source}'
    print(f'Static artifact verified at {baseurl or "/"}: {len(content["projects"])} projects; assets and private-file exclusions passed.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('site',type=Path,nargs='?',default=Path('_site'));parser.add_argument('--baseurl');args=parser.parse_args()
    check(args.site,args.baseurl)
