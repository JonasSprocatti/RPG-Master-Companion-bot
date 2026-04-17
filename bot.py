"""
🌌 Passagem Sombria - RPG Master Bot
Bot com Gemini AI + Supabase + Botões interativos + Criação separada.
"""

import os
import json
import logging
import asyncio
import random as rng
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
ADMIN_ID = os.environ.get("ADMIN_ID", "")  # Telegram user ID do admin

# ── Supabase ─────────────────────────────────────────────
db = None
if SUPABASE_URL and SUPABASE_KEY:
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase conectado")
else:
    logger.warning("⚠️ Supabase não configurado")

# ══════════════════════════════════════════════════════════
# DADOS DAS RAÇAS, CLASSES E FILOSOFIAS (para botões)
# ══════════════════════════════════════════════════════════

RACAS = {
    "mercusys":     ("🔥 Mercusys", "Mercúrio", "Velocidade dobrada, regeneração, leitura sensitiva"),
    "veny":         ("🌿 Ven'y", "Vênus", "Air Shifter — muda poderes respirando gases"),
    "terraqueo":    ("🌍 Terráqueo", "Terra", "Adaptável — pontos livres em atributos e perícias"),
    "marciano":     ("⚔️ Marciano", "Marte", "4 braços, Êxtase de Batalha, tanque de guerra"),
    "conjupitero":  ("⚙️ Conjupitero", "Júpiter", "80cm de engenharia pura, +2 Mecânica/Pilotagem"),
    "sata":         ("💫 Sata", "Saturno", "Cura genética, camuflagem cromática, médico nato"),
    "urak":         ("❄️ Urak", "Urano", "150 cordas vocais, mímica sonora, criogênese"),
    "proturno":     ("🧠 Proturno", "Netuno", "Telepatia, telecinese, controle mental"),
    "infimor":      ("🪐 Infimor", "Plutão", "3m de altura, imune ao vácuo, braços de 10m"),
}

CLASSES = {
    "estudioso":      ("📚 Estudioso", "+4PV", "Perito em fraquezas e conhecimento"),
    "mecanico":       ("🔧 Mecânico", "+6PV", "Repara aliados e naves em combate"),
    "assassino":      ("🗡️ Assassino", "+8PV", "Dano dobrado furtivo, desaparece ao matar"),
    "soldado":        ("🎖️ Soldado", "+10PV", "Tanque de fogo, supressão, armas pesadas"),
    "starlord":       ("🌟 Starlord", "+8PV", "Líder carismático, inspira aliados"),
    "franco_atirador":("🎯 Franco-Atirador", "+6PV", "+5 ataque à distância >30m"),
    "musico":         ("🎵 Músico", "+4PV", "Buff/debuff via frequências sonoras"),
    "espiao":         ("🕵️ Espião", "+4PV", "Disfarce perfeito, engenharia social"),
    "catador":        ("♻️ Catador", "+6PV", "Encontra loot extra, desmonta inimigos"),
    "piloto":         ("✈️ Piloto", "+6PV", "Deus do cockpit, +2CD veículos"),
    "batedor":        ("👁️ Batedor", "+8PV", "Nunca surpreendido, marca alvos"),
    "explorador":     ("🗺️ Explorador", "+6PV", "Ignora terreno difícil, analisa biologia"),
    "cinetico":       ("⚡ Cinético", "+4PV", "Tecnomante curador, repulsão cinética"),
    "prospector":     ("💼 Prospector", "+4PV", "Negociador, +20% créditos"),
    "pirata":         ("☠️ Pirata", "+10PV", "Terror em naves, grito amedrontador"),
}

FILOSOFIAS = {
    # Caminhos (Místicos)
    "cam_voz":        ("🗣️ Caminho da Voz", "Comando subliminar, finge-se de morto"),
    "cam_ressonancia":("🌀 Caminho da Ressonância", "Sente vivos no escuro em 10m"),
    "cam_engrenagem": ("⚙️ Caminho da Engrenagem", "Transforma falha crítica em falha comum"),
    "cam_espiral":    ("🧬 Caminho da Espiral", "Cura com vantagem nos dados"),
    "cam_anel":       ("💍 Caminho do Anel", "Sobrevive a golpe letal com 1PV"),
    "cam_ocaso":      ("🌑 Caminho do Ocaso", "Sofre 1d4, soma 1d4 em qualquer rolagem"),
    # Códigos (Seculares)
    "cod_sobrevivente":("🏕️ Código do Sobrevivente", "+2 Iniciativa, age em emboscadas"),
    "cod_corporativo": ("💰 Código Corporativo", "Vantagem em avaliar itens e negociar"),
    "cod_cetico":      ("🧊 Código do Cético", "+2CD vs ataques psíquicos"),
    "cod_fronteira":   ("🐺 Código da Fronteira", "+1 ataque se sozinho"),
    "cod_caserna":     ("🛡️ Código da Caserna", "Leva dano no lugar de aliado"),
    "cod_viralata":    ("🃏 Código do Vira-Lata", "Distrai e ataca com vantagem"),
}

# ── Estado de criação por usuário ────────────────────────
# Armazena {user_id: {"raca": ..., "classe": ..., "filosofia": ...}}
creation_state: dict = {}

# ── Tabela de XP por nível ───────────────────────────────
# XP_TABLE[nível_atual] = XP necessário para subir para o próximo
XP_TABLE = {
    1: 100, 2: 250, 3: 450, 4: 700, 5: 1000,
    6: 1400, 7: 1900, 8: 2500, 9: 3200,
}

# ── Carregar conteúdo do RPG ─────────────────────────────
RPG_FILE = os.path.join(os.path.dirname(__file__), "rpg_content.txt")
with open(RPG_FILE, "r", encoding="utf-8") as f:
    RPG_CONTENT = f.read()

# ── Formato JSON da ficha ────────────────────────────────
FICHA_JSON_FORMAT = """{
  "nome": "Nome", "raca": "Raça", "classe": "Classe",
  "filosofia": "Filosofia", "nivel": 1, "xp": 0,
  "pv_atual": 0, "pv_max": 0, "cd": 0,
  "ram_atual": 0, "ram_max": 0, "iniciativa": 0, "deslocamento": 9,
  "atributos": {"forca": 0, "destreza": 0, "constituicao": 0, "inteligencia": 0, "sabedoria": 0, "carisma": 0},
  "pericias": {"nome_pericia": 0},
  "habilidades": ["lista"],
  "armas": [{"nome": "Arma", "dano": "1d8", "efeito": ""}],
  "armadura": {"nome": "Armadura", "cd_bonus": 0},
  "inventario": ["item1"], "creditos": 100, "implantes": [], "notas": ""
}"""

