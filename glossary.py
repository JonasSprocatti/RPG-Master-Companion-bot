"""
📚 Glossário completo do Passagem Sombria — RPG Espacial
Dados estáticos exibidos por botões, sem consumir tokens da IA.
"""

# ══════════════════════════════════════════════════════════
# RAÇAS
# ══════════════════════════════════════════════════════════

RACAS_DETAIL = {
    "mercusys": (
        "🔥 *MERCUSYS — Os Nômades da Velocidade*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Mercúrio (A Fornalha dos Condenados)\n\n"
        "Humanoides altos, esguios, de pele avermelhada e *quatro pernas*. "
        "Metabolismo alucinante — tudo neles é rápido: movimento, raciocínio, "
        "regeneração e, tragicamente, o esquecimento. Vivem no eterno \"agora\".\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-2\n"
        "For+0 | Des+3 | Con+0 | Int+1 | Sab-1 | Car+1\n\n"
        "⚡ *Habilidades:*\n"
        "🏃 Alta Velocidade: deslocamento DOBRADO, regenera 1d4 extra em descanso curto "
        "(precisa dobro de rações ou +1 exaustão)\n"
        "👆 Leitura Sensitiva: ao tocar superfície, identifica composição e detecta venenos\n"
        "🔥 Resistência ao Calor: imune a fogo ambiental (desvantagem abaixo de 25°C)\n\n"
        "🌟 *Nv10 — Aceleração Relativística:* 1x/DL, ganha 2 turnos completos antes de qualquer "
        "inimigo reagir. Permanentemente imune a ataques de oportunidade."
    ),
    "veny": (
        "🌿 *VEN'Y — Os Predadores da Bruma*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Vênus (O Éden Ácido)\n\n"
        "Pele azul-esverdeada para camuflagem nas florestas de gás. Múltiplos pulmões "
        "processam quase qualquer gás. Sociedade tribal de caçadores implacáveis.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-1\n"
        "For+1 | Des+2 | Con+1 | Int-1 | Sab+1 | Car+0\n\n"
        "⚡ *Habilidades:*\n"
        "🌬️ Air Shifter (respira gás 6min = efeito):\n"
        "  O₂=asas de voo | He=flutua, imune queda | H₂=+2 Força\n"
        "  N₂=resist fogo | Ar=-2 dano físico | Kr=-2 tudo | Rn=vantagem audição\n\n"
        "🌟 *Nv10 — Pulmão Alquímico:* 2 efeitos simultâneos + exala nuvem 4d6 dano área 3x3m."
    ),
    "terraqueo": (
        "🌍 *TERRÁQUEO — A Força da Adaptação*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Terra (A Velha Mãe Sucateada)\n\n"
        "Sem a força dos Marcianos ou a telepatia dos Proturnos, os humanos compensam "
        "com resiliência absoluta. Mestres da sobrevivência, gambiarras e diplomacia.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)\n"
        "+4 pontos livres em atributos (máx +2 num único) | +3 pontos livres em perícias\n\n"
        "⚡ *Habilidades:*\n"
        "🔧 Alta Adaptabilidade: +2 atributos + 3 perícias livres extras na criação\n"
        "🛠️ Gambiarra: 1x/dia, transforma 3 sucatas em item funcional temporário\n\n"
        "🌟 *Nv10 — Espírito Indomável:* 1x/DL, sobrevive golpe letal com 1PV, "
        "cura 3d8+Con e ganha turno extra imediato."
    ),
    "marciano": (
        "⚔️ *MARCIANO — O Conclave da Guerra*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Marte (A Máquina de Moer)\n\n"
        "2,3m de altura, pele negro/vermelho-ferrugem, *QUATRO BRAÇOS*. Dois frontais "
        "precisos, dois traseiros pesados. Facções: Phobos (corpo a corpo honrado) e "
        "Deimos (rifles e táticas frias).\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)+2\n"
        "For+3 | Des-1 | Con+3 | Int+0 | Sab-1 | Car+0\n\n"
        "⚡ *Habilidades:*\n"
        "🔥 Êxtase da Batalha (1d6): 1-3 Phobos (+2 dano, +3m desloc) | "
        "4-6 Deimos (+2 ataque distância, ignora cobertura). Dura 4 turnos.\n"
        "🛡️ Endurecer: -2 dano físico recebido por 4 turnos\n\n"
        "🌟 *Nv10 — Senhor da Guerra:* Armas pesadas com 1 mão. Êxtase dá AMBOS os bônus."
    ),
    "conjupitero": (
        "⚙️ *CONJUPITERO — Titãs da Engenharia*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Júpiter (O Poço Oligárquico)\n\n"
        "80cm de altura, 120kg de puro músculo denso. Evoluíram sob gravidade esmagadora. "
        "Mentes que enxergam a realidade como uma engine de física ajustável.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-3\n"
        "For+2 | Des-2 | Con+2 | Int+2 | Sab+1 | Car-1\n\n"
        "⚡ *Habilidades:*\n"
        "🏋️ Física de Motor: +2CD vs empurrão, carga TRIPLA\n"
        "🔧 Engenharia de Bordo: +2 permanente em Pilotagem e Mecânica\n"
        "💎 Conta da Confederação: 10% desconto em todas as lojas\n\n"
        "🌟 *Nv10 — Singularidade:* 1x/dia, poço gravitacional 10m. 4d10 esmagamento, "
        "inimigos perdem Ação de Movimento."
    ),
    "sata": (
        "💫 *SATA — Cultistas do Anel*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Saturno (O Berço da Espera)\n\n"
        "1,90m, serenos, profundamente religiosos. Cultuam os anéis como estilhaços do "
        "núcleo primordial. Medicina e manipulação genética mais avançadas do sistema.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-1\n"
        "For-1 | Des+1 | Con+0 | Int+2 | Sab+2 | Car+0\n\n"
        "⚡ *Habilidades:*\n"
        "💚 Cura Genética: 1x/dia, cura 1d8+Sab PV (rolar 8=duplica, rolar 1=2 dano próprio)\n"
        "🫥 Camuflagem Cromática: +5 Furtividade imóvel ou ½ velocidade\n"
        "❤️ Emprestar Vitalidade: transfere até metade dos seus PV atuais para aliado\n\n"
        "🌟 *Nv10 — Milagre Primordial:* Pulso cura 5d8+Sab todos aliados 10m. "
        "Remove venenos/sangramentos. Pode gastar turno + ½ vida para ressuscitar aliado."
    ),
    "urak": (
        "❄️ *URAK — A Voz do Zero Absoluto*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Urano (O Cofre Congelado)\n\n"
        "Ninguém sabe como é o rosto de um Urak — cobertos por pelagens e trajes térmicos. "
        "150 cordas vocais replicam qualquer frequência. Reprodução assexuada.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-1\n"
        "For+0 | Des-1 | Con+2 | Int+0 | Sab+0 | Car+3\n\n"
        "⚡ *Habilidades:*\n"
        "🎵 Mímica Sonora: imita qualquer voz/som. Vantagem em enganação por voz.\n"
        "🧊 Criogênese: cria objeto de gelo médio (chave, escudo, martelo). Derrete em 6 turnos.\n"
        "❄️ Resistência ao Frio: sobrevive no vácuo gelado. Stress acima 15°C, dano acima 40°C.\n\n"
        "🌟 *Nv10 — Sinfonia do Inverno:* Grito 4d8 gélido 15m. Falha Con = paralisa 2 turnos. "
        "Cria barricadas de gelo permanentes."
    ),
    "proturno": (
        "🧠 *PROTURNO — Domínio da Sombra*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Netuno (O Xadrez)\n\n"
        "Pele azulada, crânios alongados, cérebros como supercomputadores quânticos. "
        "Confrontam a \"Sombra\" da mente — medos e impulsos — para subjugá-la e "
        "projetar sua vontade sobre os outros.\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)-3\n"
        "For-1 | Des+0 | Con-1 | Int+2 | Sab+3 | Car+1\n\n"
        "⚡ *Habilidades:*\n"
        "🧠 Levantamento Mental: usa Int para mover/arremessar objetos até 50kg a 10m\n"
        "💀 Invasão da Sombra: 1d20+Sab vs alvo. Sucesso = controla próxima ação. "
        "Falha = 2 dano próprio por hemorragia.\n\n"
        "🌟 *Nv10 — Soberania Telepática:* Sem dano ao falhar controle. "
        "1x/DL, esmaga 3 inimigos simultaneamente: 5d10 dano inesquivável."
    ),
    "infimor": (
        "🪐 *INFIMOR — Titãs Esquecidos do Vácuo*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Planeta: Plutão (A Sentinela Ressentida)\n\n"
        "Quase 3 metros, membros de cartilagem hiperelástica que esticam até 10m. "
        "Não respiram, sobrevivem perfeitamente no vácuo. Vivem milhares de anos. "
        "Ressentimento profundo pelo rebaixamento a \"planeta anão\".\n\n"
        "📊 *Atributos:* Vida 4d6(tira menor)+3\n"
        "For+3 | Des-1 | Con+2 | Int+0 | Sab+0 | Car+0\n\n"
        "⚡ *Habilidades:*\n"
        "🌌 Imune ao Vácuo e asfixia\n"
        "🤏 Encolher: ½ altura, ½ desloc, vantagem absoluta em furtividade\n"
        "💪 Braços Telescópicos: ataques melee a 10m de alcance\n"
        "😡 Fúria dos Desclassificados: se ouvir que Plutão não é planeta → +2 tudo, "
        "+3 ataque/dano, mas não distingue aliado de inimigo por 5 turnos!\n\n"
        "🌟 *Nv10 — Colosso do Vácuo:* 5m altura, Fúria COM controle mental, "
        "+20PV temporários, ataques arremessam inimigos."
    ),
}

