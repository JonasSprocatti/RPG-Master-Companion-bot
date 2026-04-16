"""
🌌 Passagem Sombria - RPG Master Bot
Bot do Telegram que usa a API do Gemini como Mestre de RPG.
"""

import os
import logging
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import google.generativeai as genai

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # ex: https://rpg-master-companion-bot.onrender.com
PORT = int(os.environ.get("PORT", 10000))

# ── Carregar conteúdo do RPG ─────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f:
    RPG_CONTENT = f.read()

# ── System prompt do Mestre ──────────────────────────────
SYSTEM_PROMPT = f"""Você é o **Mestre do RPG "Passagem Sombria - RPG Espacial"**.

Seu papel é narrar aventuras, controlar NPCs, aplicar as regras do sistema,
rolar dados quando necessário e criar situações emocionantes para os jogadores.

REGRAS DE COMPORTAMENTO:
1. Sempre siga as regras do sistema fielmente (d20, perícias, CD, etc.).
2. Quando um jogador declarar uma ação que exija teste, peça o teste e
   informe a CD. Simule a rolagem de dados quando o jogador pedir.
3. Narre de forma imersiva, cinematográfica e em português brasileiro.
4. Mantenha o tom sombrio e espacial do universo.
5. Quando jogadores criarem personagens, guie-os passo a passo usando
   as regras de raças, classes, filosofias e atributos do livro.
6. Use emojis temáticos com moderação para dar vida à narrativa (🎲⚔️🛡️🚀💀).
7. Quando rolar dados, mostre o resultado de forma clara:
   🎲 Resultado: 1d20 (14) + Mod (3) + Perícia (2) = 19 vs CD 15 → ✅ Sucesso!
8. Controle o inventário, vida e status dos personagens dos jogadores.
9. Crie encontros balanceados usando o Bestiário do livro.
10. Permita que múltiplos jogadores participem no mesmo chat de grupo.

IMPORTANTE: Você tem acesso COMPLETO ao livro de regras abaixo.
Use-o como referência absoluta para todas as mecânicas.

═══════════════════════════════════════════════════
LIVRO DE REGRAS COMPLETO - PASSAGEM SOMBRIA
═══════════════════════════════════════════════════

{RPG_CONTENT}
"""

# ── Configurar Gemini ────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.85,
        max_output_tokens=2048,
    ),
)

# ── Histórico de conversa por chat ───────────────────────
MAX_HISTORY = 50  # máximo de mensagens no histórico por chat
chat_sessions: dict = {}


def get_chat(chat_id: int):
    """Retorna ou cria uma sessão de chat do Gemini para o chat_id."""
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    return chat_sessions[chat_id]


def trim_history(chat_id: int):
    """Mantém o histórico dentro do limite para não estourar o contexto."""
    if chat_id in chat_sessions:
        session = chat_sessions[chat_id]
        if len(session.history) > MAX_HISTORY * 2:
            session.history = session.history[-(MAX_HISTORY * 2):]


# ── Handlers do Telegram ─────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🌌 **PASSAGEM SOMBRIA - RPG ESPACIAL** 🌌\n\n"
        "Bem-vindo, viajante. Eu sou o Mestre do Vácuo.\n\n"
        "🚀 **/novojogo** — Iniciar uma nova aventura\n"
        "🧑‍🚀 **/criarpersonagem** — Criar seu personagem\n"
        "🎲 **/rolar NdN** — Rolar dados (ex: /rolar 2d8)\n"
        "📖 **/regras** — Consultar regras rápidas\n"
        "🔄 **/reset** — Resetar a sessão\n"
        "❓ **/ajuda** — Ver comandos\n\n"
        "Ou simplesmente escreva algo e eu narrarei...\n\n"
        "_O vácuo sussurra. Você ouve?_"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **COMANDOS DISPONÍVEIS:**\n\n"
        "🚀 /novojogo — Começa uma nova aventura narrada\n"
        "🧑‍🚀 /criarpersonagem — O Mestre guia a criação do seu personagem\n"
        "🎲 /rolar 1d20 — Rola dados (1d20, 2d8, 4d6, etc.)\n"
        "📖 /regras — Resumo rápido das regras\n"
        "🗺️ /racas — Lista das raças disponíveis\n"
        "⚔️ /classes — Lista das classes disponíveis\n"
        "🔄 /reset — Limpa o histórico da sessão\n"
        "❓ /ajuda — Mostra esta mensagem\n\n"
        "💡 **Dica:** Você pode simplesmente conversar comigo!\n"
        "Diga o que seu personagem faz e eu narrarei o resultado."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)

    prompt = (
        "O jogador quer começar uma nova aventura. "
        "Apresente uma cena de abertura épica e imersiva no universo de Passagem Sombria. "
        "Dê ao jogador opções de onde começar (qual planeta ou estação) e pergunte "
        "se ele já tem um personagem criado ou se quer criar um."
    )
    response = chat.send_message(prompt)
    await update.message.reply_text(response.text, parse_mode="Markdown")


