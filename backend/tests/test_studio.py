import base64
from copy import deepcopy
from test_vertical_slice import clients,prepare,verify,invite,release
from app import local_ai
from app.studio import GeneratedQuestions,Insight

def test_import_preview_appends_and_settings_are_private(clients):
    w,b,x=clients;story,c,s=prepare(w,b);sid=story['id']
    payload={'filename':'draft.txt','data':base64.b64encode('Chapter One\nA first scene.\nChapter Two\nAnother scene.'.encode()).decode()}
    preview=w.post(f'/api/stories/{sid}/import-preview',json=payload)
    assert preview.status_code==200 and len(preview.json())==2
    assert len(w.get('/api/stories').json()[0]['chapters'])==1
    assert b.post(f'/api/stories/{sid}/import',json=payload).status_code==403
    assert w.post(f'/api/stories/{sid}/import',json=payload).json()['imported']==2
    chapters=w.get('/api/stories').json()[0]['chapters']
    assert chapters[0]['content']==c['content'] and chapters[2]['position']==3
    settings={'title':'Renamed','description':'A story','genre':'Fantasy','tags':['magic'],'word_goal':10000,'daily_goal':500,'status':'revision'}
    assert w.put(f'/api/stories/{sid}/settings',json=settings).status_code==200
    assert w.get(f'/api/stories/{sid}/settings').json()['tags']==['magic']
    assert b.get(f'/api/stories/{sid}/settings').status_code==403
    assert w.put(f'/api/stories/{sid}/settings',json={**settings,'cover':'javascript:alert(1)'}).status_code==422

def test_profile_opt_in_and_invitation(clients):
    w,b,x=clients;story,c,s=prepare(w,b)
    assert w.get('/api/beta-directory').json()==[]
    p={'bio':'I love mysteries','genres':['Mystery'],'specialties':['Pacing'],'availability':'available','listed':True}
    assert b.put('/api/beta-profile',json=p).status_code==200
    rows=w.get('/api/beta-directory?query=pacing').json();assert len(rows)==1 and 'email' not in rows[0]
    assert w.get('/api/beta-directory?query=romance').json()==[]
    assert w.post(f'/api/stories/{story["id"]}/invite-reader/{rows[0]["id"]}').status_code==200
    assert b.get('/api/inbox').json()[0]['status']=='pending'
    b.put('/api/beta-profile',json={**p,'listed':False})
    assert w.get('/api/beta-directory').json()==[]

def test_observations_reviews_targets_bookmarks_and_revocation(clients):
    w,b,x=clients;story,c,s=prepare(w,b)
    # Frozen intent targets are attached at analysis time.
    intent={**c['intent'],'targets':[{'metric':'trust','target':'Mara','expected':75}]}
    c=w.put('/api/chapters/'+c['id'],json={**{k:c[k] for k in ['title','content','revision']},'intent':intent}).json()
    s=w.post('/api/chapters/'+c['id']+'/analyze').json();s=verify(w,c,s)
    invitation=invite(w,b,story);rid=release(w,b,c,s)
    payload={'snapshot_id':s['id'],'kind':'trust','target':'Mara','value':60,'confidence':80,'explanation':'Her choices make sense.','evidence':c['content'][:20]}
    assert b.post('/api/read/'+rid+'/observations',json=payload).status_code==200
    assert b.post('/api/read/'+rid+'/observations',json={**payload,'evidence':'not a passage'}).status_code==422
    assert b.post('/api/read/'+rid+'/overall-feedback',json={'scope':'manuscript','text':'Strong opening.'}).status_code==200
    result=w.get('/api/stories/'+story['id']+'/insights').json()
    assert result['targets'][0]['actual']==60 and result['targets'][0]['gap']==-15
    assert len(result['reviews'])==1 and result['cohorts'][0]['readers']==1
    assert b.put('/api/read/'+rid+'/position',json={'snapshot_id':s['id'],'offset':30}).status_code==200
    assert b.get('/api/read/'+rid+'/position').json()['offset']==30
    bid=b.get('/api/auth/me').json()['id']
    assert w.post(f'/api/stories/{story["id"]}/helpfulness/{bid}',json={'rating':4}).status_code==200
    assert x.get('/api/read/'+rid+'/observations').status_code==401
    w.delete('/api/invitations/'+invitation)
    for suffix in ['observations','position','overall-feedback','story-state']:
        assert b.get('/api/read/'+rid+'/'+suffix).status_code==404

