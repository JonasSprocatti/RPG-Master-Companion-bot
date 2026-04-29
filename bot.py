"""
🌌 Passagem Sombria v3.0 — RPG Master Companion Bot
Diretrizes 1-9 implementadas. Bot = lógica/estado. IA = narração.
"""
import os,json,logging,asyncio,random as rng,re,unicodedata,time
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

# ══════ TRACING SYSTEM ══════
def trace(category, detail, uid=None, cid=None, extra=None):
    """Log estruturado para rastrear todo fluxo do bot.
    Categorias: MSG_IN, MSG_OUT, BTN, DICE, AI_REQ, AI_RES, INTERCEPT, DB, GODMODE, SESSION, ERROR
    """
    parts = [f"[TRACE:{category}]"]
    if cid: parts.append(f"chat={cid}")
    if uid: parts.append(f"user={uid}")
    parts.append(detail)
    if extra: parts.append(f"| {extra}")
    log.info(" ".join(parts))

TG=os.environ["TELEGRAM_TOKEN"];GK=os.environ["GEMINI_API_KEY"]
WH=os.environ.get("WEBHOOK_URL","");PT=int(os.environ.get("PORT",10000))
SU=os.environ.get("SUPABASE_URL","");SK=os.environ.get("SUPABASE_KEY","")
ADMIN=os.environ.get("ADMIN_ID","")
db=create_client(SU,SK) if SU and SK else None

RPG_FILE=os.path.join(os.path.dirname(__file__),"rpg_content.txt")
with open(RPG_FILE,"r",encoding="utf-8") as f: RPG=f.read()

XP_T={1:100,2:250,3:450,4:700,5:1000,6:1400,7:1900,8:2500,9:3200}
DICE_RE=re.compile(r'/(\d*)d(\d+)(?:([pm+-])(\d+))?')  # Aceita /1d20p5 E /1d20+5
def _norm(s): return unicodedata.normalize("NFKD",s.lower()).encode("ascii","ignore").decode()

SYSP=f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".
Setting: nosso Sistema Solar. Use como pilar narrativo principal.
ESTILO: PT-BR, sombrio/cinematográfico. Emojis temáticos. Separadores ━━━ em combate. Máx 800 palavras.
REGRA DE INTERFACE: NÃO inclua barras de status de PV ou CD nas suas respostas, a menos que o jogador pergunte expressamente.
Formato rolagem: 🎲 1d20(14)+Mod(3)+Per(2)=19 vs CD15 → ✅

🛑 REGRA DE OURO — AGÊNCIA DOS JOGADORES:
- NUNCA tome decisões, declare ações ou crie diálogos para os PCs.
- Descreva ambiente, controle NPCs, narre consequências das ações DELES.
- DIREÇÃO DE CENA: Aja como um diretor de cinema. Direcione as perguntas DIRETAMENTE ao personagem envolvido, usando o NOME dele. Exemplo: Se o Grovax agiu ou sofreu um impacto, narre para ele e pergunte: "Grovax, o que você faz?". Se o Zeb encontrou uma pista, pergunte: "Zeb, como você reage?". 
- Use o plural ("O que vocês fazem?") APENAS quando um evento de cenário atingir o grupo todo simultaneamente.
- MODO ESCUTA: Se os jogadores estiverem APENAS conversando entre si, planejando estratégias, ou fazendo roleplay de diálogo (sem interagir com o cenário, sem falar com NPCs e sem rolar dados), responda EXATAMENTE com a tag [ESCUTANDO]. Não narre absolutamente mais nada, apenas observe.

🧑‍🚀 IDENTIFICAÇÃO DE TURNO:
- Cada mensagem do jogador chega no formato: [Usuário: @nick | Personagem: Nome] diz: texto
- Use o NOME DO PERSONAGEM para se referir ao jogador na narração.
- NUNCA confunda jogadores. Cada ação é de quem mandou.

🎲 ROLAGENS DE DADOS — QUANDO EXIGIR TESTES:
- Use o formato clicável: /1d20p5 (p=plus) ou /1d20m2 (m=minus). Sem mod: /1d20
- O bot calcula e injeta: [SISTEMA: Personagem rolou NdN+X = Total]. Narre a consequência.
- CALCULE O MODIFICADOR CORRETO: Consulte FICHAS_ATIVAS, some Mod.Atributo + Perícia do jogador.
  Exemplo: Grovax tem Carisma 12 (+2) e Persuasão +3. Modificador total = +5. Peça: "Faça /1d20p5 para Persuasão CD 15"

⚠️ EXIJA TESTES NAS SEGUINTES SITUAÇÕES (NÃO deixe passar sem rolagem):
🗣️ SOCIAL — Sempre que o jogador tentar:
  • Convencer, enganar, intimidar ou manipular um NPC → Persuasão/Enganação/Intimidação
  • Extrair informação que o NPC não quer dar → Persuasão ou Intimidação (CD 13-18)
  • Barganhar preço, pedir favor, negociar acordo → Persuasão (CD 12-16)
  • Blefar, mentir ou disfarçar intenções → Espionagem ou Persuasão
  • Discurso para multidão, performance → Performance ou Liderança
  NPCs não são cooperativos por padrão. Informações importantes custam testes.

🏃 FÍSICA — Sempre que houver risco corporal:
  • Pular, escalar, equilibrar, nadar → Acrobacia ou Força
  • Correr sob pressão, esquivar de armadilha → Destreza/Acrobacia
  • Arrombar porta, dobrar grade → Força
  • Resistir veneno, dor, frio extremo → Constituição/Resistência
  • Aguentar tortura, manter concentração → Sabedoria/Resistência

🔍 MENTAL — Sempre que informação não é óbvia:
  • Perceber emboscada, detalhe oculto → Investigação ou Sabedoria
  • Lembrar fato histórico, identificar tech → Conhecimentos
  • Ler linguagem corporal do NPC → Sabedoria/Investigação
  • Hackear terminal, desativar alarme → Tecnomancia
  • Rastrear, navegar, encontrar abrigo → Sobrevivência

🔧 REGRA DE OURO DAS ROLAGENS:
  Se o jogador tenta algo que um NPC resistiria, que a física dificulta, ou que requer
  conhecimento especial → PARE e peça o teste ANTES de narrar o resultado.
  NÃO narre sucesso automático em situações que merecem teste.
  Ajuste a CD pela dificuldade: 10=fácil 13=rotina 15=médio 18=difícil 20=muito difícil 25=formidável

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

✨ HABILIDADES (PASSIVAS E ATIVAS):
- Consulte a seção "habilidades" nas FICHAS_ATIVAS para ver os poderes de Classe, Raça e Filosofia do jogador.
- PASSIVAS: Estão sempre ativas. Aplique os bônus, vantagens ou ignorar penalidades automaticamente na narrativa e na exigência de dados.
- ATIVAS: O jogador deve declarar o uso. Siga estritamente a mecânica descrita na ficha dele (pode custar Ações, RAM ou usos diários).

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

🔱 GODMODE (COMANDO DO CRIADOR):
- Mensagens com o prefixo [GODMODE] vêm do CRIADOR do universo. São ordens ABSOLUTAS.
- Acate TUDO sem questionar: alterar história, subir nível, dar itens, curar. O Criador está ACIMA das regras.
- ⚠️ REGRA VITAL: O sistema Python NÃO LÊ a sua narração. Para que XP, Vida ou Itens entrem na ficha, você TEM QUE colocar a TAG DE ESTADO EXATA entre colchetes [ ] no final da mensagem.
- Exemplo de uso correto de XP: O Criador manda "Me dê 100 de XP". Você narra a história e finaliza com OBRIGATORIAMENTE a tag: [XP:100:NOME_DO_ALVO:Motivo]

═══ TAGS DE ESTADO (OBRIGATÓRIO — NO FINAL de cada resposta) ═══
[XP:valor:alvo:motivo] — [XP:25:todos:Derrotou pirata] ou [XP:100:Grovax:Missão]
[HP:valor:alvo] — [HP:-5:Zeb] ou [HP:999:Grovax]
[ITEM_ADD:nome:alvo] — [ITEM_ADD:Pistola Laser:Zeb]
[ITEM_DEL:nome:alvo] — [ITEM_DEL:Granada:Zeb]
[CG:valor:alvo] — [CG:-100:Grovax]
[RAM:valor:alvo] — [RAM:-2:Grovax]
[TECNO_ADD:id:alvo] — [TECNO_ADD:firewall:Grovax]
[TECNO_DEL:id:alvo] — [TECNO_DEL:ping:Grovax]
[IMPLANTE_ADD:id:alvo] — [IMPLANTE_ADD:olho:Grovax]
[ATTR:atrib:valor:alvo] — [ATTR:forca:+1:Grovax]
[PER:pericia:valor:alvo] — [PER:furtividade:+1:Grovax]
IDs scripts: ping choque query scanner jammer glitch trava rollback firewall travar_arma curto_arm hack_motor ejetar_pente cegueira drenar sobrecarga desativar loop torreta hack_nav apagao inverter reator marionete emp ejetar_piloto reparo_nave formatar gravidade
IDs implantes: chip_ram olho interface_nav tradutor mira placas coracao filtro adrenalina bateria_int braco estabilizador mantis pernas ancoras

