"""Abertura da conexão SQLite e criação das tabelas."""
import sqlite3

import config
from database.modelos import SCHEMA


def criar_tabelas(conexao: sqlite3.Connection) -> None:
    conexao.executescript(SCHEMA)
    conexao.commit()


def abrir_conexao(caminho=None) -> sqlite3.Connection:
    """Abre (e cria, se preciso) o banco. Use ':memory:' nos testes."""
    conexao = sqlite3.connect(str(caminho or config.caminho_banco()))
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    criar_tabelas(conexao)
    return conexao