def test_checkpoint_blocks_text_graph_questions_and_direct_answers(clients):
    w,b,x=clients;story,c,s=prepare(w,b);end=50
    s['universe']['questions']=[{'text':'What do you expect next?','category':'prediction','evidence':c['content'][:20],'timing':'before_reveal','checkpoint':end},{'text':'What changed by the end?','category':'emotion','evidence':c['content'][-25:]}]
    s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    reading=b.get('/api/read/'+rid).json()
    assert reading['content']==c['content'][:end] and reading['checkpoint_pending']
    assert reading['universe']['entities']==[] and len(reading['questions'])==1
    assert b.get('/api/read/'+rid+'/story-state').status_code==409
    assert b.post('/api/read/'+rid+'/complete').status_code==409
    assert b.put('/api/read/'+rid+'/position',json={'snapshot_id':s['id'],'offset':end+1}).status_code==422
    assert b.post('/api/read/'+rid+'/follow-up').status_code==409
    from app.db import SessionLocal,Question
    from sqlalchemy import select
    with SessionLocal() as db:locked=db.scalar(select(Question).where(Question.release_id==rid,Question.category=='emotion')).id
    answer={'text':'I am curious','confidence':50,'emotion':'Curiosity','tension':50}
    assert b.post('/api/questions/'+locked+'/answer',json=answer).status_code==403
    assert b.post('/api/questions/'+reading['questions'][0]['id']+'/answer',json=answer).status_code==200
    reading=b.get('/api/read/'+rid).json()
    assert reading['content']==c['content'] and not reading['checkpoint_pending'] and reading['universe']['entities']==[]
    assert b.post('/api/questions/'+reading['questions'][0]['id']+'/answer',json=answer).status_code==409
    assert b.post('/api/read/'+rid+'/complete').status_code==200
    assert len(b.get('/api/read/'+rid).json()['universe']['entities'])>0

def test_merge_remaps_knowledge_and_preserves_frozen_review(clients):
    w,b,x=clients;story,c,s=prepare(w,b)
    duplicate=deepcopy(s['universe']['entities'][0]);original=duplicate['id'];duplicate['id']='duplicate';duplicate['name']='Alias'
    s['universe']['entities'].append(duplicate)
    assert w.put('/api/snapshots/'+s['id'],json=s['universe']).status_code==200
    merged=w.post('/api/snapshots/'+s['id']+'/merge',json={'keep_id':original,'remove_id':'duplicate'})
    assert merged.status_code==200
    assert all(e['id']!='duplicate' for e in merged.json()['universe']['entities'])
    frozen=verify(w,c,merged.json())
    assert w.post('/api/snapshots/'+frozen['id']+'/merge',json={'keep_id':original,'remove_id':'duplicate'}).status_code==409

def test_generated_questions_use_verified_safe_facts_and_create_new_review(clients,monkeypatch):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);seen={}
    def fake(schema,system,payload):
        seen.update(payload)
        return GeneratedQuestions(questions=[{'text':'How do you interpret this moment?','category':'reasoning','evidence':c['content'][:20]}])
    monkeypatch.setattr(local_ai,'enabled',lambda:True);monkeypatch.setattr(local_ai,'structured',fake)
    result=w.post('/api/snapshots/'+s['id']+'/questions')
    assert result.status_code==200 and result.json()['status']=='pending' and result.json()['id']!=s['id']
    assert 'intent' not in seen and all(e['reader_safe'] for e in seen['verified_facts']['entities'])