# ── System prompt ────────────────────────────────────────
SYSTEM_PROMPT = f"""Você é o Mestre do RPG "Passagem Sombria - RPG Espacial".

PAPEL: narrar aventuras, controlar NPCs, aplicar regras, rolar dados.

ESTILO DE NARRAÇÃO:
- Português brasileiro, tom sombrio e cinematográfico
- Use emojis temáticos para dar vida visual à narrativa:
  💀 para perigo/morte, ⚔️ para combate, 🎲 para rolagens,
  🛡️ para defesa, 🚀 para naves/viagem, 🔥 para fogo/explosões,
  ❤️ para vida/cura, 🧠 para tecnomancia/mente, 💎 para créditos/loot,
  🌌 para espaço/ambiente, ⚡ para ação rápida, 🩸 para sangue/dano,
  👁️ para percepção/investigação, 🗣️ para diálogo de NPCs
- Use separadores visuais (━━━, ═══) para organizar combate e rolagens
- Em combate, mostre status visual: ❤️ PV: 45/60 | 🛡️ CD: 15
- Respostas concisas mas imersivas (máximo 800 palavras)

REGRAS MECÂNICAS:
1. Siga o sistema d20 fielmente
2. Formato de rolagem: 🎲 1d20(14) + Mod(3) + Perícia(2) = 19 vs CD 15 → ✅ Sucesso!
3. Em combate, mostre iniciativa, turnos e status de todos os envolvidos
4. Controle inventário, vida e status dos jogadores

═══════════════════════════════════════
SISTEMA DE EXPERIÊNCIA (XP) — SIGA RIGOROSAMENTE
═══════════════════════════════════════

XP NECESSÁRIO PARA SUBIR DE NÍVEL:
Nv1→2: 100 XP | Nv2→3: 250 XP | Nv3→4: 450 XP | Nv4→5: 700 XP
Nv5→6: 1000 XP | Nv6→7: 1400 XP | Nv7→8: 1900 XP | Nv8→9: 2500 XP | Nv9→10: 3200 XP

FONTES DE XP (conceda AUTOMATICAMENTE durante o jogo):
⚔️ COMBATE (por inimigo derrotado pelo grupo, dividido igualmente):
  - Lacaio (Comum): 15-25 XP
  - Elite (Forte): 40-60 XP
  - Chefe: 100-150 XP
  - Super Chefe: 200-300 XP
  - Cria do Vazio (qualquer): +50% bônus extra pelo perigo

📖 HISTÓRIA E ROLEPLAY:
  - Decisão importante para a trama: 25-50 XP
  - Completar objetivo de missão: 50-100 XP
  - Resolver puzzle ou investigação complexa: 20-40 XP
  - Uso criativo de habilidade/perícia: 10-20 XP
  - Roleplay excepcional (interpretação marcante): 10-25 XP
  - Sobreviver a evento catastrófico: 15-30 XP
  - Descoberta de lore importante (Monólitos, Passagem): 30-50 XP

REGRAS DE CONCESSÃO DE XP:
- SEMPRE anuncie o XP ganho imediatamente após o evento, no formato:
  ✨ *+XX XP* — (motivo)
- Ao final de cada combate, mostre o XP total ganho por todos
- Mantenha o XP acumulado de cada jogador atualizado na sua memória
- Quando um jogador perguntar seu XP, responda com o total e quanto falta para o próximo nível
- XP de combate é DIVIDIDO igualmente entre todos os jogadores que participaram
- XP de roleplay/história é INDIVIDUAL (só quem fez a ação recebe)

═══════════════════════════════════════
DESCANSOS — QUANDO E COMO USAR
═══════════════════════════════════════

☕ DESCANSO CURTO (1-2 horas, local minimamente seguro):
  Efeitos: usar kits médicos, recuperar habilidades de Caminho/Código, reorganizar equipamento
  NÃO recupera: RAM, PV total, habilidades de classe
  NÃO permite: level up
  QUANDO SUGERIR (o Mestre deve propor naturalmente):
  - Após um combate difícil onde alguém ficou abaixo de 50% PV
  - Quando o grupo encontra uma sala segura temporária
  - Quando um jogador pede para tratar ferimentos
  - Entre encontros numa mesma missão/dungeon

🛏️ DESCANSO LONGO (8 horas, local SEGURO + comida):
  Efeitos: recupera TUDO (PV, RAM, habilidades, escudos)
  PERMITE: level up (se tiver XP suficiente)
  Consome: 1 ração por personagem
  QUANDO SUGERIR (o Mestre deve propor ou permitir):
  - Ao final de uma missão/arco narrativo completo
  - Quando o grupo volta para a nave/estalagem/base
  - Quando estão em viagem de dobra (tempo de trânsito)
  - Quando todos estão muito debilitados (maioria abaixo de 30% PV)
  - NUNCA em território hostil sem justificativa narrativa

  DURANTE O DESCANSO LONGO, se alguém tiver XP suficiente:
  - Anuncie: "⬆️ [Nome] tem XP suficiente para subir de nível! Use /levelup"
  - O level up SÓ pode acontecer durante descanso longo
  - Se alguém tentar /levelup fora de descanso longo, o Mestre deve informar
    que precisa descansar primeiro

COMPORTAMENTO DO MESTRE COM DESCANSOS:
- NÃO ofereça descanso longo a cada 5 minutos — deve ser significativo
- Se o grupo insistir em descansar em local perigoso, faça encontros aleatórios
- A viagem de dobra é o momento PERFEITO para descanso longo
- Use descansos curtos como momentos de diálogo e desenvolvimento de personagem

═══════════════════════════════════════

═══════════════════════════════════════
CRIAÇÃO DE PERSONAGEM — PASSO A PASSO (siga EXATAMENTE nesta ordem)
═══════════════════════════════════════

PASSO 1-3: Raça, Classe e Filosofia (já feitos por botões antes de você entrar)

PASSO 4 — ROLAGEM DE ATRIBUTOS:
a) Role 2d8 SETE vezes (cada dado é 1 a 8, some os 2). Mostre todos os 7 resultados.
b) Identifique e descarte o MENOR dos 7 valores.
c) Mostre os 6 valores restantes ordenados do maior ao menor.
d) Peça ao jogador para distribuir entre: Força, Destreza, Constituição, Inteligência, Sabedoria, Carisma.
e) ESPERE o jogador responder antes de continuar.

PASSO 5 — APLICAR MODIFICADORES RACIAIS:
Depois que o jogador distribuiu, some os modificadores da raça a cada atributo.
Mostre o resultado final no formato:
  💪 For: 6 (base) + (-1) racial = *5* (mod: -2)
  ⚡ Des: 9 (base) + 0 racial = *9* (mod: +0)
  etc.
Os MODIFICADORES são: valor 2-3=-3, 4-5=-2, 6-7=-1, 8-9=+0, 10-11=+1, 12-13=+2, 14-15=+3, 16+=+4

PASSO 6 — CALCULAR PV (Pontos de Vida):
⚠️ SIGA EXATAMENTE — este cálculo tem 3 partes:
a) Role o dado racial de VIDA: role 4d6 (cada dado 1 a 6), descarte o MENOR, some os 3 restantes.
   Exemplo: 🎲 4d6 → [4, 2, 5, 6] → descarta 2 → 4+5+6 = 15
b) Aplique o ajuste racial: (Mercusys -2, Ven'y -1, Terráqueo 0, Marciano +2,
   Conjupitero -3, Sata -1, Urak -1, Proturno -3, Infimor +3)
c) Some o bônus de PV da CLASSE (Estudioso +4, Mecânico +6, Assassino +8, Soldado +10,
   Starlord +8, Franco-Atirador +6, Músico +4, Espião +4, Catador +6, Piloto +6,
   Batedor +8, Explorador +6, Cinético +4, Prospector +4, Pirata +10)
d) PV FINAL = resultado da rolagem + ajuste racial + bônus classe
   Exemplo Proturno Cinético: 15 + (-3) + 4 = *16 PV*
MOSTRE CADA ETAPA SEPARADAMENTE para o jogador acompanhar.

PASSO 7 — CALCULAR CD (Classe de Defesa):
CD = 10 + Modificador de Destreza + Bônus da Armadura Inicial
(A armadura inicial vem do equipamento da classe)

PASSO 8 — CALCULAR RAM:
RAM = 1 + Modificador de Inteligência + ½ Perícia Tecnomancia (arredondar para baixo)
(Use a Tecnomancia que a classe dá como perícia inicial)

PASSO 9 — PERÍCIAS:
a) Aplique AUTOMATICAMENTE as perícias iniciais da classe. Mostre a lista completa:
   Exemplo Cinético: "🎯 Tecnomancia +5, Medicina +3, Resistência +2, Acrobacia +2"
b) Se a raça dá bônus em perícias (ex: Terráqueo +3 pontos livres, Conjupitero +2 Mecânica/Pilotagem),
   aplique-os também.
c) Mostre TODAS as perícias e seus valores finais.
d) Calcule a Iniciativa: Mod. Destreza + bônus (se houver da classe/filosofia)

PASSO 10 — EQUIPAMENTO:
Liste o equipamento inicial da classe com dano e efeitos.
Inclua o Kit de Sobrevivência Base (Comunicador, 3 rações, 2 luzes químicas, 100 CG).

PASSO 11 — NOME DO PERSONAGEM:
Pergunte o nome que o jogador quer dar ao personagem.

PASSO 12 — RESUMO FINAL:
Mostre a ficha completa formatada e adicione [FICHA_COMPLETA] na última linha.

REGRA: cada passo deve ser uma mensagem separada. ESPERE o jogador confirmar/responder
antes de avançar. NÃO pule passos. NÃO calcule tudo de uma vez.

═══════════════════════════════════════

LEVEL UP (SÓ EM DESCANSO LONGO + XP SUFICIENTE):
Dado de vida por nível: Pesado 1d10 (Marcianos, Infimor's), Médio 1d8 (Terráqueos, Ven'y,
Conjupiteros, Urak's), Leve 1d6 (Proturnos, Satas, Mercusys)
PV ganho = dado de vida + Mod. Constituição (mínimo 1)
+1 Atributo (máx +6), +1 perícia, +1 RAM em níveis ímpares (3,5,7,9)

FICHA JSON — quando pedirem EXPORT_FICHA, responda SÓ JSON puro:
{FICHA_JSON_FORMAT}

SEPARAÇÃO DE MODOS:
- MODO CRIAÇÃO: quando estiver criando personagem, foque APENAS na ficha. Não narre aventuras.
- MODO JOGO: quando estiver em sessão, narre normalmente.
- MODO CONTEXTO: quando receber CONTEXTO_SESSAO, absorva e continue dali.

AUTO-SAVE DE FICHA (MUITO IMPORTANTE):
Quando a criação do personagem estiver 100% COMPLETA (raça, classe, filosofia, atributos
distribuídos, PV/CD/RAM calculados, equipamento definido), faça o seguinte:
1. Apresente o resumo final da ficha para o jogador
2. Adicione EXATAMENTE a tag [FICHA_COMPLETA] na ÚLTIMA LINHA da sua resposta
3. Essa tag será detectada pelo sistema para salvar automaticamente
NUNCA use [FICHA_COMPLETA] antes da ficha estar totalmente finalizada.

REFERÊNCIA DO SISTEMA:
{RPG_CONTENT}
"""

