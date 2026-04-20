# 🌌 Passagem Sombria — RPG Master Companion Bot

Bot do Telegram que atua como Mestre de RPG para o universo **Passagem Sombria**, usando **Google Gemini** como IA narrativa e **Supabase** para persistência de dados.

> **Filosofia:** Toda mecânica (rolagens, cálculos, fichas) é feita em código Python. A IA só narra e mestra. Zero alucinação em dados.

## 🏗️ Arquitetura

| Arquivo | Função |
|---|---|
| `bot.py` | Lógica principal, handlers, criação de personagem estática, state machine |
| `glossary.py` | Dados mecânicos (stats de raças/classes) + textos do glossário (offline, 0 tokens) |
| `rpg_content.txt` | Referência compacta para o Gemini (regras, bestiário, XP) |
| `Dockerfile` | Container para deploy |
| `requirements.txt` | Dependências Python |
| `setup_supabase.sql` | Script SQL para criar as tabelas no Supabase |

## 🚀 Setup Completo

### 1. Bot do Telegram
1. Fale com [@BotFather](https://t.me/BotFather) → `/newbot`
2. Guarde o **token**

### 2. API do Gemini
1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Crie uma **API Key** (plano gratuito: 15 req/min, 1000/dia)

### 3. Supabase (Banco de Dados)
1. Acesse [supabase.com](https://supabase.com) e crie um projeto
2. Vá em **SQL Editor** → cole o conteúdo de `setup_supabase.sql` → Run
3. Pegue as chaves em:
   - **Settings → General** → Project URL
   - **Settings → API Keys** → aba "Legacy anon, service_role" → chave `anon` (`eyJ...`)

### 4. Deploy no Render
1. Suba todos os arquivos no GitHub
2. No [Render](https://render.com), crie um **Web Service** conectado ao repo
3. Configuração:
   - **Language:** Docker
   - **Branch:** main
4. **Environment Variables:**

| Variável | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token do BotFather |
| `GEMINI_API_KEY` | Chave do Google AI Studio |
| `SUPABASE_URL` | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | Chave `anon` legacy (`eyJ...`) |
| `WEBHOOK_URL` | URL do seu serviço Render |
| `ADMIN_ID` | Seu Telegram ID numérico ([@userinfobot](https://t.me/userinfobot)) |

5. Deploy!

## 🎮 Comandos

### ⚔️ Jogo
| Comando | Descrição |
|---|---|
| `/start` | Menu principal com botões interativos |
| `/novojogo` | Inicia nova aventura narrada pela IA |
| `/criarpersonagem` | Criação de personagem com botões (100% estática) |
| `/rolar NdN` | Rola dados reais (ex: `/rolar 1d20`, `/rolar 4d6`) |
| `/regras` | Resumo rápido das regras |

### 💾 Ficha e Progressão
| Comando | Descrição |
|---|---|
| `/salvar` | Exporta ficha do Gemini e salva no Supabase |
| `/carregar` | Carrega ficha salva e injeta na sessão |
| `/ficha` | Mostra ficha salva (offline) |
| `/fichas` | Lista fichas do grupo |
| `/levelup` | Sobe de nível (verifica XP + Descanso Longo) |
| `/deletarficha` | Deleta sua ficha (admin pode deletar de outros) |

### 📚 Sessões
| Comando | Descrição |
|---|---|
| `/salvarsessao` | IA resume a sessão e salva no banco |
| `/sessoes` | Lista sessões salvas |
| `/cargarsessao ID` | Retoma sessão pelo ID |
| `/contexto` | Importa sessão jogada fora do bot |

### 📖 Referência
| Comando | Descrição |
|---|---|
| `/glossario` | Banco de dados completo (0 tokens de IA) |
| `/ajuda` | Lista todos os comandos |
| `/reset` | Limpa sessão (fichas/sessões permanecem) |

## 📖 Glossário Interativo (100% Offline)

O `/glossario` abre um menu de botões com **TODO** o conteúdo do RPG sem gastar tokens:

```
📖 Glossário
├── 🌌 Raças (9 raças com página individual clicável)
├── ⚔️ Classes (15 classes com página individual clicável)
├── 🗡️ Armas Brancas (25 armas com preço/dano/efeito)
├── 🔫 Armas de Fogo (25 armas)
├── 🛡️ Armaduras (11 armaduras)
├── 🦾 Implantes Cibernéticos (15 implantes)
├── 🧠 Tecnomancia → Básicas / Injeções / Protocolos (30 scripts)
├── 🚀 Naves (10 naves com stats completos)
├── 🛠️ Ferramentas e Utilitários (22 itens)
├── 🔧 Modificações de Armas (20 mods)
├── 📜 Filosofias de Vida (12 caminhos/códigos)
└── 👾 Bestiário → Planetas / Fauna / Crias do Vazio
```

## 🧑‍🚀 Criação de Personagem

**100% em código Python** — sem IA, sem alucinações de dados.

Fluxo com botões interativos:
1. **Raça** → 9 botões clicáveis
2. **Classe** → 15 botões clicáveis
3. **Filosofia** → 12 botões clicáveis
4. **Atributos** → Bot rola 2d8×7 em Python (máx 16), descarta menor, jogador distribui tocando em valores
5. **Cálculos automáticos** → PV, CD, RAM, perícias, iniciativa (tudo em Python)
6. **Equipamento** → Botão se houver escolha de arma
7. **Nome** → Jogador digita
8. **Auto-save** → Salva automaticamente no Supabase

Dados rolados por `random.randint()` do Python, nunca pela IA.

## 📊 Sistema de XP

A IA concede XP automaticamente durante o jogo:

| Nível | XP necessário | Fonte | XP |
|---|---|---|---|
| 1→2 | 100 | Lacaio derrotado | 15-25 |
| 2→3 | 250 | Elite derrotado | 40-60 |
| 3→4 | 450 | Chefe derrotado | 100-150 |
| 4→5 | 700 | Missão completa | 50-100 |
| 5→6 | 1.000 | Decisão importante | 25-50 |
| 6→7 | 1.400 | Descoberta de lore | 30-50 |
| 7→8 | 1.900 | Roleplay excepcional | 10-25 |
| 8→9 | 2.500 | Cria do Vazio | +50% bônus |
| 9→10 | 3.200 | | |

Level up requer **XP suficiente + Descanso Longo**. O dado de vida é rolado em Python.

## 🔒 Isolamento por Chat

Cada chat/grupo é um universo separado:
- Fichas salvas com `chat_id` — Grupo A nunca vê dados do Grupo B
- Sessões isoladas por chat
- Contexto do Gemini separado por chat

## 🛡️ Admin

O `ADMIN_ID` pode:
- Deletar fichas de qualquer jogador (`/deletarficha NomeJogador`)
- Jogadores comuns só podem deletar sua própria ficha

## 🔧 Rodando Localmente

```bash
export TELEGRAM_TOKEN="..."
export GEMINI_API_KEY="..."
export SUPABASE_URL="..."
export SUPABASE_KEY="..."
python bot.py
```

Sem `WEBHOOK_URL`, roda em modo polling (ideal para testes).

## 📝 Créditos

- **RPG:** Passagem Sombria — RPG Espacial © 2026 Jonas Antonio da Silva Sprocatti
- **Bot:** Desenvolvido com Claude (Anthropic) + Gemini (Google) + Supabase
- **Licença do RPG:** CC BY-NC-ND 4.0
