SAMPLE_TITLE = 'The Last Light'
SAMPLE_CONTENT = '''The lighthouse had been dark for eleven years. Tonight, someone had lit it.

Mara stopped at the edge of the harbor, rain slipping beneath her collar. Across the water, the beam swept over the abandoned station with the slow assurance of a heartbeat.

Her brother Elias had kept the light before he vanished. The official report said a storm had taken him. Mara had signed it because there was nothing else to sign.

"You shouldn't be here," Theo said behind her. He wore the same blue coat he had worn at the inquest, its brass buttons polished bright.

"Someone is in the tower."

"The mechanism could have started on its own."

Mara looked at him. Eleven years of salt and silence, and now a mechanism had simply decided to wake up. Theo would not meet her eyes.

He held out an envelope. Her name was written across it in Elias's narrow handwriting. The paper was dry, though Theo's hands were wet.

"It was left at the station this morning," he said.

Inside was a small brass key and a single line: When the light returns, don't trust the tide.

Mara closed her fingers around the key. For the first time in eleven years, she let herself imagine that her brother might still be alive.

Across the harbor, the light went out.'''

def sample_universe():
    def node(id, kind, name, summary, evidence, links=(), safe=True, confidence=.92, knowledge=()):
        return dict(id=id,kind=kind,name=name,summary=summary,evidence=evidence,links=list(links),reader_safe=safe,confidence=confidence,status='pending',knowledge=list(knowledge))
    def know(text,state,evidence,safe=True): return dict(text=text,state=state,evidence=evidence,reader_safe=safe)
    return {'entities':[
        node('mara','character','Mara','Elias’s sister. The returning light challenges the story she accepted about his disappearance.','Her brother Elias had kept the light before he vanished.', ['elias','theo','key'], knowledge=[know('The lighthouse is operating again.','knows','Tonight, someone had lit it.'),know('Elias may still be alive.','believes','she let herself imagine that her brother might still be alive.'),know('Who lit the lighthouse.','does_not_know','"Someone is in the tower."'),know('Hope mixed with suspicion — an interpretation.','feels','Theo would not meet her eyes.')]),
        node('theo','character','Theo','Delivers an envelope from Elias and offers a doubtful explanation for the light.','"The mechanism could have started on its own."',['mara','letter'], confidence=.83, knowledge=[know('An envelope was left at the station.','knows','"It was left at the station this morning," he said.'),know('He may feel uncomfortable — an interpretation.','feels','Theo would not meet her eyes.')]),
        node('elias','character','Elias','The former lighthouse keeper, missing for eleven years. His fate is unresolved.','Her brother Elias had kept the light before he vanished.', ['mara','lighthouse']),
        node('lighthouse','location','The lighthouse','An abandoned station across the harbor.','The lighthouse had been dark for eleven years.', ['light']),
        node('key','object','Brass key','Arrives inside an envelope; its purpose is unknown.','Inside was a small brass key', ['letter']),
        node('letter','clue','The dry envelope','Dry paper in wet hands raises questions about Theo’s account.','The paper was dry, though Theo\'s hands were wet.', ['theo','elias'], confidence=.78),
        node('light','event','The light returns','The lighthouse operates after eleven years of darkness.','Tonight, someone had lit it.', ['mara','lighthouse']),
        node('siblings','relationship','Mara ↔ Elias','Siblings separated by an unresolved disappearance.','Her brother Elias had kept the light before he vanished.', ['mara','elias']),
        node('warning','secret','An unexplained warning','The meaning of the warning remains unresolved; keep this interpretation author-only until reviewed.','When the light returns, don\'t trust the tide.', ['letter'],safe=False,confidence=.61),
        node('missing','plot_thread','What happened to Elias?','Open: the new letter destabilizes the official report.','The official report said a storm had taken him.', ['elias','letter'])
    ], 'questions':[
        {'text':'What do you currently suspect happened to Elias?','category':'prediction','evidence':'The official report said a storm had taken him.','options':['The storm caused his disappearance','Someone concealed what happened','Elias left deliberately','I have another theory']},
        {'text':'How much do you trust Theo’s explanation for the light?','category':'trust','evidence':'"The mechanism could have started on its own."','options':['I trust him','I mostly trust him','I am unsure','I do not trust him']},
        {'text':'What was your strongest reaction when Mara opened the envelope?','category':'emotion','evidence':'Inside was a small brass key','options':['Curiosity','Unease','Surprise','Excitement','Something else']},
    ]}
