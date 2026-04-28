# 🌌 Passagem Sombria — RPG Master Companion Bot v3.2

Bot Telegram que atua como motor de RPG de mesa para o universo **Passagem Sombria**, usando **Google Gemini** como IA narrativa e **Supabase** como banco de dados persistente.

**Filosofia:** O Bot controla toda lógica, cálculos e estado. A IA apenas narra. O banco de dados é a fonte da verdade.

---

## 📁 Estrutura de Arquivos

| Arquivo | Linhas | Função |
|---|---|---|
| `bot.py` | ~1340 | Core: handlers, interceptor, criação, level up, implantes, GODMODE, tracing |
| `glossary.py` | 169 | Dados mecânicos + labels de botão (fallback local) |
| `data_loader.py` | 83 | Carrega `dados_rpg` do Supabase → memória |
| `rpg_content.txt` | 47 | Referência mecânica d20 injetada no prompt do Gemini |
| `setup_supabase.sql` | ~80 | Schema SQL |
| `Dockerfile` | 5 | Container para Render |
| `requirements.txt` | 3 | Dependências |

---

## 🔌 Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `TELEGRAM_TOKEN` | Token do BotFather |
| `GEMINI_API_KEY` | Chave do Google AI Studio |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon do Supabase |
| `WEBHOOK_URL` | URL do Render (sem ela, roda em polling) |
| `ADMIN_ID` | Telegram ID do admin (habilita GODMODE) |

---

## 🗄️ Banco de Dados

### Tabela `fichas` (1:N — um jogador pode ter várias)
Campos: id, user_id, chat_id, nome, raca, classe, filosofia, nivel, xp, pv_atual, pv_max, cd, ram_atual, ram_max, iniciativa, deslocamento, creditos, atributos (JSONB), pericias (JSONB), habilidades (JSONB), tecnomancias (JSONB), armas (JSONB), armadura, inventario (JSONB), implantes (JSONB), notas.

### Tabela `fichas_ativas` (UNIQUE user_id + chat_id)
Define qual ficha cada jogador usa na sessão atual.

### Tabela `sessoes`
Resumos de aventura com título gerado pela IA.

### Tabela `dados_rpg` (chave TEXT PK, dados JSONB)
Dados estáticos: stats de raças/classes, textos do glossário, regras. Carregados em memória no startup pelo `data_loader.py`. Para editar sem redeploy: Dashboard → dados_rpg → edite o JSON → reinicie o bot.

---

## 🔄 Fluxo de Inicialização

```
main()
  ├── DL.ensure_loaded()
  │     ├── Carrega glossary.py para memória (fallback)
  │     └── Conecta Supabase → lê dados_rpg → sobrepõe
  ├── Registra CommandHandlers (20 comandos)
  ├── Registra CallbackQueryHandler (botões)
  ├── Registra MessageHandler (texto → on_msg)
  ├── Registra Regex handler (/NdN → dados)
  └── run_webhook() ou run_polling()
```

---

## 🎮 Fluxo de Jogo

### 1. Seleção de Personagem

```
/iniciar → lista fichas do jogador → botões inline
  └── Jogador toca → db_set_active() → ficha injetada na IA
      └── Botões [🆕 Nova Aventura] [📜 Continuar]
```

### 2. Início de Sessão

```
"Nova Aventura" → jogo_ativo[cid] = True (IA LIGADA)
  └── Bot injeta FICHAS_ATIVAS + MODO_NARRATIVA na IA
      └── IA narra cena de abertura
```

### 3. Mensagem Normal (durante jogo)

```
on_msg() recebe texto
  ├── É dado? (/1d20p5) → calcula + injeta resultado na IA
  ├── É GODMODE? → [GODMODE] ordem → IA acata
  ├── jogo_ativo == False? → IGNORA (trace: GATE)
  ├── Sem ficha ativa? → IGNORA (trace: GATE)
  └── Jogo:
        ├── Header: [Usuário: @nick | Personagem: Nome] diz: texto
        ├── ask(Gemini) → resposta
        ├── intercept_and_sync() → extrai tags → atualiza DB
        ├── Se [ESCUTANDO] → IA em silêncio (jogadores conversando)
        └── Mostra resposta limpa
```

### 4. Interceptor de Estado

Cada resposta da IA é parseada buscando 11 tipos de tags:

| Tag | Formato | Efeito |
|---|---|---|
| `XP` | `[XP:valor:alvo:motivo]` | Soma XP, verifica level up |
| `HP` | `[HP:valor:alvo]` | Altera PV |
| `ITEM_ADD/DEL` | `[ITEM_ADD:nome:alvo]` | Altera inventário |
| `CG` | `[CG:valor:alvo]` | Altera créditos |
| `RAM` | `[RAM:valor:alvo]` | Altera RAM |
| `TECNO_ADD/DEL` | `[TECNO_ADD:id:alvo]` | Aprende/perde script |
| `IMPLANTE_ADD` | `[IMPLANTE_ADD:id:alvo]` | Cirurgia autônoma |
| `ATTR` | `[ATTR:atrib:valor:alvo]` | Altera atributo |
| `PER` | `[PER:pericia:valor:alvo]` | Altera perícia |

Matching de nomes é **case-insensitive e accent-insensitive**.

---

## 🧑‍🚀 Criação de Personagem

100% estática (IA não participa). Etapas:

1. Raça (9 botões) → 2. Classe (15) → 3. Filosofia (12) → 4. Atributos (2d8×7, distribui por botão) → 5. PV (4d6 desc menor + ajustes) → 6. Equipamento (botão se houver escolha) → 7. [Terráqueo: +4 attr +3 per] → 8. Nome (digita) → 9. [Se Tecno ≥ 1: seleção de scripts] → 10. Salva no DB + ativa.

