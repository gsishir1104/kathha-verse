from contextlib import nullcontext
import pytest
from fastapi import HTTPException
from app import analysis, local_ai
from test_vertical_slice import clients
from app.db import SessionLocal, User
from sqlalchemy import select

def test_hosted_provider_uses_server_side_structured_responses(monkeypatch):
    captured={}
    parsed=local_ai.CitedQuestions.model_validate({'questions':[{
        'text':'Who do you currently suspect?', 'category':'prediction',
        'source_id':1, 'options':['Nora','The caretaker','Someone else']
    }]})
    class Usage:
        input_tokens=120
        output_tokens=35
    class Response:
        output_parsed=parsed
        usage=Usage()
    class Responses:
        def parse(self,**kwargs):
            captured.update(kwargs)
            return Response()
    class Client:
        responses=Responses()
    monkeypatch.setenv('AI_PROVIDER','openai')
    monkeypatch.setenv('OPENAI_API_KEY','server-secret')
    monkeypatch.setenv('OPENAI_MODEL','gpt-test')
    monkeypatch.setattr('openai.OpenAI',lambda **kwargs:Client())
    result,input_tokens,output_tokens=local_ai._openai_structured_request(
        local_ai.CitedQuestions,'Return a reader question.',{'passages':[{'source_id':1,'text':'Nora found a key.'}]})
    assert result==parsed and (input_tokens,output_tokens)==(120,35)
    assert captured['model']=='gpt-test' and captured['store'] is False
    assert captured['text_format'] is local_ai.CitedQuestions
    assert 'server-secret' not in str(captured)