# ══════════════════════════════════════════════════════════
# CLASSES
# ══════════════════════════════════════════════════════════

CLASSES_DETAIL = {
    "estudioso": (
        "📚 *ESTUDIOSO — O Cofre de Conhecimento*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +4 | 🎯 Papel: perito em fraquezas e quebra-cabeças\n\n"
        "🎯 *Perícias:* Conhecimentos+4, Investigação+3, Mecânica+2, Tecnomancia+2, Persuasão+1\n\n"
        "🔹 *Mapa Mental (Passiva):* 1x/sessão, Mestre DEVE fornecer info sobre criatura/tech\n"
        "🔹 *Ponto Estrutural Crítico (1RAM):* próximo ataque = dano MÁXIMO dos dados\n\n"
        "🎒 *Equip:* Roupas Civis, Pistola EMP(1d4) ou Laser(1d6), Datapad, Bateria Fantasma"
    ),
    "mecanico": (
        "🔧 *MECÂNICO — Arquiteto da Sobrevivência*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +6 | 🎯 Papel: suporte defensivo, mestre de naves\n\n"
        "🎯 *Perícias:* Mecânica+5, Pilotagem+2, ArmBrancas+2, Tecnomancia+1, Persuasão+1, Sobrevivência+1\n\n"
        "🔹 *Operador Pesado (Passiva):* ignora penalidades de armaduras pesadas\n"
        "🔹 *Reparo Tático (Ativa):* aliado ganha 1d6+Mecânica PV temporários\n\n"
        "🎒 *Equip:* Traje Bordo(CD+2), Revólver Íons(1d8) ou Escopeta(2d6), Garras(1d4), Ferramentas"
    ),
    "assassino": (
        "🗡️ *ASSASSINO — A Sombra Silenciosa*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +8 | 🎯 Papel: dano explosivo, eliminação cirúrgica\n\n"
        "🎯 *Perícias:* Furtividade+4, ArmBrancas+2, ArmFogo+2, Espionagem+2, Medicina+1, Persuasão+1\n\n"
        "🔹 *Primeiro Corte (Passiva):* +2 acerto e DANO DOBRADO vs desprevenidos\n"
        "🔹 *Desaparecer (Ativa):* ao matar, rola furtividade grátis para se esconder\n\n"
        "🎒 *Equip:* Traje Furtivo(CD+1,+2Furt), Besta Phobos(1d8) ou SubMetra(2d4), Faca Plasma(1d4), Granada Fumaça"
    ),
    "soldado": (
        "🎖️ *SOLDADO — Baluarte de Fogo e Aço*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +10 | 🎯 Papel: linha de frente, tanque de fogo\n\n"
        "🎯 *Perícias:* ArmFogo+4, ArmBrancas+3, Explosivos+2, Pilotagem+1, Sobrevivência+1, Furtividade+1\n\n"
        "🔹 *Memória Muscular (Passiva):* sem penalidade de armas Pesadas\n"
        "🔹 *Fogo de Supressão (Ativa):* inimigo testa Sab ou desvantagem em tudo\n\n"
        "🎒 *Equip:* Colete(CD+2), Rifle Assalto(1d8) ou Escopeta(2d6), Faca Plasma(1d4), Kit Médico"
    ),
    "starlord": (
        "🌟 *STARLORD — A Voz de Comando*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +8 | 🎯 Papel: líder, inspirador, negociador\n\n"
        "🎯 *Perícias:* Persuasão+5, ArmFogo+2, Tecnomancia+2, Pilotagem+2, Furtividade+1\n\n"
        "🔹 *Charme Malandro (Passiva):* re-rola persuasão falhada 1x por encontro\n"
        "🔹 *\"Deixem comigo!\" (Ativa):* próximo aliado a atacar ganha Vantagem\n\n"
        "🎒 *Equip:* Roupas Elegantes, Pistola Laser(1d6), Faca Plasma(1d4)"
    ),
    "franco_atirador": (
        "🎯 *FRANCO-ATIRADOR — O Observador Letal*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +6 | 🎯 Papel: controle de campo à distância\n\n"
        "🎯 *Perícias:* ArmFogo+5, Sobrevivência+3, Furtividade+2, Investigação+2\n\n"
        "🔹 *Foco à Distância (Passiva):* +5 ataque >30m | apenas +2 se ≤30m\n"
        "🔹 *Tiro Incapacitante (Ativa):* ½ dano mas imobiliza 1 turno\n\n"
        "🎒 *Equip:* Colete(CD+2), Rifle Precisão(1d10), Bastão Choque(1d6), Binóculos Termais"
    ),
    "musico": (
        "🎵 *MÚSICO — Arquiteto de Frequências*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +4 | 🎯 Papel: buff/debuff via som, hacker psicológico\n\n"
        "🎯 *Perícias:* Tecnomancia+5, Performance+4, Persuasão+2, ArmBrancas+1\n\n"
        "🔹 *Ouvido Absoluto (Passiva):* +2CD vs controle mental e dano sônico\n"
        "🔹 *Frequência (Ativa):* aliados 10m ganham +2 dano OU inimigos 10m sofrem -2CD\n\n"
        "🎒 *Equip:* Roupas Civis, Pistola Laser(1d6), Instrumento Digital, Bateria Fantasma"
    ),
    "espiao": (
        "🕵️ *ESPIÃO — O Fantasma de Mil Rostos*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +4 | 🎯 Papel: infiltração social, extração de info\n\n"
        "🎯 *Perícias:* Espionagem+4, Persuasão+4, Furtividade+2, Acrobacia+1, Intimidação+1\n\n"
        "🔹 *Rosto na Multidão (Passiva):* Vantagem em persuasão/enganação com disfarce\n"
        "🔹 *Ponto Cego (Ativa):* mistura-se no ambiente, inimigos o ignoram\n\n"
        "🎒 *Equip:* Roupas Civis, Pistola Laser(1d6), Faca Plasma(1d4), 2 IDs Falsas"
    ),
    "catador": (
        "♻️ *CATADOR — Rei da Sucata*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +6 | 🎯 Papel: encontrar loot, reparar com pouco\n\n"
        "🎯 *Perícias:* Persuasão+3, Investigação+2, Sobrevivência+2, Mecânica+2, Pilotagem+2, ArmFogo+1\n\n"
        "🔹 *Olho para Ouro (Passiva):* 1d6, resultado 4-6 = item extra ao vasculhar\n"
        "🔹 *Desmanche Rápido (Ativa):* 1d8 dano + reduz CD permanente de robô/mecânico\n\n"
        "🎒 *Equip:* Traje Bordo(CD+2), Revólver Íons(1d8), Bastão Choque(1d6), Maçarico"
    ),
    "piloto": (
        "✈️ *PILOTO — O Coração da Nave*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +6 | 🎯 Papel: salvação em combate espacial\n\n"
        "🎯 *Perícias:* Pilotagem+5, Mecânica+2, Persuasão+2, Sobrevivência+2, ArmFogo+1\n\n"
        "🔹 *Instinto Evasivo (Passiva):* +2CD do veículo que pilota\n"
        "🔹 *Sobrecarga Propulsores (Ativa):* vantagem pilotagem evasiva, nave toma 1d4 dano\n\n"
        "🎒 *Equip:* Traje Bordo(CD+2), Revólver Íons(1d8) ou Escopeta(2d6), Chave Inglesa(1d4)"
    ),
    "batedor": (
        "👁️ *BATEDOR — A Vanguarda do Perigo*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +8 | 🎯 Papel: detetar ameaças, marca alvos\n\n"
        "🎯 *Perícias:* Sobrevivência+4, ArmFogo+3, Investigação+3, Furtividade+1, Explosivos+1\n\n"
        "🔹 *Sentidos Alertas (Passiva):* nunca surpreendido, +2 Iniciativa\n"
        "🔹 *Marca do Caçador (Ativa):* aliados sabem posição do alvo, ignoram cobertura\n\n"
        "🎒 *Equip:* Traje Furtivo(CD+1), SubMetra Flechetes(2d4), Faca Plasma(1d4), Granada Fumaça"
    ),
    "explorador": (
        "🗺️ *EXPLORADOR — Navegador das Rotas*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +6 | 🎯 Papel: guia de terreno, analista biológico\n\n"
        "🎯 *Perícias:* Investigação+4, Sobrevivência+4, Conhecimentos+3, Persuasão+1\n\n"
        "🔹 *Mapeamento Tático (Passiva):* grupo ignora terreno difícil em 10m\n"
        "🔹 *Vulnerabilidade Exposta (Ativa):* descobre fraqueza, +1d6 dano do grupo\n\n"
        "🎒 *Equip:* Colete(CD+2), Rifle Assalto(1d8), Scanner Ambiental, Corda 15m"
    ),
    "cinetico": (
        "⚡ *CINÉTICO — Ponte Mente-Máquina*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +4 | 🎯 Papel: tecnomante curador, manipulador cinético\n\n"
        "🎯 *Perícias:* Tecnomancia+5, Medicina+3, Resistência+2, Acrobacia+2\n\n"
        "🔹 *Bio-feedback (Passiva):* ao curar aliado com script, recupera 2PV próprio\n"
        "🔹 *Repulsão Cinética (1RAM):* empurra todos inimigos adjacentes 3m\n\n"
        "🎒 *Equip:* Roupas Civis, Pistola EMP(1d4), Deck Pulso, Bateria Fantasma, Kit Médico"
    ),
    "prospector": (
        "💼 *PROSPECTOR — O Rosto da Tripulação*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +4 | 🎯 Papel: negociador, gestor de créditos\n\n"
        "🎯 *Perícias:* Persuasão+5, Liderança+4, Tecnomancia+3\n\n"
        "🔹 *Contrato Lucrativo (Passiva):* +20% créditos em recompensas\n"
        "🔹 *\"Espere, podemos resolver!\" (Ativa):* inimigo hesita, perde Ação Principal 1 turno\n\n"
        "🎒 *Equip:* Roupas Luxo, Pistola Laser(1d6), Datapad, +100 CG extras (200 total)"
    ),
    "pirata": (
        "☠️ *PIRATA — O Terror do Vácuo*\n━━━━━━━━━━━━━━━━━━━━\n"
        "❤️ PV Base: +10 | 🎯 Papel: combate brutal curta distância, boarding\n\n"
        "🎯 *Perícias:* ArmFogo+3, ArmBrancas+3, Intimidação+3, Sobrevivência+2, Pilotagem+1\n\n"
        "🔹 *Brutalidade de Abordagem (Passiva):* sem penalidade espaço confinado, +1 dano em naves\n"
        "🔹 *Grito Saqueador (Ativa):* 5m, inimigos testam Sab ou Amedrontados 2 turnos\n\n"
        "🎒 *Equip:* Colete(CD+2), Escopeta Sônica(2d6), Bastão Choque(1d6), Arpéu, Granada Fumaça"
    ),
}

