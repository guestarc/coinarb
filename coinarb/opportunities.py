def compute_opportunities(observations, cost_fn=lambda b, s, q: 0.0):
    asks = [o for o in observations if o.side == 'ask']
    bids = [o for o in observations if o.side == 'bid' and o.bid_quality in ('A', 'B')]
    out = []
    for ask in asks:
        for bid in bids:
            if ask.canonical_sku != bid.canonical_sku or ask.dealer_id == bid.dealer_id:
                continue
            quantity = 1.0
            cost = cost_fn(ask, bid, quantity)
            net = bid.price - ask.price - cost
            if net <= 0:
                continue
            episode_key = f"{ask.canonical_sku}|{ask.dealer_id}|{bid.dealer_id}"
            out.append({
                'episode_key': episode_key,
                'sku': ask.canonical_sku,
                'buy_dealer': ask.dealer_id,
                'sell_dealer': bid.dealer_id,
                'buy': ask.price,
                'sell': bid.price,
                'gross': bid.price - ask.price,
                'cost': cost,
                'net': net,
                'net_return': net / ask.price,
            })
    return sorted(out, key=lambda x: x['net'], reverse=True)
