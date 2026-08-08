from coinarb.models import Observation
from coinarb.opportunities import compute_opportunities

def test_cross_dealer_only_and_positive():
 obs=[
 Observation('a','sku','ask',100,'u','x'), Observation('b','sku','bid',105,'u','x',bid_quality='A'),
 Observation('a','sku','bid',200,'u','x',bid_quality='A')]
 out=compute_opportunities(obs)
 assert len(out)==1 and out[0]['buy_dealer']=='a' and out[0]['sell_dealer']=='b'

def test_c_quality_excluded():
 obs=[Observation('a','sku','ask',100,'u','x'),Observation('b','sku','bid',120,'u','x',bid_quality='C')]
 assert compute_opportunities(obs)==[]