# ══════════════════════════════════════════════════════════
# ARSENAL — ARMAS BRANCAS
# ══════════════════════════════════════════════════════════

ARMAS_BRANCAS_TEXT = (
    "🗡️ *ARSENAL — ARMAS BRANCAS*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Ataque: 1d20 + For + Perícia | Dano: dado + For\n"
    "Armas *Ágeis* podem usar Des em vez de For.\n\n"
    "💀 *LEVES (1d4):*\n"
    "• Faca de Plasma — 40CG | Oculta, Ágil\n"
    "• Garras de Combate — 45CG | Aderência (+2 de cima), Ágil\n"
    "• Maçarico Laser — 60CG | Derretimento (ignora metal)\n"
    "• Soco Inglês — 35CG | Concussão (crítico=atordoa)\n\n"
    "⚔️ *MÉDIAS (1d6):*\n"
    "• Bastão de Choque — 50CG | Atordoante (max=perde mov)\n"
    "• Chicote Mono — 250CG | Alcance 3m, Ágil\n"
    "• Manopla Grav — 200CG | Impacto (empurra 2m)\n"
    "• Chave Inglesa — 20CG | Ferramenta (+2 vs robôs)\n"
    "• Arpéu Magnético — 90CG | Puxão 5m\n"
    "• Bastão Telescópico — 40CG | Oculta, Rápida\n"
    "• Katar Ven'y — 120CG | Tóxica (Con CD13, 1d6 2t)\n"
    "• Escudo-Lâmina — 100CG | Defensiva (+1CD vs tiros)\n\n"
    "🔥 *PESADAS (1d8):*\n"
    "• Espada Térmica — 150CG | Confiável\n"
    "• Lança Ven'y — 80CG | Ágil, arremessável 15m\n"
    "• Lâmina Marciana — 110CG | Aparar (+1CD 2 mãos)\n"
    "• Nunchaku Mono — 95CG | Ágil\n"
    "• Machado Sucata — 30CG | Despedaçador (supera 5CD=quebra)\n"
    "• Foice Deimos — 130CG | Sangramento\n\n"
    "💎 *RARAS (1d10+):*\n"
    "• Foice Diamante — 800CG | 1d10 Perfurante (-2CD armadura)\n"
    "• Alabarda Proturno — 350CG | 1d10 Alcance 3m\n"
    "• Lança Choque — 220CG | 1d10 Investida (vantagem)\n"
    "• Martelo Demolição — 180CG | 2d6 Destruidora (2x vs objetos)\n"
    "• Machado Cinético — 400CG | 2d8 Pesada (-2 acerto)\n"
    "• Martelo Sísmico — 1500CG | 1d20 Derrubar\n"
    "• Espadão Fusão — 2000CG | 2d12 Pesada, Queimadura"
)

