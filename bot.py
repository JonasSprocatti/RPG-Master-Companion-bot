"""
🌌 Passagem Sombria v2.2 — RPG Master Companion Bot
Arquitetura: Bot = lógica/estado/DB | IA = narração
Interceptor: Bot parseia respostas da IA para atualizar estado em tempo real.
"""
import os,json,logging,asyncio,random as rng,re,unicodedata
from datetime import datetime,timezone
from telegram import Update,InlineKeyboardButton as Btn,InlineKeyboardMarkup as KBD
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes
import google.generativeai as genai
from google.api_core import exceptions as gex
from supabase import create_client
from glossary import (ATTR_KEYS, ATTR_LABELS, ATTR_SHORT, PERICIAS_ATTR, PERICIAS_NOMES, calc_mod,
    RACAS_BTN, CLASSES_BTN, FILOS_BTN,
    ARMAS_BRANCAS_TEXT, ARMAS_FOGO_TEXT, ARMADURAS_TEXT, FERRAMENTAS_TEXT,
    IMPLANTES_TEXT, NAVES_TEXT, MODIFICACOES_TEXT, FILOSOFIAS_TEXT,
    TECNO_BASICAS, TECNO_INJECOES, TECNO_PROTOCOLOS,
    BESTIARIO_PLANETAS, BESTIARIO_FAUNA, BESTIARIO_VAZIO)
import data_loader as DL

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",level=logging.INFO)
log=logging.getLogger(__name__)

TG=os.environ["TELEGRAM_TOKEN"];GK=os.environ["GEMINI_API_KEY"]
WH=os.environ.get("WEBHOOK_URL","");PT=int(os.environ.get("PORT",10000))
SU=os.environ.get("SUPABASE_URL","");SK=os.environ.get("SUPABASE_KEY","")
ADMIN=os.environ.get("ADMIN_ID","")

db=create_client(SU,SK) if SU and SK else None

RPG_FILE=os.path.join(os.path.dirname(__file__),"rpg_content.txt")
with open(RPG_FILE,"r",encoding="utf-8") as f: RPG=f.read()

XP_T={1:100,2:250,3:450,4:700,5:1000,6:1400,7:1900,8:2500,9:3200}

def _norm(s):
    """Normaliza string para matching: remove acentos, lowercase."""
    return unicodedata.normalize("NFKD",s.lower()).encode("ascii","ignore").decode()

SYSP=f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".
Setting: nosso Sistema Solar. Use como pilar narrativo.
PAPEL: narrar aventuras, NPCs, regras d20, rolar dados EM JOGO.
ESTILO: PT-BR, sombrio. Emojis: 💀⚔️🎲🛡️🚀🔥❤️🧠💎🌌⚡🩸👁️🗣️
━━━ em combate. Status: ❤️ PV:45/60 | 🛡️ CD:15. Máx 800 palavras.
Rolagem: 🎲 1d20(14)+Mod(3)+Per(2)=19 vs CD15 → ✅

🛑 REGRA DE OURO - AGÊNCIA DOS JOGADORES:
- NUNCA tome decisões, declare ações, movimente ou crie diálogos para os PCs.
- Você apenas descreve o ambiente, controla NPCs e narra consequências.
- Sempre termine passando a bola (ex: "O que vocês fazem?").

🎲 ROLAGENS DE DADOS:
- Sempre que um jogador tentar ação com risco, NÃO narre resultado imediatamente.
- Pare e PEÇA O TESTE (ex: "Faça 1d20 + Destreza + Furtividade contra CD 15").
- Aguarde o jogador rolar com o bot antes de narrar consequência.

