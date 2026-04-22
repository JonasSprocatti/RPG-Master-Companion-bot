# 🌌 Passagem Sombria — RPG Master Companion Bot

Bot do Telegram que atua como Mestre de RPG para o universo **Passagem Sombria**, usando **Google Gemini** como IA narrativa e **Supabase** como banco de dados.

> **Filosofia:** Bot = lógica, dados, estado, DB. IA = narração. Zero alucinação em mecânicas.

---

## 🏗️ Arquitetura v2.2

| Arquivo | Função |
|---|---|
| `bot.py` | Lógica principal, criação estática, interceptor de estado, state machine |
| `glossary.py` | Dados mecânicos (stats raças/classes) + textos do glossário offline (0 tokens) |
| `glossary_additions.py` | Dados estruturados de tecnomancias (30 scripts) e implantes (15) para botões |
| `rpg_content.txt` | Referência compacta para o Gemini (regras, bestiário, XP) |
| `setup_supabase.sql` | Schema SQL v2 (fichas 1:N, fichas_ativas, sessões) |
| `Dockerfile` | Container para deploy |
| `requirements.txt` | Dependências Python |

### Separação de Responsabilidades

| Responsabilidade | Quem faz |
|---|---|
| Criar fichas, rolar dados, calcular PV/CD/RAM | **Bot** (Python `random.randint`) |
| Distribuir atributos, escolher arma, dar nome | **Jogador** (botões inline) |
| Narrar aventuras, controlar NPCs, pedir testes | **IA** (Gemini) |
| Conceder XP, causar dano, dar itens | **IA** (via tags) → **Bot** (intercepta e salva no DB) |
| Persistir estado (fichas, sessões, XP) | **Bot** (Supabase = fonte da verdade) |

---

## 🚀 Setup