# ══════════════════════════════════════════════════════════
# ARSENAL — ARMAS DE FOGO
# ══════════════════════════════════════════════════════════

ARMAS_FOGO_TEXT = (
    "🔫 *ARSENAL — ARMAS DE FOGO*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Ataque: 1d20 + Des + Perícia | Dano: dado + Des\n"
    "🔋 Pentes: 3 turnos de tiro. Rajada=2t. Recarregar=Ação Movimento.\n\n"
    "💀 *LEVES (1d4):*\n"
    "• Pistola EMP — 100CG | Anti-Sintético (3d4 vs robôs)\n"
    "• Lança-Chamas — 250CG | Área 3x3m\n"
    "• Sinalizadora — 25CG | Marcador (aliado=vantagem)\n"
    "• Dardos Tóxicos — 150CG | Silenciosa +1d6 veneno\n"
    "• Derringer — 120CG | Ultra-Oculta, 1º tiro=vantagem\n\n"
    "⚔️ *MÉDIAS (1d6-2d4):*\n"
    "• Pistola Laser — 60CG | 1d6 Saque Rápido\n"
    "• Besta Repetição — 180CG | 1d6 Rajada Silenciosa\n"
    "• Lança-Granadas — 300CG | 1d6 Explosão Área 3x3\n"
    "• Emissor Micro-ondas — 450CG | 1d6 Inesquivável (+1d6/t)\n"
    "• SubMetra Flechetes — 220CG | 2d4 Sangramento\n"
    "• Fuzil Estilhaços — 140CG | 2d4 Sangra cone 5m\n\n"
    "🔥 *PESADAS (1d8-1d12):*\n"
    "• Revólver Íons — 160CG | 1d8 Brutal (19-20 crítico)\n"
    "• Rifle Assalto — 200CG | 1d8 Rajada (2 alvos)\n"
    "• Carabina Terráquea — 130CG | 1d8 Confiável (sem falha)\n"
    "• Besta Phobos — 350CG | 1d10 Silenciosa\n"
    "• Rifle Laser — 280CG | 1d10 Perfurante (-1CD)\n"
    "• Rifle Precisão — 500CG | 1d12 Telescópica, Brutal\n"
    "• Arco Phobos — 300CG | 1d12 Usa FORÇA\n"
    "• Canhão Plasma — 650CG | 1d12 Sobreaquecimento\n\n"
    "💎 *ARTILHARIA (2d6+):*\n"
    "• Escopeta Sônica — 260CG | 2d6 Curto Alcance\n"
    "• Escopeta Rust — 300CG | 2d8 Descarregar (4d8)\n"
    "• Canhão Sônico — 800CG | 2d8 Cone 10m\n"
    "• Minigun — 900CG | 3d6 Pesada, Supressão\n"
    "• Canhão Antimatéria — 3500CG | 1d20 Artilharia\n"
    "• Rifle Gauss — 4500CG | 2d20 Atravessa Paredes"
)

