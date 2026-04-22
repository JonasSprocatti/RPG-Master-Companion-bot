"""
📦 Glossário Estrutural — Passagem Sombria v3.0
Contém APENAS dados mecânicos para criação/cálculos e labels de botões.
Textos descritivos e lore estão no Supabase (dados_rpg).
"""

# ══════ CONSTANTES DE ATRIBUTOS ══════
ATTR_KEYS = ["forca","destreza","constituicao","inteligencia","sabedoria","carisma"]
ATTR_LABELS = ["💪 Força","⚡ Destreza","🩸 Constituição","🧠 Inteligência","🦉 Sabedoria","🗣️ Carisma"]
ATTR_SHORT = ["For","Des","Con","Int","Sab","Car"]

def calc_mod(val):
    if val<=3: return -3
    if val<=5: return -2
    if val<=7: return -1
    if val<=9: return 0
    if val<=11: return 1
    if val<=13: return 2
    if val<=15: return 3
    return 4

# ══════ PERÍCIAS ══════
PERICIAS_ATTR = {
    "acrobacia":["destreza","forca"],"armas_brancas":["forca","destreza"],"armas_fogo":["destreza"],
    "resistencia":["constituicao"],"espionagem":["inteligencia","carisma"],"furtividade":["destreza"],
    "investigacao":["inteligencia","sabedoria"],"sobrevivencia":["sabedoria"],"conhecimentos":["inteligencia"],
    "explosivos":["inteligencia"],"mecanica":["inteligencia","destreza"],"medicina":["inteligencia"],
    "pilotagem":["destreza","inteligencia"],"tecnomancia":["inteligencia"],"intimidacao":["carisma","forca"],
    "lideranca":["carisma"],"performance":["carisma"],"persuasao":["carisma"],
}
PERICIAS_NOMES = {
    "acrobacia":"Acrobacia","armas_brancas":"Armas Brancas","armas_fogo":"Armas de Fogo",
    "resistencia":"Resistência","espionagem":"Espionagem","furtividade":"Furtividade",
    "investigacao":"Investigação","sobrevivencia":"Sobrevivência","conhecimentos":"Conhecimentos",
    "explosivos":"Explosivos","mecanica":"Mecânica","medicina":"Medicina",
    "pilotagem":"Pilotagem","tecnomancia":"Tecnomancia","intimidacao":"Intimidação",
    "lideranca":"Liderança","performance":"Performance","persuasao":"Persuasão",
}

# ══════ LABELS DE BOTÕES ══════
RACAS_BTN = {"mercusys":"🔥 Mercusys","veny":"🌿 Ven'y","terraqueo":"🌍 Terráqueo",
    "marciano":"⚔️ Marciano","conjupitero":"⚙️ Conjupitero","sata":"💫 Sata",
    "urak":"❄️ Urak","proturno":"🧠 Proturno","infimor":"🪐 Infimor"}
CLASSES_BTN = {"estudioso":"📚 Estudioso","mecanico":"🔧 Mecânico","assassino":"🗡️ Assassino",
    "soldado":"🎖️ Soldado","starlord":"🌟 Starlord","franco_atirador":"🎯 Franco-At.",
    "musico":"🎵 Músico","espiao":"🕵️ Espião","catador":"♻️ Catador",
    "piloto":"✈️ Piloto","batedor":"👁️ Batedor","explorador":"🗺️ Explorador",
    "cinetico":"⚡ Cinético","prospector":"💼 Prospector","pirata":"☠️ Pirata"}
FILOS_BTN = {"cam_voz":"🗣️ Voz","cam_ressonancia":"🌀 Ressonância","cam_engrenagem":"⚙️ Engrenagem",
    "cam_espiral":"🧬 Espiral","cam_anel":"💍 Anel","cam_ocaso":"🌑 Ocaso",
    "cod_sobrevivente":"🏕️ Sobrevivente","cod_corporativo":"💰 Corporativo",
    "cod_cetico":"🧊 Cético","cod_fronteira":"🐺 Fronteira",
    "cod_caserna":"🛡️ Caserna","cod_viralata":"🃏 Vira-Lata"}