### 1. Telegram
Fale com [@BotFather](https://t.me/BotFather) → `/newbot` → guarde o token.

### 2. Gemini
[aistudio.google.com](https://aistudio.google.com) → API Key (free: 15 req/min, 1000/dia).

### 3. Supabase
[supabase.com](https://supabase.com) → novo projeto → **SQL Editor** → cole `setup_supabase.sql` → Run.
Chaves em: Settings → API Keys → aba "Legacy anon" → copie a `eyJ...`.

### 4. Render
[render.com](https://render.com) → Web Service → Docker → conecte o repo GitHub.

**Environment Variables:**

| Variável | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token do BotFather |
| `GEMINI_API_KEY` | Chave do Google AI Studio |
| `SUPABASE_URL` | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | Chave legacy anon (`eyJ...`) |
| `WEBHOOK_URL` | URL do serviço Render |
| `ADMIN_ID` | Seu Telegram ID ([@userinfobot](https://t.me/userinfobot)) |

---

## 🎮 Comandos

| Comando | Descrição |
|---|---|
| `/start` | Menu principal com botões |
| `/iniciar` | Seleciona personagem ativo para a sessão |
| `/novojogo` | Nova aventura ou continuar com contexto |
| `/criarpersonagem` | Criação 100% estática com botões |
| `/rolar NdN` | Rola dados reais (`/rolar 1d20`) |
| `/regras` | Resumo rápido das mecânicas |
| `/ficha` | Mostra ficha ativa (offline) |
| `/fichas` | Lista todos os seus personagens |
| `/deletarficha ID` | Deleta ficha (admin pode deletar de outros) |
| `/levelup` | Sobe de nível com botões (XP + Descanso Longo) |
| `/implante` | Gerencia implantes cibernéticos (compra/instala com botões) |
| `/salvarsessao` | IA resume e salva sessão no banco |
| `/sessoes` | Lista sessões salvas |
| `/cargarsessao ID` | Retoma sessão |
| `/contexto` | Importa sessão jogada fora do bot |
| `/glossario` | Banco de dados completo (0 tokens) |
| `/reset` | Limpa sessão (fichas permanecem) |

---

## 📖 Glossário Interativo (Offline)

```
📖 Glossário
├── 🌌 Raças (9, cada uma clicável com detalhes)
├── ⚔️ Classes (15, cada uma clicável)
├── 🗡️ Armas Brancas (25 com preço/dano/efeito)
├── 🔫 Armas de Fogo (25)
├── 🛡️ Armaduras (11)
├── 🦾 Implantes Cibernéticos (15)
├── 🧠 Tecnomancia → Básicas / Injeções / Protocolos (30 scripts)
├── 🚀 Naves (10 com stats)
├── 🛠️ Ferramentas (22 itens)
├── 🔧 Modificações de Armas (20 mods)
├── 📜 Filosofias (12 caminhos/códigos)
└── 👾 Bestiário → Planetas / Fauna / Crias do Vazio
```

---

## 🧑‍🚀 Criação de Personagem (100% Estática)

Toda rolagem e cálculo feito por `random.randint()` do Python. IA não participa.

1. **Raça** → 9 botões
2. **Classe** → 15 botões
3. **Filosofia** → 12 botões
4. **Atributos** → Bot rola 2d8×7 (máx 16), descarta menor, jogador distribui tocando valores
5. **Cálculos** → PV, CD, RAM, perícias, iniciativa (automático)
6. **Equipamento** → Botão se houver escolha de arma
7. **Bônus Terráqueo** → Botões para +4 atributos (máx +2 cada) e +3 perícias livres
8. **Nome** → Jogador digita
9. **Tecnomancias** → Se classe tem Tecnomancia ≥ 1, botões para escolher scripts iniciais (Nível + Perícia, mín 3)
10. **Auto-save** → Salva no Supabase + ativa para sessão

---

## ⬆️ Level Up (Botões)

Requer **XP suficiente + Descanso Longo**. Dado de vida rolado em Python.

1. Bot verifica XP e descanso
2. Rola dado de vida automaticamente
3. **Botões para +1 Atributo** (mostra valor atual → novo)
4. **Botões para +1 Perícia** (mostra todas disponíveis com valores)
5. RAM +1 em níveis ímpares (automático)
6. Avisa a IA sobre novas capacidades

---

## 🧠 Tecnomancias

Na criação, personagens com Tecnomancia ≥ 1 escolhem scripts iniciais por botões. No level up, se ganharam slot novo (Nível + Perícia), aparecem novos scripts para escolher.

Scripts são organizados por tier: Básicas (+1/+2), Injeções (+3/+4), Protocolos (+5+). O tier máximo disponível depende do valor da perícia Tecnomancia.

A IA pode conceder/remover scripts via `[TECNO_ADD:id:alvo]` e `[TECNO_DEL:id:alvo]`.

---

## 🦾 Implantes Cibernéticos (`/implante`)

Interface completa por botões: Cabeça → Torso → Membros. Mostra preço, verifica créditos, aplica mecânica (bônus CD, PV, RAM).

Limite seguro: `2 + Mod.Constituição`. Acima do limite o bot avisa do risco e pede confirmação. 3º acima = bloqueado (morte instantânea).

A IA pode instalar implantes via `[IMPL:id:alvo]`.

---

## 📡 Interceptor de Estado

A IA inclui tags estruturadas no final de cada resposta. O Bot parseia, atualiza o banco e remove as tags antes de mostrar ao jogador.

**Tags suportadas:**

| Tag | Exemplo | Efeito |
|---|---|---|
| `[XP:valor:alvo:motivo]` | `[XP:25:todos:Derrotou pirata]` | Soma XP, verifica level up |
| `[HP:valor:alvo]` | `[HP:-5:Jonas]` | Atualiza PV (dano ou cura) |
| `[ITEM_ADD:nome:alvo]` | `[ITEM_ADD:Pistola:Jonas]` | Adiciona ao inventário |
| `[ITEM_DEL:nome:alvo]` | `[ITEM_DEL:Granada:Maria]` | Remove do inventário |
| `[CG:valor:alvo]` | `[CG:-100:Jonas]` | Altera créditos |
| `[RAM:valor:alvo]` | `[RAM:-2:Jonas]` | Gasta/recupera RAM |
| `[TECNO_ADD:id:alvo]` | `[TECNO_ADD:firewall:Jonas]` | Aprende script |
| `[TECNO_DEL:id:alvo]` | `[TECNO_DEL:ping:Jonas]` | Perde script |
| `[IMPL:id:alvo]` | `[IMPL:olho:Jonas]` | Instala implante |
| `[ATTR:atrib:valor:alvo]` | `[ATTR:forca:+1:Jonas]` | Altera atributo |
| `[PER:pericia:valor:alvo]` | `[PER:furtividade:+1:Jonas]` | Altera perícia |

O matching de nomes é **case-insensitive e accent-insensitive** (ex: "jonas" = "Jonas" = "Jonás").

Após sync, o bot mostra:
```
📡 Sync:
✨ +25XP Jonas (75/100)
🩸 Jonas: -5PV → ❤️ 10/15
🎒 Jonas +Pistola Laser
```

---

## 🗄️ Banco de Dados (Supabase)

### Tabela `fichas` (1:N)
Sem constraint UNIQUE — um jogador pode ter múltiplas fichas. Campos granulares: `atributos`, `pericias`, `tecnomancias`, `inventario`, `implantes` como JSONB individuais.

### Tabela `fichas_ativas`
UNIQUE(user_id, chat_id) — define qual ficha cada jogador está usando na sessão atual.

### Tabela `sessoes`
Registros de aventura com título e resumo gerado pela IA.

---

## 🔒 Isolamento

Cada chat/grupo é um universo separado. Fichas, sessões e contexto do Gemini são isolados por `chat_id`.

## 🛡️ Admin

`ADMIN_ID` pode deletar fichas de qualquer jogador via `/deletarficha ID`.

## 🔧 Local

```bash
export TELEGRAM_TOKEN="..." GEMINI_API_KEY="..." SUPABASE_URL="..." SUPABASE_KEY="..."
python bot.py
```
Sem `WEBHOOK_URL` roda em polling.

---

## 📊 Sistema de XP

| Nível | XP | Fontes |
|---|---|---|
| 1→2 | 100 | Lacaio 15-25, Decisão 25-50 |
| 2→3 | 250 | Elite 40-60, Puzzle 20-40 |
| 3→4 | 450 | Chefe 100-150, Missão 50-100 |
| 4→5 | 700 | Super 200-300, Lore 30-50 |
| 5→6 | 1.000 | Vazio +50% bônus |
| 6→7 | 1.400 | |
| 7→8 | 1.900 | |
| 8→9 | 2.500 | |
| 9→10 | 3.200 | |

---

## 📝 Créditos

- **RPG:** Passagem Sombria — RPG Espacial © 2026 Jonas Antonio da Silva Sprocatti
- **Bot:** Desenvolvido com Claude (Anthropic) + Gemini (Google) + Supabase
- **Licença do RPG:** CC BY-NC-ND 4.0