# ── Configurar Gemini ────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemma-3-4b-it",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=0.85,
        max_output_tokens=1500,
    ),
)

# ── Chat sessions ────────────────────────────────────────
MAX_HISTORY = 30
chat_sessions: dict = {}


def get_chat(chat_id: int):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    return chat_sessions[chat_id]


def trim_history(chat_id: int):
    if chat_id in chat_sessions:
        s = chat_sessions[chat_id]
        if len(s.history) > MAX_HISTORY * 2:
            s.history = s.history[-(MAX_HISTORY * 2):]


# ══════════════════════════════════════════════════════════
# SUPABASE HELPERS
# ══════════════════════════════════════════════════════════

def save_ficha(user_id, user_name, chat_id, ficha_data):
    if not db: return False
    try:
        db.table("fichas").upsert({
            "user_id": str(user_id), "chat_id": str(chat_id),
            "user_name": user_name,
            "character_name": ficha_data.get("nome", "?"),
            "ficha": json.dumps(ficha_data, ensure_ascii=False),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id,chat_id").execute()
        return True
    except Exception as e:
        logger.error(f"Erro salvar ficha: {e}"); return False


def load_ficha(user_id, chat_id):
    if not db: return None
    try:
        r = db.table("fichas").select("ficha").eq("user_id", str(user_id)).eq("chat_id", str(chat_id)).execute()
        return json.loads(r.data[0]["ficha"]) if r.data else None
    except Exception as e:
        logger.error(f"Erro carregar ficha: {e}"); return None


def list_fichas(chat_id):
    if not db: return []
    try:
        r = db.table("fichas").select("user_id,user_name,character_name,updated_at").eq("chat_id", str(chat_id)).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"Erro listar: {e}"); return []


def delete_ficha(user_id, chat_id):
    """Deleta a ficha de um usuário num chat específico."""
    if not db: return False
    try:
        db.table("fichas").delete().eq("user_id", str(user_id)).eq("chat_id", str(chat_id)).execute()
        return True
    except Exception as e:
        logger.error(f"Erro deletar ficha: {e}"); return False


def save_session_log(chat_id, title, summary):
    if not db: return False
    try:
        db.table("sessoes").insert({"chat_id": str(chat_id), "title": title, "summary": summary, "created_at": datetime.now(timezone.utc).isoformat()}).execute()
        return True
    except Exception as e:
        logger.error(f"Erro sessão: {e}"); return False


def load_session_logs(chat_id):
    if not db: return []
    try:
        r = db.table("sessoes").select("id,title,created_at").eq("chat_id", str(chat_id)).order("created_at", desc=True).limit(10).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"Erro listar sessões: {e}"); return []


