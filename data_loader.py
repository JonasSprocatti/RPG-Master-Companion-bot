"""
📦 Carregador de dados RPG — Supabase → memória
Carrega tudo uma vez no startup, cacheia em variáveis globais.
Se o banco falhar, usa os dados dos arquivos Python como fallback.
"""
import os, json, logging
from supabase import create_client

log = logging.getLogger(__name__)

# Fallback imports (arquivos Python locais)
from glossary import (
    RACAS_STATS as _FB_RACAS, CLASSES_STATS as _FB_CLASSES, FILOS_STATS as _FB_FILOS,
    RACAS_DETAIL as _FB_RACAS_DETAIL, CLASSES_DETAIL as _FB_CLASSES_DETAIL,
    RACAS_BTN as _FB_RACAS_BTN, CLASSES_BTN as _FB_CLASSES_BTN, FILOS_BTN as _FB_FILOS_BTN,
    ATTR_KEYS, ATTR_LABELS, ATTR_SHORT, PERICIAS_ATTR, PERICIAS_NOMES, calc_mod,
    ARMAS_BRANCAS_TEXT, ARMAS_FOGO_TEXT, ARMADURAS_TEXT, FERRAMENTAS_TEXT,
    IMPLANTES_TEXT, NAVES_TEXT, MODIFICACOES_TEXT, FILOSOFIAS_TEXT,
    TECNO_BASICAS, TECNO_INJECOES, TECNO_PROTOCOLOS,
    BESTIARIO_PLANETAS, BESTIARIO_FAUNA, BESTIARIO_VAZIO,
)
from glossary_additions import (
    TECNO_SCRIPTS as _FB_TECNO, IMPLANTES_DATA as _FB_IMPL,
    get_available_scripts as _fb_get_scripts, calc_max_scripts as _fb_calc_max,
    calc_implant_limit as _fb_calc_impl_limit,
)

# ══════ Variáveis globais (populadas no startup) ══════

RACAS_STATS = {}
CLASSES_STATS = {}
FILOS_STATS = {}
TECNO_SCRIPTS = {}
IMPLANTES_DATA = {}
RACAS_DETAIL = {}
CLASSES_DETAIL = {}

_loaded = False

def load_from_db():
    """Carrega dados_rpg do Supabase. Retorna True se sucesso."""
    global RACAS_STATS, CLASSES_STATS, FILOS_STATS, TECNO_SCRIPTS, IMPLANTES_DATA
    global RACAS_DETAIL, CLASSES_DETAIL, _loaded

    su = os.environ.get("SUPABASE_URL", "")
    sk = os.environ.get("SUPABASE_KEY", "")
    if not su or not sk:
        return False

    try:
        db = create_client(su, sk)
        r = db.table("dados_rpg").select("chave,dados").execute()
        if not r.data:
            return False

        lookup = {row["chave"]: row["dados"] for row in r.data}

        if "racas_stats" in lookup:
            raw = lookup["racas_stats"]
            RACAS_STATS.update(raw if isinstance(raw, dict) else json.loads(raw))
        if "classes_stats" in lookup:
            raw = lookup["classes_stats"]
            CLASSES_STATS.update(raw if isinstance(raw, dict) else json.loads(raw))
        if "filosofias_stats" in lookup:
            raw = lookup["filosofias_stats"]
            # Converte listas [nome, desc] de volta para tuplas
            parsed = raw if isinstance(raw, dict) else json.loads(raw)
            for k, v in parsed.items():
                FILOS_STATS[k] = tuple(v) if isinstance(v, list) else v
        if "tecnomancias" in lookup:
            raw = lookup["tecnomancias"]
            TECNO_SCRIPTS.update(raw if isinstance(raw, dict) else json.loads(raw))
        if "implantes_data" in lookup:
            raw = lookup["implantes_data"]
            IMPLANTES_DATA.update(raw if isinstance(raw, dict) else json.loads(raw))
        if "display_racas" in lookup:
            raw = lookup["display_racas"]
            RACAS_DETAIL.update(raw if isinstance(raw, dict) else json.loads(raw))
        if "display_classes" in lookup:
            raw = lookup["display_classes"]
            CLASSES_DETAIL.update(raw if isinstance(raw, dict) else json.loads(raw))

        _loaded = True
        log.info(f"✅ Dados RPG carregados do Supabase ({len(lookup)} categorias)")
        return True

    except Exception as e:
        log.warning(f"⚠️ Falha ao carregar dados do Supabase: {e}")
        return False

def load_fallback():
    """Carrega dos arquivos Python locais como fallback."""
    global RACAS_STATS, CLASSES_STATS, FILOS_STATS, TECNO_SCRIPTS, IMPLANTES_DATA
    global RACAS_DETAIL, CLASSES_DETAIL, _loaded

    RACAS_STATS.update(_FB_RACAS)
    CLASSES_STATS.update(_FB_CLASSES)
    FILOS_STATS.update(_FB_FILOS)
    TECNO_SCRIPTS.update(_FB_TECNO)
    IMPLANTES_DATA.update(_FB_IMPL)
    RACAS_DETAIL.update(_FB_RACAS_DETAIL)
    CLASSES_DETAIL.update(_FB_CLASSES_DETAIL)
    _loaded = True
    log.info("📁 Dados RPG carregados dos arquivos locais (fallback)")

def ensure_loaded():
    """Garante que os dados estão carregados. Chame no startup do bot."""
    global _loaded
    if _loaded:
        return
    if not load_from_db():
        load_fallback()

# ══════ Funções utilitárias (mesmas de glossary_additions) ══════

def get_available_scripts(tecno_skill):
    ensure_loaded()
    available = {}
    for k, v in TECNO_SCRIPTS.items():
        if v["tier"] == "basica" and tecno_skill >= 1: available[k] = v
        elif v["tier"] == "injecao" and tecno_skill >= 3: available[k] = v
        elif v["tier"] == "protocolo" and tecno_skill >= 5: available[k] = v
    return available

def calc_max_scripts(nivel, tecno_skill):
    return max(nivel + tecno_skill, 3)

def calc_implant_limit(con_mod):
    return max(2 + con_mod, 1)
