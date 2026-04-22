"""
🌌 Passagem Sombria v3.0 — RPG Master Companion Bot
Diretrizes 1-9 implementadas. Bot = lógica/estado. IA = narração.
"""
import os,json,logging,asyncio,random as rng,re,unicodedata
from datetime import datetime,timezone
from telegram import Update,InlineKeyboardButton as Btn,InlineKeyboardMarkup as KBD
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes
import google.generativeai as genai
from google.api_core import exceptions as gex
from supabase import create_client
from glossary import (ATTR_KEYS,ATTR_LABELS,ATTR_SHORT,PERICIAS_ATTR,PERICIAS_NOMES,calc_mod,
    RACAS_BTN,CLASSES_BTN,FILOS_BTN)
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
DICE_RE=re.compile(r'/(\d*)d(\d+)([+-]\d+)?')  # Diretriz 4: regex dice
def _norm(s): return unicodedata.normalize("NFKD",s.lower()).encode("ascii","ignore").decode()

SYSP=f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".
Setting: nosso Sistema Solar. Use como pilar narrativo principal.
ESTILO: PT-BR, sombrio/cinematográfico. Emojis temáticos. Separadores ━━━ em combate. Máx 800 palavras.
REGRA DE INTERFACE: NÃO inclua barras de status de PV ou CD nas suas respostas, a menos que o jogador pergunte expressamente.
Formato rolagem: 🎲 1d20(14)+Mod(3)+Per(2)=19 vs CD15 → ✅

🛑 REGRA DE OURO — AGÊNCIA DOS JOGADORES:
- NUNCA tome decisões, declare ações ou crie diálogos para os PCs.
- Descreva ambiente, controle NPCs, narre consequências das ações DELES.
- Quando houver apenas 1 jogador, narre no SINGULAR ("O que você faz?").
- Quando houver múltiplos, narre no PLURAL ("O que vocês fazem?").
- MODO ESCUTA: Se os jogadores estiverem APENAS conversando entre si, planejando estratégias, ou fazendo roleplay de diálogo (sem interagir com o cenário, sem falar com NPCs e sem rolar dados), responda EXATAMENTE com a tag [ESCUTANDO]. Não narre absolutamente mais nada, apenas observe.

🧑‍🚀 IDENTIFICAÇÃO DE TURNO:
- Cada mensagem do jogador chega no formato: [Usuário: @nick | Personagem: Nome] diz: texto
- Use o NOME DO PERSONAGEM para se referir ao jogador na narração.
- NUNCA confunda jogadores. Cada ação é de quem mandou.

🎲 ROLAGENS DE DADOS:
- Quando um jogador tentar ação com risco, PEÇA O TESTE (ex: "Faça /1d20+3 para Furtividade CD 15").
- O bot calcula automaticamente e injeta: [SISTEMA: Personagem rolou NdN+X = Total]
- Ao receber um resultado de [SISTEMA:], narre a consequência IMEDIATA baseada no valor.

📋 CONSCIÊNCIA DA FICHA (Diretriz 7):
- Você recebe o bloco FICHAS_ATIVAS com todos os dados dos jogadores.
- Quando um jogador perguntar "Quais meus status?", "O que tenho?", "Qual minha vida?",
  "Quais minhas tecnomancias?", consulte FICHAS_ATIVAS e responda com dados REAIS.
- NUNCA invente itens, status ou habilidades que não estejam no bloco.