def load_session_by_id(session_id):
    if not db: return None
    try:
        r = db.table("sessoes").select("*").eq("id", session_id).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"Erro carregar sessão: {e}"); return None


# ══════════════════════════════════════════════════════════
# FORMAT FICHA
# ══════════════════════════════════════════════════════════

def format_ficha(f):
    a = f.get("atributos", {})
    armas = f.get("armas", [])
    armas_t = "\n".join(f"  ⚔️ {x.get('nome','?')} ({x.get('dano','?')}) {x.get('efeito','')}" for x in armas) if armas else "  Nenhuma"
    impl = ", ".join(f.get("implantes", [])) or "Nenhum"
    inv = ", ".join(f.get("inventario", [])) or "Vazio"
    per = f.get("pericias", {})
    per_t = ", ".join(f"{k} +{v}" for k, v in per.items() if v) if per else "Nenhuma"
    habs = f.get("habilidades", [])
    hab_t = "\n".join(f"  🔹 {h}" for h in habs) if habs else "  Nenhuma"
    arm = f.get("armadura", {})
    arm_n = arm.get("nome", "Nenhuma") if isinstance(arm, dict) else str(arm)

    return (
        f"🧑‍🚀 *FICHA: {f.get('nome', '???')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌌 Raça: {f.get('raca', '?')} | ⚔️ Classe: {f.get('classe', '?')}\n"
        f"📜 Filosofia: {f.get('filosofia', '?')}\n"
        f"📊 Nível: {f.get('nivel', 1)} | ✨ XP: {f.get('xp', 0)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ PV: {f.get('pv_atual', '?')}/{f.get('pv_max', '?')} | "
        f"🛡️ CD: {f.get('cd', '?')} | 🧠 RAM: {f.get('ram_atual', '?')}/{f.get('ram_max', '?')}\n"
        f"⚡ Iniciativa: +{f.get('iniciativa', 0)} | 🏃 Desloc: {f.get('deslocamento', 9)}m\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💪 For: {a.get('forca', '?')} | ⚡ Des: {a.get('destreza', '?')} | "
        f"🩸 Con: {a.get('constituicao', '?')}\n"
        f"🧠 Int: {a.get('inteligencia', '?')} | 🦉 Sab: {a.get('sabedoria', '?')} | "
        f"🗣️ Car: {a.get('carisma', '?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Perícias: {per_t}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠️ Habilidades:\n{hab_t}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ Armas:\n{armas_t}\n"
        f"🛡️ Armadura: {arm_n}\n"
        f"🦾 Implantes: {impl}\n"
        f"🎒 Inventário: {inv}\n"
        f"💎 Créditos: {f.get('creditos', 0)} CG\n"
    )


# ══════════════════════════════════════════════════════════
# GEMINI COM RETRY
# ══════════════════════════════════════════════════════════

async def send_to_gemini(chat, prompt, retries=4, telegram_msg=None):
    for attempt in range(retries):
        try:
            return chat.send_message(prompt).text
        except google_exceptions.ResourceExhausted as e:
            ed = str(e)
            if "per_day" in ed:
                return "⚠️ Limite diário atingido. Tente amanhã. /rolar e /ficha funcionam offline."
            wait = (2 ** attempt) * 10 + rng.uniform(0, 5)
            logger.warning(f"429. Tentativa {attempt+1}/{retries}. {wait:.0f}s...")
            if telegram_msg and attempt < retries - 1:
                try: await telegram_msg.reply_text(f"⏳ _Retentando em {wait:.0f}s..._", parse_mode="Markdown")
                except: pass
            await asyncio.sleep(wait)
        except Exception as e:
            logger.error(f"Erro Gemini: {e}")
            if attempt == retries - 1: raise
            await asyncio.sleep(5)
    return "⚠️ Mestre indisponível. Aguarde e tente novamente."


async def reply_safe(msg, text):
    if len(text) > 4000:
        for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            try: await msg.reply_text(part, parse_mode="Markdown")
            except: await msg.reply_text(part)
    else:
        try: await msg.reply_text(text, parse_mode="Markdown")
        except: await msg.reply_text(text)


def parse_json_response(raw):
    c = raw.strip()
    if c.startswith("```"): c = c.split("\n", 1)[-1]
    if c.endswith("```"): c = c.rsplit("```", 1)[0]
    try: return json.loads(c.strip())
    except: logger.error(f"JSON inválido: {raw[:300]}"); return None


# ══════════════════════════════════════════════════════════
# CRIAÇÃO DE PERSONAGEM COM BOTÕES
# ══════════════════════════════════════════════════════════

def build_keyboard(items, prefix, cols=2):
    """Cria teclado inline a partir de um dict de items."""
    buttons = []
    for key, val in items.items():
        label = val[0] if isinstance(val, tuple) else val
        buttons.append(InlineKeyboardButton(label, callback_data=f"{prefix}:{key}"))
    # Organiza em linhas de N colunas
    return InlineKeyboardMarkup([buttons[i:i+cols] for i in range(0, len(buttons), cols)])


