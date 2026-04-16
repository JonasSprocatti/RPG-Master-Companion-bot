-- Execute este SQL no SQL Editor do Supabase para criar a tabela de fichas
-- Acesse: https://supabase.com/dashboard → seu projeto → SQL Editor → New Query

CREATE TABLE fichas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    user_name TEXT DEFAULT 'Viajante',
    character_name TEXT DEFAULT 'Desconhecido',
    ficha TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, chat_id)
);

-- Índice para buscas rápidas
CREATE INDEX idx_fichas_chat ON fichas(chat_id);

-- Habilitar Row Level Security (boa prática)
ALTER TABLE fichas ENABLE ROW LEVEL SECURITY;

-- Política que permite tudo via service key (que é o que o bot usa)
CREATE POLICY "Bot pode tudo" ON fichas
    FOR ALL
    USING (true)
    WITH CHECK (true);
