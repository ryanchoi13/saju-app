"""Versioned daily sets; old ranked menu records are left intact.

One current set per mode. Refresh is compare-and-swap under an account/day lock.
Only current sets on previous dates become meal history; refreshing is not eating.
"""
import json
import secrets
from datetime import timedelta
from menu_store import today, _key
from wardrobe_store import _connection, _execute, StorageUnavailable


def initialize():
    with _connection() as (conn, pg):
        if pg:
            _execute(conn, pg, 'SELECT pg_advisory_xact_lock(74201932)')
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS meal_set_days_v2 (
            owner_key VARCHAR(64) NOT NULL, day VARCHAR(10) NOT NULL,
            token VARCHAR(64) NOT NULL UNIQUE, payload TEXT NOT NULL,
            PRIMARY KEY(owner_key,day))''')


def _locked(conn, pg, owner, day):
    if pg:
        # Covers the first insertion as well as refreshes on existing rows.
        _execute(conn, pg, 'SELECT pg_advisory_xact_lock(hashtext(%s))', (owner+str(day),))
    else:
        conn.execute('BEGIN IMMEDIATE')


def _get(conn, pg, owner, day):
    row = _execute(conn, pg, 'SELECT token,payload FROM meal_set_days_v2 WHERE owner_key=%s AND day=%s',
                   (owner,str(day))).fetchone()
    return (row[0],json.loads(row[1])) if row else (secrets.token_hex(32), {'mode':'general','sets':{},'counts':{'general':0,'diet':0}})


def _history(conn, pg, owner, day, mode):
    rows = _execute(conn, pg, '''SELECT day,payload FROM meal_set_days_v2
        WHERE owner_key=%s AND day<%s ORDER BY day''', (owner,str(day))).fetchall()
    # Preserve accumulated exposure while padding skipped days so a menu viewed
    # months ago is not treated as yesterday by the selector's rolling windows.
    records=[];previous=None
    for raw_day, raw in rows:
        from datetime import date
        on=date.fromisoformat(raw_day)
        if previous is not None:
            for _ in range(min(7,max(0,(on-previous).days-1))):
                records.extend(_empty_day())
        plan=json.loads(raw)['sets'].get(mode)
        records.extend(plan['meals'] if plan else _empty_day())
        previous=on
    if previous is not None:
        for _ in range(min(7,max(0,(day-previous).days-1))):
            records.extend(_empty_day())
    return records


def _empty_day():
    return [dict(id='__gap__',period=p,category='__gap__',family='__gap__') for p in ('breakfast','lunch','dinner')]


def _save(conn, pg, owner, day, token, payload):
    _execute(conn, pg, '''INSERT INTO meal_set_days_v2(owner_key,day,token,payload)
        VALUES(%s,%s,%s,%s) ON CONFLICT(owner_key,day) DO UPDATE SET payload=excluded.payload''',
        (owner,str(day),token,json.dumps(payload,ensure_ascii=False)))


def _view(token, payload, day):
    mode=payload['mode'];plan=payload['sets'][mode]
    return dict(date=str(day),token=token,mode=mode,seen_sets=payload['counts'][mode],
                mode_counts=payload['counts'],items=plan['meals'],plan=plan,
                set_limit=5,exhausted=payload['counts'][mode]>=5,history=payload.get('archives',{}).get(mode,[]),
                basis_text='아침·점심·저녁을 한 세트로 준비했어요.',version='meal-set-v1')


def load(user_id, day, build):
    owner=_key(user_id)
    initialize()
    with _connection() as (conn, pg):
        _locked(conn,pg,owner,day)
        token,payload=_get(conn,pg,owner,day)
        mode=payload['mode']
        if mode not in payload['sets']:
            payload['sets'][mode]=build(mode,_history(conn,pg,owner,day,mode),[])
            payload['counts'][mode]=1
            payload.setdefault('archives',{})[mode]=[payload['sets'][mode]]
            payload.setdefault('shown',{})[mode]=[x['id'] for x in payload['sets'][mode]['meals']]
            _save(conn,pg,owner,day,token,payload)
        return _view(token,payload,day)


def explore(user_id, day, build, *, token, mode, action, expected_day, expected_seen):
    if mode not in ('general','diet') or action not in ('open','next'):
        raise ValueError('올바른 식단 선택이 아닙니다.')
    owner=_key(user_id)
    initialize()
    with _connection() as (conn,pg):
        _locked(conn,pg,owner,day)
        authorized=_execute(conn,pg,'SELECT day FROM meal_set_days_v2 WHERE owner_key=%s AND token=%s', (owner,token)).fetchone()
        if not authorized:raise KeyError('meal set session')
        current_token,payload=_get(conn,pg,owner,day)
        rollover=expected_day!=str(day)
        if not rollover and token!=current_token:raise KeyError('stale token')
        count=payload['counts'][mode]
        if expected_seen>count and not rollover:raise ValueError('식단을 다시 불러와 주세요.')
        if mode not in payload['sets'] or (action=='next' and not rollover and count==expected_seen and count<5):
            current=payload['sets'].get(mode)
            excluded=payload.get('shown',{}).get(mode,[x['id'] for x in current['meals']] if current else [])
            payload['sets'][mode]=build(mode,_history(conn,pg,owner,day,mode),excluded)
            payload['counts'][mode]=count+1
            payload.setdefault('archives',{}).setdefault(mode,[]).append(payload['sets'][mode])
            payload.setdefault('shown',{})[mode]=list(dict.fromkeys(excluded+[x['id'] for x in payload['sets'][mode]['meals']]))
        payload['mode']=mode
        _save(conn,pg,owner,day,current_token,payload)
        return _view(current_token,payload,day)


def health():
    with _connection() as (conn,pg):
        _execute(conn,pg,'SELECT owner_key,day FROM meal_set_days_v2 LIMIT 0')
        return 'postgresql' if pg else 'local_sqlite'