REFERÊNCIA MECÂNICA: {RPG}"""

# ══════ DICIONÁRIOS DE HABILIDADES ══════
RACAS_HABILIDADES = {
    "mercusys": [
        "🧬 Racial (Alta Velocidade): Deslocamento base é o dobro (18m). Regenera 1d4 PV a mais num Descanso Curto. (Exige o dobro de rações).",
        "🧬 Racial (Leitura Sensitiva): Ao tocar objetos/líquidos, identifica a composição química exata e detecta venenos ou ácidos.",
        "🧬 Racial (Resistência ao Calor): Imune a dano por fogo ambiental/calor extremo. Desvantagem em ambientes frios (< 25°C)."
    ],
    "veny": [
        "🧬 Racial (Air Shifter): Pode inalar gases para sofrer mutação (dura 1 min). Ex: Oxigênio = ganha asas; Hélio = voa no vácuo e não sofre dano de queda; Hidrogênio = fica gigante (+2 Força)."
    ],
    "terraqueo": [
        "🧬 Racial (Gambiarra): 1x/dia, pode usar a Ação para transformar 3 itens de sucata em 1 item funcional temporário (arma, comunicador, kit médico)."
    ],
    "marciano": [
        "⚡ Racial (Êxtase da Batalha): Ação Livre. Rola 1d6. (1-3 Adrenalina): +2 Dano Físico e +3m Movimento. (4-6 DHEA): Mente fria, +2 Acerto à distância e ignora cobertura. Dura 4 turnos.",
        "⚡ Racial (Endurecer): Ação de Movimento. Enrijece músculos, recebendo -2 de Dano Físico em todos os golpes sofridos por 4 turnos."
    ],
    "conjupitero": [
        "🧬 Racial (Física de Motor): +2 na Defesa(CD) contra tentativas de empurrão/arremesso. Pode carregar o triplo do peso normal.",
        "🧬 Racial (Engenharia): +2 permanente nas perícias Pilotagem e Mecânica.",
        "💼 Racial (Conta da Confederação): Recebe 10% de desconto automático na compra de qualquer item da galáxia."
    ],
    "sata": [
        "⚡ Racial (Cura Genética): 1x/dia, Ação Principal. Cura 1d8+Sabedoria de um alvo. Se rolar 8, cura o dobro. Se rolar 1, o Sata sofre 2 de dano por rejeição.",
        "⚡ Racial (Camuflagem Cromática): Ação Principal. Ganha +5 em Furtividade se ficar imóvel ou andar metade do movimento.",
        "⚡ Racial (Emprestar Vitalidade): Ação Livre. Pode transferir metade dos seus PV atuais para curar um aliado com um toque."
    ],
    "urak": [
        "🧬 Racial (Mímica Sonora): Imita qualquer voz, instrumento ou alarme de forma perfeita (Vantagem p/ iludir portas biométricas).",
        "⚡ Racial (Criogênese): Ação Principal. Congela a umidade do ar para criar um objeto médio (martelo, escudo, chave) que derrete em 6 turnos.",
        "🧬 Racial (Resistência ao Frio): Sobrevive perfeitamente no vácuo e no zero absoluto. Sofre 1 de dano contínuo acima de 40°C sem traje refrigerado."
    ],
    "proturno": [
        "🧬 Racial (Levantamento Mental): Usa Inteligência no lugar de Força para mover e arremessar objetos de até 50kg a 10m de distância.",
        "⚡ Racial (Invasão da Sombra): Ação Principal. Controle mental. Disputa de 1d20+Sab. Se o Proturno vencer, dita a ação do inimigo. Se perder, o Proturno sofre 2 de dano mental."
    ],
    "infimor": [
        "🧬 Racial (Passos do Vácuo): Sobrevive no vácuo e não respira. Pode encolher o corpo (perde metade do movimento, mas ganha Vantagem Furtiva).",
        "🧬 Racial (Braços Telescópicos): O seu alcance para ataques corpo a corpo e interações físicas é de 10 metros.",
        "🧬 Racial (Fúria do Rebaixado): Se ouvir alguém dizer que Plutão não é planeta, ganha +2 em atributos e +3 dano, mas ataca aliados e inimigos sem controle por 5 turnos."
    ]
}

FILOSOFIAS_HABILIDADES = {
    "cam_voz": ["📜 Caminho (Comando Subliminar): 1x/Descanso Longo. Rola Carisma c/ Vantagem para impor Desvantagem no alvo. Ou usa para fingir de morto perfeitamente para radares térmicos."],
    "cam_ressonancia": ["📜 Caminho (Eco no Escuro): 1x/Descanso Curto. Ignora escuridão por 1 turno e sente a localização exata de vivos num raio de 10m (mesmo atrás de paredes)."],
    "cam_engrenagem": ["📜 Caminho (Bênção da Máquina): 1x/Descanso Longo. Transforma um '1' natural (Falha Crítica) em ataque com arma ou Tecnomancia numa falha comum."],
    "cam_espiral": ["📜 Caminho (Metabolismo Acelerado): Sempre que recuperar Vida (Kit Médico ou Descanso), joga o dado de cura 2 vezes e pega o maior resultado."],
    "cam_anel": ["📜 Caminho (A Segunda Órbita): 1x/Descanso Longo. Se o PV chegar a 0, em vez de cair, o personagem fica de pé com 1 PV cravado até o final do próximo turno."],
    "cam_ocaso": ["📜 Caminho (Sacrifício de Sangue): 1x/Combate. Pode sofrer 1d4 de Dano inesquivável de propósito para somar +1d4 numa rolagem de ataque ou perícia (transforma erro em acerto)."],
    "cod_sobrevivente": ["📜 Código (Paranoia Ativa): +2 Iniciativa. 1x/Descanso Longo, não perde o turno e age normalmente se o grupo for pego em uma Rodada Surpresa/Emboscada."],
    "cod_corporativo": ["📜 Código (Olhar Avaliador): Ganha Vantagem automática para avaliar itens raros, achar loot oculto e negociar missões."],
    "cod_cetico": ["📜 Código (Fortaleza Racional): Ganha +2 de Defesa (CD) passiva especificamente contra intimidação, ataques psíquicos e controles mentais."],
    "cod_fronteira": ["📜 Código (Foco Isolado): Recebe +1 de bônus no Ataque se não houver NENHUM aliado do seu grupo num raio de 5 metros."],
    "cod_caserna": ["📜 Código (Ato de Sacrifício): 1x/Descanso Curto (Reação). Atira-se na frente de um ataque letal contra um aliado adjacente e sofre o dano no lugar dele."],
    "cod_viralata": ["📜 Código (Golpe Baixo): 1x/Combate (Ação Livre). Joga poeira/cega um inimigo a 3m de distância. O seu próximo ataque contra esse inimigo é com Vantagem."]
}

CLASSES_HABILIDADES = {
    "estudioso": ["🧠 Passiva (Mapa Mental): 1x/sessão, declara que já leu sobre o alvo para o Mestre revelar fraqueza.", "⚡ Ativa (Ponto Estrutural): 1 RAM e Ação Principal. O próximo ataque (seu ou de aliado) no alvo dá Dano Máximo sem rolar."],
    "mecanico": ["🧠 Passiva (Operador Pesado): Ignora penalidades ao vestir armaduras pesadas.", "⚡ Ativa (Reparo Tático): Ação Principal. Conserta armadura/escudo de aliado para +1d6+Mecânica de PV Temporários."],
    "assassino": ["🧠 Passiva (O Primeiro Corte): Atacar alvo furtivamente ou antes da ação dele dá +2 acerto e DOBRA O DANO da arma.", "⚡ Ativa (Desaparecer): Matou o inimigo? Ação Livre para rolar Furtividade e sumir do combate."],
    "soldado": ["🧠 Passiva (Memória Muscular): Usa Armas Pesadas perfeitamente sem o -2 no acerto.", "⚡ Ativa (Fogo de Supressão): Ação Principal. Alvo testa Sabedoria ou fica acovardado (não avança) e ataca com Desvantagem."],
    "starlord": ["🧠 Passiva (Charme Malandro): 1x/cena, re-rola falha de persuasão e lábia.", "⚡ Ativa (Deixem comigo!): Ação Livre. Grita ordens e o próximo aliado a atacar recebe Vantagem."],
    "franco_atirador": ["🧠 Passiva (Foco à Distância): +5 no acerto para alvos a >30 metros.", "⚡ Ativa (Tiro Incapacitante): Atira no membro; Dano cai pela metade, mas o alvo fica com Movimento Zero ou derruba a arma."],
    "musico": ["🧠 Passiva (Ouvido Absoluto): +2 de Defesa(CD) contra controle da mente e dano sônico.", "⚡ Ativa (Frequência Ressonância): Ação Principal. Cria aura de 10m: Aliados ganham +2 Dano OU Inimigos sofrem -2 CD. Dura até o Músico receber dano."],
    "espiao": ["🧠 Passiva (Rosto na Multidão): Vantagem absoluta para se disfarçar com roupas da facção inimiga.", "⚡ Ativa (Ponto Cego): Ação de Movimento. Esconde-se na confusão; inimigos o ignoram e não o focam até você agir."],
    "catador": ["🧠 Passiva (Olho para o Ouro): Ao lootear, joga 1d6. Em 4-6, encontra loot/sucata extra valiosa.", "⚡ Ativa (Desmanche Rápido): 1x/combate, Ação Principal. Arranca peça de robô/armadura: 1d8 dano fixo e -1 CD permanente no alvo."],
    "piloto": ["🧠 Passiva (Instinto Evasivo): O veículo ou Nave que ele pilotar recebe +2 na Defesa(CD) automaticamente.", "⚡ Ativa (Sobrecarga Propulsores): Joga Pilotagem com Vantagem para escapar de tiro espacial letal, mas a nave leva 1d4 dano de estresse."],
    "batedor": ["🧠 Passiva (Sentidos Alertas): +2 Iniciativa. Nunca cai em rodadas de surpresa.", "⚡ Ativa (Marca do Caçador): Ação Livre. Marca o inimigo; todo o grupo do batedor ignora a cobertura do alvo."],
    "explorador": ["🧠 Passiva (Mapeamento Tático): Ele e aliados a 10m ignoram as penalidades de Terreno Difícil (gelo/lama).", "⚡ Ativa (Vulnerabilidade Exposta): Ação Principal. Analisa alvo (Sobrevivência). Se passar, grupo dá +1d6 dano no bicho."],
    "cinetico": ["🧠 Passiva (Bio-feedback): Quando cura aliados com magias, cura 2 PV de si mesmo junto.", "⚡ Ativa (Repulsão Cinética): 1 RAM e Ação Principal. Empurra quem estiver colado em você 3m para trás (testam Força ou caem)."],
    "prospector": ["🧠 Passiva (Contrato Lucrativo): Garante +20% a mais de dinheiro/créditos nos loots para o grupo.", "⚡ Ativa (Espere!): 1x/combate, Ação Movimento. Convence vilão a hesitar e perder o turno (Ação Principal) dele."],
    "pirata": ["🧠 Passiva (Brutalidade Abordagem): +1 Dano atacando dentro de Naves/locais apertados, sem sofrer penalidade de espaço.", "⚡ Ativa (Grito Saqueador): Ação Principal. Inimigos a 5m testam Sabedoria ou ficam Amedrontados (Desvantagem em tudo) por 2 turnos."]
}

genai.configure(api_key=GK)
mdl=genai.GenerativeModel("gemini-2.5-flash-lite",system_instruction=SYSP,
    generation_config=genai.GenerationConfig(temperature=0.85,max_output_tokens=1500))

chats:dict={};cstate:dict={};jogo_ativo:dict={};godmode:dict={}

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
        db.table("fichas").update(clean).eq("id",fid).execute()
        trace("DB",f"UPDATE ficha={fid}",extra=f"campos={list(updates.keys())}")
        return True
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
    trace("INTERCEPT",f"Encontrou {len(changes)} tags",cid=cid,extra=f"tags={[c[0] for c in changes]}")
    actives=db_get_all_active(cid)
    nm2f={}
    for f in actives:
        nome=f.get("nome","");nm2f[nome.lower()]=f;nm2f[_norm(nome)]=f
    notifs=[];ia_inject=[]
    
    for tt,params in changes:
        parts=[p.strip() for p in params.split(":")]
        try:
            if tt == "XP" and len(parts) >= 3:
                alvo_raw = parts[1]
            else:
                alvo_raw = parts[-1] if len(parts) >= 2 else ""
                
            alvo=alvo_raw.lower(); alvo_n=_norm(alvo_raw)
            
            def _find():
                if alvo=="todos": return list({id(f):f for f in nm2f.values()}.values()),True
                f=nm2f.get(alvo) or nm2f.get(alvo_n)
                if f: return [f],False
                for active_f in nm2f.values():
                    if alvo in active_f.get("nome","").lower() or alvo in active_f.get("raca","").lower() or alvo in active_f.get("classe","").lower():
                        return [active_f], False
                return [],False

            if tt=="XP" and len(parts)>=2:
                val = int(parts[0])
                if val == 0: continue # Ignora a tag do resumo
                tgts,is_all=_find()
                xe=val//(len(tgts)or 1) if is_all else val
                for f in tgts:
                    nx=f.get("xp",0)+xe;db_update_ficha(f["id"],{"xp":nx})
                    nv=f.get("nivel",1);xr=XP_T.get(nv,9999)
                    notifs.append(f"✨ +{xe}XP {f.get('nome','?')} ({nx}/{xr}){' ⬆️ /levelup!' if nx>=xr else ''}")
                    
            elif tt=="HP" and len(parts)>=2:
                val=int(parts[0])
                tgts,is_all=_find()
                for f in tgts:
                    nh=max(0,min(f.get("pv_atual",0)+val,f.get("pv_max",1)));db_update_ficha(f["id"],{"pv_atual":nh})
                    notifs.append(f"{'💚' if val>0 else '🩸'} {f.get('nome','?')}: {val:+d}PV → ❤️{nh}/{f.get('pv_max','?')}")
                    
            elif tt=="ITEM_ADD" and len(parts)>=2:
                item=parts[0];tgts,_=_find()
                for f in tgts:
                    inv=list(f.get("inventario",[]));inv.append(item);db_update_ficha(f["id"],{"inventario":inv})
                    notifs.append(f"🎒 {f.get('nome','?')} +{item}")
                    
            elif tt=="ITEM_DEL" and len(parts)>=2:
                item=parts[0];tgts,_=_find()
                for f in tgts:
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
                val=int(parts[0]);tgts,_=_find()
                for f in tgts:
                    nr=max(0,min(f.get("ram_atual",0)+val,f.get("ram_max",0)));db_update_ficha(f["id"],{"ram_atual":nr})
                    
            elif tt=="TECNO_ADD" and len(parts)>=2:
                sid2=parts[0].lower();tgts,_=_find()
                for f in tgts:
                    if sid2 in DL.TECNO_SCRIPTS:
                        tc=list(f.get("tecnomancias",[])or[])
                        if sid2 not in tc: tc.append(sid2);db_update_ficha(f["id"],{"tecnomancias":tc})
                        notifs.append(f"🧠 {f.get('nome','?')} aprendeu: *{DL.TECNO_SCRIPTS[sid2]['nome']}*")
                        
            elif tt=="TECNO_DEL" and len(parts)>=2:
                sid2=parts[0].lower();tgts,_=_find()
                for f in tgts:
                    tc=list(f.get("tecnomancias",[])or[])
                    if sid2 in tc: tc.remove(sid2);db_update_ficha(f["id"],{"tecnomancias":tc})
                    notifs.append(f"🧠 {f.get('nome','?')} perdeu script")

            elif tt=="IMPLANTE_ADD" and len(parts)>=2:
                impl_id=parts[0].lower();tgts,_=_find()
                for f in tgts:
                    if impl_id in DL.IMPLANTES_DATA:
                        imp=DL.IMPLANTES_DATA[impl_id]
                        impl_list=list(f.get("implantes",[])or[]);con_mod=calc_mod(f.get("atributos",{}).get("constituicao",8))
                        limite=DL.calc_implant_limit(con_mod);qtd=len(impl_list)
                        impl_list.append(imp["nome"]);ups={"implantes":impl_list}
                        mec=imp.get("mecanica",{})
                        if "ram_max" in mec: ups["ram_max"]=f.get("ram_max",0)+mec["ram_max"]
                        if "cd" in mec: ups["cd"]=f.get("cd",10)+mec["cd"]
                        if "pv_max" in mec: ups["pv_max"]=f.get("pv_max",0)+mec["pv_max"];ups["pv_atual"]=f.get("pv_atual",0)+mec["pv_max"]
                        resultado="Operação Segura"
                        if qtd>=limite:
                            extra=qtd-limite+1
                            if extra==1:
                                dano=rng.randint(1,6)
                                ups["pv_max"]=f.get("pv_max",0)+(mec.get("pv_max",0))-dano
                                ups["pv_atual"]=min(f.get("pv_atual",0),ups["pv_max"])
                                notas=f.get("notas","")+"| Desvantagem Persuasão (implante) "
                                ups["notas"]=notas
                                resultado=f"Sobrecarga Nv1: perdeu {dano} Vida Máxima permanente"
                            elif extra==2:
                                notas=f.get("notas","")+"| Curto-Circuito (1-2 natural=1d6 elétrico+atordoa) "
                                ups["notas"]=notas
                                resultado="Sobrecarga Nv2: Curto-Circuito instalado"
                            elif extra>=3:
                                ups["pv_atual"]=0;ups["pv_max"]=0
                                resultado="COLAPSO NEURAL — ÓBITO CIBERNÉTICO"
                        db_update_ficha(f["id"],ups)
                        nome_p=f.get("nome","?")
                        notifs.append(f"🦾 {nome_p}: *{imp['nome']}* — {resultado}")
                        ia_inject.append(f"[SISTEMA MÉDICO: Implante {imp['nome']} instalado em {nome_p}. Resultado: {resultado}. Ficha atualizada.]")

            elif tt=="ATTR" and len(parts)>=3:
                ak=parts[0].lower();val=int(parts[1]);tgts,_=_find()
                for f in tgts:
                    if ak in ATTR_KEYS:
                        a=dict(f.get("atributos",{}));a[ak]=a.get(ak,8)+val;db_update_ficha(f["id"],{"atributos":a})
                        notifs.append(f"📊 {f.get('nome','?')}: {ATTR_SHORT[ATTR_KEYS.index(ak)]} {val:+d}")
                        
            elif tt=="PER" and len(parts)>=3:
                pk=parts[0].lower();val=int(parts[1]);tgts,_=_find()
                for f in tgts:
                    p=dict(f.get("pericias",{}));p[pk]=p.get(pk,0)+val;db_update_ficha(f["id"],{"pericias":p})
                    notifs.append(f"🎯 {f.get('nome','?')}: {PERICIAS_NOMES.get(pk,pk)} {val:+d}")
                    
        except Exception as e: log.warning(f"Intercept:{tt}:{params}→{e}")
        
    clean=STATE_RE.sub("",text).strip()
    if notifs and msg:
        trace("INTERCEPT",f"Sync notifs={len(notifs)}",cid=cid,extra=str(notifs))
        try: await msg.reply_text("📡 *Sync:*\n"+"\n".join(notifs),parse_mode="Markdown")
        except: pass
    if ia_inject:
        try:
            ch=gc(cid)
            for inj in ia_inject: await ask(ch,inj)
        except: pass
    return clean

# ══════ CRIAÇÃO ESTÁTICA E IMPORTAÇÃO ══════
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
        "atributos":attrs,"pericias":per,
        "habilidades": [f"📜 {fl[0]}: {fl[1]}"] + RACAS_HABILIDADES.get(st["raca"], []) + CLASSES_HABILIDADES.get(st["classe"], []) + FILOSOFIAS_HABILIDADES.get(st["filosofia"], []),
        "tecnomancias":list(st.get("tecno_selected",[])),
        "armas":[x for x in equip if any(w in x for w in["1d","2d","3d"])],
        "armadura":f"{arm['nome']} (CD+{arm['cd']})",
        "inventario":[x for x in equip if not any(w in x for w in["1d","2d","3d"])],
        "creditos":100+c.get("creditos_extra",0),"implantes":[]}

async def cmd_importar(u,c):
    txt = u.message.text.replace("/importar", "").strip()
    if not txt:
        template = (
            "📝 *IMPORTAÇÃO MANUAL DE FICHA*\n"
            "Copie o modelo abaixo, preencha com os dados exatos e envie de volta (não apague as palavras antes dos dois-pontos):\n\n"
            "`/importar\n"
            "Nome: \n"
            "Raca: terraqueo\n"
            "Classe: soldado\n"
            "Filosofia: cod_sobrevivente\n"
            "Nivel: 1\n"
            "XP: 0\n"
            "PV: 15\n"
            "Forca: 8\n"
            "Destreza: 8\n"
            "Constituicao: 8\n"
            "Inteligencia: 8\n"
            "Sabedoria: 8\n"
            "Carisma: 8\n"
            "Pericias: armas_de_fogo:4, sobrevivencia:2\n"
            "Armas: Rifle de Assalto, Faca\n"
            "Inventario: Kit Médico, Rações\n"
            "Tecnomancias: \n"
            "Implantes: \n"
            "Creditos: 100`\n\n"
            "⚠️ *Atenção:* Os atributos devem ser os valores finais (já somados com os bônus da raça). O bot calculará CD, RAM e Iniciativa sozinho com base na sua Classe e Raça!"
        )
        await u.message.reply_text(template, parse_mode="Markdown")
        return
        
    try:
        lines = txt.split('\n')
        data = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                data[_norm(k.strip())] = v.strip()
        
        required = ["nome", "raca", "classe", "filosofia", "nivel", "xp", "pv", "forca", "destreza", "constituicao", "inteligencia", "sabedoria", "carisma"]
        for req in required:
            if req not in data:
                await u.message.reply_text(f"❌ Faltou o campo: {req.capitalize()}")
                return
                
        r_id = _norm(data["raca"])
        c_id = _norm(data["classe"])
        f_id = _norm(data["filosofia"])
        
        if r_id not in DL.RACAS_STATS: return await u.message.reply_text(f"❌ Raça inválida: {data['raca']}")
        if c_id not in DL.CLASSES_STATS: return await u.message.reply_text(f"❌ Classe inválida: {data['classe']}")
        if f_id not in DL.FILOS_STATS: return await u.message.reply_text(f"❌ Filosofia inválida: {data['filosofia']}")
            
        nivel = int(data["nivel"]); xp = int(data["xp"]); pv = int(data["pv"])
        attrs = {
            "forca": int(data["forca"]), "destreza": int(data["destreza"]),
            "constituicao": int(data["constituicao"]), "inteligencia": int(data["inteligencia"]),
            "sabedoria": int(data["sabedoria"]), "carisma": int(data["carisma"])
        }

        r = DL.RACAS_STATS[r_id]; cls = DL.CLASSES_STATS[c_id]; fl = DL.FILOS_STATS[f_id]
        
        dm = calc_mod(attrs["destreza"])
        arm = cls["armadura"]
        cd = 10 + (dm if arm["tipo"]=="leve" else min(dm,2) if arm["tipo"]=="media" else 0) + arm["cd"]
        
        per_dict = {}
        if data.get("pericias"):
            for p_item in data["pericias"].split(","):
                if ":" in p_item:
                    pk, pv_val = p_item.split(":")
                    per_dict[_norm(pk.strip()).replace(" ", "_")] = int(pv_val.strip())
                    
        tec = per_dict.get("tecnomancia", 0)
        im = calc_mod(attrs["inteligencia"])
        ram = max(1 + im + tec//2, 0)
        for n in range(3, nivel + 1):
            if n % 2 != 0: ram += 1
                
        init = dm + (2 if f_id == "cod_sobrevivente" or c_id == "batedor" else 0)
        
        armas_list = [x.strip() for x in data.get("armas", "").split(",") if x.strip()]
        inv_list = [x.strip() for x in data.get("inventario", "").split(",") if x.strip()]
        creditos = int(data.get("creditos", 100))

        ficha = {
            "nome": data["nome"], "raca": r["nome"], "classe": cls["nome"], "filosofia": fl[0],
            "nivel": nivel, "xp": xp, "pv_atual": pv, "pv_max": pv,
            "cd": cd, "ram_atual": ram, "ram_max": ram, "iniciativa": init,
            "deslocamento": r.get("desloc", 9), "atributos": attrs, "pericias": per_dict,
            "habilidades": [f"📜 {fl[0]}: {fl[1]}"] + RACAS_HABILIDADES.get(r_id, []) + CLASSES_HABILIDADES.get(c_id, []) + FILOSOFIAS_HABILIDADES.get(f_id, []),
            "tecnomancias": [], "armas": armas_list, "armadura": f"{arm['nome']} (CD+{arm['cd']})",
            "inventario": inv_list, "creditos": creditos, "implantes": []
        }
        
        if data.get("tecnomancias"):
            t_list = []
            for t_item in data["tecnomancias"].split(","):
                t_id = _norm(t_item.strip())
                if t_id in DL.TECNO_SCRIPTS: t_list.append(t_id)
            ficha["tecnomancias"] = t_list

        if data.get("implantes"):
            ficha["implantes"] = [x.strip() for x in data["implantes"].split(",") if x.strip()]

        cid = u.effective_chat.id; uid = u.message.from_user.id; un = u.message.from_user.first_name or "?"
        fid = db_create_ficha(uid, un, cid, ficha)
        
        if fid:
            db_set_active(uid, cid, fid); ficha["id"] = fid
            await rp(u.message, f"✅ *Ficha Importada com Sucesso!* (ID:{fid})")
            await rp(u.message, ff(ficha))
            ch = gc(cid); await ask(ch, f"FICHAS_ATIVAS:\n{inject_fichas_prompt([ficha])}\nPersonagem importado manualmente.", m=u.message)
            await u.message.reply_text("🚀 Ficha ativada! Você pode usar /godmode se precisar ajustar mais alguma coisa.")
        else:
            await u.message.reply_text("⚠️ Erro ao salvar no banco de dados.")
            
    except Exception as e:
        await u.message.reply_text(f"⚠️ Erro de formatação: {e}. Certifique-se de usar o modelo corretamente.")

# ══════ HELPERS ══════
async def ask(chat,p,ret=4,m=None):
    trace("AI_REQ","→ Gemini",extra=f"prompt_len={len(p)} first_50='{p[:50]}...'")
    for i in range(ret):
        try:
            resp=chat.send_message(p).text
            trace("AI_RES","← Gemini",extra=f"resp_len={len(resp)} has_tags={'[' in resp and ':' in resp}")
            return resp
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
        lines.append(f"Habilidades Ativas e Passivas:\n{f.get('habilidades',[])}\n")
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
    [Btn("🚀 Novo Jogo",callback_data="m:lobby"),Btn("🧑‍🚀 Criar Personagem",callback_data="m:criar")],
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
    cid = u.effective_chat.id
    uid = u.message.from_user.id
    old_history=len(chats[cid].history) if cid in chats else 0
    had_game=jogo_ativo.get(cid,False)
    had_godmode=bool(godmode)
    trace("SESSION","🔄 RESET",uid=uid,cid=cid,extra=f"history={old_history} game={had_game}")
    chats.pop(cid, None)
    jogo_ativo.pop(cid, None)
    godmode.clear()
    cstate.pop(uid, None) 
    txt=(f"🔄 *RESET COMPLETO*\n━━━━━━━━━━━━━━━━━━━━\n"
         f"🧹 Histórico IA: *{old_history} msgs removidas*\n"
         f"🎮 Sessão: *{'desligada' if had_game else 'já estava off'}*\n"
         f"🔱 Godmode: *{'desativado' if had_godmode else 'n/a'}*\n"
         f"💾 Fichas e sessões: *intactas no banco*\n"
         f"━━━━━━━━━━━━━━━━━━━━\n"
         f"_Use /novojogo para iniciar nova sessão._")
    await u.message.reply_text(txt,reply_markup=MAIN_KB,parse_mode="Markdown")
async def cmd_help(u,c): await rp(u.message,"📡 *PROTOCOLOS*\n━━━━━━━━━━━━━━━━━━━━\n⚔️ /iniciar /novojogo /criarpersonagem /importar\n🎲 Rolagens: /1d20 /2d8p4 /1d6m1 (p=plus m=minus)\n💾 /ficha /fichas /deletarficha /levelup /implante\n📚 /salvarsessao /sessoes /cargarsessao ID /contexto\n📖 /glossario /regras /reset /ajuda")

async def cmd_debug(u,c):
    uid=str(u.message.from_user.id)
    if ADMIN and uid!=str(ADMIN):
        await u.message.reply_text("❌ Acesso negado.");return
    cid=u.effective_chat.id
    await u.message.reply_text("⚙️ _Executando diagnóstico..._",parse_mode="Markdown")
    
    # ── 1. Reload forçado do data_loader ──
    db_ok=DL.reload_all()
    
    txt="⚙️ *DIAGNÓSTICO COMPLETO*\n━━━━━━━━━━━━━━━━━━━━\n"
    
    # ── 2. Supabase ──
    txt+="\n*📡 SUPABASE*\n"
    if db_ok:
        txt+=f"🟢 Conexão: OK\n"
        txt+=f"🟢 dados_rpg: {len(DL.DISPLAY)} displays carregados\n"
    else:
        txt+=f"🔴 Conexão: FALHOU (usando fallback local)\n"
    
    # ── 3. Dados mecânicos ──
    txt+=f"\n*📦 DADOS MECÂNICOS*\n"
    checks=[
        ("Raças",DL.RACAS_STATS,9),("Classes",DL.CLASSES_STATS,15),
        ("Filosofias",DL.FILOS_STATS,12),("Tecnomancias",DL.TECNO_SCRIPTS,29),
        ("Implantes",DL.IMPLANTES_DATA,15),
    ]
    for nome,data,esperado in checks:
        qtd=len(data)
        icon="🟢" if qtd>=esperado else "🟡" if qtd>0 else "🔴"
        txt+=f"{icon} {nome}: {qtd}/{esperado}\n"
    
    # ── 4. Display (glossário do banco) ──
    txt+=f"\n*📖 GLOSSÁRIO (dados_rpg)*\n"
    display_keys=["display_racas","display_classes","display_armas_brancas","display_armas_fogo",
        "display_armaduras","display_ferramentas","display_implantes","display_naves",
        "display_modificacoes","display_filosofias","display_tecno_basicas",
        "display_tecno_injecoes","display_tecno_protocolos",
        "display_bestiario_planetas","display_bestiario_fauna","display_bestiario_vazio"]
    ok=0;fail=0
    for k in display_keys:
        val=DL.DISPLAY.get(k)
        if val:
            ok+=1
        else:
            fail+=1
            txt+=f"🔴 Faltando: `{k}`\n"
    if fail==0: txt+=f"🟢 Todos {ok}/{len(display_keys)} displays carregados\n"
    else: txt+=f"🟡 {ok}/{len(display_keys)} carregados, {fail} faltando\n"
    
    # Regras
    if DL.REGRAS_TEXT and len(DL.REGRAS_TEXT)>10:
        txt+=f"🟢 Regras: OK ({len(DL.REGRAS_TEXT)} chars)\n"
    else:
        txt+=f"🔴 Regras: vazio ou não carregado\n"
    
    # ── 5. Estado da sessão neste chat ──
    txt+=f"\n*🎮 SESSÃO (chat {cid})*\n"
    jogo=jogo_ativo.get(cid,False)
    txt+=f"{'🟢' if jogo else '⚫'} Jogo ativo: *{'SIM' if jogo else 'NÃO'}*\n"
    history_len=len(chats[cid].history) if cid in chats else 0
    txt+=f"🧠 Histórico IA: *{history_len} msgs* {'(limite 60)' if history_len>50 else ''}\n"
    god_users=[k for k,v in godmode.items() if v]
    txt+=f"🔱 Godmode: *{'ATIVO (' + ','.join(god_users) + ')' if god_users else 'off'}*\n"
    
    # ── 6. Fichas ativas neste chat ──
    actives=db_get_all_active(cid)
    txt+=f"\n*👥 FICHAS ATIVAS*\n"
    if actives:
        for f in actives:
            txt+=f"  ✅ {f.get('user_name','?')} → *{f.get('nome','?')}* (Nv{f.get('nivel',1)} ❤️{f.get('pv_atual','?')}/{f.get('pv_max','?')})\n"
    else:
        txt+="  ⚫ Nenhuma ficha ativa neste chat\n"
    
    # ── 7. Gemini ──
    txt+=f"\n*🤖 GEMINI*\n"
    txt+=f"🟢 Modelo: `{mdl.model_name}`\n"
    try:
        test_resp=mdl.generate_content("Responda apenas: OK")
        txt+=f"🟢 Ping: *OK* ({len(test_resp.text)} chars)\n"
    except Exception as e:
        txt+=f"🔴 Ping: *FALHOU* ({str(e)[:50]})\n"
    
    txt+="\n━━━━━━━━━━━━━━━━━━━━"
    await rp(u.message,txt)

async def cmd_godmode(u,c):
    uid=str(u.message.from_user.id)
    if not ADMIN or uid!=str(ADMIN):
        await u.message.reply_text("❌ Acesso negado.");return
    cid=u.effective_chat.id
    if godmode.get(uid):
        godmode.pop(uid,None)
        await u.message.reply_text("🔱 *GODMODE DESATIVADO*\n_Você voltou a ser mortal._",parse_mode="Markdown")
    else:
        godmode[uid]=cid
        await u.message.reply_text("🔱 *GODMODE ATIVADO*\n━━━━━━━━━━━━━━━━━━━━\n_O Criador assumiu o controle._\n\nSuas mensagens agora são comandos absolutos para a IA.\nDigite qualquer ordem: subir nível, mudar história, criar NPCs...\n\n/godmode novamente para desativar.",parse_mode="Markdown")

async def cmd_regras(u,c):
    DL.ensure_loaded()
    txt=DL.REGRAS_TEXT
    if txt: await rp(u.message,txt if isinstance(txt,str) else json.dumps(txt))
    else: await rp(u.message,"📖 *MANUAL*\n━━━━━━━━━━━━━━━━━━━━\n🎲 1d20+Atrib+Per ≥ CD\n⚔️ Melee:dado+For | 🔫 Ranged:dado+Des\n🛡️ CD:10+Des+Arm\n💥20=Crítico|💀1=Falha\n❤️0PV=Morte|🔋Pente:3t|🧠RAM:1+Int+½Tecno")

async def cmd_glossario(u,c): await u.message.reply_text("📖 *BANCO DE DADOS*",reply_markup=GLOSS_KB,parse_mode="Markdown")

async def cmd_iniciar(u,c):
    await _build_lobby(u.message,u.effective_chat.id)

async def _build_lobby(msg,cid):
    """Monta o painel de lobby mostrando quem está pronto."""
    actives=db_get_all_active(cid)
    lines=["🌌 *LOBBY DE SESSÃO*\n━━━━━━━━━━━━━━━━━━━━"]
    if actives:
        lines.append("*Tripulação confirmada:*")
        for f in actives:
            lines.append(f"  ✅ {f.get('user_name','?')} → *{f.get('nome','?')}* ({f.get('raca','')} {f.get('classe','')} Nv{f.get('nivel',1)})")
    else:
        lines.append("❌ _Nenhum tripulante selecionou personagem._")
    lines.append(f"\n👥 *{len(actives)}* jogador(es) pronto(s)")
    lines.append("\n_Cada jogador toca_ 🧑‍🚀 _para selecionar._")
    btns=[[Btn("🧑‍🚀 Selecionar Meu Personagem",callback_data="lobby:sel")]]
    if actives:
        btns.append([Btn("🔄 Atualizar Lobby",callback_data="lobby:refresh")])
        btns.append([Btn("🆕 Nova Aventura",callback_data="play:new"),Btn("📜 Continuar",callback_data="play:context")])
    await msg.reply_text("\n".join(lines),reply_markup=KBD(btns),parse_mode="Markdown")

async def cmd_novojogo(u,c):
    await _build_lobby(u.message,u.effective_chat.id)

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
    if cid not in chats or not chats[cid].history:
        await u.message.reply_text("❌ Sem sessão ativa para salvar.");return
    
    await u.message.reply_text("📝 _Extraindo diários de bordo..._",parse_mode="Markdown")
    
    # ── Extrai as últimas 50 mensagens do histórico real do Gemini ──
    history=chats[cid].history
    recent=history[-50:] if len(history)>50 else history
    
    log_lines=[]
    for msg in recent:
        role="JOGADOR" if msg.role=="user" else "MESTRE"
        text=""
        for part in msg.parts:
            if hasattr(part,"text") and part.text:
                # Limpa tags de sistema do log
                clean=STATE_RE.sub("",part.text).strip()
                if clean and "[ESCUTANDO]" not in clean.upper():
                    text=clean[:200]  # Trunca mensagens muito longas
        if text:
            log_lines.append(f"[{role}]: {text}")
    
    transcript="\n".join(log_lines)
    trace("SESSION",f"Extraindo contexto: {len(log_lines)} msgs de {len(recent)} no histórico",cid=cid)
    
    # ── Pede à IA para gerar resumo baseado no transcript real ──
    prompt_resumo=f"""RESUMO_SESSAO: Baseado no LOG REAL abaixo, escreva o resumo detalhado.
