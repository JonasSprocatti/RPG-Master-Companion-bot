"""
🌌 Passagem Sombria - RPG Master Bot
Criação de personagem 100% em código Python. IA só mestra.
"""
import os,json,logging,asyncio,random as rng
from datetime import datetime,timezone
from telegram import Update,InlineKeyboardButton as Btn,InlineKeyboardMarkup as KBD
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes
import google.generativeai as genai
from google.api_core import exceptions as gex
from supabase import create_client
from glossary import *

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",level=logging.INFO)
log=logging.getLogger(__name__)

TG=os.environ["TELEGRAM_TOKEN"];GK=os.environ["GEMINI_API_KEY"]
WH=os.environ.get("WEBHOOK_URL","");PT=int(os.environ.get("PORT",10000))
SU=os.environ.get("SUPABASE_URL","");SK=os.environ.get("SUPABASE_KEY","")
ADMIN=os.environ.get("ADMIN_ID","")

db=create_client(SU,SK) if SU and SK else None
RPG_FILE=os.path.join(os.path.dirname(__file__),"rpg_content.txt")
with open(RPG_FILE,"r",encoding="utf-8") as f: RPG=f.read()

SYSP=f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".
PAPEL: narrar aventuras, controlar NPCs, aplicar regras do d20, rolar dados EM JOGO.
ESTILO: PT-BR, sombrio, cinematográfico. Emojis temáticos: 💀⚔️🎲🛡️🚀🔥❤️🧠💎🌌⚡🩸👁️🗣️
Separadores ━━━ em combate. Status: ❤️ PV: 45/60 | 🛡️ CD: 15. Máx 800 palavras.
Formato rolagem: 🎲 1d20(14)+Mod(3)+Per(2)=19 vs CD15 → ✅

IMPORTANTE: A CRIAÇÃO de personagem é feita pelo BOT em código. Você NÃO cria fichas.
Quando receber CARREGAR_FICHA com JSON, use como ficha oficial do jogador.
Quando receber CONTEXTO_SESSAO, absorva e continue.

XP: Nv1→2:100|2→3:250|3→4:450|4→5:700|5→6:1000|6→7:1400|7→8:1900|8→9:2500|9→10:3200
Combate(dividido): Lacaio 15-25, Elite 40-60, Chefe 100-150, Super 200-300, Vazio +50%
História: Decisão 25-50, Missão 50-100, Puzzle 20-40, Criativo 10-20, RP 10-25, Lore 30-50
SEMPRE anuncie: ✨ *+XX XP* — (motivo). Level up SÓ em Descanso Longo.
Descanso Curto: kits, habilidades. Longo: TUDO + level. Se XP suficiente em DL: avise /levelup.