async def cmd_create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    creation_state[user_id] = {}

    text = (
        "🧑‍🚀 *CRIAÇÃO DE PERSONAGEM*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Vamos criar seu viajante das estrelas!\n"
        "📋 Passo 1 de 4: Escolha sua *Raça*\n\n"
        "Cada raça vem de um planeta diferente\n"
        "com habilidades únicas. Toque para escolher:"
    )

    keyboard = build_keyboard(RACAS, "raca", cols=2)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def callback_raca(query, data_key):
    user_id = query.from_user.id
    raca_info = RACAS[data_key]

    creation_state.setdefault(user_id, {})
    creation_state[user_id]["raca"] = data_key
    creation_state[user_id]["raca_nome"] = raca_info[0]

    await query.edit_message_text(
        f"✅ Raça escolhida: *{raca_info[0]}*\n"
        f"🌍 Planeta: {raca_info[1]}\n"
        f"⚡ Destaque: {raca_info[2]}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Passo 2 de 4: Escolha sua *Classe*\n\n"
        f"Sua especialização define seu papel no grupo:",
        parse_mode="Markdown"
    )

    keyboard = build_keyboard(CLASSES, "classe", cols=2)
    await query.message.reply_text("⚔️ Toque para escolher sua classe:", reply_markup=keyboard)


async def callback_classe(query, data_key):
    user_id = query.from_user.id
    classe_info = CLASSES[data_key]

    creation_state.setdefault(user_id, {})
    creation_state[user_id]["classe"] = data_key
    creation_state[user_id]["classe_nome"] = classe_info[0]

    await query.edit_message_text(
        f"✅ Classe escolhida: *{classe_info[0]}*\n"
        f"❤️ Bônus de Vida: {classe_info[1]}\n"
        f"🎯 Papel: {classe_info[2]}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Passo 3 de 4: Escolha sua *Filosofia de Vida*\n\n"
        f"🌌 *Caminhos* = místicos/religiosos\n"
        f"⚙️ *Códigos* = seculares/pragmáticos",
        parse_mode="Markdown"
    )

    keyboard = build_keyboard(FILOSOFIAS, "filos", cols=2)
    await query.message.reply_text("📜 Toque para escolher:", reply_markup=keyboard)


