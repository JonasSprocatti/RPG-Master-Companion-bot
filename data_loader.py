"""
📦 Data Loader v3.1 — Fallback Inteligente
Carrega a base do glossary.py PRIMEIRO, e depois sobrepõe com os dados do Supabase.
"""
import os, json, logging
from supabase import create_client
from glossary import (RACAS_STATS as _FB_R, CLASSES_STATS as _FB_C, FILOS_STATS as _FB_F,
    TECNO_SCRIPTS as _FB_T, IMPLANTES_DATA as _FB_I,
    get_available_scripts, calc_max_scripts, calc_implant_limit)

log = logging.getLogger(__name__)

# 1. Carrega SEMPRE o Fallback (Local) PRIMEIRO para a memória nunca ficar vazia!
RACAS_STATS = _FB_R.copy()
CLASSES_STATS = _FB_C.copy()
FILOS_STATS = _FB_F.copy()
TECNO_SCRIPTS = _FB_T.copy()
IMPLANTES_DATA = _FB_I.copy()

# Textos de display do glossário
DISPLAY = {}  
REGRAS_TEXT = ""  

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
        
        # 2. Atualiza apenas as categorias que de fato existirem no Banco de Dados
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
        log.info(f"✅ Dados RPG: {len(lk)} categorias sobrepostas com sucesso do Supabase")
        return True
    except Exception as e:
        log.warning(f"⚠️ DB falhou: {e}"); return False

def load_fallback():
    global _loaded
    # As variáveis já foram preenchidas no topo do arquivo, só marcamos como loaded.
    _loaded=True; log.info("📁 Dados RPG: usando apenas fallback local")

def ensure_loaded():
    global _loaded
    if _loaded: return
    if not load_from_db(): load_fallback()

def get_display(key, fallback="❌ Dados não encontrados."):
    """Busca texto de display do glossário."""
    ensure_loaded()
    return DISPLAY.get(key, fallback)
