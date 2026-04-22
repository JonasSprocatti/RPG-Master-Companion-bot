
# ══════════════════════════════════════════════════════════
# DADOS ESTRUTURADOS — TECNOMANCIAS (para seleção por botão)
# ══════════════════════════════════════════════════════════

TECNO_SCRIPTS = {
    # ── BÁSICAS (Nv1, Tecnomancia +1/+2) ──
    "ping":         {"nome":"Ping","ram":0,"tier":"basica","acao":"livre","desc":"Interage com eletrônico a 10m (luzes, portas)"},
    "choque":       {"nome":"Choque Estático","ram":0,"tier":"basica","acao":"principal","desc":"1d6 dano elétrico"},
    "query":        {"nome":"Query Neural","ram":0,"tier":"basica","acao":"principal","desc":"Lê último pensamento de cibernético (Int vs alvo)"},
    "bateria":      {"nome":"Bateria Fantasma","ram":0,"tier":"basica","acao":"principal","desc":"Recarrega device por 1h"},
    "scanner":      {"nome":"Scanner Frequência","ram":0,"tier":"basica","acao":"livre","desc":"Vê emissões Wi-Fi/rádio em 50m"},
    "jammer":       {"nome":"Jammer Pessoal","ram":1,"tier":"basica","acao":"movimento","desc":"Bolha 10m sem comunicação 3 turnos"},
    "glitch":       {"nome":"Glitch Visual","ram":1,"tier":"basica","acao":"principal","desc":"-2 próximo ataque do alvo"},
    "trava":        {"nome":"Trava Biométrica","ram":1,"tier":"basica","acao":"movimento","desc":"Tranca porta com seu DNA"},
    "rollback":     {"nome":"Rollback Celular","ram":1,"tier":"basica","acao":"principal","desc":"Cura 1d8+Int PV"},
    "firewall":     {"nome":"Firewall Ativo","ram":1,"tier":"basica","acao":"reação","desc":"Bloqueia 1d10+Int dano"},
    # ── INJEÇÕES MALICIOSAS (Nv2, Tecnomancia +3/+4) ──
    "travar_arma":  {"nome":"Travar Armamento","ram":2,"tier":"injecao","acao":"principal","desc":"Trava arma inimiga 1 turno"},
    "curto_arm":    {"nome":"Curto em Armadura","ram":2,"tier":"injecao","acao":"principal","desc":"-3CD 2 turnos + 1d4 queimadura"},
    "hack_motor":   {"nome":"Hackear Implante Motor","ram":2,"tier":"injecao","acao":"principal","desc":"½ desloc, sem esquivar 3 turnos"},
    "ejetar_pente": {"nome":"Ejetar Pente","ram":1,"tier":"injecao","acao":"reação","desc":"Força recarga do inimigo"},
    "cegueira":     {"nome":"Cegueira Cibernética","ram":2,"tier":"injecao","acao":"principal","desc":"Cego 2 turnos, desvantagem ataques"},
    "drenar":       {"nome":"Drenar Escudos","ram":2,"tier":"injecao","acao":"principal","desc":"Drena escudo → PV temporários próprios"},
    "sobrecarga":   {"nome":"Sobrecarga Sistema","ram":2,"tier":"injecao","acao":"principal","desc":"2d6 elétrico área 3x3m"},
    "desativar":    {"nome":"Desativar Suporte Vida","ram":2,"tier":"injecao","acao":"principal","desc":"Desliga O₂/aquecimento do traje"},
    "loop":         {"nome":"Loop de Feedback","ram":2,"tier":"injecao","acao":"reação","desc":"Anula script inimigo, gasta RAM dele"},
    "torreta":      {"nome":"Torreta Sentinela","ram":3,"tier":"injecao","acao":"principal","desc":"Drone/torreta vira aliado 3 turnos"},
    # ── PROTOCOLOS SOBRESCRITA (Nv3, Tecnomancia +5+) ──
    "hack_nav":     {"nome":"Hackear Navegação","ram":3,"tier":"protocolo","acao":"principal","desc":"Controla nave inimiga 1 turno"},
    "apagao":       {"nome":"Apagão do Motor","ram":4,"tier":"protocolo","acao":"principal","desc":"Desliga motor, nave à deriva 1 turno"},
    "inverter":     {"nome":"Inverter Propulsores","ram":3,"tier":"protocolo","acao":"reação","desc":"3d8 dano casco inimigo"},
    "reator":       {"nome":"Sobrecarga Reator","ram":5,"tier":"protocolo","acao":"principal","desc":"2t contagem → 6d10 explosão"},
    "marionete":    {"nome":"Marionete Sintética","ram":4,"tier":"protocolo","acao":"principal","desc":"Controla ciborgue/androide 3 turnos"},
    "emp":          {"nome":"EMP Localizado","ram":4,"tier":"protocolo","acao":"principal","desc":"10m desliga tudo 2 turnos"},
    "ejetar_piloto":{"nome":"Ejetar Piloto","ram":3,"tier":"protocolo","acao":"principal","desc":"Ejeta piloto de caça/mecha"},
    "reparo_nave":  {"nome":"Reparo Estrutural","ram":4,"tier":"protocolo","acao":"principal","desc":"4d10 PV cura para a NAVE"},
    "formatar":     {"nome":"Formatar Mente","ram":5,"tier":"protocolo","acao":"principal","desc":"5d8 psíquico + apaga 24h memória"},
    "gravidade":    {"nome":"Gravidade Zero Local","ram":4,"tier":"protocolo","acao":"principal","desc":"5x5m sem gravidade, desvantagem ataques"},
}