async def callback_filosofia(query, data_key):
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    filos_info = FILOSOFIAS[data_key]

    creation_state.setdefault(user_id, {})
    creation_state[user_id]["filosofia"] = data_key
    creation_state[user_id]["filosofia_nome"] = filos_info[0]

    state = creation_state[user_id]

    await query.edit_message_text(
        f"✅ Filosofia escolhida: *{filos_info[0]}*\n"
        f"⚡ Efeito: {filos_info[1]}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Passo 4 de 4: *Atributos e Finalização*\n\n"
        f"🎲 O Mestre vai rolar seus dados agora...",
        parse_mode="Markdown"
    )

    # Agora sim chama o Gemini para a parte de atributos
    chat = get_chat(chat_id)

    raca_nome = state.get("raca_nome", "?")
    classe_nome = state.get("classe_nome", "?")
    filos_nome = state.get("filosofia_nome", "?")

    prompt = (
        f"MODO CRIAÇÃO (NÃO narre aventura, foque APENAS na ficha):\n"
        f"O jogador está criando um personagem com:\n"
        f"- Raça: {raca_nome}\n"
        f"- Classe: {classe_nome}\n"
        f"- Filosofia: {filos_nome}\n\n"
        f"Comece pelo PASSO 4 — ROLAGEM DE ATRIBUTOS:\n"
        f"a) Role 2d8 SETE vezes (cada dado 1-8, some os dois). Mostre os 7 resultados.\n"
        f"b) Descarte o menor.\n"
        f"c) Mostre os 6 restantes ordenados.\n"
        f"d) Lembre os modificadores raciais desta raça.\n"
        f"e) Peça ao jogador para distribuir entre For, Des, Con, Int, Sab, Car.\n\n"
        f"PARE AQUI. NÃO calcule PV, CD, RAM, perícias ou equipamento ainda.\n"
        f"Espere o jogador responder com a distribuição."
    )

    text = await send_to_gemini(chat, prompt, telegram_msg=query.message)
    await reply_safe(query.message, text)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador de callbacks dos botões inline."""
    query = update.callback_query
    await query.answer()

    data = query.data  # ex: "raca:mercusys"
    prefix, key = data.split(":", 1)

    if prefix == "raca":
        await callback_raca(query, key)
    elif prefix == "classe":
        await callback_classe(query, key)
    elif prefix == "filos":
        await callback_filosofia(query, key)


# ══════════════════════════════════════════════════════════
# HANDLERS BÁSICOS
# ══════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Nova Aventura", callback_data="menu:novojogo"),
         InlineKeyboardButton("🧑‍🚀 Criar Personagem", callback_data="menu:criar")],
        [InlineKeyboardButton("📂 Carregar Ficha", callback_data="menu:carregar"),
         InlineKeyboardButton("📚 Carregar Sessão", callback_data="menu:sessoes")],
        [InlineKeyboardButton("❓ Ajuda", callback_data="menu:ajuda")],
    ])
    await update.message.reply_text(
        "🌌 *PASSAGEM SOMBRIA — RPG ESPACIAL* 🌌\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Bem-vindo ao vácuo, viajante.\n"
        "Eu sou o Mestre. O que deseja?\n\n"
        "_O silêncio das estrelas te observa..._",
        reply_markup=kb, parse_mode="Markdown"
    )


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("menu:"):
        return

    action = data.split(":", 1)[1]
    msg = query.message

    if action == "novojogo":
        chat_id = msg.chat_id
        chat_sessions.pop(chat_id, None)
        chat = get_chat(chat_id)
        await msg.reply_text("🌌 _Preparando a aventura..._", parse_mode="Markdown")
        text = await send_to_gemini(chat,
            "O jogador quer começar uma nova aventura. "
            "Apresente uma cena de abertura épica. "
            "Dê opções de onde começar. Seja conciso e use emojis temáticos.",
            telegram_msg=msg)
        await reply_safe(msg, text)

    elif action == "criar":
        user_id = query.from_user.id
        creation_state[user_id] = {}
        text = (
            "🧑‍🚀 *CRIAÇÃO DE PERSONAGEM*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 Passo 1 de 4: Escolha sua *Raça*\n\n"
            "Cada raça tem habilidades únicas:"
        )
        keyboard = build_keyboard(RACAS, "raca", cols=2)
        await msg.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

    elif action == "carregar":
        user_id = query.from_user.id
        chat_id = msg.chat_id
        ficha = load_ficha(user_id, chat_id)
        if not ficha:
            await msg.reply_text("❌ Nenhuma ficha salva. Use /criarpersonagem")
        else:
            chat = get_chat(chat_id)
            user_name = query.from_user.first_name or "Viajante"
            inject = (
                f"CARREGAR_FICHA: {user_name} carregou:\n"
                f"{json.dumps(ficha, ensure_ascii=False, indent=2)}\n"
                f"Use como ficha oficial. Confirme brevemente."
            )
            text = await send_to_gemini(chat, inject, telegram_msg=msg)
            await reply_safe(msg, format_ficha(ficha))
            await reply_safe(msg, text)

    elif action == "sessoes":
        chat_id = msg.chat_id
        sessoes = load_session_logs(chat_id)
        if not sessoes:
            await msg.reply_text("📚 Nenhuma sessão salva. Jogue e use /salvarsessao")
        else:
            lines = ["📚 *SESSÕES SALVAS:*\n"]
            for s in sessoes:
                d = s.get("created_at", "")[:10]
                lines.append(f"• ID *{s['id']}* — {s.get('title', '?')} ({d})")
            lines.append("\nUse /cargarsessao ID")
            await reply_safe(msg, "\n".join(lines))

    elif action == "ajuda":
        await cmd_help_text(msg)


async def cmd_help_text(msg):
    await reply_safe(msg,
        "📖 *COMANDOS:*\n\n"
        "*⚔️ Jogo:*\n"
        "/novojogo — Nova aventura\n"
        "/criarpersonagem — Criar personagem\n"
        "/rolar 1d20 — Rolar dados\n"
        "/regras /racas /classes\n\n"
        "*💾 Ficha:*\n"
        "/salvar /carregar /ficha /fichas\n"
        "/levelup — Subir de nível\n"
        "/deletarficha — Deletar sua ficha\n"
        "💡 _Fichas salvam automaticamente ao criar!_\n\n"
        "*📚 Sessões:*\n"
        "/salvarsessao — Salvar progresso\n"
        "/sessoes — Listar sessões\n"
        "/cargarsessao ID — Retomar\n"
        "/contexto — Importar de fora\n\n"
        "/reset — Limpar sessão\n"
        "/ajuda — Esta mensagem"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_help_text(update.message)


async def cmd_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)
    await update.message.reply_text("🌌 _Preparando..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        "O jogador quer começar uma aventura nova. Cena de abertura épica com emojis. Conciso.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("🎲 Use: /rolar NdN"); return
    dice_str = args[0].lower()
    try:
        n, s = dice_str.split("d"); n = int(n) if n else 1; s = int(s)
        if n < 1 or n > 20 or s < 1 or s > 100: raise ValueError
    except:
        await update.message.reply_text("❌ Formato inválido"); return
    rolls = [rng.randint(1, s) for _ in range(n)]
    total = sum(rolls)
    crit = ""
    if s == 20 and n == 1:
        if rolls[0] == 20: crit = "\n\n🌟 *ACERTO CRÍTICO! O cosmos sorriu!*"
        elif rolls[0] == 1: crit = "\n\n💀 *FALHA CRÍTICA! O vácuo ri de você...*"
    await reply_safe(update.message, f"🎲 *{dice_str.upper()}*\nDados: {rolls}\n*Total: {total}*{crit}")


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_safe(update.message,
        "📖 *REGRAS RÁPIDAS*\n━━━━━━━━━━━━━━━━━━━━\n"
        "🎲 Teste: 1d20 + Atributo + Perícia ≥ CD\n"
        "⚔️ Melee: dado + Força | 🔫 Ranged: dado + Destreza\n"
        "🛡️ Defesa: 10 + Des + Armadura\n\n"
        "💥 20 nat = Crítico | 💀 1 nat = Falha\n"
        "❤️ 0 PV = Testes de Morte (3 sucessos/falhas)\n"
        "🔋 Pentes: 3 turnos | 🧠 RAM: 1 + Int + ½Tecno")


async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🌌 *RAÇAS JOGÁVEIS:*\n━━━━━━━━━━━━━━━━━━━━\n"]
    for k, v in RACAS.items():
        lines.append(f"{v[0]} — 🌍 {v[1]}\n  _{v[2]}_\n")
    await reply_safe(update.message, "\n".join(lines))


async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["⚔️ *CLASSES DISPONÍVEIS:*\n━━━━━━━━━━━━━━━━━━━━\n"]
    for k, v in CLASSES.items():
        lines.append(f"{v[0]} ({v[1]}) — _{v[2]}_")
    await reply_safe(update.message, "\n".join(lines))


# ══════════════════════════════════════════════════════════
# FICHA: SALVAR / CARREGAR / VER / LEVELUP
# ══════════════════════════════════════════════════════════

async def cmd_salvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"
    chat = get_chat(chat_id)
    await update.message.reply_text(
        "💾 _Exportando ficha... aguarde alguns segundos._", parse_mode="Markdown")
    await asyncio.sleep(5)  # Pequeno delay para evitar rate limit
    raw = await send_to_gemini(chat,
        "EXPORT_FICHA: Exporte a ficha do jogador atual em JSON puro. "
        "Sem markdown, sem texto extra. Se não tem personagem: NO_CHARACTER",
        retries=3, telegram_msg=update.message)
    if "NO_CHARACTER" in raw or "⚠️" in raw:
        await update.message.reply_text(
            "❌ Sem personagem ou API indisponível. Aguarde 1 minuto e tente de novo.")
        return
    ficha = parse_json_response(raw)
    if not ficha:
        await update.message.reply_text("⚠️ Erro ao extrair. Aguarde 1 minuto e tente /salvar de novo.")
        return
    if save_ficha(user_id, user_name, chat_id, ficha):
        await update.message.reply_text(f"✅ *{ficha.get('nome','?')}* salvo!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Erro ao salvar.")


async def cmd_carregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"
    ficha = load_ficha(user_id, chat_id)
    if not ficha:
        await update.message.reply_text("❌ Sem ficha. Use /criarpersonagem + /salvar"); return
    chat = get_chat(chat_id)
    text = await send_to_gemini(chat,
        f"CARREGAR_FICHA: {user_name} carregou:\n{json.dumps(ficha, ensure_ascii=False, indent=2)}\n"
        f"Use como ficha oficial. Confirme brevemente com emojis.",
        telegram_msg=update.message)
    await reply_safe(update.message, format_ficha(ficha))
    await reply_safe(update.message, text)


async def cmd_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    ficha = load_ficha(update.message.from_user.id, update.effective_chat.id)
    if not ficha: await update.message.reply_text("❌ Sem ficha salva. Use /salvar"); return
    await reply_safe(update.message, format_ficha(ficha))


async def cmd_fichas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    fichas = list_fichas(update.effective_chat.id)
    if not fichas: await update.message.reply_text("📋 Nenhuma ficha neste chat."); return
    lines = ["📋 *FICHAS DESTE CHAT:*\n"]
    for f in fichas:
        lines.append(f"• *{f.get('character_name', '?')}* — {f.get('user_name', '?')}")
    await reply_safe(update.message, "\n".join(lines))


async def cmd_deletar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deleta a ficha. Só o próprio dono ou o Admin podem deletar."""
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    is_admin = ADMIN_ID and str(user_id) == str(ADMIN_ID)

    # Se admin, pode deletar a de qualquer um (passa o user_id como argumento)
    args = context.args
    target_id = user_id  # default: deleta a própria

    if args and is_admin:
        # Admin pode passar o user_id de outro jogador
        # Mas também pode passar o nome — vamos buscar pelo nome
        target_name = " ".join(args)
        fichas = list_fichas(chat_id)
        found = None
        for f in fichas:
            if target_name.lower() in f.get("character_name", "").lower() or \
               target_name.lower() in f.get("user_name", "").lower():
                found = f
                break
        if found:
            target_id = int(found.get("user_id", user_id))
        else:
            await update.message.reply_text(
                f"❌ Personagem/jogador '{target_name}' não encontrado.\n"
                f"Use /fichas para ver os nomes.")
            return
    elif args and not is_admin:
        await update.message.reply_text("❌ Só o Admin pode deletar fichas de outros jogadores.")
        return

    # Verifica se a ficha existe
    ficha = load_ficha(target_id, chat_id)
    if not ficha:
        await update.message.reply_text("❌ Nenhuma ficha encontrada para deletar.")
        return

    nome = ficha.get("nome", "?")

    # Confirma e deleta
    if delete_ficha(target_id, chat_id):
        if target_id == user_id:
            await update.message.reply_text(f"🗑️ Ficha de *{nome}* deletada.", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"🗑️ Admin deletou a ficha de *{nome}*.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Erro ao deletar.")