REFERÊNCIA: {RPG}"""

genai.configure(api_key=GK)
mdl=genai.GenerativeModel("gemini-2.5-flash-lite",system_instruction=SYSP,
    generation_config=genai.GenerationConfig(temperature=0.85,max_output_tokens=1500))

chats:dict={}; cstate:dict={}; XP_T={1:100,2:250,3:450,4:700,5:1000,6:1400,7:1900,8:2500,9:3200}

def gc(cid):
    if cid not in chats: chats[cid]=mdl.start_chat(history=[])
    return chats[cid]
def th(cid):
    if cid in chats and len(chats[cid].history)>60: chats[cid].history=chats[cid].history[-60:]

# ── DB ───────────────────────────────────────────────────
def sf(uid,un,cid,d):
    if not db: return False
    try: db.table("fichas").upsert({"user_id":str(uid),"chat_id":str(cid),"user_name":un,"character_name":d.get("nome","?"),"ficha":json.dumps(d,ensure_ascii=False),"updated_at":datetime.now(timezone.utc).isoformat()},on_conflict="user_id,chat_id").execute(); return True
    except Exception as e: log.error(f"sf:{e}"); return False
def lf(uid,cid):
    if not db: return None
    try: r=db.table("fichas").select("ficha").eq("user_id",str(uid)).eq("chat_id",str(cid)).execute(); return json.loads(r.data[0]["ficha"]) if r.data else None
    except: return None
def lfs(cid):
    if not db: return []
    try: r=db.table("fichas").select("user_id,user_name,character_name").eq("chat_id",str(cid)).execute(); return r.data or []
    except: return []
def df(uid,cid):
    if not db: return False
    try: db.table("fichas").delete().eq("user_id",str(uid)).eq("chat_id",str(cid)).execute(); return True
    except: return False
def ss(cid,t,s):
    if not db: return False
    try: db.table("sessoes").insert({"chat_id":str(cid),"title":t,"summary":s,"created_at":datetime.now(timezone.utc).isoformat()}).execute(); return True
    except: return False
def ls(cid):
    if not db: return []
    try: r=db.table("sessoes").select("id,title,created_at").eq("chat_id",str(cid)).order("created_at",desc=True).limit(10).execute(); return r.data or []
    except: return []
def lsi(sid):
    if not db: return None
    try: r=db.table("sessoes").select("*").eq("id",sid).execute(); return r.data[0] if r.data else None
    except: return None

# ── Gemini ───────────────────────────────────────────────
async def ask(chat,p,ret=4,m=None):
    for i in range(ret):
        try: return chat.send_message(p).text
        except gex.ResourceExhausted as e:
            if "per_day" in str(e): return "⚠️ Limite diário. Tente amanhã. Offline: /rolar /ficha /glossario"
            w=(2**i)*10+rng.uniform(0,5)
            if m and i<ret-1:
                try: await m.reply_text(f"⏳ _{w:.0f}s..._",parse_mode="Markdown")
                except: pass
            await asyncio.sleep(w)
        except Exception as e:
            log.error(f"G:{e}")
            if i==ret-1: raise
            await asyncio.sleep(5)
    return "⚠️ Mestre offline. Use /rolar /ficha /glossario."

async def rp(m,t):
    for p in([t[i:i+4000] for i in range(0,len(t),4000)] if len(t)>4000 else [t]):
        try: await m.reply_text(p,parse_mode="Markdown")
        except: await m.reply_text(p)

def kb(items,pfx,cols=2):
    bs=[Btn(v,callback_data=f"{pfx}:{k}") for k,v in items.items()]
    return KBD([bs[i:i+cols] for i in range(0,len(bs),cols)])

# ── Format Ficha ─────────────────────────────────────────
def ff(f):
    a=f.get("atributos",{})
    arms="\n".join(f"  ⚔️ {x}" for x in f.get("armas",[])) or "  —"
    per=", ".join(f"{PERICIAS_NOMES.get(k,k)}+{v}" for k,v in f.get("pericias",{}).items() if v) or "—"
    habs="\n".join(f"  🔹 {h}" for h in f.get("habilidades",[])) or "  —"
    return (f"🧑‍🚀 *{f.get('nome','???')}*\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🌌 {f.get('raca','?')} | ⚔️ {f.get('classe','?')} | 📜 {f.get('filosofia','?')}\n"
        f"📊 Nv{f.get('nivel',1)} | ✨ {f.get('xp',0)} XP\n━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ {f.get('pv_atual','?')}/{f.get('pv_max','?')} | 🛡️ CD{f.get('cd','?')} | 🧠 RAM {f.get('ram_atual','?')}/{f.get('ram_max','?')}\n"
        f"⚡ Init+{f.get('iniciativa',0)} | 🏃 {f.get('deslocamento',9)}m\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💪For:{a.get('forca','?')}({calc_mod(a.get('forca',8)):+d}) "
        f"⚡Des:{a.get('destreza','?')}({calc_mod(a.get('destreza',8)):+d}) "
        f"🩸Con:{a.get('constituicao','?')}({calc_mod(a.get('constituicao',8)):+d})\n"
        f"🧠Int:{a.get('inteligencia','?')}({calc_mod(a.get('inteligencia',8)):+d}) "
        f"🦉Sab:{a.get('sabedoria','?')}({calc_mod(a.get('sabedoria',8)):+d}) "
        f"🗣️Car:{a.get('carisma','?')}({calc_mod(a.get('carisma',8)):+d})\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 {per}\n🛠️ Habilidades:\n{habs}\n⚔️ Armas:\n{arms}\n"
        f"🛡️ {f.get('armadura','?')} | 🦾 {', '.join(f.get('implantes',[])) or '—'}\n"
        f"🎒 {', '.join(f.get('inventario',[])) or '—'}\n💎 {f.get('creditos',100)} CG")

# ══════════════════════════════════════════════════════════
# CRIAÇÃO DE PERSONAGEM — 100% ESTÁTICA
# ══════════════════════════════════════════════════════════

def roll_attrs():
    """Rola 2d8 sete vezes, descarta menor, retorna 6 valores ordenados desc."""
    rolls=[rng.randint(1,8)+rng.randint(1,8) for _ in range(7)]
    rolls.sort()
    dropped=rolls.pop(0)
    rolls.sort(reverse=True)
    return rolls,dropped

def roll_pv(raca_key,classe_key):
    """Rola 4d6, descarta menor, aplica ajuste racial + bônus classe."""
    dice=[rng.randint(1,6) for _ in range(4)]
    dice.sort()
    dropped=dice[0]
    total=sum(dice[1:])
    r=RACAS_STATS[raca_key]
    c=CLASSES_STATS[classe_key]
    ajuste=r["vida_ajuste"]
    bonus=c["pv"]
    pv=max(total+ajuste+bonus,1)
    return pv,dice,dropped,total,ajuste,bonus

def build_ficha(st):
    """Constrói a ficha completa a partir do estado de criação."""
    r=RACAS_STATS[st["raca"]]; c=CLASSES_STATS[st["classe"]]
    fl=FILOS_STATS[st["filosofia"]]

    # Atributos com raciais
    attrs={}
    for i,k in enumerate(ATTR_KEYS):
        base=st["atributos_base"][k]
        racial=r["mods"][i]
        attrs[k]=base+racial

    # PV
    pv=st["pv"]

    # CD
    des_mod=calc_mod(attrs["destreza"])
    arm=c["armadura"]
    if arm["tipo"]=="leve": cd=10+des_mod+arm["cd"]
    elif arm["tipo"]=="media": cd=10+min(des_mod,2)+arm["cd"]
    else: cd=10+arm["cd"]

    # Perícias (fixas da classe + raciais)
    pericias=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items():
            pericias[pk]=pericias.get(pk,0)+pv2

    # RAM
    tecno=pericias.get("tecnomancia",0)
    int_mod=calc_mod(attrs["inteligencia"])
    ram=max(1+int_mod+tecno//2,0)

    # Iniciativa
    init=des_mod
    if st["filosofia"]=="cod_sobrevivente": init+=2
    if st["classe"]=="batedor": init+=2

    # Deslocamento
    desloc=r.get("desloc",9)

    # Créditos
    cred=100
    if "creditos_extra" in c: cred+=c["creditos_extra"]

    # Equipamento
    equip=list(c.get("equip_fixo",[]))
    if st.get("equip_choice"):
        equip.insert(0,st["equip_choice"])

    # Habilidades
    habs=[f"{fl[0]}: {fl[1]}"]

    ficha={
        "nome":st.get("nome","Sem Nome"),"raca":r["nome"],"classe":c["nome"],
        "filosofia":fl[0],"nivel":1,"xp":0,
        "pv_atual":pv,"pv_max":pv,"cd":cd,
        "ram_atual":ram,"ram_max":ram,
        "iniciativa":init,"deslocamento":desloc,
        "atributos":attrs,"pericias":pericias,"habilidades":habs,
        "armas":[x for x in equip if any(w in x for w in ["1d","2d","3d"])],
        "armadura":f"{arm['nome']} (CD+{arm['cd']})",
        "inventario":[x for x in equip if not any(w in x for w in ["1d","2d","3d"])],
        "creditos":cred,"implantes":[],"notas":"",
    }
    return ficha

def build_creation_summary(st):
    """Monta o texto da ficha durante criação (pré-nome)."""
    r=RACAS_STATS[st["raca"]]; c=CLASSES_STATS[st["classe"]]
    fl=FILOS_STATS[st["filosofia"]]

    lines=["📋 *RESUMO DA FICHA*\n━━━━━━━━━━━━━━━━━━━━"]
    lines.append(f"🌌 Raça: *{r['nome']}* ({r['planeta']})")
    lines.append(f"⚔️ Classe: *{c['nome']}* (❤️+{c['pv']} PV)")
    lines.append(f"📜 Filosofia: *{fl[0]}*\n")

    # Atributos
    lines.append("📊 *ATRIBUTOS:*")
    for i,k in enumerate(ATTR_KEYS):
        base=st["atributos_base"][k]
        racial=r["mods"][i]
        final=base+racial
        mod=calc_mod(final)
        sign="+" if racial>=0 else ""
        lines.append(f"  {ATTR_LABELS[i]}: {base} {sign}{racial} racial = *{final}* (mod: {mod:+d})")

    # PV
    pv_d=st["pv_detail"]
    lines.append(f"\n❤️ *PV:* 🎲4d6{pv_d['dice']} descarta {pv_d['dropped']} = {pv_d['subtotal']} "
        f"{pv_d['ajuste']:+d} racial {pv_d['bonus']:+d} classe = *{st['pv']} PV*")

    # CD
    attrs={}
    for i,k in enumerate(ATTR_KEYS): attrs[k]=st["atributos_base"][k]+r["mods"][i]
    des_mod=calc_mod(attrs["destreza"])
    arm=c["armadura"]
    if arm["tipo"]=="leve": cd=10+des_mod+arm["cd"]
    elif arm["tipo"]=="media": cd=10+min(des_mod,2)+arm["cd"]
    else: cd=10+arm["cd"]
    lines.append(f"🛡️ *CD:* 10 + Des({des_mod:+d}) + {arm['nome']}(+{arm['cd']}) = *{cd}*")

    # RAM
    tecno=c["pericias"].get("tecnomancia",0)
    int_mod=calc_mod(attrs["inteligencia"])
    ram=max(1+int_mod+tecno//2,0)
    lines.append(f"🧠 *RAM:* 1 + Int({int_mod:+d}) + ½Tecno({tecno//2}) = *{ram}*")

    # Perícias
    pericias=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items(): pericias[pk]=pericias.get(pk,0)+pv2
    per_lines=[]
    for pk,pv2 in sorted(pericias.items(),key=lambda x:-x[1]):
        pa=PERICIAS_ATTR.get(pk,["?"])
        best_attr=max(pa,key=lambda a:calc_mod(attrs.get(a,8)))
        bmod=calc_mod(attrs.get(best_attr,8))
        total=pv2+bmod
        per_lines.append(f"{PERICIAS_NOMES.get(pk,pk)} +{total} ({ATTR_SHORT[ATTR_KEYS.index(best_attr)]})")
    lines.append(f"\n🎯 *Perícias:* {', '.join(per_lines)}")

    init=des_mod+(2 if st["filosofia"]=="cod_sobrevivente" or st["classe"]=="batedor" else 0)
    lines.append(f"⚡ Iniciativa: +{init} | 🏃 Desloc: {r.get('desloc',9)}m")

    # Equipamento
    lines.append(f"\n🛡️ Armadura: {arm['nome']} (+{arm['cd']}CD)")
    equip=list(c.get("equip_fixo",[]))
    if st.get("equip_choice"): equip.insert(0,st["equip_choice"])
    lines.append("🎒 Equipamento: "+", ".join(equip))
    cred=100+(c.get("creditos_extra",0))
    lines.append(f"💎 Créditos: {cred} CG")
    lines.append(f"\n📜 {fl[0]}: _{fl[1]}_")

    return "\n".join(lines)

# ── Menus ────────────────────────────────────────────────
MAIN_KB=KBD([
    [Btn("🚀 Iniciar Aventura",callback_data="m:jogo"),Btn("🧑‍🚀 Criar Personagem",callback_data="m:criar")],
    [Btn("📂 Carregar Ficha",callback_data="m:cficha"),Btn("📚 Retomar Sessão",callback_data="m:csess")],
    [Btn("📖 Glossário",callback_data="m:gloss"),Btn("❓ Comandos",callback_data="m:help")]])
GLOSS_KB=KBD([
    [Btn("🌌 Raças",callback_data="g:racas"),Btn("⚔️ Classes",callback_data="g:classes")],
    [Btn("🗡️ Armas Brancas",callback_data="g:ab"),Btn("🔫 Armas de Fogo",callback_data="g:af")],
    [Btn("🛡️ Armaduras",callback_data="g:ar"),Btn("🦾 Implantes",callback_data="g:im")],
    [Btn("🧠 Tecnomancia",callback_data="g:te"),Btn("🚀 Naves",callback_data="g:na")],
    [Btn("🛠️ Ferramentas",callback_data="g:fe"),Btn("🔧 Modificações",callback_data="g:mo")],
    [Btn("📜 Filosofias",callback_data="g:fi"),Btn("👾 Bestiário",callback_data="g:be")],
    [Btn("🔙 Menu",callback_data="m:back")]])
WELCOME="🌌 *TERMINAL DA CONFEDERAÇÃO* 🌌\n━━━━━━━━━━━━━━━━━━━━\n\n⚡ _Conexão estabelecida..._\n📡 _Aguardando instruções, viajante._"

# ══════════════════════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════════════════════

async def cmd_start(u,c): await u.message.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_reset(u,c):
    chats.pop(u.effective_chat.id,None)
    await u.message.reply_text("🔄 _Memória neural purgada._\n💾 Fichas/sessões permanecem.",reply_markup=MAIN_KB,parse_mode="Markdown")

async def cmd_help(u,c): await rp(u.message,"📡 *PROTOCOLOS*\n━━━━━━━━━━━━━━━━━━━━\n⚔️ /novojogo /criarpersonagem /rolar /regras\n💾 /salvar /carregar /ficha /fichas /levelup /deletarficha\n📚 /salvarsessao /sessoes /cargarsessao /contexto\n📖 /glossario\n🔧 /reset /ajuda")
async def cmd_glossario(u,c): await u.message.reply_text("📖 *BANCO DE DADOS*\n━━━━━━━━━━━━━━━━━━━━",reply_markup=GLOSS_KB,parse_mode="Markdown")
async def cmd_novojogo(u,c):
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    await u.message.reply_text("🌌 _Inicializando..._",parse_mode="Markdown")
    await rp(u.message,await ask(ch,"Novo jogo. Cena épica. Opções de onde começar. Conciso.",m=u.message))
async def cmd_criar(u,c):
    cstate[u.message.from_user.id]={"step":"raca","chat_id":u.effective_chat.id}
    await u.message.reply_text("🧑‍🚀 *PROTOCOLO DE RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n\n📋 Etapa 1/5: *Origem genética*",reply_markup=kb(RACAS_BTN,"r",2),parse_mode="Markdown")

async def cmd_rolar(u,c):
    a=c.args
    if not a: await u.message.reply_text("🎲 /rolar NdN"); return
    d=a[0].lower()
    try: n,s=d.split("d");n=int(n)if n else 1;s=int(s)
    except: await u.message.reply_text("❌ Formato inválido");return
    if n<1 or n>20 or s<1 or s>100: await u.message.reply_text("❌ Limites: 1-20d, 1-100 faces");return
    rs=[rng.randint(1,s)for _ in range(n)];t=sum(rs)
    cr=""
    if s==20 and n==1:
        if rs[0]==20:cr="\n\n🌟 *O COSMOS SE CURVA!*"
        elif rs[0]==1:cr="\n\n💀 *O VÁCUO RI...*"
    await rp(u.message,f"🎲 *{d.upper()}*\n{rs}\n*Total: {t}*{cr}")

async def cmd_regras(u,c): await rp(u.message,"📖 *MANUAL*\n━━━━━━━━━━━━━━━━━━━━\n🎲 1d20+Atrib+Per ≥ CD\n⚔️ Melee: dado+For | 🔫 Ranged: dado+Des\n🛡️ CD: 10+Des+Arm\n💥 20nat=Crítico | 💀 1nat=Falha\n❤️ 0PV=Testes Morte | 🔋 Pente:3t | 🧠 RAM:1+Int+½Tecno")

# ── Ficha ────────────────────────────────────────────────
async def cmd_salvar(u,c):
    if not db: return
    cid,uid,un=u.effective_chat.id,u.message.from_user.id,u.message.from_user.first_name or"?"
    ch=gc(cid)
    await u.message.reply_text("💾 _Transmitindo... aguarde._",parse_mode="Markdown")
    await asyncio.sleep(5)
    raw=await ask(ch,"EXPORT_FICHA: JSON puro da ficha atual. Sem markdown. Se não tem: NO_CHARACTER",ret=3,m=u.message)
    if "NO_CHARACTER" in raw or "⚠️" in raw: await u.message.reply_text("❌ Sem personagem ou API offline. Aguarde e tente.");return
    f=None
    try:
        c2=raw.strip()
        if c2.startswith("```"):c2=c2.split("\n",1)[-1]
        if c2.endswith("```"):c2=c2.rsplit("```",1)[0]
        f=json.loads(c2.strip())
    except:pass
    if not f: await u.message.reply_text("⚠️ Falha extração. Aguarde 1min, /salvar");return
    if sf(uid,un,cid,f): await u.message.reply_text(f"✅ *{f.get('nome','?')}* salvo!",parse_mode="Markdown")

async def cmd_carregar(u,c):
    if not db:return
    cid,uid,un=u.effective_chat.id,u.message.from_user.id,u.message.from_user.first_name or"?"
    f=lf(uid,cid)
    if not f: await u.message.reply_text("❌ Sem registro.");return
    ch=gc(cid)
    t=await ask(ch,f"CARREGAR_FICHA: {un} carregou:\n{json.dumps(f,ensure_ascii=False)}\nConfirme brevemente.",m=u.message)
    await rp(u.message,ff(f));await rp(u.message,t)

async def cmd_ficha(u,c):
    if not db:return
    f=lf(u.message.from_user.id,u.effective_chat.id)
    if not f: await u.message.reply_text("❌ Sem registro.");return
    await rp(u.message,ff(f))

async def cmd_fichas(u,c):
    if not db:return
    fs=lfs(u.effective_chat.id)
    if not fs: await u.message.reply_text("📋 Vazio.");return
    await rp(u.message,"📋 *REGISTROS:*\n"+"\n".join(f"• *{f.get('character_name','?')}* — {f.get('user_name','?')}" for f in fs))

async def cmd_deletar(u,c):
    if not db:return
    cid,uid=u.effective_chat.id,u.message.from_user.id
    adm=ADMIN and str(uid)==str(ADMIN)
    target=uid
    if c.args and adm:
        nm=" ".join(c.args).lower()
        for f in lfs(cid):
            if nm in f.get("character_name","").lower() or nm in f.get("user_name","").lower(): target=int(f["user_id"]);break
        else: await u.message.reply_text("❌ Não encontrado.");return
    elif c.args and not adm: await u.message.reply_text("❌ Apenas o Comandante.");return
    fi=lf(target,cid)
    if not fi: await u.message.reply_text("❌ Sem registro.");return
    if df(target,cid): await u.message.reply_text(f"🗑️ *{fi.get('nome','?')}* eliminado.",parse_mode="Markdown")

async def cmd_levelup(u,c):
    if not db:return
    cid,uid,un=u.effective_chat.id,u.message.from_user.id,u.message.from_user.first_name or"?"
    fi=lf(uid,cid)
    if not fi: await u.message.reply_text("❌ Sem ficha.");return
    nv,xp,nm=fi.get("nivel",1),fi.get("xp",0),fi.get("nome","?")
    if nv>=10: await u.message.reply_text("🌟 Nível máximo!");return
    xr=XP_T.get(nv,9999)
    if xp<xr: await u.message.reply_text(f"❌ *{nm}*: {xp}/{xr} XP (faltam {xr-xp})",parse_mode="Markdown");return
    ch=gc(cid)
    ck=await ask(ch,"Descanso Longo ativo? SIM ou NAO.",m=u.message)
    if "NAO" in ck.upper() or "NÃO" in ck.upper():
        await u.message.reply_text(f"🛏️ *{nm}* precisa Descanso Longo. XP:{xp}/{xr}✅",parse_mode="Markdown");return

    # Rola dado de vida em Python
    dado_nv=RACAS_STATS.get(next((k for k,v in RACAS_STATS.items() if v["nome"]==fi.get("raca","")),None) or "terraqueo",{}).get("dado_nv","1d8")
    faces=int(dado_nv.split("d")[1])
    roll_hp=rng.randint(1,faces)
    con_mod=calc_mod(fi.get("atributos",{}).get("constituicao",8))
    hp_gain=max(roll_hp+con_mod,1)
    new_pv=fi["pv_max"]+hp_gain

    txt=(f"⬆️ *{nm}* sobe para Nível {nv+1}!\n━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ PV: 🎲{dado_nv}={roll_hp} + Con({con_mod:+d}) = +{hp_gain} → *{new_pv} PV*\n")
    if (nv+1)%2==1 and nv+1>=3: txt+=f"🧠 +1 RAM (nível ímpar)\n"
    txt+=f"\n💪 Ganhou *+1 ponto de atributo* — onde investir?\n🎯 Ganhou *+1 ponto de perícia* — onde investir?\n\n_Responda na conversa e use /salvar para gravar._"

    fi["nivel"]=nv+1;fi["pv_max"]=new_pv;fi["pv_atual"]=new_pv
    if (nv+1)%2==1 and nv+1>=3: fi["ram_max"]=fi.get("ram_max",0)+1;fi["ram_atual"]=fi["ram_max"]
    sf(uid,un,cid,fi)

    # Injeta no Gemini
    ch2=gc(cid)
    await ask(ch2,f"CARREGAR_FICHA: {un} subiu para nv{nv+1}. Ficha:\n{json.dumps(fi,ensure_ascii=False)}\nEle ganhou +1 atributo e +1 perícia para distribuir. Ajude-o a escolher de forma épica.",m=u.message)
    await rp(u.message,txt)

# ── Sessões ──────────────────────────────────────────────
async def cmd_salvar_sessao(u,c):
    if not db:return
    cid=u.effective_chat.id;ch=gc(cid)
    if cid not in chats: await u.message.reply_text("❌ Sem sessão.");return
    await u.message.reply_text("📝 _Compilando..._",parse_mode="Markdown")
    s=await ask(ch,"RESUMO_SESSAO: Resuma TUDO factual. 1000 palavras max.",m=u.message)
    t=await ask(ch,"Título CURTO 6 palavras. Só título.")
    t=t.strip().strip('"')[:60]
    if ss(cid,t,s): await u.message.reply_text(f"✅ *{t}*",parse_mode="Markdown");await rp(u.message,s)

async def cmd_sessoes(u,c):
    if not db:return
    sl=ls(u.effective_chat.id)
    if not sl: await u.message.reply_text("📚 Vazio.");return
    await rp(u.message,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')} ({s.get('created_at','')[:10]})" for s in sl)+"\n\n/cargarsessao ID")

async def cmd_cargarsessao(u,c):
    if not db or not c.args: await u.message.reply_text("❌ /cargarsessao ID");return
    try:sid=int(c.args[0])
    except: await u.message.reply_text("❌ ID inválido.");return
    s=lsi(sid)
    if not s or s.get("chat_id")!=str(u.effective_chat.id): await u.message.reply_text("❌ Não encontrado.");return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Retomando '{s.get('title')}'.\n{s.get('summary')}\nRecapitule e pergunte o que fazer.",m=u.message))

async def cmd_contexto(u,c):
    txt=u.message.text.replace("/contexto","",1).strip()
    if not txt: await u.message.reply_text("📎 Cole o contexto: `/contexto Estávamos em Marte...`",parse_mode="Markdown");return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Importado.\n{txt}\nConfirme e recapitule.",m=u.message))
    if db:ss(cid,"📎 Importado",txt)

# ══════════════════════════════════════════════════════════
# CALLBACK ROUTER
# ══════════════════════════════════════════════════════════

async def on_cb(u:Update,c:ContextTypes.DEFAULT_TYPE):
    q=u.callback_query;await q.answer();d=q.data;m=q.message
    uid=q.from_user.id;cid=m.chat_id;un=q.from_user.first_name or"?"

    # Menu principal
    if d=="m:back" or d=="m:start": await m.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
    elif d=="m:jogo":
        chats.pop(cid,None);ch=gc(cid)
        await m.reply_text("🌌 _Inicializando..._",parse_mode="Markdown")
        await rp(m,await ask(ch,"Novo jogo. Cena épica. Opções. Conciso.",m=m))
    elif d=="m:criar":
        cstate[uid]={"step":"raca","chat_id":cid}
        await m.reply_text("🧑‍🚀 *RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n📋 Etapa 1/5: *Origem*",reply_markup=kb(RACAS_BTN,"r",2),parse_mode="Markdown")
    elif d=="m:cficha":
        f=lf(uid,cid)
        if not f: await m.reply_text("❌ Sem registro.");return
        ch=gc(cid)
        t=await ask(ch,f"CARREGAR_FICHA: {un}:\n{json.dumps(f,ensure_ascii=False)}\nConfirme.",m=m)
        await rp(m,ff(f));await rp(m,t)
    elif d=="m:csess":
        sl=ls(cid)
        if not sl: await m.reply_text("📚 Vazio.");return
        await rp(m,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')}" for s in sl)+"\n/cargarsessao ID")
    elif d=="m:gloss": await m.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")
    elif d=="m:help": await rp(m,"📡 /novojogo /criarpersonagem /rolar /regras /salvar /carregar /ficha /fichas /levelup /deletarficha /salvarsessao /sessoes /cargarsessao /contexto /glossario /reset")

    # Glossário
    elif d=="g:racas": await m.reply_text("🌌 *RAÇAS:*",reply_markup=kb(RACAS_BTN,"gr",2),parse_mode="Markdown")
    elif d=="g:classes": await m.reply_text("⚔️ *CLASSES:*",reply_markup=kb(CLASSES_BTN,"gc",2),parse_mode="Markdown")
    elif d.startswith("gr:"): await rp(m,RACAS_DETAIL.get(d[3:],"❌")); await m.reply_text("🔙",reply_markup=KBD([[Btn("🌌 Raças",callback_data="g:racas"),Btn("📖 Menu",callback_data="m:gloss")]]))
    elif d.startswith("gc:"): await rp(m,CLASSES_DETAIL.get(d[3:],"❌")); await m.reply_text("🔙",reply_markup=KBD([[Btn("⚔️ Classes",callback_data="g:classes"),Btn("📖 Menu",callback_data="m:gloss")]]))
    elif d=="g:ab": await rp(m,ARMAS_BRANCAS_TEXT)
    elif d=="g:af": await rp(m,ARMAS_FOGO_TEXT)
    elif d=="g:ar": await rp(m,ARMADURAS_TEXT)
    elif d=="g:im": await rp(m,IMPLANTES_TEXT)
    elif d=="g:fe": await rp(m,FERRAMENTAS_TEXT)
    elif d=="g:mo": await rp(m,MODIFICACOES_TEXT)
    elif d=="g:na": await rp(m,NAVES_TEXT)
    elif d=="g:fi": await rp(m,FILOSOFIAS_TEXT)
    elif d=="g:te": await m.reply_text("🧠 *TECNOMANCIA*",reply_markup=KBD([[Btn("🟢 Básicas",callback_data="gt:b")],[Btn("🟡 Injeções",callback_data="gt:i")],[Btn("🔴 Protocolos",callback_data="gt:p")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d=="gt:b": await rp(m,TECNO_BASICAS)
    elif d=="gt:i": await rp(m,TECNO_INJECOES)
    elif d=="gt:p": await rp(m,TECNO_PROTOCOLOS)
    elif d=="g:be": await m.reply_text("👾 *BESTIÁRIO*",reply_markup=KBD([[Btn("🌍 Planetas",callback_data="gb:p")],[Btn("🦎 Fauna",callback_data="gb:f")],[Btn("👾 Vazio",callback_data="gb:v")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d=="gb:p": await rp(m,BESTIARIO_PLANETAS)
    elif d=="gb:f": await rp(m,BESTIARIO_FAUNA)
    elif d=="gb:v": await rp(m,BESTIARIO_VAZIO)

    # Criação — Raça
    elif d.startswith("r:"):
        k=d[2:];cstate.setdefault(uid,{})
        cstate[uid].update({"step":"classe","raca":k,"chat_id":cid})
        await q.edit_message_text(f"✅ Origem: *{RACAS_BTN[k]}*\n\n📋 Etapa 2/5: *Especialização*",parse_mode="Markdown")
        await m.reply_text("⚔️ Selecione:",reply_markup=kb(CLASSES_BTN,"c",2))

    # Criação — Classe
    elif d.startswith("c:"):
        k=d[2:];cstate.setdefault(uid,{})
        cstate[uid].update({"step":"filosofia","classe":k})
        await q.edit_message_text(f"✅ Classe: *{CLASSES_BTN[k]}*\n\n📋 Etapa 3/5: *Código de conduta*\n🌌 Caminhos = misticismo | ⚙️ Códigos = pragmatismo",parse_mode="Markdown")
        await m.reply_text("📜 Selecione:",reply_markup=kb(FILOS_BTN,"f",2))

    # Criação — Filosofia → Rola atributos
    elif d.startswith("f:"):
        k=d[2:];st=cstate.setdefault(uid,{})
        st.update({"step":"attr_0","filosofia":k})
        vals,dropped=roll_attrs()
        st["rolled"]=vals; st["all_rolls"]=vals+[dropped]; st["dropped"]=dropped
        txt=(f"✅ Filosofia: *{FILOS_BTN[k]}*\n\n"
            f"📋 Etapa 4/5: *Calibração Neural*\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 Rolagem 2d8 ×7 (máx 16 por dado):\n"
            f"Resultados: {sorted(st['all_rolls'])}\n"
            f"❌ Descartado: {dropped}\n"
            f"✅ Disponíveis: *{vals}*\n\n"
            f"Agora distribua! Toque no valor para *{ATTR_LABELS[0]}*:")
        btns=[Btn(f"{v}",callback_data=f"av:{i}") for i,v in enumerate(vals)]
        await q.edit_message_text(txt,parse_mode="Markdown")
        await m.reply_text(f"Escolha para {ATTR_LABELS[0]}:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))

    # Criação — Atribuir valores sequencialmente
    elif d.startswith("av:"):
        idx=int(d[3:]);st=cstate.get(uid)
        if not st: return
        attr_i=int(st.get("step","attr_0").split("_")[1])
        vals=st["rolled"]
        chosen=vals[idx]
        st.setdefault("atributos_base",{})
        st["atributos_base"][ATTR_KEYS[attr_i]]=chosen
        vals.pop(idx)
        st["rolled"]=vals

        if attr_i<5:
            st["step"]=f"attr_{attr_i+1}"
            btns=[Btn(f"{v}",callback_data=f"av:{i}") for i,v in enumerate(vals)]
            await q.edit_message_text(f"✅ {ATTR_LABELS[attr_i]}: *{chosen}*\n\nEscolha para *{ATTR_LABELS[attr_i+1]}*:",parse_mode="Markdown")
            if btns:
                await m.reply_text(f"{ATTR_LABELS[attr_i+1]}:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))
            else:
                # Último valor automático
                st["atributos_base"][ATTR_KEYS[5]]=vals[0] if vals else chosen
                st["step"]="equip"
                await _finalize_attrs(m,uid)
        else:
            st["step"]="equip"
            await q.edit_message_text(f"✅ {ATTR_LABELS[5]}: *{chosen}*",parse_mode="Markdown")
            await _finalize_attrs(m,uid)

    # Criação — Escolha de arma
    elif d.startswith("eq:"):
        idx=int(d[3:]);st=cstate.get(uid)
        if not st:return
        choices=CLASSES_STATS[st["classe"]].get("equip_escolha",CLASSES_STATS[st["classe"]].get("equip_escolha_melee",[]))
        if choices: st["equip_choice"]=choices[0][idx]
        st["step"]="nome"
        await q.edit_message_text(f"✅ Arma: *{st.get('equip_choice','?')}*",parse_mode="Markdown")
        await m.reply_text("✏️ *Último passo!*\nDigite o *nome* do seu personagem:",parse_mode="Markdown")

async def _finalize_attrs(m,uid):
    """Chamado após todos os 6 atributos serem distribuídos."""
    st=cstate.get(uid)
    if not st:return

    # Rola PV
    pv,dice,dropped,subtotal,ajuste,bonus=roll_pv(st["raca"],st["classe"])
    st["pv"]=pv
    st["pv_detail"]={"dice":dice,"dropped":dropped,"subtotal":subtotal,"ajuste":ajuste,"bonus":bonus}

    # Verifica se tem escolha de equipamento
    cls=CLASSES_STATS[st["classe"]]
    choices=cls.get("equip_escolha",cls.get("equip_escolha_melee",[]))

    summary=build_creation_summary(st)
    await rp(m,summary)

    if choices:
        opts=choices[0]
        btns=[Btn(f"{opt}",callback_data=f"eq:{i}") for i,opt in enumerate(opts)]
        await m.reply_text("⚔️ Escolha sua arma:",reply_markup=KBD([[b] for b in btns]))
    else:
        st["step"]="nome"
        await m.reply_text("✏️ *Último passo!*\nDigite o *nome* do seu personagem:",parse_mode="Markdown")

# ── Mensagens de texto ───────────────────────────────────
async def on_msg(u:Update,c:ContextTypes.DEFAULT_TYPE):
    cid=u.effective_chat.id;txt=u.message.text;un=u.message.from_user.first_name or"?"
    uid=u.message.from_user.id
    if not txt:return

    # Verifica se está em criação (esperando nome)
    st=cstate.get(uid)
    if st and st.get("step")=="nome" and st.get("chat_id")==cid:
        st["nome"]=txt.strip()[:30]
        ficha=build_ficha(st)

        # Terráqueo: +4 atributos livres e +3 perícias livres
        # TODO: implementar com botões no futuro, por agora aplica automaticamente
        raca=RACAS_STATS.get(st["raca"],{})
        if "bonus_attr" in raca:
            # Distribui automaticamente nos 2 maiores
            sorted_attrs=sorted(ATTR_KEYS,key=lambda k:ficha["atributos"][k])
            for i in range(raca["bonus_attr"]):
                best=sorted_attrs[i%len(sorted_attrs)]
                ficha["atributos"][best]+=1

        await rp(u.message,f"✅ *{ficha['nome']}* — registro completo!\n━━━━━━━━━━━━━━━━━━━━")
        await rp(u.message,ff(ficha))

        if db and sf(uid,un,cid,ficha):
            await u.message.reply_text(f"💾 *{ficha['nome']}* salvo automaticamente!",parse_mode="Markdown")

        # Injeta no Gemini
        ch=gc(cid)
        await ask(ch,f"CARREGAR_FICHA: {un} criou:\n{json.dumps(ficha,ensure_ascii=False)}\nPersonagem pronto. Aguarde instruções.",m=u.message)

        del cstate[uid]
        await u.message.reply_text("🚀 Personagem pronto! Use /novojogo para iniciar uma aventura.",reply_markup=MAIN_KB)
        return

    # Conversa normal com IA
    ch=gc(cid)
    try:
        resp=await ask(ch,f"[Jogador: {un}]: {txt}",m=u.message)
        th(cid)
        await rp(u.message,resp)
    except Exception as e:
        log.error(f"Msg:{e}");await u.message.reply_text("⚠️ Interferência. Tente novamente.")

async def on_err(u,c): log.error(f"Err:{c.error}")

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
def main():
    app=Application.builder().token(TG).build()
    for cmd,fn in[("start",cmd_start),("reset",cmd_reset),("ajuda",cmd_help),("help",cmd_help),
        ("novojogo",cmd_novojogo),("criarpersonagem",cmd_criar),("rolar",cmd_rolar),("roll",cmd_rolar),
        ("regras",cmd_regras),("glossario",cmd_glossario),("salvar",cmd_salvar),("carregar",cmd_carregar),
        ("ficha",cmd_ficha),("fichas",cmd_fichas),("deletarficha",cmd_deletar),("levelup",cmd_levelup),
        ("salvarsessao",cmd_salvar_sessao),("sessoes",cmd_sessoes),("cargarsessao",cmd_cargarsessao),("contexto",cmd_contexto)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,on_msg))
    app.add_error_handler(on_err)
    if WH: app.run_webhook(listen="0.0.0.0",port=PT,url_path=TG,webhook_url=f"{WH}/{TG}")
    else: app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":main()
