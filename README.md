# 🌌 Passagem Sombria — RPG Master Bot

Bot do Telegram que atua como Mestre de RPG para o universo **Passagem Sombria**, usando a API do **Google Gemini** como inteligência artificial.

## 🚀 Setup Rápido

### 1. Criar o Bot no Telegram
1. Abra o Telegram e fale com [@BotFather](https://t.me/BotFather)
2. Envie `/newbot`
3. Escolha um nome (ex: `Passagem Sombria RPG`)
4. Escolha um username (ex: `PassagemSombriaRPG_bot`)
5. **Guarde o token** que o BotFather vai te dar

### 2. Pegar a API Key do Gemini
1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Clique em **"Get API Key"**
3. Crie uma nova chave de API
4. **Guarde a chave**

### 3. Subir o Código no GitHub
1. No seu repositório `RPG-Master-Companion-bot`, faça upload de todos os arquivos:
   - `bot.py`
   - `rpg_content.txt`
   - `requirements.txt`
   - `Dockerfile`

### 4. Deploy no Render
1. No Render, na tela de configuração do Web Service:
   - **Name:** `RPG-Master-Companion-bot`
   - **Language:** `Docker`
   - **Branch:** `main`
   - **Dockerfile Path:** `./Dockerfile`

2. Em **Environment Variables**, adicione:
   | Variável | Valor |
   |---|---|
   | `TELEGRAM_TOKEN` | O token do BotFather |
   | `GEMINI_API_KEY` | Sua chave da API do Gemini |
   | `WEBHOOK_URL` | `https://rpg-master-companion-bot.onrender.com` |

3. Clique em **Deploy**

### 5. Pronto! 🎉
Abra o Telegram, procure pelo seu bot e envie `/start`

## 📖 Comandos do Bot

| Comando | Descrição |
|---|---|
| `/start` | Mensagem de boas-vindas |
| `/novojogo` | Iniciar uma nova aventura |
| `/criarpersonagem` | Criar personagem passo a passo |
| `/rolar 1d20` | Rolar dados |
| `/regras` | Resumo das regras |
| `/racas` | Lista de raças |
| `/classes` | Lista de classes |
| `/reset` | Resetar sessão |
| `/ajuda` | Ver comandos |

## 🔧 Rodando Localmente (Opcional)

```bash
export TELEGRAM_TOKEN="seu_token"
export GEMINI_API_KEY="sua_chave"
python bot.py
```

Sem a variável `WEBHOOK_URL`, o bot roda em modo polling (ideal para testes locais).