def test_story_state_never_returns_future_or_unreleased_chapters(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    future=w.post('/api/stories/'+story['id']+'/chapters',json={'title':'Future','content':'A future secret.'}).json()
    assert b.get('/api/read/'+rid+'/story-state').status_code==409
    assert b.post('/api/read/'+rid+'/complete').status_code==200
    assert len(b.get('/api/read/'+rid+'/story-state').json())==1
    assert future['title'] not in b.get('/api/read/'+rid+'/story-state').text
    assert w.get('/api/read/'+rid+'/story-state').status_code==404

def test_richer_state_is_cited_pending_and_private(clients,monkeypatch):
    from app.studio import StateSuggestions
    w,b,x=clients;story,c,s=prepare(w,b);entity=s['universe']['entities'][0]
    monkeypatch.setattr(local_ai,'enabled',lambda:True)
    monkeypatch.setattr(local_ai,'structured',lambda *args:StateSuggestions(suggestions=[{'entity_id':entity['id'],'field':'goals','text':'Find answers','source_id':1}]))
    result=w.post('/api/snapshots/'+s['id']+'/suggest-state')
    assert result.status_code==200
    e=result.json()['universe']['entities'][0]
    assert e['goals'][0]['evidence'] in c['content'] and not e['goals'][0]['reader_safe'] and e['status']=='pending'
    assert b.post('/api/snapshots/'+s['id']+'/suggest-state').status_code==403

def test_checkpoint_generation_never_sends_suffix_to_model(clients,monkeypatch):
    w,b,x=clients;story,c,s=prepare(w,b)
    s['universe']['entities'].append({'id':'reveal','kind':'reveal','name':'Ending','summary':'The ending','evidence':c['content'][-30:],'status':'pending','reader_safe':False,'confidence':0.5,'links':[],'knowledge':[]})
    s=verify(w,c,s);seen=[]
    def fake(schema,system,payload):
        seen.append(payload)
        return local_ai.CitedQuestions(questions=[{'text':'What do you think happens next?','category':'prediction','source_id':1}])
    monkeypatch.setattr(local_ai,'enabled',lambda:True);monkeypatch.setattr(local_ai,'structured',fake)
    result=w.post('/api/snapshots/'+s['id']+'/testing-moments')
    assert result.status_code==200,result.text
    assert all(c['content'][-30:] not in str(payload) for payload in seen)
    assert any(q['timing']=='before_reveal' for q in result.json()['universe']['questions'])

def test_reader_observations_join_dynamic_memory(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    payload={'snapshot_id':s['id'],'kind':'suspicion','target':'Theo','value':80,'confidence':70,'explanation':'His hesitation stands out.'}
    assert b.post('/api/read/'+rid+'/observations',json=payload).status_code==200
    memory=b.get('/api/read/'+rid+'/memory').json()
    assert memory[-1]['category']=='suspicion' and memory[-1]['answer']==payload['explanation']
    assert b.post('/api/read/'+rid+'/follow-up').status_code==200

def test_belief_truth_stays_writer_only():
    from app.analysis import reader_projection
    entity={'id':'a','status':'confirmed','reader_safe':True,'links':[],'knowledge':[{'text':'Someone is innocent','reader_safe':True,'truth':'false'}]}
    assert 'truth' not in reader_projection({'entities':[entity]},beta_graph=True)['entities'][0]['knowledge'][0]

def test_docx_import_reads_paragraph_text():
    import io,zipfile
    from app.studio import parse_manuscript
    from app.studio_schemas import ImportIn
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as archive:
        archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Chapter One</w:t></w:r></w:p><w:p><w:r><w:t>A scene.</w:t></w:r></w:p></w:body></w:document>')
    result=parse_manuscript(ImportIn(filename='book.docx',data=base64.b64encode(data.getvalue()).decode()))
    assert result==[{'title':'Chapter One','content':'A scene.'}]