NÃO invente eventos que não estão no log. Use APENAS o que realmente aconteceu.

LOG DAS ÚLTIMAS {len(log_lines)} INTERAÇÕES:
{transcript}

FORMATO OBRIGATÓRIO:
## Resumo da Sessão: [Título Épico]

[Parágrafo: cenário, personagens presentes, atmosfera]

**[Nome do Evento 1]:**
[O que aconteceu, testes feitos, resultados, decisões]

**[Nome do Evento 2]:**
[Próximo evento, descobertas, consequências]

[...quantos eventos forem necessários...]

**Situação Atual:**
[Onde os personagens estão AGORA, o que está pendente, ganchos abertos]

---
[XP:0:todos:Resumo da Sessão]"""

    s = await ask(ch, prompt_resumo, m=u.message)
    t = await ask(ch, "Gere APENAS um Título CURTO de no máximo 6 palavras para esta sessão. Só o texto, sem aspas.")
    t = t.strip().strip('"')[:60]
    
    if db_save_session(cid,t,s): 
        await u.message.reply_text(f"✅ *Sessão Salva: {t}*\n📊 Baseada em *{len(log_lines)} interações* reais.", parse_mode="Markdown")
        await rp(u.message, s)

# 👇 ESTA É A FUNÇÃO QUE FALTAVA! 👇
async def cmd_sessoes(u,c):
    sl=db_list_sessions(u.effective_chat.id)
    if not sl: await u.message.reply_text("📚 Vazio.");return
    await rp(u.message,"📚 *MISSÕES:*\n"+"\n".join(f"• ID *{s['id']}* — {s.get('title','?')}" for s in sl)+"\n/cargarsessao ID")
# 👆 ----------------------------- 👆

async def cmd_cargarsessao(u,c):
    if not c.args: return
    try:sid=int(c.args[0])
    except: return
    s=db_get_session(sid)
    if not s or s.get("chat_id")!=str(u.effective_chat.id): return
    cid=u.effective_chat.id
    old_history=len(chats[cid].history) if cid in chats else 0
    chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
    nomes=", ".join(f.get("nome","?") for f in actives)
    trace("SESSION",f"📂 Carregando sessão {sid}",cid=cid,extra=f"purged={old_history}")
    boot=(f"⚙️ *BOOT DO MESTRE*\n━━━━━━━━━━━━━━━━━━━━\n"
          f"🧹 Memória: *PURGADA* ({old_history} msgs)\n"
          f"📂 Sessão: *{s.get('title','?')}*\n"
          f"📋 Fichas: *{len(actives)}* ({nomes})\n"
          f"✅ Sistema: *ONLINE*\n━━━━━━━━━━━━━━━━━━━━")
    await u.message.reply_text(boot,parse_mode="Markdown")
    if ctx: await ask(ch,ctx)
    jogo_ativo[cid] = True
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Retomando '{s.get('title')}'.\n{s.get('summary')}\nRecapitule.",m=u.message))

async def cmd_contexto(u,c):
    txt=u.message.text.replace("/contexto","",1).strip()
    if not txt: await u.message.reply_text("📎 `/contexto texto...`",parse_mode="Markdown");return
    cid=u.effective_chat.id
    old_history=len(chats[cid].history) if cid in chats else 0
    chats.pop(cid,None);ch=gc(cid)
    actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
    nomes=", ".join(f.get("nome","?") for f in actives)
    trace("SESSION","📎 Contexto manual",cid=cid,extra=f"purged={old_history}")
    boot=(f"⚙️ *BOOT DO MESTRE*\n━━━━━━━━━━━━━━━━━━━━\n"
          f"🧹 Memória: *PURGADA* ({old_history} msgs)\n"
          f"📎 Contexto: *manual*\n"
          f"📋 Fichas: *{len(actives)}* ({nomes})\n"
          f"✅ Sistema: *ONLINE*\n━━━━━━━━━━━━━━━━━━━━")
    await u.message.reply_text(boot,parse_mode="Markdown")
    if ctx: await ask(ch,ctx)
    jogo_ativo[cid] = True
    await rp(u.message,await ask(ch,f"CONTEXTO_SESSAO: Importado.\n{txt}\nConfirme.",m=u.message))
    if db:db_save_session(cid,"📎 Importado",txt)

# ══════ CALLBACK ROUTER ══════
async def on_cb(u:Update,c:ContextTypes.DEFAULT_TYPE):
    try:
        q=u.callback_query;await q.answer();d=q.data;m=q.message
        uid=q.from_user.id;cid=m.chat_id;un=q.from_user.first_name or"?"
        trace("BTN",f"callback='{d}'",uid=uid,cid=cid,extra=f"user={un}")

        if d in("m:back","m:start"): await m.reply_text(WELCOME,reply_markup=MAIN_KB,parse_mode="Markdown")
        elif d in("m:lobby","m:init"):
            await _build_lobby(m,cid)
        elif d.startswith("sel:"):
            fid=int(d[4:]);db_set_active(uid,cid,fid);f=db_get_ficha(fid)
            if f:
                await m.reply_text(f"✅ *{f.get('nome','?')}* ativado!",parse_mode="Markdown")
                await rp(m,ff(f))
                ch=gc(cid);await ask(ch,f"FICHAS_ATIVAS:\n{inject_fichas_prompt([f])}",m=m)
                # Mostra lobby atualizado para todos verem
                await _build_lobby(m,cid)
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
        elif d=="m:help": await rp(m,"📡 /iniciar /novojogo /criarpersonagem /importar\n🎲 Rolagens: /1d20 /2d8p4 /1d6m1 (p=plus m=minus)\n💾 /ficha /fichas /deletarficha /levelup /implante\n📚 /salvarsessao /sessoes /cargarsessao ID /contexto\n📖 /glossario /regras /reset /ajuda")

        # ── Lobby ──
        elif d=="lobby:sel":
            fichas=db_list_fichas(uid,cid)
            if not fichas:
                await m.reply_text("❌ Sem personagens. Use /criarpersonagem ou /importar primeiro.");return
            btns=[Btn(f"⚔️ {f['nome']} (Nv{f['nivel']})",callback_data=f"sel:{f['id']}") for f in fichas]
            await m.reply_text(f"🧑‍🚀 *{un}, selecione seu personagem:*",reply_markup=KBD([[b] for b in btns]),parse_mode="Markdown")
        elif d=="lobby:refresh":
            await _build_lobby(m,cid)

        elif d=="play:new":
            actives=db_get_all_active(cid)
            if not actives:
                await m.reply_text("❌ Nenhum jogador selecionou personagem. Usem 🧑‍🚀 no lobby.");return
            
            # ── Boot sequence com diagnóstico ──
            old_history=len(chats[cid].history) if cid in chats else 0
            chats.pop(cid,None)  # PURGA total do histórico Gemini
            ch=gc(cid)           # Chat novo, history=[]
            ctx=inject_fichas_prompt(actives)
            n_jogadores=len(actives)
            modo="singular" if n_jogadores<=1 else "plural"
            nomes=", ".join(f.get("nome","?") for f in actives)
            
            trace("SESSION","▶️ Nova aventura",uid=uid,cid=cid,extra=f"purged={old_history}msgs jogadores={n_jogadores}")
            
            boot=(f"⚙️ *BOOT DO MESTRE*\n━━━━━━━━━━━━━━━━━━━━\n"
                  f"🧹 Memória anterior: *PURGADA* ({old_history} msgs removidas)\n"
                  f"🧠 IA: *Nova instância* (histórico zerado)\n"
                  f"📋 Fichas injetadas: *{n_jogadores}* ({nomes})\n"
                  f"🎭 Modo: *{modo}*\n"
                  f"✅ Sistema: *ONLINE*\n━━━━━━━━━━━━━━━━━━━━")
            await q.edit_message_text(boot,parse_mode="Markdown")
            
            if ctx: await ask(ch,f"MODO_NARRATIVA: {modo}. {n_jogadores} jogador(es) ativo(s).\n{ctx}")
            jogo_ativo[cid] = True
            await rp(m,await ask(ch,"SISTEMA: NOVA aventura no Sistema Solar. Cena épica. Gancho. Opções. Conciso.",m=m))
        elif d=="play:context":
            if jogo_ativo.get(cid):
                # Já tem sessão ativa — aviso grave
                history_len=len(chats[cid].history) if cid in chats else 0
                cstate[uid]={"step":"wait_context_confirm","chat_id":cid}
                await q.edit_message_text(
                    f"⚠️ *ATENÇÃO — SESSÃO ATIVA*\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"Existe uma sessão em andamento com *{history_len} mensagens*.\n\n"
                    f"Continuar vai *APAGAR TODO O HISTÓRICO* e iniciar do zero com contexto importado.\n\n"
                    f"Tem certeza?",
                    reply_markup=KBD([[Btn("⚠️ SIM, apagar e reimportar",callback_data="ctx:confirm")],
                                      [Btn("❌ CANCELAR — manter sessão",callback_data="ctx:cancel")]]),
                    parse_mode="Markdown")
            else:
                cstate[uid]={"step":"wait_context","chat_id":cid,"ts":time.time()}
                await q.edit_message_text(
                    "📜 *Envio de Contexto*\n━━━━━━━━━━━━━━━━━━━━\n"
                    "Digite o resumo da aventura anterior.\n\n"
                    "_⏳ Expira em 2 minutos. Qualquer outra ação cancela._",
                    reply_markup=KBD([[Btn("❌ Cancelar",callback_data="ctx:cancel")]]),
                    parse_mode="Markdown")

        # ── Contexto: confirmar/cancelar ──
        elif d=="ctx:confirm":
            cstate[uid]={"step":"wait_context","chat_id":cid,"ts":time.time()}
            await q.edit_message_text(
                "📜 *Confirmado.* Digite o resumo da aventura.\n_⏳ Expira em 2 minutos._",
                reply_markup=KBD([[Btn("❌ Cancelar",callback_data="ctx:cancel")]]),
                parse_mode="Markdown")
        elif d=="ctx:cancel":
            cstate.pop(uid,None)
            await q.edit_message_text("✅ *Cancelado.* Sessão atual mantida intacta.",parse_mode="Markdown")

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
                    st["atributos_base"][ATTR_KEYS[5]]=chosen;st["step"]="equip"
                    await _fin_attrs(m,uid)
            else:
                st["step"]="equip"
                await q.edit_message_text(f"✅ {ATTR_LABELS[5]}: *{chosen}*",parse_mode="Markdown")
                await _fin_attrs(m,uid)
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

        elif d.startswith("la:"):
            k=d[3:];st=cstate.get(uid)
            if not st or st.get("step")!="lvl_attr":return
            fid=st.get("ficha_id")
            if not fid: return
            f=db_get_ficha(fid)
            if not f:
                await m.reply_text("⚠️ Ficha não encontrada.")
                return
            a=f.get("atributos",{})
            if not isinstance(a, dict): a = {}
            val = int(a.get(k, 8)) + 1
            a[k] = val
            db_update_ficha(fid,{"atributos":a})
            
            await q.edit_message_text(f"✅ {ATTR_SHORT[ATTR_KEYS.index(k)]}→*{val}*({calc_mod(val):+d})",parse_mode="Markdown")
            
            st["step"]="lvl_per"
            per=f.get("pericias",{})
            if not isinstance(per, dict): per = {}
            limit=5 if st.get("novo_nv", 1)<=4 else 7
            all_per=set(list(per.keys())+list(PERICIAS_NOMES.keys()))
            per_btns=[Btn(f"{PERICIAS_NOMES.get(pk,pk)}(+{per.get(pk,0)})",callback_data=f"lp:{pk}") for pk in sorted(all_per) if int(per.get(pk,0))<limit]
            await m.reply_text("🎯 *+1 Perícia:*",reply_markup=KBD([per_btns[i:i+2] for i in range(0,len(per_btns),2)]),parse_mode="Markdown")
            
        elif d.startswith("lp:"):
            k=d[3:];st=cstate.get(uid)
            if not st or st.get("step")!="lvl_per":return
            fid=st.get("ficha_id")
            if not fid: return
            f=db_get_ficha(fid)
            if not f:
                await m.reply_text("⚠️ Ficha não encontrada.")
                return
            
            per=f.get("pericias",{})
            if not isinstance(per, dict): per = {}
            
            try: val = int(per.get(k, 0)) + 1
            except: val = 1
            per[k] = val
            
            db_update_ficha(fid,{"pericias":per})
            await q.edit_message_text(f"✅ {PERICIAS_NOMES.get(k,k)}→*+{val}*",parse_mode="Markdown")
            
            tecno_skill=int(per.get("tecnomancia",0))
            novo_nv=st.get("novo_nv", 1)
            
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
            
            cstate.pop(uid,None)
            await m.reply_text(f"⬆️ *{f.get('nome','?')}* Nv{novo_nv} completo!",parse_mode="Markdown")
            ch=gc(cid)
            await ask(ch,f"SISTEMA: {f.get('nome','?')} subiu Nv{novo_nv}.",m=m)

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
            fid=st.get("ficha_id")
            if not fid: return
            f=db_get_ficha(fid)
            if not f:
                await m.reply_text("⚠️ Ficha não encontrada."); return
                
            tc=list(f.get("tecnomancias",[])or[])
            if sid2 not in tc: tc.append(sid2);db_update_ficha(fid,{"tecnomancias":tc})
            nm_s=DL.TECNO_SCRIPTS.get(sid2,{}).get("nome",sid2)
            await q.edit_message_text(f"✅ Aprendeu: *{nm_s}*",parse_mode="Markdown")
            
            cstate.pop(uid,None)
            await m.reply_text(f"⬆️ Level up completo!",parse_mode="Markdown")
            ch=gc(cid)
            await ask(ch,f"SISTEMA: {f.get('nome','?')} aprendeu {nm_s}.",m=m)

    except Exception as e:
        log.error(f"Erro Global Callback: {e}")
        try: await u.callback_query.message.reply_text(f"⚠️ Erro ao processar o botão: {e}")
        except: pass

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

async def on_msg(u:Update,c:ContextTypes.DEFAULT_TYPE):
    cid=u.effective_chat.id;txt=u.message.text;un=u.message.from_user.first_name or"?"
    uid=u.message.from_user.id;username=u.message.from_user.username or un
    if not txt:return
    trace("MSG_IN",f"texto='{txt[:80]}...' " if len(txt)>80 else f"texto='{txt}'",uid=uid,cid=cid,extra=f"user={un} jogo={jogo_ativo.get(cid,False)} godmode={godmode.get(str(uid),False)}")

    st=cstate.get(uid)

    dice_match=DICE_RE.match(txt.strip())
    if dice_match:
        n=int(dice_match.group(1) or 1);s=int(dice_match.group(2))
        mod_sign=dice_match.group(3);mod_val=int(dice_match.group(4) or 0)
        mod=mod_val if mod_sign in("p","+") else -mod_val if mod_sign in("m","-") else 0
        if 1<=n<=20 and 1<=s<=100:
            rolls=[rng.randint(1,s) for _ in range(n)];total=sum(rolls)+mod
            mod_str=f"{mod:+d}" if mod else ""
            cr=""
            if s==20 and n==1:
                if rolls[0]==20:cr="\n🌟 *CRÍTICO!*"
                elif rolls[0]==1:cr="\n💀 *FALHA CRÍTICA!*"
            await rp(u.message,f"🎲 *{n}d{s}{mod_str}*\n{rolls}{f' {mod_str}' if mod else ''} = *{total}*{cr}")
            trace("DICE",f"{n}d{s}{mod_str}={total}",uid=uid,cid=cid,extra=f"rolls={rolls} inject_ia={jogo_ativo.get(cid,False)}")
            
            if jogo_ativo.get(cid):
                ficha=db_get_active(uid,cid)
                nome_pc=ficha.get("nome","?") if ficha else un
                ch=gc(cid)
                await ask(ch,f"[SISTEMA: O personagem {nome_pc} rolou {n}d{s}{mod_str} e obteve {total}. Narre a consequência.]",m=u.message)
                resp=ch.history[-1].parts[0].text if ch.history else ""
                if resp:
                    clean=await intercept_and_sync(resp,cid,msg=u.message)
                    if "[ESCUTANDO]" in clean.upper():
                        clean = re.sub(r'\[?ESCUTANDO\]?', '', clean, flags=re.IGNORECASE).strip()
                    if clean: await rp(u.message,clean)
            return

    if st and st.get("step")=="wait_context_confirm" and st.get("chat_id")==cid:
        # Esperando confirmação por BOTÃO, não por texto
        await u.message.reply_text("⚠️ Aguardando confirmação. Use os botões acima ou /reset para cancelar.")
        return

    if st and st.get("step")=="wait_context" and st.get("chat_id")==cid:
        # Expiração: 2 minutos
        ts=st.get("ts",0)
        if time.time()-ts>120:
            cstate.pop(uid,None)
            trace("GATE","⏰ wait_context EXPIROU — mensagem tratada normalmente",uid=uid,cid=cid)
            # NÃO retorna — cai no fluxo normal de jogo abaixo
        else:
            # Confirmação: mostra o que vai acontecer antes de purgar
            old_history=len(chats[cid].history) if cid in chats else 0
            chats.pop(cid,None);ch=gc(cid)
            actives=db_get_all_active(cid);ctx=inject_fichas_prompt(actives)
            modo="singular" if len(actives)<=1 else "plural"
            nomes=", ".join(f.get("nome","?") for f in actives)
            
            trace("SESSION","📜 Retomando com contexto",uid=uid,cid=cid,extra=f"purged={old_history}msgs jogadores={len(actives)}")
            
            boot=(f"⚙️ *BOOT DO MESTRE*\n━━━━━━━━━━━━━━━━━━━━\n"
                  f"🧹 Memória anterior: *PURGADA* ({old_history} msgs removidas)\n"
                  f"🧠 IA: *Nova instância* + contexto importado\n"
                  f"📋 Fichas: *{len(actives)}* ({nomes})\n"
                  f"✅ Sistema: *ONLINE*\n━━━━━━━━━━━━━━━━━━━━")
            await u.message.reply_text(boot,parse_mode="Markdown")
            
            if ctx: await ask(ch,f"MODO_NARRATIVA: {modo}.\n{ctx}")
            jogo_ativo[cid] = True 
            resp=await ask(ch,f"CONTEXTO_SESSAO: Retomando.\n{txt}\nRecapitule e pergunte ação.",m=u.message)
            await rp(u.message,resp);cstate.pop(uid,None);return

    if st and st.get("step")=="nome" and st.get("chat_id")==cid:
        st["nome"]=txt.strip()[:30]
        ficha=build_ficha(st)
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

    if godmode.get(str(uid)):
        trace("GODMODE",f"Ordem: '{txt[:80]}'",uid=uid,cid=cid)
        ch=gc(cid)
        try:
            ficha=db_get_active(uid,cid)
            nome_pc = ficha.get("nome","todos") if ficha else "todos"
            header = (f"[GODMODE - Criador interagindo com foco em '{nome_pc}'] Ordem: {txt}\n"
                      f"⚠️ SISTEMA: Se o Criador pediu XP, níveis, itens ou cura, OBRIGATORIAMENTE termine a narração com a tag exata, ex: [XP:100:{nome_pc}:Godmode]")
            resp=await ask(ch,header,m=u.message)
            th(cid)
            clean=await intercept_and_sync(resp,cid,msg=u.message)
            if "[ESCUTANDO]" in clean.upper():
                clean=re.sub(r'\[?ESCUTANDO\]?','',clean,flags=re.IGNORECASE).strip()
            if clean: await rp(u.message,clean)
        except Exception as e:
            log.error(f"Godmode:{e}");await u.message.reply_text("⚠️ Erro no GODMODE.")
        return

    if not jogo_ativo.get(cid):
        trace("GATE","❌ Mensagem IGNORADA — jogo_ativo=False",uid=uid,cid=cid)
        # Cooldown: avisa no máximo 1x a cada 5 minutos por chat
        last_gate=cstate.get(f"gate_{cid}",0)
        if time.time()-last_gate>300:
            cstate[f"gate_{cid}"]=time.time()
            await u.message.reply_text("⚠️ _Sessão inativa (servidor pode ter reiniciado)._\n\n🚀 /novojogo — iniciar nova sessão\n📂 /cargarsessao ID — retomar sessão salva\n📋 /sessoes — ver sessões disponíveis",parse_mode="Markdown")
        return
    
    ficha=db_get_active(uid,cid)
    if not ficha:
        trace("GATE","❌ Mensagem IGNORADA — sem ficha ativa",uid=uid,cid=cid)
        await u.message.reply_text(f"⚠️ *{un}*, você não tem personagem ativo neste chat.\nUse /novojogo e selecione seu personagem no lobby.",parse_mode="Markdown")
        return
    
    ch=gc(cid)
    try:
        nome_pc=ficha.get("nome","?")
        header=f"[Usuário: @{username} | Personagem: {nome_pc}] diz: {txt}"
        resp=await ask(ch,header,m=u.message)
        th(cid)
        clean=await intercept_and_sync(resp,cid,msg=u.message)
        
        if "[ESCUTANDO]" in clean.upper():
            trace("AI_RES","IA em modo ESCUTANDO (silêncio)",uid=uid,cid=cid)
            clean = re.sub(r'\[?ESCUTANDO\]?', '', clean, flags=re.IGNORECASE).strip()
            if not clean: return 
        
        trace("MSG_OUT",f"resp_len={len(clean)}",cid=cid)
        await rp(u.message,clean)
    except Exception as e:
        log.error(f"Msg:{e}");await u.message.reply_text("⚠️ Interferência.")

async def on_err(u,c):
    trace("ERROR",f"Global: {c.error}")
    log.error(f"Err:{c.error}")

# ══════ KEEP-ALIVE (evita Render free tier dormir) ══════
async def keep_alive():
    """Pinga o próprio servidor a cada 10 minutos."""
    if not WH:
        log.info("⏸️ Keep-alive desativado (sem WEBHOOK_URL)")
        return
    import urllib.request
    while True:
        await asyncio.sleep(600)
        try:
            await asyncio.to_thread(urllib.request.urlopen,WH,timeout=10)
            trace("SESSION","💓 Keep-alive OK")
        except Exception as e:
            trace("SESSION",f"💓 Keep-alive falhou: {e}")

async def post_init(app):
    asyncio.create_task(keep_alive())
    log.info("💓 Keep-alive iniciado (ping a cada 10min)")

def main():
    DL.ensure_loaded()
    app=Application.builder().token(TG).post_init(post_init).build()
    for cmd,fn in[("start",cmd_start),("reset",cmd_reset),("ajuda",cmd_help),("help",cmd_help),("debug",cmd_debug),("godmode",cmd_godmode),
        ("iniciar",cmd_iniciar),("novojogo",cmd_novojogo),("criarpersonagem",cmd_criar),("importar",cmd_importar),
        ("regras",cmd_regras),("glossario",cmd_glossario),
        ("ficha",cmd_ficha),("fichas",cmd_fichas),("deletarficha",cmd_deletar),
        ("levelup",cmd_levelup),("implante",cmd_implante),
        ("salvarsessao",cmd_salvar_sessao),("sessoes",cmd_sessoes),
        ("cargarsessao",cmd_cargarsessao),("contexto",cmd_contexto)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,on_msg))
    app.add_handler(MessageHandler(filters.Regex(r'^/\d*d\d+'),on_msg))
    app.add_error_handler(on_err)
    if WH: app.run_webhook(listen="0.0.0.0",port=PT,url_path=TG,webhook_url=f"{WH}/{TG}")
    else: app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":main()
