# region imports
from AlgorithmImports import *
from datetime import timedelta
import math
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


class OptionMath:
    @staticmethod
    def norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @staticmethod
    def norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

    @staticmethod
    def bs_price(s: float, k: float, t: float, r: float, sigma: float, right: OptionRight) -> float:
        if s <= 0 or k <= 0 or t <= 0 or sigma <= 0:
            intrinsic = max(0.0, s - k) if right == OptionRight.CALL else max(0.0, k - s)
            return intrinsic

        sqt = math.sqrt(t)
        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqt)
        d2 = d1 - sigma * sqt

        if right == OptionRight.CALL:
            return s * OptionMath.norm_cdf(d1) - k * math.exp(-r * t) * OptionMath.norm_cdf(d2)
        return k * math.exp(-r * t) * OptionMath.norm_cdf(-d2) - s * OptionMath.norm_cdf(-d1)

    @staticmethod
    def bs_delta(s: float, k: float, t: float, r: float, sigma: float, right: OptionRight) -> float:
        if s <= 0 or k <= 0 or t <= 0 or sigma <= 0:
            if right == OptionRight.CALL:
                return 1.0 if s > k else 0.0
            return -1.0 if s < k else 0.0

        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
        if right == OptionRight.CALL:
            return OptionMath.norm_cdf(d1)
        return OptionMath.norm_cdf(d1) - 1.0

    @staticmethod
    def bs_vega(s: float, k: float, t: float, r: float, sigma: float) -> float:
        if s <= 0 or k <= 0 or t <= 0 or sigma <= 0:
            return 0.0
        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
        return s * OptionMath.norm_pdf(d1) * math.sqrt(t)

    @staticmethod
    def implied_vol(mid: float, s: float, k: float, t: float, r: float, right: OptionRight, floor: float, cap: float):
        if mid <= 0 or s <= 0 or k <= 0 or t <= 0:
            return None

        sigma = 0.35
        for _ in range(24):
            price = OptionMath.bs_price(s, k, t, r, sigma, right)
            vega = OptionMath.bs_vega(s, k, t, r, sigma)
            diff = price - mid
            if abs(diff) < 1e-4:
                break
            if vega < 1e-8:
                break
            sigma = sigma - diff / vega
            sigma = max(floor, min(cap, sigma))

        if sigma < floor or sigma > cap:
            return None
        return float(sigma)


