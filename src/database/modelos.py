"""Esquema do banco SQLite (criado automaticamente na primeira execução).

Relacionamentos
---------------
usuarios 1---1 preferencias
usuarios 1---N historico
usuarios 1---N favoritos          (único por usuário + conhecimento_id)
usuarios 1---N checklists         (único por usuário + modelo_id)
checklists 1---N tarefas_checklist
Todas as tabelas filhas usam ON DELETE CASCADE: excluir a conta apaga os dados.
`conhecimento_id` aponta para o JSON da base (não é chave estrangeira do SQLite).
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    criado_em   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preferencias (
    usuario_id      INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    fonte_escala    REAL    NOT NULL DEFAULT 1.0,
    alto_contraste  INTEGER NOT NULL DEFAULT 0,
    usar_ia         INTEGER NOT NULL DEFAULT 0,
    template_padrao TEXT    NOT NULL DEFAULT 'A'
);

CREATE TABLE IF NOT EXISTS historico (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id       INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pergunta         TEXT NOT NULL,
    resposta         TEXT NOT NULL,
    status           TEXT NOT NULL,
    template         TEXT NOT NULL,
    ids_conhecimento TEXT NOT NULL DEFAULT '',
    usou_ia          INTEGER NOT NULL DEFAULT 0,
    criado_em        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_historico_usuario ON historico(usuario_id, criado_em);

CREATE TABLE IF NOT EXISTS favoritos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    conhecimento_id TEXT NOT NULL,
    criado_em       TEXT NOT NULL,
    UNIQUE (usuario_id, conhecimento_id)
);

CREATE TABLE IF NOT EXISTS checklists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    modelo_id   TEXT NOT NULL,
    titulo      TEXT NOT NULL,
    criado_em   TEXT NOT NULL,
    UNIQUE (usuario_id, modelo_id)
);

CREATE TABLE IF NOT EXISTS tarefas_checklist (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_id    INTEGER NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
    ordem           INTEGER NOT NULL,
    descricao       TEXT NOT NULL,
    conhecimento_id TEXT,
    concluida       INTEGER NOT NULL DEFAULT 0,
    concluida_em    TEXT
);
CREATE INDEX IF NOT EXISTS idx_tarefas_checklist ON tarefas_checklist(checklist_id, ordem);
"""