Habilidades montadas automaticamente: Racial + Classe + Filosofia.

### Importação (`/importar`)
Template com todos os campos. Bot calcula CD, RAM e Iniciativa automaticamente.

---

## ⬆️ Level Up

1. Verifica XP ≥ tabela → 2. Rola dado de vida (d6/d8/d10) + Con → 3. +1 RAM em nível ímpar → 4. Botões para +1 Atributo → 5. Botões para +1 Perícia → 6. [Se ganhou slot Tecno: botões para novo script]

---

## 🦾 Implantes

### Via `/implante` (botões: Cabeça/Torso/Membros)
Verifica créditos, mostra preços, avisa de risco se acima do limite.

### Via IA (`[IMPLANTE_ADD:id:alvo]`)
Bot calcula tolerância `max(2+Con,1)`, aplica mecânica do implante, avalia sobrecarga:
- ✅ Dentro do limite → limpo
- ⚠️ 1º acima → -1d6 PV máx permanente + Desvantagem Persuasão
- ☠️ 2º acima → Curto-Circuito (1-2 natural = dano)
- 💀 3º acima → PV=0 (morte)

Injeta `[SISTEMA MÉDICO: ...]` na IA para narrar.

---

## 🔱 GODMODE

`/godmode` — toggle exclusivo do ADMIN_ID. Bypassa `jogo_ativo`. IA acata qualquer ordem sem questionar. Emite tags de estado para o bot registrar mudanças.

---

## 🎲 Dados (Regex)

`/1d20`, `/1d20p5` (plus), `/2d8m1` (minus). Formato `p/m` fica clicável inteiro no Telegram. Formato `+/-` também aceito. Resultado injetado na IA se jogo ativo.

---

## 📡 Sistema de Tracing

17 pontos de trace cobrindo todo o fluxo. Formato:
```
[TRACE:CATEGORIA] chat=ID user=ID detalhe | extras
```

### Categorias

| Categoria | Rastreia |
|---|---|
| `MSG_IN` | Mensagem recebida + estado (jogo? godmode?) |
| `MSG_OUT` | Resposta enviada (tamanho) |
| `BTN` | Botão pressionado (callback data) |
| `DICE` | Rolagem (fórmula, resultado, se injetou na IA) |
| `AI_REQ` | Request ao Gemini (tamanho, preview) |
| `AI_RES` | Resposta do Gemini (tamanho, presença de tags) |
| `INTERCEPT` | Tags encontradas + notificações de sync |
| `DB` | Escrita no banco (campos alterados) |
| `GODMODE` | Comandos do Criador |
| `SESSION` | Início/reset de sessão |
| `GATE` | Mensagens BLOQUEADAS (motivo) |
| `ERROR` | Erros globais |

### Diagnóstico: "A IA está offline?"

```bash
# Mensagens recebidas vs respondidas
grep "TRACE:MSG_IN\|TRACE:MSG_OUT\|TRACE:GATE" logs.txt

# IA em modo escuta (silêncio)
grep "ESCUTANDO" logs.txt

# Mensagens bloqueadas
grep "TRACE:GATE" logs.txt

# Requests/responses IA
grep "TRACE:AI_" logs.txt
```

| Sintoma | Causa no log | Solução |
|---|---|---|
| IA não responde | `GATE: jogo_ativo=False` | `/novojogo` |
| IA ignora 1 jogador | `GATE: sem ficha ativa` | Jogador precisa `/iniciar` |
| IA responde vazio | `ESCUTANDO` | Jogadores só conversando |
| IA demora | `AI_REQ` sem `AI_RES` | Rate limit Gemini |

### Exemplo de Log

```
INFO [TRACE:MSG_IN] chat=-100123 user=567 texto='Eu ataco o pirata' | user=Jonas jogo=True godmode=False
INFO [TRACE:AI_REQ] → Gemini | prompt_len=89 first_50='[Usuário: @jonas | Personagem: Grovax]...'
INFO [TRACE:AI_RES] ← Gemini | resp_len=450 has_tags=True
INFO [TRACE:INTERCEPT] chat=-100123 Encontrou 2 tags | tags=['XP', 'HP']
INFO [TRACE:DB] UPDATE ficha=42 | campos=['xp']
INFO [TRACE:DB] UPDATE ficha=42 | campos=['pv_atual']
INFO [TRACE:MSG_OUT] chat=-100123 resp_len=380
```

---

## 🗺️ Comandos

| Comando | Descrição |
|---|---|
| `/start` | Menu principal |
| `/iniciar` | Seleciona personagem |
| `/novojogo` | Inicia aventura |
| `/criarpersonagem` | Criação por botões |
| `/importar` | Importa ficha existente |
| `/ficha` | Mostra ficha ativa |
| `/fichas` | Lista todas |
| `/deletarficha ID` | Deleta ficha |
| `/levelup` | Level up com botões |
| `/implante` | Gerencia implantes |
| `/1d20p5` | Rola dado |
| `/salvarsessao` | Salva sessão |
| `/sessoes` | Lista sessões |
| `/cargarsessao ID` | Retoma sessão |
| `/contexto` | Importa contexto |
| `/glossario` | Banco de dados offline |
| `/regras` | Regras rápidas |
| `/godmode` | Modo Criador (admin) |
| `/debug` | Diagnóstico Supabase |
| `/reset` | Desliga IA |

---

## 📝 Créditos

- **RPG:** Passagem Sombria © 2026 Jonas Antonio da Silva Sprocatti
- **Bot:** Claude (Anthropic) + Gemini (Google) + Supabase
- **Licença RPG:** CC BY-NC-ND 4.0