# ══════════════════════════════════════════════════════════
# ARMADURAS
# ══════════════════════════════════════════════════════════

ARMADURAS_TEXT = (
    "🛡️ *ARMADURAS E TRAJES*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "CD = 10 + Mod.Des + Bônus Armadura\n\n"
    "👕 *LEVES* (soma toda Des):\n"
    "• Roupas Civis — 20CG | +0CD\n"
    "• Roupas Elegantes — 80CG | +0CD (status social)\n"
    "• Traje Furtivo Nanofibra — 250CG | +1CD, +2 Furtividade\n"
    "• Escudo Energia Pessoal — 800CG | +0CD, absorve 10 dano (recarrega DL)\n\n"
    "🦺 *MÉDIAS* (Des máx +2):\n"
    "• Colete Tático — 150CG | +2CD, bolsos magnéticos\n"
    "• Traje Bordo Atmosférico — 180CG | +2CD, imune vácuo/gases, O₂ 12h\n"
    "• Exoesqueleto Leve — 300CG | +4CD, -2 Furt/Acro, +50kg carga\n\n"
    "🏋️ *PESADAS* (NÃO soma Des):\n"
    "• Armadura Reativa Urak — 450CG | +3CD, reflete 1d4 térmico em melee\n"
    "• Armadura Eng. Conjupitera — 500CG | +4CD, -2 Furt, +2 Mecânica\n"
    "• Armadura Marciana — 650CG | +6CD, -4 Furt, exige For+2\n"
    "• Mecha-Suit Assalto — 3500CG | +8CD, sem esquiva, ignora queda"
)

# ══════════════════════════════════════════════════════════
# FERRAMENTAS E UTILITÁRIOS
# ══════════════════════════════════════════════════════════

FERRAMENTAS_TEXT = (
    "🛠️ *FERRAMENTAS E UTILITÁRIOS*\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "🏕️ *SOBREVIVÊNCIA:*\n"
    "• Kit Sobrevivência Base — 50CG (Comunicador, 3 rações, 2 luzes)\n"
    "• Tubo de Rações (3 dias) — 15CG\n"
    "• Luzes Químicas — 5CG\n"
    "• Comunicador de Pulso — 25CG\n"
    "• Corda Nanofibra (150m) — 20CG\n"
    "• Fita Isolante Espacial — 5CG\n\n"
    "💊 *MÉDICO:*\n"
    "• Kit Médico Batalha — 30CG (cura 1d8 PV)\n"
    "• Kit Primeiros Socorros — 20CG (estanca sangramento)\n\n"
    "💣 *TÁTICO:*\n"
    "• Granada de Fumaça — 35CG\n"
    "• Granada de Luz — 40CG (cega área 3x3m)\n"
    "• Scanner Ambiental — 60CG (venenos/radiação)\n"
    "• Binóculos Termais — 80CG\n\n"
    "🧠 *TECNOLOGIA:*\n"
    "• Bateria Fantasma — 30CG (recupera 1 RAM)\n"
    "• Deck Digital de Pulso — 100CG (interface Tecnomancia)\n"
    "• Datapad Pesquisa — 120CG (Estudiosos)\n"
    "• Datapad Corporativo — 80CG (logística)\n"
    "• Instrumento Musical Digital — 100CG (Músicos)\n\n"
    "🕵️ *INFILTRAÇÃO:*\n"
    "• Identidades Falsas — 150CG\n"
    "• Contratos + Caneta Digital — 15CG\n\n"
    "🍷 *DIVERSOS:*\n"
    "• Módulo Som Portátil — 25CG\n"
    "• Garrafa Contrabandista — 40CG (suborno/moral)"
)

# ══════════════════════════════════════════════════════════
# IMPLANTES CIBERNÉTICOS
# ══════════════════════════════════════════════════════════

IMPLANTES_TEXT = (
    "🦾 *IMPLANTES CIBERNÉTICOS*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ Limite seguro: 2 + Mod.Con\n"
    "1º extra: -1d6 PV máx + desvantagem social\n"
    "2º extra: curto-circuito em 1-2 natural\n"
    "3º extra: MORTE na cirurgia\n\n"
    "🧠 *CABEÇA:*\n"
    "• Chip Expansão RAM — 1500CG | +2 Slots RAM\n"
    "• Olho Biônico — 800CG | +2 ataque distância, ignora fumo/escuro\n"
    "• Interface Navegação — 1200CG | Vantagem manobras evasivas (Piloto)\n"
    "• Tradutor Universal — 600CG | +2 Persuasão, traduz qualquer idioma\n"
    "• Mira Preditiva — 950CG | Reduz penalidade sniper perto\n\n"
    "🫀 *TORSO:*\n"
    "• Placas Subdérmicas — 1100CG | +1CD permanente\n"
    "• Coração Sintético — 2500CG | +5PV máx, +2 vs venenos\n"
    "• Filtro Pulmonar — 750CG | Imune gases venenosos\n"
    "• Reator Adrenalina — 3000CG | 1x/dia Ação Principal extra\n"
    "• Bateria Interna — 2000CG | Gasta PV para conjurar sem RAM\n\n"
    "🦿 *MEMBROS:*\n"
    "• Braço Hidráulico — 850CG | +2 dano melee, Vantagem For\n"
    "• Estabilizador Pulso — 500CG | Sem penalidade armas pesadas\n"
    "• Lâmina Mantis — 1000CG | 1d8 oculta, dobra dano furtivo\n"
    "• Pernas Pneumáticas — 1500CG | 2x deslocamento, ignora queda 15m\n"
    "• Âncoras Magnéticas — 700CG | Imune derrubar, anda no teto"
)

