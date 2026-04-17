"""
🌌 Passagem Sombria - RPG Master Bot
Telegram + Gemini AI + Supabase + Botões + Glossário completo
"""
import os, json, logging, asyncio, random as rng
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as KBD
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from supabase import create_client
from glossary import *

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────
TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 10000))
SB_URL = os.environ.get("SUPABASE_URL", "")
SB_KEY = os.environ.get("SUPABASE_KEY", "")
ADMIN_ID = os.environ.get("ADMIN_ID", "")

db = create_client(SB_URL, SB_KEY) if SB_URL and SB_KEY else None
if db: logger.info("✅ Supabase conectado")

# ── RPG Content + Model ──────────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f: RPG_CONTENT = f.read()

FICHA_FMT = '{"nome":"","raca":"","classe":"","filosofia":"","nivel":1,"xp":0,"pv_atual":0,"pv_max":0,"cd":0,"ram_atual":0,"ram_max":0,"iniciativa":0,"deslocamento":9,"atributos":{"forca":0,"destreza":0,"constituicao":0,"inteligencia":0,"sabedoria":0,"carisma":0},"pericias":{},"habilidades":[],"armas":[],"armadura":{},"inventario":[],"creditos":100,"implantes":[],"notas":""}'

SYSTEM_PROMPT = f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".
PAPEL: narrar aventuras, controlar NPCs, aplicar regras, rolar dados.

ESTILO: Português BR, tom sombrio/cinematográfico. Use emojis temáticos:
💀 perigo ⚔️ combate 🎲 rolagens 🛡️ defesa 🚀 naves 🔥 explosões
❤️ cura 🧠 tecnomancia 💎 loot 🌌 ambiente ⚡ ação 🩸 dano 👁️ percepção 🗣️ NPCs
Use separadores (━━━) em combate. Mostre status: ❤️ PV: 45/60 | 🛡️ CD: 15
Máximo 800 palavras por resposta.

REGRAS: d20 fielmente. Rolagem: 🎲 1d20(14)+Mod(3)+Per(2)=19 vs CD15 → ✅

═══ CRIAÇÃO DE PERSONAGEM ═══
PASSO 4 (após botões): Role 2d8 por 7 vezes, descarte menor valores dentre as 7 rolagens, mostre 6 ordenados. PARE, peça distribuição.
PASSOS 5-9 (AUTOMÁTICO — TUDO NUMA MENSAGEM após jogador distribuir):
- Aplique raciais, calcule PV (4d6 tira menor + ajuste racial + bônus classe), CD, RAM, perícias FIXAS da classe, Iniciativa
- Perícias dual-attribute: mostre atributo com maior bônus
- NÃO peça confirmação em cálculos automáticos
PASSO 10: Equipamento (PARE só se tiver escolha de arma)
PASSO 11: Pergunte o nome do personagem. SE, E SOMENTE SE, a raça do personagem for "Terráqueo", peça TAMBÉM para ele escolher +3 perícias livres. Para TODAS as outras raças, pergunte APENAS o nome e avance.
PASSO 12: Resumo + [FICHA_COMPLETA]

Perícias FIXAS da classe nv1. Level up: +1 em QUALQUER perícia (nova ou existente).

═══ XP ═══
Nv1→2:100|2→3:250|3→4:450|4→5:700|5→6:1000|6→7:1400|7→8:1900|8→9:2500|9→10:3200
Combate(dividido): Lacaio 15-25, Elite 40-60, Chefe 100-150, Super 200-300, Vazio +50%
História: Decisão 25-50, Missão 50-100, Puzzle 20-40, Criativo 10-20, RP 10-25, Lore 30-50
SEMPRE anuncie: ✨ *+XX XP* — (motivo). Level up SÓ em Descanso Longo.

═══ DESCANSOS ═══
Curto(1h): kits, habilidades. NÃO RAM/level. Longo(8h+comida+seguro): TUDO + level up.
Sugira descanso curto após combate difícil. Longo só em nave/base/dobra.
Se alguém tem XP suficiente em DL: "⬆️ [Nome] pode subir de nível! Use /levelup"

LEVEL UP: dado racial (d10 Marte/Plutão, d8 Terra/Vênus/Júpiter/Urano, d6 Netuno/Saturno/Mercúrio) +Con. +1 Atrib, +1 perícia, +1RAM ímpares.
MODOS: CRIAÇÃO=só ficha. JOGO=narrar. CONTEXTO=absorver e continuar.

EXPORT_FICHA → responda SÓ JSON puro: {FICHA_FMT}
[FICHA_COMPLETA] na última linha quando criação 100% completa.