async def cmd_levelup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Viajante"
    ficha = load_ficha(user_id, chat_id)
    if not ficha: await update.message.reply_text("❌ Sem ficha. Use /salvar primeiro."); return

    nv = ficha.get("nivel", 1)
    xp = ficha.get("xp", 0)
    nome = ficha.get("nome", "?")

    # Nível máximo
    if nv >= 10:
        await update.message.reply_text("🌟 Nível máximo (10) atingido!"); return

    # Verifica XP necessário
    xp_necessario = XP_TABLE.get(nv, 9999)
    if xp < xp_necessario:
        falta = xp_necessario - xp
        await update.message.reply_text(
            f"❌ *{nome}* ainda não tem XP suficiente.\n\n"
            f"📊 Nível atual: {nv}\n"
            f"✨ XP atual: {xp} / {xp_necessario}\n"
            f"⏳ Faltam: *{falta} XP*\n\n"
            f"Continue jogando para ganhar XP em combates e decisões!",
            parse_mode="Markdown"
        )
        return

    # Verifica se está em descanso longo (pergunta ao Gemini)
    chat = get_chat(chat_id)
    check_prompt = (
        "O jogador quer fazer level up. Verifique: o grupo está ATUALMENTE em um "
        "Descanso Longo ou acabou de completar um? Responda APENAS 'SIM' ou 'NAO'. "
        "Se não tem certeza ou não houve descanso longo recente, responda 'NAO'."
    )
    rest_check = await send_to_gemini(chat, check_prompt, telegram_msg=update.message)

    if "NAO" in rest_check.upper() or "NÃO" in rest_check.upper():
        await update.message.reply_text(
            f"🛏️ *{nome}* precisa de um Descanso Longo para subir de nível!\n\n"
            f"Encontre um local seguro (nave, estalagem, base) e descanse 8 horas.\n"
            f"Viagens de dobra também contam como descanso longo.\n\n"
            f"✨ XP: {xp}/{xp_necessario} — Pronto para subir quando descansar!",
            parse_mode="Markdown"
        )
        return

    # Tudo OK — faz o level up
    await update.message.reply_text(
        f"⬆️ _Subindo {nome} para Nível {nv+1}..._", parse_mode="Markdown")

    prompt = (
        f"MODO CRIAÇÃO — LEVELUP do personagem:\n"
        f"Ficha atual:\n{json.dumps(ficha, ensure_ascii=False, indent=2)}\n\n"
        f"O jogador tem {xp} XP (precisava de {xp_necessario}) e está em Descanso Longo.\n"
        f"Aplique level up de {nv} → {nv+1}:\n"
        f"1. 🎲 Role dado de vida da raça + Con → some ao PV máximo\n"
        f"2. 💪 O jogador ganha +1 ponto de atributo — PERGUNTE onde quer\n"
        f"3. 🎯 Ganha +1 ponto de perícia — PERGUNTE onde quer\n"
        f"4. 🧠 Se nível {nv+1} é ímpar, ganha +1 RAM\n"
        f"5. ❤️ PV atual = novo PV máximo (cura completa no descanso)\n\n"
        f"Narre o level up de forma épica. "
        f"PERGUNTE onde colocar atributo e perícia. "
        f"NÃO inicie aventura — foque só na progressão."
    )
    text = await send_to_gemini(chat, prompt, telegram_msg=update.message)
    await reply_safe(update.message, text)

    # Salva nível incrementado (atributos finalizados quando jogador responder + /salvar)
    ficha["nivel"] = nv + 1
    save_ficha(user_id, user_name, chat_id, ficha)


# ══════════════════════════════════════════════════════════
# SESSÕES: SALVAR / LISTAR / CARREGAR / IMPORTAR
# ══════════════════════════════════════════════════════════

async def cmd_salvar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    chat_id = update.effective_chat.id
    chat = get_chat(chat_id)
    if chat_id not in chat_sessions or not chat_sessions[chat_id].history:
        await update.message.reply_text("❌ Sem sessão ativa."); return
    await update.message.reply_text("📝 _Resumindo sessão..._", parse_mode="Markdown")
    summary = await send_to_gemini(chat,
        "RESUMO_SESSAO: Resuma TUDO desta sessão — jogadores, personagens, local, "
        "eventos, combates, itens, NPCs, ganchos pendentes, onde parou. "
        "Factual e detalhado. Máximo 1000 palavras.",
        telegram_msg=update.message)
    title = await send_to_gemini(chat,
        "Título CURTO (máx 6 palavras) para esta sessão. Só o título, sem aspas.")
    title = title.strip().strip('"').strip("'")[:60]
    if save_session_log(chat_id, title, summary):
        await update.message.reply_text(f"✅ Sessão salva: *{title}*\nUse /sessoes para ver.", parse_mode="Markdown")
        await reply_safe(update.message, f"📝 *Resumo:*\n\n{summary}")
    else:
        await update.message.reply_text("❌ Erro ao salvar.")


