-- Execute no SQL Editor do Supabase (https://supabase.com/dashboard → SQL Editor)
-- Se já criou a tabela fichas antes, rode apenas a parte de sessões.

-- ═══════════════════════════════════════
-- TABELA DE FICHAS (personagens)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS fichas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    user_name TEXT DEFAULT 'Viajante',
    character_name TEXT DEFAULT 'Desconhecido',
    ficha TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, chat_id)
);

CREATE INDEX IF NOT EXISTS idx_fichas_chat ON fichas(chat_id);

ALTER TABLE fichas ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "fichas_full_access" ON fichas
    FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════
-- TABELA DE SESSÕES (progresso da aventura)
-- ═══════════════════════════════════════
CREATE TABLE IF NOT EXISTS sessoes (
    id BIGSERIAL PRIMARY KEY,
    chat_id TEXT NOT NULL,
    title TEXT DEFAULT 'Sessão sem título',
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessoes_chat ON sessoes(chat_id);

ALTER TABLE sessoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "sessoes_full_access" ON sessoes
    FOR ALL USING (true) WITH CHECK (true);
