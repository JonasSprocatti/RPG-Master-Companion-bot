"""
📦 Data Loader v3.0 — Supabase → memória → fallback Python
Carrega uma vez no startup, cacheia em variáveis globais.
"""
import os, json, logging
from supabase import create_client
from glossary import (RACAS_STATS as _FB_R, CLASSES_STATS as _FB_C, FILOS_STATS as _FB_F,
    TECNO_SCRIPTS as _FB_T, IMPLANTES_DATA as _FB_I,
    get_available_scripts, calc_max_scripts, calc_implant_limit)

log = logging.getLogger(__name__)

# Dados mecânicos (populados no startup)
RACAS_STATS = {}; CLASSES_STATS = {}; FILOS_STATS = {}
TECNO_SCRIPTS = {}; IMPLANTES_DATA = {}

# Textos de display do glossário (populados do DB)
DISPLAY = {}  # chave → texto (ex: "display_racas" → {"mercusys":"texto..."})
REGRAS_TEXT = ""  # Texto de /regras do banco

_loaded = False

def load_from_db():
    global RACAS_STATS,CLASSES_STATS,FILOS_STATS,TECNO_SCRIPTS,IMPLANTES_DATA,DISPLAY,REGRAS_TEXT,_loaded
    su=os.environ.get("SUPABASE_URL",""); sk=os.environ.get("SUPABASE_KEY","")
    if not su or not sk: return False
    try:
        db=create_client(su,sk)
        r=db.table("dados_rpg").select("chave,dados").execute()
        if not r.data: return False
        lk={row["chave"]:(row["dados"] if isinstance(row["dados"],dict) else json.loads(row["dados"])) for row in r.data if row.get("dados")}
        if "racas_stats" in lk: RACAS_STATS.update(lk["racas_stats"])
        if "classes_stats" in lk: CLASSES_STATS.update(lk["classes_stats"])
        if "filosofias_stats" in lk:
            for k,v in lk["filosofias_stats"].items(): FILOS_STATS[k]=tuple(v) if isinstance(v,list) else v
        if "tecnomancias" in lk: TECNO_SCRIPTS.update(lk["tecnomancias"])
        if "implantes_data" in lk: IMPLANTES_DATA.update(lk["implantes_data"])
        # Textos de display
        for key in["display_racas","display_classes","display_armas_brancas","display_armas_fogo",
                    "display_armaduras","display_ferramentas","display_implantes","display_naves",
                    "display_modificacoes","display_filosofias","display_tecno_basicas",
                    "display_tecno_injecoes","display_tecno_protocolos",
                    "display_bestiario_planetas","display_bestiario_fauna","display_bestiario_vazio"]:
            if key in lk: DISPLAY[key]=lk[key]
        if "regras" in lk: REGRAS_TEXT=lk["regras"] if isinstance(lk["regras"],str) else json.dumps(lk["regras"])
        _loaded=True
        log.info(f"✅ Dados RPG: {len(lk)} categorias do Supabase")
        return True
    except Exception as e:
        log.warning(f"⚠️ DB falhou: {e}"); return False

def load_fallback():
    global RACAS_STATS,CLASSES_STATS,FILOS_STATS,TECNO_SCRIPTS,IMPLANTES_DATA,_loaded
    RACAS_STATS.update(_FB_R); CLASSES_STATS.update(_FB_C); FILOS_STATS.update(_FB_F)
    TECNO_SCRIPTS.update(_FB_T); IMPLANTES_DATA.update(_FB_I)
    _loaded=True; log.info("📁 Dados RPG: fallback local")

def ensure_loaded():
    global _loaded
    if _loaded: return
    if not load_from_db(): load_fallback()

def get_display(key, fallback="❌ Dados não encontrados."):
    """Busca texto de display do glossário."""
    ensure_loaded()
    return DISPLAY.get(key, fallback)