REGRAS DE TECNOMANCIA (RAM & SCRIPTS):
- RAM Máxima = 1 + Mod.Int + (Tecnomancia//2) + (Nível ímpar = +1). DL recupera RAM.
- Scripts Conhecidos: Nível + Tecnomancia (Mínimo 3).
- OVERCLOCK (Sem RAM): Sofre 1d6 Psíquico por Ponto faltante. Falha Crítica(1): falha+dano+Atordoado.

REGRAS DE IMPLANTES:
- Limite Seguro = max(2 + Mod.Con, 1).
- 1º acima: -1d6 PV Máx permanente, Desvantagem Persuasão/Enganação.
- 2º acima: Falha crítica em 1-2, causa 1d6 Elétrico + Atordoamento.
- 3º acima: Colapso do sistema nervoso = morte.

CRIAÇÃO DE FICHAS É FEITA PELO BOT. VOCÊ NÃO CRIA FICHAS.
Quando receber FICHAS_ATIVAS, use como estado oficial.
Quando receber CONTEXTO_SESSAO, absorva e continue.

═══ TAGS DE ESTADO (OBRIGATÓRIO) ═══
Sempre que narração causar mudança de estado, INCLUA tags NO FINAL:
[XP:valor:alvo:motivo] — ex: [XP:25:todos:Derrotou pirata]
[HP:valor:alvo] — ex: [HP:-5:Jonas] (dano) [HP:8:Maria] (cura)
[ITEM_ADD:nome:alvo] — ex: [ITEM_ADD:Pistola Laser:Jonas]
[ITEM_DEL:nome:alvo] — ex: [ITEM_DEL:Granada Fumaça:Maria]
[CG:valor:alvo] — ex: [CG:-100:Jonas] [CG:500:todos]
[RAM:valor:alvo] — ex: [RAM:-2:Jonas]
[TECNO_ADD:id_script:alvo] — ex: [TECNO_ADD:firewall:Jonas] (aprendeu script)
[TECNO_DEL:id_script:alvo] — ex: [TECNO_DEL:ping:Jonas] (perdeu script)
[IMPL:id_implante:alvo] — ex: [IMPL:olho:Jonas] (instalou implante)
[ATTR:atributo:valor:alvo] — ex: [ATTR:forca:+1:Jonas] (bônus/penalidade permanente)
[PER:pericia:valor:alvo] — ex: [PER:furtividade:+1:Jonas] (ganhou proficiência)
"alvo" = nome personagem ou "todos". Bot remove tags antes de mostrar.
NUNCA omita tags quando houver mudança. XP SEMPRE usa tag.
IDs de scripts: ping, choque, query, bateria, scanner, jammer, glitch, trava, rollback, firewall,
  travar_arma, curto_arm, hack_motor, ejetar_pente, cegueira, drenar, sobrecarga, desativar, loop, torreta,
  hack_nav, apagao, inverter, reator, marionete, emp, ejetar_piloto, reparo_nave, formatar, gravidade
IDs de implantes: chip_ram, olho, interface_nav, tradutor, mira, placas, coracao, filtro, adrenalina, bateria_int,
  braco, estabilizador, mantis, pernas, ancoras

REFERÊNCIA: {RPG}"""

genai.configure(api_key=GK)
mdl=genai.GenerativeModel("gemini-2.5-flash-lite",system_instruction=SYSP,
    generation_config=genai.GenerationConfig(temperature=0.85,max_output_tokens=1500))

chats:dict={};cstate:dict={}

def gc(cid):
    if cid not in chats: chats[cid]=mdl.start_chat(history=[])
    return chats[cid]
def th(cid):
    if cid in chats and len(chats[cid].history)>60: chats[cid].history=chats[cid].history[-60:]

# ══════ DATABASE ══════

def db_create_ficha(uid,un,cid,data):
    if not db: return None
    try:
        r=db.table("fichas").insert({"user_id":str(uid),"chat_id":str(cid),"user_name":un,
            "nome":data.get("nome","?"),"raca":data.get("raca",""),"classe":data.get("classe",""),
            "filosofia":data.get("filosofia",""),"nivel":data.get("nivel",1),"xp":data.get("xp",0),
            "pv_atual":data.get("pv_atual",0),"pv_max":data.get("pv_max",0),
            "cd":data.get("cd",10),"ram_atual":data.get("ram_atual",0),"ram_max":data.get("ram_max",0),
            "iniciativa":data.get("iniciativa",0),"deslocamento":data.get("deslocamento",9),
            "creditos":data.get("creditos",100),
            "atributos":json.dumps(data.get("atributos",{})),
            "pericias":json.dumps(data.get("pericias",{})),
            "habilidades":json.dumps(data.get("habilidades",[])),
            "tecnomancias":json.dumps(data.get("tecnomancias",[])),
            "armas":json.dumps(data.get("armas",[])),
            "armadura":data.get("armadura",""),
            "inventario":json.dumps(data.get("inventario",[])),
            "implantes":json.dumps(data.get("implantes",[])),
        }).execute()
        return r.data[0]["id"] if r.data else None
    except Exception as e: log.error(f"db_create:{e}"); return None

def db_update_ficha(fid,updates):
    if not db: return False
    try:
        clean={}
        for k,v in updates.items():
            clean[k]=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
        clean["updated_at"]=datetime.now(timezone.utc).isoformat()
        db.table("fichas").update(clean).eq("id",fid).execute();return True
    except Exception as e: log.error(f"db_update:{e}"); return False

def db_get_ficha(fid):
    if not db: return None
    try:
        r=db.table("fichas").select("*").eq("id",fid).execute()
        if r.data:
            row=r.data[0]
            for k in["atributos","pericias","habilidades","tecnomancias","armas","inventario","implantes"]:
                if k in row and isinstance(row[k],str):
                    try: row[k]=json.loads(row[k])
                    except: pass
            return row
        return None
    except: return None

def db_list_fichas(uid,cid):
    if not db: return []
    try: r=db.table("fichas").select("id,nome,raca,classe,nivel,xp").eq("user_id",str(uid)).eq("chat_id",str(cid)).execute(); return r.data or []
    except: return []

def db_list_fichas_chat(cid):
    if not db: return []
    try: r=db.table("fichas").select("id,user_id,user_name,nome,raca,classe,nivel").eq("chat_id",str(cid)).execute(); return r.data or []
    except: return []

def db_delete_ficha(fid):
    if not db: return False
    try: db.table("fichas").delete().eq("id",fid).execute(); return True
    except: return False

def db_set_active(uid,cid,fid):
    if not db: return False
    try:
        db.table("fichas_ativas").upsert({"user_id":str(uid),"chat_id":str(cid),"ficha_id":fid,
            "activated_at":datetime.now(timezone.utc).isoformat()},on_conflict="user_id,chat_id").execute();return True
    except Exception as e: log.error(f"set_active:{e}"); return False

def db_get_active(uid,cid):
    if not db: return None
    try:
        r=db.table("fichas_ativas").select("ficha_id").eq("user_id",str(uid)).eq("chat_id",str(cid)).execute()
        return db_get_ficha(r.data[0]["ficha_id"]) if r.data else None
    except: return None

def db_get_active_id(uid,cid):
    if not db: return None
    try:
        r=db.table("fichas_ativas").select("ficha_id").eq("user_id",str(uid)).eq("chat_id",str(cid)).execute()
        return r.data[0]["ficha_id"] if r.data else None
    except: return None

def db_get_all_active(cid):
    """Retorna fichas ativas do chat. Otimizado: busca IDs de uma vez."""
    if not db: return []
    try:
        r=db.table("fichas_ativas").select("ficha_id").eq("chat_id",str(cid)).execute()
        if not r.data: return []
        ids=[row["ficha_id"] for row in r.data]
        r2=db.table("fichas").select("*").in_("id",ids).execute()
        fichas=[]
        for row in (r2.data or []):
            for k in["atributos","pericias","habilidades","tecnomancias","armas","inventario","implantes"]:
                if k in row and isinstance(row[k],str):
                    try: row[k]=json.loads(row[k])
                    except: pass
            fichas.append(row)
        return fichas
    except Exception as e: log.error(f"all_active:{e}"); return []

def db_save_session(cid,t,s):
    if not db: return False
    try: db.table("sessoes").insert({"chat_id":str(cid),"title":t,"summary":s}).execute(); return True
    except: return False
def db_list_sessions(cid):
    if not db: return []
    try: r=db.table("sessoes").select("id,title,created_at").eq("chat_id",str(cid)).order("created_at",desc=True).limit(10).execute(); return r.data or []
    except: return []
def db_get_session(sid):
    if not db: return None
    try: r=db.table("sessoes").select("*").eq("id",sid).execute(); return r.data[0] if r.data else None
    except: return None

# ══════ INTERCEPTOR (FIX: case-insensitive + accent-insensitive) ══════

STATE_RE=re.compile(r'\[(XP|HP|ITEM_ADD|ITEM_DEL|CG|RAM|TECNO_ADD|TECNO_DEL|IMPL|ATTR|PER):([^\]]+)\]')

async def intercept_and_sync(text,cid,msg=None):
    if not db: return text
    changes=STATE_RE.findall(text)
    if not changes: return text
    actives=db_get_all_active(cid)
    # FIX: Build lookup with normalized names AND original names
    nm2f={}
    for f in actives:
        nome=f.get("nome","")
        nm2f[nome.lower()]=f
        nm2f[_norm(nome)]=f  # accent-insensitive
    notifs=[]
    for tt,params in changes:
        parts=[p.strip() for p in params.split(":")]
        try:
            alvo_raw=parts[1].strip() if len(parts)>=2 else ""
            alvo=alvo_raw.lower()
            alvo_n=_norm(alvo_raw)
            def _resolve(alvo,alvo_n):
                if alvo=="todos": return list(set(f["id"] for f in nm2f.values())), True
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                return ([f] if f else []), False
            if tt=="XP" and len(parts)>=3:
                val,motivo=int(parts[0]),parts[2]
                targets,is_all=_resolve(alvo,alvo_n)
                if is_all:
                    # targets é lista de IDs, preciso fichas
                    tgts=list({id(f):f for f in nm2f.values()}.values())  # unique fichas
                    xe=val//(len(tgts) or 1)
                else:
                    tgts=targets; xe=val
                for f in tgts:
                    nx=f.get("xp",0)+xe;db_update_ficha(f["id"],{"xp":nx})
                    nv=f.get("nivel",1);xr=XP_T.get(nv,9999)
                    lm=f" ⬆️ /levelup!" if nx>=xr else ""
                    notifs.append(f"✨ +{xe}XP {f.get('nome','?')} ({nx}/{xr}){lm}")
            elif tt=="HP" and len(parts)>=2:
                val=int(parts[0])
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    nh=max(0,min(f.get("pv_atual",0)+val,f.get("pv_max",1)));db_update_ficha(f["id"],{"pv_atual":nh})
                    notifs.append(f"{'💚' if val>0 else '🩸'} {f.get('nome','?')}: {val:+d}PV → ❤️{nh}/{f.get('pv_max','?')}")
            elif tt=="ITEM_ADD" and len(parts)>=2:
                item=parts[0]
                targets,is_all=_resolve(alvo,alvo_n)
                tgts=list({id(f):f for f in nm2f.values()}.values()) if is_all else targets
                for f in tgts:
                    inv=list(f.get("inventario",[]));inv.append(item);db_update_ficha(f["id"],{"inventario":inv})
                    notifs.append(f"🎒 {f.get('nome','?')} +{item}")
            elif tt=="ITEM_DEL" and len(parts)>=2:
                item=parts[0]
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    inv=list(f.get("inventario",[]));
                    if item in inv:inv.remove(item)
                    db_update_ficha(f["id"],{"inventario":inv})
                    notifs.append(f"🎒 {f.get('nome','?')} -{item}")
            elif tt=="CG" and len(parts)>=2:
                val=int(parts[0])
                targets,is_all=_resolve(alvo,alvo_n)
                tgts=list({id(f):f for f in nm2f.values()}.values()) if is_all else targets
                for f in tgts:
                    nc=max(0,f.get("creditos",0)+val);db_update_ficha(f["id"],{"creditos":nc})
                    notifs.append(f"{'💎' if val>0 else '💸'} {f.get('nome','?')}: {val:+d}CG → {nc}")
            elif tt=="RAM" and len(parts)>=2:
                val=int(parts[0])
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    nr=max(0,min(f.get("ram_atual",0)+val,f.get("ram_max",0)));db_update_ficha(f["id"],{"ram_atual":nr})
            elif tt=="TECNO_ADD" and len(parts)>=2:
                script_id=parts[0].strip().lower()
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and script_id in DL.TECNO_SCRIPTS:
                    tecno=list(f.get("tecnomancias",[]) or [])
                    if script_id not in tecno:
                        tecno.append(script_id);db_update_ficha(f["id"],{"tecnomancias":tecno})
                        notifs.append(f"🧠 {f.get('nome','?')} aprendeu: *{DL.TECNO_SCRIPTS[script_id]['nome']}*")
            elif tt=="TECNO_DEL" and len(parts)>=2:
                script_id=parts[0].strip().lower()
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    tecno=list(f.get("tecnomancias",[]) or [])
                    if script_id in tecno: tecno.remove(script_id);db_update_ficha(f["id"],{"tecnomancias":tecno})
                    notifs.append(f"🧠 {f.get('nome','?')} perdeu script: {script_id}")
            elif tt=="IMPL" and len(parts)>=2:
                impl_id=parts[0].strip().lower()
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and impl_id in DL.IMPLANTES_DATA:
                    impl=list(f.get("implantes",[]) or []);imp_data=DL.IMPLANTES_DATA[impl_id]
                    impl.append(imp_data["nome"]);ups={"implantes":impl}
                    # Aplica mecânica do implante
                    mec=imp_data.get("mecanica",{})
                    if "ram_max" in mec: ups["ram_max"]=f.get("ram_max",0)+mec["ram_max"];ups["ram_atual"]=ups["ram_max"]
                    if "cd" in mec: ups["cd"]=f.get("cd",10)+mec["cd"]
                    if "pv_max" in mec: ups["pv_max"]=f.get("pv_max",0)+mec["pv_max"];ups["pv_atual"]=f.get("pv_atual",0)+mec["pv_max"]
                    db_update_ficha(f["id"],ups)
                    notifs.append(f"🦾 {f.get('nome','?')} instalou: *{imp_data['nome']}*")
            elif tt=="ATTR" and len(parts)>=3:
                attr_key=parts[0].strip().lower()
                val=int(parts[1])
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and attr_key in ATTR_KEYS:
                    a=dict(f.get("atributos",{}));a[attr_key]=a.get(attr_key,8)+val
                    db_update_ficha(f["id"],{"atributos":a})
                    notifs.append(f"📊 {f.get('nome','?')}: {ATTR_SHORT[ATTR_KEYS.index(attr_key)]} {val:+d} → {a[attr_key]}")
            elif tt=="PER" and len(parts)>=3:
                per_key=parts[0].strip().lower()
                val=int(parts[1])
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    p=dict(f.get("pericias",{}));p[per_key]=p.get(per_key,0)+val
                    db_update_ficha(f["id"],{"pericias":p})
                    notifs.append(f"🎯 {f.get('nome','?')}: {PERICIAS_NOMES.get(per_key,per_key)} {val:+d}")
        except Exception as e: log.warning(f"Intercept:{tt}:{params}→{e}")
    clean=STATE_RE.sub("",text).strip()
    if notifs and msg:
        try: await msg.reply_text("📡 *Sync:*\n"+"\n".join(notifs),parse_mode="Markdown")
        except: pass
    return clean

# ══════ CRIAÇÃO ESTÁTICA ══════

def roll_attrs():
    rolls=[rng.randint(1,8)+rng.randint(1,8) for _ in range(7)]
    rolls.sort();dropped=rolls.pop(0);rolls.sort(reverse=True)
    return rolls,dropped

def roll_pv(rk,ck):
    dice=[rng.randint(1,6) for _ in range(4)]
    dice.sort();d=dice[0];t=sum(dice[1:])
    r=DL.RACAS_STATS[rk];c=DL.CLASSES_STATS[ck]
    return max(t+r["vida_ajuste"]+c["pv"],1),dice,d,t,r["vida_ajuste"],c["pv"]

def build_ficha(st):
    r=DL.RACAS_STATS[st["raca"]];c=DL.CLASSES_STATS[st["classe"]];fl=DL.FILOS_STATS[st["filosofia"]]
    attrs={k:st["atributos_base"][k]+r["mods"][i] for i,k in enumerate(ATTR_KEYS)}
    # Terráqueo bonus attrs
    if st.get("bonus_attrs"):
        for k,v in st["bonus_attrs"].items(): attrs[k]=attrs.get(k,8)+v
    dm=calc_mod(attrs["destreza"]);arm=c["armadura"]
    cd=10+(dm if arm["tipo"]=="leve" else min(dm,2) if arm["tipo"]=="media" else 0)+arm["cd"]
    per=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items(): per[pk]=per.get(pk,0)+pv2
    # Terráqueo bonus pericias
    if st.get("bonus_pericias"):
        for pk,pv2 in st["bonus_pericias"].items(): per[pk]=per.get(pk,0)+pv2
    tec=per.get("tecnomancia",0);im=calc_mod(attrs["inteligencia"])
    ram=max(1+im+tec//2,0)
    init=dm+(2 if st["filosofia"]=="cod_sobrevivente" or st["classe"]=="batedor" else 0)
    equip=list(c.get("equip_fixo",[]));
    if st.get("equip_choice"):equip.insert(0,st["equip_choice"])
    return {"nome":st.get("nome","?"),"raca":r["nome"],"classe":c["nome"],"filosofia":fl[0],
        "nivel":1,"xp":0,"pv_atual":st["pv"],"pv_max":st["pv"],"cd":cd,
        "ram_atual":ram,"ram_max":ram,"iniciativa":init,"deslocamento":r.get("desloc",9),
        "atributos":attrs,"pericias":per,"habilidades":[f"{fl[0]}: {fl[1]}"],
        "tecnomancias":[],"armas":[x for x in equip if any(w in x for w in["1d","2d","3d"])],
        "armadura":f"{arm['nome']} (CD+{arm['cd']})",
        "inventario":[x for x in equip if not any(w in x for w in["1d","2d","3d"])],
        "creditos":100+c.get("creditos_extra",0),"implantes":[]}

# ══════ HELPERS ══════

async def ask(chat,p,ret=4,m=None):
    for i in range(ret):
        try: return chat.send_message(p).text
        except gex.ResourceExhausted as e:
            if "per_day" in str(e): return "⚠️ Limite diário."
            w=(2**i)*10+rng.uniform(0,5)
            if m and i<ret-1:
                try: await m.reply_text(f"⏳ _{w:.0f}s..._",parse_mode="Markdown")
                except: pass
            await asyncio.sleep(w)
        except Exception as e:
            log.error(f"G:{e}")
            if i==ret-1: raise
            await asyncio.sleep(5)
    return "⚠️ Mestre offline."

async def rp(m,t):
    for p in([t[i:i+4000] for i in range(0,len(t),4000)] if len(t)>4000 else [t]):
        try: await m.reply_text(p,parse_mode="Markdown")
        except: await m.reply_text(p)

def mkb(items,pfx,cols=2):
    """Make keyboard from dict."""
    bs=[Btn(v,callback_data=f"{pfx}:{k}") for k,v in items.items()]
    return KBD([bs[i:i+cols] for i in range(0,len(bs),cols)])

def ff(f):
    a=f.get("atributos",{})
    arms="\n".join(f"  ⚔️ {x}" for x in(f.get("armas",[])or[]))or"  —"
    per=", ".join(f"{PERICIAS_NOMES.get(k,k)}+{v}" for k,v in(f.get("pericias",{})or{}).items() if v)or"—"
    habs="\n".join(f"  🔹 {h}" for h in(f.get("habilidades",[])or[]))or"  —"
    tecno=", ".join(f.get("tecnomancias",[])or[])or"—"
    return (f"🧑‍🚀 *{f.get('nome','?')}* (ID:{f.get('id','?')})\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🌌 {f.get('raca','?')} | ⚔️ {f.get('classe','?')} | 📜 {f.get('filosofia','?')}\n"
        f"📊 Nv{f.get('nivel',1)} | ✨ {f.get('xp',0)}XP\n━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ {f.get('pv_atual','?')}/{f.get('pv_max','?')} | 🛡️ CD{f.get('cd','?')} | 🧠 RAM{f.get('ram_atual','?')}/{f.get('ram_max','?')}\n"
        f"⚡Init+{f.get('iniciativa',0)} | 🏃{f.get('deslocamento',9)}m\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💪{a.get('forca','?')}({calc_mod(a.get('forca',8)):+d}) ⚡{a.get('destreza','?')}({calc_mod(a.get('destreza',8)):+d}) 🩸{a.get('constituicao','?')}({calc_mod(a.get('constituicao',8)):+d})\n"
        f"🧠{a.get('inteligencia','?')}({calc_mod(a.get('inteligencia',8)):+d}) 🦉{a.get('sabedoria','?')}({calc_mod(a.get('sabedoria',8)):+d}) 🗣️{a.get('carisma','?')}({calc_mod(a.get('carisma',8)):+d})\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 {per}\n🧠 Tecno: {tecno}\n🛠️\n{habs}\n⚔️\n{arms}\n"
        f"🛡️ {f.get('armadura','?')} | 🦾 {', '.join(f.get('implantes',[])or[])or'—'}\n"
        f"🎒 {', '.join(f.get('inventario',[])or[])or'—'}\n💎 {f.get('creditos',100)}CG")

MAIN_KB=KBD([
    [Btn("🚀 Iniciar Sessão",callback_data="m:init"),Btn("🧑‍🚀 Criar Personagem",callback_data="m:criar")],
    [Btn("📋 Minhas Fichas",callback_data="m:mfichas"),Btn("📚 Retomar Sessão",callback_data="m:csess")],
    [Btn("📖 Glossário",callback_data="m:gloss"),Btn("❓ Comandos",callback_data="m:help")]])
GLOSS_KB=KBD([
    [Btn("🌌 Raças",callback_data="g:racas"),Btn("⚔️ Classes",callback_data="g:classes")],
    [Btn("🗡️ Armas",callback_data="g:ab"),Btn("🔫 Armas Fogo",callback_data="g:af")],
    [Btn("🛡️ Armaduras",callback_data="g:ar"),Btn("🦾 Implantes",callback_data="g:im")],
    [Btn("🧠 Tecnomancia",callback_data="g:te"),Btn("🚀 Naves",callback_data="g:na")],
    [Btn("🛠️ Ferramentas",callback_data="g:fe"),Btn("🔧 Mods",callback_data="g:mo")],
    [Btn("📜 Filosofias",callback_data="g:fi"),Btn("👾 Bestiário",callback_data="g:be")],
    [Btn("🔙 Menu",callback_data="m:back")]])
WELCOME="🌌 *TERMINAL DA CONFEDERAÇÃO* 🌌\n━━━━━━━━━━━━━━━━━━━━\n⚡ _Conexão estabelecida..._\n📡 _Aguardando instruções, viajante._"

def inject_fichas_prompt(fichas):
    if not fichas: return ""
    lines=["FICHAS_ATIVAS:\n"]
    for f in fichas:
        a=f.get("atributos",{})
        lines.append(f"--- {f.get('nome','?')} ({f.get('raca','?')} {f.get('classe','?')} Nv{f.get('nivel',1)}) ---")
        lines.append(f"PV:{f.get('pv_atual')}/{f.get('pv_max')} CD:{f.get('cd')} RAM:{f.get('ram_atual')}/{f.get('ram_max')}")
        lines.append(f"For:{a.get('forca',8)} Des:{a.get('destreza',8)} Con:{a.get('constituicao',8)} Int:{a.get('inteligencia',8)} Sab:{a.get('sabedoria',8)} Car:{a.get('carisma',8)}")
        lines.append(f"Per:{f.get('pericias',{})} Armas:{f.get('armas',[])} Inv:{f.get('inventario',[])} CG:{f.get('creditos',100)} Tecno:{f.get('tecnomancias',[])}\n")
    return "\n".join(lines)

# ══════ HANDLERS ══════

async def cmd_start(u,c): await u.message.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_reset(u,c):
    chats.pop(u.effective_chat.id,None)
    await u.message.reply_text("🔄 _Memória neural purgada._\n💾 Fichas/sessões permanecem.",reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_help(u,c): await rp(u.message,"📡 *PROTOCOLOS*\n━━━━━━━━━━━━━━━━━━━━\n⚔️ /iniciar /novojogo /criarpersonagem /rolar /regras\n💾 /ficha /fichas /deletarficha ID /levelup /implante\n📚 /salvarsessao /sessoes /cargarsessao ID /contexto\n📖 /glossario /reset /ajuda")
async def cmd_glossario(u,c): await u.message.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")

async def cmd_rolar(u,c):
    a=c.args
    if not a: await u.message.reply_text("🎲 /rolar NdN");return
    d=a[0].lower()
    try: n,s=d.split("d");n=int(n)if n else 1;s=int(s)
    except: await u.message.reply_text("❌ Inválido");return
    if n<1 or n>20 or s<1 or s>100:return
    rs=[rng.randint(1,s)for _ in range(n)];t=sum(rs)
    cr=""
    if s==20 and n==1:
        if rs[0]==20:cr="\n\n🌟 *O COSMOS SE CURVA!*"
        elif rs[0]==1:cr="\n\n💀 *O VÁCUO RI...*"
    await rp(u.message,f"🎲 *{d.upper()}*\n{rs}\n*Total: {t}*{cr}")

async def cmd_regras(u,c): await rp(u.message,"📖 *MANUAL*\n━━━━━━━━━━━━━━━━━━━━\n🎲 1d20+Atrib+Per ≥ CD\n⚔️ Melee:dado+For | 🔫 Ranged:dado+Des\n🛡️ CD:10+Des+Arm\n💥20=Crítico|💀1=Falha\n❤️0PV=Morte|🔋Pente:3t|🧠RAM:1+Int+½Tecno")

async def cmd_iniciar(u,c):
    cid=u.effective_chat.id;uid=u.message.from_user.id
    fichas=db_list_fichas(uid,cid)
    if not fichas: await u.message.reply_text("❌ Sem personagens. Use /criarpersonagem");return
    btns=[Btn(f"⚔️ {f['nome']} (Nv{f['nivel']})",callback_data=f"sel:{f['id']}") for f in fichas]
    await u.message.reply_text("🧑‍🚀 *Selecione personagem:*",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")

async def cmd_novojogo(u,c):
    cid=u.effective_chat.id
    actives=db_get_all_active(cid)
    if not actives:
        await u.message.reply_text("❌ Nenhum personagem ativo. Usem /iniciar primeiro.");return
    play_kb=KBD([[Btn("🆕 Nova Aventura",callback_data="play:new")],[Btn("📜 Continuar História",callback_data="play:context")]])
    await u.message.reply_text("🌌 *Fichas sincronizadas.* Como iniciar?",reply_markup=play_kb,parse_mode="Markdown")

async def cmd_criar(u,c):
    cstate[u.message.from_user.id]={"step":"raca","chat_id":u.effective_chat.id}
    await u.message.reply_text("🧑‍🚀 *RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n📋 1/5: *Origem*",reply_markup=mkb(RACAS_BTN,"r",2),parse_mode="Markdown")

async def cmd_ficha(u,c):
    f=db_get_active(u.message.from_user.id,u.effective_chat.id)
    if not f: await u.message.reply_text("❌ Sem personagem ativo. /iniciar");return
    await rp(u.message,ff(f))

async def cmd_fichas(u,c):
    fs=db_list_fichas(u.message.from_user.id,u.effective_chat.id)
    if not fs: await u.message.reply_text("📋 Vazio. /criarpersonagem");return
    await rp(u.message,"📋 *PERSONAGENS:*\n"+"\n".join(f"• ID *{f['id']}* — {f['nome']} ({f['raca']} {f['classe']} Nv{f['nivel']})" for f in fs)+"\n\n/deletarficha ID")

async def cmd_deletar(u,c):
    if not c.args: await u.message.reply_text("❌ /deletarficha ID");return
    try:fid=int(c.args[0])
    except: await u.message.reply_text("❌ ID inválido.");return
    uid=u.message.from_user.id;adm=ADMIN and str(uid)==str(ADMIN)
    f=db_get_ficha(fid)
    if not f: await u.message.reply_text("❌ Não encontrada.");return
    if str(f.get("user_id"))!=str(uid) and not adm: await u.message.reply_text("❌ Sem permissão.");return
    if db_delete_ficha(fid): await u.message.reply_text(f"🗑️ *{f.get('nome','?')}* eliminado.",parse_mode="Markdown")

async def cmd_levelup(u,c):
    """Level up com botões para atributo e perícia."""
    cid,uid,un=u.effective_chat.id,u.message.from_user.id,u.message.from_user.first_name or"?"
    f=db_get_active(uid,cid)
    if not f: await u.message.reply_text("❌ Sem personagem ativo.");return
    nv,xp,nm=f.get("nivel",1),f.get("xp",0),f.get("nome","?")
    if nv>=10: await u.message.reply_text("🌟 Máximo!");return
    xr=XP_T.get(nv,9999)
    if xp<xr: await u.message.reply_text(f"❌ *{nm}*: {xp}/{xr}XP (faltam {xr-xp})",parse_mode="Markdown");return

    # Rola dado de vida em Python
    rk=next((k for k,v in DL.RACAS_STATS.items() if v["nome"]==f.get("raca","")),None) or "terraqueo"
    faces=int(DL.RACAS_STATS[rk]["dado_nv"].split("d")[1])
    rh=rng.randint(1,faces);cm=calc_mod(f.get("atributos",{}).get("constituicao",8))
    hg=max(rh+cm,1);np2=f["pv_max"]+hg

    ups={"nivel":nv+1,"pv_max":np2,"pv_atual":np2}
    if(nv+1)%2==1 and nv+1>=3: ups["ram_max"]=f.get("ram_max",0)+1;ups["ram_atual"]=ups["ram_max"]
    db_update_ficha(f["id"],ups)

    txt=f"⬆️ *{nm}* → Nv{nv+1}!\n━━━━━━━━━━━━━━━━━━━━\n❤️ 🎲{DL.RACAS_STATS[rk]['dado_nv']}={rh}+Con({cm:+d})=+{hg} → *{np2}PV*\n"
    if(nv+1)%2==1 and nv+1>=3: txt+="🧠 +1 RAM\n"
    await rp(u.message,txt)

    # Botões para escolher atributo
    cstate[uid]={"step":"lvl_attr","chat_id":cid,"ficha_id":f["id"],"novo_nv":nv+1}
    a=f.get("atributos",{})
    btns=[Btn(f"{ATTR_LABELS[i]} ({a.get(k,8)}→{a.get(k,8)+1})",callback_data=f"la:{k}") for i,k in enumerate(ATTR_KEYS)]
    await u.message.reply_text("💪 *+1 Atributo* — onde investir?",reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")

# ── Sessões ──────────────────────────────────────────────

async def cmd_salvar_sessao(u,c):
    if not db:return
    cid=u.effective_chat.id;ch=gc(cid)
    if cid not in chats: await u.message.reply_text("❌ Sem sessão.");return
    await u.message.reply_text("📝 _Compilando..._",parse_mode="Markdown")
    s=await ask(ch,"RESUMO_SESSAO: Resuma TUDO factual. 1000 palavras max.",m=u.message)
    t=await ask(ch,"Título CURTO 6 palavras. Só título.")
    t=t.strip().strip('"')[:60]
    if db_save_session(cid,t,s): await u.message.reply_text(f"✅ *{t}*",parse_mode="Markdown");await rp(u.message,s)

async def cmd_sessoes(u,c):
    if not db:return
    sl=db_list_sessions(u.effective_chat.id)
    if not sl: await u.message.reply_text("📚 Vazio.");return
    await rp(u.message,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')} ({s.get('created_at','')[:10]})" for s in sl)+"\n\n/cargarsessao ID")

async def cmd_cargarsessao(u,c):
    if not db or not c.args: await u.message.reply_text("❌ /cargarsessao ID");return
    try:sid=int(c.args[0])
    except: await u.message.reply_text("❌ ID inválido.");return
    s=db_get_session(sid)
    if not s or s.get("chat_id")!=str(u.effective_chat.id): await u.message.reply_text("❌ Não encontrado.");return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid)
    ctx=inject_fichas_prompt(actives)
    if ctx: await ask(ch,ctx)
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Retomando '{s.get('title')}'.\n{s.get('summary')}\nRecapitule e pergunte o que fazer.",m=u.message))

async def cmd_contexto(u,c):
    txt=u.message.text.replace("/contexto","",1).strip()
    if not txt: await u.message.reply_text("📎 `/contexto Estávamos em Marte...`",parse_mode="Markdown");return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid)
    ctx=inject_fichas_prompt(actives)
    if ctx: await ask(ch,ctx)
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Importado.\n{txt}\nConfirme e recapitule.",m=u.message))
    if db:db_save_session(cid,"📎 Importado",txt)

# ══════ CALLBACK ROUTER ══════

async def on_cb(u:Update,c:ContextTypes.DEFAULT_TYPE):
    q=u.callback_query;await q.answer();d=q.data;m=q.message
    uid=q.from_user.id;cid=m.chat_id;un=q.from_user.first_name or"?"

    # Menu principal
    if d in("m:back","m:start"): await m.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
    elif d=="m:init":
        fichas=db_list_fichas(uid,cid)
        if not fichas: await m.reply_text("❌ Sem personagens. Crie um primeiro.");return
        btns=[Btn(f"⚔️ {f['nome']} (Nv{f['nivel']})",callback_data=f"sel:{f['id']}") for f in fichas]
        await m.reply_text("🧑‍🚀 *Selecione personagem:*",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")
    elif d.startswith("sel:"):
        fid=int(d[4:]);db_set_active(uid,cid,fid)
        f=db_get_ficha(fid)
        if f:
            await m.reply_text(f"✅ *{f.get('nome','?')}* ativado!",parse_mode="Markdown")
            await rp(m,ff(f))
            ch=gc(cid);await ask(ch,f"FICHAS_ATIVAS:\n{inject_fichas_prompt([f])}\nPersonagem ativo.",m=m)
            play_kb=KBD([[Btn("🆕 Nova Aventura",callback_data="play:new")],[Btn("📜 Continuar História",callback_data="play:context")]])
            await m.reply_text("🌌 *Fichas sincronizadas.* Como iniciar?",reply_markup=play_kb,parse_mode="Markdown")
    elif d=="m:criar":
        try:
            cstate[uid]={"step":"raca","chat_id":cid}
            await m.reply_text("🧑‍🚀 *RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n📋 1/5: *Origem*",reply_markup=mkb(RACAS_BTN,"r",2),parse_mode="Markdown")
        except Exception as e: await m.reply_text(f"⚠️ Erro: {e}")
    elif d=="m:mfichas":
        fs=db_list_fichas(uid,cid)
        if not fs: await m.reply_text("📋 Sem personagens.");return
        await rp(m,"📋 *PERSONAGENS:*\n"+"\n".join(f"• ID *{f['id']}* — {f['nome']} ({f['raca']} {f['classe']} Nv{f['nivel']})" for f in fs))
    elif d=="m:csess":
        sl=db_list_sessions(cid)
        if not sl: await m.reply_text("📚 Sem sessões.");return
        await rp(m,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')}" for s in sl)+"\n/cargarsessao ID")
    elif d=="m:gloss": await m.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")
    elif d=="m:help": await rp(m,"📡 /iniciar /novojogo /criarpersonagem /rolar /regras /ficha /fichas /deletarficha /levelup /salvarsessao /sessoes /cargarsessao /contexto /glossario /reset")

    # Novo Jogo
    elif d=="play:new":
        chats.pop(cid,None);ch=gc(cid)
        actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
        if ctx: await ask(ch,ctx)
        await q.edit_message_text("🌌 _Inicializando..._",parse_mode="Markdown")
        await rp(m,await ask(ch,"SISTEMA: NOVA aventura. Cena épica no Sistema Solar com os personagens ativos. Gancho de missão. Opções. Conciso.",m=m))
    elif d=="play:context":
        cstate[uid]={"step":"wait_context","chat_id":cid}
        await q.edit_message_text("📜 *Envio de Contexto*\nDigite ou cole o resumo da aventura anterior:",parse_mode="Markdown")

    # Glossário
    elif d=="g:racas": await m.reply_text("🌌 *RAÇAS:*",reply_markup=mkb(RACAS_BTN,"gr",2),parse_mode="Markdown")
    elif d=="g:classes": await m.reply_text("⚔️ *CLASSES:*",reply_markup=mkb(CLASSES_BTN,"gc",2),parse_mode="Markdown")
    elif d.startswith("gr:"): await rp(m,DL.RACAS_DETAIL.get(d[3:],"❌"));await m.reply_text("🔙",reply_markup=KBD([[Btn("🌌",callback_data="g:racas"),Btn("📖",callback_data="m:gloss")]]))
    elif d.startswith("gc:"): await rp(m,DL.CLASSES_DETAIL.get(d[3:],"❌"));await m.reply_text("🔙",reply_markup=KBD([[Btn("⚔️",callback_data="g:classes"),Btn("📖",callback_data="m:gloss")]]))
    elif d=="g:ab": await rp(m,ARMAS_BRANCAS_TEXT)
    elif d=="g:af": await rp(m,ARMAS_FOGO_TEXT)
    elif d=="g:ar": await rp(m,ARMADURAS_TEXT)
    elif d=="g:im": await rp(m,IMPLANTES_TEXT)
    elif d=="g:fe": await rp(m,FERRAMENTAS_TEXT)
    elif d=="g:mo": await rp(m,MODIFICACOES_TEXT)
    elif d=="g:na": await rp(m,NAVES_TEXT)
    elif d=="g:fi": await rp(m,FILOSOFIAS_TEXT)
    elif d=="g:te": await m.reply_text("🧠",reply_markup=KBD([[Btn("🟢 Básicas",callback_data="gt:b")],[Btn("🟡 Injeções",callback_data="gt:i")],[Btn("🔴 Protocolos",callback_data="gt:p")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d in("gt:b","gt:i","gt:p"): await rp(m,{"gt:b":TECNO_BASICAS,"gt:i":TECNO_INJECOES,"gt:p":TECNO_PROTOCOLOS}[d])
    elif d=="g:be": await m.reply_text("👾",reply_markup=KBD([[Btn("🌍 Planetas",callback_data="gb:p")],[Btn("🦎 Fauna",callback_data="gb:f")],[Btn("👾 Vazio",callback_data="gb:v")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d in("gb:p","gb:f","gb:v"): await rp(m,{"gb:p":BESTIARIO_PLANETAS,"gb:f":BESTIARIO_FAUNA,"gb:v":BESTIARIO_VAZIO}[d])

    # ── Criação ──
    elif d.startswith("r:"):
        k=d[2:];cstate.setdefault(uid,{});cstate[uid].update({"step":"classe","raca":k,"chat_id":cid})
        await q.edit_message_text(f"✅ *{RACAS_BTN[k]}*\n\n📋 2/5: *Especialização*",parse_mode="Markdown")
        await m.reply_text("⚔️ Selecione:",reply_markup=mkb(CLASSES_BTN,"c",2))
    elif d.startswith("c:"):
        k=d[2:];cstate.setdefault(uid,{});cstate[uid].update({"step":"filosofia","classe":k})
        await q.edit_message_text(f"✅ *{CLASSES_BTN[k]}*\n\n📋 3/5: *Código de conduta*",parse_mode="Markdown")
        await m.reply_text("📜 Selecione:",reply_markup=mkb(FILOS_BTN,"f",2))
    elif d.startswith("f:"):
        k=d[2:];st=cstate.setdefault(uid,{});st.update({"step":"attr_0","filosofia":k})
        vals,dropped=roll_attrs();st["rolled"]=vals;st["all_rolls"]=vals+[dropped];st["dropped"]=dropped
        txt=(f"✅ *{FILOS_BTN[k]}*\n\n📋 4/5: *Calibração Neural*\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 2d8 ×7 (máx 16):\nResultados: {sorted(st['all_rolls'])}\n❌ Descartado: {dropped}\n✅ *{vals}*\n\nDistribua! Toque para *{ATTR_LABELS[0]}*:")
        await q.edit_message_text(txt,parse_mode="Markdown")
        btns=[Btn(str(v),callback_data=f"av:{i}") for i,v in enumerate(vals)]
        await m.reply_text(f"{ATTR_LABELS[0]}:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))
    elif d.startswith("av:"):
        idx=int(d[3:]);st=cstate.get(uid)
        if not st:return
        ai=int(st.get("step","attr_0").split("_")[1]);vals=st["rolled"]
        chosen=vals[idx];st.setdefault("atributos_base",{});st["atributos_base"][ATTR_KEYS[ai]]=chosen
        vals.pop(idx);st["rolled"]=vals
        if ai<5:
            st["step"]=f"attr_{ai+1}"
            if vals:
                btns=[Btn(str(v),callback_data=f"av:{i}") for i,v in enumerate(vals)]
                await q.edit_message_text(f"✅ {ATTR_LABELS[ai]}: *{chosen}*",parse_mode="Markdown")
                await m.reply_text(f"{ATTR_LABELS[ai+1]}:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))
            else:
                st["atributos_base"][ATTR_KEYS[5]]=chosen;st["step"]="equip"
                await _fin_attrs(m,uid)
        else:
            st["step"]="equip"
            await q.edit_message_text(f"✅ {ATTR_LABELS[5]}: *{chosen}*",parse_mode="Markdown")
            await _fin_attrs(m,uid)
    elif d.startswith("eq:"):
        idx=int(d[3:]);st=cstate.get(uid)
        if not st:return
        cls=DL.CLASSES_STATS[st["classe"]]
        choices=cls.get("equip_escolha",cls.get("equip_escolha_melee",[]))
        if choices:st["equip_choice"]=choices[0][idx]
        await q.edit_message_text(f"✅ *{st.get('equip_choice','?')}*",parse_mode="Markdown")
        # Terráqueo? Precisa distribuir +4 atributos
        if st["raca"]=="terraqueo":
            st["step"]="terra_attr"
            st["bonus_attrs"]={};st["bonus_attr_remaining"]=4
            btns=[Btn(f"{ATTR_LABELS[i]}",callback_data=f"ta:{k}") for i,k in enumerate(ATTR_KEYS)]
            await m.reply_text(f"🌍 *Bônus Terráqueo:* Distribua *4 pontos* de atributo (máx +2 em um).\nRestam: *4*\n\nToque para adicionar +1:",
                reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]),parse_mode="Markdown")
        else:
            st["step"]="nome"
            await m.reply_text("✏️ Digite o *nome* do personagem:",parse_mode="Markdown")

    # ── Terráqueo: +4 atributos livres ──
    elif d.startswith("ta:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="terra_attr":return
        ba=st.setdefault("bonus_attrs",{})
        if ba.get(k,0)>=2:
            await m.reply_text(f"⚠️ Máximo +2 em {ATTR_SHORT[ATTR_KEYS.index(k)]}. Escolha outro.");return
        ba[k]=ba.get(k,0)+1
        st["bonus_attr_remaining"]-=1
        rem=st["bonus_attr_remaining"]
        if rem>0:
            dist=" ".join(f"{ATTR_SHORT[ATTR_KEYS.index(a)]}+{v}" for a,v in ba.items())
            btns=[Btn(f"{ATTR_LABELS[i]} (+{ba.get(k2,0)})",callback_data=f"ta:{k2}") for i,k2 in enumerate(ATTR_KEYS) if ba.get(k2,0)<2]
            await q.edit_message_text(f"🌍 *Bônus Terráqueo:* {dist}\nRestam: *{rem}*",parse_mode="Markdown")
            await m.reply_text("Toque para +1:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))
        else:
            # Agora +3 perícias livres
            st["step"]="terra_per"
            st["bonus_pericias"]={};st["bonus_per_remaining"]=3
            per_btns=[Btn(f"{PERICIAS_NOMES[pk]}",callback_data=f"tp:{pk}") for pk in sorted(PERICIAS_NOMES.keys())]
            await m.reply_text(f"🌍 *Bônus Terráqueo:* Distribua *3 pontos* de perícia.\nRestam: *3*",
                reply_markup=KBD([per_btns[i:i+3] for i in range(0,len(per_btns),3)]),parse_mode="Markdown")

    # ── Terráqueo: +3 perícias livres ──
    elif d.startswith("tp:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="terra_per":return
        bp=st.setdefault("bonus_pericias",{})
        bp[k]=bp.get(k,0)+1
        st["bonus_per_remaining"]-=1
        rem=st["bonus_per_remaining"]
        if rem>0:
            dist=" ".join(f"{PERICIAS_NOMES.get(a,a)}+{v}" for a,v in bp.items())
            per_btns=[Btn(f"{PERICIAS_NOMES[pk]}",callback_data=f"tp:{pk}") for pk in sorted(PERICIAS_NOMES.keys())]
            await q.edit_message_text(f"🌍 Perícias: {dist}\nRestam: *{rem}*",parse_mode="Markdown")
            await m.reply_text("Toque para +1:",reply_markup=KBD([per_btns[i:i+3] for i in range(0,len(per_btns),3)]))
        else:
            st["step"]="nome"
            await m.reply_text("✏️ Digite o *nome* do personagem:",parse_mode="Markdown")

    # ── Level Up: escolha atributo por botão ──
    elif d.startswith("la:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_attr":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        a=f.get("atributos",{});a[k]=a.get(k,8)+1
        db_update_ficha(fid,{"atributos":a})
        await q.edit_message_text(f"✅ {ATTR_SHORT[ATTR_KEYS.index(k)]} → *{a[k]}* ({calc_mod(a[k]):+d})",parse_mode="Markdown")
        # Agora perícia
        st["step"]="lvl_per"
        per=f.get("pericias",{})
        # Mostra perícias atuais + opções novas
        all_per=set(list(per.keys())+list(PERICIAS_NOMES.keys()))
        limit=5 if st["novo_nv"]<=4 else 7
        per_btns=[Btn(f"{PERICIAS_NOMES.get(pk,pk)} (+{per.get(pk,0)}→{per.get(pk,0)+1})",callback_data=f"lp:{pk}") for pk in sorted(all_per) if per.get(pk,0)<limit]
        await m.reply_text("🎯 *+1 Perícia* — onde investir?",reply_markup=KBD([per_btns[i:i+2] for i in range(0,len(per_btns),2)]),parse_mode="Markdown")

    # ── Level Up: escolha perícia por botão ──
    elif d.startswith("lp:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_per":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        per=f.get("pericias",{});per[k]=per.get(k,0)+1
        db_update_ficha(fid,{"pericias":per})
        await q.edit_message_text(f"✅ {PERICIAS_NOMES.get(k,k)} → *+{per[k]}*",parse_mode="Markdown")

        # Verifica se ganhou slot de tecnomancia novo
        tecno_skill=per.get("tecnomancia",0)
        novo_nv=st["novo_nv"]
        if tecno_skill>=1:
            max_scripts=DL.calc_max_scripts(novo_nv,tecno_skill)
            current_scripts=list(f.get("tecnomancias",[]) or [])
            if len(current_scripts)<max_scripts:
                # Tem slot novo — oferecer seleção
                available=DL.get_available_scripts(tecno_skill)
                available={k2:v for k2,v in available.items() if k2 not in current_scripts}
                if available:
                    st["step"]="lvl_tecno"
                    slots_novos=max_scripts-len(current_scripts)
                    btns=[Btn(f"🧠 {v['nome']} ({v['ram']}RAM)",callback_data=f"lt:{k2}") for k2,v in sorted(available.items(),key=lambda x:x[1]["ram"])]
                    await m.reply_text(f"🧠 *Novo script disponível!* ({len(current_scripts)+1}/{max_scripts})\nEscolha:",
                        reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")
                    return

        cstate.pop(uid,None)
        ch=gc(cid);await ask(ch,f"SISTEMA: {f.get('nome','?')} subiu Nv{novo_nv}. Novas capacidades.",m=m)
        await m.reply_text(f"⬆️ Level up de *{f.get('nome','?')}* completo! Use /ficha para ver.",parse_mode="Markdown")

    # ── Tecnomancia: seleção de scripts (criação) ──
    elif d.startswith("ts:"):
        script_id=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="tecno_select":return
        if script_id in st["tecno_selected"]:
            await m.reply_text("⚠️ Já selecionado!");return
        st["tecno_selected"].append(script_id)
        st["tecno_remaining"]-=1
        rem=st["tecno_remaining"]
        nome_script=DL.TECNO_SCRIPTS.get(script_id,{}).get("nome",script_id)
        if rem>0:
            sel_names=", ".join(DL.TECNO_SCRIPTS[s]["nome"] for s in st["tecno_selected"])
            avail={k:v for k,v in st["tecno_available"].items() if k not in st["tecno_selected"]}
            btns=[Btn(f"🧠 {v['nome']} ({v['ram']}RAM)",callback_data=f"ts:{k}") for k,v in sorted(avail.items(),key=lambda x:x[1]["ram"])]
            await q.edit_message_text(f"✅ +{nome_script}\n📋 Selecionados: {sel_names}\n🧠 Restam: *{rem}*",parse_mode="Markdown")
            if btns:
                await m.reply_text("Próximo script:",reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]))
        else:
            # Todos selecionados — salvar ficha
            ficha=st["built_ficha"]
            ficha["tecnomancias"]=list(st["tecno_selected"])
            sel_names=", ".join(DL.TECNO_SCRIPTS[s]["nome"] for s in st["tecno_selected"])
            await q.edit_message_text(f"✅ +{nome_script}\n🧠 Scripts: {sel_names}",parse_mode="Markdown")
            await _save_and_finish(m,uid,un,cid,ficha)

    # ── Tecnomancia: seleção no level up ──
    elif d.startswith("lt:"):
        script_id=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_tecno":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        tecno=list(f.get("tecnomancias",[]) or [])
        if script_id not in tecno:
            tecno.append(script_id)
            db_update_ficha(fid,{"tecnomancias":tecno})
        nome_script=DL.TECNO_SCRIPTS.get(script_id,{}).get("nome",script_id)
        await q.edit_message_text(f"✅ Aprendeu: *{nome_script}*",parse_mode="Markdown")
        cstate.pop(uid,None)
        ch=gc(cid);await ask(ch,f"SISTEMA: {f.get('nome','?')} aprendeu {nome_script}.",m=m)
        await m.reply_text(f"⬆️ Level up de *{f.get('nome','?')}* completo!",parse_mode="Markdown")

    # ── Implantes: categoria ──
    elif d.startswith("ic:"):
        slot=d[3:].replace("cabeca","cabeça")
        f=db_get_active(uid,cid)
        if not f:return
        cred=f.get("creditos",0)
        impls={k:v for k,v in DL.IMPLANTES_DATA.items() if v["slot"]==slot}
        impl_atuais=[i.lower() for i in (f.get("implantes",[]) or [])]
        btns=[]
        for k,v in impls.items():
            ja="✅" if v["nome"].lower() in " ".join(impl_atuais) else ""
            pode="💎" if cred>=v["preco"] else "🚫"
            btns.append(Btn(f"{ja}{pode} {v['nome']} ({v['preco']}CG)",callback_data=f"ii:{k}"))
        btns.append(Btn("🔙 Voltar",callback_data="m:back"))
        await m.reply_text(f"🦾 *{slot.upper()}* — 💎 {cred} CG disponíveis",
            reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")

    # ── Implantes: instalar ──
    elif d.startswith("ii:"):
        impl_id=d[3:];f=db_get_active(uid,cid)
        if not f or impl_id not in DL.IMPLANTES_DATA:return
        imp=DL.IMPLANTES_DATA[impl_id];cred=f.get("creditos",0)
        if cred<imp["preco"]:
            await m.reply_text(f"❌ Créditos insuficientes. Precisa: {imp['preco']} CG, tem: {cred} CG.");return
        impl_list=list(f.get("implantes",[]) or [])
        con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
        limite=DL.calc_implant_limit(con_mod)
        qtd=len(impl_list)
        if qtd>=limite:
            extra=qtd-limite+1
            avisos={1:"⚠️ -1d6 PV Máx permanente!",2:"☠️ Curto-circuito em falha 1-2!",3:"💀 COLAPSO NEURAL — MORTE!"}
            aviso=avisos.get(extra,"💀 PERIGO EXTREMO!")
            if extra>=3:
                await m.reply_text(f"💀 *IMPOSSÍVEL.* Instalar um 3º implante acima do limite causa morte instantânea.");return
            confirm_kb=KBD([[Btn(f"⚠️ Confirmar ({aviso})",callback_data=f"ic_confirm:{impl_id}")],[Btn("🔙 Cancelar",callback_data="m:back")]])
            await m.reply_text(f"⚠️ *AVISO:* Acima do limite seguro ({qtd}/{limite})!\n{aviso}\n\nInstalar *{imp['nome']}* mesmo assim?",
                reply_markup=confirm_kb,parse_mode="Markdown")
            return
        # Instala direto (dentro do limite)
        await _install_implant(m,f,impl_id)

    elif d.startswith("ic_confirm:"):
        impl_id=d[11:];f=db_get_active(uid,cid)
        if not f:return
        await _install_implant(m,f,impl_id)

async def _fin_attrs(m,uid):
    st=cstate.get(uid)
    if not st:return
    pv,dice,dropped,subtotal,ajuste,bonus=roll_pv(st["raca"],st["classe"])
    st["pv"]=pv;st["pv_detail"]={"dice":dice,"dropped":dropped,"subtotal":subtotal,"ajuste":ajuste,"bonus":bonus}
    r=DL.RACAS_STATS[st["raca"]];c=DL.CLASSES_STATS[st["classe"]];fl=DL.FILOS_STATS[st["filosofia"]]
    lines=["📋 *RESUMO*\n━━━━━━━━━━━━━━━━━━━━",f"🌌 {r['nome']} | ⚔️ {c['nome']} | 📜 {fl[0]}\n"]
    for i,k in enumerate(ATTR_KEYS):
        b=st["atributos_base"][k];rc=r["mods"][i];f2=b+rc;md=calc_mod(f2)
        lines.append(f"{ATTR_LABELS[i]}: {b}{rc:+d} = *{f2}* ({md:+d})")
    d2=st["pv_detail"]
    lines.append(f"\n❤️ 🎲4d6{d2['dice']} desc {d2['dropped']} = {d2['subtotal']} {d2['ajuste']:+d}racial {d2['bonus']:+d}classe = *{pv} PV*")
    attrs={k:st["atributos_base"][k]+r["mods"][i] for i,k in enumerate(ATTR_KEYS)}
    dm=calc_mod(attrs["destreza"]);arm=c["armadura"]
    cd=10+(dm if arm["tipo"]=="leve" else min(dm,2) if arm["tipo"]=="media" else 0)+arm["cd"]
    per=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items(): per[pk]=per.get(pk,0)+pv2
    tec=per.get("tecnomancia",0);im=calc_mod(attrs["inteligencia"]);ram=max(1+im+tec//2,0)
    lines.append(f"🛡️ CD: {cd} | 🧠 RAM: {ram}")
    per_s=", ".join(f"{PERICIAS_NOMES.get(pk,pk)}+{pv2}" for pk,pv2 in sorted(per.items(),key=lambda x:-x[1]))
    lines.append(f"🎯 {per_s}")
    await rp(m,"\n".join(lines))
    cls=DL.CLASSES_STATS[st["classe"]]
    choices=cls.get("equip_escolha",cls.get("equip_escolha_melee",[]))
    if choices:
        btns=[Btn(opt,callback_data=f"eq:{i}") for i,opt in enumerate(choices[0])]
        await m.reply_text("⚔️ Arma:",reply_markup=KBD([[b] for b in btns]))
    else:
        # Terráqueo? Bonus
        if st["raca"]=="terraqueo":
            st["step"]="terra_attr"
            st["bonus_attrs"]={};st["bonus_attr_remaining"]=4
            btns=[Btn(f"{ATTR_LABELS[i]}",callback_data=f"ta:{k}") for i,k in enumerate(ATTR_KEYS)]
            await m.reply_text("🌍 *Bônus Terráqueo:* Distribua *4 pontos* de atributo (máx +2 em um).\nRestam: *4*",
                reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]),parse_mode="Markdown")
        else:
            st["step"]="nome"
            await m.reply_text("✏️ Digite o *nome* do personagem:",parse_mode="Markdown")

# ── Save & Finish (criação) ───────────────────────────────

async def _save_and_finish(msg,uid,un,cid,ficha):
    """Salva ficha, ativa, injeta na IA, limpa estado."""
    fid=db_create_ficha(uid,un,cid,ficha)
    if fid:
        db_set_active(uid,cid,fid);ficha["id"]=fid
        await rp(msg,f"✅ *{ficha['nome']}* registrado! (ID:{fid})")
        await rp(msg,ff(ficha))
        ch=gc(cid);await ask(ch,f"FICHAS_ATIVAS:\n{inject_fichas_prompt([ficha])}\nPersonagem criado.",m=msg)
    else:
        await msg.reply_text("⚠️ Erro ao salvar.")
    cstate.pop(uid,None)
    await msg.reply_text("🚀 Pronto! /iniciar para sessão ou /novojogo para aventura.",reply_markup=MAIN_KB)

async def _install_implant(msg,f,impl_id):
    """Instala implante, deduz créditos, aplica mecânica."""
    imp=DL.IMPLANTES_DATA[impl_id]
    impl_list=list(f.get("implantes",[]) or [])
    impl_list.append(imp["nome"])
    ups={"implantes":impl_list,"creditos":f.get("creditos",0)-imp["preco"]}
    mec=imp.get("mecanica",{})
    if "ram_max" in mec: ups["ram_max"]=f.get("ram_max",0)+mec["ram_max"];ups["ram_atual"]=ups["ram_max"]
    if "cd" in mec: ups["cd"]=f.get("cd",10)+mec["cd"]
    if "pv_max" in mec: ups["pv_max"]=f.get("pv_max",0)+mec["pv_max"];ups["pv_atual"]=f.get("pv_atual",0)+mec["pv_max"]
    db_update_ficha(f["id"],ups)
    await msg.reply_text(
        f"🦾 *{imp['nome']}* instalado em *{f.get('nome','?')}*!\n"
        f"💎 -{imp['preco']} CG → {ups['creditos']} CG\n"
        f"📋 Efeito: _{imp['efeito']}_",parse_mode="Markdown")

# ── /implante ────────────────────────────────────────────

async def cmd_implante(u,c):
    """Gerencia implantes cibernéticos."""
    f=db_get_active(u.message.from_user.id,u.effective_chat.id)
    if not f: await u.message.reply_text("❌ Sem personagem ativo. /iniciar");return

    impl_atuais=f.get("implantes",[]) or []
    con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
    limite=DL.calc_implant_limit(con_mod)
    qtd=len(impl_atuais)

    aviso=""
    if qtd>=limite:
        extra=qtd-limite+1
        if extra==1: aviso="\n⚠️ *RISCO:* 1º acima do limite! -1d6 PV Máx permanente."
        elif extra==2: aviso="\n☠️ *PERIGO:* 2º acima! Curto-circuito em falha 1-2."
        elif extra>=3: aviso="\n💀 *LETAL:* 3º acima = colapso neural. MORTE."

    txt=(f"🦾 *IMPLANTES DE {f.get('nome','?')}*\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Limite seguro: {limite} (2 + Con({con_mod:+d}))\n"
        f"🦾 Instalados: {qtd}/{limite}\n")
    if impl_atuais: txt+="\n".join(f"  • {i}" for i in impl_atuais)+"\n"
    txt+=f"\n💎 Créditos: {f.get('creditos',0)} CG{aviso}\n\n"
    txt+="Selecione categoria para instalar:"

    cat_kb=KBD([
        [Btn("🧠 Cabeça",callback_data="ic:cabeca")],
        [Btn("🫀 Torso",callback_data="ic:torso")],
        [Btn("🦿 Membros",callback_data="ic:membros")],
        [Btn("🔙 Cancelar",callback_data="m:back")]])
    await u.message.reply_text(txt,reply_markup=cat_kb,parse_mode="Markdown")

# ── Mensagens de texto ───────────────────────────────────

async def on_msg(u:Update,c:ContextTypes.DEFAULT_TYPE):
    cid=u.effective_chat.id;txt=u.message.text;un=u.message.from_user.first_name or"?"
    uid=u.message.from_user.id
    if not txt:return

    st=cstate.get(uid)

    # Esperando contexto prévio (play:context)
    if st and st.get("step")=="wait_context" and st.get("chat_id")==cid:
        chats.pop(cid,None);ch=gc(cid)
        actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
        if ctx: await ask(ch,ctx)
        await u.message.reply_text("🔄 _Sincronizando memórias..._",parse_mode="Markdown")
        resp=await ask(ch,f"CONTEXTO_SESSAO: Retomando aventura.\n\n{txt}\n\nSISTEMA: Recapitule, insira personagens ativos na cena e pergunte próxima ação.",m=u.message)
        await rp(u.message,resp)
        cstate.pop(uid,None)
        return

    # Criação: esperando nome
    if st and st.get("step")=="nome" and st.get("chat_id")==cid:
        st["nome"]=txt.strip()[:30]
        ficha=build_ficha(st)
        st["built_ficha"]=ficha

        # Se tem Tecnomancia, oferecer seleção de scripts
        tecno_skill=ficha.get("pericias",{}).get("tecnomancia",0)
        if tecno_skill>=1:
            max_scripts=DL.calc_max_scripts(1,tecno_skill)
            available=DL.get_available_scripts(tecno_skill)
            st["step"]="tecno_select"
            st["tecno_remaining"]=max_scripts
            st["tecno_selected"]=[]
            st["tecno_available"]=available
            btns=[Btn(f"🧠 {v['nome']} ({v['ram']}RAM)",callback_data=f"ts:{k}") for k,v in sorted(available.items(),key=lambda x:x[1]["ram"])]
            await u.message.reply_text(
                f"🧠 *TECNOMANCIA — Seleção de Scripts*\n━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 Tecnomancia +{tecno_skill} → *{max_scripts} scripts* disponíveis\n"
                f"Restam: *{max_scripts}*\n\nSelecione seus scripts iniciais:",
                reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")
            return

        # Sem tecnomancia — salva direto
        await _save_and_finish(u.message,uid,un,cid,ficha)
        return

    # Jogo normal — com interceptor
    ch=gc(cid)
    try:
        resp=await ask(ch,f"[Jogador: {un}]: {txt}",m=u.message)
        th(cid)
        clean=await intercept_and_sync(resp,cid,msg=u.message)
        await rp(u.message,clean)
    except Exception as e:
        log.error(f"Msg:{e}");await u.message.reply_text("⚠️ Interferência.")

async def on_err(u,c): log.error(f"Err:{c.error}")

# ══════ MAIN ══════
def main():
    DL.ensure_loaded()
    app=Application.builder().token(TG).build()
    for cmd,fn in[("start",cmd_start),("reset",cmd_reset),("ajuda",cmd_help),("help",cmd_help),
        ("iniciar",cmd_iniciar),("novojogo",cmd_novojogo),("criarpersonagem",cmd_criar),
        ("rolar",cmd_rolar),("roll",cmd_rolar),("regras",cmd_regras),("glossario",cmd_glossario),
        ("ficha",cmd_ficha),("fichas",cmd_fichas),("deletarficha",cmd_deletar),("levelup",cmd_levelup),("implante",cmd_implante),
        ("salvarsessao",cmd_salvar_sessao),("sessoes",cmd_sessoes),
        ("cargarsessao",cmd_cargarsessao),("contexto",cmd_contexto)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,on_msg))
    app.add_error_handler(on_err)
    if WH: app.run_webhook(listen="0.0.0.0",port=PT,url_path=TG,webhook_url=f"{WH}/{TG}")
    else: app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":main()
