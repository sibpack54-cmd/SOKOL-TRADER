"""
Telegram Bot v0.6 — python-telegram-bot v22.8
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import Config
from lab import TruthLab
from outcome_engine import OutcomeEngine
from tinkoff_client import TinkoffClient
from portfolio import Portfolio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SokolBot:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.lab = TruthLab(Config.DB_PATH)
        self.portfolio = Portfolio(Config.PORTFOLIO_PATH)
        self.app = Application.builder().token(self.token).build()
        self._register_handlers()

    def _check_whitelist(self, update: Update) -> bool:
        """Проверить, есть ли chat_id в whitelist"""
        if not Config.ALLOWED_CHAT_IDS:
            logger.warning("ALLOWED_CHAT_IDS не настроен, доступ запрещён всем")
            return False
        
        chat_id = update.effective_chat.id
        if chat_id not in Config.ALLOWED_CHAT_IDS:
            logger.warning(f"⛔ Доступ запрещён для chat_id={chat_id}")
            return False
        
        return True

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("radar", self.cmd_radar))
        self.app.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
        self.app.add_handler(CommandHandler("signals", self.cmd_signals))
        self.app.add_handler(CommandHandler("lab", self.cmd_lab))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        self.app.add_handler(CommandHandler("outcomes", self.cmd_outcomes))
        self.app.add_handler(CommandHandler("buy", self.cmd_buy))
        self.app.add_handler(CommandHandler("sell", self.cmd_sell))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("close", self.cmd_close))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        text = """
🦅 SOKOL-TRADER — ZIMA MARKET INTELLIGENCE

Я — твой советник. Не автопилот.
Помогаю видеть рынок яснее.

Доступные команды:
/radar — ТОП-5 возможностей
/portfolio — Мой портфель
/signals — Активные сигналы
/lab — Статистика Лаборатории
/settings — Настройки

«Мы не продаём робота. Мы продаём усиление мышления.»
"""
        await update.message.reply_text(text)

    async def cmd_radar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        text = await self._build_radar_text()

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_radar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup)

    async def _build_radar_text(self):
        """Построить текст радара"""
        text = "🦅 SOKOL RADAR\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # TODO: Загрузить реальные данные через tinkoff_client и indicators
        # Пока заглушка
        text += "SBER: 250.50₽ | ⚪ HOLD\n"
        text += "GAZP: 160.25₽ | ⚪ HOLD\n"
        text += "YNDX: 3800.00₽ | ⚪ HOLD\n"
        text += "LKOH: 6500.00₽ | ⚪ HOLD\n"
        text += "ROSN: 550.00₽ | ⚪ HOLD\n"

        text += f"\n━━━━━━━━━━━━━━━━━━━━\nОбновлено: {datetime.now().strftime('%H:%M')}"
        return text

    async def cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        positions = self.portfolio.get_active_positions()
        if not positions:
            text = """
📊 МОЙ ПОРТФЕЛЬ

Пока пусто.
Добавь позиции через сигналы или /buy.
"""
        else:
            lines = ["📊 МОЙ ПОРТФЕЛЬ", ""]
            for pos in positions:
                ticker = pos["ticker"]
                qty = pos["qty"]
                entry = pos["entry_price"]
                pnl_pct = pos.get("pnl_pct", 0)
                emoji = "📈" if pnl_pct >= 0 else "📉"
                lines.append(f"{emoji} {ticker} | {qty} шт | Вход: {entry:.2f}₽ | P&L: {pnl_pct:+.2f}%")
            text = "\n".join(lines)
        await update.message.reply_text(text)

    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        text = """
📈 АКТИВНЫЕ СИГНАЛЫ

Нет активных сигналов на сегодня.
"""
        await update.message.reply_text(text)

    async def cmd_lab(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        stats = self.lab.get_stats()
        text = f"""
🧪 ЛАБОРАТОРИЯ ИСТИНЫ

Всего сигналов: {stats.get('total', 0)}
✅ WIN: {stats.get('WIN', 0)} ({stats.get('win_rate', 0)}%)
❌ LOSS: {stats.get('LOSS', 0)} ({stats.get('loss_rate', 0)}%)
⚪ NEUTRAL: {stats.get('NEUTRAL', 0)}
"""
        await update.message.reply_text(text)

    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        text = """