# ══════════════════════════════════════════════════════════
# TECNOMANCIA
# ══════════════════════════════════════════════════════════

TECNO_BASICAS = (
    "🟢 *ROTINAS BÁSICAS (Nível 1)*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Requisito: Tecnomancia +1 ou +2\n\n"
    "⚡ *Custo 0 (cantrips):*\n"
    "1. *Ping* (livre) — interage com eletrônico a 10m. Apagar luzes, abrir portas.\n"
    "2. *Choque Estático* (principal) — 1d6 dano elétrico.\n"
    "3. *Query Neural* (principal) — lê último pensamento de cibernético (Int vs alvo).\n"
    "4. *Bateria Fantasma* (principal) — recarrega lanterna/comunicador por 1h.\n"
    "5. *Scanner de Frequência* (livre) — vê emissões Wi-Fi/rádio/Bluetooth em 50m.\n\n"
    "🔋 *Custo 1 RAM:*\n"
    "6. *Jammer Pessoal* (movimento) — bolha 10m, sem comunicação por 3 turnos.\n"
    "7. *Glitch Visual* (principal) — enche visor do alvo de pop-ups: -2 próximo ataque.\n"
    "8. *Trava Biométrica* (movimento) — tranca porta com seu DNA.\n"
    "9. *Rollback Celular* (principal) — cura 1d8+Int PV. Fecha cortes visualmente.\n"
    "10. *Firewall Ativo* (reação) — barreira hexagonal bloqueia 1d10+Int dano."
)

TECNO_INJECOES = (
    "🟡 *INJEÇÕES MALICIOSAS (Nível 2)*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Requisito: Tecnomancia +3 ou +4\n\n"
    "🔋 *Custo 1 RAM:*\n"
    "14. *Ejetar Pente* (reação) — força recarga do inimigo em pleno tiroteio.\n\n"
    "🔋🔋 *Custo 2 RAM:*\n"
    "11. *Travar Armamento* (principal) — trava arma inimiga por 1 turno.\n"
    "12. *Curto em Armadura* (principal) — -3CD por 2 turnos + 1d4 queimadura.\n"
    "13. *Hackear Implante Motor* (principal) — ½ desloc, sem esquivar por 3 turnos.\n"
    "15. *Cegueira Cibernética* (principal) — desliga olhos: cego 2t, desvantagem.\n"
    "16. *Drenar Escudos* (principal) — suga escudo inimigo → PV temporários próprios.\n"
    "17. *Sobrecarga Sistema* (principal) — 2d6 elétrico em área 3x3m.\n"
    "18. *Desativar Suporte Vida* (principal) — desliga O₂/aquecedores do traje.\n"
    "19. *Loop de Feedback* (reação) — anula script inimigo, gasta RAM dele.\n\n"
    "🔋🔋🔋 *Custo 3 RAM:*\n"
    "20. *Torreta Sentinela* (principal) — drone/torreta vira aliado por 3 turnos."
)

TECNO_PROTOCOLOS = (
    "🔴 *PROTOCOLOS DE SOBRESCRITA (Nível 3)*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Requisito: Tecnomancia +5 ou mais\n\n"
    "🔋🔋🔋 *Custo 3 RAM:*\n"
    "21. *Hackear Navegação* (principal) — controla nave inimiga por 1 turno.\n"
    "23. *Inverter Propulsores* (reação) — 3d8 dano estrutural ao casco inimigo.\n"
    "27. *Ejetar Piloto* (principal) — ejeta piloto de caça/mecha com explosão.\n\n"
    "🔋🔋🔋🔋 *Custo 4 RAM:*\n"
    "22. *Apagão do Motor* (principal) — desliga motor de nave, à deriva 1 turno.\n"
    "26. *EMP Localizado* (principal) — 10m desliga TUDO por 2t (só biologia funciona).\n"
    "28. *Reparo Estrutural* (principal) — 4d10 PV de cura para a NAVE.\n"
    "30. *Gravidade Zero Local* (principal) — 5x5m sem gravidade, desvantagem ataques.\n\n"
    "🔋🔋🔋🔋🔋 *Custo 5 RAM:*\n"
    "24. *Sobrecarga de Reator* (principal) — 2 turnos de contagem → 6d10 EXPLOSÃO.\n"
    "25. *Marionete Sintética* (principal) — controla ciborgue/androide por 3 turnos.\n"
    "29. *Formatar Mente* (principal) — 5d8 psíquico + apaga 24h de memória."
)

# ══════════════════════════════════════════════════════════
# NAVES
# ══════════════════════════════════════════════════════════

NAVES_TEXT = (
    "🚀 *FROTA ESTELAR*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "CD Nave: 10 + Manobrabilidade + Piloto\n"
    "⚡ Energia: dano normal | ⚡ EMP: 2x vs escudo, ½ vs casco | 💥 Balístico: +1 dado vs casco\n\n"
    "✈️ *CLASSE LIGEIRA:*\n"
    "• Caça Ligeiro — 15.000CG | Casco 30, Escudo 10, Man+4 | Plasma 3d6\n"
    "• Interceptador Furtivo — 45.000CG | Casco 40, Escudo 15, Man+3 | EMP 2d10\n"
    "• Veleiro Solar Sata — Raro | Casco 40, Escudo 25, Man+5 | Micro-ondas 3d8\n\n"
    "🚀 *CLASSE MÉDIA:*\n"
    "• Cargueiro Modificado — 60.000CG | Casco 60, Escudo 30, Man+1 | Torreta 3d8\n"
    "  _→ Nave inicial perfeita para o grupo!_\n"
    "• Nave de Prospecção — 90.000CG | Casco 80, Escudo 20, Man-1 | Laser 4d8\n\n"
    "⚔️ *CLASSE PESADA:*\n"
    "• Cruzador Proturno — Raro | Casco 70, Escudo 80, Man+0 | Íon 8d10\n"
    "• Corveta Militar — 190.000CG | Casco 100, Escudo 50, Man-1 | Mísseis 6d10\n"
    "• Bombardeiro Urak — Raro | Casco 120, Escudo 30, Man-3 | Sísmico 8d12\n"
    "• Fragata Marciana — 300.000CG | Casco 150, Escudo 40, Man-2 | Railgun 5d12\n\n"
    "💀 *CLASSE COLOSSAL:*\n"
    "• Encouraçado — INCOMPRÁVEL | Casco 300, Escudo 150, Man-4 | Plasma 10d20\n"
    "  _→ Inimigo de nível Chefe. O grupo invade, não enfrenta._"
)

