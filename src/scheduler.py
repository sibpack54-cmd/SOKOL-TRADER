"""
Планировщик сканирования — AsyncIOScheduler
SOKOL-TRADER v0.6.2
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

import telegram
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from tinkoff_client import TinkoffClient
from indicators import get_indicators
from signal_engine import SignalEngine
from telegram_bot import SokolBot
from lab import TruthLab
from outcome_engine import OutcomeEngine

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sokol.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def scan_market(
    bot: SokolBot,
    tinkoff: TinkoffClient,
    signal_engine: SignalEngine,
    lab: TruthLab
) -> None:
    """Сканировать рынок и генерировать сигналы."""
    if not signal_engine.is_market_open():
        logger.info("⏸️ Рынок закрыт: %s MSK", datetime.now().strftime('%H:%M'))
        return

    logger.info("🔍 Сканирование рынка: %s MSK", datetime.now().strftime('%H:%M'))

    signals_found = 0
    errors = 0

    for ticker in Config.TICKERS:
        try:
            df = await tinkoff.get_candles(ticker, interval=Config.TIMEFRAME, days=7)

            if df is None or df.empty:
                logger.warning("⚠️ Нет данных для %s", ticker)
                continue

            indicators = get_indicators(df)
            if not indicators:
                logger.warning("⚠️ Нет индикаторов для %s", ticker)
                continue

            current_price = indicators.get("close", 0)
            signal = signal_engine.generate_signal(indicators, ticker, current_price)

            if signal:
                signal_id = lab.record_signal(signal)
                logger.info(
                    "✅ СИГНАЛ %s | %s | ZSS=%.2f | Confidence=%.1f%%",
                    signal.signal_type, ticker, signal.zss_score, signal.confidence_pct
                )
                await bot.send_signal(signal)
                signals_found += 1
            else:
                logger.debug("⚪ Нет сигнала для %s", ticker)

        except asyncio.TimeoutError:
            logger.error("❌ Таймаут %s", ticker)
            errors += 1
        except Exception as e:
            logger.error("❌ Ошибка %s: %s", ticker, e)
            errors += 1

    logger.info("📊 Сканирование завершено: %d сигналов, %d ошибок", signals_found, errors)


async def scheduled_outcome_check(
    lab: TruthLab,
    client: TinkoffClient,
    bot: SokolBot
) -> None:
    """Ежедневная проверка outcomes в 19:00 МСК."""
    logger.info("🔄 Запуск Outcome Engine...")

    try:
        engine = OutcomeEngine(
            lab=lab,
            client=client,
            threshold_pct=Config.OUTCOME_THRESHOLD_PCT
        )
        engine.init_outcomes_table()
        await engine.run_all_checkpoints()

        stats = engine.get_statistics()
        logger.info("✅ Outcome check завершён. Сигналов: %d", stats['total_signals'])

        if stats['total_signals'] > 0:
            await send_outcome_report(bot, stats)
        else:
            logger.info("📭 Нет данных для отчёта")

    except Exception as e:
        logger.error("❌ Outcome check failed: %s", e)


async def send_outcome_report(bot: SokolBot, stats: Dict) -> None:
    """Отправить отчёт по outcomes в Telegram."""
    try:
        parts = []
        parts.append("📊 <b>Ежедневный отчёт Outcomes</b>")
        parts.append("Всего сигналов: %d" % stats['total_signals'])
        parts.append("")

        for cp in [1, 3, 7, 30]:
            s = stats['by_checkpoint'].get(cp, {})
            win = s.get('win', 0)
            loss = s.get('loss', 0)
            neutral = s.get('neutral', 0)
            winrate = s.get('winrate', 0)

            parts.append("<b>%d дней:</b>" % cp)
            parts.append("🟢 WIN: %d | 🔴 LOSS: %d | ⚪ NEUTRAL: %d" % (win, loss, neutral))
            parts.append("📈 Winrate: %.1f%%" % winrate)
            parts.append("")

        parts.append("<b>MFE / MAE:</b>")
        parts.append("↗️ Средний MFE: %.2f%%" % stats['avg_mfe'])
        parts.append("↘️ Средний MAE: %.2f%%" % stats['avg_mae'])

        message = chr(10).join(parts)

        await bot.app.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        logger.info("📨 Отчёт отправлен в Telegram")
    except Exception as e:
        logger.error("❌ Ошибка отправки отчёта: %s", e)


async def run_bot_polling(bot: SokolBot) -> None:
    """
    Запуск Telegram polling с защитой от Conflict.
    Использует initialize() + start() + updater.start_polling() 
    вместо run_polling(), чтобы избежать конфликта event loop.
    """
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info("🤖 Запуск Telegram polling (попытка %d/%d)...", attempt + 1, max_retries)

            # Инициализация и запуск
            await bot.app.initialize()
            await bot.app.start()
            await bot.app.updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True
            )
            logger.info("✅ Telegram polling запущен")

            # Держим задачу живой
            while True:
                await asyncio.sleep(3600)

        except telegram.error.Conflict:
            logger.warning("⚠️ Conflict (другой экземпляр бота). Ждём %d сек...", retry_delay)
            await asyncio.sleep(retry_delay)
            continue

        except asyncio.CancelledError:
            logger.info("🛑 Telegram polling остановлен")
            return

        except Exception as e:
            logger.error("❌ Ошибка Telegram polling: %s", e)
            if attempt < max_retries - 1:
                logger.info("🔄 Перезапуск через %d сек...", retry_delay)
                await asyncio.sleep(retry_delay)
            else:
                logger.error("❌ Максимум попыток, остановка")
                raise
        finally:
            # Корректное завершение
            try:
                if bot.app.updater.running:
                    await bot.app.updater.stop()
                if bot.app.running:
                    await bot.app.stop()
                await bot.app.shutdown()
            except Exception:
                pass


async def main() -> None:
    """Главная функция с asyncio event loop."""
    logger.info("🦅 SOKOL-TRADER v0.6.2 запускается...")
    logger.info("=" * 50)

    config = Config()
    lab = TruthLab(config.DB_PATH)
    signal_engine = SignalEngine()

    logger.info("📁 База данных: %s", config.DB_PATH)
    logger.info("📈 Тикеры: %s", ", ".join(Config.TICKERS))
    logger.info("⏱️  Таймфрейм: %s", Config.TIMEFRAME)
    logger.info("🎯 Порог Outcome: ±%s%%", Config.OUTCOME_THRESHOLD_PCT)

    async with TinkoffClient() as tinkoff:
        logger.info("🔍 Загрузка FIGI...")
        await tinkoff.preload_figis(Config.TICKERS)
        logger.info("✅ FIGI загружены")

        # Telegram Bot
        bot = SokolBot()
        logger.info("🤖 Telegram Bot инициализирован")

        # Scheduler
        scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

        # Задача 1: Сканирование рынка каждые 15 минут
        scheduler.add_job(
            scan_market,
            'interval',
            minutes=15,
            args=[bot, tinkoff, signal_engine, lab],
            id="market_scanner",
            replace_existing=True
        )
        logger.info("🕐 Сканер: каждые 15 минут")

        # Задача 2: Ежедневная проверка outcomes в 19:00 МСК
        check_time = Config.OUTCOME_CHECK_TIME.split(":")
        scheduler.add_job(
            scheduled_outcome_check,
            CronTrigger(
                hour=int(check_time[0]),
                minute=int(check_time[1]),
                timezone="Europe/Moscow"
            ),
            args=[lab, tinkoff, bot],
            id="outcome_daily",
            replace_existing=True
        )
        logger.info("🕐 Outcome check: ежедневно в %s МСК", Config.OUTCOME_CHECK_TIME)

        # Запуск scheduler
        scheduler.start()
        logger.info("=" * 50)
        logger.info("✅ SOKOL-TRADER v0.6.2 работает!")
        logger.info("💡 Нажмите Ctrl+C для остановки")

        # Запуск Telegram polling как отдельная задача
        bot_task = asyncio.create_task(run_bot_polling(bot))

        # Ждём сигнала остановки
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Остановка по запросу пользователя...")
        finally:
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
            scheduler.shutdown()
            logger.info("👋 SOKOL-TRADER остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 SOKOL-TRADER завершён")