# ══════ STATS MECÂNICOS (fallback — fonte principal é o Supabase) ══════
RACAS_STATS = {
    "mercusys":{"nome":"Mercusys","planeta":"Mercúrio","mods":[0,3,0,1,-1,1],"vida_ajuste":-2,"dado_nv":"1d8","desloc":18},
    "veny":{"nome":"Ven'y","planeta":"Vênus","mods":[1,2,1,-1,1,0],"vida_ajuste":-1,"dado_nv":"1d8","desloc":9},
    "terraqueo":{"nome":"Terráqueo","planeta":"Terra","mods":[0,0,0,0,0,0],"vida_ajuste":0,"dado_nv":"1d8","desloc":9,"bonus_attr":4,"bonus_attr_max":2,"bonus_per":3},
    "marciano":{"nome":"Marciano","planeta":"Marte","mods":[3,-1,3,0,-1,0],"vida_ajuste":2,"dado_nv":"1d10","desloc":9},
    "conjupitero":{"nome":"Conjupitero","planeta":"Júpiter","mods":[2,-2,2,2,1,-1],"vida_ajuste":-3,"dado_nv":"1d8","desloc":6,"bonus_per_fixo":{"pilotagem":2,"mecanica":2}},
    "sata":{"nome":"Sata","planeta":"Saturno","mods":[-1,1,0,2,2,0],"vida_ajuste":-1,"dado_nv":"1d6","desloc":9},
    "urak":{"nome":"Urak","planeta":"Urano","mods":[0,-1,2,0,0,3],"vida_ajuste":-1,"dado_nv":"1d8","desloc":9},
    "proturno":{"nome":"Proturno","planeta":"Netuno","mods":[-1,0,-1,2,3,1],"vida_ajuste":-3,"dado_nv":"1d6","desloc":9},
    "infimor":{"nome":"Infimor","planeta":"Plutão","mods":[3,-1,2,0,0,0],"vida_ajuste":3,"dado_nv":"1d10","desloc":6},
}