# ══════════════════════════════════════════════════════════
# MODIFICAÇÕES DE ARMAS
# ══════════════════════════════════════════════════════════

MODIFICACOES_TEXT = (
    "🔧 *MODIFICAÇÕES DE ARMAS*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Slots: Simples=1 mod | Primárias=2 mods (máx 1 tecnomágica)\n"
    "Instalação: 1h (Descanso Curto) + teste Mecânica/Tecnomancia CD13\n\n"
    "🗡️ *CORPO A CORPO — Mecânica:*\n"
    "• Empunhadura Nanofibra — 150CG | Torna arma Ágil\n"
    "• Fio Serrilhado — 200CG | Adiciona Sangramento\n"
    "• Cabo Retrátil — 120CG | Torna Oculta\n"
    "• Haste Telescópica — 160CG | +3m Alcance\n"
    "• Injetor Fluídos — 100CG | Aplica veneno direto\n\n"
    "🗡️ *CORPO A CORPO — Tecnomancia:*\n"
    "• Motor Cinético — 250CG | Empurra 2m (Impacto)\n"
    "• Célula Choque — 300CG | Atordoa 1x/combate\n"
    "• Núcleo Superaquecido — 400CG | ½ dano vira fogo\n"
    "• Matriz Desestabilizadora — 450CG | 2x dano vs escudos\n"
    "• Cristal Sata — 600CG | Crítico = cura 1d4 PV\n\n"
    "🔫 *ARMAS DE FOGO — Mecânica:*\n"
    "• Pente Estendido — 150CG | Pente dura 4 turnos\n"
    "• Silenciador — 200CG | Torna Silenciosa\n"
    "• Cano Serrado — 100CG | +2 dano perto, -4 longe\n"
    "• Coronha Contrapeso — 200CG | Anula Pesada\n"
    "• Lança-Granadas Acoplado — 350CG | Dispara granadas\n\n"
    "🔫 *ARMAS DE FOGO — Tecnomancia:*\n"
    "• Mira Smart-Link — 500CG | Re-rola erro 1x\n"
    "• Conversor Térmico — 400CG | Dano vira fogo + queimadura\n"
    "• Capacitor EMP — 350CG | Anti-Sintético\n"
    "• Trava Biométrica — 250CG | Anti-roubo (choque no ladrão)\n"
    "• Câmara Magnética — 500CG | Perfurante (-1CD)"
)

# ══════════════════════════════════════════════════════════
# BESTIÁRIO
# ══════════════════════════════════════════════════════════

BESTIARIO_PLANETAS = (
    "👾 *BESTIÁRIO — CRIATURAS POR PLANETA*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Formato: Nome (HP, CD, Dano) — Habilidade\n\n"
    "🌍 *TERRA:*\n"
    "• Pirata Saqueador (15, 12, 1d6) — Matilha, foge com HP5\n"
    "• Mercenário Corp (45, 15, 1d8) — Granada de Luz\n"
    "• Comodoro Renegado (110, 16, 2x1d8) — Chama 1d4 reforços\n\n"
    "⚔️ *MARTE:*\n"
    "• Recruta Phobos (25, 13, 1d8) — Último ataque ao morrer\n"
    "• Legionário Deimos (55, 16, 1d12) — Endurecer -2 dano\n"
    "• Senhor da Guerra (140, 17, 3 ataques) — Cura 10PV em crítico\n\n"
    "🌿 *VÊNUS:*\n"
    "• Batedor Bruma (20, 13, 1d8) — Salto 6m com Hélio\n"
    "• Xamã de Gases (50, 14, 1d8) — Nuvem Argônio -2 dano\n"
    "• Predador Ápice (120, 14, 2x2d6) — Sopro veneno 3d6\n\n"
    "🔥 *MERCÚRIO:*\n"
    "• Corredor Deserto (18, 14, 1d4) — 18m desloc, fuga sem oportunidade\n"
    "• Assassino Poeira (40, 15, 2x1d6) — Regenera 5PV/turno\n"
    "• Ancião Relativístico (90, 17, 1d6+4) — 2 turnos antes de todos\n\n"
    "⚙️ *JÚPITER:*\n"
    "• Operário Mineração (30, 14, 2d6) — Imune empurrão\n"
    "• Eng. Combate (65, 16, 2d6) — Monta torreta 1d8\n"
    "• Barão Diamantes (150, 18, 2d10) — Singularidade 4d10\n\n"
    "💫 *SATURNO:*\n"
    "• Acólito Anel (20, 12, 1d4) — Cura 1d8 aliado\n"
    "• Inquisidor Genético (55, 15, 2d4) — Bloqueia cura 2t\n"
    "• Sacerdote Primordial (100, 16, dreno 2d8) — Ressuscita aliado\n\n"
    "❄️ *URANO:*\n"
    "• Ecoador (22, 13, 1d6) — Mímica voz (desvantagem 1º ataque)\n"
    "• Tecelão Frio (50, 14, 2d6) — Barricada gelo CD15 HP20\n"
    "• Maestro Zero (115, 15, elétrico) — Sinfonia 4d8 gélido 15m\n\n"
    "🧠 *NETUNO:*\n"
    "• Guarda Sombra (15, 12, 1d6) — 1d4 psíquico\n"
    "• Inquisidor Telepata (45, 14, 2d6) — Controle mental\n"
    "• Juiz Quântico (105, 16, 3d10) — Bloqueia RAM/ações extras 10m\n\n"
    "🪐 *PLUTÃO:*\n"
    "• Catador Exilado (35, 11, 1d6) — Ataque 10m furtivo\n"
    "• Esmagador (70, 13, 2d6) — Fúria abaixo 50%HP\n"
    "• Titã Esquecido (150, 14, 2d8) — Fase2 a 50%: cresce, +20PV"
)

