"""
🌌 Passagem Sombria - RPG Master Bot
Bot do Telegram com Gemini AI + Supabase para fichas persistentes.
"""

import os
import json
import logging
import asyncio
import random as rng
from datetime import datetime, timezone
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
from supabase import create_client

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
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# ── Supabase (banco de fichas) ───────────────────────────
db = None
if SUPABASE_URL and SUPABASE_KEY:
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase conectado")
else:
    logger.warning("⚠️ Supabase não configurado — fichas não serão salvas")

# ── Carregar conteúdo do RPG ─────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f:
    RPG_CONTENT = f.read()

# ── Formato JSON da ficha (para o Gemini extrair) ────────
FICHA_JSON_FORMAT = """{
  "nome": "Nome do Personagem",
  "raca": "Raça",
  "classe": "Classe",
  "filosofia": "Caminho ou Código escolhido",
  "nivel": 1,
  "pv_atual": 0,
  "pv_max": 0,
  "cd": 0,
  "ram_atual": 0,
  "ram_max": 0,
  "iniciativa": 0,
  "deslocamento": 9,
  "atributos": {
    "forca": 0, "destreza": 0, "constituicao": 0,
    "inteligencia": 0, "sabedoria": 0, "carisma": 0
  },
  "pericias": {"nome_pericia": 0},
  "habilidades": ["lista de habilidades da raça, classe e filosofia"],
  "armas": [{"nome": "Arma", "dano": "1d8", "efeito": "Confiável"}],
  "armadura": {"nome": "Armadura", "cd_bonus": 0},
  "inventario": ["item1", "item2"],
  "creditos": 100,
  "implantes": [],
  "notas": "observações extras"
}"""

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

REGRA CRÍTICA DE ROLAGEM DE ATRIBUTOS (siga EXATAMENTE):
Ao criar personagem, os atributos são definidos assim:
- Passo 1: Role 2d8 SETE vezes. Cada rolagem gera um valor (soma dos 2 dados).
- Passo 2: Dos 7 valores obtidos, DESCARTE o menor.
- Passo 3: Sobram 6 valores. O jogador distribui livremente esses 6 valores entre os 6 atributos (Força, Destreza, Constituição, Inteligência, Sabedoria, Carisma).
- Passo 4: Some os modificadores raciais a cada atributo.
Exemplo: rolagens = [9, 5, 12, 7, 11, 8, 10] → descarta 5 → sobram [9, 12, 7, 11, 8, 10] → jogador distribui.
IMPORTANTE: NÃO role 2d8 por atributo individualmente. Role tudo de uma vez e deixe o jogador distribuir.

SISTEMA DE FICHA:
Quando o sistema pedir para exportar a ficha (via comando EXPORT_FICHA), responda APENAS com
um bloco JSON válido no formato abaixo, sem texto adicional, sem markdown, sem explicações:
{FICHA_JSON_FORMAT}

REFERÊNCIA COMPLETA DO SISTEMA:

