-- ============================================================================
-- SciAgent 数据库初始化脚本
-- PostgreSQL 16 + pgvector + uuid-ossp
-- ============================================================================

-- 1. 扩展 ───────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. ENUM 类型 ───────────────────────────────────────────────────────────────
CREATE TYPE subscription_plan AS ENUM ('free', 'basic', 'pro', 'enterprise');
CREATE TYPE paper_source    AS ENUM ('openalex', 'cnki', 'wanfang', 'cqvip', 'manual_import', 'zotero', 'mendeley', 'scholar');
CREATE TYPE sandbox_status  AS ENUM ('running', 'stopped', 'error', 'completed');
CREATE TYPE workspace_role  AS ENUM ('owner', 'editor', 'viewer');
CREATE TYPE log_action      AS ENUM ('create', 'update', 'delete', 'export', 'share', 'login', 'search', 'payment');

-- 3. 表定义 ──────────────────────────────────────────────────────────────────

-- 3.1 users
CREATE TABLE users (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(320)    NOT NULL UNIQUE,
    hashed_password     TEXT            NOT NULL,
    full_name           VARCHAR(128)    NOT NULL,
    institution         VARCHAR(256)    DEFAULT '',
    subscription_plan   subscription_plan NOT NULL DEFAULT 'free',
    trial_ends_at       TIMESTAMPTZ,
    preferred_language  VARCHAR(10)     NOT NULL DEFAULT 'zh-CN',
    is_active           BOOLEAN         NOT NULL DEFAULT true,
    is_verified         BOOLEAN         NOT NULL DEFAULT false,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON users(email);

-- 3.2 papers
CREATE TABLE papers (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    openalex_id     VARCHAR(255),
    doi             VARCHAR(500)    UNIQUE,
    title           TEXT            NOT NULL,
    abstract        TEXT,
    authors         JSONB,
    publication_date DATE,
    journal         VARCHAR(500),
    source_db       paper_source    NOT NULL DEFAULT 'openalex',
    language        VARCHAR(10)     DEFAULT 'en',
    citation_count  INT             DEFAULT 0,
    keywords        TEXT[],
    references_json JSONB,
    metadata        JSONB,
    full_text_url   TEXT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_papers_doi        ON papers(doi);
CREATE INDEX idx_papers_title_trgm ON papers USING GIN(title gin_trgm_ops);
CREATE INDEX idx_papers_embedding  ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 3.3 user_library
CREATE TABLE user_library (
    id          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id    UUID            NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    folder_name VARCHAR(100),
    tags        TEXT[],
    is_favorite BOOLEAN         DEFAULT false,
    is_read     BOOLEAN         DEFAULT false,
    added_at    TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE(user_id, paper_id)
);
CREATE INDEX idx_user_library_user   ON user_library(user_id);
CREATE INDEX idx_user_library_folder ON user_library(user_id, folder_name);

-- 3.4 annotations
CREATE TABLE annotations (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id        UUID            NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    content         TEXT            NOT NULL,
    highlight_range JSONB,
    color           VARCHAR(20)     DEFAULT '#FFEB3B',
    is_public       BOOLEAN         DEFAULT false,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_annotations_paper ON annotations(paper_id, user_id);

-- 3.5 documents
CREATE TABLE documents (
    id          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(500)    NOT NULL,
    content     TEXT,
    doc_type    VARCHAR(50)     NOT NULL DEFAULT 'note',
    format      VARCHAR(20)     DEFAULT 'markdown',
    tags        TEXT[],
    is_archived BOOLEAN         DEFAULT false,
    parent_id   UUID            REFERENCES documents(id),
    version     INT             NOT NULL DEFAULT 1,
    embedding   vector(1536),
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_documents_user ON documents(user_id);

-- 3.6 sandbox_sessions
CREATE TABLE sandbox_sessions (
    id            UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          VARCHAR(200)    NOT NULL,
    description   TEXT,
    container_id  VARCHAR(100),
    status        sandbox_status  NOT NULL DEFAULT 'running',
    config        JSONB,
    started_at    TIMESTAMPTZ     NOT NULL DEFAULT now(),
    stopped_at    TIMESTAMPTZ
);
CREATE INDEX idx_sandbox_user ON sandbox_sessions(user_id);

-- 3.7 workspaces
CREATE TABLE workspaces (
    id          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(200)    NOT NULL,
    description TEXT,
    owner_id    UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_public   BOOLEAN         DEFAULT false,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);

-- 3.8 workspace_members
CREATE TABLE workspace_members (
    id            UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id  UUID            NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id       UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role          workspace_role  NOT NULL DEFAULT 'viewer',
    joined_at     TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, user_id)
);
CREATE INDEX idx_workspace_members_user ON workspace_members(user_id);

-- 3.9 activity_logs
CREATE TABLE activity_logs (
    id            UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action        log_action      NOT NULL,
    resource_type VARCHAR(50),
    resource_id   UUID,
    detail        JSONB,
    ip_address    INET,
    user_agent    TEXT,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id, created_at DESC);

-- 3.10 model_providers
CREATE TABLE model_providers (
    id           UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(50)     NOT NULL UNIQUE,
    display_name VARCHAR(100)    NOT NULL,
    base_url     VARCHAR(500)    NOT NULL,
    api_type     VARCHAR(20)     DEFAULT 'openai',
    is_builtin   BOOLEAN         DEFAULT false,
    is_enabled   BOOLEAN         DEFAULT true,
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- 3.11 user_model_configs
CREATE TABLE user_model_configs (
    id               UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_id      UUID            NOT NULL REFERENCES model_providers(id),
    api_key_encrypted TEXT,
    model_name       VARCHAR(100)    NOT NULL,
    is_default       BOOLEAN         DEFAULT false,
    priority         INT             DEFAULT 0,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE(user_id, provider_id, model_name)
);

-- 3.12 subscriptions
CREATE TABLE subscriptions (
    id               UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID                NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan             subscription_plan   NOT NULL DEFAULT 'free',
    status           VARCHAR(20)         NOT NULL DEFAULT 'active',
    auto_renew       BOOLEAN             DEFAULT true,
    payment_provider VARCHAR(30),
    started_at       TIMESTAMPTZ         NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ,
    cancelled_at     TIMESTAMPTZ
);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);

-- 3.13 payments
CREATE TABLE payments (
    id                 UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id    UUID            REFERENCES subscriptions(id),
    user_id            UUID            NOT NULL REFERENCES users(id),
    amount             NUMERIC(10,2)   NOT NULL,
    currency           VARCHAR(3)      DEFAULT 'CNY',
    provider           VARCHAR(30),
    provider_payment_id VARCHAR(255),
    status             VARCHAR(20)     NOT NULL DEFAULT 'pending',
    paid_at            TIMESTAMPTZ
);
CREATE INDEX idx_payments_user ON payments(user_id);

-- 3.14 invoices
CREATE TABLE invoices (
    id             UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID            NOT NULL REFERENCES users(id),
    payment_id     UUID            REFERENCES payments(id),
    invoice_number VARCHAR(50)     UNIQUE NOT NULL,
    pdf_url        TEXT,
    issued_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- 3.15 coupons
CREATE TABLE coupons (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(50)     UNIQUE NOT NULL,
    discount_type   VARCHAR(20)     NOT NULL,
    discount_value  NUMERIC(10,2)   NOT NULL,
    max_uses        INT             DEFAULT 0,
    current_uses    INT             DEFAULT 0,
    expires_at      TIMESTAMPTZ
);

-- 3.16 conversations
CREATE TABLE conversations (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(200),
    pinned          BOOLEAN         DEFAULT false,
    deleted_at      TIMESTAMPTZ,
    content_vector  vector(1536),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX idx_conversations_user ON conversations(user_id, pinned DESC, updated_at DESC);

-- 4. 默认模型提供商种子数据 ──────────────────────────────────────────────────
INSERT INTO model_providers (name, display_name, base_url, api_type, is_builtin) VALUES
    ('openai',   'OpenAI',         'https://api.openai.com/v1',                           'openai', true),
    ('deepseek', 'DeepSeek',       'https://api.deepseek.com/v1',                         'openai', true),
    ('qwen',     '通义千问',       'https://dashscope.aliyuncs.com/compatible-mode/v1',   'openai', true),
    ('ollama',   'Ollama (本地)',   'http://localhost:11434/v1',                           'openai', true);
