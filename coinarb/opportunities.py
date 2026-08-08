def compute_opportunities(observations, cost_fn=lambda b,s,q: 0.0):
    asks = [o for o in observations if o.side == 'ask']
    bids = [o for o in observations if o.side == 'bid' and o.bid_quality in ('A','B')]
    out = []
    for a in asks:
        for b in bids:
            if a.canonical_sku != b.canonical_sku or a.dealer_id == b.dealer_id:
                continue
            q = 1.0
            cost = cost_fn(a,b,q)
            net = b.price - a.price - cost
            if net > 0:
                out.append({
                    'sku': a.canonical_sku,
                    'buy_dealer': a.dealer_id,
                    'sell_dealer': b.dealer_id,
                    'buy': a.price,
                    'sell': b.price,
                    'gross': b.price-a.price,
                    'cost': cost,
                    'net': net,
                    'net_return': net/a.price,
                })
    return sorted(out, key=lambda x: x['net'], reverse=True)