{RPG_CONTENT}
"""

# ── Configurar Gemini ────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
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


# ── Supabase helpers ─────────────────────────────────────

def save_ficha(user_id: int, user_name: str, chat_id: int, ficha_data: dict):
    """Salva ou atualiza a ficha no Supabase."""
    if not db:
        return False
    try:
        record = {
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "user_name": user_name,
            "character_name": ficha_data.get("nome", "Desconhecido"),
            "ficha": json.dumps(ficha_data, ensure_ascii=False),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Upsert: atualiza se existir, cria se não
        db.table("fichas").upsert(
            record, on_conflict="user_id,chat_id"
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar ficha: {e}")
        return False


def load_ficha(user_id: int, chat_id: int) -> dict | None:
    """Carrega a ficha do Supabase."""
    if not db:
        return None
    try:
        result = (
            db.table("fichas")
            .select("ficha")
            .eq("user_id", str(user_id))
            .eq("chat_id", str(chat_id))
            .execute()
        )
        if result.data:
            return json.loads(result.data[0]["ficha"])
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar ficha: {e}")
        return None


def list_fichas(chat_id: int) -> list:
    """Lista todas as fichas de um chat/grupo."""
    if not db:
        return []
    try:
        result = (
            db.table("fichas")
            .select("user_name, character_name, updated_at")
            .eq("chat_id", str(chat_id))
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Erro ao listar fichas: {e}")
        return []


def format_ficha(ficha: dict) -> str:
    """Formata a ficha para exibição no Telegram."""
    attr = ficha.get("atributos", {})
    armas = ficha.get("armas", [])
    armas_txt = "\n".join(
        f"  • {a.get('nome','?')} ({a.get('dano','?')}) {a.get('efeito','')}"
        for a in armas
    ) if armas else "  Nenhuma"

    implantes = ficha.get("implantes", [])
    impl_txt = ", ".join(implantes) if implantes else "Nenhum"

    inv = ficha.get("inventario", [])
    inv_txt = ", ".join(inv) if inv else "Vazio"

    pericias = ficha.get("pericias", {})
    per_txt = ", ".join(f"{k}+{v}" for k, v in pericias.items() if v) if pericias else "Nenhuma"

    habs = ficha.get("habilidades", [])
    hab_txt = "\n".join(f"  • {h}" for h in habs) if habs else "  Nenhuma"

    armadura = ficha.get("armadura", {})
    arm_nome = armadura.get("nome", "Nenhuma") if isinstance(armadura, dict) else str(armadura)

    return (
        f"🧑‍🚀 *FICHA: {ficha.get('nome', '???')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌌 Raça: {ficha.get('raca', '?')} | Classe: {ficha.get('classe', '?')}\n"
        f"📜 Filosofia: {ficha.get('filosofia', '?')}\n"
        f"📊 Nível: {ficha.get('nivel', 1)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ PV: {ficha.get('pv_atual', '?')}/{ficha.get('pv_max', '?')}\n"
        f"🛡️ CD: {ficha.get('cd', '?')}\n"
        f"🧠 RAM: {ficha.get('ram_atual', '?')}/{ficha.get('ram_max', '?')}\n"
        f"⚡ Iniciativa: +{ficha.get('iniciativa', 0)}\n"
        f"🏃 Deslocamento: {ficha.get('deslocamento', 9)}m\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💪 For: {attr.get('forca', '?')} | ⚡ Des: {attr.get('destreza', '?')} | "
        f"🩸 Con: {attr.get('constituicao', '?')}\n"
        f"🧠 Int: {attr.get('inteligencia', '?')} | 🦉 Sab: {attr.get('sabedoria', '?')} | "
        f"🗣️ Car: {attr.get('carisma', '?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Perícias: {per_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠️ Habilidades:\n{hab_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ Armas:\n{armas_txt}\n"
        f"🛡️ Armadura: {arm_nome}\n"
        f"🦾 Implantes: {impl_txt}\n"
        f"🎒 Inventário: {inv_txt}\n"
        f"💎 Créditos: {ficha.get('creditos', 0)} CG\n"
    )


# ── Envio com retry (backoff exponencial + jitter) ───────
async def send_to_gemini(chat, prompt: str, retries: int = 4, telegram_msg=None) -> str:
    for attempt in range(retries):
        try:
            response = chat.send_message(prompt)
            return response.text

        except google_exceptions.ResourceExhausted as e:
            error_detail = str(e)
            if "per_minute" in error_detail:
                quota_type = "requisições por minuto"
            elif "per_day" in error_detail:
                quota_type = "requisições diárias"
                logger.error(f"Limite DIÁRIO atingido: {error_detail}")
                return (
                    "⚠️ *Limite diário da API atingido.*\n\n"
                    "Tente novamente amanhã.\n"
                    "💡 Use /rolar, /regras e /ficha (funcionam offline)."
                )
            elif "tokens" in error_detail:
                quota_type = "tokens por minuto"
            else:
                quota_type = "API"

            base_wait = (2 ** attempt) * 10
            jitter = rng.uniform(0, 5)
            wait = base_wait + jitter

            logger.warning(
                f"Rate limit 429 ({quota_type}). "
                f"Tentativa {attempt+1}/{retries}. Aguardando {wait:.0f}s..."
            )

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
        "💡 Use /rolar, /regras e /ficha (funcionam offline)."
    )


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
        "💾 /salvar — Salvar ficha do personagem\n"
        "📂 /carregar — Carregar ficha salva\n"
        "📋 /ficha — Ver sua ficha atual\n"
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
        "🎲 /rolar 1d20 — Rola dados\n"
        "📖 /regras — Resumo das regras\n"
        "🗺️ /racas — Raças disponíveis\n"
        "⚔️ /classes — Classes disponíveis\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💾 /salvar — Salva sua ficha no banco\n"
        "📂 /carregar — Carrega sua ficha salva\n"
        "📋 /ficha — Mostra sua ficha atual\n"
        "📋 /fichas — Lista fichas do grupo\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 /reset — Limpa a sessão\n"
        "❓ /ajuda — Esta mensagem"
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
        "1) Raça, 2) Classe, 3) Filosofia, 4) Atributos, "
        "5) PV/CD/RAM, 6) Equipamento. "
        "Comece listando as 9 raças de forma RESUMIDA (nome, planeta, 1 frase) e peça que escolha. "
        "LEMBRETE: na etapa de atributos, role 2d8 SETE vezes de uma vez, "
        "descarte o menor dos 7 resultados, e deixe o jogador distribuir os 6 restantes."
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


# ── Comandos de Ficha ────────────────────────────────────

async def cmd_salvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pede ao Gemini para exportar a ficha em JSON e salva no Supabase."""
    if not db:
        await update.message.reply_text(
            "⚠️ Banco de dados não configurado. Peça ao admin para configurar o Supabase."
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"
    chat = get_chat(chat_id)

    await update.message.reply_text("💾 _Exportando ficha..._", parse_mode="Markdown")

    # Pede ao Gemini para extrair os dados da ficha em JSON
    export_prompt = (
        "EXPORT_FICHA: Exporte a ficha COMPLETA do personagem do jogador atual "
        "em formato JSON puro. Use EXATAMENTE a estrutura de JSON que está nas suas instruções. "
        "Responda APENAS com o JSON, sem markdown, sem ```json, sem texto antes ou depois. "
        "Se o jogador ainda não tem personagem criado, responda apenas: NO_CHARACTER"
    )

    raw = await send_to_gemini(chat, export_prompt, telegram_msg=update.message)

    if "NO_CHARACTER" in raw:
        await update.message.reply_text(
            "❌ Nenhum personagem encontrado nesta sessão.\n"
            "Use /criarpersonagem primeiro!"
        )
        return

    # Limpa possível markdown do JSON
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]  # remove primeira linha
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    try:
        ficha_data = json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"JSON inválido do Gemini: {raw[:500]}")
        await update.message.reply_text(
            "⚠️ Não consegui extrair a ficha. Tente novamente com /salvar.\n"
            "Dica: certifique-se de que o personagem foi criado completamente."
        )
        return

    # Salva no Supabase
    success = save_ficha(user_id, user_name, chat_id, ficha_data)

    if success:
        nome = ficha_data.get("nome", "Personagem")
        await update.message.reply_text(
            f"✅ Ficha de *{nome}* salva com sucesso!\n"
            f"Use /ficha para visualizar ou /carregar para recuperar em outra sessão.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Erro ao salvar. Tente novamente.")


