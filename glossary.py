"""
📚 Glossário + Dados Mecânicos do Passagem Sombria
Tudo estático — nenhum token de IA gasto aqui.
"""

# ══════════════════════════════════════════════════════════
# DADOS MECÂNICOS PARA CRIAÇÃO DE PERSONAGEM
# ══════════════════════════════════════════════════════════

ATTR_KEYS = ["forca","destreza","constituicao","inteligencia","sabedoria","carisma"]
ATTR_LABELS = ["💪 Força","⚡ Destreza","🩸 Constituição","🧠 Inteligência","🦉 Sabedoria","🗣️ Carisma"]
ATTR_SHORT = ["For","Des","Con","Int","Sab","Car"]

def calc_mod(val):
    """Calcula modificador de atributo."""
    if val<=3: return -3
    if val<=5: return -2
    if val<=7: return -1
    if val<=9: return 0
    if val<=11: return 1
    if val<=13: return 2
    if val<=15: return 3
    return 4

RACAS_STATS = {
    "mercusys":    {"nome":"Mercusys","planeta":"Mercúrio","mods":[0,3,0,1,-1,1],"vida_ajuste":-2,"dado_nv":"1d8","desloc":18},
    "veny":        {"nome":"Ven'y","planeta":"Vênus","mods":[1,2,1,-1,1,0],"vida_ajuste":-1,"dado_nv":"1d8","desloc":9},
    "terraqueo":   {"nome":"Terráqueo","planeta":"Terra","mods":[0,0,0,0,0,0],"vida_ajuste":0,"dado_nv":"1d8","desloc":9,
                    "bonus_attr":4,"bonus_attr_max":2,"bonus_per":3},
    "marciano":    {"nome":"Marciano","planeta":"Marte","mods":[3,-1,3,0,-1,0],"vida_ajuste":2,"dado_nv":"1d10","desloc":9},
    "conjupitero": {"nome":"Conjupitero","planeta":"Júpiter","mods":[2,-2,2,2,1,-1],"vida_ajuste":-3,"dado_nv":"1d8","desloc":6,
                    "bonus_per_fixo":{"pilotagem":2,"mecanica":2}},
    "sata":        {"nome":"Sata","planeta":"Saturno","mods":[-1,1,0,2,2,0],"vida_ajuste":-1,"dado_nv":"1d6","desloc":9},
    "urak":        {"nome":"Urak","planeta":"Urano","mods":[0,-1,2,0,0,3],"vida_ajuste":-1,"dado_nv":"1d8","desloc":9},
    "proturno":    {"nome":"Proturno","planeta":"Netuno","mods":[-1,0,-1,2,3,1],"vida_ajuste":-3,"dado_nv":"1d6","desloc":9},
    "infimor":     {"nome":"Infimor","planeta":"Plutão","mods":[3,-1,2,0,0,0],"vida_ajuste":3,"dado_nv":"1d10","desloc":6},
}

