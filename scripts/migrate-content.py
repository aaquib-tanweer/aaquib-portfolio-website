"""One-time, read-only import of existing local content into Jekyll source."""
import json, sqlite3
from pathlib import Path
root = Path(__file__).resolve().parents[1]
target = root / '_data/portfolio.json'
if target.exists():
    raise SystemExit('Jekyll content already exists; refusing to overwrite it.')
database = root / '.portfolio-data/portfolio.sqlite3'
if database.exists():
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        data = json.loads(connection.execute('SELECT value FROM settings WHERE key=?', ('content',)).fetchone()[0])
else:
    data = json.loads((root / 'content-seed.json').read_text())
if any(not post.get('published') for post in data.get('posts', [])):
    raise SystemExit('Private drafts exist. Keep them in the local database; import them through Owner Studio after migration. Nothing was overwritten.')
posts = data.pop('posts', [])
data.pop('version', None)
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
for post in posts:
    metadata = {key:post.get(key,'') for key in ['id','title','excerpt','date']}
    metadata.update({'layout':'post','render_with_liquid':False})
    header = '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key,value in metadata.items())
    (root / '_posts' / f'{post["date"][:10]}-{post["id"]}.md').write_text(f'---\n{header}\n---\n{post["body"]}\n')
print(f'Migrated {len(data["projects"])} projects and {len(posts)} published posts. Original database preserved.')
