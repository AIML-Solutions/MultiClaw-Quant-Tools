# region imports
from AlgorithmImports import *
from datetime import timedelta
from collections import deque
import numpy as np
# endregion


class ProportionalFeeModel(FeeModel):
    def __init__(self, rate: float, min_fee: float = 0.0):
        super().__init__()
        self._rate = float(rate)
        self._min_fee = float(min_fee)

    def get_order_fee(self, parameters):
        price = float(parameters.security.price)
        qty = abs(float(parameters.order.absolute_quantity))
        notional = price * qty
        fee = max(self._min_fee, notional * self._rate)
        ccy = parameters.security.quote_currency.symbol
        return OrderFee(CashAmount(fee, ccy))


class BpsSlippageModel:
    def __init__(self, bps: float):
        self._bps = float(bps)

    def get_slippage_approximation(self, asset, order):
        return float(asset.price) * self._bps


class AnchoredVwapState:
    """
    Multi-anchor VWAP state from daily bars:
    - weekly anchor (resets each ISO week)
    - monthly anchor (resets each calendar month)
    - event anchor (resets on shock/volume events)
    """

    def __init__(self, slope_window: int = 5):
        self.week_key = None
        self.month_key = None

        self.week_pv = 0.0
        self.week_v = 0.0
        self.month_pv = 0.0
        self.month_v = 0.0
        self.event_pv = 0.0
        self.event_v = 0.0

        self.weekly_value = None
        self.monthly_value = None
        self.event_value = None

        self.prev_close = None
        self.vol_hist = deque(maxlen=20)
        self.ret_hist = deque(maxlen=20)
        self.weekly_hist = deque(maxlen=max(2, slope_window))

    @property
    def has_core(self) -> bool:
        return self.weekly_value is not None and self.monthly_value is not None

    def weekly_slope(self) -> float:
        if len(self.weekly_hist) < 2:
            return 0.0
        start = float(self.weekly_hist[0])
        end = float(self.weekly_hist[-1])
        if abs(start) < 1e-12:
            return 0.0
        return (end - start) / abs(start)

    def _reset_week(self, week_key):
        self.week_key = week_key
        self.week_pv = 0.0
        self.week_v = 0.0

    def _reset_month(self, month_key):
        self.month_key = month_key
        self.month_pv = 0.0
        self.month_v = 0.0

    def _reset_event(self):
        self.event_pv = 0.0
        self.event_v = 0.0

    def update(self, bar: TradeBar):
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        volume = max(0.0, float(bar.volume))
        typical = (high + low + close) / 3.0
        eff_vol = max(1.0, volume)

        iso = bar.end_time.isocalendar()
        week_key = (iso.year, iso.week)
        month_key = (bar.end_time.year, bar.end_time.month)

        if self.week_key != week_key:
            self._reset_week(week_key)
        if self.month_key != month_key:
            self._reset_month(month_key)

        # Event anchor reset conditions.
        if self.prev_close is not None and self.prev_close > 0:
            gap = abs(close - self.prev_close) / self.prev_close
            ret_abs = abs(np.log(max(1e-9, close / self.prev_close)))
            self.ret_hist.append(ret_abs)

            vol_avg = float(np.mean(self.vol_hist)) if len(self.vol_hist) >= 5 else None
            ret_avg = float(np.mean(self.ret_hist)) if len(self.ret_hist) >= 8 else None

            shock_gap = gap >= 0.030
            shock_vol = vol_avg is not None and volume > 1.9 * vol_avg and gap >= 0.008
            shock_ret = ret_avg is not None and ret_abs > 2.4 * ret_avg and gap >= 0.006

            if shock_gap or shock_vol or shock_ret:
                self._reset_event()

        self.vol_hist.append(volume)

        # Accumulate all anchors.
        self.week_pv += typical * eff_vol
        self.week_v += eff_vol

        self.month_pv += typical * eff_vol
        self.month_v += eff_vol

        self.event_pv += typical * eff_vol
        self.event_v += eff_vol

        self.weekly_value = self.week_pv / self.week_v if self.week_v > 0 else None
        self.monthly_value = self.month_pv / self.month_v if self.month_v > 0 else None
        self.event_value = self.event_pv / self.event_v if self.event_v > 0 else None

        if self.weekly_value is not None:
            self.weekly_hist.append(self.weekly_value)

        self.prev_close = close


