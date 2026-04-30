# 🌌 Passagem Sombria — RPG Master Companion Bot

Bot Telegram para RPG de mesa no universo **Passagem Sombria**. Gemini narra, Supabase persiste, Python controla tudo.

**Filosofia:** Bot = lógica/cálculos/estado. IA = narração/NPCs. Banco = verdade.

🌐 [Página do Projeto](https://rpg-master-companion-bot.onrender.com) | 🤖 [Iniciar conversa](https://t.me/PassagemSombria_bot)

---

## 📁 Arquivos

| Arquivo | Função |
|---|---|
| `bot.py` (~2400 linhas) | Core completo: handlers, SYSP, interceptor, criação, combate, GIFs, tracing |
| `glossary.py` (170 linhas) | Dados mecânicos (30 scripts, 15 implantes, stats) + labels de botão |
| `data_loader.py` (95 linhas) | Carrega dados_rpg do Supabase → memória, fallback glossary.py |
| `rpg_content.txt` (47 linhas) | Regras mecânicas d20 injetadas no prompt do Gemini |
| `setup_supabase.sql` | Schema: fichas, fichas_ativas, sessoes, inventario_grupo |

---

## 🔌 Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `TELEGRAM_TOKEN` | Token do @BotFather |
| `GEMINI_API_KEY` | Chave Google AI Studio |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon do Supabase |
| `WEBHOOK_URL` | URL do Render (sem ela = polling local) |
| `ADMIN_ID` | Telegram ID do admin (habilita GODMODE, /painel, /guiar) |
| `TENOR_API_KEY` | Chave do Tenor para GIFs animados |

---

## 🗄️ Banco de Dados

### Tabelas

**`fichas`** — Personagens (1:N por jogador). Campos: atributos, pericias, tecnomancias, inventario, implantes (todos JSONB).

**`fichas_ativas`** — UNIQUE(user_id, chat_id). Define qual ficha cada jogador usa. Persiste entre sessões.

**`sessoes`** — Resumos de aventura com título e transcript.

**`inventario_grupo`** — Baú da nave. Um registro JSONB por chat_id.

**`dados_rpg`** — Dados estáticos: stats, textos de glossário, regras. Editável pelo dashboard sem redeploy.

---

## 🎮 Fluxo de Jogo

### 1. Lobby (`/novojogo` ou `/iniciar`)

```
🌌 LOBBY DE SESSÃO
━━━━━━━━━━━━━━━━━━━━
Tripulação confirmada:
  ✅ Jonas → Grovax (Marciano Soldado Nv3)
  ✅ Bergah → Zeb (Terráqueo Explorador Nv2)
👥 2 jogador(es) pronto(s)

[🧑‍🚀 Selecionar Meu Personagem]
[🆕 Nova Aventura]  [📜 Continuar]
```

Cada jogador toca 🧑‍🚀, seleciona ficha, lobby atualiza. Mestre toca "Nova Aventura" quando todos estiverem prontos.

### 2. Boot do Mestre

```
⚙️ BOOT DO MESTRE
━━━━━━━━━━━━━━━━━━━━
🧹 Memória anterior: PURGADA (47 msgs removidas)
🧠 IA: Nova instância (histórico zerado)
📋 Fichas injetadas: 3 (Grovax, Zeb, Sh'Bihl)
✅ Sistema: ONLINE
```

`chats.pop(cid)` purga o Gemini. `gc(cid)` cria instância limpa. Fichas injetadas como contexto.

### 3. Mensagem do Jogador → IA

```
on_msg() recebe texto
  ├── /1d20p5 → Regex dice → calcula → injeta na IA
  ├── GODMODE → [GODMODE] ordem → IA acata
  ├── jogo_ativo=False → Aviso amigável (cooldown 5min)
  ├── sem ficha → Aviso pessoal
  └── Jogo normal:
        ├── [Usuário: @nick | Personagem: Nome] diz: texto
        ├── ask(Gemini) → resposta
        ├── intercept_and_sync() → extrai tags → atualiza DB
        ├── GIF_RE → busca Tenor → send_animation
        ├── [ESCUTANDO] → silêncio (jogadores conversando)
        └── Mostra resposta limpa
```

### 4. Interceptor de Estado

11 tags parseadas por regex em cada resposta da IA:

| Tag | Efeito no DB |
|---|---|
| `[XP:valor:alvo:motivo]` | Soma XP, verifica level up |
| `[HP:valor:alvo]` | Altera pv_atual |
| `[ITEM_ADD:nome:alvo]` | Adiciona inventário |
| `[ITEM_DEL:nome:alvo]` | Remove inventário |
| `[CG:valor:alvo]` | Altera créditos |
| `[RAM:valor:alvo]` | Altera ram_atual (OBRIGATÓRIO em scripts com custo>0) |
| `[TECNO_ADD:id:alvo]` | Aprende script |
| `[TECNO_DEL:id:alvo]` | Perde script |
| `[IMPLANTE_ADD:id:alvo]` | Cirurgia autônoma com cálculos de tolerância |
| `[ATTR:atrib:valor:alvo]` | Altera atributo |
| `[PER:pericia:valor:alvo]` | Altera perícia |

---

## 🎲 Rolagem de Dados

Regex: `/(\\d*)d(\\d+)(?:([pm+-])(\\d+))?`

| Formato | Resultado | Clicável no Telegram? |
|---|---|---|
| `/1d20p9` | 1d20+9 | ✅ inteiro |
| `/1d20+5` | 1d20+5 | ⚠️ parcial |
| `/2d8m1` | 2d8-1 | ✅ |

A IA **calcula o número real** consultando a ficha e escreve `/1d20p9` (NUNCA `/1d20pmod_tecnomancia`). O bot rola, mostra resultado e injeta `[SISTEMA: Personagem rolou...]` na IA.

### Perícias que NÃO existem

A IA é proibida de inventar perícias. "Psionismo" não existe. Poderes do Proturno usam:
- Levantamento Mental → teste de Inteligência pura
- Invasão da Sombra → disputa de Sabedoria

---

## 🧠 Tecnomancia e RAM

**30 scripts** organizados em 3 tiers:
- +1 a +3 → Básicas (10 scripts, inclui Bateria Fantasma)
- +4 a +6 → +Injeções (10 scripts)
- +7+ → +Protocolos (10 scripts)

**Consumo de RAM é obrigatório.** A IA DEVE incluir `[RAM:-X:nome]` sempre que um script com custo>0 for usado. O interceptor atualiza `ram_atual` no banco.

---

## 🧑‍🚀 Criação de Personagem

100% por botões. 10 etapas: Raça → Classe → Filosofia → Atributos (2d8×7) → PV (4d6) → Equipamento → [Terráqueo: +4 attr +3 per] → Nome → [Tecnomancia: seleção de scripts] → Auto-save.

Habilidades montadas automaticamente: Racial + Classe + Filosofia.

---

## 🗺️ Comandos

### Jogador
| Comando | Descrição |
|---|---|
| `/start` | Menu principal |
| `/iniciar`, `/novojogo` | Lobby de sessão |
| `/criarpersonagem` | Criação por botões |
| `/importar` | Importa ficha via template |
| `/ficha` | Ficha com barras visuais + inventário clicável |
| `/fichas` | Lista todas |
| `/deletarficha ID` | Deleta |
| `/levelup` | Level up com botões (atributo + perícia + script) |
| `/implante` | Gerencia implantes por botão |
| `/rolar` | Menu de rolagem rápida por botão |
| `/rolar_oculto` | Rolagem secreta (PV do bot → só mestre e IA veem) |
| `/1d20p5` | Rola dado direto |
| `/grupo` | HUD da mesa (status de todos) |
| `/bau`, `/nave` | Baú da nave (inventário compartilhado) |
| `/glossario` | Banco de dados offline |
| `/regras` | Referência rápida |
| `/salvarsessao` | Salva sessão (baseada em 50 msgs reais) |
| `/sessoes` | Lista sessões |
| `/cargarsessao ID` | Retoma sessão |
| `/contexto texto` | Importa contexto manual |
| `/gif termo` | Busca GIF animado |
| `/setimagem URL` | Define avatar do personagem |

### Admin
| Comando | Descrição |
|---|---|
| `/godmode` | Toggle modo Criador (ordens absolutas) |
| `/painel` | Hub de comandos rápidos |
| `/combate` | Gerenciador de turnos (iniciativa automática) |
| `/guiar ordem` | Direção oculta (PV → grupo, jogadores não veem) |
| `/debug` | Diagnóstico completo do sistema |
| `/reset` | Desliga IA e limpa sessão |

---

## ⚔️ Combate (`/combate`)

Admin inicia → bot rola iniciativa automática → cria fila de turnos → IA foca no jogador da vez.

```
⚔️ COMBATE ATIVO
🎯 Vez de: Grovax
1. 👉 Grovax (Init 19)
2.    Zeb (Init 15)
3.    Sh'Bihl (Init 12)
[⏭️ Próximo] [🏁 Fim]
```

---

## 🔱 GODMODE e `/guiar`

**GODMODE:** Toggle para admin. Mensagens viram ordens absolutas. IA acata e emite tags de estado.

**`/guiar`:** Direção oculta no PV do bot → IA executa como evento natural no grupo. Jogadores não veem a instrução. Se não há grupo rastreado, busca no banco e lista grupos com fichas ativas.

---

## 🎬 GIFs

IA inclui `[GIF:space explosion]` na narração. Bot busca Tenor, envia animação e remove tag. Também `/gif termo` para busca manual. Requer `TENOR_API_KEY`.

---

## 📡 Tracing

17+ pontos de trace nos logs. Formato: `[TRACE:CATEGORIA] chat=ID user=ID detalhe`

| Categoria | Rastreia |
|---|---|
| `MSG_IN` | Mensagem recebida + estado |
| `MSG_OUT` | Resposta enviada |
| `BTN` | Botão pressionado |
| `DICE` | Rolagem |
| `AI_REQ/AI_RES` | Request/response Gemini |
| `INTERCEPT` | Tags encontradas |
| `DB` | Escrita no banco |
| `GODMODE` | Comandos do Criador |
| `SESSION` | Início/reset/keep-alive |
| `GATE` | Mensagens bloqueadas (motivo) |

### Diagnóstico: "IA offline?"

```bash
grep "TRACE:GATE" logs.txt     # Mensagens bloqueadas
grep "ESCUTANDO" logs.txt       # IA em silêncio
grep "TRACE:AI_" logs.txt       # Requests/responses
```

---

## 💓 Keep-Alive

Background task pinga o webhook a cada 10 minutos. Mantém Render free tier acordado. Log: `💓 Keep-alive OK (HTTP 404)`.

---

## 🌐 Landing Page

Servida em `/` via aiohttp no mesmo port do webhook. Estilo sci-fi com estrelas animadas, stats do RPG e link direto para o bot.

---

## ⚙️ Setup

```bash
# Local
export TELEGRAM_TOKEN="..." GEMINI_API_KEY="..." SUPABASE_URL="..." SUPABASE_KEY="..."
python bot.py  # polling

# Render: Docker + env vars + WEBHOOK_URL
```

### Supabase
1. SQL Editor → `setup_supabase.sql`
2. Inserir dados em `dados_rpg` (stats, glossário, regras)
3. Editar pelo dashboard sem redeploy

---

## 📝 Créditos

- **RPG:** Passagem Sombria © 2026 Jonas Antonio da Silva Sprocatti
- **Bot:** Claude (Anthropic) + Gemini (Google) + Supabase
- **Licença:** CC BY-NC-ND 4.0
