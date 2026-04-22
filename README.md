# 🌌 Passagem Sombria — RPG Master Companion Bot v3.0

Bot Telegram de RPG com **Gemini** (narração) e **Supabase** (estado). Bot = lógica. IA = narração.

## 📁 Arquitetura

| Arquivo | Função |
|---|---|
| `bot.py` | Handlers, criação estática, interceptor, regex dice, cirurgia implantes |
| `glossary.py` | Dados mecânicos (stats/botões) — fallback local |
| `data_loader.py` | Carrega dados do Supabase → memória (fallback → glossary.py) |
| `rpg_content.txt` | Regras mecânicas d20 para o Gemini (sem lore) |
| `setup_supabase.sql` | Schema: fichas, fichas_ativas, sessoes |
| `seed_dados_rpg.sql` | Popula dados_rpg com stats + textos de glossário |

## 🚀 Setup

1. **Telegram**: [@BotFather](https://t.me/BotFather) → token
2. **Gemini**: [aistudio.google.com](https://aistudio.google.com) → API key
3. **Supabase**: Novo projeto → SQL Editor → executar `setup_supabase.sql` → depois `seed_dados_rpg.sql`
4. **Render**: Docker, variáveis: `TELEGRAM_TOKEN`, `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `WEBHOOK_URL`, `ADMIN_ID`

### Alimentar tabelas no Supabase

```sql
-- 1. Criar estrutura
-- Execute setup_supabase.sql (fichas, fichas_ativas, sessoes)

-- 2. Popular dados estáticos
-- Execute seed_dados_rpg.sql (stats, textos glossário, regras)

-- 3. Para editar dados sem redeploy:
-- Supabase Dashboard → dados_rpg → edite o JSON da chave desejada
-- Na próxima reinicialização do bot, os dados atualizados serão carregados
```

## 🎲 Rolagem via Regex (Diretriz 4)

Sem comando `/rolar`. O jogador digita diretamente no chat:

```
/1d20        → rola 1d20
/2d8+4       → rola 2d8 e soma +4
/4d6-1       → rola 4d6 e subtrai 1
```

O bot captura via regex `/(\\d*)d(\\d+)([+-]\\d+)?`, calcula o resultado em Python, exibe no chat e injeta automaticamente na IA:

```
[SISTEMA: O personagem Kira rolou 1d20+3 e obteve 17]
```

A IA então narra a consequência imediata.

## 🧑‍🚀 Identidade de Turno (Diretriz 3)

Cada mensagem é enviada à IA com cabeçalho:

```
[Usuário: @jonas_sp | Personagem: Kira] diz: Eu me escondo atrás da parede
```

A IA usa o nome do **personagem** para se referir ao jogador. Quando há 1 jogador ativo, narra no singular. Com múltiplos, no plural.

## 🦾 Cirurgia de Implantes (Diretriz 6)

### Via comando `/implante`
Botões: Cabeça → Torso → Membros. Verifica créditos e limite seguro.

### Via IA (interceptor)
A IA dispara `[IMPLANTE_ADD:olho:Jonas]` → Bot executa:

1. Calcula tolerância: `max(2 + Mod.Con, 1)`
2. Adiciona implante no DB
3. Avalia sobrecarga:
   - ✅ Dentro do limite → instalação limpa
   - ⚠️ 1º acima → rola 1d6, subtrai de PV máx permanente + "Desvantagem Persuasão"
   - ☠️ 2º acima → adiciona status "Curto-Circuito" (1-2 natural = 1d6 elétrico)
   - 💀 3º acima → PV = 0, alerta de óbito cibernético
4. Injeta relatório na IA: `[SISTEMA MÉDICO: Implante X instalado. Resultado: Sobrecarga Nv1: perdeu 4 PV Máximo]`
5. IA narra a reação do corpo

## 📋 Consciência da Ficha (Diretriz 7)

Quando o jogador pergunta "Quais meus status?", "O que tenho no inventário?", a IA consulta o bloco `FICHAS_ATIVAS` (atualizado pelo bot) e responde com dados reais. Proibida de inventar itens ou status.

## 🧠 Tiers de Tecnomancia (Diretriz 1)

| Proficiência Total | Tiers Disponíveis |
|---|---|
| +1 a +3 | Básicas (10 scripts) |
| +4 a +6 | + Injeções (10 scripts) |
| +7 ou mais | + Protocolos (10 scripts) |

Na criação e level up, os botões de seleção filtram automaticamente pelo tier.

## 📡 Tags do Interceptor

| Tag | Efeito |
|---|---|
| `[XP:valor:motivo:alvo]` | Soma XP, verifica level up |
| `[HP:valor:alvo]` | Altera PV |
| `[ITEM_ADD:nome:alvo]` | Adiciona inventário |
| `[ITEM_DEL:nome:alvo]` | Remove inventário |
| `[CG:valor:alvo]` | Altera créditos |
| `[RAM:valor:alvo]` | Altera RAM |
| `[TECNO_ADD:id:alvo]` | Aprende script |
| `[IMPLANTE_ADD:id:alvo]` | Cirurgia autônoma (com cálculos) |
| `[ATTR:atrib:valor:alvo]` | Altera atributo |
| `[PER:pericia:valor:alvo]` | Altera perícia |

## 🔧 Local

```bash
export TELEGRAM_TOKEN="..." GEMINI_API_KEY="..." SUPABASE_URL="..." SUPABASE_KEY="..."
python bot.py
```

## 📝 Créditos

- **RPG:** Passagem Sombria © 2026 Jonas Antonio da Silva Sprocatti
- **Bot:** Claude (Anthropic) + Gemini (Google) + Supabase
- **Licença:** CC BY-NC-ND 4.0