class OptionsGreeksVix(QCAlgorithm):
    """
    Adaptive options lane (enhanced):
    - directional long options with DTE/delta targeting
    - Black-Scholes fallback for IV/Greeks when chain greeks are incomplete
    - live Greek exposure constraints (delta/vega)
    - fallback underlying trend sleeve when chain data is unavailable
    """

    def initialize(self):
        self.set_start_date(int(self.get_parameter("start_year") or 2014), 1, 1)
        self.set_end_date(int(self.get_parameter("end_year") or 2025), 12, 31)
        self.set_cash(float(self.get_parameter("initial_cash") or 100000))

        # Market/config
        self.underlying_ticker = (self.get_parameter("underlying_ticker") or "SPY").upper().strip()
        self.option_underlying_ticker = (self.get_parameter("option_underlying_ticker") or "AAPL").upper().strip()
        self.enable_options = str(self.get_parameter("enable_options") or "true").lower() in ("1", "true", "yes", "y")
        self.enable_fallback_equity = str(self.get_parameter("fallback_equity_mode") or "true").lower() in (
            "1",
            "true",
            "yes",
            "y",
        )

        # Risk controls
        self.max_contracts = int(self.get_parameter("max_contracts") or 2)
        self.cooldown_days = int(self.get_parameter("cooldown_days") or 3)
        self.take_profit = float(self.get_parameter("take_profit") or 0.35)
        self.stop_loss = float(self.get_parameter("stop_loss") or -0.18)
        self.max_holding_days = int(self.get_parameter("max_holding_days") or 8)
        self.max_alloc_pct = float(self.get_parameter("max_alloc_pct") or 0.02)
        self.min_option_price = float(self.get_parameter("min_option_price") or 0.20)
        self.max_spread_pct = float(self.get_parameter("max_spread_pct") or 0.25)
        self.max_drawdown_pct = float(self.get_parameter("max_drawdown_pct") or 0.12)
        self.risk_off_cooldown_days = int(self.get_parameter("risk_off_cooldown_days") or 7)
        self.max_daily_entries = int(self.get_parameter("max_daily_entries") or 1)

        self.max_abs_delta_exposure = float(self.get_parameter("max_abs_delta_exposure") or 350.0)
        self.max_abs_vega_exposure = float(self.get_parameter("max_abs_vega_exposure") or 6000.0)
        self.iv_floor = float(self.get_parameter("iv_floor") or 0.05)
        self.iv_cap = float(self.get_parameter("iv_cap") or 2.20)
        self.risk_free_rate = float(self.get_parameter("risk_free_rate") or 0.01)

        # Regime tuning
        legacy_target_delta = self.get_parameter("target_delta")
        if legacy_target_delta:
            td = float(legacy_target_delta)
            self.target_delta_low_vol = td
            self.target_delta_high_vol = max(0.15, td - 0.08)
        else:
            self.target_delta_low_vol = float(self.get_parameter("target_delta_low_vol") or 0.34)
            self.target_delta_high_vol = float(self.get_parameter("target_delta_high_vol") or 0.24)

        self.target_dte_low_vol = int(self.get_parameter("target_dte_low_vol") or 24)
        self.target_dte_high_vol = int(self.get_parameter("target_dte_high_vol") or 12)
        self.min_dte = int(self.get_parameter("min_dte") or 6)
        self.max_dte = int(self.get_parameter("max_dte") or 45)
        self.high_vol_atr_pct = float(self.get_parameter("high_vol_atr_pct") or 0.024)

        # Fallback controls
        self.fallback_trigger_days = int(self.get_parameter("fallback_trigger_days") or 5)
        self.fallback_disable_option_days = int(self.get_parameter("fallback_disable_option_days") or 20)
        self.fallback_alloc_pct = float(self.get_parameter("fallback_alloc_pct") or 0.20)
        self.fallback_stop_atr_mult = float(self.get_parameter("fallback_stop_atr_mult") or 2.3)
        self.fallback_take_profit = float(self.get_parameter("fallback_take_profit") or 0.10)

        # Core underlyings (daily to remain data-compatible in local environments).
        under_sec = self.add_equity(self.underlying_ticker, Resolution.DAILY)
        opt_under_sec = self.add_equity(self.option_underlying_ticker, Resolution.DAILY)

        under_sec.set_fee_model(ProportionalFeeModel(rate=0.00005, min_fee=0.35))
        under_sec.set_slippage_model(BpsSlippageModel(0.0002))
        opt_under_sec.set_fee_model(ProportionalFeeModel(rate=0.00005, min_fee=0.35))
        opt_under_sec.set_slippage_model(BpsSlippageModel(0.00025))

        self.underlying = under_sec.symbol
        self.option_underlying = opt_under_sec.symbol

        self.fast = self.sma(self.underlying, 50, Resolution.DAILY)
        self.slow = self.sma(self.underlying, 200, Resolution.DAILY)
        self.atr = self.atr(self.underlying, 20, MovingAverageType.WILDERS, Resolution.DAILY)

        self.option_symbol = None
        if self.enable_options:
            opt = self.add_option(self.option_underlying_ticker, Resolution.DAILY)
            opt.set_filter(lambda u: u.strikes(-12, 12).expiration(timedelta(days=1), timedelta(days=55)))
            opt.set_fee_model(ProportionalFeeModel(rate=0.0035, min_fee=0.65))
            opt.set_slippage_model(BpsSlippageModel(0.0012))
            self.option_symbol = opt.symbol

        self.open_option_symbols = set()
        self.open_meta = {}  # option symbol -> {entry_time, entry_price, iv_est}
        self.fallback_meta = None  # {entry_time, entry_price, stop_price}

        self.days_without_chain = 0
        self.option_lane_disabled = False
        self.next_entry_time = self.start_date
        self.entries_today = 0
        self.entries_day = None
        self.peak_equity = float(self.portfolio.total_portfolio_value)

        self.set_benchmark(self.underlying)
        self.set_warm_up(timedelta(days=240))

    def _time_to_expiry_years(self, expiry: datetime) -> float:
        days = max(0, (expiry.date() - self.time.date()).days)
        return max(1.0 / 365.0, days / 365.0)

    def _mid_price(self, contract) -> float:
        bid = float(contract.bid_price) if contract.bid_price is not None else 0.0
        ask = float(contract.ask_price) if contract.ask_price is not None else 0.0
        last = float(contract.last_price) if contract.last_price is not None else 0.0
        if bid > 0 and ask > 0 and ask >= bid:
            return 0.5 * (bid + ask)
        return last

    def _spread_pct(self, contract) -> float:
        bid = float(contract.bid_price) if contract.bid_price is not None else 0.0
        ask = float(contract.ask_price) if contract.ask_price is not None else 0.0
        if bid <= 0 or ask <= 0 or ask < bid:
            return 0.10
        mid = 0.5 * (bid + ask)
        return (ask - bid) / max(1e-9, mid)

    def _is_high_vol_regime(self) -> bool:
        if not (self.atr.is_ready and self.fast.is_ready and self.slow.is_ready):
            return False

        px = float(self.securities[self.underlying].price)
        if px <= 0:
            return False

        atr_pct = float(self.atr.current.value) / px
        return atr_pct >= self.high_vol_atr_pct

    def _risk_direction(self) -> OptionRight:
        if not (self.fast.is_ready and self.slow.is_ready):
            return OptionRight.CALL

        px = float(self.securities[self.underlying].price)
        uptrend = px > float(self.fast.current.value) and float(self.fast.current.value) > float(self.slow.current.value)

        if uptrend and not self._is_high_vol_regime():
            return OptionRight.CALL
        return OptionRight.PUT

    def _estimate_abs_delta(self, contract, mark: float) -> float:
        if contract.greeks is not None and contract.greeks.delta is not None:
            return abs(float(contract.greeks.delta))

        und_px = float(self.securities[self.option_underlying].price)
        if und_px <= 0 or mark <= 0:
            return 0.0

        t = self._time_to_expiry_years(contract.expiry)
        iv = OptionMath.implied_vol(
            mark,
            und_px,
            float(contract.strike),
            t,
            self.risk_free_rate,
            contract.right,
            self.iv_floor,
            self.iv_cap,
        )
        if iv is None:
            m = abs(float(contract.strike) - und_px) / und_px
            return max(0.05, min(0.95, 1 - 2.2 * m))

        delta = OptionMath.bs_delta(
            und_px,
            float(contract.strike),
            t,
            self.risk_free_rate,
            iv,
            contract.right,
        )
        return abs(float(delta))

    def _estimate_iv(self, contract, mark: float):
        und_px = float(self.securities[self.option_underlying].price)
        if und_px <= 0 or mark <= 0:
            return None
        t = self._time_to_expiry_years(contract.expiry)
        return OptionMath.implied_vol(
            mark,
            und_px,
            float(contract.strike),
            t,
            self.risk_free_rate,
            contract.right,
            self.iv_floor,
            self.iv_cap,
        )

    def _estimate_vega(self, contract, iv: float) -> float:
        und_px = float(self.securities[self.option_underlying].price)
        if und_px <= 0 or iv is None:
            return 0.0
        t = self._time_to_expiry_years(contract.expiry)
        return OptionMath.bs_vega(
            und_px,
            float(contract.strike),
            t,
            self.risk_free_rate,
            iv,
        )

    def _select_contract(self, chain: OptionChain, right: OptionRight, target_delta: float, target_dte: int):
        best = None
        best_score = 1e9

        und_px = float(self.securities[self.option_underlying].price)
        if und_px <= 0:
            return None, None

        # Reference IV from nearest ATM candidate.
        atm_iv = None
        atm_dist = 1e9
        for c in chain:
            if c.right != right:
                continue
            mark = self._mid_price(c)
            if mark <= 0:
                continue
            iv = self._estimate_iv(c, mark)
            if iv is None:
                continue
            d = abs(float(c.strike) - und_px)
            if d < atm_dist:
                atm_dist = d
                atm_iv = iv

        for c in chain:
            if c.right != right:
                continue

            dte = (c.expiry.date() - self.time.date()).days
            if dte < self.min_dte or dte > self.max_dte:
                continue

            mark = self._mid_price(c)
            spread_pct = self._spread_pct(c)
            if mark < self.min_option_price:
                continue
            if spread_pct > self.max_spread_pct:
                continue

            abs_delta = self._estimate_abs_delta(c, mark)
            if abs_delta <= 0:
                continue

            iv = self._estimate_iv(c, mark)
            if iv is not None and not (self.iv_floor <= iv <= self.iv_cap):
                continue

            moneyness = abs(float(c.strike) - und_px) / und_px
            iv_penalty = 0.0
            if iv is not None and atm_iv is not None:
                iv_penalty = 0.25 * abs(iv - atm_iv)

            oi = float(c.open_interest) if c.open_interest is not None else 0.0
            oi_penalty = 0.10 if oi <= 0 else 0.0

            score = (
                abs(abs_delta - target_delta)
                + 0.018 * abs(dte - target_dte)
                + 1.8 * moneyness
                + 0.35 * spread_pct
                + iv_penalty
                + oi_penalty
            )

            if score < best_score:
                best_score = score
                best = c

        if best is None:
            return None, None

        mark = self._mid_price(best)
        iv = self._estimate_iv(best, mark)
        return best, iv

    def _compute_option_greek_exposure(self):
        net_delta = 0.0
        net_vega = 0.0

        und_px = float(self.securities[self.option_underlying].price)
        if und_px <= 0:
            return 0.0, 0.0

        for sym in list(self.open_option_symbols):
            holding = self.portfolio[sym]
            if not holding.invested:
                continue

            qty = float(holding.quantity)
            mark = float(self.securities[sym].price)
            if mark <= 0:
                continue

            strike = float(sym.id.strike_price)
            expiry = sym.id.date
            right = sym.id.option_right
            t = self._time_to_expiry_years(expiry)

            iv = self.open_meta.get(sym, {}).get("iv_est")
            if iv is None:
                iv = OptionMath.implied_vol(
                    mark,
                    und_px,
                    strike,
                    t,
                    self.risk_free_rate,
                    right,
                    self.iv_floor,
                    self.iv_cap,
                )
            if iv is None:
                continue

            delta = OptionMath.bs_delta(und_px, strike, t, self.risk_free_rate, iv, right)
            vega = OptionMath.bs_vega(und_px, strike, t, self.risk_free_rate, iv)

            net_delta += qty * 100.0 * float(delta)
            net_vega += qty * 100.0 * float(vega)

        return net_delta, net_vega

    def _manage_option_positions(self):
        for sym in list(self.open_option_symbols):
            holding = self.portfolio[sym]
            if not holding.invested:
                self.open_option_symbols.discard(sym)
                self.open_meta.pop(sym, None)
                continue

            px = float(self.securities[sym].price)
            avg = float(holding.average_price)
            if avg <= 0:
                continue

            pnl = (px - avg) / avg
            dte = (sym.id.date.date() - self.time.date()).days

            meta = self.open_meta.get(sym, {})
            entry_time = meta.get("entry_time", self.time)
            holding_days = max(0, (self.time.date() - entry_time.date()).days)

            # Dynamic cut: if IV collapses sharply post entry, reduce hold time.
            iv_entry = meta.get("iv_est")
            iv_now = None
            und_px = float(self.securities[self.option_underlying].price)
            t = self._time_to_expiry_years(sym.id.date)
            if und_px > 0 and px > 0:
                iv_now = OptionMath.implied_vol(px, und_px, float(sym.id.strike_price), t, self.risk_free_rate, sym.id.option_right, self.iv_floor, self.iv_cap)

            iv_crush = (iv_entry is not None and iv_now is not None and iv_now < 0.72 * iv_entry)

            if dte <= 2 or holding_days >= self.max_holding_days or pnl >= self.take_profit or pnl <= self.stop_loss or iv_crush:
                self.liquidate(sym, f"option_risk_exit dte={dte} days={holding_days} pnl={pnl:.2%}")
                self.open_option_symbols.discard(sym)
                self.open_meta.pop(sym, None)

    def _manage_fallback_position(self):
        if self.fallback_meta is None:
            return

        holding = self.portfolio[self.underlying]
        if not holding.invested:
            self.fallback_meta = None
            return

        px = float(self.securities[self.underlying].price)
        avg = float(holding.average_price)
        if avg <= 0:
            return

        pnl = (px - avg) / avg
        entry_time = self.fallback_meta.get("entry_time", self.time)
        holding_days = max(0, (self.time.date() - entry_time.date()).days)

        atr_now = float(self.atr.current.value) if self.atr.is_ready else 0.0
        trail_stop = px - self.fallback_stop_atr_mult * atr_now
        self.fallback_meta["stop_price"] = max(self.fallback_meta.get("stop_price", trail_stop), trail_stop)

        stop_hit = px <= self.fallback_meta.get("stop_price", -1e9)
        trend_broken = self.fast.is_ready and px < float(self.fast.current.value)

        if (
            stop_hit
            or trend_broken
            or pnl >= self.fallback_take_profit
            or pnl <= self.stop_loss
            or holding_days >= self.max_holding_days
        ):
            self.liquidate(self.underlying, f"fallback_exit pnl={pnl:.2%} days={holding_days}")
            self.fallback_meta = None

    def _refresh_daily_entry_counter(self):
        day = self.time.date()
        if self.entries_day != day:
            self.entries_day = day
            self.entries_today = 0

    def _drawdown_guard(self) -> bool:
        tpv = float(self.portfolio.total_portfolio_value)
        self.peak_equity = max(self.peak_equity, tpv)
        dd = (self.peak_equity - tpv) / self.peak_equity if self.peak_equity > 0 else 0.0

        if dd < self.max_drawdown_pct:
            return False

        self.option_lane_disabled = True
        self.liquidate("max_drawdown_guard")
        self.next_entry_time = self.time + timedelta(days=self.risk_off_cooldown_days)
        self.debug(f"risk_off_guard triggered drawdown={dd:.2%}; cooling down until {self.next_entry_time}")
        return True

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        self._refresh_daily_entry_counter()
        if self._drawdown_guard():
            return

        self._manage_option_positions()
        self._manage_fallback_position()

        # One sleeve at a time.
        if any(self.portfolio[s].invested for s in self.open_option_symbols):
            return
        if self.portfolio[self.underlying].invested:
            return

        if self.time < self.next_entry_time:
            return

        if not (self.fast.is_ready and self.slow.is_ready and self.atr.is_ready):
            return

        if self.entries_today >= self.max_daily_entries:
            return

        net_delta, net_vega = self._compute_option_greek_exposure()
        if abs(net_delta) > self.max_abs_delta_exposure or abs(net_vega) > self.max_abs_vega_exposure:
            self.debug(f"greek guard blocked entry: net_delta={net_delta:.1f}, net_vega={net_vega:.1f}")
            return

        high_vol = self._is_high_vol_regime()
        right = self._risk_direction()

        target_delta = self.target_delta_high_vol if high_vol else self.target_delta_low_vol
        target_dte = self.target_dte_high_vol if high_vol else self.target_dte_low_vol

        entered = False

        if (not self.enable_options) and self.enable_fallback_equity:
            # Fallback-only mode: mark option availability as degraded so fallback can engage.
            self.days_without_chain = max(self.days_without_chain, self.fallback_trigger_days)

        # 1) Primary options lane
        if self.enable_options and (not self.option_lane_disabled) and self.option_symbol is not None:
            chain = data.option_chains.get(self.option_symbol)
            if chain is not None and len(chain) > 0:
                contract, iv_est = self._select_contract(chain, right, target_delta, target_dte)
                if contract is not None:
                    mark = self._mid_price(contract)

                    if mark > 0:
                        alloc_cash = max(0.0, float(self.portfolio.cash) * self.max_alloc_pct)
                        qty = int(alloc_cash // (mark * 100.0))
                        qty = max(1, min(qty, self.max_contracts))

                        if (mark * 100.0 * qty) <= float(self.portfolio.cash):
                            ticket = self.market_order(contract.symbol, qty, tag=f"option_entry right={right} hv={high_vol}")
                            if ticket is not None:
                                self.open_option_symbols.add(contract.symbol)
                                self.open_meta[contract.symbol] = {
                                    "entry_time": self.time,
                                    "entry_price": mark,
                                    "iv_est": iv_est,
                                }
                                self.days_without_chain = 0
                                self.entries_today += 1
                                entered = True
            else:
                self.days_without_chain += 1
                if self.days_without_chain >= self.fallback_disable_option_days:
                    self.option_lane_disabled = True
                    self.debug(
                        f"option lane disabled after {self.days_without_chain} days without chain data; "
                        f"continuing with fallback underlying mode"
                    )

        # 2) Fallback equity lane
        if (not entered) and self.enable_fallback_equity and self.days_without_chain >= self.fallback_trigger_days:
            px = float(self.securities[self.underlying].price)
            fast = float(self.fast.current.value)
            slow = float(self.slow.current.value)

            bullish = px > fast and fast > slow
            if bullish:
                alloc_cash = max(0.0, float(self.portfolio.cash) * self.fallback_alloc_pct)
                qty = int(alloc_cash // max(1e-9, px))
                if qty > 0:
                    ticket = self.market_order(self.underlying, qty, tag="fallback_underlying_entry")
                    if ticket is not None:
                        atr_now = float(self.atr.current.value)
                        self.fallback_meta = {
                            "entry_time": self.time,
                            "entry_price": px,
                            "stop_price": px - self.fallback_stop_atr_mult * atr_now,
                        }
                        self.entries_today += 1
                        entered = True

        if entered:
            self.next_entry_time = self.time + timedelta(days=self.cooldown_days)

    def on_end_of_algorithm(self):
        tpv = float(self.portfolio.total_portfolio_value)
        dd = (self.peak_equity - tpv) / self.peak_equity if self.peak_equity > 0 else 0.0
        net_delta, net_vega = self._compute_option_greek_exposure()
        self.log(
            f"END | TPV={tpv:.2f} | peak={self.peak_equity:.2f} | drawdown={dd:.2%} | "
            f"days_without_chain={self.days_without_chain} | option_lane_disabled={self.option_lane_disabled} | "
            f"net_delta={net_delta:.1f} | net_vega={net_vega:.1f}"
        )
