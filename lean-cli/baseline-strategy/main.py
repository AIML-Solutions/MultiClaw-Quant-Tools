# region imports
from AlgorithmImports import *
from datetime import timedelta
import math
# endregion


class ProportionalFeeModel(FeeModel):
    """Simple percent-of-notional fee model with optional minimum fee."""

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
    """Percent slippage model: slippage = price * bps."""

    def __init__(self, bps: float):
        self._bps = float(bps)

    def get_slippage_approximation(self, asset, order):
        return float(asset.price) * self._bps


class SimpleSuperTrend:
    """Compact SuperTrend implementation driven by TradeBar updates."""

    def __init__(self, period: int, multiplier: float):
        self.multiplier = float(multiplier)
        self.atr = AverageTrueRange(period, MovingAverageType.WILDERS)
        self.final_upper = None
        self.final_lower = None
        self.prev_close = None
        self.value = None

    @property
    def is_ready(self) -> bool:
        return self.atr.is_ready and self.value is not None

    def update(self, bar: TradeBar):
        self.atr.update(bar)
        close = float(bar.close)

        if not self.atr.is_ready:
            self.prev_close = close
            return

        atr = float(self.atr.current.value)
        hl2 = (float(bar.high) + float(bar.low)) / 2.0
        basic_upper = hl2 + self.multiplier * atr
        basic_lower = hl2 - self.multiplier * atr

        if self.final_upper is None:
            self.final_upper = basic_upper
            self.final_lower = basic_lower
            self.value = basic_lower
            self.prev_close = close
            return

        prev_close = self.prev_close if self.prev_close is not None else close
        self.final_upper = basic_upper if (basic_upper < self.final_upper or prev_close > self.final_upper) else self.final_upper
        self.final_lower = basic_lower if (basic_lower > self.final_lower or prev_close < self.final_lower) else self.final_lower

        prev_st = self.value
        if prev_st == self.final_upper:
            self.value = self.final_lower if close > self.final_upper else self.final_upper
        else:
            self.value = self.final_upper if close < self.final_lower else self.final_lower

        self.prev_close = close


