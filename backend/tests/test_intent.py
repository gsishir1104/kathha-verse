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
    saved=w.put(f'/api/chapters/{cid}',json={'title':chapter['title'],'content':chapter['content'],'revision':chapter['revision'],'intent':cleared})
    assert saved.status_code==200 and saved.json()['intent']=={**cleared,'targets':[],'scenes':[]}
