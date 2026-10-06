from app.graph_connections import GraphProposals, ConnectionProposal, EventPosition, apply_proposals
from app.analysis import reader_projection


def entity(id, kind='character', status='pending'):
    return dict(id=id,kind=kind,name=id,summary=id,evidence='A visits B.',confidence=.5,
                reader_safe=True,status=status,links=[],knowledge=[])


def test_connections_require_existing_visible_ids_and_valid_citation():
    original={'entities':[entity('a'),entity('b','location'),entity('hidden',status='rejected')],'questions':[]}
    proposals=GraphProposals(connections=[
        ConnectionProposal(source_id='a',target_id='b',label='visited',passage_id=1),
        ConnectionProposal(source_id='a',target_id='hidden',label='knows',passage_id=1),
        ConnectionProposal(source_id='a',target_id='missing',label='knows',passage_id=1),
        ConnectionProposal(source_id='a',target_id='b',label='owns',passage_id=999)])
    result=apply_proposals(original,proposals,{1:'A visits B.'})
    assert len(result['entities'][0]['relations'])==1
    assert result['entities'][0]['relations'][0]['evidence']=='A visits B.'
    assert 'relations' not in original['entities'][0]
    assert not reader_projection(result,beta_graph=True)['entities']


def test_chronology_allows_flashback_order_and_unknown_time():
    original={'entities':[entity('later','event'),entity('earlier','event'),entity('unknown','event'),entity('person')],'questions':[]}
    proposals=GraphProposals(events=[
        EventPosition(entity_id='later',position=2,time_label='Next day',passage_id=1),
        EventPosition(entity_id='earlier',position=1,time_label='Before the meeting',passage_id=1),
        EventPosition(entity_id='unknown',position=None,passage_id=1),
        EventPosition(entity_id='person',position=3,passage_id=1)])
    result=apply_proposals(original,proposals,{1:'A visits B.'})
    assert [e['timeline_order'] for e in result['entities']]==[2,1,None,None]