async def cmd_listar_sessoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    sessoes = load_session_logs(update.effective_chat.id)
    if not sessoes: await update.message.reply_text("📚 Nenhuma sessão salva."); return
    lines = ["📚 *SESSÕES SALVAS:*\n"]
    for s in sessoes:
        lines.append(f"• ID *{s['id']}* — {s.get('title','?')} ({s.get('created_at','')[:10]})")
    lines.append("\n/cargarsessao ID para retomar")
    await reply_safe(update.message, "\n".join(lines))


async def cmd_carregar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db: await update.message.reply_text("⚠️ Banco não configurado."); return
    args = context.args
    if not args: await update.message.reply_text("❌ Use: /cargarsessao ID"); return
    try: sid = int(args[0])
    except: await update.message.reply_text("❌ ID inválido."); return
    sessao = load_session_by_id(sid)
    if not sessao: await update.message.reply_text("❌ Sessão não encontrada."); return
    chat_id = update.effective_chat.id
    if sessao.get("chat_id") != str(chat_id):
        await update.message.reply_text("❌ Esta sessão pertence a outro chat."); return
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)
    await update.message.reply_text(f"📂 _Carregando: {sessao.get('title','?')}..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        f"CONTEXTO_SESSAO: Retomando sessão anterior.\n"
        f"Título: {sessao.get('title','?')}\n\n"
        f"RESUMO:\n{sessao.get('summary','')}\n\n"
        f"Recapitule brevemente com emojis e pergunte o que querem fazer.",
        telegram_msg=update.message)
    await reply_safe(update.message, text)


async def cmd_contexto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ctx = update.message.text.replace("/contexto", "", 1).strip()
    if not ctx:
        await update.message.reply_text(
            "📎 *IMPORTAR CONTEXTO*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "Cole o resumo junto com o comando:\n\n"
            "`/contexto Estávamos em Marte. Kira é Ven'y Assassina nv3. "
            "Encontramos um Monólito ativado...`\n\n"
            "Quanto mais detalhe, melhor!", parse_mode="Markdown")
        return
    chat_sessions.pop(chat_id, None)
    chat = get_chat(chat_id)
    await update.message.reply_text("📎 _Absorvendo contexto..._", parse_mode="Markdown")
    text = await send_to_gemini(chat,
        f"CONTEXTO_SESSAO: Sessão importada de fora do bot.\n\n{ctx}\n\n"
        f"Confirme que entendeu: personagens, local, situação. "
        f"Recapitule e pergunte se está correto. Use emojis.",
        telegram_msg=update.message)
    if db: save_session_log(chat_id, "📎 Sessão Importada", ctx)
    await reply_safe(update.message, text)


# ══════════════════════════════════════════════════════════
# RESET E MENSAGENS
# ══════════════════════════════════════════════════════════

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_sessions.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "🔄 Sessão resetada!\n💾 Fichas e sessões salvas permanecem no banco.\n"
        "Use /carregar ou /cargarsessao para retomar.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    user_name = update.message.from_user.first_name or "Viajante"
    user_id = update.message.from_user.id
    if not user_msg: return
    chat = get_chat(chat_id)
    try:
        text = await send_to_gemini(chat, f"[Jogador: {user_name}]: {user_msg}", telegram_msg=update.message)
        trim_history(chat_id)

        # Detecta auto-save de ficha completa
        if "[FICHA_COMPLETA]" in text:
            text = text.replace("[FICHA_COMPLETA]", "").strip()
            await reply_safe(update.message, text)

            # Tenta exportar e salvar automaticamente (com delay para evitar rate limit)
            if db:
                await update.message.reply_text(
                    "💾 _Salvando ficha... aguarde 15s para evitar limite da API._",
                    parse_mode="Markdown")
                await asyncio.sleep(15)  # Espera rate limit resetar

                raw = await send_to_gemini(chat,
                    "EXPORT_FICHA: Exporte a ficha completa em JSON puro. Sem markdown, sem texto extra.",
                    retries=2, telegram_msg=None)  # Menos retries, sem spam
                ficha = parse_json_response(raw)
                if ficha and save_ficha(user_id, user_name, chat_id, ficha):
                    await update.message.reply_text(
                        f"✅ Ficha de *{ficha.get('nome', '?')}* salva!\n"
                        f"Use /ficha para ver a qualquer momento.",
                        parse_mode="Markdown")
                else:
                    await update.message.reply_text(
                        "⚠️ Auto-save falhou. Aguarde 1 minuto e use /salvar.")
        else:
            await reply_safe(update.message, text)
    except Exception as e:
        logger.error(f"Erro: {e}")
        await update.message.reply_text("⚠️ Erro. Tente novamente!")


async def error_handler(update, context):
    logger.error(f"Erro: {context.error}")


# ══════════════════════════════════════════════════════════
# CALLBACK ROUTER
# ══════════════════════════════════════════════════════════

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteia todos os callbacks de botões inline."""
    query = update.callback_query
    data = query.data

    if data.startswith("menu:"):
        await handle_menu_callback(update, context)
    elif data.startswith(("raca:", "classe:", "filos:")):
        await handle_callback(update, context)


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

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
    app.add_handler(CommandHandler("salvar", cmd_salvar))
    app.add_handler(CommandHandler("carregar", cmd_carregar))
    app.add_handler(CommandHandler("ficha", cmd_ficha))
    app.add_handler(CommandHandler("fichas", cmd_fichas))
    app.add_handler(CommandHandler("deletarficha", cmd_deletar_ficha))
    app.add_handler(CommandHandler("levelup", cmd_levelup))
    app.add_handler(CommandHandler("salvarsessao", cmd_salvar_sessao))
    app.add_handler(CommandHandler("sessoes", cmd_listar_sessoes))
    app.add_handler(CommandHandler("cargarsessao", cmd_carregar_sessao))
    app.add_handler(CommandHandler("contexto", cmd_contexto))
    app.add_handler(CommandHandler("reset", cmd_reset))

    # Botões inline (um único handler roteia tudo)
    app.add_handler(CallbackQueryHandler(callback_router))

    # Mensagens livres
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    if WEBHOOK_URL:
        logger.info(f"🚀 Webhook: {WEBHOOK_URL}")
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=TELEGRAM_TOKEN,
                        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")
    else:
        logger.info("🚀 Polling (local)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