CLASSES_STATS = {
    "estudioso":{"nome":"Estudioso","pv":4,"pericias":{"conhecimentos":4,"investigacao":3,"mecanica":2,"tecnomancia":2,"persuasao":1},"equip_fixo":["Datapad Pesquisa","Bateria Fantasma","Kit Sobrevivência Base"],"equip_escolha":[["Pistola EMP (1d4 Anti-Sintético)","Pistola Laser (1d6 Saque Rápido)"]],"armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "mecanico":{"nome":"Mecânico","pv":6,"pericias":{"mecanica":5,"pilotagem":2,"armas_brancas":2,"tecnomancia":1,"persuasao":1,"sobrevivencia":1},"equip_fixo":["Garras Combate (1d4)","Ferramentas Mecânicas","Kit Sobrevivência Base"],"equip_escolha":[["Revólver Íons (1d8 Brutal)","Escopeta Sônica (2d6 Curto Alcance)"]],"armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "assassino":{"nome":"Assassino","pv":8,"pericias":{"furtividade":4,"armas_brancas":2,"armas_fogo":2,"espionagem":2,"medicina":1,"persuasao":1},"equip_fixo":["Faca Plasma (1d4 Oculta/Ágil)","Granada Fumaça","Kit Sobrevivência Base"],"equip_escolha":[["Besta Phobos (1d10 Silenciosa)","SubMetra Flechetes (2d4 Sangramento)"]],"armadura":{"nome":"Traje Furtivo Nanofibra","cd":1,"tipo":"leve"}},
    "soldado":{"nome":"Soldado","pv":10,"pericias":{"armas_fogo":4,"armas_brancas":3,"explosivos":2,"pilotagem":1,"sobrevivencia":1,"furtividade":1},"equip_fixo":["Faca Plasma (1d4)","Kit Médico Batalha","Kit Sobrevivência Base"],"equip_escolha":[["Rifle Assalto (1d8 Rajada)","Escopeta Sônica (2d6 Curto Alcance)"]],"armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "starlord":{"nome":"Starlord","pv":8,"pericias":{"persuasao":5,"armas_fogo":2,"tecnomancia":2,"pilotagem":2,"furtividade":1},"equip_fixo":["Pistola Laser (1d6)","Faca Plasma (1d4)","Kit Sobrevivência Base"],"armadura":{"nome":"Roupas Elegantes","cd":0,"tipo":"leve"}},
    "franco_atirador":{"nome":"Franco-Atirador","pv":6,"pericias":{"armas_fogo":5,"sobrevivencia":3,"furtividade":2,"investigacao":2},"equip_fixo":["Rifle Precisão (1d12 Telescópica/Brutal)","Bastão Choque (1d6)","Binóculos Termais","Kit Sobrevivência Base"],"armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "musico":{"nome":"Músico","pv":4,"pericias":{"tecnomancia":5,"performance":4,"persuasao":2,"armas_brancas":1},"equip_fixo":["Pistola Laser (1d6)","Instrumento Musical Digital","Bateria Fantasma","Kit Sobrevivência Base"],"armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "espiao":{"nome":"Espião","pv":4,"pericias":{"espionagem":4,"persuasao":4,"furtividade":2,"acrobacia":1,"intimidacao":1},"equip_fixo":["Pistola Laser (1d6)","Faca Plasma (1d4 Oculta)","2 IDs Falsas","Kit Sobrevivência Base"],"armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "catador":{"nome":"Catador","pv":6,"pericias":{"persuasao":3,"investigacao":2,"sobrevivencia":2,"mecanica":2,"pilotagem":2,"armas_fogo":1},"equip_fixo":["Revólver Íons (1d8)","Bastão Choque (1d6)","Maçarico Laser","Kit Sobrevivência Base"],"armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "piloto":{"nome":"Piloto","pv":6,"pericias":{"pilotagem":5,"mecanica":2,"persuasao":2,"sobrevivencia":2,"armas_fogo":1},"equip_fixo":["Chave Inglesa (1d4)","Kit Sobrevivência Base"],"equip_escolha":[["Revólver Íons (1d8 Brutal)","Escopeta Sônica (2d6 Curto Alcance)"]],"armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "batedor":{"nome":"Batedor","pv":8,"pericias":{"sobrevivencia":4,"armas_fogo":3,"investigacao":3,"furtividade":1,"explosivos":1},"equip_fixo":["SubMetra Flechetes (2d4)","Faca Plasma (1d4)","Granada Fumaça","Kit Sobrevivência Base"],"armadura":{"nome":"Traje Furtivo Nanofibra","cd":1,"tipo":"leve"}},
    "explorador":{"nome":"Explorador","pv":6,"pericias":{"investigacao":4,"sobrevivencia":4,"conhecimentos":3,"persuasao":1},"equip_fixo":["Rifle Assalto (1d8)","Faca Plasma (1d4)","Scanner Ambiental","Corda Nanofibra 15m","Kit Sobrevivência Base"],"armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "cinetico":{"nome":"Cinético","pv":4,"pericias":{"tecnomancia":5,"medicina":3,"resistencia":2,"acrobacia":2},"equip_fixo":["Pistola EMP (1d4)","Deck Pulso","Bateria Fantasma","Kit Médico Batalha","Kit Sobrevivência Base"],"armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "prospector":{"nome":"Prospector","pv":4,"pericias":{"persuasao":5,"lideranca":4,"tecnomancia":3},"equip_fixo":["Pistola Laser (1d6)","Datapad Corporativo","Contratos + Caneta Digital","Kit Sobrevivência Base"],"armadura":{"nome":"Roupas Luxo","cd":0,"tipo":"leve"},"creditos_extra":100},
    "pirata":{"nome":"Pirata","pv":10,"pericias":{"armas_fogo":3,"armas_brancas":3,"intimidacao":3,"sobrevivencia":2,"pilotagem":1},"equip_fixo":["Escopeta Sônica (2d6)","Arpéu Magnético","Granada Fumaça","Kit Sobrevivência Base"],"equip_escolha_melee":[["Bastão Choque (1d6 Atordoante)","Faca Plasma (1d4 Oculta)"]],"armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
}

FILOS_STATS = {
    "cam_voz":("🗣️ Caminho da Voz","1x/DL: desvantagem no teste do alvo (Car) ou finge-se de morto"),
    "cam_ressonancia":("🌀 Caminho da Ressonância","1x/DC: ignora escuridão, sente vivos 10m por 1 turno"),
    "cam_engrenagem":("⚙️ Caminho da Engrenagem","1x/DL: transforma falha crítica em falha comum"),
    "cam_espiral":("🧬 Caminho da Espiral","Toda cura (kit/DC) rola com Vantagem"),
    "cam_anel":("💍 Caminho do Anel","1x/DL: ao chegar a 0PV, fica com 1PV até próximo turno"),
    "cam_ocaso":("🌑 Caminho do Ocaso","1x/combate: sofre 1d4 dano verdadeiro, soma 1d4 em qualquer rolagem"),
    "cod_sobrevivente":("🏕️ Código do Sobrevivente","+2 Iniciativa permanente. 1x/DL age na rodada surpresa"),
    "cod_corporativo":("💰 Código Corporativo","Vantagem em avaliar itens, achar loot oculto, negociar"),
    "cod_cetico":("🧊 Código do Cético","+2CD vs psíquico/controle/intimidação"),
    "cod_fronteira":("🐺 Código da Fronteira","+1 ataque se sem aliado em 5m"),
    "cod_caserna":("🛡️ Código da Caserna","1x/DC: reação leva dano por aliado adjacente"),
    "cod_viralata":("🃏 Código do Vira-Lata","1x/combate: distrai 3m, ataca com vantagem"),
}

# ══════ TECNOMANCIAS (30 scripts) ══════
TECNO_SCRIPTS = {
    "ping":{"nome":"Ping","ram":0,"tier":"basica","desc":"Interage eletrônico 10m"},
    "choque":{"nome":"Choque Estático","ram":0,"tier":"basica","desc":"1d6 elétrico"},
    "query":{"nome":"Query Neural","ram":0,"tier":"basica","desc":"Lê pensamento cibernético"},
    "bateria":{"nome":"Bateria Fantasma","ram":0,"tier":"basica","desc":"Recarrega device 1h"},
    "scanner":{"nome":"Scanner Frequência","ram":0,"tier":"basica","desc":"Emissões 50m"},
    "jammer":{"nome":"Jammer Pessoal","ram":1,"tier":"basica","desc":"Bolha 10m 3t"},
    "glitch":{"nome":"Glitch Visual","ram":1,"tier":"basica","desc":"-2 ataque alvo"},
    "trava":{"nome":"Trava Biométrica","ram":1,"tier":"basica","desc":"Tranca porta DNA"},
    "rollback":{"nome":"Rollback Celular","ram":1,"tier":"basica","desc":"Cura 1d8+Int"},
    "firewall":{"nome":"Firewall Ativo","ram":1,"tier":"basica","desc":"Bloqueia 1d10+Int dano"},
    "travar_arma":{"nome":"Travar Armamento","ram":2,"tier":"injecao","desc":"Trava arma 1t"},
    "curto_arm":{"nome":"Curto em Armadura","ram":2,"tier":"injecao","desc":"-3CD 2t"},
    "hack_motor":{"nome":"Hackear Motor","ram":2,"tier":"injecao","desc":"½ desloc 3t"},
    "ejetar_pente":{"nome":"Ejetar Pente","ram":1,"tier":"injecao","desc":"Força recarga"},
    "cegueira":{"nome":"Cegueira Cibernética","ram":2,"tier":"injecao","desc":"Cego 2t"},
    "drenar":{"nome":"Drenar Escudos","ram":2,"tier":"injecao","desc":"Escudo→PV temp"},
    "sobrecarga":{"nome":"Sobrecarga Sistema","ram":2,"tier":"injecao","desc":"2d6 área"},
    "desativar":{"nome":"Desativar Suporte","ram":2,"tier":"injecao","desc":"Desliga O₂"},
    "loop":{"nome":"Loop Feedback","ram":2,"tier":"injecao","desc":"Anula script"},
    "torreta":{"nome":"Torreta Sentinela","ram":3,"tier":"injecao","desc":"Drone aliado 3t"},
    "hack_nav":{"nome":"Hackear Navegação","ram":3,"tier":"protocolo","desc":"Controla nave 1t"},
    "apagao":{"nome":"Apagão Motor","ram":4,"tier":"protocolo","desc":"Nave à deriva 1t"},
    "inverter":{"nome":"Inverter Propulsores","ram":3,"tier":"protocolo","desc":"3d8 casco"},
    "reator":{"nome":"Sobrecarga Reator","ram":5,"tier":"protocolo","desc":"6d10 explosão"},
    "marionete":{"nome":"Marionete Sintética","ram":4,"tier":"protocolo","desc":"Controla 3t"},
    "emp":{"nome":"EMP Localizado","ram":4,"tier":"protocolo","desc":"Desliga 10m 2t"},
    "ejetar_piloto":{"nome":"Ejetar Piloto","ram":3,"tier":"protocolo","desc":"Ejeta piloto"},
    "reparo_nave":{"nome":"Reparo Estrutural","ram":4,"tier":"protocolo","desc":"4d10 PV nave"},
    "formatar":{"nome":"Formatar Mente","ram":5,"tier":"protocolo","desc":"5d8 psi"},
    "gravidade":{"nome":"Gravidade Zero","ram":4,"tier":"protocolo","desc":"5x5m sem grav"},
}

# ══════ IMPLANTES (15) ══════
IMPLANTES_DATA = {
    "chip_ram":{"nome":"Chip Expansão RAM","preco":1500,"slot":"cabeça","efeito":"+2 RAM","mecanica":{"ram_max":2}},
    "olho":{"nome":"Olho Biônico","preco":800,"slot":"cabeça","efeito":"+2 dist, ignora fumo","mecanica":{}},
    "interface_nav":{"nome":"Interface Navegação","preco":1200,"slot":"cabeça","efeito":"Vantagem evasiva","mecanica":{}},
    "tradutor":{"nome":"Tradutor Universal","preco":600,"slot":"cabeça","efeito":"+2 Persuasão","mecanica":{}},
    "mira":{"nome":"Mira Preditiva","preco":950,"slot":"cabeça","efeito":"Reduz penalidade sniper","mecanica":{}},
    "placas":{"nome":"Placas Subdérmicas","preco":1100,"slot":"torso","efeito":"+1 CD","mecanica":{"cd":1}},
    "coracao":{"nome":"Coração Sintético","preco":2500,"slot":"torso","efeito":"+5 PV máx","mecanica":{"pv_max":5}},
    "filtro":{"nome":"Filtro Pulmonar","preco":750,"slot":"torso","efeito":"Imune gases","mecanica":{}},
    "adrenalina":{"nome":"Reator Adrenalina","preco":3000,"slot":"torso","efeito":"Ação extra 1x/dia","mecanica":{}},
    "bateria_int":{"nome":"Bateria Interna","preco":2000,"slot":"torso","efeito":"PV→RAM","mecanica":{}},
    "braco":{"nome":"Braço Hidráulico","preco":850,"slot":"membros","efeito":"+2 dano melee","mecanica":{}},
    "estabilizador":{"nome":"Estabilizador Pulso","preco":500,"slot":"membros","efeito":"Sem pesada","mecanica":{}},
    "mantis":{"nome":"Lâmina Mantis","preco":1000,"slot":"membros","efeito":"1d8 oculta","mecanica":{}},
    "pernas":{"nome":"Pernas Pneumáticas","preco":1500,"slot":"membros","efeito":"2x desloc","mecanica":{}},
    "ancoras":{"nome":"Âncoras Magnéticas","preco":700,"slot":"membros","efeito":"Imune derrubar","mecanica":{}},
}

# ══════ FUNÇÕES UTILITÁRIAS ══════

def get_available_scripts(tecno_total):
    """Diretriz 1: Tiers de Tecnomancia por proficiência total.
    +1 a +3 → Básicas | +4 a +6 → +Injeções | +7+ → +Protocolos"""
    available = {}
    for k,v in TECNO_SCRIPTS.items():
        if v["tier"]=="basica" and tecno_total>=1: available[k]=v
        elif v["tier"]=="injecao" and tecno_total>=4: available[k]=v
        elif v["tier"]=="protocolo" and tecno_total>=7: available[k]=v
    return available

def calc_max_scripts(nivel,tecno_skill):
    return max(nivel+tecno_skill,3)

def calc_implant_limit(con_mod):
    return max(2+con_mod,1)