⚙️ НАСТРОЙКИ

Настройки пока недоступны.
Скоро...
"""
        await update.message.reply_text(text)

    async def cmd_outcomes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/outcomes — статистика результатов"""
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        # Создать временный client для OutcomeEngine
        async with TinkoffClient() as client:
            engine = OutcomeEngine(lab=self.lab, client=client, threshold_pct=Config.OUTCOME_THRESHOLD_PCT)
            engine.init_outcomes_table()
            stats = engine.get_statistics()

        if stats['total_signals'] == 0:
            await update.message.reply_text("📊 Пока нет данных для анализа.")
            return

        lines = ["📊 <b>Статистика Outcomes</b>", f"Всего сигналов: {stats['total_signals']}"]

        for cp in [1, 3, 7, 30]:
            s = stats['by_checkpoint'].get(cp, {})
            lines.append(f"\n<b>{cp} дней:</b>")
            lines.append(f"🟢 WIN: {s.get('win', 0)} | 🔴 LOSS: {s.get('loss', 0)} | ⚪ NEUTRAL: {s.get('neutral', 0)}")
            lines.append(f"📈 Winrate: {s.get('winrate', 0):.1f}%")

        lines.append(f"\n<b>MFE/MAE:</b>")
        lines.append(f"↗️ Средний MFE: {stats['avg_mfe']:.2f}%")
        lines.append(f"↘️ Средний MAE: {stats['avg_mae']:.2f}%")

        await update.message.reply_html("\n".join(lines))

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if not self._check_whitelist(update):
            await query.edit_message_text("⛔ Доступ запрещён")
            return

        if query.data == "refresh_radar":
            text = await self._build_radar_text()
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_radar")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)

    async def cmd_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ручная покупка: /buy <ticker> <lots>"""
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Использование: /buy <ticker> <lots>")
            return

        ticker = context.args[0].upper()
        try:
            lots = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Количество лотов должно быть числом")
            return

        # Проверка: уже в позиции?
        if self.portfolio.get_position_by_ticker(ticker):
            await update.message.reply_text(f"⚠️ {ticker} уже в портфеле")
            return

        # Проверка: торговая сессия открыта
        from signal_engine import SignalEngine
        signal_engine = SignalEngine()
        if not signal_engine.is_market_open():
            await update.message.reply_text("⏸️ Рынок закрыт, покупка невозможна")
            return

        await update.message.reply_text("⏳ Обрабатываю покупку...")

        try:
            async with TinkoffClient() as client:
                # Получить текущую цену
                current_price = await client.get_current_price(ticker)
                if current_price == 0:
                    await update.message.reply_text(f"❌ Не удалось получить цену для {ticker}")
                    return

                # TODO: выполнить реальный ордер через T-Invest API
                # order_response = await client.post_order(ticker, lots, "BUY", current_price)

                # Временное решение: добавить в портфель без реального ордера
                from datetime import datetime
                signal_id = f"manual_{ticker}_{datetime.now().isoformat()}"
                stop_loss = current_price * 0.98
                take_profit_1 = current_price * 1.02
                take_profit_2 = current_price * 1.04

                self.portfolio.add_position(
                    ticker=ticker,
                    qty=lots,
                    price=current_price,
                    signal_id=signal_id,
                    stop=stop_loss,
                    tp1=take_profit_1,
                    tp2=take_profit_2
                )

                text = f"""
✅ Куплено {ticker}
━━━━━━━━━━━━━━━━━━━━
� Количество: {lots} лотов
💰 Цена: {current_price:.2f} ₽
🛡️ Стоп: {stop_loss:.2f} ₽
🎯 TP1: {take_profit_1:.2f} ₽
🎯 TP2: {take_profit_2:.2f} ₽