def test_local_extraction_requires_real_evidence_and_defaults_private(monkeypatch):
    payload=local_ai.CitedUniverse.model_validate({'entities':[
        {'name':'Nora','kind':'character','summary':'Finds a key.','source_id':1,'connections':['Invented'],'knowledge':[]},
        {'name':'Invented','kind':'secret','summary':'Unsupported.','source_id':999,'connections':[],'knowledge':[]}],
        'questions':[{'text':'What do you think the key opens?','category':'prediction','source_id':1}]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:payload)
    universe,mode=local_ai.extract_local('Nora found a key.')
    assert mode=='local-ai' and len(universe['entities'])==1
    assert universe['entities'][0]['reader_safe'] is False
    assert universe['entities'][0]['status']=='pending'
    assert universe['entities'][0]['links']==[]
    with pytest.raises(HTTPException) as error:local_ai.extract_local('x'*(local_ai.MAX_CHARS+1))
    assert error.value.status_code==422

def test_schema_compatibility_preserves_required_types():
    schema=local_ai.model_schema(local_ai.CitedUniverse)
    assert schema['type']=='object'
    assert 'entities' in schema['required']
    entity=schema['properties']['entities']['items']
    assert 'character' in entity['properties']['kind']['enum']
    assert '$ref' not in str(schema) and 'maxLength' not in str(schema)

def test_quota_persists_and_failed_requests_refund(clients):
    w,b,x=clients
    user_id=w.get('/api/auth/me').json()['id']
    with pytest.raises(ValueError):
        with local_ai.allowance(user_id,'analysis'):raise ValueError('model unavailable')
    for _ in range(local_ai.DAILY_LIMIT):
        with local_ai.allowance(user_id,'analysis'):pass
    with pytest.raises(HTTPException) as error:
        with local_ai.allowance(user_id,'analysis'):pass
    assert error.value.status_code==429

def test_local_model_runs_one_request_at_a_time(clients):
    w,b,x=clients
    uid=w.get('/api/auth/me').json()['id']
    with local_ai.allowance(uid,'analysis'):
        with pytest.raises(HTTPException) as error:
            with local_ai.allowance(uid,'analysis'):pass
        assert error.value.status_code==429


def test_passages_preserve_exact_unicode_source():
    original = "Nora\u2019s key\u2014\u2018silver\u2019."
    content = original + "\r\n\r\n" + "\u00e9" * 4100
    sources = local_ai.passages(content)
    assert len(sources) == 4
    assert all(text in content and len(text) <= 2000 for text in sources.values())
    assert sources[1] == original


def test_hosted_analysis_resolves_unicode_evidence_from_source_id(monkeypatch):
    content = "The ’King Pritvi' was ruling the village."
    payload = local_ai.CitedUniverse.model_validate({'entities':[
        {'name':'King Pritvi','kind':'character','summary':'Rules the village.',
         'source_id':1,'connections':[],'knowledge':[]}],
        'questions':[{'text':'How do you feel about King Pritvi?',
                      'category':'emotion','source_id':1,
                      'options':['Curious','Uneasy','Sympathetic']} ]})
    monkeypatch.setattr(analysis,'DEMO_MODE',False)
    monkeypatch.setattr(local_ai,'structured',lambda *args:payload)
    universe,_=analysis.extract(content)
    assert universe['entities'][0]['evidence']==content
    assert universe['questions'][0]['evidence']==content
    analysis.validate_universe(local_ai.Universe.model_validate(universe),content)


def test_questions_reject_unknown_citations():
    question = local_ai.CitedQuestion(text='What surprised you?', category='emotion', source_id=999)
    assert local_ai.resolve_questions([question], {1: 'Nora found a key.'}) == []


def test_invalid_optional_question_does_not_discard_valid_universe(monkeypatch):
    payload=local_ai.CitedUniverse.model_validate({'entities':[
        {'name':'Nora','kind':'character','summary':'Finds a key.','source_id':1,'connections':[],'knowledge':[]}],
        'questions':[{'text':'What does the key open?','category':'prediction','source_id':999}]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:payload)
    universe,mode=local_ai.extract_local('Nora found a key.')
    assert mode=='local-ai'
    assert [e['name'] for e in universe['entities']]==['Nora']
    assert universe['questions']==[]


def test_extra_knowledge_is_bounded_without_losing_citation_validation():
    entry = {'text': 'Found a key.', 'state': 'knows', 'source_id': 1}
    entity = local_ai.CitedEntity(name='Nora', kind='character', summary='Finds a key.', source_id=1, connections=[], knowledge=[entry] * 3)
    assert len(entity.knowledge) == 2
    assert all(k.source_id == 1 for k in entity.knowledge)

def test_labeled_relationships_are_kept_with_exact_evidence(monkeypatch):
    payload=local_ai.CitedUniverse.model_validate({'entities':[
        {'name':'Nora','kind':'character','summary':'Enters the house.','source_id':1,'connections':['House'],
         'relationships':[{'target':'House','label':'enters','source_id':1}],'knowledge':[]},
        {'name':'House','kind':'location','summary':'A locked house.','source_id':1,'connections':[],
         'relationships':[],'knowledge':[]}],
        'questions':[{'text':'Why does Nora enter?','category':'prediction','source_id':1}]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:payload)
    universe,_=local_ai.extract_local('Nora enters the locked house.')
    nora=universe['entities'][0]
    assert nora['relations']==[{'target_id':'local-2','label':'enters','strength':50,'evidence':'Nora enters the locked house.'}]

def test_chapter_facts_keep_order_category_entities_and_exact_evidence(monkeypatch):
    content='Nora finds the key and enters the locked house.'
    payload=local_ai.CitedUniverse.model_validate({'entities':[
        {'name':'Nora','kind':'character','summary':'Finds a key.','source_id':1,'connections':['Key','House'],'knowledge':[]},
        {'name':'Key','kind':'object','summary':'A discovered key.','source_id':1,'connections':[],'knowledge':[]},
        {'name':'House','kind':'location','summary':'A locked house.','source_id':1,'connections':[],'knowledge':[]}],
        'facts':[
            {'category':'object','text':'Nora finds the key.','source_id':1,'order':1,'related_entities':['Nora','Key']},
            {'category':'location','text':'Nora enters the locked house.','source_id':1,'order':2,'related_entities':['Nora','House']}],
        'questions':[{'text':'What do you think Nora will find inside?','category':'prediction','source_id':1}]})
    monkeypatch.setattr(local_ai,'structured',lambda *args:payload)
    universe,_=local_ai.extract_local(content)
    assert [fact['category'] for fact in universe['facts']]==['object','location']
    assert universe['facts'][0]['entity_ids']==['local-1','local-2']
    assert all(fact['evidence']==content for fact in universe['facts'])
    analysis.validate_universe(local_ai.Universe.model_validate(universe),content)

def test_explicit_name_reveal_merges_alias_and_remaps_every_reference():
    content='Samyukta followed the Strange Man. “What should I call you?” Samyukta asked. “Abhi,” he replied simply.'
    universe={'entities':[
        {'id':'stranger','name':'Strange Man','kind':'character','summary':'A mysterious visitor.','evidence':'Samyukta followed the Strange Man.','confidence':0.5,'reader_safe':False,'status':'pending','links':['samyukta'],'knowledge':[],'relations':[{'target_id':'samyukta','label':'followed by','evidence':'Samyukta followed the Strange Man.'}]},
        {'id':'abhi','name':'Abhi','kind':'character','summary':'He reveals his name.','evidence':'“Abhi,” he replied simply.','confidence':0.5,'reader_safe':False,'status':'pending','links':['stranger'],'knowledge':[],'relations':[{'target_id':'stranger','label':'same person','evidence':'“Abhi,” he replied simply.'}]},
        {'id':'samyukta','name':'Samyukta','kind':'character','summary':'She follows him.','evidence':'Samyukta followed the Strange Man.','confidence':0.5,'reader_safe':False,'status':'pending','links':['stranger'],'knowledge':[],'relations':[{'target_id':'stranger','label':'follows','evidence':'Samyukta followed the Strange Man.'}]}
    ],'questions':[]}
    repaired=local_ai.consolidate_explicit_identity_reveals(universe,content)
    assert [e['name'] for e in repaired['entities']].count('Abhi')==1
    assert all(e['name']!='Strange Man' for e in repaired['entities'])
    assert all('stranger' not in e['links'] for e in repaired['entities'])
    assert all(r['target_id']!='stranger' for e in repaired['entities'] for r in e['relations'])
    abhi=next(e for e in repaired['entities'] if e['name']=='Abhi')
    assert 'abhi' not in abhi['links'] and all(r['target_id']!='abhi' for r in abhi['relations'])

def test_long_chapter_analysis_covers_all_4000_words(monkeypatch):
    content=' '.join('word'+str(i) for i in range(4000))
    seen=[]
    def fake(schema,system,payload):
        sources=payload['passages'];seen.extend(p['text'] for p in sources)
        return local_ai.CitedUniverse.model_validate({'entities':[{'name':'Nora','kind':'character','summary':'Present in the chapter.','source_id':1,'connections':[],'knowledge':[]}],'questions':[{'text':'What surprised you here?','category':'emotion','source_id':1}]})
    monkeypatch.setattr(local_ai,'structured',fake)
    universe,mode=local_ai.extract_local(content)
    assert ''.join(seen)==content
    assert len(seen)>1 and universe['entities'][0]['status']=='pending'
    assert mode=='local-ai'


def test_section_boundaries_preserve_end_of_chapter():
    content=('A paragraph with words.\n'*900)+'FINAL CHAPTER CLUE'
    for size in (2200,local_ai.ANALYSIS_PASS_CHARS):
        chunks=local_ai.chapter_sections(content,size)
        assert ''.join(chunks)==content
        assert all(len(c)<=size for c in chunks)
        assert chunks[-1].endswith('FINAL CHAPTER CLUE')


def test_explicit_word_limit():
    local_ai.validate_chapter_length('word ' * 4000)
    with pytest.raises(HTTPException) as error:
        local_ai.validate_chapter_length('word ' * 4001)
    assert '4,000 words' in error.value.detail
