"""
🌌 Passagem Sombria - RPG Master Bot
Bot do Telegram que usa a API do Gemini como Mestre de RPG.
"""

import os
import time
import logging
import asyncio
import random as rng
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 10000))

# ── Carregar conteúdo do RPG ─────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f:
    RPG_CONTENT = f.read()

# ── System prompt do Mestre ──────────────────────────────
SYSTEM_PROMPT = f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".

Seu papel: narrar aventuras, controlar NPCs, aplicar regras, rolar dados, criar situações épicas.

REGRAS:
1. Siga o sistema fielmente (d20, perícias, CD, etc.).
2. Simule rolagens quando necessário. Formato: 🎲 1d20(14) + Mod(3) + Perícia(2) = 19 vs CD 15 → ✅
3. Narre em português brasileiro, tom sombrio e cinematográfico.
4. Guie criação de personagens passo a passo.
5. Use emojis com moderação (🎲⚔️🛡️🚀💀).
6. Controle inventário, vida e status dos jogadores.
7. Use o Bestiário para encontros balanceados.
8. Respostas concisas mas imersivas (máximo 800 palavras).

REFERÊNCIA COMPLETA DO SISTEMA:

{RPG_CONTENT}
"""

# ── Configurar Gemini ────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.85,
        max_output_tokens=1500,
    ),
)

# ── Histórico de conversa por chat ───────────────────────
MAX_HISTORY = 30
chat_sessions: dict = {}


def get_chat(chat_id: int):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    return chat_sessions[chat_id]


def trim_history(chat_id: int):
    if chat_id in chat_sessions:
        session = chat_sessions[chat_id]
        if len(session.history) > MAX_HISTORY * 2:
            session.history = session.history[-(MAX_HISTORY * 2):]


# ── Envio com retry (backoff exponencial + jitter) ───────
async def send_to_gemini(chat, prompt: str, retries: int = 4, telegram_msg=None) -> str:
    """Envia mensagem ao Gemini com retry automático para 429.
    Usa backoff exponencial com jitter conforme recomendação do Google.
    """
    for attempt in range(retries):
        try:
            response = chat.send_message(prompt)
            return response.text

        except google_exceptions.ResourceExhausted as e:
            # Parse do erro para saber qual cota bateu
            error_detail = str(e)
            if "per_minute" in error_detail:
                quota_type = "requisições por minuto"
            elif "per_day" in error_detail:
                quota_type = "requisições diárias"
                # Se bateu limite diário, não adianta retry
                logger.error(f"Limite DIÁRIO atingido: {error_detail}")
                return (
                    "⚠️ *Limite diário da API atingido.*\n\n"
                    "O plano gratuito do Gemini tem um limite de requisições por dia. "
                    "Tente novamente amanhã, ou peça ao administrador para "
                    "ativar o plano pago no Google AI Studio.\n\n"
                    "💡 Enquanto isso, use /rolar e /regras (funcionam offline)."
                )
            elif "tokens" in error_detail:
                quota_type = "tokens por minuto"
            else:
                quota_type = "API"

            # Backoff exponencial com jitter: 10s, 25s, 55s, 115s
            base_wait = (2 ** attempt) * 10
            jitter = rng.uniform(0, 5)
            wait = base_wait + jitter

            logger.warning(
                f"Rate limit 429 ({quota_type}). "
                f"Tentativa {attempt+1}/{retries}. Aguardando {wait:.0f}s..."
            )

            # Avisa o jogador no Telegram que está aguardando
            if telegram_msg and attempt < retries - 1:
                try:
                    await telegram_msg.reply_text(
                        f"⏳ _Limite de {quota_type} atingido. "
                        f"Tentando novamente em {wait:.0f}s..._",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

            await asyncio.sleep(wait)

        except Exception as e:
            logger.error(f"Erro Gemini: {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(5)

    return (
        "⚠️ O Mestre está temporariamente indisponível.\n"
        "Aguarde 1-2 minutos e tente novamente.\n"
        "💡 Use /rolar e /regras enquanto isso (funcionam offline)."
    )


# ── Enviar resposta (com fallback de Markdown) ───────────
async def reply_safe(message, text: str):
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts:
            try:
                await message.reply_text(part, parse_mode="Markdown")
            except Exception:
                await message.reply_text(part)
    else:
        try:
            await message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await message.reply_text(text)


# ── Handlers do Telegram ─────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🌌 *PASSAGEM SOMBRIA - RPG ESPACIAL* 🌌\n\n"
        "Bem-vindo, viajante. Eu sou o Mestre do Vácuo.\n\n"
        "🚀 /novojogo — Iniciar uma nova aventura\n"
        "🧑‍🚀 /criarpersonagem — Criar seu personagem\n"
        "🎲 /rolar NdN — Rolar dados (ex: /rolar 2d8)\n"
        "📖 /regras — Consultar regras rápidas\n"
        "🔄 /reset — Resetar a sessão\n"
        "❓ /ajuda — Ver comandos\n\n"
        "Ou simplesmente escreva algo e eu narrarei...\n\n"
        "_O vácuo sussurra. Você ouve?_"
    )
    await reply_safe(update.message, welcome)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *COMANDOS DISPONÍVEIS:*\n\n"
        "🚀 /novojogo — Começa uma nova aventura\n"
        "🧑‍🚀 /criarpersonagem — Criação guiada de personagem\n"
        "🎲 /rolar 1d20 — Rola dados (1d20, 2d8, 4d6...)\n"
        "📖 /regras — Resumo das regras\n"
        "🗺️ /racas — Raças disponíveis\n"
        "⚔️ /classes — Classes disponíveis\n"
        "🔄 /reset — Limpa a sessão\n"
        "❓ /ajuda — Esta mensagem\n\n"
        "💡 Dica: converse livremente comigo!"
    )
    await reply_safe(update.message, help_text)


async def cmd_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)

    await update.message.reply_text("🌌 _Preparando a aventura..._", parse_mode="Markdown")

    prompt = (
        "O jogador quer começar uma nova aventura. "
        "Apresente uma cena de abertura épica no universo de Passagem Sombria. "
        "Dê opções de onde começar e pergunte se já tem personagem ou quer criar um. "
        "Seja conciso mas imersivo."
    )
    text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)

    await update.message.reply_text("🧑‍🚀 _Iniciando criação de personagem..._", parse_mode="Markdown")

    prompt = (
        "O jogador quer criar um personagem. Guie passo a passo: "
        "1) Raça, 2) Classe, 3) Filosofia, 4) Atributos (2d8 x7, descarta menor), "
        "5) PV/CD/RAM, 6) Equipamento. "
        "Comece listando as 9 raças de forma RESUMIDA (nome, planeta, 1 frase) e peça que escolha."
    )
    text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("🎲 Use: /rolar NdN (ex: /rolar 1d20, /rolar 4d6)")
        return

    dice_str = args[0].lower()
    try:
        num, sides = dice_str.split("d")
        num = int(num) if num else 1
        sides = int(sides)
        if num < 1 or num > 20 or sides < 1 or sides > 100:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Formato inválido. Use: /rolar NdN (ex: /rolar 2d8)")
        return

    rolls = [rng.randint(1, sides) for _ in range(num)]
    total = sum(rolls)

    crit_msg = ""
    if sides == 20 and num == 1:
        if rolls[0] == 20:
            crit_msg = "\n\n🌟 *ACERTO CRÍTICO!*"
        elif rolls[0] == 1:
            crit_msg = "\n\n💀 *FALHA CRÍTICA!*"

    result = f"🎲 *{dice_str.upper()}*\nDados: {rolls}\n*Total: {total}*{crit_msg}"
    await reply_safe(update.message, result)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = (
        "📖 *REGRAS RÁPIDAS*\n\n"
        "🎲 Teste: 1d20 + Atributo + Perícia ≥ CD\n"
        "⚔️ Dano melee: dado arma + Força\n"
        "🔫 Dano ranged: dado arma + Destreza\n"
        "🛡️ Defesa: 10 + Des + Armadura\n\n"
        "💥 20 natural = Crítico (dobra dados)\n"
        "💀 1 natural = Falha crítica\n\n"
        "❤️ 0 PV = Testes de Morte\n"
        "🔋 Pentes duram 3 turnos\n"
        "🧠 RAM = 1 + Int + ½Tecnomancia"
    )
    await reply_safe(update.message, rules)


async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    await update.message.reply_text("🗺️ _Consultando arquivos..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        "Liste as 9 raças jogáveis de forma CURTA: nome, planeta, principal vantagem. Use emojis.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    await update.message.reply_text("⚔️ _Consultando arquivos..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        "Liste as 15 classes jogáveis de forma CURTA: nome, PV base, papel, habilidade principal.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    await update.message.reply_text(
        "🔄 Sessão resetada! O vácuo engoliu suas memórias...\n"
        "Use /novojogo ou /criarpersonagem para recomeçar."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text
    user_name = update.message.from_user.first_name or "Viajante"

    if not user_message:
        return

    chat = get_chat(chat_id)
    prompt = f"[Jogador: {user_name}]: {user_message}"

    try:
        text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
        trim_history(chat_id)
        await reply_safe(update.message, text)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        await update.message.reply_text(
            "⚠️ O vácuo interferiu... Tente novamente em alguns segundos!"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")


# ── Main ─────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ajuda", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("novojogo", cmd_new_game))
    app.add_handler(CommandHandler("criarpersonagem", cmd_create_character))
    app.add_handler(CommandHandler("rolar", cmd_roll))
    app.add_handler(CommandHandler("roll", cmd_roll))
    app.add_handler(CommandHandler("regras", cmd_rules))
    app.add_handler(CommandHandler("racas", cmd_races))
    app.add_handler(CommandHandler("classes", cmd_classes))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    if WEBHOOK_URL:
        logger.info(f"🚀 Webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
        )
    else:
        logger.info("🚀 Polling mode (local)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
