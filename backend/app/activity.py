"""Record successful authenticated actions, never request bodies or query strings."""
import time
from .db import SessionLocal, UserPresence, UserActivity

def record(user_id,method,route,params):
    now=time.time()
    with SessionLocal() as db:
        presence=db.get(UserPresence,user_id)
        if not presence: presence=UserPresence(user_id=user_id);db.add(presence)
        presence.last_active=now
        if method in {'POST','PUT','DELETE','PATCH'} and not route.startswith(('/api/admin/','/api/chat')):
            labels={'/api/preferences':'Updated reading preferences','/api/beta-profile':'Updated beta reader profile','/api/stories':'Created story','/api/auth/logout':'Signed out'}
            action=labels.get(route)
            if not action:
                parts=[p.replace('-',' ') for p in route.split('/') if p and p!='api' and not p.startswith('{')]
                action=({'POST':'Submitted','PUT':'Updated','DELETE':'Removed','PATCH':'Updated'}[method]+' '+ ' / '.join(parts))[:100]
            resource=next((str(v) for k,v in params.items() if k.endswith('_id')),'')[:100]
            db.add(UserActivity(user_id=user_id,action=action,resource=resource))
        db.commit()
