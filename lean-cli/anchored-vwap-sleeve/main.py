# region imports
from AlgorithmImports import *
from datetime import timedelta
from collections import deque
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


class AnchoredVwapState:
    def __init__(self, slope_window: int = 6):
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
        a = float(self.weekly_hist[0])
        b = float(self.weekly_hist[-1])
        if abs(a) < 1e-12:
            return 0.0
        return (b - a) / abs(a)

    def _reset_week(self, key):
        self.week_key = key
        self.week_pv = 0.0
        self.week_v = 0.0

    def _reset_month(self, key):
        self.month_key = key
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

        if self.prev_close is not None and self.prev_close > 0:
            gap = abs(close - self.prev_close) / self.prev_close
            ret_abs = abs(math.log(max(1e-9, close / self.prev_close)))
            self.ret_hist.append(ret_abs)

            vol_avg = (sum(self.vol_hist) / len(self.vol_hist)) if len(self.vol_hist) >= 5 else None
            ret_avg = (sum(self.ret_hist) / len(self.ret_hist)) if len(self.ret_hist) >= 8 else None

            shock_gap = gap >= 0.030
            shock_vol = vol_avg is not None and volume > 1.9 * vol_avg and gap >= 0.008
            shock_ret = ret_avg is not None and ret_abs > 2.4 * ret_avg and gap >= 0.006

            if shock_gap or shock_vol or shock_ret:
                self._reset_event()

        self.vol_hist.append(volume)

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


class SymbolState:
    def __init__(self, symbol: Symbol, is_crypto: bool, atr: AverageTrueRange, sma: SimpleMovingAverage):
        self.symbol = symbol
        self.is_crypto = is_crypto

        self.atr = atr
        self.sma = sma
        self.avwap = AnchoredVwapState(slope_window=6)

        self.raw_last_close = None
        self.raw_prev_close = None

    @property
    def ready(self) -> bool:
        return self.atr.is_ready and self.sma.is_ready and self.avwap.has_core

    @property
    def raw_close(self) -> float:
        return float(self.raw_last_close or 0.0)

    @property
    def atr_value(self) -> float:
        return float(self.atr.current.value) if self.atr.is_ready else 0.0