async def cmd_create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)

    prompt = (
        "O jogador quer criar um personagem do zero. "
        "Guie-o passo a passo pela criação seguindo as regras do livro: "
        "1) Escolher Raça, 2) Escolher Classe, 3) Escolher Filosofia de Vida, "
        "4) Rolar atributos (2d8 sete vezes, descartar o menor), "
        "5) Calcular PV, CD e RAM, 6) Equipamento inicial. "
        "Comece perguntando qual raça ele quer jogar, listando as opções de forma resumida."
    )
    response = chat.send_message(prompt)
    await update.message.reply_text(response.text, parse_mode="Markdown")


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random

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

    rolls = [random.randint(1, sides) for _ in range(num)]
    total = sum(rolls)

    # Detectar críticos no d20
    crit_msg = ""
    if sides == 20 and num == 1:
        if rolls[0] == 20:
            crit_msg = "\n\n🌟 **ACERTO CRÍTICO! O UNIVERSO SORRIU PRA VOCÊ!**"
        elif rolls[0] == 1:
            crit_msg = "\n\n💀 **FALHA CRÍTICA! O COSMOS CONSPIROU CONTRA VOCÊ!**"

    result = (
        f"🎲 **Rolagem: {dice_str.upper()}**\n"
        f"Dados: {rolls}\n"
        f"**Total: {total}**"
        f"{crit_msg}"
    )
    await update.message.reply_text(result, parse_mode="Markdown")


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = (
        "📖 **REGRAS RÁPIDAS — PASSAGEM SOMBRIA**\n\n"
        "🎲 **Teste:** 1d20 + Atributo + Perícia ≥ CD\n"
        "⚔️ **Dano corpo a corpo:** Dado da arma + Força\n"
        "🔫 **Dano à distância:** Dado da arma + Destreza\n"
        "🛡️ **Defesa (CD):** 10 + Des + Armadura\n\n"
        "💥 **20 natural** = Crítico (dobra dados de dano)\n"
        "💀 **1 natural** = Falha crítica (arma emperra)\n\n"
        "❤️ **0 PV** = Inconsciente → Testes de Morte\n"
        "🔋 **Pentes** duram 3 turnos de tiro\n"
        "🧠 **RAM** = 1 + Int + ½ Tecnomancia\n\n"
        "Pergunte-me qualquer detalhe sobre as regras!"
    )
    await update.message.reply_text(rules, parse_mode="Markdown")


async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    prompt = (
        "Liste de forma resumida e organizada todas as 9 raças jogáveis "
        "do Passagem Sombria, com o planeta de origem e a principal vantagem de cada uma. "
        "Mantenha curto e visual com emojis."
    )
    response = chat.send_message(prompt)
    await update.message.reply_text(response.text, parse_mode="Markdown")


async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    prompt = (
        "Liste de forma resumida e organizada todas as 15 classes jogáveis "
        "do Passagem Sombria, com o papel no grupo e a principal habilidade de cada. "
        "Mantenha curto e visual com emojis."
    )
    response = chat.send_message(prompt)
    await update.message.reply_text(response.text, parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    await update.message.reply_text(
        "🔄 Sessão resetada! O vácuo engoliu suas memórias...\n"
        "Use /novojogo para recomeçar ou /criarpersonagem para criar um personagem."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de texto comuns e envia ao Gemini."""
    chat_id = update.effective_chat.id
    user_message = update.message.text
    user_name = update.message.from_user.first_name or "Viajante"

    if not user_message:
        return

    chat = get_chat(chat_id)

    # Contexto do jogador na mensagem
    prompt = f"[Jogador: {user_name}]: {user_message}"

    try:
        response = chat.send_message(prompt)
        trim_history(chat_id)

        # Telegram tem limite de 4096 chars por mensagem
        text = response.text
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        try:
            # Tenta sem Markdown se der erro de parse
            await update.message.reply_text(response.text)
        except Exception:
            await update.message.reply_text(
                "⚠️ O vácuo interferiu na transmissão... Tente novamente!"
            )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")


# ── Main ─────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
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

    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Erros
    app.add_error_handler(error_handler)

    # Modo de execução
    if WEBHOOK_URL:
        logger.info(f"🚀 Iniciando com webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
        )
    else:
        logger.info("🚀 Iniciando com polling (modo local)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
