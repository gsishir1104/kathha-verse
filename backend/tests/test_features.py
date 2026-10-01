from copy import deepcopy
from pathlib import Path
import sqlite3
from test_vertical_slice import clients,prepare,verify,invite,release
from app.db import engine
from app import backups,local_ai
from app.features import graph_delta


def test_history_restore_keeps_released_snapshot_and_rejects_stale_save(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    changed=w.put('/api/chapters/'+c['id'],json={'title':'Edited','content':'New manuscript','revision':c['revision'],'intent':c['intent']})
    assert changed.status_code==200
    rows=w.get('/api/chapters/'+c['id']+'/history').json();assert len(rows)==1 and rows[0]['content']==c['content']
    assert b.get('/api/chapters/'+c['id']+'/history').status_code==403
    url='/api/chapters/'+c['id']+'/restore/'+rows[0]['id']
    assert w.post(url,json={'revision':1}).status_code==409
    restored=w.post(url,json={'revision':2});assert restored.status_code==200
    assert restored.json()['content']==c['content'] and restored.json()['revision']==3
    assert b.get('/api/read/'+rid).json()['content']==c['content']
    assert len(w.get('/api/chapters/'+c['id']+'/history').json())==2


def test_graph_comments_and_writer_workflow_are_scoped_to_snapshot(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    entity=s['universe']['entities'][0]
    payload={'snapshot_id':s['id'],'entity_id':entity['id'],'target_id':'','category':'confusion','text':'The motivation is unclear.'}
    url='/api/read/'+rid+'/graph-comments'
    assert x.post(url,json=payload).status_code==401
    assert b.get(url).status_code==409
    assert b.post(url,json=payload).status_code==409
    assert b.post('/api/read/'+rid+'/complete').status_code==200
    assert b.post(url,json={**payload,'snapshot_id':'wrong'}).status_code==409
    assert b.post(url,json={**payload,'entity_id':'future-character'}).status_code==422
    assert b.post(url,json={**payload,'target_id':'unknown-edge'}).status_code==422
    assert b.post(url,json=payload).status_code==200
    assert len(b.get(url).json())==1
    board='/api/stories/'+story['id']+'/feedback-board'
    assert b.get(board).status_code==403
    item=w.get(board).json()[0];assert item['target']==entity['name']
    assert w.put(board+'/'+item['key'],json={'status':'addressed'}).status_code==200
    assert w.get(board).json()[0]['status']=='addressed'
    assert b.put(board+'/'+item['key'],json={'status':'reviewed'}).status_code==403
    assert b.get('/api/read/'+rid+'/graph-changes').json()['previous_chapter'] is None


def test_backups_are_consistent_independent_copies(clients):
    target=backups.backup_database(force=True)
    assert target and target.exists() and target != Path(engine.url.database)
    with sqlite3.connect(target) as db:
        assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
        assert db.execute('select count(*) from users').fetchone()[0]>=3
    assert backups.backup_database() is None


def test_detailed_analysis_covers_every_character_and_remaps_links(monkeypatch):
    pieces=[]
    def fake(content, section=False):
        pieces.append(content)
        return {'entities':[{'id':'a','name':'Nora','kind':'character','summary':'Finds a key','evidence':content[:10],'confidence':0.5,'reader_safe':False,'status':'pending','links':['b'],'knowledge':[]},{'id':'b','name':'Key','kind':'object','summary':'A key','evidence':content[:10],'confidence':0.5,'reader_safe':False,'status':'pending','links':[],'knowledge':[]}],'questions':[{'text':'What do you think?','category':'prediction','evidence':content[:10]}]},'local-ai'
    monkeypatch.setattr(local_ai,'extract_local',fake)
    content=('A chapter paragraph.\n'*300)
    result,mode=local_ai.extract_detailed(content)
    assert ''.join(pieces)==content and len(pieces)>1
    assert len(result['entities'])==2
    assert result['entities'][0]['links']==[result['entities'][1]['id']]
    assert mode=='local-ai'


def test_graph_delta_matches_names_not_generated_ids():
    old={'entities':[{'id':'a','name':'Nora','kind':'character','summary':'Arrives','links':[],'knowledge':[]}]}
    new=deepcopy(old);new['entities'][0]['id']='different-id'
    assert graph_delta(old,new)=={'added':[],'changed':[],'absent':[]}
    new['entities'][0]['summary']='Leaves'
    assert graph_delta(old,new)['changed']==['Nora']


def test_comparison_excludes_later_chapters_and_unreleased_drafts(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);first=release(w,b,c,s)
    c2=w.post('/api/stories/'+story['id']+'/chapters',json={'title':'Later','content':c['content']}).json()
    s2=w.post('/api/chapters/'+c2['id']+'/analyze').json()
    s2['universe']['entities'][0]['name']='LATER_CHAPTER_CANARY'
    s2=verify(w,c2,s2)
    release(w,b,c2,s2)
    shelf=b.get('/api/library').json();second=next(row['id'] for row in shelf if row['position']==2)
    assert b.post('/api/read/'+first+'/complete').status_code==200
    assert b.post('/api/read/'+second+'/complete').status_code==200
    early=b.get('/api/read/'+first+'/graph-changes')
    assert early.json()['previous_chapter'] is None and 'LATER_CHAPTER_CANARY' not in early.text
    later=b.get('/api/read/'+second+'/graph-changes')
    assert later.json()['previous_chapter']==1 and 'LATER_CHAPTER_CANARY' in later.text
    assert x.get('/api/read/'+second+'/graph-changes').status_code==401


def test_detailed_section_can_keep_entities_without_inventing_questions(monkeypatch):
    result=local_ai.CitedSection.model_validate({'entities':[{'name':'Nora','kind':'character','summary':'Finds a key.','source_id':1,'connections':[],'knowledge':[]}],'questions':[]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:result)
    universe,mode=local_ai.extract_local('Nora found a key.',section=True)
    assert len(universe['entities'])==1 and universe['questions']==[]


def test_larger_connection_sets_remain_bounded_and_only_link_extracted_entities(monkeypatch):
    entity={'name':'Nora','kind':'character','summary':'A friend','source_id':1,'connections':['A','B','C','D','E','F'],'knowledge':[]}
    result=local_ai.CitedSection.model_validate({'entities':[entity],'questions':[]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:result)
    universe,_=local_ai.extract_local('Nora meets friends.',section=True)
    assert universe['entities'][0]['links']==[]