class AnchoredVwapCrossAssetSleeve(QCAlgorithm):
    """
    Cross-asset Anchored VWAP sleeve:
    - weekly/monthly/event AVWAP confluence entries
    - benchmark regime gate
    - ATR-based sizing and non-widening trailing stops
    - partial-fill-safe protective stop maintenance
    """

    def initialize(self):
        self.set_start_date(int(self.get_parameter("start_year") or 2019), 1, 1)
        self.set_end_date(int(self.get_parameter("end_year") or 2025), 12, 31)
        self.set_cash(float(self.get_parameter("initial_cash") or 100000))

        self.risk_per_trade = float(self.get_parameter("risk_per_trade") or 0.003)
        self.max_positions = int(self.get_parameter("max_positions") or 3)
        self.max_position_weight = float(self.get_parameter("max_position_weight") or 0.15)
        self.cooldown_days = int(self.get_parameter("cooldown_days") or 5)

        self.atr_stop_mult = float(self.get_parameter("atr_stop_mult") or 2.4)
        self.trail_atr_mult = float(self.get_parameter("trail_atr_mult") or 1.9)
        self.min_stop_pct = float(self.get_parameter("min_stop_pct") or 0.015)
        self.min_trail_pct = float(self.get_parameter("min_trail_pct") or 0.020)

        self.min_hold_days = int(self.get_parameter("min_hold_days") or 3)
        self.max_entries_per_day = int(self.get_parameter("max_entries_per_day") or 2)
        self.entry_gap_pct_max = float(self.get_parameter("entry_gap_pct_max") or 0.050)
        self.max_benchmark_atr_pct = float(self.get_parameter("max_benchmark_atr_pct") or 0.045)
        self.weekly_entry_only = str(self.get_parameter("weekly_entry_only") or "true").lower() in ("1", "true", "yes", "y")

        self.include_crypto = str(self.get_parameter("include_crypto") or "false").lower() in ("1", "true", "yes", "y")

        eq_default = "SPY,QQQ,IWM,EEM,TLT,GLD,USO"
        cr_default = "BTCUSD,ETHUSD"

        eq_raw = (self.get_parameter("equity_tickers") or eq_default).upper().strip()
        cr_raw = (self.get_parameter("crypto_tickers") or cr_default).upper().strip()

        eq_tickers = [t.strip() for t in eq_raw.split(",") if t.strip()]
        cr_tickers = [t.strip() for t in cr_raw.split(",") if t.strip()] if self.include_crypto else []

        self.states = {}
        self.ticker_to_symbol = {}

        for ticker in eq_tickers:
            sec = self.add_equity(ticker, Resolution.DAILY)
            sec.set_data_normalization_mode(DataNormalizationMode.RAW)
            sec.set_fee_model(ProportionalFeeModel(rate=0.00005, min_fee=0.35))
            sec.set_slippage_model(BpsSlippageModel(0.0002))

            atr = self.atr(sec.symbol, 14, MovingAverageType.WILDERS, Resolution.DAILY)
            sma = self.sma(sec.symbol, 50, Resolution.DAILY)
            self.states[sec.symbol] = SymbolState(sec.symbol, is_crypto=False, atr=atr, sma=sma)
            self.ticker_to_symbol[ticker] = sec.symbol

        for ticker in cr_tickers:
            sec = self.add_crypto(ticker, Resolution.DAILY, Market.COINBASE, True)
            sec.set_fee_model(ProportionalFeeModel(rate=0.0006, min_fee=0.0))
            sec.set_slippage_model(BpsSlippageModel(0.0008))

            atr = self.atr(sec.symbol, 14, MovingAverageType.WILDERS, Resolution.DAILY)
            sma = self.sma(sec.symbol, 50, Resolution.DAILY)
            self.states[sec.symbol] = SymbolState(sec.symbol, is_crypto=True, atr=atr, sma=sma)
            self.ticker_to_symbol[ticker] = sec.symbol

        self.positions = {}
        self.pending_entries = {}
        self.cooldown_until = {}
        self.entries_today = 0
        self.entries_day = None

        self.benchmark_symbol = self.ticker_to_symbol.get("SPY") or next(iter(self.states.keys()))
        self.set_benchmark(self.benchmark_symbol)
        self.set_warm_up(timedelta(days=140))

    def _symbol_has_pending_entry(self, symbol: Symbol) -> bool:
        return any(v["symbol"] == symbol for v in self.pending_entries.values())

    def _active_positions_count(self) -> int:
        return sum(1 for s in self.states if self.portfolio[s].invested)

    def _refresh_daily_entry_counter(self):
        day = self.time.date()
        if self.entries_day != day:
            self.entries_day = day
            self.entries_today = 0

    def _benchmark_vol_ok(self) -> bool:
        st = self.states.get(self.benchmark_symbol)
        if st is None or not st.atr.is_ready:
            return True
        px = st.raw_close
        if px <= 0:
            return True
        return (st.atr_value / px) <= self.max_benchmark_atr_pct

    def _update_stop_ticket(self, ticket: OrderTicket, quantity: float, stop_price: float, tag: str) -> bool:
        if ticket is None:
            return False
        fields = UpdateOrderFields()
        fields.quantity = -abs(quantity)
        fields.stop_price = stop_price
        fields.tag = tag
        r = ticket.update(fields)
        return r is not None and r.is_success

    def _regime_ok(self) -> bool:
        st = self.states.get(self.benchmark_symbol)
        if st is None:
            return True
        if not st.ready:
            return False

        px = st.raw_close
        w = st.avwap.weekly_value
        m = st.avwap.monthly_value
        sma = float(st.sma.current.value)

        if w is None or m is None:
            return False

        return px > w and w >= m and px > sma

    def _entry_signal(self, st: SymbolState) -> bool:
        if not st.ready:
            return False

        px = st.raw_close
        prev = st.raw_prev_close
        sma = float(st.sma.current.value)
        w = float(st.avwap.weekly_value)
        m = float(st.avwap.monthly_value)
        e = float(st.avwap.event_value) if st.avwap.event_value is not None else None

        if px <= 0 or w <= 0:
            return False

        slope = st.avwap.weekly_slope()
        dist_w = (px - w) / px
        not_overstretched = dist_w <= self.entry_gap_pct_max

        trend = px > w and w > m and px > sma and slope >= 0.0 and not_overstretched
        reclaim = (
            prev is not None
            and prev <= w
            and px > w
            and slope > -0.01
            and not_overstretched
        )
        event_ok = True if e is None else (px >= 0.997 * e)

        return (trend or reclaim) and event_ok

    def _compute_position_size(self, symbol: Symbol, st: SymbolState):
        price = st.raw_close
        if price <= 0:
            return 0, 0

        atr = st.atr_value
        stop_dist = max(self.atr_stop_mult * atr, price * self.min_stop_pct)
        if stop_dist <= 0:
            return 0, 0

        tpv = float(self.portfolio.total_portfolio_value)
        risk_budget = tpv * self.risk_per_trade

        qty_by_risk = risk_budget / stop_dist
        qty_by_weight = (tpv * self.max_position_weight) / price
        qty_by_cash = (float(self.portfolio.cash) * 0.95) / price

        raw_qty = min(qty_by_risk, qty_by_weight, qty_by_cash)

        lot = float(self.securities[symbol].symbol_properties.lot_size)
        lot = lot if lot > 0 else 1.0

        if st.is_crypto:
            qty = math.floor(raw_qty / lot) * lot
            if qty * price < 25.0:
                return 0, 0
        else:
            qty = int(math.floor(raw_qty))
            if qty < 1:
                return 0, 0

        return qty, stop_dist

    def _update_trailing_stop(self, symbol: Symbol, st: SymbolState):
        pos = self.positions.get(symbol)
        if not pos or pos.get("status") == "exit_pending":
            return

        px = st.raw_close
        pos["highest"] = max(pos["highest"], px)

        atr = st.atr_value
        trail_pct = max(self.min_trail_pct, (self.trail_atr_mult * atr / px) if px > 0 else self.min_trail_pct)
        candidate = pos["highest"] * (1.0 - trail_pct)

        one_r_trigger = pos["entry_price"] + pos["initial_stop_dist"]
        if px >= one_r_trigger:
            candidate = max(candidate, pos["entry_price"])

        new_stop = max(pos["stop_price"], candidate)
        if new_stop > pos["stop_price"] * 1.001 and pos.get("stop_ticket") is not None:
            if self._update_stop_ticket(pos["stop_ticket"], pos["quantity"], new_stop, f"trail|{self.time}"):
                pos["stop_price"] = new_stop

    def _apply_regime_exit(self, symbol: Symbol, st: SymbolState):
        if not self.portfolio[symbol].invested:
            return

        pos = self.positions.get(symbol)
        if not pos or pos.get("status") == "exit_pending":
            return

        px = st.raw_close
        w = st.avwap.weekly_value
        sma = float(st.sma.current.value) if st.sma.is_ready else None

        holding_days = max(0, (self.time.date() - pos.get("entry_time", self.time).date()).days)

        regime_broken = False
        if w is not None and px < float(w):
            regime_broken = True
        if sma is not None and px < sma:
            regime_broken = True

        # Let fresh entries breathe unless breakdown is severe.
        severe_break = (w is not None and px < 0.97 * float(w))
        if holding_days < self.min_hold_days and (not severe_break):
            regime_broken = False

        if not regime_broken:
            return

        pos["status"] = "exit_pending"
        if pos.get("stop_ticket") is not None:
            pos["stop_ticket"].cancel("regime-exit")
        self.liquidate(symbol, "regime-exit")

    def on_data(self, data: Slice):
        if self.is_warming_up:
            for symbol, st in self.states.items():
                if symbol in data.bars:
                    bar = data.bars[symbol]
                    st.raw_prev_close = st.raw_last_close
                    st.raw_last_close = float(bar.close)
                    st.avwap.update(bar)
            return

        self._refresh_daily_entry_counter()

        # Update states and open positions
        for symbol, st in self.states.items():
            if symbol not in data.bars:
                continue

            bar = data.bars[symbol]
            st.raw_prev_close = st.raw_last_close
            st.raw_last_close = float(bar.close)
            st.avwap.update(bar)

            if self.portfolio[symbol].invested and symbol in self.positions:
                self._update_trailing_stop(symbol, st)
                self._apply_regime_exit(symbol, st)

        if not self._regime_ok():
            return
        if not self._benchmark_vol_ok():
            return

        if self.weekly_entry_only and self.time.weekday() != 0:
            # New entries only at start of week to reduce churn.
            return

        if self.entries_today >= self.max_entries_per_day:
            return

        if self._active_positions_count() >= self.max_positions:
            return

        for symbol, st in self.states.items():
            if symbol not in data.bars:
                continue
            if self.portfolio[symbol].invested:
                continue
            if self._symbol_has_pending_entry(symbol):
                continue
            if self.time < self.cooldown_until.get(symbol, datetime.min):
                continue
            if self._active_positions_count() >= self.max_positions:
                break
            if not self._entry_signal(st):
                continue

            qty, stop_dist = self._compute_position_size(symbol, st)
            if qty <= 0:
                continue

            ticket = self.market_order(symbol, qty, tag="avwap-entry")
            if ticket is None:
                continue

            self.pending_entries[ticket.order_id] = {
                "symbol": symbol,
                "stop_dist": stop_dist,
                "filled_qty": 0.0,
                "filled_notional": 0.0,
                "submitted_time": self.time,
            }
            self.entries_today += 1

    def on_order_event(self, order_event: OrderEvent):
        if order_event.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
            return

        symbol = order_event.symbol
        fill_qty = float(order_event.fill_quantity)
        fill_price = float(order_event.fill_price)

        pending = self.pending_entries.get(order_event.order_id)
        if fill_qty > 0 and pending is not None:
            pending["filled_qty"] += fill_qty
            pending["filled_notional"] += fill_qty * fill_price

            cumulative_qty = float(pending["filled_qty"])
            if cumulative_qty <= 0:
                return

            avg_entry = float(pending["filled_notional"]) / cumulative_qty
            stop_dist = float(pending["stop_dist"])
            stop_price = max(0.01, avg_entry - stop_dist)

            pos = self.positions.get(symbol)
            if pos is None:
                stop_ticket = self.stop_market_order(symbol, -cumulative_qty, stop_price, tag="protective-stop")
                self.positions[symbol] = {
                    "entry_price": avg_entry,
                    "quantity": cumulative_qty,
                    "highest": fill_price,
                    "stop_price": stop_price,
                    "initial_stop_dist": stop_dist,
                    "entry_time": self.time,
                    "stop_ticket": stop_ticket,
                    "status": "entry_pending" if order_event.status == OrderStatus.PARTIALLY_FILLED else "active",
                    "entry_order_id": order_event.order_id,
                }
            else:
                pos["entry_price"] = avg_entry
                pos["quantity"] = cumulative_qty
                pos["highest"] = max(pos["highest"], fill_price)
                pos["initial_stop_dist"] = stop_dist
                pos["status"] = "entry_pending" if order_event.status == OrderStatus.PARTIALLY_FILLED else "active"

                if pos.get("stop_ticket") is None:
                    pos["stop_ticket"] = self.stop_market_order(symbol, -cumulative_qty, stop_price, tag="protective-stop")
                    pos["stop_price"] = stop_price
                elif self._update_stop_ticket(pos["stop_ticket"], cumulative_qty, stop_price, f"protective-stop-partial|{self.time}"):
                    pos["stop_price"] = stop_price

            if order_event.status == OrderStatus.FILLED:
                self.pending_entries.pop(order_event.order_id, None)
                p = self.positions.get(symbol)
                if p is not None:
                    p["status"] = "active"
            return

        if fill_qty < 0:
            pos = self.positions.get(symbol)
            if pos is not None:
                pos["status"] = "exit_pending"
                pos["quantity"] = max(0.0, float(self.portfolio[symbol].quantity))

            if abs(float(self.portfolio[symbol].quantity)) < 1e-9:
                pos = self.positions.pop(symbol, None)
                if pos and pos.get("stop_ticket") is not None:
                    pos["stop_ticket"].cancel("position-flat")
                self.cooldown_until[symbol] = self.time + timedelta(days=self.cooldown_days)

    def on_end_of_algorithm(self):
        tpv = float(self.portfolio.total_portfolio_value)
        self.log(
            f"END | TPV={tpv:.2f} | open_positions={self._active_positions_count()} | symbols={len(self.states)}"
        )