CLASSES_STATS = {
    "estudioso":{"nome":"Estudioso","pv":4,"pericias":{"conhecimentos":4,"investigacao":3,"mecanica":2,"tecnomancia":2,"persuasao":1},
        "equip_fixo":["Datapad Pesquisa","Bateria Fantasma","Kit Sobrevivência Base"],"equip_escolha":[("Pistola EMP (1d4 Anti-Sintético)","Pistola Laser (1d6 Saque Rápido)")],
        "armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "mecanico":{"nome":"Mecânico","pv":6,"pericias":{"mecanica":5,"pilotagem":2,"armas_brancas":2,"tecnomancia":1,"persuasao":1,"sobrevivencia":1},
        "equip_fixo":["Garras Combate (1d4)","Ferramentas Mecânicas","Kit Sobrevivência Base"],"equip_escolha":[("Revólver Íons (1d8 Brutal)","Escopeta Sônica (2d6 Curto Alcance)")],
        "armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "assassino":{"nome":"Assassino","pv":8,"pericias":{"furtividade":4,"armas_brancas":2,"armas_fogo":2,"espionagem":2,"medicina":1,"persuasao":1},
        "equip_fixo":["Faca Plasma (1d4 Oculta/Ágil)","Granada Fumaça","Kit Sobrevivência Base"],"equip_escolha":[("Besta Phobos (1d10 Silenciosa)","SubMetra Flechetes (2d4 Sangramento)")],
        "armadura":{"nome":"Traje Furtivo Nanofibra","cd":1,"tipo":"leve"}},
    "soldado":{"nome":"Soldado","pv":10,"pericias":{"armas_fogo":4,"armas_brancas":3,"explosivos":2,"pilotagem":1,"sobrevivencia":1,"furtividade":1},
        "equip_fixo":["Faca Plasma (1d4)","Kit Médico Batalha","Kit Sobrevivência Base"],"equip_escolha":[("Rifle Assalto (1d8 Rajada)","Escopeta Sônica (2d6 Curto Alcance)")],
        "armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "starlord":{"nome":"Starlord","pv":8,"pericias":{"persuasao":5,"armas_fogo":2,"tecnomancia":2,"pilotagem":2,"furtividade":1},
        "equip_fixo":["Pistola Laser (1d6)","Faca Plasma (1d4)","Kit Sobrevivência Base"],
        "armadura":{"nome":"Roupas Elegantes","cd":0,"tipo":"leve"}},
    "franco_atirador":{"nome":"Franco-Atirador","pv":6,"pericias":{"armas_fogo":5,"sobrevivencia":3,"furtividade":2,"investigacao":2},
        "equip_fixo":["Rifle Precisão (1d12 Telescópica/Brutal)","Bastão Choque (1d6)","Binóculos Termais","Kit Sobrevivência Base"],
        "armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "musico":{"nome":"Músico","pv":4,"pericias":{"tecnomancia":5,"performance":4,"persuasao":2,"armas_brancas":1},
        "equip_fixo":["Pistola Laser (1d6)","Instrumento Musical Digital","Bateria Fantasma","Kit Sobrevivência Base"],
        "armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "espiao":{"nome":"Espião","pv":4,"pericias":{"espionagem":4,"persuasao":4,"furtividade":2,"acrobacia":1,"intimidacao":1},
        "equip_fixo":["Pistola Laser (1d6)","Faca Plasma (1d4 Oculta)","2 IDs Falsas","Kit Sobrevivência Base"],
        "armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "catador":{"nome":"Catador","pv":6,"pericias":{"persuasao":3,"investigacao":2,"sobrevivencia":2,"mecanica":2,"pilotagem":2,"armas_fogo":1},
        "equip_fixo":["Revólver Íons (1d8)","Bastão Choque (1d6)","Maçarico Laser","Kit Sobrevivência Base"],
        "armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "piloto":{"nome":"Piloto","pv":6,"pericias":{"pilotagem":5,"mecanica":2,"persuasao":2,"sobrevivencia":2,"armas_fogo":1},
        "equip_fixo":["Chave Inglesa (1d4)","Kit Sobrevivência Base"],"equip_escolha":[("Revólver Íons (1d8 Brutal)","Escopeta Sônica (2d6 Curto Alcance)")],
        "armadura":{"nome":"Traje Bordo Atmosférico","cd":2,"tipo":"media"}},
    "batedor":{"nome":"Batedor","pv":8,"pericias":{"sobrevivencia":4,"armas_fogo":3,"investigacao":3,"furtividade":1,"explosivos":1},
        "equip_fixo":["SubMetra Flechetes (2d4)","Faca Plasma (1d4)","Granada Fumaça","Kit Sobrevivência Base"],
        "armadura":{"nome":"Traje Furtivo Nanofibra","cd":1,"tipo":"leve"}},
    "explorador":{"nome":"Explorador","pv":6,"pericias":{"investigacao":4,"sobrevivencia":4,"conhecimentos":3,"persuasao":1},
        "equip_fixo":["Rifle Assalto (1d8)","Faca Plasma (1d4)","Scanner Ambiental","Corda Nanofibra 15m","Kit Sobrevivência Base"],
        "armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
    "cinetico":{"nome":"Cinético","pv":4,"pericias":{"tecnomancia":5,"medicina":3,"resistencia":2,"acrobacia":2},
        "equip_fixo":["Pistola EMP (1d4)","Deck Pulso","Bateria Fantasma","Kit Médico Batalha","Kit Sobrevivência Base"],
        "armadura":{"nome":"Roupas Civis","cd":0,"tipo":"leve"}},
    "prospector":{"nome":"Prospector","pv":4,"pericias":{"persuasao":5,"lideranca":4,"tecnomancia":3},
        "equip_fixo":["Pistola Laser (1d6)","Datapad Corporativo","Contratos + Caneta Digital","Kit Sobrevivência Base"],
        "armadura":{"nome":"Roupas Luxo","cd":0,"tipo":"leve"},"creditos_extra":100},
    "pirata":{"nome":"Pirata","pv":10,"pericias":{"armas_fogo":3,"armas_brancas":3,"intimidacao":3,"sobrevivencia":2,"pilotagem":1},
        "equip_fixo":["Escopeta Sônica (2d6)","Arpéu Magnético","Granada Fumaça","Kit Sobrevivência Base"],
        "equip_escolha_melee":[("Bastão Choque (1d6 Atordoante)","Faca Plasma (1d4 Oculta)")],
        "armadura":{"nome":"Colete Tático","cd":2,"tipo":"media"}},
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

# Perícias com atributos possíveis (primeiro = padrão)
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

# ══════════════════════════════════════════════════════════
# BOTÕES (labels curtos para criação)
# ══════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════
# TEXTOS DE DISPLAY DO GLOSSÁRIO (raças, classes, etc.)
# Mesmo conteúdo de antes — mantido para brevidade
# ══════════════════════════════════════════════════════════

# Reutiliza os textos longos do glossary anterior
# (RACAS_DETAIL, CLASSES_DETAIL, ARMAS_BRANCAS_TEXT, etc.)
# Importados aqui para manter o arquivo gerenciável

RACAS_DETAIL = {
    "mercusys":"🔥 *MERCUSYS — Nômades da Velocidade*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Mercúrio | Des+3 Int+1 Sab-1 | Vida-2 | 🏃 18m\n\n⚡ Deslocamento DOBRADO, regenera 1d4 extra DC (dobro rações)\n👆 Leitura Sensitiva (toque=composição)\n🔥 Resist Calor (desvantagem <25°C)\n🌟 Nv10: 2 turnos extras, imune ataque oportunidade",
    "veny":"🌿 *VEN'Y — Predadores da Bruma*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Vênus | For+1 Des+2 Con+1 Int-1 Sab+1 | Vida-1\n\n🌬️ Air Shifter: O₂=asas He=flutua H₂=+2For N₂=resist fogo Ar=-2dano\n🌟 Nv10: 2 efeitos simultâneos + nuvem 4d6",
    "terraqueo":"🌍 *TERRÁQUEO — Força da Adaptação*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Terra | +4 atributos livres | +3 perícias livres | Vida+0\n\n🔧 Gambiarra: 1x/dia, 3 sucatas→item funcional\n🌟 Nv10: Sobrevive golpe letal 1PV, cura 3d8+Con, turno extra",
    "marciano":"⚔️ *MARCIANO — Conclave da Guerra*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Marte | For+3 Con+3 Des-1 Sab-1 | Vida+2 | 4 BRAÇOS\n\n🔥 Êxtase: 1-3=+2dano/+3m 4-6=+2ataque dist (4t)\n🛡️ Endurecer: -2 dano (4t)\n🌟 Nv10: Armas pesadas 1 mão, ambos Êxtases",
    "conjupitero":"⚙️ *CONJUPITERO — Titãs da Engenharia*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Júpiter | For+2 Con+2 Int+2 Des-2 Sab+1 Car-1 | Vida-3 | 80cm 120kg\n\n🏋️ +2CD vs empurrão, carga TRIPLA\n🔧 +2 Pilotagem/Mecânica permanente | 💎 10% desconto\n🌟 Nv10: Singularidade 10m, 4d10 esmagamento",
    "sata":"💫 *SATA — Cultistas do Anel*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Saturno | Int+2 Sab+2 For-1 Des+1 | Vida-1\n\n💚 Cura Genética 1x/dia: 1d8+Sab\n🫥 Camuflagem: +5 Furtividade imóvel\n❤️ Emprestar Vitalidade (transfere PV)\n🌟 Nv10: Pulso 5d8+Sab 10m, remove condições, ressuscita",
    "urak":"❄️ *URAK — Voz do Zero Absoluto*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Urano | Car+3 Con+2 Des-1 | Vida-1 | 150 cordas vocais\n\n🎵 Mímica Sonora: imita qualquer voz, vantagem enganação\n🧊 Criogênese: cria objeto de gelo (6t)\n❄️ Resist Frio (stress >15°C)\n🌟 Nv10: Grito 4d8 gélido 15m, paralisa 2t",
    "proturno":"🧠 *PROTURNO — Domínio da Sombra*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Netuno | Int+2 Sab+3 Car+1 For-1 Con-1 | Vida-3\n\n🧠 Levantamento Mental: Int para mover 50kg a 10m\n💀 Invasão Sombra: controle mental (Sab vs alvo, falha=2dano)\n🌟 Nv10: Sem dano falha, esmaga 3 inimigos 5d10",
    "infimor":"🪐 *INFIMOR — Titãs do Vácuo*\n━━━━━━━━━━━━━━━━━━━━\n🌍 Plutão | For+3 Con+2 Des-1 | Vida+3 | ~3m, imune vácuo\n\n🤏 Encolher: ½ altura, vantagem furtividade\n💪 Braços Telescópicos: melee a 10m\n😡 Fúria Desclassificados: +2 tudo mas perde controle 5t\n🌟 Nv10: Colosso 5m, Fúria COM controle, +20PV temp",
}

CLASSES_DETAIL = {
    "estudioso":"📚 *ESTUDIOSO* — Cofre de Conhecimento\n━━━━━━━━━━━━━━━━━━━━\n❤️+4 PV | 🎯 Perito fraquezas/puzzles\nPerícias: Conhecimentos+4 Investigação+3 Mecânica+2 Tecnomancia+2 Persuasão+1\n🔹 Mapa Mental: 1x/sessão, Mestre dá info sobre criatura/tech\n🔹 Ponto Estrutural (1RAM): próximo ataque=dano MÁXIMO\n🎒 Roupas Civis | EMP ou Laser | Datapad | Bateria",
    "mecanico":"🔧 *MECÂNICO* — Arquiteto da Sobrevivência\n━━━━━━━━━━━━━━━━━━━━\n❤️+6 PV | 🎯 Suporte/reparos/naves\nPerícias: Mecânica+5 Pilotagem+2 ArmBrancas+2 Tecnomancia+1 Persuasão+1 Sobrevivência+1\n🔹 Ignora penalidade armaduras pesadas\n🔹 Reparo Tático: 1d6+Mec PV temporários aliado\n🎒 Traje Bordo | Íons ou Escopeta | Garras | Ferramentas",
    "assassino":"🗡️ *ASSASSINO* — Sombra Silenciosa\n━━━━━━━━━━━━━━━━━━━━\n❤️+8 PV | 🎯 Dano explosivo furtivo\nPerícias: Furtividade+4 ArmBrancas+2 ArmFogo+2 Espionagem+2 Medicina+1 Persuasão+1\n🔹 Primeiro Corte: +2 acerto, DOBRA dano vs desprevenido\n🔹 Desaparecer: ao matar, furtividade grátis\n🎒 Traje Furtivo | Besta Phobos ou SubMetra | Faca Plasma | Granada",
    "soldado":"🎖️ *SOLDADO* — Baluarte de Fogo\n━━━━━━━━━━━━━━━━━━━━\n❤️+10 PV | 🎯 Linha de frente, tanque\nPerícias: ArmFogo+4 ArmBrancas+3 Explosivos+2 Pilotagem+1 Sobrevivência+1 Furtividade+1\n🔹 Sem penalidade armas Pesadas\n🔹 Fogo Supressão: inimigo testa Sab ou desvantagem\n🎒 Colete | Rifle ou Escopeta | Faca Plasma | Kit Médico",
    "starlord":"🌟 *STARLORD* — Voz de Comando\n━━━━━━━━━━━━━━━━━━━━\n❤️+8 PV | 🎯 Líder/inspirador\nPerícias: Persuasão+5 ArmFogo+2 Tecnomancia+2 Pilotagem+2 Furtividade+1\n🔹 Charme: re-rola persuasão falhada 1x\n🔹 \"Deixem comigo!\": aliado ganha Vantagem\n🎒 Roupas Elegantes | Pistola Laser | Faca Plasma",
    "franco_atirador":"🎯 *FRANCO-ATIRADOR* — Observador Letal\n━━━━━━━━━━━━━━━━━━━━\n❤️+6 PV | 🎯 Controle à distância\nPerícias: ArmFogo+5 Sobrevivência+3 Furtividade+2 Investigação+2\n🔹 +5 ataque >30m (só +2 ≤30m)\n🔹 Tiro Incapacitante: ½ dano, imobiliza 1t\n🎒 Colete | Rifle Precisão | Bastão Choque | Binóculos",
    "musico":"🎵 *MÚSICO* — Arquiteto de Frequências\n━━━━━━━━━━━━━━━━━━━━\n❤️+4 PV | 🎯 Buff/debuff via som\nPerícias: Tecnomancia+5 Performance+4 Persuasão+2 ArmBrancas+1\n🔹 +2CD vs controle mental/sônico\n🔹 Frequência: +2 dano aliados OU -2CD inimigos 10m\n🎒 Roupas Civis | Pistola Laser | Instrumento | Bateria",
    "espiao":"🕵️ *ESPIÃO* — Fantasma de Mil Rostos\n━━━━━━━━━━━━━━━━━━━━\n❤️+4 PV | 🎯 Infiltração social\nPerícias: Espionagem+4 Persuasão+4 Furtividade+2 Acrobacia+1 Intimidação+1\n🔹 Vantagem persuasão/enganação com disfarce\n🔹 Ponto Cego: inimigos o ignoram\n🎒 Roupas Civis | Pistola Laser | Faca Plasma | 2 IDs",
    "catador":"♻️ *CATADOR* — Rei da Sucata\n━━━━━━━━━━━━━━━━━━━━\n❤️+6 PV | 🎯 Loot/reparos com pouco\nPerícias: Persuasão+3 Investigação+2 Sobrevivência+2 Mecânica+2 Pilotagem+2 ArmFogo+1\n🔹 Olho para Ouro: 1d6, 4-6=item extra\n🔹 Desmanche: 1d8 dano + reduz CD robô\n🎒 Traje Bordo | Revólver Íons | Bastão Choque | Maçarico",
    "piloto":"✈️ *PILOTO* — Coração da Nave\n━━━━━━━━━━━━━━━━━━━━\n❤️+6 PV | 🎯 Salvação em combate espacial\nPerícias: Pilotagem+5 Mecânica+2 Persuasão+2 Sobrevivência+2 ArmFogo+1\n🔹 +2CD veículo pilotado\n🔹 Sobrecarga Propulsores: vantagem evasiva, nave toma 1d4\n🎒 Traje Bordo | Íons ou Escopeta | Chave Inglesa",
    "batedor":"👁️ *BATEDOR* — Vanguarda do Perigo\n━━━━━━━━━━━━━━━━━━━━\n❤️+8 PV | 🎯 Detectar/marcar ameaças\nPerícias: Sobrevivência+4 ArmFogo+3 Investigação+3 Furtividade+1 Explosivos+1\n🔹 Nunca surpreendido, +2 Iniciativa\n🔹 Marca: aliados ignoram cobertura do alvo\n🎒 Traje Furtivo | SubMetra | Faca Plasma | Granada",
    "explorador":"🗺️ *EXPLORADOR* — Navegador das Rotas\n━━━━━━━━━━━━━━━━━━━━\n❤️+6 PV | 🎯 Guia/analista biológico\nPerícias: Investigação+4 Sobrevivência+4 Conhecimentos+3 Persuasão+1\n🔹 Grupo ignora terreno difícil 10m\n🔹 Vulnerabilidade: descobre fraqueza, +1d6 dano\n🎒 Colete | Rifle Assalto | Scanner | Corda 15m",
    "cinetico":"⚡ *CINÉTICO* — Ponte Mente-Máquina\n━━━━━━━━━━━━━━━━━━━━\n❤️+4 PV | 🎯 Tecnomante curador\nPerícias: Tecnomancia+5 Medicina+3 Resistência+2 Acrobacia+2\n🔹 Bio-feedback: ao curar aliado, recupera 2PV próprio\n🔹 Repulsão (1RAM): empurra inimigos 3m\n🎒 Roupas Civis | EMP | Deck Pulso | Bateria | Kit Médico",
    "prospector":"💼 *PROSPECTOR* — Rosto da Tripulação\n━━━━━━━━━━━━━━━━━━━━\n❤️+4 PV | 🎯 Negociador/créditos\nPerícias: Persuasão+5 Liderança+4 Tecnomancia+3\n🔹 +20% créditos em recompensas\n🔹 \"Espere!\": inimigo perde ação 1t\n🎒 Roupas Luxo | Pistola Laser | Datapad | +100CG extras",
    "pirata":"☠️ *PIRATA* — Terror do Vácuo\n━━━━━━━━━━━━━━━━━━━━\n❤️+10 PV | 🎯 Combate brutal/boarding\nPerícias: ArmFogo+3 ArmBrancas+3 Intimidação+3 Sobrevivência+2 Pilotagem+1\n🔹 Sem penalidade espaço confinado, +1 dano em nave\n🔹 Grito: 5m, Sab ou Amedrontado 2t\n🎒 Colete | Escopeta Sônica | Bastão ou Faca | Arpéu | Granada",
}

# Arsenal, Armaduras, Ferramentas, Implantes, Tecnomancia, Naves, Bestiário, Filosofias
# (Textos longos para o glossário — mesmos de antes)

ARMAS_BRANCAS_TEXT = (
    "🗡️ *ARSENAL — ARMAS BRANCAS*\n━━━━━━━━━━━━━━━━━━━━\n"
    "Ataque: 1d20+For+Per | Dano: dado+For | Ágeis: podem usar Des\n\n"
    "💀 *1d4:* Faca Plasma 40CG (Oculta/Ágil) | Garras 45CG (Aderência/Ágil) | Maçarico 60CG (Derrete metal) | Soco Inglês 35CG (Crítico=atordoa)\n\n"
    "⚔️ *1d6:* Bastão Choque 50CG (Max=perde mov) | Chicote Mono 250CG (3m/Ágil) | Manopla Grav 200CG (Empurra 2m) | Chave Inglesa 20CG (+2 vs robôs) | Arpéu 90CG (Puxa 5m) | Bastão Telescópico 40CG (Oculta) | Katar Ven'y 120CG (Veneno) | Escudo-Lâmina 100CG (+1CD tiros)\n\n"
    "🔥 *1d8:* Espada Térmica 150CG | Lança Ven'y 80CG (Arremessável/Ágil) | Lâmina Marciana 110CG (Aparar +1CD) | Nunchaku 95CG (Ágil) | Machado Sucata 30CG (Quebra armadura) | Foice Deimos 130CG (Sangra)\n\n"
    "💎 *1d10+:* Foice Diamante 800CG 1d10 (-2CD arm) | Alabarda 350CG 1d10 (3m) | Lança Choque 220CG 1d10 (Investida) | Martelo Demolição 180CG 2d6 (2x objetos) | Machado Cinético 400CG 2d8 (Pesada) | Martelo Sísmico 1500CG 1d20 (Derrubar) | Espadão Fusão 2000CG 2d12 (Pesada/Queima)")

ARMAS_FOGO_TEXT = (
    "🔫 *ARSENAL — ARMAS DE FOGO*\n━━━━━━━━━━━━━━━━━━━━\n"
    "Ataque: 1d20+Des+Per | Dano: dado+Des | 🔋 Pente: 3t | Rajada: 2t\n\n"
    "💀 *1d4:* EMP 100CG (3d4 vs robôs) | Lança-Chamas 250CG (Área 3x3) | Sinalizadora 25CG (Marca) | Dardos Tóxicos 150CG (Silenciosa+1d6 veneno) | Derringer 120CG (Oculta/1º=vantagem)\n\n"
    "⚔️ *1d6-2d4:* Pistola Laser 60CG 1d6 (Saque Rápido) | Besta Repetição 180CG 1d6 (Rajada Silenciosa) | Lança-Granadas 300CG 1d6 (Área) | Micro-ondas 450CG 1d6 (Contínuo +1d6/t) | SubMetra 220CG 2d4 (Sangra) | Fuzil Estilhaços 140CG 2d4 (Cone 5m)\n\n"
    "🔥 *1d8-1d12:* Revólver Íons 160CG 1d8 (Brutal 19-20) | Rifle Assalto 200CG 1d8 (Rajada) | Carabina 130CG 1d8 (Sem falha) | Besta Phobos 350CG 1d10 (Silenciosa) | Rifle Laser 280CG 1d10 (-1CD) | Rifle Precisão 500CG 1d12 (Telescópica/Brutal) | Arco Phobos 300CG 1d12 (Usa FOR) | Canhão Plasma 650CG 1d12\n\n"
    "💎 *2d6+:* Escopeta Sônica 260CG 2d6 (-4 >10m) | Rust 300CG 2d8 (Descarregar=4d8) | Canhão Sônico 800CG 2d8 (Cone 10m) | Minigun 900CG 3d6 (Pesada) | Antimatéria 3500CG 1d20 | Gauss 4500CG 2d20 (Atravessa paredes)")

ARMADURAS_TEXT = (
    "🛡️ *ARMADURAS*\n━━━━━━━━━━━━━━━━━━━━\nCD = 10 + Des + Armadura\n\n"
    "👕 *Leves* (toda Des): Civis 20CG +0 | Elegantes 80CG +0 | Furtivo 250CG +1(+2Furt) | Escudo Energia 800CG absorve 10dano\n\n"
    "🦺 *Médias* (Des máx+2): Colete 150CG +2 | Traje Bordo 180CG +2(imune vácuo) | Exoesqueleto 300CG +4(-2Furt)\n\n"
    "🏋️ *Pesadas* (sem Des): Urak 450CG +3(reflete 1d4) | Conjupitera 500CG +4(+2Mec) | Marciana 650CG +6(-4Furt) | Mecha 3500CG +8")

FERRAMENTAS_TEXT = "🛠️ *FERRAMENTAS E UTILITÁRIOS*\n━━━━━━━━━━━━━━━━━━━━\n🏕️ Kit Base 50CG | Rações 3d 15CG | Luzes 5CG | Comunicador 25CG | Corda 20CG | Fita 5CG\n💊 Kit Médico 30CG (1d8) | Primeiros Socorros 20CG\n💣 Granada Fumaça 35CG | Granada Luz 40CG | Scanner 60CG | Binóculos 80CG\n🧠 Bateria Fantasma 30CG (+1RAM) | Deck Pulso 100CG | Datapad 120CG | Instrumento 100CG\n🕵️ IDs Falsas 150CG | Contratos 15CG\n🍷 Módulo Som 25CG | Garrafa 40CG"

IMPLANTES_TEXT = "🦾 *IMPLANTES*\n━━━━━━━━━━━━━━━━━━━━\n⚠️ Limite: 2+Mod.Con | 1º extra=-1d6PV | 2º=curto 1-2nat | 3º=morte\n\n🧠 Chip RAM 1500CG +2RAM | Olho 800CG +2dist | Interface Nav 1200CG vantagem evasiva | Tradutor 600CG +2Pers | Mira 950CG\n🫀 Placas 1100CG +1CD | Coração 2500CG +5PV | Filtro 750CG imune gás | Adrenalina 3000CG ação extra | Bateria Int 2000CG PV→RAM\n🦿 Braço 850CG +2dano | Estabilizador 500CG sem pesada | Mantis 1000CG 1d8 dobra furtivo | Pernas 1500CG 2x desloc | Âncoras 700CG imune derrubar"

NAVES_TEXT = "🚀 *FROTA ESTELAR*\n━━━━━━━━━━━━━━━━━━━━\nCD: 10+Man+Piloto | ⚡Energia=normal | ⚡EMP=2x escudo ½casco | 💥Balístico=+1d casco\n\n✈️ Caça 15k C30 E10 M+4 Plasma3d6 | Interceptador 45k C40 E15 M+3 EMP2d10 | Veleiro Sata C40 E25 M+5 Micro3d8\n🚀 Cargueiro 60k C60 E30 M+1 Torreta3d8 ⭐NAVE INICIAL | Prospecção 90k C80 E20 M-1 Laser4d8\n⚔️ Cruzador Proturno C70 E80 M0 Íon8d10 | Corveta 190k C100 E50 M-1 Mísseis6d10 | Bombardeiro Urak C120 E30 M-3 Sísmico8d12 | Fragata Marciana 300k C150 E40 M-2 Railgun5d12\n💀 Encouraçado C300 E150 M-4 Plasma10d20 — CHEFE"

MODIFICACOES_TEXT = "🔧 *MODIFICAÇÕES*\n━━━━━━━━━━━━━━━━━━━━\nSlots: Simples=1 | Primária=2 (máx 1 tecno) | CD13 para instalar\n\n🗡️ Mec: Nanofibra 150(Ágil) | Fio 200(Sangra) | Cabo 120(Oculta) | Haste 160(+3m) | Injetor 100(veneno)\n🗡️ Tec: Motor 250(Impacto) | Choque 300(Atordoa) | Núcleo 400(½fogo) | Matriz 450(2x escudo) | Cristal 600(cura crítico)\n🔫 Mec: Pente 150(4t) | Silenciador 200 | Cano Serrado 100(+2/-4) | Coronha 200(anula Pesada) | Granadas 350\n🔫 Tec: SmartLink 500(re-rola) | Térmico 400(fogo) | EMP 350(Anti-Sint) | Biométrica 250 | Magnética 500(-1CD)"

FILOSOFIAS_TEXT = "📜 *FILOSOFIAS DE VIDA*\n━━━━━━━━━━━━━━━━━━━━\n🌌 *Caminhos:* Voz (desvantagem alvo) | Ressonância (sente 10m escuro) | Engrenagem (falha→comum) | Espiral (cura vantagem) | Anel (1PV letal) | Ocaso (1d4 dano=+1d4 rolagem)\n⚙️ *Códigos:* Sobrevivente (+2 Init) | Corporativo (vantagem negociar) | Cético (+2CD psi) | Fronteira (+1 sozinho) | Caserna (tanka aliado) | Vira-Lata (distrai+vantagem)"

TECNO_BASICAS = "🟢 *ROTINAS BÁSICAS (Nv1, Tecno+1/+2)*\n━━━━━━━━━━━━━━━━━━━━\n⚡0RAM: Ping(livre,interage 10m) | Choque(1d6) | Query(lê pensamento) | Bateria(recarrega) | Scanner(vê emissões 50m)\n🔋1RAM: Jammer(10m sem comun 3t) | Glitch(-2 ataque alvo) | Trava Biométrica(tranca porta) | Rollback(cura 1d8+Int) | Firewall(reação, bloqueia 1d10+Int)"
TECNO_INJECOES = "🟡 *INJEÇÕES MALICIOSAS (Nv2, Tecno+3/+4)*\n━━━━━━━━━━━━━━━━━━━━\n🔋1: Ejetar Pente(reação,força recarga)\n🔋🔋2: Travar Arma(1t) | Curto Armadura(-3CD 2t) | Hackear Motor(½desloc 3t) | Cegueira(cego 2t) | Drenar Escudo(→PV temp) | Sobrecarga(2d6 área) | Desativar Vida(desliga O₂) | Loop(anula script)\n🔋🔋🔋3: Torreta Sentinela(drone aliado 3t)"
TECNO_PROTOCOLOS = "🔴 *PROTOCOLOS SOBRESCRITA (Nv3, Tecno+5+)*\n━━━━━━━━━━━━━━━━━━━━\n🔋🔋🔋3: Hackear Nav(controla nave 1t) | Inverter Prop(3d8 casco) | Ejetar Piloto\n🔋🔋🔋🔋4: Apagão Motor(à deriva 1t) | EMP Local(10m desliga tudo 2t) | Reparo Nave(4d10PV) | Gravidade Zero(5x5m)\n🔋🔋🔋🔋🔋5: Sobrecarga Reator(6d10 explosão) | Marionete(controla 3t) | Formatar Mente(5d8 psi)"

BESTIARIO_PLANETAS = "👾 *BESTIÁRIO POR PLANETA*\n━━━━━━━━━━━━━━━━━━━━\n🌍Terra: Pirata(15,12,1d6) Mercenário(45,15,1d8) Comodoro(110,16,2x1d8)\n⚔️Marte: Recruta(25,13,1d8) Legionário(55,16,1d12) Senhor Guerra(140,17,3atk)\n🌿Vênus: Batedor(20,13,1d8) Xamã(50,14,1d8) Predador(120,14,2x2d6)\n🔥Mercúrio: Corredor(18,14,1d4) Assassino(40,15,2x1d6) Ancião(90,17)\n⚙️Júpiter: Operário(30,14,2d6) Eng(65,16,2d6) Barão(150,18,2d10)\n💫Saturno: Acólito(20,12,cura) Inquisidor(55,15,2d4) Sacerdote(100,16)\n❄️Urano: Ecoador(22,13,1d6) Tecelão(50,14,2d6) Maestro(115,15)\n🧠Netuno: Guarda(15,12,1d6) Telepata(45,14,2d6) Juiz(105,16,3d10)\n🪐Plutão: Catador(35,11,1d6) Esmagador(70,13,2d6) Titã(150,14,2d8)"
BESTIARIO_FAUNA = "🦎 *FAUNA ALIENÍGENA*\n━━━━━━━━━━━━━━━━━━━━\nCão-Cego(18,12,1d6 matilha sangra) | Parasita Neural(8,14,controle) | Rastejador Vidro(22,15,1d8 invisível) | Urso-Tanque(65,16,2d8) | Morcego-Bomba(15,11,explode 2d6) | Sanguessuga Vácuo(10,10,drena) | Mímico Carnal(40,13,1d10) | Enxame Ferrugem(35,12,corrói) | Devorador Fósforo(45,14,2d6) | Leviatã(120,18,3d10 engole) | Quimera Alfa(85,17,2d8 regen)\n🌿 Flora: Musgo(1d4 ácido) | Lírio-Ímã(EMP) | Árvore-Pulmão(alucinógeno) | Vinhas Tungstênio(prende) | Orquídea Sangue(+2For/Des, -1PV máx)"
BESTIARIO_VAZIO = "👾 *CRIAS DO VAZIO*\n━━━━━━━━━━━━━━━━━━━━\n💀Comuns: Sanguessuga(30,12,drena PV+RAM) | Enxame Adaptativo(15cada,evolui)\n⚔️Elites: Falso Aliado(50,13,assimila) | Espectro(45,16,1d10psi IMUNE físico) | Tecelão Fendas(50,14,portais) | Terror(70,14,emerge)\n🔥Fortes: Olho Abismo(60,13,3d8 linha) | Silenciador(65,15,desliga tecno 15m) | Bocarra(55,12,2d8 ácido explode)\n💀Chefes: Devorador(80→∞,cresce) | Colecionador(110,15,absorve) | Soberana(180,17,2d8psi invoca controla)"