REFERÊNCIA: {RPG_CONTENT}
"""

genai.configure(api_key=GEMINI_KEY)
mdl = genai.GenerativeModel("gemini-2.5-flash-lite", system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(temperature=0.85, max_output_tokens=1500))

MAX_HIST = 30
chats: dict = {}
creation_state: dict = {}
XP_TABLE = {1:100,2:250,3:450,4:700,5:1000,6:1400,7:1900,8:2500,9:3200}

RACAS_BTN = {
    "mercusys":"🔥 Mercusys","veny":"🌿 Ven'y","terraqueo":"🌍 Terráqueo",
    "marciano":"⚔️ Marciano","conjupitero":"⚙️ Conjupitero","sata":"💫 Sata",
    "urak":"❄️ Urak","proturno":"🧠 Proturno","infimor":"🪐 Infimor"}
CLASSES_BTN = {
    "estudioso":"📚 Estudioso","mecanico":"🔧 Mecânico","assassino":"🗡️ Assassino",
    "soldado":"🎖️ Soldado","starlord":"🌟 Starlord","franco_atirador":"🎯 Franco-At.",
    "musico":"🎵 Músico","espiao":"🕵️ Espião","catador":"♻️ Catador",
    "piloto":"✈️ Piloto","batedor":"👁️ Batedor","explorador":"🗺️ Explorador",
    "cinetico":"⚡ Cinético","prospector":"💼 Prospector","pirata":"☠️ Pirata"}
FILOS_BTN = {
    "cam_voz":"🗣️ Voz","cam_ressonancia":"🌀 Ressonância","cam_engrenagem":"⚙️ Engrenagem",
    "cam_espiral":"🧬 Espiral","cam_anel":"💍 Anel","cam_ocaso":"🌑 Ocaso",
    "cod_sobrevivente":"🏕️ Sobrevivente","cod_corporativo":"💰 Corporativo",
    "cod_cetico":"🧊 Cético","cod_fronteira":"🐺 Fronteira",
    "cod_caserna":"🛡️ Caserna","cod_viralata":"🃏 Vira-Lata"}

def get_chat(cid):
    if cid not in chats: chats[cid] = mdl.start_chat(history=[])
    return chats[cid]

def trim_hist(cid):
    if cid in chats and len(chats[cid].history)>MAX_HIST*2:
        chats[cid].history = chats[cid].history[-(MAX_HIST*2):]

# ── Supabase ─────────────────────────────────────────────
def save_ficha(uid,uname,cid,data):
    if not db: return False
    try:
        db.table("fichas").upsert({"user_id":str(uid),"chat_id":str(cid),"user_name":uname,
            "character_name":data.get("nome","?"),"ficha":json.dumps(data,ensure_ascii=False),
            "updated_at":datetime.now(timezone.utc).isoformat()},on_conflict="user_id,chat_id").execute()
        return True
    except Exception as e: logger.error(f"save_ficha: {e}"); return False

def load_ficha(uid,cid):
    if not db: return None
    try:
        r=db.table("fichas").select("ficha").eq("user_id",str(uid)).eq("chat_id",str(cid)).execute()
        return json.loads(r.data[0]["ficha"]) if r.data else None
    except Exception as e: logger.error(f"load_ficha: {e}"); return None

def list_fichas(cid):
    if not db: return []
    try:
        r=db.table("fichas").select("user_id,user_name,character_name").eq("chat_id",str(cid)).execute()
        return r.data or []
    except: return []

def delete_ficha(uid,cid):
    if not db: return False
    try: db.table("fichas").delete().eq("user_id",str(uid)).eq("chat_id",str(cid)).execute(); return True
    except: return False

def save_session(cid,title,summary):
    if not db: return False
    try: db.table("sessoes").insert({"chat_id":str(cid),"title":title,"summary":summary,"created_at":datetime.now(timezone.utc).isoformat()}).execute(); return True
    except: return False

def load_sessions(cid):
    if not db: return []
    try: r=db.table("sessoes").select("id,title,created_at").eq("chat_id",str(cid)).order("created_at",desc=True).limit(10).execute(); return r.data or []
    except: return []

def load_session_id(sid):
    if not db: return None
    try: r=db.table("sessoes").select("*").eq("id",sid).execute(); return r.data[0] if r.data else None
    except: return None

# ── Gemini + Helpers ─────────────────────────────────────
async def ask_gemini(chat,prompt,retries=4,msg=None):
    for i in range(retries):
        try: return chat.send_message(prompt).text
        except google_exceptions.ResourceExhausted as e:
            if "per_day" in str(e): return "⚠️ Limite diário atingido. Tente amanhã. Comandos offline funcionam: /rolar /ficha /glossario"
            w=(2**i)*10+rng.uniform(0,5)
            if msg and i<retries-1:
                try: await msg.reply_text(f"⏳ _Retentando em {w:.0f}s..._",parse_mode="Markdown")
                except: pass
            await asyncio.sleep(w)
        except Exception as e:
            logger.error(f"Gemini: {e}")
            if i==retries-1: raise
            await asyncio.sleep(5)
    return "⚠️ Mestre indisponível. Use comandos offline enquanto isso."

async def reply(msg,text):
    for part in [text[i:i+4000] for i in range(0,len(text),4000)] if len(text)>4000 else [text]:
        try: await msg.reply_text(part,parse_mode="Markdown")
        except: await msg.reply_text(part)

def parse_json(raw):
    c=raw.strip()
    if c.startswith("```"): c=c.split("\n",1)[-1]
    if c.endswith("```"): c=c.rsplit("```",1)[0]
    try: return json.loads(c.strip())
    except: return None

def format_ficha(f):
    a=f.get("atributos",{})
    arms="\n".join(f"  ⚔️ {x.get('nome','?')} ({x.get('dano','?')}) {x.get('efeito','')}" for x in f.get("armas",[])) or "  Nenhuma"
    impl=", ".join(f.get("implantes",[])) or "Nenhum"
    inv=", ".join(f.get("inventario",[])) or "Vazio"
    per=", ".join(f"{k} +{v}" for k,v in f.get("pericias",{}).items() if v) or "Nenhuma"
    habs="\n".join(f"  🔹 {h}" for h in f.get("habilidades",[])) or "  Nenhuma"
    arm=f.get("armadura",{});arm_n=arm.get("nome","?") if isinstance(arm,dict) else str(arm)
    return (f"🧑‍🚀 *{f.get('nome','???')}*\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🌌 {f.get('raca','?')} | ⚔️ {f.get('classe','?')} | 📜 {f.get('filosofia','?')}\n"
        f"📊 Nv{f.get('nivel',1)} | ✨ {f.get('xp',0)} XP\n━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ {f.get('pv_atual','?')}/{f.get('pv_max','?')} | 🛡️ CD{f.get('cd','?')} | 🧠 RAM {f.get('ram_atual','?')}/{f.get('ram_max','?')}\n"
        f"⚡ Init +{f.get('iniciativa',0)} | 🏃 {f.get('deslocamento',9)}m\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💪{a.get('forca','?')} ⚡{a.get('destreza','?')} 🩸{a.get('constituicao','?')} "
        f"🧠{a.get('inteligencia','?')} 🦉{a.get('sabedoria','?')} 🗣️{a.get('carisma','?')}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 {per}\n🛠️ Habilidades:\n{habs}\n⚔️ Armas:\n{arms}\n"
        f"🛡️ {arm_n} | 🦾 {impl}\n🎒 {inv}\n💎 {f.get('creditos',0)} CG")

def kb(items,prefix,cols=2):
    btns=[Btn(v,callback_data=f"{prefix}:{k}") for k,v in items.items()]
    return KBD([btns[i:i+cols] for i in range(0,len(btns),cols)])

# ── Menu Principal ───────────────────────────────────────
MAIN_MENU = KBD([
    [Btn("🚀 Iniciar Aventura",callback_data="m:jogo"),Btn("🧑‍🚀 Criar Personagem",callback_data="m:criar")],
    [Btn("📂 Carregar Ficha",callback_data="m:cficha"),Btn("📚 Retomar Sessão",callback_data="m:csess")],
    [Btn("📖 Glossário",callback_data="m:gloss"),Btn("❓ Comandos",callback_data="m:help")]])

WELCOME = ("🌌 *TERMINAL DA CONFEDERAÇÃO* 🌌\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "⚡ _Conexão estabelecida..._\n"
    "🛸 _Coordenadas do Sistema Solar carregadas._\n"
    "📡 _Aguardando instruções, viajante._\n\n"
    "O que deseja fazer?")

# ── Glossário Menu ───────────────────────────────────────
GLOSS_MENU = KBD([
    [Btn("🌌 Raças",callback_data="g:racas"),Btn("⚔️ Classes",callback_data="g:classes")],
    [Btn("🗡️ Armas Brancas",callback_data="g:abr"),Btn("🔫 Armas de Fogo",callback_data="g:afg")],
    [Btn("🛡️ Armaduras",callback_data="g:arm"),Btn("🦾 Implantes",callback_data="g:imp")],
    [Btn("🧠 Tecnomancia",callback_data="g:tecno"),Btn("🚀 Naves",callback_data="g:naves")],
    [Btn("🛠️ Ferramentas",callback_data="g:ferr"),Btn("🔧 Modificações",callback_data="g:mods")],
    [Btn("📜 Filosofias",callback_data="g:filos"),Btn("👾 Bestiário",callback_data="g:best")],
    [Btn("🔙 Menu Principal",callback_data="m:back")]])

TECNO_MENU = KBD([
    [Btn("🟢 Básicas (Nv1)",callback_data="gt:bas")],
    [Btn("🟡 Injeções (Nv2)",callback_data="gt:inj")],
    [Btn("🔴 Protocolos (Nv3)",callback_data="gt:pro")],
    [Btn("🔙 Glossário",callback_data="m:gloss")]])

BEST_MENU = KBD([
    [Btn("🌍 Por Planeta",callback_data="gb:plan")],
    [Btn("🦎 Fauna Alienígena",callback_data="gb:fauna")],
    [Btn("👾 Crias do Vazio",callback_data="gb:vazio")],
    [Btn("🔙 Glossário",callback_data="m:gloss")]])

# ══════════════════════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════════════════════

async def cmd_start(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME,reply_markup=MAIN_MENU,parse_mode="Markdown")

async def cmd_reset(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    chats.pop(update.effective_chat.id,None)
    await update.message.reply_text(
        "🔄 _Memória neural purgada..._\n💾 Fichas e sessões permanecem nos servidores.\n\n"
        "📡 _Terminal reiniciado. Aguardando instruções._",
        reply_markup=MAIN_MENU,parse_mode="Markdown")

async def cmd_help(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await reply(update.message,
        "📡 *PROTOCOLOS DO TERMINAL*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚔️ *Operações:*\n/novojogo /criarpersonagem\n/rolar 1d20 /regras\n\n"
        "💾 *Banco de Dados:*\n/salvar /carregar /ficha /fichas\n/levelup /deletarficha\n\n"
        "📚 *Registros de Missão:*\n/salvarsessao /sessoes /cargarsessao ID\n/contexto\n\n"
        "📖 *Arquivos:*\n/glossario — Consultar base de dados completa\n\n"
        "🔧 *Sistema:*\n/reset — Purgar memória neural\n/ajuda — Este protocolo")

async def cmd_glossario(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *BANCO DE DADOS DA CONFEDERAÇÃO*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "Selecione a categoria para consulta:",
        reply_markup=GLOSS_MENU,parse_mode="Markdown")

async def cmd_novojogo(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id; chats.pop(cid,None); chat=get_chat(cid)
    await update.message.reply_text("🌌 _Inicializando simulação..._",parse_mode="Markdown")
    t=await ask_gemini(chat,"Novo jogo. Cena de abertura épica com emojis. Opções de onde começar. Conciso.",msg=update.message)
    await reply(update.message,t)

async def cmd_criar(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    creation_state[update.message.from_user.id]={}
    await update.message.reply_text(
        "🧑‍🚀 *PROTOCOLO DE RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "📋 Etapa 1/4: Selecione sua *origem genética*\n\n"
        "Cada raça carrega o peso de seu planeta natal.\nEscolha com sabedoria, viajante:",
        reply_markup=kb(RACAS_BTN,"r",2),parse_mode="Markdown")

async def cmd_rolar(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    args=ctx.args
    if not args: await update.message.reply_text("🎲 Protocolo: /rolar NdN"); return
    d=args[0].lower()
    try: n,s=d.split("d"); n=int(n) if n else 1; s=int(s)
    except: await update.message.reply_text("❌ Formato inválido"); return
    if n<1 or n>20 or s<1 or s>100: await update.message.reply_text("❌ Limites: 1-20 dados, 1-100 faces"); return
    rolls=[rng.randint(1,s) for _ in range(n)]; total=sum(rolls)
    c=""
    if s==20 and n==1:
        if rolls[0]==20: c="\n\n🌟 *O COSMOS SE CURVA À SUA VONTADE!*"
        elif rolls[0]==1: c="\n\n💀 *O VÁCUO RI DA SUA OUSADIA...*"
    await reply(update.message,f"🎲 *{d.upper()}*\nResultados: {rolls}\n*Total: {total}*{c}")

async def cmd_regras(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await reply(update.message,
        "📖 *MANUAL DE SOBREVIVÊNCIA*\n━━━━━━━━━━━━━━━━━━━━\n"
        "🎲 Teste: 1d20 + Atributo + Perícia ≥ CD\n"
        "⚔️ Melee: dado + For | 🔫 Ranged: dado + Des\n"
        "🛡️ Defesa: 10 + Des + Armadura\n\n"
        "💥 20 nat = Crítico (dobra dados)\n"
        "💀 1 nat = Falha crítica (arma emperra)\n\n"
        "❤️ 0 PV = Testes de Morte (3 sucessos ou falhas)\n"
        "🔋 Pentes: 3 turnos de tiro | Rajada: 2t\n"
        "🧠 RAM: 1 + Int + ½Tecnomancia")

# ── Ficha ────────────────────────────────────────────────
async def cmd_salvar(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco offline."); return
    cid,uid,un=update.effective_chat.id,update.message.from_user.id,update.message.from_user.first_name or"?"
    chat=get_chat(cid)
    await update.message.reply_text("💾 _Transmitindo dados ao servidor... aguarde._",parse_mode="Markdown")
    await asyncio.sleep(5)
    raw=await ask_gemini(chat,"EXPORT_FICHA: JSON puro. Sem markdown. Se não tem personagem: NO_CHARACTER",retries=3,msg=update.message)
    if "NO_CHARACTER" in raw or "⚠️" in raw: await update.message.reply_text("❌ Sem personagem ativo. Use /criarpersonagem"); return
    ficha=parse_json(raw)
    if not ficha: await update.message.reply_text("⚠️ Falha na extração. Aguarde 1 min e tente /salvar"); return
    if save_ficha(uid,un,cid,ficha): await update.message.reply_text(f"✅ *{ficha.get('nome','?')}* — dados salvos nos servidores da Confederação.",parse_mode="Markdown")
    else: await update.message.reply_text("❌ Erro no servidor.")

async def cmd_carregar(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    cid,uid,un=update.effective_chat.id,update.message.from_user.id,update.message.from_user.first_name or"?"
    ficha=load_ficha(uid,cid)
    if not ficha: await update.message.reply_text("❌ Nenhum registro encontrado. Use /criarpersonagem + /salvar"); return
    chat=get_chat(cid)
    t=await ask_gemini(chat,f"CARREGAR_FICHA: {un} carregou:\n{json.dumps(ficha,ensure_ascii=False)}\nConfirme brevemente.",msg=update.message)
    await reply(update.message,format_ficha(ficha))
    await reply(update.message,t)

async def cmd_ficha(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    f=load_ficha(update.message.from_user.id,update.effective_chat.id)
    if not f: await update.message.reply_text("❌ Sem registro. Use /salvar"); return
    await reply(update.message,format_ficha(f))

async def cmd_fichas(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    fs=list_fichas(update.effective_chat.id)
    if not fs: await update.message.reply_text("📋 Nenhum registro neste canal."); return
    lines=["📋 *REGISTROS ATIVOS:*\n"]+[f"• *{f.get('character_name','?')}* — {f.get('user_name','?')}" for f in fs]
    await reply(update.message,"\n".join(lines))

async def cmd_deletar(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    cid,uid=update.effective_chat.id,update.message.from_user.id
    is_adm=ADMIN_ID and str(uid)==str(ADMIN_ID)
    args=ctx.args; target=uid
    if args and is_adm:
        name=" ".join(args).lower()
        for f in list_fichas(cid):
            if name in f.get("character_name","").lower() or name in f.get("user_name","").lower():
                target=int(f["user_id"]); break
        else: await update.message.reply_text("❌ Não encontrado. Use /fichas"); return
    elif args and not is_adm: await update.message.reply_text("❌ Apenas o Comandante pode deletar registros alheios."); return
    ficha=load_ficha(target,cid)
    if not ficha: await update.message.reply_text("❌ Sem registro."); return
    if delete_ficha(target,cid): await update.message.reply_text(f"🗑️ Registro de *{ficha.get('nome','?')}* eliminado dos servidores.",parse_mode="Markdown")

async def cmd_levelup(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    cid,uid,un=update.effective_chat.id,update.message.from_user.id,update.message.from_user.first_name or"?"
    ficha=load_ficha(uid,cid)
    if not ficha: await update.message.reply_text("❌ Sem registro. Use /salvar"); return
    nv,xp,nome=ficha.get("nivel",1),ficha.get("xp",0),ficha.get("nome","?")
    if nv>=10: await update.message.reply_text("🌟 *Lenda do Sistema* — nível máximo atingido!",parse_mode="Markdown"); return
    xp_req=XP_TABLE.get(nv,9999)
    if xp<xp_req:
        await update.message.reply_text(f"❌ *{nome}* — XP insuficiente.\n✨ {xp}/{xp_req} (faltam {xp_req-xp})\nContinue a missão, soldado.",parse_mode="Markdown"); return
    chat=get_chat(cid)
    chk=await ask_gemini(chat,"O grupo está em Descanso Longo? Responda SIM ou NAO.",msg=update.message)
    if "NAO" in chk.upper() or "NÃO" in chk.upper():
        await update.message.reply_text(f"🛏️ *{nome}* precisa de Descanso Longo para evoluir.\n✨ XP: {xp}/{xp_req} — pronto quando descansar.",parse_mode="Markdown"); return
    await update.message.reply_text(f"⬆️ _Evolução neural de {nome} em progresso..._",parse_mode="Markdown")
    t=await ask_gemini(chat,f"MODO CRIAÇÃO — LEVELUP:\nFicha:{json.dumps(ficha,ensure_ascii=False)}\n{nv}→{nv+1}. XP:{xp}/{xp_req}. DL ativo.\n"
        f"1.🎲 Role dado vida raça+Con, mostre etapas\n2.💪 +1 atributo — liste atuais, PERGUNTE\n"
        f"3.🎯 +1 perícia (qualquer) — liste atuais+sugestões, PERGUNTE\n4.🧠 Nv{nv+1} ímpar? +1RAM\n5.❤️ Cura total\nNarre épico. NÃO inicie aventura.",msg=update.message)
    await reply(update.message,t)
    ficha["nivel"]=nv+1; save_ficha(uid,un,cid,ficha)

# ── Sessões ──────────────────────────────────────────────
async def cmd_salvar_sessao(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    cid=update.effective_chat.id; chat=get_chat(cid)
    if cid not in chats or not chats[cid].history: await update.message.reply_text("❌ Sem sessão ativa."); return
    await update.message.reply_text("📝 _Compilando relatório de missão..._",parse_mode="Markdown")
    s=await ask_gemini(chat,"RESUMO_SESSAO: Resuma TUDO — jogadores, local, eventos, combates, itens, NPCs, ganchos, onde parou. Factual. 1000 palavras máx.",msg=update.message)
    t=await ask_gemini(chat,"Título CURTO (6 palavras máx) desta sessão. Só o título.")
    t=t.strip().strip('"')[:60]
    if save_session(cid,t,s):
        await update.message.reply_text(f"✅ Missão registrada: *{t}*",parse_mode="Markdown")
        await reply(update.message,f"📝 *Relatório:*\n\n{s}")

async def cmd_sessoes(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db: return
    ss=load_sessions(update.effective_chat.id)
    if not ss: await update.message.reply_text("📚 Sem registros de missão."); return
    lines=["📚 *REGISTROS DE MISSÃO:*\n"]+[f"• ID *{s['id']}* — {s.get('title','?')} ({s.get('created_at','')[:10]})" for s in ss]+["\n/cargarsessao ID para retomar"]
    await reply(update.message,"\n".join(lines))

async def cmd_cargar_sessao(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    if not db or not ctx.args: await update.message.reply_text("❌ Use: /cargarsessao ID"); return
    try: sid=int(ctx.args[0])
    except: await update.message.reply_text("❌ ID inválido."); return
    s=load_session_id(sid)
    if not s or s.get("chat_id")!=str(update.effective_chat.id): await update.message.reply_text("❌ Registro não encontrado ou de outro canal."); return
    cid=update.effective_chat.id; chats.pop(cid,None); chat=get_chat(cid)
    await update.message.reply_text(f"📂 _Restaurando: {s.get('title','?')}..._",parse_mode="Markdown")
    t=await ask_gemini(chat,f"CONTEXTO_SESSAO: Retomando.\nTítulo:{s.get('title')}\nResumo:{s.get('summary')}\nRecapitule com emojis, pergunte o que fazer.",msg=update.message)
    await reply(update.message,t)

async def cmd_contexto(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id; txt=update.message.text.replace("/contexto","",1).strip()
    if not txt:
        await update.message.reply_text("📎 *IMPORTAR DADOS EXTERNOS*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "Cole o contexto junto ao comando:\n\n`/contexto Estávamos em Marte. Kira é Ven'y Assassina nv3...`",parse_mode="Markdown"); return
    chats.pop(cid,None); chat=get_chat(cid)
    await update.message.reply_text("📎 _Processando dados externos..._",parse_mode="Markdown")
    t=await ask_gemini(chat,f"CONTEXTO_SESSAO: Importado de fora.\n{txt}\nConfirme entendimento, recapitule, pergunte se correto.",msg=update.message)
    if db: save_session(cid,"📎 Importado",txt)
    await reply(update.message,t)

# ══════════════════════════════════════════════════════════
# CALLBACKS (Botões)
# ══════════════════════════════════════════════════════════

async def on_callback(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); d=q.data; m=q.message
    uid=q.from_user.id; cid=m.chat_id; un=q.from_user.first_name or"?"

    # ── Menu principal ──
    if d=="m:back" or d=="m:start":
        await m.reply_text(WELCOME,reply_markup=MAIN_MENU,parse_mode="Markdown")
    elif d=="m:jogo":
        chats.pop(cid,None); chat=get_chat(cid)
        await m.reply_text("🌌 _Inicializando simulação..._",parse_mode="Markdown")
        t=await ask_gemini(chat,"Novo jogo. Cena de abertura épica. Opções de onde começar. Conciso.",msg=m)
        await reply(m,t)
    elif d=="m:criar":
        creation_state[uid]={}
        await m.reply_text("🧑‍🚀 *PROTOCOLO DE RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n\n📋 Etapa 1/4: *Origem genética*\n\nCada raça carrega o legado de seu planeta:",
            reply_markup=kb(RACAS_BTN,"r",2),parse_mode="Markdown")
    elif d=="m:cficha":
        f=load_ficha(uid,cid)
        if not f: await m.reply_text("❌ Sem registro. Inicie o Protocolo de Recrutamento."); return
        chat=get_chat(cid)
        t=await ask_gemini(chat,f"CARREGAR_FICHA: {un} carregou:\n{json.dumps(f,ensure_ascii=False)}\nConfirme brevemente.",msg=m)
        await reply(m,format_ficha(f)); await reply(m,t)
    elif d=="m:csess":
        ss=load_sessions(cid)
        if not ss: await m.reply_text("📚 Sem registros. Jogue e use /salvarsessao"); return
        lines=["📚 *REGISTROS DE MISSÃO:*\n"]+[f"• ID *{s['id']}* — {s.get('title','?')}" for s in ss]+["\n/cargarsessao ID"]
        await reply(m,"\n".join(lines))
    elif d=="m:gloss":
        await m.reply_text("📖 *BANCO DE DADOS DA CONFEDERAÇÃO*\n━━━━━━━━━━━━━━━━━━━━\nSelecione categoria:",reply_markup=GLOSS_MENU,parse_mode="Markdown")
    elif d=="m:help":
        await reply(m,"📡 *PROTOCOLOS:*\n/novojogo /criarpersonagem /rolar /regras\n/salvar /carregar /ficha /fichas /levelup /deletarficha\n/salvarsessao /sessoes /cargarsessao /contexto\n/glossario /reset /ajuda")

    # ── Glossário ──
    elif d=="g:racas":
        await m.reply_text("🌌 *RAÇAS DO SISTEMA*\nSelecione para detalhes:",reply_markup=kb(RACAS_BTN,"gr",2),parse_mode="Markdown")
    elif d=="g:classes":
        await m.reply_text("⚔️ *CLASSES DE ESPECIALIZAÇÃO*\nSelecione para detalhes:",reply_markup=kb(CLASSES_BTN,"gc",2),parse_mode="Markdown")
    elif d.startswith("gr:"):
        k=d[3:]; txt=RACAS_DETAIL.get(k,"❌ Não encontrado.")
        await reply(m,txt)
        await m.reply_text("🔙 Voltar:",reply_markup=KBD([[Btn("🌌 Raças",callback_data="g:racas"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d.startswith("gc:"):
        k=d[3:]; txt=CLASSES_DETAIL.get(k,"❌ Não encontrado.")
        await reply(m,txt)
        await m.reply_text("🔙 Voltar:",reply_markup=KBD([[Btn("⚔️ Classes",callback_data="g:classes"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:abr": await reply(m,ARMAS_BRANCAS_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:afg": await reply(m,ARMAS_FOGO_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:arm": await reply(m,ARMADURAS_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:imp": await reply(m,IMPLANTES_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:ferr": await reply(m,FERRAMENTAS_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:mods": await reply(m,MODIFICACOES_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:naves": await reply(m,NAVES_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:filos": await reply(m,FILOSOFIAS_TEXT); await m.reply_text("🔙",reply_markup=KBD([[Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:tecno":
        await m.reply_text("🧠 *TECNOMANCIA*\n━━━━━━━━━━━━━━━━━━━━\nRAM: 1+Mod.Int+½Tecno (+1 ímpares)\nSelecione o nível:",reply_markup=TECNO_MENU,parse_mode="Markdown")
    elif d=="gt:bas": await reply(m,TECNO_BASICAS); await m.reply_text("🔙",reply_markup=KBD([[Btn("🧠 Tecnomancia",callback_data="g:tecno"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="gt:inj": await reply(m,TECNO_INJECOES); await m.reply_text("🔙",reply_markup=KBD([[Btn("🧠 Tecnomancia",callback_data="g:tecno"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="gt:pro": await reply(m,TECNO_PROTOCOLOS); await m.reply_text("🔙",reply_markup=KBD([[Btn("🧠 Tecnomancia",callback_data="g:tecno"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="g:best":
        await m.reply_text("👾 *BESTIÁRIO*\n━━━━━━━━━━━━━━━━━━━━\nSelecione categoria:",reply_markup=BEST_MENU,parse_mode="Markdown")
    elif d=="gb:plan": await reply(m,BESTIARIO_PLANETAS); await m.reply_text("🔙",reply_markup=KBD([[Btn("👾 Bestiário",callback_data="g:best"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="gb:fauna": await reply(m,BESTIARIO_FAUNA); await m.reply_text("🔙",reply_markup=KBD([[Btn("👾 Bestiário",callback_data="g:best"),Btn("📖 Glossário",callback_data="m:gloss")]]))
    elif d=="gb:vazio": await reply(m,BESTIARIO_VAZIO); await m.reply_text("🔙",reply_markup=KBD([[Btn("👾 Bestiário",callback_data="g:best"),Btn("📖 Glossário",callback_data="m:gloss")]]))

    # ── Criação de personagem ──
    elif d.startswith("r:"):
        k=d[2:]; creation_state.setdefault(uid,{})
        creation_state[uid]["raca"]=k; creation_state[uid]["raca_nome"]=RACAS_BTN[k]
        await q.edit_message_text(f"✅ Origem: *{RACAS_BTN[k]}*\n\n📋 Etapa 2/4: *Especialização de combate*\nSua classe define seu papel na tripulação:",parse_mode="Markdown")
        await m.reply_text("⚔️ Selecione sua classe:",reply_markup=kb(CLASSES_BTN,"c",2))
    elif d.startswith("c:"):
        k=d[2:]; creation_state.setdefault(uid,{})
        creation_state[uid]["classe"]=k; creation_state[uid]["classe_nome"]=CLASSES_BTN[k]
        await q.edit_message_text(f"✅ Classe: *{CLASSES_BTN[k]}*\n\n📋 Etapa 3/4: *Código de conduta*\n🌌 Caminhos = fé e misticismo\n⚙️ Códigos = lógica e pragmatismo",parse_mode="Markdown")
        await m.reply_text("📜 Selecione sua filosofia:",reply_markup=kb(FILOS_BTN,"f",2))
    elif d.startswith("f:"):
        k=d[2:]; creation_state.setdefault(uid,{})
        creation_state[uid]["filosofia"]=k; creation_state[uid]["filosofia_nome"]=FILOS_BTN[k]
        st=creation_state[uid]
        await q.edit_message_text(f"✅ Filosofia: *{FILOS_BTN[k]}*\n\n📋 Etapa 4/4: *Calibração neural*\n🎲 O Mestre rolará seus dados...",parse_mode="Markdown")
        chat=get_chat(cid)
        t=await ask_gemini(chat,
            f"MODO CRIAÇÃO:\nRaça:{st.get('raca_nome','?')}\nClasse:{st.get('classe_nome','?')}\nFilosofia:{st.get('filosofia_nome','?')}\n\n"
            f"PASSO 4: Role 2d8 x7, descarte menor, mostre 6 ordenados. Lembre raciais. Peça distribuição. PARE.",msg=m)
        await reply(m,t)

# ── Mensagens livres ─────────────────────────────────────
async def handle_msg(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id; txt=update.message.text; un=update.message.from_user.first_name or"?"
    uid=update.message.from_user.id
    if not txt: return
    chat=get_chat(cid)
    try:
        resp=await ask_gemini(chat,f"[Jogador: {un}]: {txt}",msg=update.message)
        trim_hist(cid)
        if "[FICHA_COMPLETA]" in resp:
            resp=resp.replace("[FICHA_COMPLETA]","").strip()
            await reply(update.message,resp)
            if db:
                await update.message.reply_text("💾 _Salvando registro... aguarde 15s._",parse_mode="Markdown")
                await asyncio.sleep(15)
                raw=await ask_gemini(chat,"EXPORT_FICHA: JSON puro. Sem markdown.",retries=2)
                f=parse_json(raw)
                if f and save_ficha(uid,un,cid,f):
                    await update.message.reply_text(f"✅ *{f.get('nome','?')}* — registro salvo automaticamente!",parse_mode="Markdown")
                else: await update.message.reply_text("⚠️ Auto-save falhou. Aguarde 1 min e use /salvar")
        else: await reply(update.message,resp)
    except Exception as e:
        logger.error(f"Msg: {e}"); await update.message.reply_text("⚠️ Interferência no sinal. Tente novamente.")

async def on_error(update,ctx): logger.error(f"Erro: {ctx.error}")

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
def main():
    app=Application.builder().token(TG_TOKEN).build()
    for cmd,fn in [("start",cmd_start),("reset",cmd_reset),("ajuda",cmd_help),("help",cmd_help),
        ("novojogo",cmd_novojogo),("criarpersonagem",cmd_criar),("rolar",cmd_rolar),("roll",cmd_rolar),
        ("regras",cmd_regras),("glossario",cmd_glossario),("salvar",cmd_salvar),("carregar",cmd_carregar),
        ("ficha",cmd_ficha),("fichas",cmd_fichas),("deletarficha",cmd_deletar),("levelup",cmd_levelup),
        ("salvarsessao",cmd_salvar_sessao),("sessoes",cmd_sessoes),("cargarsessao",cmd_cargar_sessao),("contexto",cmd_contexto)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,handle_msg))
    app.add_error_handler(on_error)
    if WEBHOOK_URL:
        logger.info(f"🚀 {WEBHOOK_URL}")
        app.run_webhook(listen="0.0.0.0",port=PORT,url_path=TG_TOKEN,webhook_url=f"{WEBHOOK_URL}/{TG_TOKEN}")
    else:
        logger.info("🚀 Polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
