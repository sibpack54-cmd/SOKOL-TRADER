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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SokolBot:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.lab = TruthLab(Config.DB_PATH)
        self.app = Application.builder().token(self.token).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("radar", self.cmd_radar))
        self.app.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
        self.app.add_handler(CommandHandler("signals", self.cmd_signals))
        self.app.add_handler(CommandHandler("lab", self.cmd_lab))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        self.app.add_handler(CommandHandler("outcomes", self.cmd_outcomes))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = """
📊 МОЙ ПОРТФЕЛЬ

Пока пусто.
Добавь позиции через сигналы.
"""
        await update.message.reply_text(text)

    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
📈 АКТИВНЫЕ СИГНАЛЫ

Нет активных сигналов на сегодня.
"""
        await update.message.reply_text(text)

    async def cmd_lab(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = """
⚙️ НАСТРОЙКИ

Настройки пока недоступны.
Скоро...
"""
        await update.message.reply_text(text)

    async def cmd_outcomes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/outcomes — статистика результатов"""
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

        if query.data == "refresh_radar":
            text = await self._build_radar_text()
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_radar")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)

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
