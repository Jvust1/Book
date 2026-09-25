import copy
from concurrent.futures import ThreadPoolExecutor
import threading
import pytest
from book_mygpt_selection.authority import Authority, Clock
from book_mygpt_selection.contract import BridgeError, Selection, project, digest
from test_projection import inputs, selector

class FakeClock(Clock):
    def __init__(self):self.wall=1_800_000_000_000;self.mono=100.0
    def wall_ms(self):return self.wall
    def monotonic(self):return self.mono
    def advance(self,seconds):self.wall+=int(seconds*1000);self.mono+=seconds

class Source:
    def __init__(self,data):self.data=data
    def project(self,s):return project(*self.data,s)

@pytest.fixture
def setup(inputs):
    clock=FakeClock();source=Source(inputs);auth=Authority(source,clock=clock)
    token,_=auth.authorize()
    sel=selector().json();sha=digest(source.project(selector()))
    return auth,token,sel,sha,clock,source

def grant(x,seq=1,rid='select-1'):
    auth,token,sel,sha,*_=x
    return auth.grant(token,sel,sha,seq,rid)

def test_grant_resolve_clear_and_no_body_in_ticket(setup):
    a,t,s,sha,c,source=setup;ticket=grant(setup)
    assert a.resolve(t,ticket)==source.project(Selection.parse(s))
    assert 'parts' not in ticket and 'display' not in str({k:v for k,v in ticket.items() if k!='selection'})
    a.clear(t,2,'clear-2')
    with pytest.raises(BridgeError,match='INACTIVE'):a.resolve(t,ticket)

@pytest.mark.parametrize('key,value',[('epoch',99),('content_sha256','0'*64),('expires_at_ms',1_900_000_000_000),('lease_id','forged'),('session_id','forged'),('issuer_id','forged')])
def test_mac_covers_every_identity_field(setup,key,value):
    a,t,*_=setup;ticket=grant(setup);ticket[key]=value
    with pytest.raises(BridgeError):a.resolve(t,ticket)

def test_cross_session_and_forged_body_fail(setup):
    a,t,*_=setup;ticket=grant(setup);other,_=a.authorize()
    with pytest.raises(BridgeError,match='WRONG_SESSION'):a.resolve(other,ticket)
    ticket['parts']=[{'kind':'text','text':'injected'}]
    with pytest.raises(BridgeError,match='INVALID_TICKET'):a.resolve(t,ticket)

@pytest.mark.parametrize('wall,mono',[(91,0),(0,91),(-1,0)])
def test_wall_forward_monotonic_forward_and_wall_rollback_fail(setup,wall,mono):
    a,t,s,sha,c,source=setup;ticket=grant(setup);c.wall+=wall*1000;c.mono+=mono
    with pytest.raises(BridgeError):a.resolve(t,ticket)

def test_duplicate_is_not_a_renewal_or_reactivation(setup):
    a,t,s,sha,c,source=setup;first=grant(setup);c.advance(10)
    assert grant(setup)==first
    second=grant(setup,2,'select-2')
    assert second['epoch']>first['epoch']
    with pytest.raises(BridgeError,match='INACTIVE'):grant(setup)

def test_conflicting_request_and_old_sequence_rejected(setup):
    a,t,s,sha,*_=setup;grant(setup)
    with pytest.raises(BridgeError,match='CONFLICT'):a.grant(t,s,'0'*64,1,'select-1')
    with pytest.raises(BridgeError,match='OUT_OF_ORDER'):a.clear(t,1,'old-clear')

@pytest.mark.parametrize('value',[True,0,-1,1.2,'1',2**53])
def test_sequence_is_strict_safe_integer(setup,value):
    a,t,*_=setup
    with pytest.raises(BridgeError):a.clear(t,value,'bad')

def test_stale_view_rejected_and_previous_grant_invalidated(setup):
    a,t,s,sha,c,source=setup;ticket=grant(setup)
    source.data[1]['records'][0]['parts'][0]['render_text']='Changed source'
    with pytest.raises(BridgeError,match='STALE'):grant(setup,2,'select-2')
    with pytest.raises(BridgeError,match='INACTIVE'):a.resolve(t,ticket)

def test_source_changes_under_same_version_and_commit_are_revalidated(setup):
    a,t,s,sha,c,source=setup;ticket=grant(setup)
    source.data[1]['records'][0]['parts'][0]['render_text']='Changed source'
    with pytest.raises(BridgeError,match='SOURCE_CHANGED'):a.resolve(t,ticket)
    with pytest.raises(BridgeError):a.commit_current(t,ticket,lambda:pytest.fail('must not commit'))

def test_revoke_terminal(setup):
    a,t,*_=setup;ticket=grant(setup);a.revoke(t);a.revoke(t)
    with pytest.raises(BridgeError,match='UNAUTHORIZED'):a.resolve(t,ticket)
    with pytest.raises(BridgeError):a.status(t)

def test_capacity_is_bounded_without_evicting_replay_receipts(inputs):
    source=Source(inputs);a=Authority(source,max_sessions=1,command_capacity=2);t,_=a.authorize()
    with pytest.raises(BridgeError,match='CAPACITY'):a.authorize()
    a.clear(t,1,'clear-1');a.clear(t,2,'clear-2')
    with pytest.raises(BridgeError,match='CAPACITY'):a.clear(t,3,'clear-3')
    assert a.clear(t,1,'clear-1')['last_sequence']==1

def test_late_selection_cannot_resurrect_after_newer_clear(setup):
    a,t,s,sha,c,source=setup;started=threading.Event();release=threading.Event()
    original=source.project
    def slow(sel):started.set();assert release.wait(3);return original(sel)
    source.project=slow
    with ThreadPoolExecutor() as pool:
        future=pool.submit(a.grant,t,s,sha,1,'slow')
        assert started.wait(3);a.clear(t,2,'clear');release.set()
        with pytest.raises(BridgeError,match='SUPERSEDED'):future.result()
    assert not a.status(t)['has_active_selection']

def test_commit_runs_only_while_current(setup):
    a,t,*_=setup;ticket=grant(setup)
    assert a.commit_current(t,ticket,lambda:42)==42
    a.clear(t,2,'clear')
    with pytest.raises(BridgeError):a.commit_current(t,ticket,lambda:pytest.fail('late commit'))