class SymbolState:
    def __init__(self, symbol: Symbol, is_crypto: bool):
        self.symbol = symbol
        self.is_crypto = is_crypto

        self.ema_fast = ExponentialMovingAverage(50)
        self.ema_slow = ExponentialMovingAverage(200)
        self.rsi = RelativeStrengthIndex(14, MovingAverageType.WILDERS)
        self.atr = AverageTrueRange(14, MovingAverageType.WILDERS)

        self.st_fast = SimpleSuperTrend(10, 2.0)
        self.st_slow = SimpleSuperTrend(20, 3.0)

        # True calendar-week filter (close of completed ISO weeks) on indicator stream.
        self.weekly_sma = SimpleMovingAverage(25)
        self.current_week = None
        self.last_week_close = None

        self.last_close = None
        self.prev_close = None
        self.raw_last_close = None
        self.raw_prev_close = None
        self.price_scale = 1.0

        self.prev_fast_st = None
        self.prev_slow_st = None
        self.last_update = None

    @property
    def ready(self) -> bool:
        return (
            self.ema_slow.is_ready
            and self.rsi.is_ready
            and self.atr.is_ready
            and self.st_fast.is_ready
            and self.st_slow.is_ready
            and self.weekly_sma.is_ready
        )

    @property
    def close(self) -> float:
        return float(self.last_close or 0.0)

    @property
    def raw_close(self) -> float:
        if self.raw_last_close is not None:
            return float(self.raw_last_close)
        return float(self.last_close or 0.0)

    @property
    def atr_value(self) -> float:
        return float(self.atr.current.value) if self.atr.is_ready else 0.0

    @property
    def raw_atr_value(self) -> float:
        if not self.atr.is_ready:
            return 0.0
        scale = self.price_scale if self.price_scale > 0 else 1.0
        return float(self.atr.current.value) / scale

    @property
    def ema_fast_value(self) -> float:
        return float(self.ema_fast.current.value)

    @property
    def ema_slow_value(self) -> float:
        return float(self.ema_slow.current.value)

    @property
    def rsi_value(self) -> float:
        return float(self.rsi.current.value)

    def update_raw_only(self, raw_bar: TradeBar):
        self.raw_prev_close = self.raw_last_close
        self.raw_last_close = float(raw_bar.close)
        self.last_update = raw_bar.end_time

    def update(self, raw_bar: TradeBar, indicator_bar: TradeBar = None):
        signal_bar = indicator_bar if indicator_bar is not None else raw_bar
        signal_close = float(signal_bar.close)
        raw_close = float(raw_bar.close)
        end_time = signal_bar.end_time

        self.update_raw_only(raw_bar)

        self.prev_close = self.last_close
        self.prev_fast_st = self.st_fast.value
        self.prev_slow_st = self.st_slow.value

        self.ema_fast.update(end_time, signal_close)
        self.ema_slow.update(end_time, signal_close)
        self.rsi.update(end_time, signal_close)
        self.atr.update(signal_bar)
        self.st_fast.update(signal_bar)
        self.st_slow.update(signal_bar)

        scale = signal_close / raw_close if raw_close > 0 else 1.0
        if scale > 0:
            self.price_scale = scale

        # True calendar-week update: push previous week's close when week changes.
        iso = end_time.isocalendar()
        week_key = (iso.year, iso.week)
        if self.current_week is None:
            self.current_week = week_key
        elif week_key != self.current_week and self.last_week_close is not None:
            self.weekly_sma.update(end_time, self.last_week_close)
            self.current_week = week_key

        self.last_week_close = signal_close
        self.last_close = signal_close
        self.last_update = end_time


