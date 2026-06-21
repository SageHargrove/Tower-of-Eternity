import sys, traceback
sys.path.append('c:/infinite gacha/tower-gacha/backend')
from routers.tower import enter_floor, EnterFloorReq
try:
    req = EnterFloorReq(floor_number=1, team_id=1)
    res = enter_floor(req)
    print('OK')
except Exception as e:
    traceback.print_exc()