class RegimeEnsembleAlpha(QCAlgorithm):
    """
    Regime-aware allocator (enhanced):
    - momentum + trend + anchored VWAP structure score
    - volatility-normalized alpha with correlation penalty
    - volatility-targeted gross exposure + drawdown gating
    - turnover cap + cash buffer + defensive floor
    """

    def initialize(self):
        self.set_start_date(int(self.get_parameter("start_year") or 2018), 1, 1)
        self.set_end_date(int(self.get_parameter("end_year") or 2025), 12, 31)
        self.set_cash(float(self.get_parameter("initial_cash") or 100000))

        self.max_weight = float(self.get_parameter("max_weight") or 0.14)
        self.rebalance_days = int(self.get_parameter("rebalance_days") or 7)
        self.max_drawdown = float(self.get_parameter("max_drawdown") or 0.10)
        self.hard_stop_drawdown = float(self.get_parameter("hard_stop_drawdown") or 0.16)
        self.risk_off_days = int(self.get_parameter("risk_off_days") or 12)

        self.min_rebalance_delta = float(self.get_parameter("min_rebalance_delta") or 0.015)
        self.max_turnover_per_rebalance = float(self.get_parameter("max_turnover_per_rebalance") or 0.20)
        self.min_cash_pct = float(self.get_parameter("min_cash_pct") or 0.04)
        self.defensive_floor = float(self.get_parameter("defensive_floor") or 0.20)
        self.alpha_quantile_floor = float(self.get_parameter("alpha_quantile_floor") or 0.60)

        self.mom_fast_w = float(self.get_parameter("mom_fast_weight") or 0.30)
        self.mom_mid_w = float(self.get_parameter("mom_mid_weight") or 0.35)
        self.mom_slow_w = float(self.get_parameter("mom_slow_weight") or 0.35)

        self.target_portfolio_vol = float(self.get_parameter("target_portfolio_vol") or 0.10)
        self.corr_penalty_weight = float(self.get_parameter("corr_penalty_weight") or 0.20)

        # Defaults chosen for local data availability and diverse factor behavior.
        risk_default = "SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG"
        def_default = "USO,BNO"
        crypto_default = "BTCUSD,ETHUSD"

        self.include_crypto = str(self.get_parameter("include_crypto") or "false").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )
        self.max_crypto_weight_total = float(self.get_parameter("max_crypto_weight_total") or 0.25)

        risk_raw = (self.get_parameter("risk_tickers") or risk_default).upper().strip()
        def_raw = (self.get_parameter("def_tickers") or def_default).upper().strip()
        crypto_raw = (self.get_parameter("crypto_tickers") or crypto_default).upper().strip()

        self.risk_assets = [t.strip() for t in risk_raw.split(",") if t.strip()]
        self.def_assets = [t.strip() for t in def_raw.split(",") if t.strip()]
        self.crypto_assets = [t.strip() for t in crypto_raw.split(",") if t.strip()] if self.include_crypto else []

        for t in self.crypto_assets:
            if t not in self.risk_assets:
                self.risk_assets.append(t)

        self.symbols = {}
        self.is_crypto_ticker = {}
        all_tickers = list(dict.fromkeys(self.risk_assets + self.def_assets))
        for ticker in all_tickers:
            if ticker in self.crypto_assets:
                sec = self.add_crypto(ticker, Resolution.DAILY, Market.COINBASE, True)
                sec.set_fee_model(ProportionalFeeModel(rate=0.0006, min_fee=0.0))
                sec.set_slippage_model(BpsSlippageModel(0.0008))
                self.is_crypto_ticker[ticker] = True
            else:
                sec = self.add_equity(ticker, Resolution.DAILY)
                sec.set_fee_model(ProportionalFeeModel(rate=0.00005, min_fee=0.35))
                sec.set_slippage_model(BpsSlippageModel(0.0002))
                self.is_crypto_ticker[ticker] = False
            self.symbols[ticker] = sec.symbol

        # Indicators
        self.mom21 = {}
        self.mom63 = {}
        self.mom126 = {}
        self.sma20 = {}
        self.sma100 = {}
        self.atr20 = {}

        self.avwap = {}

        for sym in self.symbols.values():
            self.mom21[sym] = self.roc(sym, 21, Resolution.DAILY)
            self.mom63[sym] = self.roc(sym, 63, Resolution.DAILY)
            self.mom126[sym] = self.roc(sym, 126, Resolution.DAILY)
            self.sma20[sym] = self.sma(sym, 20, Resolution.DAILY)
            self.sma100[sym] = self.sma(sym, 100, Resolution.DAILY)
            self.atr20[sym] = self.atr(sym, 20, MovingAverageType.SIMPLE, Resolution.DAILY)
            self.avwap[sym] = AnchoredVwapState(slope_window=6)

        self.spy = self.symbols.get("SPY")
        self.qqq = self.symbols.get("QQQ", self.spy)
        self.iwm = self.symbols.get("IWM", self.spy)

        self.spy_sma200 = self.sma(self.spy, 200, Resolution.DAILY) if self.spy is not None else None
        self.qqq_sma100 = self.sma(self.qqq, 100, Resolution.DAILY) if self.qqq is not None else None
        self.iwm_sma100 = self.sma(self.iwm, 100, Resolution.DAILY) if self.iwm is not None else None

        self.peak_equity = float(self.portfolio.total_portfolio_value)
        self.last_rebalance = self.start_date - timedelta(days=30)
        self.risk_off_until = datetime.min
        self.hard_stop_armed = False

        if self.spy is not None:
            self.set_benchmark(self.spy)
        self.set_warm_up(timedelta(days=280))

        sched_symbol = self.spy if self.spy is not None else list(self.symbols.values())[0]
        self.schedule.on(
            self.date_rules.every_day(sched_symbol),
            self.time_rules.after_market_open(sched_symbol, 45),
            self.rebalance,
        )

    def on_data(self, data: Slice):
        for sym in self.symbols.values():
            if sym in data.bars:
                self.avwap[sym].update(data.bars[sym])

    def _indicator_ready(self, sym: Symbol) -> bool:
        return (
            self.mom21[sym].is_ready
            and self.mom63[sym].is_ready
            and self.mom126[sym].is_ready
            and self.sma20[sym].is_ready
            and self.sma100[sym].is_ready
            and self.atr20[sym].is_ready
            and self.avwap[sym].has_core
        )

    def _available_tickers(self):
        out = []
        for ticker, sym in self.symbols.items():
            sec = self.securities[sym]
            if not sec.has_data:
                continue
            if not self._indicator_ready(sym):
                continue
            out.append(ticker)
        return out

    def _regime_score(self) -> int:
        score = 0

        if self.spy is not None and self.spy_sma200 is not None and self.spy_sma200.is_ready:
            px = float(self.securities[self.spy].price)
            if px > float(self.spy_sma200.current.value):
                score += 1

        if self.qqq is not None and self.qqq_sma100 is not None and self.qqq_sma100.is_ready:
            px = float(self.securities[self.qqq].price)
            if px > float(self.qqq_sma100.current.value):
                score += 1

        if self.iwm is not None and self.iwm_sma100 is not None and self.iwm_sma100.is_ready:
            px = float(self.securities[self.iwm].price)
            if px > float(self.iwm_sma100.current.value):
                score += 1

        # Breadth across risk universe.
        breadth_total = 0
        breadth_up = 0
        avwap_total = 0
        avwap_up = 0

        for ticker in self.risk_assets:
            sym = self.symbols.get(ticker)
            if sym is None:
                continue
            sec = self.securities[sym]
            if not sec.has_data or not self._indicator_ready(sym):
                continue
            px = float(sec.price)

            breadth_total += 1
            if px > float(self.sma20[sym].current.value):
                breadth_up += 1

            av = self.avwap[sym]
            if av.weekly_value is not None:
                avwap_total += 1
                if px > float(av.weekly_value):
                    avwap_up += 1

        if breadth_total > 0 and breadth_up / breadth_total >= 0.60:
            score += 1

        if avwap_total > 0 and avwap_up / avwap_total >= 0.55:
            score += 1

        return score

    def _corr_to_spy(self, sym: Symbol, lookback: int = 90) -> float:
        if self.spy is None:
            return 0.0
        if sym == self.spy:
            return 1.0

        h = self.history([sym, self.spy], lookback, Resolution.DAILY)
        if h.empty:
            return 0.0

        try:
            c = h.close.unstack(level=0)
        except Exception:
            return 0.0

        if sym not in c.columns or self.spy not in c.columns:
            return 0.0

        c = c[[sym, self.spy]].dropna()
        if c.shape[0] < 30:
            return 0.0

        r1 = np.diff(np.log(c[sym].values))
        r2 = np.diff(np.log(c[self.spy].values))
        if len(r1) < 10 or np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            return 0.0

        return float(np.corrcoef(r1, r2)[0, 1])

    def _asset_alpha(self, sym: Symbol, corr_to_spy: float) -> float:
        px = float(self.securities[sym].price)
        if px <= 0:
            return -999.0

        mom = (
            self.mom_fast_w * float(self.mom21[sym].current.value)
            + self.mom_mid_w * float(self.mom63[sym].current.value)
            + self.mom_slow_w * float(self.mom126[sym].current.value)
        )

        sma20 = float(self.sma20[sym].current.value)
        sma100 = float(self.sma100[sym].current.value)
        trend_bonus = 0.20 if (px > sma20 and sma20 > sma100) else -0.10
        stretch = abs((px - sma20) / sma20) if sma20 > 0 else 0.0

        av = self.avwap[sym]
        av_bonus = 0.0
        slope_bonus = 0.0
        if av.weekly_value is not None and av.monthly_value is not None:
            w = float(av.weekly_value)
            m = float(av.monthly_value)
            if px > w and w >= m:
                av_bonus += 0.20
            elif px < w and w <= m:
                av_bonus -= 0.14

            dist_w = (px - w) / max(1e-9, px)
            av_bonus += max(-0.08, min(0.08, dist_w * 0.60))
            slope_bonus += max(-0.10, min(0.10, av.weekly_slope() * 4.0))

        if av.event_value is not None:
            e = float(av.event_value)
            dist_e = (px - e) / max(1e-9, px)
            av_bonus += max(-0.07, min(0.07, dist_e * 0.70))

        atr = float(self.atr20[sym].current.value)
        vol_proxy = max(0.004, atr / px)

        corr_penalty = self.corr_penalty_weight * max(0.0, corr_to_spy - 0.72)

        raw = (mom + trend_bonus + av_bonus + slope_bonus - 0.24 * stretch - corr_penalty) / vol_proxy
        return raw

    def _market_realized_vol(self) -> float:
        if self.spy is None:
            return self.target_portfolio_vol

        px = float(self.securities[self.spy].price)
        atr = float(self.atr20[self.spy].current.value) if self.spy in self.atr20 else 0.0
        if px <= 0 or atr <= 0:
            return self.target_portfolio_vol

        return max(0.06, min(0.65, (atr / px) * np.sqrt(252.0)))

    def _target_exposure(self, regime_score: int, drawdown: float, realized_vol: float) -> float:
        if drawdown >= self.max_drawdown:
            base = 0.20
        elif regime_score >= 5:
            base = 0.96
        elif regime_score == 4:
            base = 0.84
        elif regime_score == 3:
            base = 0.68
        elif regime_score == 2:
            base = 0.50
        elif regime_score == 1:
            base = 0.36
        else:
            base = 0.24

        vol_scale = self.target_portfolio_vol / max(0.06, realized_vol)
        vol_scale = max(0.45, min(1.18, vol_scale))

        exp = max(0.12, min(0.98, base * vol_scale))
        exp = min(exp, 1.0 - self.min_cash_pct)
        return max(0.0, exp)

    def _current_weight(self, sym: Symbol) -> float:
        tpv = float(self.portfolio.total_portfolio_value)
        if tpv <= 0:
            return 0.0
        return float(self.portfolio[sym].holdings_value) / tpv

    def _apply_crypto_cap(self, targets: dict) -> dict:
        if not self.crypto_assets:
            return targets

        crypto_syms = {self.symbols[t] for t in self.crypto_assets if t in self.symbols}
        crypto_weight = sum(w for s, w in targets.items() if s in crypto_syms)
        if crypto_weight <= self.max_crypto_weight_total or crypto_weight <= 0:
            return targets

        scale = self.max_crypto_weight_total / crypto_weight
        out = {}
        for sym, w in targets.items():
            out[sym] = w * scale if sym in crypto_syms else w
        return out

    def _apply_turnover_cap(self, targets: dict) -> dict:
        cap = max(0.0, self.max_turnover_per_rebalance)
        if cap <= 0:
            return targets

        changes = {}
        total_turnover = 0.0

        # Targets from desired portfolio.
        for sym, target in targets.items():
            cur = self._current_weight(sym)
            delta = target - cur
            changes[sym] = (cur, target, delta)
            total_turnover += abs(delta)

        # Existing holdings being flattened.
        for kvp in self.portfolio:
            sym = kvp.key
            h = kvp.value
            if not h.invested or sym in changes:
                continue
            cur = self._current_weight(sym)
            changes[sym] = (cur, 0.0, -cur)
            total_turnover += abs(cur)

        if total_turnover <= cap + 1e-12:
            return targets

        scale = cap / max(1e-12, total_turnover)
        adjusted = {}
        for sym, (cur, _, delta) in changes.items():
            new_w = cur + delta * scale
            if new_w > 0:
                adjusted[sym] = new_w

        return adjusted

    def rebalance(self):
        if self.is_warming_up:
            return

        if (self.time.date() - self.last_rebalance.date()).days < self.rebalance_days:
            return

        available = self._available_tickers()
        if len(available) < 3:
            self.debug(f"rebalance skipped: insufficient ready symbols ({len(available)})")
            return

        tpv = float(self.portfolio.total_portfolio_value)
        self.peak_equity = max(self.peak_equity, tpv)
        drawdown = (self.peak_equity - tpv) / self.peak_equity if self.peak_equity > 0 else 0.0

        if drawdown >= self.hard_stop_drawdown and not self.hard_stop_armed:
            self.risk_off_until = max(self.risk_off_until, self.time + timedelta(days=self.risk_off_days))
            self.hard_stop_armed = True
        elif drawdown <= (self.max_drawdown * 0.60):
            # Rearm only after significant recovery to avoid repeatedly extending risk-off windows.
            self.hard_stop_armed = False

        in_risk_off = self.time < self.risk_off_until

        regime = self._regime_score()
        realized_vol = self._market_realized_vol()
        target_exposure = self._target_exposure(regime, drawdown, realized_vol)

        if in_risk_off:
            target_exposure = min(target_exposure, 0.25)

        corr_cache = {}
        for ticker in available:
            sym = self.symbols[ticker]
            corr_cache[ticker] = self._corr_to_spy(sym)

        candidates = []
        for ticker in available:
            sym = self.symbols[ticker]
            sc = self._asset_alpha(sym, corr_cache[ticker])

            if ticker in self.risk_assets and regime <= 1:
                sc *= 0.55
            if ticker in self.def_assets and regime <= 1:
                sc *= 1.25
            if in_risk_off and ticker in self.risk_assets:
                sc *= 0.40

            candidates.append((ticker, sym, sc))

        positives = [(t, s, a) for t, s, a in candidates if a > 0]
        targets = {}

        if positives:
            alpha_vals = np.array([a for _, _, a in positives], dtype=float)
            q_floor = float(np.quantile(alpha_vals, min(0.95, max(0.0, self.alpha_quantile_floor))))
            positives = [(t, s, a) for t, s, a in positives if a >= q_floor]

        if positives:
            positives.sort(key=lambda x: x[2], reverse=True)
            top_n = int(self.get_parameter("top_n") or 6)
            selected = positives[:max(1, top_n)]

            raw_targets = {}
            blend_sum = 0.0
            for ticker, sym, alpha in selected:
                px = float(self.securities[sym].price)
                atr = float(self.atr20[sym].current.value)
                vol = max(0.004, atr / max(1e-9, px))
                inv_vol = 1.0 / vol
                blend = max(0.0, alpha) * np.sqrt(inv_vol)
                raw_targets[sym] = blend
                blend_sum += blend

            if blend_sum > 0:
                for sym, blend in raw_targets.items():
                    w = (blend / blend_sum) * target_exposure
                    targets[sym] = min(self.max_weight, max(0.0, w))

        # Defensive fallback / floor (only include defensive assets with positive short trend).
        def_syms = []
        for t in self.def_assets:
            if t not in available:
                continue
            s = self.symbols[t]
            px = float(self.securities[s].price)
            s20 = float(self.sma20[s].current.value)
            if px > s20:
                def_syms.append(s)
        if (not targets) and def_syms:
            eq = min(0.30, target_exposure)
            each = eq / len(def_syms)
            for s in def_syms:
                targets[s] = each

        if regime <= 1 and def_syms:
            floor_each = self.defensive_floor / len(def_syms)
            for s in def_syms:
                targets[s] = max(targets.get(s, 0.0), floor_each)

        if in_risk_off and def_syms:
            # Prefer defensive shelf during risk-off cooldown.
            desired = min(0.35, max(self.defensive_floor, target_exposure))
            each = desired / len(def_syms)
            targets = {s: each for s in def_syms}

        gross = sum(targets.values())
        if gross > 0:
            scale = min(1.0, target_exposure / gross)
            for sym in list(targets.keys()):
                targets[sym] *= scale

        targets = self._apply_crypto_cap(targets)
        targets = self._apply_turnover_cap(targets)

        # Flatten removed holdings.
        target_syms = set(targets.keys())
        for kvp in self.portfolio:
            sym = kvp.key
            h = kvp.value
            if h.invested and sym not in target_syms and abs(self._current_weight(sym)) >= self.min_rebalance_delta:
                self.liquidate(sym, "out_of_target")

        # Apply targets with turnover guard.
        for sym, w in targets.items():
            current_w = self._current_weight(sym)
            if abs(w - current_w) < self.min_rebalance_delta:
                continue
            self.set_holdings(sym, w)

        self.last_rebalance = self.time
        self.debug(
            f"rebalance regime={regime} dd={drawdown:.2%} vol={realized_vol:.2%} "
            f"target_exposure={target_exposure:.2f} symbols={len(available)} holdings={len(targets)} "
            f"risk_off={in_risk_off} hard_stop_armed={self.hard_stop_armed}"
        )

    def on_end_of_algorithm(self):
        tpv = float(self.portfolio.total_portfolio_value)
        dd = (self.peak_equity - tpv) / self.peak_equity if self.peak_equity > 0 else 0.0
        crypto_syms = {self.symbols[t] for t in self.crypto_assets if t in self.symbols}
        crypto_w = sum(abs(self._current_weight(s)) for s in crypto_syms)
        self.log(
            f"END | TPV={tpv:.2f} | peak={self.peak_equity:.2f} | drawdown={dd:.2%} | "
            f"include_crypto={self.include_crypto} | crypto_weight={crypto_w:.2%} | "
            f"risk_off_until={self.risk_off_until}"
        )
