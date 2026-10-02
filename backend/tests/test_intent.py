from test_vertical_slice import clients
from app import local_ai


def test_intent_suggestions_are_private_unsaved_and_editable(clients, monkeypatch):
    w,b,x=clients
    chapter=w.get('/api/stories').json()[0]['chapters'][0]
    cid=chapter['id']
    proposed={'emotion':'Hope','tension':40,'prediction_target':'lighthouse','desired_predictability':30,'notes':'Consider leaving the light unexplained.'}
    monkeypatch.setattr(local_ai,'enabled',lambda: True)
    monkeypatch.setattr(local_ai,'suggest_intent',lambda content: proposed)
    response=w.post(f'/api/chapters/{cid}/suggest-intent')
    assert response.status_code==200
    assert response.json()['intent']==proposed
    unchanged=w.get(f'/api/chapters/{cid}').json()
    assert unchanged['intent']==chapter['intent'] and unchanged['revision']==chapter['revision']
    assert b.post(f'/api/chapters/{cid}/suggest-intent').status_code==403
    x.post('/api/auth/register',json={'name':'Other writer','email':'other@example.com','password':'long-password-123','role':'writer'})
    assert x.post(f'/api/chapters/{cid}/suggest-intent').status_code==404
    cleared={'emotion':'','tension':None,'prediction_target':'','desired_predictability':None,'notes':''}
    saved=w.put(f'/api/chapters/{cid}/intent',json={'revision':chapter['revision'],'intent':cleared})
    assert saved.status_code==200 and saved.json()['intent']=={**cleared,'targets':[],'scenes':[]}

def test_saving_intent_keeps_current_story_universe(clients):
    w,b,x=clients
    chapter=w.get('/api/stories').json()[0]['chapters'][0]
    snapshot=w.post(f'/api/chapters/{chapter["id"]}/manual').json()
    intent={**chapter['intent'],'emotion':'Wonder','tension':72}

    saved=w.put(f'/api/chapters/{chapter["id"]}/intent',json={'revision':chapter['revision'],'intent':intent})

    assert saved.status_code==200,saved.text
    result=saved.json()
    assert result['revision']==chapter['revision']
    assert result['state']=='review'
    assert result['snapshot']['id']==snapshot['id']
    assert result['snapshot']['universe']==snapshot['universe']
    assert result['intent']['emotion']=='Wonder'

    stale=w.put(f'/api/chapters/{chapter["id"]}/intent',json={'revision':chapter['revision']+1,'intent':intent})
    assert stale.status_code==409
    assert b.put(f'/api/chapters/{chapter["id"]}/intent',json={'revision':chapter['revision'],'intent':intent}).status_code==403
    assert x.put(f'/api/chapters/{chapter["id"]}/intent',json={'revision':chapter['revision'],'intent':intent}).status_code==401