async def cmd_carregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Carrega a ficha do Supabase e injeta no contexto do Gemini."""
    if not db:
        await update.message.reply_text(
            "⚠️ Banco de dados não configurado."
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"

    ficha = load_ficha(user_id, chat_id)

    if not ficha:
        await update.message.reply_text(
            "❌ Nenhuma ficha salva encontrada.\n"
            "Use /criarpersonagem para criar um e /salvar para guardar."
        )
        return

    # Injeta a ficha no contexto do Gemini
    chat = get_chat(chat_id)
    inject_prompt = (
        f"CARREGAR_FICHA: O jogador {user_name} está carregando seu personagem salvo. "
        f"A ficha completa dele é:\n{json.dumps(ficha, ensure_ascii=False, indent=2)}\n\n"
        f"A partir de agora, use esses dados como a ficha oficial deste jogador. "
        f"Cumprimente o jogador confirmando que o personagem foi carregado, "
        f"mencionando o nome, raça e classe dele brevemente."
    )

    text = await send_to_gemini(chat, inject_prompt, telegram_msg=update.message)

    # Mostra a ficha formatada + resposta do Mestre
    ficha_txt = format_ficha(ficha)
    await reply_safe(update.message, ficha_txt)
    await reply_safe(update.message, text)


async def cmd_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra a ficha salva do jogador."""
    if not db:
        await update.message.reply_text(
            "⚠️ Banco de dados não configurado. "
            "Pergunte ao Mestre sobre sua ficha na conversa!"
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id

    ficha = load_ficha(user_id, chat_id)

    if not ficha:
        await update.message.reply_text(
            "❌ Nenhuma ficha salva. Use /salvar após criar seu personagem."
        )
        return

    await reply_safe(update.message, format_ficha(ficha))


async def cmd_fichas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todas as fichas salvas no grupo/chat."""
    if not db:
        await update.message.reply_text("⚠️ Banco de dados não configurado.")
        return

    chat_id = update.effective_chat.id
    fichas = list_fichas(chat_id)

    if not fichas:
        await update.message.reply_text("📋 Nenhuma ficha salva neste chat ainda.")
        return

    lines = ["📋 *FICHAS SALVAS NESTE CHAT:*\n"]
    for f in fichas:
        lines.append(
            f"• *{f.get('character_name', '?')}* — jogador: {f.get('user_name', '?')}"
        )

    await reply_safe(update.message, "\n".join(lines))


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    await update.message.reply_text(
        "🔄 Sessão resetada! O vácuo engoliu suas memórias...\n"
        "💾 Suas fichas salvas continuam no banco (/carregar para recuperar).\n"
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
    app.add_handler(CommandHandler("salvar", cmd_salvar))
    app.add_handler(CommandHandler("carregar", cmd_carregar))
    app.add_handler(CommandHandler("ficha", cmd_ficha))
    app.add_handler(CommandHandler("fichas", cmd_fichas))
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
