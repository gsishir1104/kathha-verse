from app.analysis import reader_projection

def test_beta_graph_shares_confirmed_entities_but_not_private_knowledge():
    private={'text':'private', 'reader_safe':False}
    public={'text':'chapter fact', 'reader_safe':True}
    entities=[{'id':'a','status':'confirmed','reader_safe':False,'links':['b','c'],'knowledge':[private,public]}, {'id':'b','status':'confirmed','reader_safe':True,'links':[],'knowledge':[]}, {'id':'c','status':'rejected','reader_safe':True,'links':[],'knowledge':[]}]
    graph=reader_projection({'entities':entities},beta_graph=True)['entities']
    assert [e['id'] for e in graph]==['a','b']
    assert graph[0]['links']==['b'] and graph[0]['knowledge']==[public]
    assert [e['id'] for e in reader_projection({'entities':entities})['entities']]==['b']
    assert entities[0]['reader_safe'] is False

def test_beta_graph_only_shares_facts_whose_entities_are_visible():
    entities=[{'id':'a','status':'confirmed','reader_safe':False,'links':['b'],'knowledge':[]}, {'id':'b','status':'confirmed','reader_safe':True,'links':[],'knowledge':[]}]
    facts=[
        {'category':'relationship','text':'A trusts B.','evidence':'A trusts B.','order':1,'entity_ids':['a','b']},
        {'category':'location','text':'B enters the house.','evidence':'B enters the house.','order':2,'entity_ids':['b']}]
    assert reader_projection({'entities':entities,'facts':facts})['facts']==[facts[1]]
    assert reader_projection({'entities':entities,'facts':facts},beta_graph=True)['facts']==facts