🧠 TECNOMANCIA:
- RAM Máx = 1 + Mod.Int + (Tecnomancia//2) + (+1 nível ímpar). DL recupera.
- Scripts Conhecidos = Nível + Perícia (mín 3).
- Tiers: +1 a +3 = Básicas | +4 a +6 = +Injeções | +7+ = +Protocolos.
- OVERCLOCK (sem RAM): 1d6 psíquico por ponto faltante. Falha Crítica(1)=falha+dano+Atordoado.

🦾 IMPLANTES:
- Limite seguro = max(2+Mod.Con, 1).
- Para instalar narrativamente: use tag [IMPLANTE_ADD:id_implante:nome_personagem]
- O bot calcula tolerância, aplica penalidades e atualiza a ficha automaticamente.
- Você receberá um relatório médico [SISTEMA MÉDICO: ...]. Narre a reação do corpo.

🚀 COMBATE ESPACIAL (Diretriz 8):
- CD Nave = 10 + Manobrabilidade + Mod.Pilotagem do piloto.
- Exija testes de Pilotagem para manobras. Use a CD da nave do bestiário/frota.
- Tipos de dano: EMP = 2x vs escudos, ½ vs casco | Balístico = +1 dado vs casco | Energia = equilibrado
- Narre impacto nos subsistemas: escudo caindo, casco rachando, motor travando.
- Estações: Leme(evasiva), Artilharia(fogo), Engenharia(reparo/escudo), Sensores(hackear fraqueza).
- Cada tripulante opera UMA estação por turno.

CRIAÇÃO DE FICHAS É FEITA PELO BOT. VOCÊ NÃO CRIA FICHAS.

═══ TAGS DE ESTADO (OBRIGATÓRIO — NO FINAL de cada resposta) ═══
[XP:valor:alvo:motivo] — [XP:25:todos:Derrotou pirata]
[HP:valor:alvo] — [HP:-5:Jonas]
[ITEM_ADD:nome:alvo] — [ITEM_ADD:Pistola Laser:Jonas]
[ITEM_DEL:nome:alvo] — [ITEM_DEL:Granada:Maria]
[CG:valor:alvo] — [CG:-100:Jonas]
[RAM:valor:alvo] — [RAM:-2:Jonas]
[TECNO_ADD:id:alvo] — [TECNO_ADD:firewall:Jonas]
[TECNO_DEL:id:alvo] — [TECNO_DEL:ping:Jonas]
[IMPLANTE_ADD:id:alvo] — [IMPLANTE_ADD:olho:Jonas]
[ATTR:atrib:valor:alvo] — [ATTR:forca:+1:Jonas]
[PER:pericia:valor:alvo] — [PER:furtividade:+1:Jonas]
IDs scripts: ping choque query bateria scanner jammer glitch trava rollback firewall travar_arma curto_arm hack_motor ejetar_pente cegueira drenar sobrecarga desativar loop torreta hack_nav apagao inverter reator marionete emp ejetar_piloto reparo_nave formatar gravidade
IDs implantes: chip_ram olho interface_nav tradutor mira placas coracao filtro adrenalina bateria_int braco estabilizador mantis pernas ancoras

REFERÊNCIA MECÂNICA: {RPG}"""

genai.configure(api_key=GK)
mdl=genai.GenerativeModel("gemini-2.5-flash-lite",system_instruction=SYSP,
    generation_config=genai.GenerationConfig(temperature=0.85,max_output_tokens=1500))

# Passo 1: Variável de Trava de Sessão adicionada
chats:dict={};cstate:dict={};jogo_ativo:dict={}

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
        for k,v in updates.items(): clean[k]=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
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
    except: pass
    return None

def db_list_fichas(uid, cid):
    if not db: return []
    try: 
        r=db.table("fichas").select("id,nome,raca,classe,nivel,xp").eq("user_id",str(uid)).execute()
        return r.data or []
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

def db_get_all_active(cid):
    if not db: return []
    try:
        r=db.table("fichas_ativas").select("ficha_id").eq("chat_id",str(cid)).execute()
        if not r.data: return []
        ids=[row["ficha_id"] for row in r.data]
        r2=db.table("fichas").select("*").in_("id",ids).execute()
        fichas=[]
        for row in(r2.data or[]):
            for k in["atributos","pericias","habilidades","tecnomancias","armas","inventario","implantes"]:
                if k in row and isinstance(row[k],str):
                    try: row[k]=json.loads(row[k])
                    except: pass
            fichas.append(row)
        return fichas
    except: return []

def db_save_session(cid,t,s):
    if not db: return False
    try: db.table("sessoes").insert({"chat_id":str(cid),"title":t,"summary":s}).execute(); return True
    except: return False
def db_list_sessions(cid):
    if not db: return []
    try: return db.table("sessoes").select("id,title,created_at").eq("chat_id",str(cid)).order("created_at",desc=True).limit(10).execute().data or []
    except: return []
def db_get_session(sid):
    if not db: return None
    try: r=db.table("sessoes").select("*").eq("id",sid).execute(); return r.data[0] if r.data else None
    except: return None

# ══════ INTERCEPTOR (Diretrizes 1,6,7) ══════
STATE_RE=re.compile(r'\[(XP|HP|ITEM_ADD|ITEM_DEL|CG|RAM|TECNO_ADD|TECNO_DEL|IMPLANTE_ADD|ATTR|PER):([^\]]+)\]')

async def intercept_and_sync(text,cid,msg=None):
    if not db: return text
    changes=STATE_RE.findall(text)
    if not changes: return text
    actives=db_get_all_active(cid)
    nm2f={}
    for f in actives:
        nome=f.get("nome","");nm2f[nome.lower()]=f;nm2f[_norm(nome)]=f
    notifs=[];ia_inject=[]
    for tt,params in changes:
        parts=[p.strip() for p in params.split(":")]
        try:
            alvo_raw=parts[-1] if len(parts)>=2 else ""
            alvo=alvo_raw.lower();alvo_n=_norm(alvo_raw)
            def _find():
                if alvo=="todos": return list({id(f):f for f in nm2f.values()}.values()),True
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                return ([f] if f else []),False

            if tt=="XP" and len(parts)>=3:
                val,motivo=int(parts[0]),parts[1]
                tgts,is_all=_find()
                xe=val//(len(tgts)or 1) if is_all else val
                for f in tgts:
                    nx=f.get("xp",0)+xe;db_update_ficha(f["id"],{"xp":nx})
                    nv=f.get("nivel",1);xr=XP_T.get(nv,9999)
                    notifs.append(f"✨ +{xe}XP {f.get('nome','?')} ({nx}/{xr}){' ⬆️ /levelup!' if nx>=xr else ''}")
            elif tt=="HP" and len(parts)>=2:
                val=int(parts[0]);f=(nm2f.get(alvo) or nm2f.get(alvo_n))
                if f:
                    nh=max(0,min(f.get("pv_atual",0)+val,f.get("pv_max",1)));db_update_ficha(f["id"],{"pv_atual":nh})
                    notifs.append(f"{'💚' if val>0 else '🩸'} {f.get('nome','?')}: {val:+d}PV → ❤️{nh}/{f.get('pv_max','?')}")
            elif tt=="ITEM_ADD" and len(parts)>=2:
                item=parts[0];tgts,_=_find()
                for f in tgts:
                    inv=list(f.get("inventario",[]));inv.append(item);db_update_ficha(f["id"],{"inventario":inv})
                    notifs.append(f"🎒 {f.get('nome','?')} +{item}")
            elif tt=="ITEM_DEL" and len(parts)>=2:
                item=parts[0];f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    inv=list(f.get("inventario",[]));
                    if item in inv:inv.remove(item)
                    db_update_ficha(f["id"],{"inventario":inv})
                    notifs.append(f"🎒 {f.get('nome','?')} -{item}")
            elif tt=="CG" and len(parts)>=2:
                val=int(parts[0]);tgts,_=_find()
                for f in tgts:
                    nc=max(0,f.get("creditos",0)+val);db_update_ficha(f["id"],{"creditos":nc})
                    notifs.append(f"{'💎' if val>0 else '💸'} {f.get('nome','?')}: {val:+d}CG → {nc}")
            elif tt=="RAM" and len(parts)>=2:
                val=int(parts[0]);f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    nr=max(0,min(f.get("ram_atual",0)+val,f.get("ram_max",0)));db_update_ficha(f["id"],{"ram_atual":nr})
            elif tt=="TECNO_ADD" and len(parts)>=2:
                sid2=parts[0].lower();f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and sid2 in DL.TECNO_SCRIPTS:
                    tc=list(f.get("tecnomancias",[])or[])
                    if sid2 not in tc: tc.append(sid2);db_update_ficha(f["id"],{"tecnomancias":tc})
                    notifs.append(f"🧠 {f.get('nome','?')} aprendeu: *{DL.TECNO_SCRIPTS[sid2]['nome']}*")
            elif tt=="TECNO_DEL" and len(parts)>=2:
                sid2=parts[0].lower();f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    tc=list(f.get("tecnomancias",[])or[])
                    if sid2 in tc: tc.remove(sid2);db_update_ficha(f["id"],{"tecnomancias":tc})
                    notifs.append(f"🧠 {f.get('nome','?')} perdeu script")

            # ── DIRETRIZ 6: Cirurgia autônoma de implantes ──
            elif tt=="IMPLANTE_ADD" and len(parts)>=2:
                impl_id=parts[0].lower();f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and impl_id in DL.IMPLANTES_DATA:
                    imp=DL.IMPLANTES_DATA[impl_id]
                    impl_list=list(f.get("implantes",[])or[]);con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
                    limite=DL.calc_implant_limit(con_mod);qtd=len(impl_list)
                    impl_list.append(imp["nome"]);ups={"implantes":impl_list}
                    # Mecânica do implante
                    mec=imp.get("mecanica",{})
                    if "ram_max" in mec: ups["ram_max"]=f.get("ram_max",0)+mec["ram_max"]
                    if "cd" in mec: ups["cd"]=f.get("cd",10)+mec["cd"]
                    if "pv_max" in mec: ups["pv_max"]=f.get("pv_max",0)+mec["pv_max"];ups["pv_atual"]=f.get("pv_atual",0)+mec["pv_max"]
                    resultado="Operação Segura"
                    if qtd>=limite:
                        extra=qtd-limite+1
                        if extra==1:  # Perda de Humanidade
                            dano=rng.randint(1,6)
                            ups["pv_max"]=f.get("pv_max",0)+(mec.get("pv_max",0))-dano
                            ups["pv_atual"]=min(f.get("pv_atual",0),ups["pv_max"])
                            notas=f.get("notas","")+"| Desvantagem Persuasão (implante) "
                            ups["notas"]=notas
                            resultado=f"Sobrecarga Nv1: perdeu {dano} Vida Máxima permanente"
                        elif extra==2:  # Curto-Circuito
                            notas=f.get("notas","")+"| Curto-Circuito (1-2 natural=1d6 elétrico+atordoa) "
                            ups["notas"]=notas
                            resultado="Sobrecarga Nv2: Curto-Circuito instalado"
                        elif extra>=3:  # Morte
                            ups["pv_atual"]=0;ups["pv_max"]=0
                            resultado="COLAPSO NEURAL — ÓBITO CIBERNÉTICO"
                    db_update_ficha(f["id"],ups)
                    nome_p=f.get("nome","?")
                    notifs.append(f"🦾 {nome_p}: *{imp['nome']}* — {resultado}")
                    ia_inject.append(f"[SISTEMA MÉDICO: Implante {imp['nome']} instalado em {nome_p}. Resultado: {resultado}. Ficha atualizada.]")

            elif tt=="ATTR" and len(parts)>=3:
                ak=parts[0].lower();val=int(parts[1]);f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f and ak in ATTR_KEYS:
                    a=dict(f.get("atributos",{}));a[ak]=a.get(ak,8)+val;db_update_ficha(f["id"],{"atributos":a})
                    notifs.append(f"📊 {f.get('nome','?')}: {ATTR_SHORT[ATTR_KEYS.index(ak)]} {val:+d}")
            elif tt=="PER" and len(parts)>=3:
                pk=parts[0].lower();val=int(parts[1]);f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f:
                    p=dict(f.get("pericias",{}));p[pk]=p.get(pk,0)+val;db_update_ficha(f["id"],{"pericias":p})
                    notifs.append(f"🎯 {f.get('nome','?')}: {PERICIAS_NOMES.get(pk,pk)} {val:+d}")
        except Exception as e: log.warning(f"Intercept:{tt}:{params}→{e}")
    clean=STATE_RE.sub("",text).strip()
    if notifs and msg:
        try: await msg.reply_text("📡 *Sync:*\n"+"\n".join(notifs),parse_mode="Markdown")
        except: pass
    # Injeta relatórios médicos na IA
    if ia_inject:
        try:
            ch=gc(cid)
            for inj in ia_inject: await ask(ch,inj)
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
    if st.get("bonus_attrs"):
        for k,v in st["bonus_attrs"].items(): attrs[k]=attrs.get(k,8)+v
    dm=calc_mod(attrs["destreza"]);arm=c["armadura"]
    cd=10+(dm if arm["tipo"]=="leve" else min(dm,2) if arm["tipo"]=="media" else 0)+arm["cd"]
    per=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items(): per[pk]=per.get(pk,0)+pv2
    if st.get("bonus_pericias"):
        for pk,pv2 in st["bonus_pericias"].items(): per[pk]=per.get(pk,0)+pv2
    tec=per.get("tecnomancia",0);im=calc_mod(attrs["inteligencia"]);ram=max(1+im+tec//2,0)
    init=dm+(2 if st["filosofia"]=="cod_sobrevivente" or st["classe"]=="batedor" else 0)
    equip=list(c.get("equip_fixo",[]));
    if st.get("equip_choice"):equip.insert(0,st["equip_choice"])
    return {"nome":st.get("nome","?"),"raca":r["nome"],"classe":c["nome"],"filosofia":fl[0],
        "nivel":1,"xp":0,"pv_atual":st["pv"],"pv_max":st["pv"],"cd":cd,
        "ram_atual":ram,"ram_max":ram,"iniciativa":init,"deslocamento":r.get("desloc",9),
        "atributos":attrs,"pericias":per,"habilidades":[f"{fl[0]}: {fl[1]}"],
        "tecnomancias":list(st.get("tecno_selected",[])),
        "armas":[x for x in equip if any(w in x for w in["1d","2d","3d"])],
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
            log.error(f"G:{e}");
            if i==ret-1: raise
            await asyncio.sleep(5)
    return "⚠️ Mestre offline."

async def rp(m,t):
    for p in([t[i:i+4000] for i in range(0,len(t),4000)] if len(t)>4000 else [t]):
        try: await m.reply_text(p,parse_mode="Markdown")
        except: await m.reply_text(p)

def mkb(items,pfx,cols=2):
    bs=[Btn(v,callback_data=f"{pfx}:{k}") for k,v in items.items()]
    return KBD([bs[i:i+cols] for i in range(0,len(bs),cols)])

def ff(f):
    a=f.get("atributos",{})
    arms="\n".join(f"  ⚔️ {x}" for x in(f.get("armas",[])or[]))or"  —"
    per=", ".join(f"{PERICIAS_NOMES.get(k,k)}+{v}" for k,v in(f.get("pericias",{})or{}).items() if v)or"—"
    habs="\n".join(f"  🔹 {h}" for h in(f.get("habilidades",[])or[]))or"  —"
    tec_ids=f.get("tecnomancias",[])or[]
    tecno=", ".join(DL.TECNO_SCRIPTS.get(t,{}).get("nome",t) for t in tec_ids) if tec_ids else "—"
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

def inject_fichas_prompt(fichas):
    if not fichas: return ""
    lines=["FICHAS_ATIVAS:\n"]
    for f in fichas:
        a=f.get("atributos",{});tec_ids=f.get("tecnomancias",[])or[]
        tnames=[DL.TECNO_SCRIPTS.get(t,{}).get("nome",t) for t in tec_ids]
        lines.append(f"--- {f.get('nome','?')} ({f.get('raca','?')} {f.get('classe','?')} Nv{f.get('nivel',1)}) ---")
        lines.append(f"PV:{f.get('pv_atual')}/{f.get('pv_max')} CD:{f.get('cd')} RAM:{f.get('ram_atual')}/{f.get('ram_max')}")
        lines.append(f"For:{a.get('forca',8)} Des:{a.get('destreza',8)} Con:{a.get('constituicao',8)} Int:{a.get('inteligencia',8)} Sab:{a.get('sabedoria',8)} Car:{a.get('carisma',8)}")
        lines.append(f"Per:{f.get('pericias',{})} Armas:{f.get('armas',[])} Inv:{f.get('inventario',[])}")
        lines.append(f"CG:{f.get('creditos',100)} Tecno:{tnames} Implantes:{f.get('implantes',[])} Filosofia:{f.get('filosofia','')}\n")
    return "\n".join(lines)

async def _save_and_finish(msg,uid,un,cid,ficha):
    fid=db_create_ficha(uid,un,cid,ficha)
    if fid:
        db_set_active(uid,cid,fid);ficha["id"]=fid
        await rp(msg,f"✅ *{ficha['nome']}* registrado! (ID:{fid})")
        await rp(msg,ff(ficha))
        ch=gc(cid);await ask(ch,f"FICHAS_ATIVAS:\n{inject_fichas_prompt([ficha])}\nPersonagem criado.",m=msg)
    else: await msg.reply_text("⚠️ Erro ao salvar.")
    cstate.pop(uid,None)
    await msg.reply_text("🚀 /iniciar para sessão ou /novojogo para aventura.",reply_markup=MAIN_KB)

async def _install_implant(msg,f,impl_id):
    imp=DL.IMPLANTES_DATA[impl_id];impl_list=list(f.get("implantes",[])or[])
    impl_list.append(imp["nome"]);ups={"implantes":impl_list,"creditos":f.get("creditos",0)-imp["preco"]}
    mec=imp.get("mecanica",{})
    if "ram_max" in mec: ups["ram_max"]=f.get("ram_max",0)+mec["ram_max"]
    if "cd" in mec: ups["cd"]=f.get("cd",10)+mec["cd"]
    if "pv_max" in mec: ups["pv_max"]=f.get("pv_max",0)+mec["pv_max"]
    db_update_ficha(f["id"],ups)
    await msg.reply_text(f"🦾 *{imp['nome']}* instalado!\n💎 -{imp['preco']}CG → {ups['creditos']}CG\n_{imp['efeito']}_",parse_mode="Markdown")

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

# ══════ HANDLERS ══════
async def cmd_start(u,c): await u.message.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_reset(u,c):
    chats.pop(u.effective_chat.id,None)
    # Passo 2: Desliga a sessão e silencia o Mestre
    jogo_ativo.pop(u.effective_chat.id,None)
    await u.message.reply_text("🔄 _Memória neural purgada. Mestre silenciado._",reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_help(u,c): await rp(u.message,"📡 *PROTOCOLOS*\n━━━━━━━━━━━━━━━━━━━━\n⚔️ /iniciar /novojogo /criarpersonagem\n🎲 Rolagens diretas: /1d20 /2d8+4\n💾 /ficha /fichas /deletarficha /levelup /implante\n📚 /salvarsessao /sessoes /cargarsessao ID /contexto\n📖 /glossario /regras /reset /ajuda")

async def cmd_debug(u,c):
    """Ferramenta de Troubleshooting para limpar o Cache e testar o DB."""
    # 1. Limpa a memória REAL do bot (reinicia o Data Loader)
    DL._loaded = False
    DL.DISPLAY.clear()
    DL.ensure_loaded() # Força o bot a ir ler o Supabase AGORA
    
    txt = "⚙️ *DIAGNÓSTICO DO SISTEMA*\n━━━━━━━━━━━━━━━━━━━━\n"
    txt += "✅ Memória limpa e recarregada do Supabase.\n\n"
    
    # 2. Testa um Dicionário (Submenus de Raças)
    r = DL.get_display("display_racas", {})
    if isinstance(r, dict) and r:
        txt += f"🟢 *Raças (Dicionário):* OK! Encontrou {len(r)} raças.\n"
    else:
        txt += f"🔴 *Raças (Dicionário):* ERRO. Retornou vazio ou formato incorreto.\n"
        
    # 3. Testa um Texto Direto (Naves)
    n = DL.get_display("display_naves", "")
    if isinstance(n, str) and len(n) > 10:
        txt += f"🟢 *Naves (Texto):* OK! Carregou {len(n)} caracteres.\n"
    else:
        txt += f"🔴 *Naves (Texto):* ERRO. Retornou vazio ou formato incorreto.\n"
        
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_regras(u,c):
    """Diretriz 5: busca regras do banco."""
    DL.ensure_loaded()
    txt=DL.REGRAS_TEXT
    if txt: await rp(u.message,txt if isinstance(txt,str) else json.dumps(txt))
    else: await rp(u.message,"📖 *MANUAL*\n━━━━━━━━━━━━━━━━━━━━\n🎲 1d20+Atrib+Per ≥ CD\n⚔️ Melee:dado+For | 🔫 Ranged:dado+Des\n🛡️ CD:10+Des+Arm\n💥20=Crítico|💀1=Falha\n❤️0PV=Morte|🔋Pente:3t|🧠RAM:1+Int+½Tecno")

async def cmd_glossario(u,c): await u.message.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")

async def cmd_iniciar(u,c):
    cid=u.effective_chat.id;uid=u.message.from_user.id
    fichas=db_list_fichas(uid,cid)
    if not fichas: await u.message.reply_text("❌ Sem personagens. /criarpersonagem");return
    btns=[Btn(f"⚔️ {f['nome']} (Nv{f['nivel']})",callback_data=f"sel:{f['id']}") for f in fichas]
    await u.message.reply_text("🧑‍🚀 *Selecione personagem:*",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")

async def cmd_novojogo(u,c):
    cid=u.effective_chat.id
    actives=db_get_all_active(cid)
    if not actives: await u.message.reply_text("❌ Usem /iniciar primeiro.");return
    play_kb=KBD([[Btn("🆕 Nova Aventura",callback_data="play:new")],[Btn("📜 Continuar",callback_data="play:context")]])
    await u.message.reply_text("🌌 *Fichas sincronizadas.* Como iniciar?",reply_markup=play_kb,parse_mode="Markdown")

async def cmd_criar(u,c):
    cstate[u.message.from_user.id]={"step":"raca","chat_id":u.effective_chat.id}
    await u.message.reply_text("🧑‍🚀 *RECRUTAMENTO*\n━━━━━━━━━━━━━━━━━━━━\n📋 1/5: *Origem*",reply_markup=mkb(RACAS_BTN,"r",2),parse_mode="Markdown")

async def cmd_ficha(u,c):
    f=db_get_active(u.message.from_user.id,u.effective_chat.id)
    if not f: await u.message.reply_text("❌ /iniciar");return
    await rp(u.message,ff(f))

async def cmd_fichas(u,c):
    fs=db_list_fichas(u.message.from_user.id,u.effective_chat.id)
    if not fs: await u.message.reply_text("📋 Vazio.");return
    await rp(u.message,"📋 *PERSONAGENS:*\n"+"\n".join(f"• ID *{f['id']}* — {f['nome']} ({f['raca']} {f['classe']} Nv{f['nivel']})" for f in fs)+"\n/deletarficha ID")

async def cmd_deletar(u,c):
    if not c.args: await u.message.reply_text("❌ /deletarficha ID");return
    try:fid=int(c.args[0])
    except: return
    uid=u.message.from_user.id;f=db_get_ficha(fid)
    if not f: return
    if str(f.get("user_id"))!=str(uid) and not(ADMIN and str(uid)==str(ADMIN)): return
    if db_delete_ficha(fid): await u.message.reply_text(f"🗑️ *{f.get('nome','?')}* eliminado.",parse_mode="Markdown")

async def cmd_levelup(u,c):
    cid,uid,un=u.effective_chat.id,u.message.from_user.id,u.message.from_user.first_name or"?"
    f=db_get_active(uid,cid)
    if not f: await u.message.reply_text("❌ Sem ativo.");return
    nv,xp,nm=f.get("nivel",1),f.get("xp",0),f.get("nome","?")
    if nv>=10: await u.message.reply_text("🌟 Máximo!");return
    xr=XP_T.get(nv,9999)
    if xp<xr: await u.message.reply_text(f"❌ *{nm}*: {xp}/{xr}XP (faltam {xr-xp})",parse_mode="Markdown");return
    rk=next((k for k,v in DL.RACAS_STATS.items() if v["nome"]==f.get("raca","")),None)or"terraqueo"
    faces=int(DL.RACAS_STATS[rk]["dado_nv"].split("d")[1])
    rh=rng.randint(1,faces);cm=calc_mod(f.get("atributos",{}).get("constituicao",8))
    hg=max(rh+cm,1);np2=f["pv_max"]+hg
    ups={"nivel":nv+1,"pv_max":np2,"pv_atual":np2}
    if(nv+1)%2==1 and nv+1>=3: ups["ram_max"]=f.get("ram_max",0)+1;ups["ram_atual"]=ups["ram_max"]
    db_update_ficha(f["id"],ups)
    txt=f"⬆️ *{nm}* → Nv{nv+1}!\n━━━━━━━━━━━━━━━━━━━━\n❤️ 🎲{DL.RACAS_STATS[rk]['dado_nv']}={rh}+Con({cm:+d})=+{hg} → *{np2}PV*\n"
    if(nv+1)%2==1 and nv+1>=3: txt+="🧠 +1 RAM\n"
    await rp(u.message,txt)
    cstate[uid]={"step":"lvl_attr","chat_id":cid,"ficha_id":f["id"],"novo_nv":nv+1}
    a=f.get("atributos",{})
    btns=[Btn(f"{ATTR_LABELS[i]} ({a.get(k,8)}→{a.get(k,8)+1})",callback_data=f"la:{k}") for i,k in enumerate(ATTR_KEYS)]
    await u.message.reply_text("💪 *+1 Atributo:*",reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")

async def cmd_implante(u,c):
    f=db_get_active(u.message.from_user.id,u.effective_chat.id)
    if not f: await u.message.reply_text("❌ /iniciar");return
    impl=f.get("implantes",[])or[];con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
    lim=DL.calc_implant_limit(con_mod);qtd=len(impl)
    aviso=""
    if qtd>=lim: aviso=f"\n⚠️ *ACIMA DO LIMITE* ({qtd}/{lim})!"
    txt=f"🦾 *{f.get('nome','?')}*\n━━━━━━━━━━━━━━━━━━━━\nLimite: {lim} | Instalados: {qtd}{aviso}\n💎 {f.get('creditos',0)}CG"
    if impl: txt+="\n"+"\n".join(f"  • {i}" for i in impl)
    cat_kb=KBD([[Btn("🧠 Cabeça",callback_data="ic:cabeça")],[Btn("🫀 Torso",callback_data="ic:torso")],[Btn("🦿 Membros",callback_data="ic:membros")],[Btn("🔙",callback_data="m:back")]])
    await u.message.reply_text(txt,reply_markup=cat_kb,parse_mode="Markdown")

async def cmd_salvar_sessao(u,c):
    if not db:return
    cid=u.effective_chat.id;ch=gc(cid)
    if cid not in chats: await u.message.reply_text("❌ Sem sessão.");return
    await u.message.reply_text("📝 _Compilando..._",parse_mode="Markdown")
    s=await ask(ch,"RESUMO_SESSAO: Resuma tudo factual. 1000 palavras max.",m=u.message)
    t=await ask(ch,"Título CURTO 6 palavras. Só título.")
    t=t.strip().strip('"')[:60]
    if db_save_session(cid,t,s): await u.message.reply_text(f"✅ *{t}*",parse_mode="Markdown");await rp(u.message,s)

async def cmd_sessoes(u,c):
    sl=db_list_sessions(u.effective_chat.id)
    if not sl: await u.message.reply_text("📚 Vazio.");return
    await rp(u.message,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')}" for s in sl)+"\n/cargarsessao ID")

async def cmd_cargarsessao(u,c):
    if not c.args: return
    try:sid=int(c.args[0])
    except: return
    s=db_get_session(sid)
    if not s or s.get("chat_id")!=str(u.effective_chat.id): return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
    if ctx: await ask(ch,ctx)
    
    # Passo 4 (parte a): Liga o Mestre ao carregar sessão anterior
    jogo_ativo[cid] = True
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Retomando '{s.get('title')}'.\n{s.get('summary')}\nRecapitule.",m=u.message))

async def cmd_contexto(u,c):
    txt=u.message.text.replace("/contexto","",1).strip()
    if not txt: await u.message.reply_text("📎 `/contexto texto...`",parse_mode="Markdown");return
    cid=u.effective_chat.id;chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
    if ctx: await ask(ch,ctx)
    
    # Passo 4 (parte b): Liga o Mestre ao dar contexto manual
    jogo_ativo[cid] = True
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Importado.\n{txt}\nConfirme.",m=u.message))
    if db:db_save_session(cid,"📎 Importado",txt)

# ══════ CALLBACK ROUTER ══════
async def on_cb(u:Update,c:ContextTypes.DEFAULT_TYPE):
    q=u.callback_query;await q.answer();d=q.data;m=q.message
    uid=q.from_user.id;cid=m.chat_id;un=q.from_user.first_name or"?"

    if d in("m:back","m:start"): await m.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
    elif d=="m:init":
        fichas=db_list_fichas(uid,cid)
        if not fichas: await m.reply_text("❌ Sem personagens.");return
        btns=[Btn(f"⚔️ {f['nome']} (Nv{f['nivel']})",callback_data=f"sel:{f['id']}") for f in fichas]
        await m.reply_text("🧑‍🚀 *Selecione:*",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")
    elif d.startswith("sel:"):
        fid=int(d[4:]);db_set_active(uid,cid,fid);f=db_get_ficha(fid)
        if f:
            await m.reply_text(f"✅ *{f.get('nome','?')}* ativado!",parse_mode="Markdown")
            await rp(m,ff(f))
            ch=gc(cid);await ask(ch,f"FICHAS_ATIVAS:\n{inject_fichas_prompt([f])}",m=m)
            play_kb=KBD([[Btn("🆕 Nova Aventura",callback_data="play:new")],[Btn("📜 Continuar",callback_data="play:context")]])
            await m.reply_text("🌌 *Sincronizado.* Como iniciar?",reply_markup=play_kb,parse_mode="Markdown")
    elif d=="m:criar":
        cstate[uid]={"step":"raca","chat_id":cid}
        await m.reply_text("🧑‍🚀 *RECRUTAMENTO* 1/5: *Origem*",reply_markup=mkb(RACAS_BTN,"r",2),parse_mode="Markdown")
    elif d=="m:mfichas":
        fs=db_list_fichas(uid,cid)
        if not fs: await m.reply_text("📋 Vazio.");return
        await rp(m,"📋 *PERSONAGENS:*\n"+"\n".join(f"• ID *{f['id']}* — {f['nome']} ({f['raca']} {f['classe']} Nv{f['nivel']})" for f in fs))
    elif d=="m:csess":
        sl=db_list_sessions(cid)
        if not sl: await m.reply_text("📚 Vazio.");return
        await rp(m,"📚\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')}" for s in sl)+"\n/cargarsessao ID")
    elif d=="m:gloss": await m.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")
    elif d=="m:help": await rp(m,"📡 /iniciar /novojogo /criarpersonagem /1d20 /ficha /fichas /deletarficha /levelup /implante /salvarsessao /sessoes /cargarsessao /contexto /glossario /regras /reset")

    # Jogo
    elif d=="play:new":
        chats.pop(cid,None);ch=gc(cid);actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
        n_jogadores=len(actives)
        modo="singular" if n_jogadores<=1 else "plural"
        if ctx: await ask(ch,f"MODO_NARRATIVA: {modo}. {n_jogadores} jogador(es) ativo(s).\n{ctx}")
        
        # Passo 3: Liga o Mestre ao começar um novo jogo!
        jogo_ativo[cid] = True
        
        await q.edit_message_text("🌌 _Inicializando..._",parse_mode="Markdown")
        await rp(m,await ask(ch,"SISTEMA: NOVA aventura no Sistema Solar. Cena épica. Gancho. Opções. Conciso.",m=m))
    elif d=="play:context":
        cstate[uid]={"step":"wait_context","chat_id":cid}
        await q.edit_message_text("📜 *Envio de Contexto*\nDigite o resumo da aventura anterior:",parse_mode="Markdown")

    # Glossário — busca do banco via DL.get_display
    elif d=="g:racas": await m.reply_text("🌌 *RAÇAS:*",reply_markup=mkb(RACAS_BTN,"gr",2),parse_mode="Markdown")
    elif d=="g:classes": await m.reply_text("⚔️ *CLASSES:*",reply_markup=mkb(CLASSES_BTN,"gc",2),parse_mode="Markdown")
    elif d.startswith("gr:"):
        data=DL.get_display("display_racas",{});txt=data.get(d[3:],"❌") if isinstance(data,dict) else "❌"
        await rp(m,txt);await m.reply_text("🔙",reply_markup=KBD([[Btn("🌌",callback_data="g:racas"),Btn("📖",callback_data="m:gloss")]]))
    elif d.startswith("gc:"):
        data=DL.get_display("display_classes",{});txt=data.get(d[3:],"❌") if isinstance(data,dict) else "❌"
        await rp(m,txt);await m.reply_text("🔙",reply_markup=KBD([[Btn("⚔️",callback_data="g:classes"),Btn("📖",callback_data="m:gloss")]]))
    elif d=="g:ab": await rp(m,DL.get_display("display_armas_brancas","❌ Dados não carregados. Execute seed_dados_rpg.sql"))
    elif d=="g:af": await rp(m,DL.get_display("display_armas_fogo","❌"))
    elif d=="g:ar": await rp(m,DL.get_display("display_armaduras","❌"))
    elif d=="g:im": await rp(m,DL.get_display("display_implantes","❌"))
    elif d=="g:fe": await rp(m,DL.get_display("display_ferramentas","❌"))
    elif d=="g:mo": await rp(m,DL.get_display("display_modificacoes","❌"))
    elif d=="g:na": await rp(m,DL.get_display("display_naves","❌"))
    elif d=="g:fi": await rp(m,DL.get_display("display_filosofias","❌"))
    elif d=="g:te": await m.reply_text("🧠",reply_markup=KBD([[Btn("🟢 Básicas",callback_data="gt:b")],[Btn("🟡 Injeções",callback_data="gt:i")],[Btn("🔴 Protocolos",callback_data="gt:p")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d=="gt:b": await rp(m,DL.get_display("display_tecno_basicas","❌"))
    elif d=="gt:i": await rp(m,DL.get_display("display_tecno_injecoes","❌"))
    elif d=="gt:p": await rp(m,DL.get_display("display_tecno_protocolos","❌"))
    elif d=="g:be": await m.reply_text("👾",reply_markup=KBD([[Btn("🌍 Planetas",callback_data="gb:p")],[Btn("🦎 Fauna",callback_data="gb:f")],[Btn("👾 Vazio",callback_data="gb:v")],[Btn("🔙",callback_data="m:gloss")]]),parse_mode="Markdown")
    elif d=="gb:p": await rp(m,DL.get_display("display_bestiario_planetas","❌"))
    elif d=="gb:f": await rp(m,DL.get_display("display_bestiario_fauna","❌"))
    elif d=="gb:v": await rp(m,DL.get_display("display_bestiario_vazio","❌"))

    # Implantes
    elif d.startswith("ic:"):
        slot=d[3:];f=db_get_active(uid,cid)
        if not f:return
        impls={k:v for k,v in DL.IMPLANTES_DATA.items() if v["slot"]==slot};cred=f.get("creditos",0)
        btns=[Btn(f"{'💎' if cred>=v['preco'] else '🚫'} {v['nome']} ({v['preco']}CG)",callback_data=f"ii:{k}") for k,v in impls.items()]
        btns.append(Btn("🔙",callback_data="m:back"))
        await m.reply_text(f"🦾 *{slot.upper()}* — 💎{cred}CG",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")
    elif d.startswith("ii:"):
        impl_id=d[3:];f=db_get_active(uid,cid)
        if not f or impl_id not in DL.IMPLANTES_DATA:return
        imp=DL.IMPLANTES_DATA[impl_id]
        if f.get("creditos",0)<imp["preco"]: await m.reply_text("❌ Créditos insuficientes.");return
        impl_list=list(f.get("implantes",[])or[]);con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
        lim=DL.calc_implant_limit(con_mod)
        if len(impl_list)>=lim+2: await m.reply_text("💀 IMPOSSÍVEL. Morte certa.");return
        if len(impl_list)>=lim:
            await m.reply_text(f"⚠️ *ACIMA DO LIMITE!*\nInstalar *{imp['nome']}* mesmo assim?",
                reply_markup=KBD([[Btn("⚠️ Confirmar",callback_data=f"ix:{impl_id}")],[Btn("🔙",callback_data="m:back")]]),parse_mode="Markdown")
        else: await _install_implant(m,f,impl_id)
    elif d.startswith("ix:"):
        f=db_get_active(uid,cid)
        if f: await _install_implant(m,f,d[3:])

    # ── Criação ──
    elif d.startswith("r:"):
        k=d[2:];cstate.setdefault(uid,{});cstate[uid].update({"step":"classe","raca":k,"chat_id":cid})
        await q.edit_message_text(f"✅ *{RACAS_BTN[k]}*\n📋 2/5: *Especialização*",parse_mode="Markdown")
        await m.reply_text("⚔️ Selecione:",reply_markup=mkb(CLASSES_BTN,"c",2))
    elif d.startswith("c:"):
        k=d[2:];cstate.setdefault(uid,{});cstate[uid].update({"step":"filosofia","classe":k})
        await q.edit_message_text(f"✅ *{CLASSES_BTN[k]}*\n📋 3/5: *Código*",parse_mode="Markdown")
        await m.reply_text("📜 Selecione:",reply_markup=mkb(FILOS_BTN,"f",2))
    elif d.startswith("f:"):
        k=d[2:];st=cstate.setdefault(uid,{});st.update({"step":"attr_0","filosofia":k})
        vals,dropped=roll_attrs();st["rolled"]=vals;st["all_rolls"]=vals+[dropped];st["dropped"]=dropped
        await q.edit_message_text(f"✅ *{FILOS_BTN[k]}*\n📋 4/5: *Calibração*\n━━━━━━━━━━━━━━━━━━━━\n🎲 2d8×7 (máx16):\n{sorted(st['all_rolls'])}\n❌ Desc: {dropped}\n✅ *{vals}*",parse_mode="Markdown")
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
                try:
                    st["atributos_base"][ATTR_KEYS[5]]=chosen;st["step"]="equip"
                    await _fin_attrs(m,uid)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    await m.reply_text(f"⚠️ *Erro Crítico ao compilar a ficha:*\n`{e}`\nO código travou nessa etapa. Verifique o log do terminal!", parse_mode="Markdown")
        else:
            try:
                st["step"]="equip"
                await q.edit_message_text(f"✅ {ATTR_LABELS[5]}: *{chosen}*",parse_mode="Markdown")
                await _fin_attrs(m,uid)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                await m.reply_text(f"⚠️ *Erro Crítico ao compilar a ficha:*\n`{e}`\nO código travou nessa etapa. Verifique o log do terminal!", parse_mode="Markdown")
    elif d.startswith("eq:"):
        idx=int(d[3:]);st=cstate.get(uid)
        if not st:return
        cls=DL.CLASSES_STATS[st["classe"]];choices=cls.get("equip_escolha",cls.get("equip_escolha_melee",[]))
        if choices:st["equip_choice"]=choices[0][idx]
        await q.edit_message_text(f"✅ *{st.get('equip_choice','?')}*",parse_mode="Markdown")
        if st["raca"]=="terraqueo":
            st["step"]="terra_attr";st["bonus_attrs"]={};st["bonus_attr_remaining"]=4
            btns=[Btn(f"{ATTR_LABELS[i]}",callback_data=f"ta:{k}") for i,k in enumerate(ATTR_KEYS)]
            await m.reply_text("🌍 *Terráqueo:* +4 atributos (máx+2 cada). Restam: *4*",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]),parse_mode="Markdown")
        else: st["step"]="nome";await m.reply_text("✏️ Digite o *nome*:",parse_mode="Markdown")
    elif d.startswith("ta:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="terra_attr":return
        ba=st.setdefault("bonus_attrs",{})
        if ba.get(k,0)>=2: await m.reply_text("⚠️ Máx+2!");return
        ba[k]=ba.get(k,0)+1;st["bonus_attr_remaining"]-=1;rem=st["bonus_attr_remaining"]
        if rem>0:
            btns=[Btn(f"{ATTR_LABELS[i]}(+{ba.get(k2,0)})",callback_data=f"ta:{k2}") for i,k2 in enumerate(ATTR_KEYS) if ba.get(k2,0)<2]
            await q.edit_message_text(f"🌍 {' '.join(f'{ATTR_SHORT[ATTR_KEYS.index(a)]}+{v}' for a,v in ba.items())} | Restam: *{rem}*",parse_mode="Markdown")
            await m.reply_text("+1:",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]))
        else:
            st["step"]="terra_per";st["bonus_pericias"]={};st["bonus_per_remaining"]=3
            per_btns=[Btn(PERICIAS_NOMES[pk],callback_data=f"tp:{pk}") for pk in sorted(PERICIAS_NOMES.keys())]
            await m.reply_text("🌍 *+3 perícias:* Restam: *3*",reply_markup=KBD([per_btns[i:i+3] for i in range(0,len(per_btns),3)]),parse_mode="Markdown")
    elif d.startswith("tp:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="terra_per":return
        bp=st.setdefault("bonus_pericias",{});bp[k]=bp.get(k,0)+1;st["bonus_per_remaining"]-=1
        if st["bonus_per_remaining"]>0:
            per_btns=[Btn(PERICIAS_NOMES[pk],callback_data=f"tp:{pk}") for pk in sorted(PERICIAS_NOMES.keys())]
            await q.edit_message_text(f"🌍 {' '.join(f'{PERICIAS_NOMES.get(a,a)}+{v}' for a,v in bp.items())} | Restam: *{st['bonus_per_remaining']}*",parse_mode="Markdown")
            await m.reply_text("+1:",reply_markup=KBD([per_btns[i:i+3] for i in range(0,len(per_btns),3)]))
        else: st["step"]="nome";await m.reply_text("✏️ Digite o *nome*:",parse_mode="Markdown")

    # Level up
    elif d.startswith("la:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_attr":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        a=f.get("atributos",{});a[k]=a.get(k,8)+1;db_update_ficha(fid,{"atributos":a})
        await q.edit_message_text(f"✅ {ATTR_SHORT[ATTR_KEYS.index(k)]}→*{a[k]}*({calc_mod(a[k]):+d})",parse_mode="Markdown")
        st["step"]="lvl_per";per=f.get("pericias",{})
        limit=5 if st["novo_nv"]<=4 else 7
        all_per=set(list(per.keys())+list(PERICIAS_NOMES.keys()))
        per_btns=[Btn(f"{PERICIAS_NOMES.get(pk,pk)}(+{per.get(pk,0)})",callback_data=f"lp:{pk}") for pk in sorted(all_per) if per.get(pk,0)<limit]
        await m.reply_text("🎯 *+1 Perícia:*",reply_markup=KBD([per_btns[i:i+2] for i in range(0,len(per_btns),2)]),parse_mode="Markdown")
    elif d.startswith("lp:"):
        k=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_per":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        per=f.get("pericias",{});per[k]=per.get(k,0)+1;db_update_ficha(fid,{"pericias":per})
        await q.edit_message_text(f"✅ {PERICIAS_NOMES.get(k,k)}→*+{per[k]}*",parse_mode="Markdown")
        # Verifica novo script
        tecno_skill=per.get("tecnomancia",0);novo_nv=st["novo_nv"]
        if tecno_skill>=1:
            mx=DL.calc_max_scripts(novo_nv,tecno_skill);cur=list(f.get("tecnomancias",[])or[])
            if len(cur)<mx:
                avail=DL.get_available_scripts(tecno_skill)
                avail={k2:v for k2,v in avail.items() if k2 not in cur}
                if avail:
                    st["step"]="lvl_tecno"
                    btns=[Btn(f"🧠 {v['nome']}({v['ram']}R)",callback_data=f"lt:{k2}") for k2,v in sorted(avail.items(),key=lambda x:x[1]["ram"])]
                    await m.reply_text(f"🧠 *Novo script!* ({len(cur)+1}/{mx})",reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")
                    return
        cstate.pop(uid,None);ch=gc(cid);await ask(ch,f"SISTEMA: {f.get('nome','?')} subiu Nv{st['novo_nv']}.",m=m)
        await m.reply_text(f"⬆️ *{f.get('nome','?')}* Nv{st['novo_nv']} completo!",parse_mode="Markdown")

    # Tecnomancia seleção
    elif d.startswith("ts:"):
        sid2=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="tecno_select":return
        if sid2 in st.get("tecno_selected",[]): return
        st.setdefault("tecno_selected",[]).append(sid2);st["tecno_remaining"]-=1
        nm_s=DL.TECNO_SCRIPTS.get(sid2,{}).get("nome",sid2)
        if st["tecno_remaining"]>0:
            avail={k:v for k,v in st["tecno_available"].items() if k not in st["tecno_selected"]}
            btns=[Btn(f"🧠 {v['nome']}({v['ram']}R)",callback_data=f"ts:{k}") for k,v in sorted(avail.items(),key=lambda x:x[1]["ram"])]
            await q.edit_message_text(f"✅ +{nm_s} | Restam: *{st['tecno_remaining']}*",parse_mode="Markdown")
            if btns: await m.reply_text("Próximo:",reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]))
        else:
            ficha=st["built_ficha"];ficha["tecnomancias"]=list(st["tecno_selected"])
            await q.edit_message_text(f"✅ +{nm_s} | Scripts completos!",parse_mode="Markdown")
            await _save_and_finish(m,uid,un,cid,ficha)
    elif d.startswith("lt:"):
        sid2=d[3:];st=cstate.get(uid)
        if not st or st.get("step")!="lvl_tecno":return
        fid=st["ficha_id"];f=db_get_ficha(fid)
        if not f:return
        tc=list(f.get("tecnomancias",[])or[])
        if sid2 not in tc: tc.append(sid2);db_update_ficha(fid,{"tecnomancias":tc})
        nm_s=DL.TECNO_SCRIPTS.get(sid2,{}).get("nome",sid2)
        await q.edit_message_text(f"✅ Aprendeu: *{nm_s}*",parse_mode="Markdown")
        cstate.pop(uid,None);ch=gc(cid);await ask(ch,f"SISTEMA: {f.get('nome','?')} aprendeu {nm_s}.",m=m)
        await m.reply_text(f"⬆️ Level up completo!",parse_mode="Markdown")

async def _fin_attrs(m,uid):
    st=cstate.get(uid)
    if not st:return
    pv,dice,dropped,subtotal,ajuste,bonus=roll_pv(st["raca"],st["classe"])
    st["pv"]=pv;st["pv_detail"]={"dice":dice,"dropped":dropped,"subtotal":subtotal,"ajuste":ajuste,"bonus":bonus}
    r=DL.RACAS_STATS[st["raca"]];c=DL.CLASSES_STATS[st["classe"]];fl=DL.FILOS_STATS[st["filosofia"]]
    lines=["📋 *RESUMO*\n━━━━━━━━━━━━━━━━━━━━",f"🌌 {r['nome']} | ⚔️ {c['nome']} | 📜 {fl[0]}\n"]
    for i,k in enumerate(ATTR_KEYS):
        b=st["atributos_base"][k];rc=r["mods"][i];f2=b+rc
        lines.append(f"{ATTR_LABELS[i]}: {b}{rc:+d}=*{f2}*({calc_mod(f2):+d})")
    d2=st["pv_detail"]
    lines.append(f"\n❤️ 4d6{d2['dice']} desc {d2['dropped']}={d2['subtotal']}{d2['ajuste']:+d}racial{d2['bonus']:+d}classe=*{pv}PV*")
    attrs={k:st["atributos_base"][k]+r["mods"][i] for i,k in enumerate(ATTR_KEYS)}
    dm=calc_mod(attrs["destreza"]);arm=c["armadura"]
    cd=10+(dm if arm["tipo"]=="leve" else min(dm,2) if arm["tipo"]=="media" else 0)+arm["cd"]
    per=dict(c["pericias"])
    if "bonus_per_fixo" in r:
        for pk,pv2 in r["bonus_per_fixo"].items(): per[pk]=per.get(pk,0)+pv2
    if st.get("bonus_pericias"):
        for pk,pv2 in st["bonus_pericias"].items(): per[pk]=per.get(pk,0)+pv2
    tec=per.get("tecnomancia",0);im=calc_mod(attrs["inteligencia"]);ram=max(1+im+tec//2,0)
    lines.append(f"🛡️ CD:{cd} | 🧠 RAM:{ram}")
    lines.append(f"🎯 {', '.join(f'{PERICIAS_NOMES.get(pk,pk)}+{pv2}' for pk,pv2 in sorted(per.items(),key=lambda x:-x[1]))}")
    await rp(m,"\n".join(lines))
    cls=DL.CLASSES_STATS[st["classe"]];choices=cls.get("equip_escolha",cls.get("equip_escolha_melee",[]))
    if choices:
        btns=[Btn(opt,callback_data=f"eq:{i}") for i,opt in enumerate(choices[0])]
        await m.reply_text("⚔️ Arma:",reply_markup=KBD([[b] for b in btns]))
    elif st["raca"]=="terraqueo":
        st["step"]="terra_attr";st["bonus_attrs"]={};st["bonus_attr_remaining"]=4
        btns=[Btn(f"{ATTR_LABELS[i]}",callback_data=f"ta:{k}") for i,k in enumerate(ATTR_KEYS)]
        await m.reply_text("🌍 *+4 atributos:*",reply_markup=KBD([btns[i:i+3] for i in range(0,len(btns),3)]),parse_mode="Markdown")
    else: st["step"]="nome";await m.reply_text("✏️ Digite o *nome*:",parse_mode="Markdown")

# ══════ MESSAGE HANDLER (Diretriz 3: identidade, Diretriz 4: regex dice) ══════

async def on_msg(u:Update,c:ContextTypes.DEFAULT_TYPE):
    cid=u.effective_chat.id;txt=u.message.text;un=u.message.from_user.first_name or"?"
    uid=u.message.from_user.id;username=u.message.from_user.username or un
    if not txt:return

    st=cstate.get(uid)

    # ── Diretriz 4: Rolagem de dados via Regex (/1d20, /2d8+4) ──
    dice_match=DICE_RE.match(txt.strip())
    if dice_match:
        n=int(dice_match.group(1) or 1);s=int(dice_match.group(2));mod=int(dice_match.group(3) or 0)
        if 1<=n<=20 and 1<=s<=100:
            rolls=[rng.randint(1,s) for _ in range(n)];total=sum(rolls)+mod
            mod_str=f"{mod:+d}" if mod else ""
            cr=""
            if s==20 and n==1:
                if rolls[0]==20:cr="\n🌟 *CRÍTICO!*"
                elif rolls[0]==1:cr="\n💀 *FALHA CRÍTICA!*"
            await rp(u.message,f"🎲 *{n}d{s}{mod_str}*\n{rolls}{f' {mod_str}' if mod else ''} = *{total}*{cr}")
            # Injeta resultado na IA (Diretriz 4)
            ficha=db_get_active(uid,cid)
            nome_pc=ficha.get("nome","?") if ficha else un
            ch=gc(cid)
            await ask(ch,f"[SISTEMA: O personagem {nome_pc} rolou {n}d{s}{mod_str} e obteve {total}. Narre a consequência.]",m=u.message)
            resp=ch.history[-1].parts[0].text if ch.history else ""
            if resp:
                clean=await intercept_and_sync(resp,cid,msg=u.message)
                await rp(u.message,clean)
            return

    # Esperando contexto (play:context)
    if st and st.get("step")=="wait_context" and st.get("chat_id")==cid:
        chats.pop(cid,None);ch=gc(cid)
        actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
        modo="singular" if len(actives)<=1 else "plural"
        if ctx: await ask(ch,f"MODO_NARRATIVA: {modo}.\n{ctx}")
        
        # Passo 4 (parte c): Liga o mestre ao fornecer um novo contexto manualmente!
        jogo_ativo[cid] = True 
        
        resp=await ask(ch,f"CONTEXTO_SESSAO: Retomando.\n{txt}\nRecapitule e pergunte ação.",m=u.message)
        await rp(u.message,resp);cstate.pop(uid,None);return

    # Criação: esperando nome
    if st and st.get("step")=="nome" and st.get("chat_id")==cid:
        st["nome"]=txt.strip()[:30]
        ficha=build_ficha(st)
        # Tecnomancia?
        tecno_total=ficha.get("pericias",{}).get("tecnomancia",0)
        if tecno_total>=1:
            mx=DL.calc_max_scripts(1,tecno_total)
            avail=DL.get_available_scripts(tecno_total)
            st["step"]="tecno_select";st["tecno_remaining"]=mx;st["tecno_selected"]=[]
            st["tecno_available"]=avail;st["built_ficha"]=ficha
            btns=[Btn(f"🧠 {v['nome']}({v['ram']}R)",callback_data=f"ts:{k}") for k,v in sorted(avail.items(),key=lambda x:x[1]["ram"])]
            await u.message.reply_text(f"🧠 *TECNOMANCIA*\n+{tecno_total} → *{mx} scripts*\nRestam: *{mx}*",
                reply_markup=KBD([btns[i:i+2] for i in range(0,len(btns),2)]),parse_mode="Markdown")
            return
        await _save_and_finish(u.message,uid,un,cid,ficha);return

    # Passo 5: A Porta do Segurança (Se o jogo não estiver ativo, o bot fica mudo)
    # ── Jogo normal — Diretriz 3: identidade ──
    if not jogo_ativo.get(cid): return
    
    ch=gc(cid)
    try:
        ficha=db_get_active(uid,cid)
        nome_pc=ficha.get("nome","?") if ficha else un
        # Diretriz 3: cabeçalho de identidade
        header=f"[Usuário: @{username} | Personagem: {nome_pc}] diz: {txt}"
        resp=await ask(ch,header,m=u.message)
        th(cid)
        clean=await intercept_and_sync(resp,cid,msg=u.message)
        
        # Se a IA perceber que é só conversa entre jogadores, o bot cancela o envio da mensagem
        if "[ESCUTANDO]" in clean.upper():
            return 
            
        await rp(u.message,clean)
    except Exception as e:
        log.error(f"Msg:{e}");await u.message.reply_text("⚠️ Interferência.")

async def on_err(u,c): log.error(f"Err:{c.error}")

# ══════ MAIN ══════
def main():
    DL.ensure_loaded()
    app=Application.builder().token(TG).build()
    for cmd,fn in[("start",cmd_start),("reset",cmd_reset),("ajuda",cmd_help),("help",cmd_help),("debug",cmd_debug),
        ("iniciar",cmd_iniciar),("novojogo",cmd_novojogo),("criarpersonagem",cmd_criar),
        ("regras",cmd_regras),("glossario",cmd_glossario),
        ("ficha",cmd_ficha),("fichas",cmd_fichas),("deletarficha",cmd_deletar),
        ("levelup",cmd_levelup),("implante",cmd_implante),
        ("salvarsessao",cmd_salvar_sessao),("sessoes",cmd_sessoes),
        ("cargarsessao",cmd_cargarsessao),("contexto",cmd_contexto)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,on_msg))
    # Diretriz 4: captura /NdN como comando regex
    app.add_handler(MessageHandler(filters.Regex(r'^/\d*d\d+'),on_msg))
    app.add_error_handler(on_err)
    if WH: app.run_webhook(listen="0.0.0.0",port=PT,url_path=TG,webhook_url=f"{WH}/{TG}")
    else: app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":main()
