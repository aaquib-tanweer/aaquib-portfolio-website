import hashlib
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
import server

class PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.previous_data = server.DATA
        cls.previous_origin = server.ORIGIN
        server.DATA = Path(cls.temp.name)
        salt = 'a1' * 16
        with server.db() as c:
            c.execute('INSERT INTO settings VALUES (?,?)', ('password', json.dumps({'salt':salt,'hash':server.password_hash('test-only-password',salt)})))
        cls.http = server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.port = cls.http.server_port
        server.ORIGIN = f'http://127.0.0.1:{cls.port}'
        cls.thread = threading.Thread(target=cls.http.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.thread.join()
        server.DATA = cls.previous_data; server.ORIGIN = cls.previous_origin; cls.temp.cleanup()
    def request(self,method,path,body=None,headers=None):
        connection = http.client.HTTPConnection('127.0.0.1',self.port)
        h = {'Origin':server.ORIGIN,'Content-Type':'application/json'}
        if headers: h.update(headers)
        connection.request(method,path,json.dumps(body) if body is not None else None,h)
        response = connection.getresponse(); raw=response.read()
        result=(response.status, dict(response.getheaders()),json.loads(raw) if response.getheader('Content-Type','').startswith('application/json') else raw)
        connection.close(); return result
    def login(self):
        status,headers,result=self.request('POST','/api/login',{'password':'test-only-password'})
        self.assertEqual(status,200)
        self.assertIn('HttpOnly',headers['Set-Cookie']); self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        return {'Cookie':headers['Set-Cookie'].split(';')[0],'X-CSRF-Token':result['csrf']}
    def test_access_and_private_files(self):
        self.assertEqual(self.request('GET','/api/admin/content')[0],401)
        self.assertEqual(self.request('POST','/api/admin/content',{})[0],401)
        for path in ['/server.py','/.portfolio-data/portfolio.sqlite3','/content-seed.json','/../server.py']:
            self.assertEqual(self.request('GET',path)[0],404)
    def test_origin_csrf_and_logout(self):
        auth=self.login()
        self.assertEqual(self.request('POST','/api/admin/content',{}, {**auth,'Origin':'https://attacker.example'})[0],403)
        self.assertEqual(self.request('POST','/api/admin/content',{}, {**auth,'X-CSRF-Token':'wrong'})[0],403)
        self.assertEqual(self.request('POST','/api/logout',{},auth)[0],200)
        self.assertEqual(self.request('GET','/api/admin/content',headers=auth)[0],401)
    def test_drafts_publish_persistence_and_conflict(self):
        auth=self.login(); content=self.request('GET','/api/admin/content',headers=auth)[2]
        content['posts']=[{'id':'test-post','title':'A test post','excerpt':'Preview','body':'First paragraph.\n\nSecond paragraph.','published':False,'date':'2026-10-11T00:00:00Z'}]
        status,_,saved=self.request('POST','/api/admin/content',content,auth); self.assertEqual(status,200)
        self.assertEqual(self.request('GET','/api/content')[2]['posts'],[])
        self.assertEqual(self.request('POST','/api/admin/content',content,auth)[0],409)
        saved['posts'][0]['published']=True
        status,_,saved=self.request('POST','/api/admin/content',saved,auth); self.assertEqual(status,200)
        self.assertEqual(len(self.request('GET','/api/content')[2]['posts']),1)
        with server.db() as c: persisted=json.loads(c.execute('SELECT value FROM settings WHERE key="content"').fetchone()[0])
        self.assertTrue(persisted['posts'][0]['published'])
        saved['posts']=[]
        self.assertEqual(self.request('POST','/api/admin/content',saved,auth)[0],200)
    def test_project_url_validation_and_updates(self):
        auth=self.login(); content=self.request('GET','/api/admin/content',headers=auth)[2]
        content['projects']=[{'id':'test-project','title':'Backend','preview':'A project overview','tags':'Python','url':'javascript:alert(1)'}]
        self.assertEqual(self.request('POST','/api/admin/content',content,auth)[0],400)
        content['projects'][0]['url']='https://github.com/example/project'
        status,_,saved=self.request('POST','/api/admin/content',content,auth); self.assertEqual(status,200)
        self.assertEqual(self.request('GET','/api/content')[2]['projects'][0]['preview'],'A project overview')
        saved['bio']='Updated owner bio'
        self.assertEqual(self.request('POST','/api/admin/content',saved,auth)[0],200)
        self.assertEqual(self.request('GET','/api/content')[2]['bio'],'Updated owner bio')
    def test_failed_login_limit(self):
        server.ATTEMPTS.clear()
        for _ in range(8): self.assertEqual(self.request('POST','/api/login',{'password':'wrong'})[0],401)
        self.assertEqual(self.request('POST','/api/login',{'password':'wrong'})[0],429)
        server.ATTEMPTS.clear()

if __name__=='__main__': unittest.main()
