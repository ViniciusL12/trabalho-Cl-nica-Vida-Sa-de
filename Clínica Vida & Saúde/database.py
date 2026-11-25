import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", INSTANCE_DIR / "clinica.db"))


@contextmanager
def get_connection():
    """Abre uma conexão SQLite e habilita as chaves estrangeiras."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    """Cria as tabelas e insere registros fictícios somente no primeiro uso."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                nascimento TEXT,
                telefone TEXT,
                email TEXT,
                observacoes TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                horario TEXT NOT NULL,
                tipo TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Agendada'
                    CHECK (status IN ('Agendada', 'Confirmada', 'Concluída', 'Cancelada')),
                observacoes TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
            );
            """
        )

        quantidade = connection.execute(
            "SELECT COUNT(*) AS total FROM pacientes"
        ).fetchone()["total"]
        if quantidade == 0:
            pacientes_exemplo = [
                ("Ana Exemplo", "1990-04-12", "(11) 90000-0001", "ana.exemplo@email.test", "Registro fictício para demonstração."),
                ("Bruno Demonstração", "1985-09-23", "(11) 90000-0002", "bruno.demo@email.test", "Registro fictício para demonstração."),
                ("Carla Modelo", "2000-01-08", "(11) 90000-0003", "carla.modelo@email.test", "Registro fictício para demonstração."),
            ]
            connection.executemany(
                """
                INSERT INTO pacientes (nome, nascimento, telefone, email, observacoes)
                VALUES (?, ?, ?, ?, ?)
                """,
                pacientes_exemplo,
            )
            ids = connection.execute(
                "SELECT id FROM pacientes ORDER BY id ASC"
            ).fetchall()
            consultas_exemplo = [
                (
                    ids[0]["id"],
                    (date.today() + timedelta(days=1)).isoformat(),
                    "09:00",
                    "Consulta de rotina",
                    "Confirmada",
                    "Agendamento fictício.",
                ),
                (
                    ids[1]["id"],
                    (date.today() + timedelta(days=2)).isoformat(),
                    "14:30",
                    "Avaliação inicial",
                    "Agendada",
                    "Agendamento fictício.",
                ),
                (
                    ids[2]["id"],
                    (date.today() + timedelta(days=3)).isoformat(),
                    "11:00",
                    "Retorno",
                    "Agendada",
                    "Agendamento fictício.",
                ),
            ]
            connection.executemany(
                """
                INSERT INTO consultas (paciente_id, data, horario, tipo, status, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                consultas_exemplo,
            )