⚠️ ВНИМАНИЕ: Позиция добавлена локально. Реальный ордер не исполнен (требуется интеграция с T-Invest OrdersService).
"""
                await update.message.reply_text(text)
                logger.info(f"✅ Ручная покупка {ticker}: {lots} лотов по {current_price:.2f}₽")

        except Exception as e:
            logger.error(f"❌ Ошибка покупки {ticker}: {e}")
            await update.message.reply_text(f"❌ Ошибка покупки: {e}")

    async def cmd_sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ручная продажа: /sell <ticker>"""
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return

        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Использование: /sell <ticker>")
            return

        ticker = context.args[0].upper()

        # Проверка: есть ли позиция?
        pos = self.portfolio.get_position_by_ticker(ticker)
        if not pos:
            await update.message.reply_text(f"⚠️ {ticker} не в портфеле")
            return

        await update.message.reply_text("⏳ Обрабатываю продажу...")

        try:
            async with TinkoffClient() as client:
                # Получить текущую цену
                current_price = await client.get_current_price(ticker)
                if current_price == 0:
                    await update.message.reply_text(f"❌ Не удалось получить цену для {ticker}")
                    return

                # TODO: выполнить реальный ордер через T-Invest API
                # order_response = await client.post_order(ticker, pos["qty"], "SELL", current_price)

                # Временное решение: закрыть позицию локально
                pnl = self.portfolio.close_position(ticker, current_price)
                if pnl is None:
                    await update.message.reply_text(f"❌ Не удалось закрыть позицию {ticker}")
                    return

                pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
                emoji = "�" if pnl >= 0 else "📉"

                text = f"""
✅ Продано {ticker}
━━━━━━━━━━━━━━━━━━━━
📦 Количество: {pos["qty"]} лотов
💰 Цена продажи: {current_price:.2f} ₽
💰 Цена входа: {pos["entry_price"]:.2f} ₽
{emoji} P&L: {pnl:+.2f} ₽ ({pnl_pct:+.2f}%)

⚠️ ВНИМАНИЕ: Позиция закрыта локально. Реальный ордер не исполнен (требуется интеграция с T-Invest OrdersService).
"""
                await update.message.reply_text(text)
                logger.info(f"✅ Ручная продажа {ticker}: {pos['qty']} лотов по {current_price:.2f}₽, P&L: {pnl:+.2f}₽")

        except Exception as e:
            logger.error(f"❌ Ошибка продажи {ticker}: {e}")
            await update.message.reply_text(f"❌ Ошибка продажи: {e}")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус позиций с P&L"""
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return

        await self.cmd_portfolio(update, context)

    async def cmd_close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Закрыть позицию по рынку: /close <ticker>"""
        if not self._check_whitelist(update):
            await update.message.reply_text("⛔ Доступ запрещён")
            return

        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Использование: /close <ticker>")
            return

        ticker = context.args[0].upper()

        # Проверка: есть ли позиция?
        pos = self.portfolio.get_position_by_ticker(ticker)
        if not pos:
            await update.message.reply_text(f"⚠️ {ticker} не в портфеле")
            return

        await update.message.reply_text("⏳ Закрываю позицию по рынку...")

        try:
            async with TinkoffClient() as client:
                # Получить текущую цену
                current_price = await client.get_current_price(ticker)
                if current_price == 0:
                    await update.message.reply_text(f"❌ Не удалось получить цену для {ticker}")
                    return

                # TODO: выполнить рыночный ордер через T-Invest API
                # order_response = await client.post_order(ticker, pos["qty"], "SELL", current_price, order_type="MARKET")

                # Временное решение: закрыть позицию локально
                pnl = self.portfolio.close_position(ticker, current_price)
                if pnl is None:
                    await update.message.reply_text(f"❌ Не удалось закрыть позицию {ticker}")
                    return

                pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
                emoji = "📈" if pnl >= 0 else "📉"

                text = f"""
✅ Закрыта позиция {ticker}
━━━━━━━━━━━━━━━━━━━━
📦 Количество: {pos["qty"]} лотов
💰 Цена закрытия: {current_price:.2f} ₽ (рынок)
💰 Цена входа: {pos["entry_price"]:.2f} ₽
{emoji} P&L: {pnl:+.2f} ₽ ({pnl_pct:+.2f}%)

⚠️ ВНИМАНИЕ: Позиция закрыта локально. Реальный рыночный ордер не исполнен (требуется интеграция с T-Invest OrdersService).
"""
                await update.message.reply_text(text)
                logger.info(f"✅ Закрытие {ticker} по рынку: {pos['qty']} лотов по {current_price:.2f}₽, P&L: {pnl:+.2f}₽")

        except Exception as e:
            logger.error(f"❌ Ошибка закрытия {ticker}: {e}")
            await update.message.reply_text(f"❌ Ошибка закрытия: {e}")

    async def send_sl_tp_alert(self, ticker: str, alert_type: str, current_price: float, position: Dict):
        """Отправить уведомление о срабатывании SL/TP"""
        entry_price = position["entry_price"]
        stop_loss = position["stop_loss"]
        take_profit_1 = position["take_profit_1"]
        take_profit_2 = position["take_profit_2"]
        qty = position["qty"]

        pnl = (current_price - entry_price) * qty
        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        if alert_type == "SL":
            emoji = "🚨"
            title = f"СТОП-ЛОСС"
            trigger_price = stop_loss
        elif alert_type == "TP1":
            emoji = "🎯"
            title = f"ТЕЙК-ПРОФИТ 1"
            trigger_price = take_profit_1
        elif alert_type == "TP2":
            emoji = "🎯"
            title = f"ТЕЙК-ПРОФИТ 2"
            trigger_price = take_profit_2
        else:
            return

        text = f"""
{emoji} {ticker} — {title}
━━━━━━━━━━━━━━━━━━━━
💰 Текущая цена: {current_price:.2f} ₽
🎯 Триггер: {trigger_price:.2f} ₽
📊 P&L: {pnl:+.2f} ₽ ({pnl_pct:+.2f}%)
📦 Количество: {qty} шт
"""

        keyboard = [
            [InlineKeyboardButton("🔴 Продать", callback_data=f"sell_{ticker}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.app.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=text,
            reply_markup=reply_markup
        )
        logger.info(f"📨 Отправлено уведомление {alert_type} для {ticker}")

    async def send_signal(self, signal):
        """Отправить сигнал в Telegram с кнопками"""
        signal_type_rus = "ПОКУПКА" if signal.signal_type == "BUY" else "ПРОДАЖА"
        
        text = f"""
🦅 SOKOL-TRADER | {signal_type_rus} | {signal.ticker}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 {signal.rating} | ZSS: {signal.zss_score} | Уверенность: {signal.confidence:.0f}%
💰 Вход: {signal.entry_price:.2f} ₽
🛡️ Стоп: {signal.stop_loss:.2f} ₽ ({((signal.stop_loss/signal.entry_price)-1)*100:.1f}%)
🎯 TP1: {signal.take_profit_1:.2f} ₽ (+{((signal.take_profit_1/signal.entry_price)-1)*100:.1f}%)
🎯 TP2: {signal.take_profit_2:.2f} ₽ (+{((signal.take_profit_2/signal.entry_price)-1)*100:.1f}%)
⚖️ Размер: 8% капитала
📈 R/R: 3.2:1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🦅 Рекомендует. Человек решает.
"""

        keyboard = [
            [InlineKeyboardButton("📥 Я КУПИЛ", callback_data=f"buy_{signal.signal_id}")],
            [InlineKeyboardButton("📊 Подробнее", callback_data=f"details_{signal.signal_id}")],
            [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"skip_{signal.signal_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.app.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=text,
            reply_markup=reply_markup
        )

    async def send_signal_details(self, signal):
        """Отправить детали сигнала (Confidence Decomposition)"""
        text = f"""
📊 ПОДРОБНЕЕ | {signal.ticker}

ZSS: {signal.zss_score}
RSI: {signal.rsi:.1f} | MACD: {signal.macd} | OBV: {signal.obv}
ADX: {signal.adx:.1f} | VWAP: {signal.vwap_diff:.2f}% | Объем: x{signal.volume_ratio:.1f}
Сектор: {signal.sector_trend} | IMOEX: {signal.imoex_trend}
Уровень: {signal.level_age_days} дней

Confidence Decomposition:
Уровень ........................... {signal.weight_rsi:.1f}%
Объем ............................. {signal.weight_obv:.1f}%
Тренд ............................. {signal.weight_adx:.1f}%
Retest ............................ {signal.weight_vwap:.1f}%
Дивергенция ....................... {signal.weight_stochastic:.1f}%
"""

        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=f"back_{signal.signal_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.app.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=text,
            reply_markup=reply_markup
        )

    def run(self):
        logger.info("🦅 SOKOL-TRADER запущен")
        self.app.run_polling()