class EnhancedMultiAssetSuperTrend(QCAlgorithm):
    """
    Upgraded mixed-asset trend strategy with:
    - realistic non-zero fees/slippage by asset class
    - fractional crypto sizing (lot-size aware)
    - true calendar-week trend filter
    - portfolio-level exposure caps
    - trailing stop on high-water mark (never widens)

    Equity execution stays on RAW bars for realistic fills.
    Equity indicator warmup and live maintenance use a separate SCALED_RAW stream so
    splits/dividends do not corrupt EMA/ATR/SuperTrend/weekly regime state.
    """

    def initialize(self):
        self.set_start_date(int(self.get_parameter("start_year") or 2019), 1, 1)
        self.set_end_date(int(self.get_parameter("end_year") or 2025), 12, 31)
        self.set_cash(float(self.get_parameter("initial_cash") or 100000))

        # Strategy parameters (parameterized for sensitivity sweeps).
        self.risk_per_trade = float(self.get_parameter("risk_per_trade") or 0.004)  # 0.40%
        self.max_positions = int(self.get_parameter("max_positions") or 6)
        self.cooldown_days = int(self.get_parameter("cooldown_days") or 3)
        self.max_gross_exposure = float(self.get_parameter("max_gross_exposure") or 0.90)
        self.max_crypto_exposure = float(self.get_parameter("max_crypto_exposure") or 0.35)
        self.max_equity_exposure = float(self.get_parameter("max_equity_exposure") or 0.85)
        self.max_position_notional = float(self.get_parameter("max_position_notional") or 0.18)

        self.atr_stop_mult = float(self.get_parameter("atr_stop_mult") or 3.0)
        self.atr_trail_mult = float(self.get_parameter("atr_trail_mult") or 2.2)
        self.min_stop_pct = float(self.get_parameter("min_stop_pct") or 0.015)
        self.min_trail_pct = float(self.get_parameter("min_trail_pct") or 0.02)
        self.rsi_entry_floor = float(self.get_parameter("rsi_entry_floor") or 48)
        self.rsi_entry_ceiling = float(self.get_parameter("rsi_entry_ceiling") or 78)
        self.risk_on_multiplier = float(self.get_parameter("risk_on_multiplier") or 1.10)
        self.risk_off_multiplier = float(self.get_parameter("risk_off_multiplier") or 0.60)

        self.equity_indicator_mode = DataNormalizationMode.SCALED_RAW

        self.symbol_states = {}
        self.ticker_to_symbol = {}
        self.positions = {}
        self.pending_entries = {}
        self.cooldown_until = {}

        # Defaults aligned to locally-available sample data to avoid silent zero-trade runs.
        default_equities = ["SPY", "QQQ", "IWM", "EEM", "AAPL", "BAC", "IBM"]
        default_cryptos = []

        eq_raw = (self.get_parameter("equity_tickers") or ",".join(default_equities)).strip()
        cr_raw = (self.get_parameter("crypto_tickers") or ",".join(default_cryptos)).strip()
        extra_eq = (self.get_parameter("extra_equity_tickers") or "").strip()
        include_vix = str(self.get_parameter("include_vix_proxy") or "false").strip().lower() in ("1", "true", "yes", "y")

        equity_tickers = [t.strip().upper() for t in eq_raw.split(",") if t.strip()]
        crypto_tickers = [t.strip().upper() for t in cr_raw.split(",") if t.strip()]
        if extra_eq:
            equity_tickers.extend([t.strip().upper() for t in extra_eq.split(",") if t.strip()])
        if include_vix:
            equity_tickers.append("VIXY")

        # dedupe while preserving order
        equity_tickers = list(dict.fromkeys(equity_tickers))
        crypto_tickers = list(dict.fromkeys(crypto_tickers))

        for ticker in equity_tickers:
            sec = self.add_equity(ticker, Resolution.DAILY, fill_forward=True)
            sec.set_data_normalization_mode(DataNormalizationMode.RAW)
            sec.set_fee_model(ProportionalFeeModel(rate=0.00005, min_fee=0.35))  # ~0.5 bps
            sec.set_slippage_model(BpsSlippageModel(0.0002))  # 2 bps
            self.symbol_states[sec.symbol] = SymbolState(sec.symbol, is_crypto=False)
            self.ticker_to_symbol[ticker] = sec.symbol

        for ticker in crypto_tickers:
            sec = self.add_crypto(ticker, Resolution.DAILY, Market.COINBASE, fill_forward=True)
            sec.set_fee_model(ProportionalFeeModel(rate=0.0006, min_fee=0.0))  # 6 bps
            sec.set_slippage_model(BpsSlippageModel(0.0008))  # 8 bps
            self.symbol_states[sec.symbol] = SymbolState(sec.symbol, is_crypto=True)
            self.ticker_to_symbol[ticker] = sec.symbol

        self._warm_up_all_symbols(history_days=420)

    def _history_tradebars(self, symbol: Symbol, periods: int, data_normalization_mode=None):
        if data_normalization_mode is None:
            return list(self.history[TradeBar](symbol, periods, Resolution.DAILY))
        return list(
            self.history[TradeBar](
                symbol,
                periods,
                Resolution.DAILY,
                data_normalization_mode=data_normalization_mode,
            )
        )

    def _get_indicator_bar(self, symbol: Symbol, raw_bar: TradeBar, state: SymbolState):
        if state.is_crypto:
            return None

        start = raw_bar.end_time - timedelta(days=10)
        bars = list(
            self.history[TradeBar](
                symbol,
                start,
                raw_bar.end_time,
                Resolution.DAILY,
                data_normalization_mode=self.equity_indicator_mode,
            )
        )
        if len(bars) == 0:
            return None
        return bars[-1]

    def _warm_up_all_symbols(self, history_days: int):
        for symbol, state in self.symbol_states.items():
            if state.is_crypto:
                history = self._history_tradebars(symbol, history_days)
            else:
                history = self._history_tradebars(symbol, history_days, self.equity_indicator_mode)

            if len(history) == 0:
                self.debug(f"Warmup: no history for {symbol}")
                continue

            count = 0
            for bar in history:
                state.update(bar, bar)
                count += 1

            self.debug(
                f"Warmup: {symbol} bars={count} ready={state.ready} weekly_samples={state.weekly_sma.samples}"
            )

    def _symbol_has_pending_entry(self, symbol: Symbol) -> bool:
        return any(pending["symbol"] == symbol for pending in self.pending_entries.values())

    def on_data(self, data: Slice):
        # 1) Update indicators and maintain open positions.
        for symbol, state in self.symbol_states.items():
            if symbol not in data.bars:
                continue

            raw_bar = data.bars[symbol]
            indicator_bar = raw_bar
            if not state.is_crypto:
                indicator_bar = self._get_indicator_bar(symbol, raw_bar, state)
                if indicator_bar is None:
                    state.update_raw_only(raw_bar)
                    self.debug(f"Indicator update skipped for {symbol}: no SCALED_RAW bar available")
                    if self.portfolio[symbol].invested and symbol in self.positions:
                        self._update_trailing_stop(symbol, state)
                    continue

            state.update(raw_bar, indicator_bar)

            if self.portfolio[symbol].invested and symbol in self.positions:
                self._update_trailing_stop(symbol, state)
                self._apply_regime_exit(symbol, state)

        # 2) Evaluate new entries.
        if self._active_positions_count() >= self.max_positions:
            return

        for symbol, state in self.symbol_states.items():
            if symbol not in data.bars:
                continue
            if not state.ready:
                continue
            if self.portfolio[symbol].invested:
                continue
            if self._symbol_has_pending_entry(symbol):
                continue
            if self.time < self.cooldown_until.get(symbol, datetime.min):
                continue
            if self._active_positions_count() >= self.max_positions:
                break

            if not self._entry_signal(state):
                continue

            qty, stop_dist = self._compute_position_size(symbol, state)
            if qty <= 0:
                continue

            ticket = self.market_order(symbol, qty, tag="entry")
            if ticket is None:
                continue

            self.pending_entries[ticket.order_id] = {
                "symbol": symbol,
                "stop_dist": stop_dist,
                "submitted_time": self.time,
                "filled_qty": 0.0,
                "filled_notional": 0.0,
            }

    def _entry_signal(self, state: SymbolState) -> bool:
        close = state.close
        fast_st = float(state.st_fast.value)
        slow_st = float(state.st_slow.value)

        crossed_up_fast = (
            state.prev_close is not None
            and state.prev_fast_st is not None
            and float(state.prev_close) <= float(state.prev_fast_st)
            and close > fast_st
        )

        regime_ok = close > slow_st and close > state.ema_fast_value and state.ema_fast_value > state.ema_slow_value
        momentum_ok = self.rsi_entry_floor <= state.rsi_value <= self.rsi_entry_ceiling
        weekly_ok = state.weekly_sma.is_ready and close > float(state.weekly_sma.current.value)

        # Avoid extremely low-volatility drift entries.
        atr_frac = state.atr_value / close if close > 0 else 0
        vol_ok = 0.005 <= atr_frac <= 0.22

        return crossed_up_fast and regime_ok and momentum_ok and weekly_ok and vol_ok

    def _active_positions_count(self) -> int:
        return sum(1 for s in self.symbol_states if self.portfolio[s].invested)

    def _gross_exposure(self) -> float:
        return sum(abs(float(self.portfolio[s].holdings_value)) for s in self.symbol_states)

    def _asset_class_exposure(self, is_crypto: bool) -> float:
        return sum(
            abs(float(self.portfolio[s].holdings_value))
            for s, st in self.symbol_states.items()
            if st.is_crypto == is_crypto
        )

    def _market_risk_scale(self) -> float:
        scale = 1.0

        spy = self.ticker_to_symbol.get("SPY")
        if spy is not None and spy in self.symbol_states:
            st = self.symbol_states[spy]
            if st.ready:
                risk_on = st.close > st.ema_slow_value and st.ema_fast_value > st.ema_slow_value
                scale *= self.risk_on_multiplier if risk_on else self.risk_off_multiplier

        # Optional volatility proxy haircut if VIXY is present and elevated.
        vixy = self.ticker_to_symbol.get("VIXY")
        if vixy is not None and vixy in self.symbol_states:
            vst = self.symbol_states[vixy]
            if vst.ready and vst.close > vst.ema_fast_value:
                scale *= 0.80

        return max(0.35, min(1.30, scale))

    def _compute_position_size(self, symbol: Symbol, state: SymbolState):
        price = state.raw_close
        signal_price = state.close
        if price <= 0 or signal_price <= 0:
            return 0, 0

        tpv = float(self.portfolio.total_portfolio_value)
        gross_now = self._gross_exposure()
        gross_room = max(0.0, tpv * self.max_gross_exposure - gross_now)
        if gross_room <= 0:
            return 0, 0

        if state.is_crypto:
            class_room = max(0.0, tpv * self.max_crypto_exposure - self._asset_class_exposure(True))
        else:
            class_room = max(0.0, tpv * self.max_equity_exposure - self._asset_class_exposure(False))

        if class_room <= 0:
            return 0, 0

        stop_dist = max(self.atr_stop_mult * state.raw_atr_value, price * self.min_stop_pct)
        if stop_dist <= 0:
            return 0, 0

        risk_budget = tpv * self.risk_per_trade * self._market_risk_scale()
        qty_by_risk = risk_budget / stop_dist

        notional_cap = tpv * self.max_position_notional
        qty_by_notional = notional_cap / price

        qty_by_gross = gross_room / price
        qty_by_class = class_room / price

        # Keep cash buffer; margin_remaining can be > cash for equities.
        qty_by_bp = max(0.0, float(self.portfolio.margin_remaining) * 0.95 / price)

        raw_qty = min(qty_by_risk, qty_by_notional, qty_by_gross, qty_by_class, qty_by_bp)

        lot_size = float(self.securities[symbol].symbol_properties.lot_size)
        lot_size = lot_size if lot_size > 0 else 1.0

        if state.is_crypto:
            qty = math.floor(raw_qty / lot_size) * lot_size
            min_notional = 25.0
            if qty * price < min_notional:
                return 0, 0
        else:
            qty = int(math.floor(raw_qty))
            if qty < 1:
                return 0, 0

        return qty, stop_dist

    def _update_stop_ticket(self, ticket: OrderTicket, quantity: float, stop_price: float, tag: str) -> bool:
        if ticket is None:
            return False

        fields = UpdateOrderFields()
        fields.quantity = -abs(quantity)
        fields.stop_price = stop_price
        fields.tag = tag
        response = ticket.update(fields)
        return response is not None and response.is_success

    def _update_trailing_stop(self, symbol: Symbol, state: SymbolState):
        pos = self.positions.get(symbol)
        if not pos or pos.get("status") == "exit_pending":
            return

        close = state.raw_close
        pos["highest"] = max(pos["highest"], close)

        atr = state.atr_value
        signal_close = state.close
        trail_pct = max(
            self.min_trail_pct,
            (self.atr_trail_mult * atr / signal_close) if signal_close > 0 else self.min_trail_pct,
        )
        candidate = pos["highest"] * (1.0 - trail_pct)

        # Never widen stop; include break-even floor after ~1R move.
        one_r_trigger = pos["entry_price"] + pos["initial_stop_dist"]
        if close >= one_r_trigger:
            candidate = max(candidate, pos["entry_price"])

        new_stop = max(pos["stop_price"], candidate)

        if new_stop > pos["stop_price"] * 1.001 and pos.get("stop_ticket") is not None:
            if self._update_stop_ticket(pos["stop_ticket"], pos["quantity"], new_stop, f"trail|{self.time}"):
                pos["stop_price"] = new_stop

    def _apply_regime_exit(self, symbol: Symbol, state: SymbolState):
        if not self.portfolio[symbol].invested:
            return

        pos = self.positions.get(symbol)
        if not pos or pos.get("status") == "exit_pending":
            return

        close = state.close
        slow_st = float(state.st_slow.value)

        regime_broken = close < slow_st or close < state.ema_fast_value or state.rsi_value < 45
        if not regime_broken:
            return

        pos["status"] = "exit_pending"

        if pos.get("stop_ticket") is not None:
            pos["stop_ticket"].cancel("manual-regime-exit")

        self.liquidate(symbol, "regime-exit")

    def on_order_event(self, order_event: OrderEvent):
        if order_event.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
            return

        symbol = order_event.symbol
        fill_qty = float(order_event.fill_quantity)
        fill_price = float(order_event.fill_price)

        # Entry fill -> protect immediately and resize the protective stop with UpdateOrderFields on later partial fills.
        pending = self.pending_entries.get(order_event.order_id)
        if fill_qty > 0 and pending is not None:
            pending["filled_qty"] += fill_qty
            pending["filled_notional"] += fill_qty * fill_price

            cumulative_qty = float(pending["filled_qty"])
            if cumulative_qty <= 0:
                return

            avg_entry_price = float(pending["filled_notional"]) / cumulative_qty
            stop_dist = float(pending["stop_dist"])
            stop_price = max(0.01, avg_entry_price - stop_dist)

            pos = self.positions.get(symbol)
            if pos is None:
                stop_ticket = self.stop_market_order(symbol, -cumulative_qty, stop_price, tag="protective-stop")
                self.positions[symbol] = {
                    "entry_price": avg_entry_price,
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
                pos["entry_price"] = avg_entry_price
                pos["quantity"] = cumulative_qty
                pos["highest"] = max(pos["highest"], fill_price)
                pos["initial_stop_dist"] = stop_dist
                pos["status"] = "entry_pending" if order_event.status == OrderStatus.PARTIALLY_FILLED else "active"

                if pos.get("stop_ticket") is None:
                    pos["stop_ticket"] = self.stop_market_order(symbol, -cumulative_qty, stop_price, tag="protective-stop")
                    pos["stop_price"] = stop_price
                elif self._update_stop_ticket(
                    pos["stop_ticket"],
                    cumulative_qty,
                    stop_price,
                    f"protective-stop-partial|{self.time}",
                ):
                    pos["stop_price"] = stop_price

            if order_event.status == OrderStatus.FILLED:
                pending = self.pending_entries.pop(order_event.order_id, None)
                pos = self.positions.get(symbol)
                if pos is not None:
                    pos["status"] = "active"
            return

        # Exit fill -> mark exit flow and clear state + cooldown once flat.
        if fill_qty < 0:
            pos = self.positions.get(symbol)
            if pos is not None:
                pos["status"] = "exit_pending"
                pos["quantity"] = max(0.0, float(self.portfolio[symbol].quantity))

            holding_qty = float(self.portfolio[symbol].quantity)
            if abs(holding_qty) < 1e-9:
                pos = self.positions.pop(symbol, None)
                if pos and pos.get("stop_ticket") is not None:
                    pos["stop_ticket"].cancel("position-flat")
                self.cooldown_until[symbol] = self.time + timedelta(days=self.cooldown_days)

    def on_end_of_algorithm(self):
        gross = self._gross_exposure()
        tpv = float(self.portfolio.total_portfolio_value)
        self.log(
            f"END | TPV={tpv:.2f} | gross={gross:.2f} | gross_pct={(gross / tpv * 100.0 if tpv > 0 else 0):.2f}% | "
            f"open_positions={self._active_positions_count()}"
        )