def get_available_scripts(tecno_skill):
    """Retorna scripts disponíveis baseado no nível de Tecnomancia."""
    available = {}
    for k,v in TECNO_SCRIPTS.items():
        if v["tier"]=="basica" and tecno_skill>=1: available[k]=v
        elif v["tier"]=="injecao" and tecno_skill>=3: available[k]=v
        elif v["tier"]=="protocolo" and tecno_skill>=5: available[k]=v
    return available

def calc_max_scripts(nivel,tecno_skill):
    """Calcula quantos scripts o personagem pode conhecer."""
    return max(nivel+tecno_skill,3)

# ══════════════════════════════════════════════════════════
# DADOS ESTRUTURADOS — IMPLANTES (para comando /implante)
# ══════════════════════════════════════════════════════════

IMPLANTES_DATA = {
    # Cabeça
    "chip_ram":     {"nome":"Chip Expansão RAM","preco":1500,"slot":"cabeça","efeito":"+2 Slots RAM","mecanica":{"ram_max":2}},
    "olho":         {"nome":"Olho Biônico","preco":800,"slot":"cabeça","efeito":"+2 ataque distância, ignora fumo/escuro","mecanica":{}},
    "interface_nav":{"nome":"Interface Navegação","preco":1200,"slot":"cabeça","efeito":"Vantagem manobras evasivas (Piloto)","mecanica":{}},
    "tradutor":     {"nome":"Tradutor Universal","preco":600,"slot":"cabeça","efeito":"+2 Persuasão, traduz qualquer idioma","mecanica":{"pericias":{"persuasao":2}}},
    "mira":         {"nome":"Mira Preditiva","preco":950,"slot":"cabeça","efeito":"Reduz penalidade sniper perto","mecanica":{}},
    # Torso
    "placas":       {"nome":"Placas Subdérmicas","preco":1100,"slot":"torso","efeito":"+1 CD permanente","mecanica":{"cd":1}},
    "coracao":      {"nome":"Coração Sintético","preco":2500,"slot":"torso","efeito":"+5 PV máx, +2 vs venenos","mecanica":{"pv_max":5}},
    "filtro":       {"nome":"Filtro Pulmonar","preco":750,"slot":"torso","efeito":"Imune gases venenosos","mecanica":{}},
    "adrenalina":   {"nome":"Reator Adrenalina","preco":3000,"slot":"torso","efeito":"1x/dia Ação Principal extra","mecanica":{}},
    "bateria_int":  {"nome":"Bateria Interna","preco":2000,"slot":"torso","efeito":"Gasta PV para conjurar sem RAM","mecanica":{}},
    # Membros
    "braco":        {"nome":"Braço Hidráulico","preco":850,"slot":"membros","efeito":"+2 dano melee, Vantagem For","mecanica":{}},
    "estabilizador":{"nome":"Estabilizador Pulso","preco":500,"slot":"membros","efeito":"Sem penalidade armas pesadas","mecanica":{}},
    "mantis":       {"nome":"Lâmina Mantis","preco":1000,"slot":"membros","efeito":"1d8 oculta, dobra dano furtivo","mecanica":{}},
    "pernas":       {"nome":"Pernas Pneumáticas","preco":1500,"slot":"membros","efeito":"2x deslocamento, ignora queda 15m","mecanica":{}},
    "ancoras":      {"nome":"Âncoras Magnéticas","preco":700,"slot":"membros","efeito":"Imune derrubar, anda no teto","mecanica":{}},
}

def calc_implant_limit(con_mod):
    """Limite seguro de implantes."""
    return max(2+con_mod,1)