BESTIARIO_FAUNA = (
    "🦎 *FAUNA ALIENÍGENA E QUIMERAS*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Espécies trazidas de sistemas vizinhos, mutadas pelo Caminho da Espiral.\n\n"
    "• Cão-Cego Eridani (18, 12, 1d6) — Matilha vantagem, sangramento, imune cegueira\n"
    "• Parasita Neural Tau Ceti (8, 14, 1d4) — Controla hospedeiro (Sab CD16)\n"
    "• Rastejador de Vidro (22, 15, 1d8) — Invisível, perfurante -2CD\n"
    "• Urso-Tanque Kepler (65, 16, 2d8) — Derruba, resiste armas leves\n"
    "• Morcego-Bomba Proxima (15, 11, voo) — Explode ao morrer: 2d6 fogo 3x3m\n"
    "• Sanguessuga Vácuo (10, 10, agarrar) — Drena bateria de implante/1d4 escudo\n"
    "• Mímico Carnal (40, 13, 1d10) — Disfarça-se de cano/painel, 1º ataque=crítico\n"
    "• Enxame Ferrugem (35, 12, auto) — Corrói metal: -1CD permanente\n"
    "• Devorador Fósforo (45, 14, 2d6) — Luz cegante, desvantagem ranged\n"
    "• Leviatã de Fosso (120, 18, 3d10) — Emerge, engole inteiro (Des CD16)\n"
    "• Quimera Alfa (85, 17, 2d8) — Brutal 19-20, regenera 1d8 (não com fogo/ácido)\n\n"
    "🌿 *FLORA PERIGOSA (Armadilhas):*\n"
    "• Musgo Necrótico — 1d4 ácido/turno ao tocar\n"
    "• Lírio-Ímã — EMP natural, desativa implantes 1d4 turnos\n"
    "• Árvore-Pulmão — Ar alucinógeno (Con CD14 ou atordoado)\n"
    "• Vinhas Tungstênio — Presa (Des CD15), só Derretimento/Despedaçador corta\n"
    "• Orquídea de Sangue — Droga: +2 For/Des 1h, perde 1PV máx permanente"
)

BESTIARIO_VAZIO = (
    "👾 *CRIAS DO VAZIO — PASSAGEM SOMBRIA*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Seres de outra dimensão. Desafiam biologia e tecnologia.\n\n"
    "💀 *COMUNS E LACAIOS:*\n"
    "• Sanguessuga Estelar (30, 12, 1d6) — Drena 2PV + 1RAM a 5m\n"
    "• Enxame Adaptativo (15 cada, 12, 1d4) — Evolui: -3 do tipo de dano recebido\n\n"
    "⚔️ *ELITES:*\n"
    "• Falso Aliado/Mímico (50, 13, 1d8) — Absorve aparência ao matar. Só Investigação detecta.\n"
    "• Espectro do Vácuo (45, 16, 1d10 psi) — IMUNE a dano físico. Só energia/tecnomancia.\n"
    "• Tecelão de Fendas (50, 14, portais) — Redireciona tiros para aliados via portal\n"
    "• Terror Subterrâneo (70, 14, 2d6) — Emerge sob jogador, derruba\n\n"
    "🔥 *FORTES:*\n"
    "• Olho do Abismo (60, 13, 3d8 linha) — Imóvel, escudo frontal ½ dano\n"
    "• Silenciador Cósmico (65, 15, 1d8) — Desliga TODA tecnomancia/implantes em 15m\n"
    "• Bocarra Corrosiva (55, 12, 2d8 ácido) — Sangue cáustico (-1CD melee), explode ao morrer\n\n"
    "💀 *CHEFES:*\n"
    "• Devorador de Mundos (80→∞, 14, 2d6) — Cresce ao comer: +10HP +1dano cada\n"
    "• Colecionador de Matrizes (110, 15, 2d8) — Absorve perícias/armas ao matar\n"
    "• Soberana da Ruína (180, 17, 2d8 psi) — Invoca 1d4 enxames/turno, controle mental CD16"
)

# ══════════════════════════════════════════════════════════
# FILOSOFIAS
# ══════════════════════════════════════════════════════════

FILOSOFIAS_TEXT = (
    "📜 *FILOSOFIAS DE VIDA*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Escolhida no Nível 1. Define a bússola moral e concede 1 habilidade.\n\n"
    "🌌 *CAMINHOS (Místicos):*\n"
    "🗣️ *Voz:* 1x/DL, impõe desvantagem no teste de resistência do alvo em Car. "
    "Ou finge-se de morto enganando scanners.\n"
    "🌀 *Ressonância:* 1x/DC, ignora escuridão total, sente vivos em 10m por 1 turno.\n"
    "⚙️ *Engrenagem:* 1x/DL, transforma falha crítica (1 natural) em falha comum.\n"
    "🧬 *Espiral:* Toda cura (kit/DC) rola com Vantagem.\n"
    "💍 *Anel:* 1x/DL, ao chegar a 0PV, fica com 1PV até próximo turno.\n"
    "🌑 *Ocaso:* 1x/combate, sofre 1d4 dano verdadeiro, soma 1d4 em qualquer rolagem.\n\n"
    "⚙️ *CÓDIGOS (Seculares):*\n"
    "🏕️ *Sobrevivente:* +2 Iniciativa permanente. 1x/DL age na rodada surpresa.\n"
    "💰 *Corporativo:* Vantagem em avaliar itens, achar loot oculto, negociar.\n"
    "🧊 *Cético:* +2CD vs psíquico/controle/intimidação.\n"
    "🐺 *Fronteira:* +1 ataque se sem aliado em 5m.\n"
    "🛡️ *Caserna:* 1x/DC, reação: leva dano no lugar de aliado adjacente.\n"
    "🃏 *Vira-Lata:* 1x/combate, distrai inimigo 3m, ataca com vantagem."
)
