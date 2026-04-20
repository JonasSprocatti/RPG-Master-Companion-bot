-- ═══════════════════════════════════════
-- PASSAGEM SOMBRIA v2.0 — Schema Completo
-- Executar no SQL Editor do Supabase
-- ═══════════════════════════════════════

-- Dropar tabelas antigas (se existirem)
DROP TABLE IF EXISTS fichas_ativas CASCADE;
DROP TABLE IF EXISTS sessoes CASCADE;
DROP TABLE IF EXISTS fichas CASCADE;

-- ═══════════════════════════════════════
-- FICHAS (1:N — um jogador pode ter várias fichas)
-- ═══════════════════════════════════════
CREATE TABLE fichas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    user_name TEXT DEFAULT 'Viajante',
    
    -- Identidade
    nome TEXT NOT NULL DEFAULT 'Sem Nome',
    raca TEXT NOT NULL DEFAULT '',
    classe TEXT NOT NULL DEFAULT '',
    filosofia TEXT NOT NULL DEFAULT '',
    
    -- Status
    nivel INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    pv_atual INTEGER DEFAULT 0,
    pv_max INTEGER DEFAULT 0,
    cd INTEGER DEFAULT 10,
    ram_atual INTEGER DEFAULT 0,
    ram_max INTEGER DEFAULT 0,
    iniciativa INTEGER DEFAULT 0,
    deslocamento INTEGER DEFAULT 9,
    creditos INTEGER DEFAULT 100,
    
    -- Componentes granulares (JSONB para queries eficientes)
    atributos JSONB DEFAULT '{"forca":8,"destreza":8,"constituicao":8,"inteligencia":8,"sabedoria":8,"carisma":8}',
    pericias JSONB DEFAULT '{}',
    habilidades JSONB DEFAULT '[]',
    tecnomancias JSONB DEFAULT '[]',
    armas JSONB DEFAULT '[]',
    armadura TEXT DEFAULT '',
    inventario JSONB DEFAULT '[]',
    implantes JSONB DEFAULT '[]',
    notas TEXT DEFAULT '',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SEM constraint UNIQUE(user_id, chat_id) — permite múltiplas fichas
CREATE INDEX idx_fichas_user_chat ON fichas(user_id, chat_id);

ALTER TABLE fichas ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY fichas_access ON fichas FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ═══════════════════════════════════════
-- FICHAS ATIVAS (qual ficha cada jogador está usando na sessão)
-- ═══════════════════════════════════════
CREATE TABLE fichas_ativas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    ficha_id BIGINT NOT NULL REFERENCES fichas(id) ON DELETE CASCADE,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, chat_id)  -- só 1 ficha ativa por jogador por chat
);

CREATE INDEX idx_ativas_chat ON fichas_ativas(chat_id);

ALTER TABLE fichas_ativas ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY ativas_access ON fichas_ativas FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ═══════════════════════════════════════
-- SESSÕES (registros de aventuras)
-- ═══════════════════════════════════════
CREATE TABLE sessoes (
    id BIGSERIAL PRIMARY KEY,
    chat_id TEXT NOT NULL,
    title TEXT DEFAULT 'Sessão sem título',
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessoes_chat ON sessoes(chat_id);

ALTER TABLE sessoes ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY sessoes_access ON sessoes FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
