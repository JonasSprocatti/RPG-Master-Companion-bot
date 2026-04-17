"""
🌌 Passagem Sombria - RPG Master Bot
Bot do Telegram com Gemini AI + Supabase para fichas persistentes.
Features: fichas, level up, importar contexto, log de sessões.
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

# ── Supabase ─────────────────────────────────────────────
db = None
if SUPABASE_URL and SUPABASE_KEY:
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase conectado")
else:
    logger.warning("⚠️ Supabase não configurado")

# ── Carregar conteúdo do RPG ─────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f:
    RPG_CONTENT = f.read()

# ── Formato JSON da ficha ────────────────────────────────
FICHA_JSON_FORMAT = """{
  "nome": "Nome do Personagem",
  "raca": "Raça",
  "classe": "Classe",
  "filosofia": "Caminho ou Código escolhido",
  "nivel": 1,
  "xp": 0,
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
  "habilidades": ["lista de habilidades"],
  "armas": [{"nome": "Arma", "dano": "1d8", "efeito": "Confiável"}],
  "armadura": {"nome": "Armadura", "cd_bonus": 0},
  "inventario": ["item1", "item2"],
  "creditos": 100,
  "implantes": [],
  "notas": ""
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
- Passo 1: Role 2d8 SETE vezes. Cada rolagem gera um valor (soma dos 2 dados).
- Passo 2: Dos 7 valores, DESCARTE o menor.
- Passo 3: Sobram 6 valores. O jogador distribui livremente entre For, Des, Con, Int, Sab, Car.
- Passo 4: Some os modificadores raciais.
IMPORTANTE: NÃO role 2d8 por atributo. Role tudo de uma vez e deixe o jogador distribuir.

REGRAS DE LEVEL UP:
Ao subir de nível, o personagem ganha:
- +1 Ponto de Atributo (máx +6 por atributo)
- Role dado de vida da raça + Con para PV extra (Pesado d10: Marcianos/Infimor's, Médio d8: Terráqueos/Ven'y/Conjupiteros/Urak's, Leve d6: Proturnos/Satas/Mercusys)
- +1 ponto de perícia (limite +5 até nv4, +7 do nv5+)
- Níveis ímpares (3,5,7,9): +1 Slot RAM

SISTEMA DE FICHA (JSON):
Quando o sistema pedir EXPORT_FICHA, responda APENAS com JSON puro no formato abaixo:
{FICHA_JSON_FORMAT}

Quando o sistema enviar LEVELUP_FICHA com um JSON, aplique as regras de level up,
role os dados necessários, e retorne o JSON atualizado com nível+1.
Responda APENAS com o JSON atualizado, sem texto adicional.

Quando o sistema enviar CONTEXTO_SESSAO, absorva as informações como contexto da aventura
e continue a narrativa a partir daquele ponto.

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


# ══════════════════════════════════════════════════════════
# SUPABASE HELPERS
# ══════════════════════════════════════════════════════════

def save_ficha(user_id: int, user_name: str, chat_id: int, ficha_data: dict):
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
        db.table("fichas").upsert(record, on_conflict="user_id,chat_id").execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar ficha: {e}")
        return False


def load_ficha(user_id: int, chat_id: int) -> dict | None:
    if not db:
        return None
    try:
        result = (
            db.table("fichas").select("ficha")
            .eq("user_id", str(user_id)).eq("chat_id", str(chat_id))
            .execute()
        )
        if result.data:
            return json.loads(result.data[0]["ficha"])
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar ficha: {e}")
        return None


def list_fichas(chat_id: int) -> list:
    if not db:
        return []
    try:
        result = (
            db.table("fichas")
            .select("user_name, character_name, updated_at")
            .eq("chat_id", str(chat_id)).execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Erro ao listar fichas: {e}")
        return []


def save_session_log(chat_id: int, title: str, summary: str):
    """Salva um resumo de sessão no banco."""
    if not db:
        return False
    try:
        record = {
            "chat_id": str(chat_id),
            "title": title,
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db.table("sessoes").insert(record).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar sessão: {e}")
        return False


def load_session_logs(chat_id: int) -> list:
    """Lista sessões salvas de um chat."""
    if not db:
        return []
    try:
        result = (
            db.table("sessoes")
            .select("id, title, created_at")
            .eq("chat_id", str(chat_id))
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Erro ao listar sessões: {e}")
        return []


def load_session_by_id(session_id: int) -> dict | None:
    """Carrega uma sessão específica."""
    if not db:
        return None
    try:
        result = (
            db.table("sessoes").select("*")
            .eq("id", session_id).execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar sessão: {e}")
        return None


# ══════════════════════════════════════════════════════════
# FORMATAÇÃO DE FICHA
# ══════════════════════════════════════════════════════════

def format_ficha(ficha: dict) -> str:
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
        f"📊 Nível: {ficha.get('nivel', 1)} | XP: {ficha.get('xp', 0)}\n"
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


# ══════════════════════════════════════════════════════════
# GEMINI COM RETRY
# ══════════════════════════════════════════════════════════

async def send_to_gemini(chat, prompt: str, retries: int = 4, telegram_msg=None) -> str:
    for attempt in range(retries):
        try:
            response = chat.send_message(prompt)
            return response.text
        except google_exceptions.ResourceExhausted as e:
            error_detail = str(e)
            if "per_day" in error_detail:
                logger.error(f"Limite DIÁRIO: {error_detail}")
                return (
                    "⚠️ *Limite diário da API atingido.*\n"
                    "Tente amanhã. Use /rolar, /regras e /ficha (offline)."
                )
            quota_type = "requisições por minuto" if "per_minute" in error_detail else "API"
            base_wait = (2 ** attempt) * 10
            jitter = rng.uniform(0, 5)
            wait = base_wait + jitter
            logger.warning(f"429 ({quota_type}). Tentativa {attempt+1}/{retries}. {wait:.0f}s...")
            if telegram_msg and attempt < retries - 1:
                try:
                    await telegram_msg.reply_text(
                        f"⏳ _Limite atingido. Retentando em {wait:.0f}s..._",
                        parse_mode="Markdown")
                except Exception:
                    pass
            await asyncio.sleep(wait)
        except Exception as e:
            logger.error(f"Erro Gemini: {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(5)
    return "⚠️ Mestre indisponível. Aguarde 1-2 min. Use /rolar e /ficha (offline)."


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


def parse_json_response(raw: str) -> dict | None:
    """Limpa e parseia JSON vindo do Gemini."""
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"JSON inválido: {raw[:300]}")
        return None


# ══════════════════════════════════════════════════════════
# HANDLERS — COMANDOS BÁSICOS
# ══════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🌌 *PASSAGEM SOMBRIA - RPG ESPACIAL* 🌌\n\n"
        "Bem-vindo, viajante. Eu sou o Mestre do Vácuo.\n\n"
        "*Jogo:*\n"
        "🚀 /novojogo — Iniciar aventura\n"
        "🧑‍🚀 /criarpersonagem — Criar personagem\n"
        "🎲 /rolar NdN — Rolar dados\n"
        "📖 /regras — Regras rápidas\n\n"
        "*Ficha:*\n"
        "💾 /salvar — Salvar ficha\n"
        "📂 /carregar — Carregar ficha salva\n"
        "📋 /ficha — Ver sua ficha\n"
        "⬆️ /levelup — Subir de nível\n\n"
        "*Sessão:*\n"
        "📝 /salvarsessao — Salvar progresso da aventura\n"
        "📚 /sessoes — Ver sessões salvas\n"
        "📂 /cargarsessao ID — Carregar sessão\n"
        "📎 /contexto — Importar contexto externo\n\n"
        "🔄 /reset — Resetar sessão\n"
        "❓ /ajuda — Todos os comandos\n\n"
        "_O vácuo sussurra. Você ouve?_"
    )
    await reply_safe(update.message, welcome)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *TODOS OS COMANDOS:*\n\n"
        "*⚔️ Jogo:*\n"
        "/novojogo — Nova aventura\n"
        "/criarpersonagem — Criar personagem\n"
        "/rolar 1d20 — Rolar dados\n"
        "/regras — Resumo das regras\n"
        "/racas — Lista de raças\n"
        "/classes — Lista de classes\n\n"
        "*💾 Ficha e Progressão:*\n"
        "/salvar — Salvar ficha no banco\n"
        "/carregar — Recuperar ficha salva\n"
        "/ficha — Mostrar sua ficha\n"
        "/fichas — Fichas do grupo\n"
        "/levelup — Subir de nível\n\n"
        "*📚 Sessões:*\n"
        "/salvarsessao — Salvar resumo da aventura\n"
        "/sessoes — Listar sessões salvas\n"
        "/cargarsessao 1 — Carregar sessão pelo ID\n"
        "/contexto — Importar história de fora\n\n"
        "*🔧 Sistema:*\n"
        "/reset — Limpar sessão (fichas salvas permanecem)\n"
        "/ajuda — Esta mensagem"
    )
    await reply_safe(update.message, help_text)


async def cmd_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)
    await update.message.reply_text("🌌 _Preparando a aventura..._", parse_mode="Markdown")
    prompt = (
        "O jogador quer começar uma nova aventura. "
        "Apresente uma cena de abertura épica. "
        "Dê opções de onde começar e pergunte se já tem personagem. Seja conciso."
    )
    text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    await update.message.reply_text("🧑‍🚀 _Iniciando criação..._", parse_mode="Markdown")
    prompt = (
        "O jogador quer criar um personagem. Guie passo a passo: "
        "1) Raça, 2) Classe, 3) Filosofia, 4) Atributos, 5) PV/CD/RAM, 6) Equipamento. "
        "Comece listando as 9 raças RESUMIDAMENTE e peça que escolha. "
        "LEMBRETE: na etapa de atributos, role 2d8 SETE vezes, "
        "descarte o menor dos 7, e deixe o jogador distribuir os 6 restantes."
    )
    text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("🎲 Use: /rolar NdN (ex: /rolar 1d20)")
        return
    dice_str = args[0].lower()
    try:
        num, sides = dice_str.split("d")
        num = int(num) if num else 1
        sides = int(sides)
        if num < 1 or num > 20 or sides < 1 or sides > 100:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Formato inválido. Use: /rolar NdN")
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
        "⚔️ Melee: dado arma + Força\n"
        "🔫 Ranged: dado arma + Destreza\n"
        "🛡️ Defesa: 10 + Des + Armadura\n\n"
        "💥 20 nat = Crítico (dobra dados)\n"
        "💀 1 nat = Falha crítica\n\n"
        "❤️ 0 PV = Testes de Morte\n"
        "🔋 Pentes duram 3 turnos\n"
        "🧠 RAM = 1 + Int + ½Tecnomancia"
    )
    await reply_safe(update.message, rules)


async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    await update.message.reply_text("🗺️ _Consultando..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        "Liste as 9 raças CURTAS: nome, planeta, vantagem. Emojis.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    await update.message.reply_text("⚔️ _Consultando..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        "Liste as 15 classes CURTAS: nome, PV base, papel, habilidade.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


# ══════════════════════════════════════════════════════════
# HANDLERS — FICHA (SALVAR / CARREGAR / VER)
# ══════════════════════════════════════════════════════════

async def cmd_salvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"
    chat = get_chat(chat_id)

    await update.message.reply_text("💾 _Exportando ficha..._", parse_mode="Markdown")

    export_prompt = (
        "EXPORT_FICHA: Exporte a ficha COMPLETA do personagem do jogador atual "
        "em JSON puro. Use a estrutura das instruções. "
        "Responda APENAS com o JSON. Sem markdown, sem texto extra. "
        "Se não tem personagem, responda apenas: NO_CHARACTER"
    )
    raw = await send_to_gemini(chat, export_prompt, telegram_msg=update.message)

    if "NO_CHARACTER" in raw:
        await update.message.reply_text("❌ Nenhum personagem nesta sessão. Use /criarpersonagem")
        return

    ficha_data = parse_json_response(raw)
    if not ficha_data:
        await update.message.reply_text("⚠️ Erro ao extrair ficha. Tente /salvar novamente.")
        return

    if save_ficha(user_id, user_name, chat_id, ficha_data):
        nome = ficha_data.get("nome", "Personagem")
        await update.message.reply_text(
            f"✅ Ficha de *{nome}* salva!\n/ficha para ver | /carregar para recuperar",
            parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Erro ao salvar. Tente novamente.")


async def cmd_carregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"

    ficha = load_ficha(user_id, chat_id)
    if not ficha:
        await update.message.reply_text("❌ Nenhuma ficha salva. Use /criarpersonagem + /salvar")
        return

    chat = get_chat(chat_id)
    inject_prompt = (
        f"CARREGAR_FICHA: O jogador {user_name} carregou seu personagem:\n"
        f"{json.dumps(ficha, ensure_ascii=False, indent=2)}\n\n"
        f"Use esses dados como ficha oficial. Confirme o carregamento brevemente."
    )
    text = await send_to_gemini(chat, inject_prompt, telegram_msg=update.message)

    await reply_safe(update.message, format_ficha(ficha))
    await reply_safe(update.message, text)


async def cmd_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado. Pergunte ao Mestre na conversa.")
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    ficha = load_ficha(user_id, chat_id)

    if not ficha:
        await update.message.reply_text("❌ Nenhuma ficha salva. Use /salvar após criar personagem.")
        return

    await reply_safe(update.message, format_ficha(ficha))


async def cmd_fichas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    fichas = list_fichas(chat_id)

    if not fichas:
        await update.message.reply_text("📋 Nenhuma ficha neste chat ainda.")
        return

    lines = ["📋 *FICHAS DESTE CHAT:*\n"]
    for f in fichas:
        lines.append(f"• *{f.get('character_name', '?')}* — {f.get('user_name', '?')}")
    await reply_safe(update.message, "\n".join(lines))


# ══════════════════════════════════════════════════════════
# HANDLER — LEVEL UP
# ══════════════════════════════════════════════════════════

async def cmd_levelup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"

    ficha = load_ficha(user_id, chat_id)
    if not ficha:
        await update.message.reply_text("❌ Nenhuma ficha salva. Use /salvar primeiro.")
        return

    nivel_atual = ficha.get("nivel", 1)
    if nivel_atual >= 10:
        await update.message.reply_text("🌟 Você já é Nível 10 — Lenda do Sistema! Nível máximo atingido.")
        return

    await update.message.reply_text(
        f"⬆️ _Subindo {ficha.get('nome', 'Personagem')} do Nível {nivel_atual} para {nivel_atual + 1}..._",
        parse_mode="Markdown"
    )

    chat = get_chat(chat_id)
    levelup_prompt = (
        f"LEVELUP_FICHA: O jogador {user_name} está subindo de nível.\n"
        f"Ficha atual:\n{json.dumps(ficha, ensure_ascii=False, indent=2)}\n\n"
        f"Aplique as regras de level up do Passagem Sombria:\n"
        f"1. Aumente o nível de {nivel_atual} para {nivel_atual + 1}\n"
        f"2. O jogador ganha +1 Ponto de Atributo — pergunte onde ele quer colocar\n"
        f"3. Role o dado de vida da raça + Constituição e some ao PV máximo\n"
        f"4. O jogador ganha +1 ponto de perícia — pergunte onde quer distribuir\n"
        f"5. Se o novo nível for ímpar (3,5,7,9), some +1 Slot de RAM\n"
        f"6. Atualize pv_atual para o novo pv_max (cura completa no level up)\n\n"
        f"NÃO retorne JSON agora. Narre o level up de forma épica e "
        f"PERGUNTE ao jogador onde quer colocar o ponto de atributo e o ponto de perícia. "
        f"Mostre o resultado do dado de vida rolado."
    )

    text = await send_to_gemini(chat, levelup_prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)

    # Salva ficha com nível incrementado (os atributos serão finalizados quando o jogador responder e usar /salvar)
    ficha["nivel"] = nivel_atual + 1
    save_ficha(user_id, user_name, chat_id, ficha)


# ══════════════════════════════════════════════════════════
# HANDLERS — SESSÕES (SALVAR / LISTAR / CARREGAR / IMPORTAR)
# ══════════════════════════════════════════════════════════

async def cmd_salvar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pede ao Gemini para resumir a sessão atual e salva no banco."""
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)

    if chat_id not in chat_sessions or not chat_sessions[chat_id].history:
        await update.message.reply_text("❌ Nenhuma sessão ativa para salvar.")
        return

    await update.message.reply_text("📝 _Resumindo a sessão..._", parse_mode="Markdown")

    summary_prompt = (
        "RESUMO_SESSAO: Crie um resumo COMPLETO e detalhado da sessão de jogo atual. "
        "Inclua:\n"
        "- Quais jogadores participaram e seus personagens\n"
        "- Onde a aventura começou e onde está agora\n"
        "- Principais eventos, combates e decisões\n"
        "- Estado atual dos personagens (vida, itens ganhos/perdidos)\n"
        "- NPCs encontrados e relações estabelecidas\n"
        "- Ganchos narrativos pendentes (o que falta resolver)\n"
        "- Onde exatamente a sessão parou\n\n"
        "Este resumo será usado para retomar a aventura em outra sessão. "
        "Seja factual e detalhado (não narrativo). Máximo 1000 palavras."
    )

    summary = await send_to_gemini(chat, summary_prompt, telegram_msg=update.message)

    # Gera título
    title_prompt = (
        "Crie um título CURTO (máximo 6 palavras) para esta sessão de RPG "
        "baseado nos eventos principais. Responda APENAS com o título, sem aspas."
    )
    title = await send_to_gemini(chat, title_prompt)
    title = title.strip().strip('"').strip("'")[:60]

    if save_session_log(chat_id, title, summary):
        await update.message.reply_text(
            f"✅ Sessão salva: *{title}*\n"
            f"Use /sessoes para ver todas e /cargarsessao ID para retomar.",
            parse_mode="Markdown"
        )
        await reply_safe(update.message, f"📝 *Resumo:*\n\n{summary}")
    else:
        await update.message.reply_text("❌ Erro ao salvar sessão.")


async def cmd_listar_sessoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    chat_id = update.effective_chat.id
    sessoes = load_session_logs(chat_id)

    if not sessoes:
        await update.message.reply_text("📚 Nenhuma sessão salva neste chat.")
        return

    lines = ["📚 *SESSÕES SALVAS:*\n"]
    for s in sessoes:
        data = s.get("created_at", "")[:10]
        lines.append(f"• ID *{s['id']}* — {s.get('title', '?')} ({data})")
    lines.append("\nUse /cargarsessao ID para carregar")
    await reply_safe(update.message, "\n".join(lines))


async def cmd_carregar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Carrega uma sessão salva e injeta o contexto no Gemini."""
    if not db:
        await update.message.reply_text("⚠️ Banco não configurado.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Use: /cargarsessao ID (ex: /cargarsessao 1)")
        return

    try:
        session_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Use /sessoes para ver os IDs.")
        return

    sessao = load_session_by_id(session_id)
    if not sessao:
        await update.message.reply_text("❌ Sessão não encontrada. Use /sessoes para ver os IDs.")
        return

    chat_id = update.effective_chat.id
    # Verifica se a sessão pertence a este chat
    if sessao.get("chat_id") != str(chat_id):
        await update.message.reply_text("❌ Esta sessão pertence a outro chat.")
        return

    # Reset e injeta contexto
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)

    await update.message.reply_text(
        f"📂 _Carregando sessão: {sessao.get('title', '?')}..._",
        parse_mode="Markdown"
    )

    inject_prompt = (
        f"CONTEXTO_SESSAO: O grupo está retomando uma aventura anterior.\n"
        f"Título da sessão: {sessao.get('title', '?')}\n\n"
        f"RESUMO COMPLETO DA SESSÃO ANTERIOR:\n{sessao.get('summary', '')}\n\n"
        f"Use este resumo como contexto absoluto. Os jogadores querem continuar "
        f"exatamente de onde pararam. Recapitule brevemente onde estavam e "
        f"o que estava acontecendo, e pergunte o que querem fazer agora."
    )

    text = await send_to_gemini(chat, inject_prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_contexto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite importar contexto de uma sessão externa (jogada fora do bot)."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    # Verifica se tem texto após /contexto
    contexto_text = user_message.replace("/contexto", "", 1).strip()

    if not contexto_text:
        await update.message.reply_text(
            "📎 *IMPORTAR CONTEXTO EXTERNO*\n\n"
            "Cole o resumo da sessão anterior junto com o comando.\n\n"
            "Exemplo:\n"
            "`/contexto Estávamos na estação orbital de Marte. "
            "O grupo é formado por Kira (Ven'y Assassina nv3) e "
            "Marcus (Terráqueo Soldado nv2). Acabamos de encontrar "
            "um Monólito ativado no porão da estação. Um pirata "
            "chamado Drex nos persegue.`\n\n"
            "Quanto mais detalhes, melhor o Mestre vai entender!",
            parse_mode="Markdown"
        )
        return

    # Reset e injeta
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)

    await update.message.reply_text("📎 _Absorvendo contexto..._", parse_mode="Markdown")

    inject_prompt = (
        f"CONTEXTO_SESSAO: O grupo está importando uma sessão que foi jogada FORA deste bot. "
        f"Absorva o seguinte contexto como se tivesse sido jogado aqui:\n\n"
        f"{contexto_text}\n\n"
        f"Com base neste contexto:\n"
        f"1. Confirme que entendeu os personagens, localização e situação\n"
        f"2. Recapitule brevemente os pontos principais\n"
        f"3. Pergunte se está tudo correto ou se querem ajustar algo\n"
        f"4. Quando confirmarem, continue a narrativa daquele ponto"
    )

    text = await send_to_gemini(chat, inject_prompt, telegram_msg=update.message)

    # Salva o contexto importado como sessão também
    if db:
        save_session_log(chat_id, "Sessão Importada", contexto_text)

    await reply_safe(update.message, text)


# ══════════════════════════════════════════════════════════
# HANDLERS — RESET E MENSAGENS
# ══════════════════════════════════════════════════════════

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    await update.message.reply_text(
        "🔄 Sessão resetada!\n"
        "💾 Fichas e sessões salvas continuam no banco.\n"
        "Use /carregar para ficha ou /cargarsessao para retomar aventura."
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
        logger.error(f"Erro: {e}")
        await update.message.reply_text("⚠️ Erro. Tente novamente em alguns segundos!")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Jogo
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

    # Ficha
    app.add_handler(CommandHandler("salvar", cmd_salvar))
    app.add_handler(CommandHandler("carregar", cmd_carregar))
    app.add_handler(CommandHandler("ficha", cmd_ficha))
    app.add_handler(CommandHandler("fichas", cmd_fichas))
    app.add_handler(CommandHandler("levelup", cmd_levelup))

    # Sessões
    app.add_handler(CommandHandler("salvarsessao", cmd_salvar_sessao))
    app.add_handler(CommandHandler("sessoes", cmd_listar_sessoes))
    app.add_handler(CommandHandler("cargarsessao", cmd_carregar_sessao))
    app.add_handler(CommandHandler("contexto", cmd_contexto))

    # Reset e mensagens
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    if WEBHOOK_URL:
        logger.info(f"🚀 Webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0", port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
        )
    else:
        logger.info("🚀 Polling (local)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
