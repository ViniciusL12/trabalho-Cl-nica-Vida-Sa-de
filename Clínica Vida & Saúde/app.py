import os
import re
import secrets
from datetime import date

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

from database import (
    get_connection,
    initialize_database,
)


app = Flask(__name__)
APP_ENV = os.environ.get("APP_ENV", "development").lower()
SECRET_KEY = os.environ.get("SECRET_KEY")
if APP_ENV == "production" and not SECRET_KEY:
    raise RuntimeError("Configure a variável SECRET_KEY antes de iniciar em produção.")

app.config["SECRET_KEY"] = SECRET_KEY or secrets.token_hex(32)
app.config["DEBUG"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

CONSULTA_STATUSES = ("Agendada", "Confirmada", "Concluída", "Cancelada")


def linear_search_patients(pacientes, termo):
    """Busca pacientes percorrendo a lista, de forma simples e didática."""
    termo = termo.casefold().strip()
    if not termo:
        return pacientes

    encontrados = []
    for paciente in pacientes:
        campos = (paciente["nome"], paciente["telefone"] or "", paciente["email"] or "")
        if any(termo in campo.casefold() for campo in campos):
            encontrados.append(paciente)
    return encontrados


def bubble_sort_patients(pacientes):
    """Ordena os pacientes por nome usando o algoritmo Bubble Sort."""
    ordenados = list(pacientes)
    for limite in range(len(ordenados) - 1, 0, -1):
        houve_troca = False
        for indice in range(limite):
            nome_atual = ordenados[indice]["nome"].casefold()
            proximo_nome = ordenados[indice + 1]["nome"].casefold()
            if nome_atual > proximo_nome:
                ordenados[indice], ordenados[indice + 1] = (
                    ordenados[indice + 1],
                    ordenados[indice],
                )
                houve_troca = True
        if not houve_troca:
            break
    return ordenados


def patient_form_data():
    return {
        "nome": request.form.get("nome", "").strip(),
        "nascimento": request.form.get("nascimento", "").strip() or None,
        "telefone": format_phone_number(request.form.get("telefone", "")),
        "email": request.form.get("email", "").strip() or None,
        "observacoes": request.form.get("observacoes", "").strip() or None,
    }


def format_phone_number(value):
    """Normaliza telefones brasileiros para o mesmo formato exibido pelo formulário."""
    digits = re.sub(r"\D", "", value)
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return digits or None


def valid_patient(data):
    if not data["nome"]:
        flash("Informe o nome do paciente.", "error")
        return False
    if data["telefone"] and not re.fullmatch(
        r"\(\d{2}\) \d{4,5}-\d{4}", data["telefone"]
    ):
        flash("Informe um telefone com DDD e 8 ou 9 dígitos.", "error")
        return False
    if data["email"] and "@" not in data["email"]:
        flash("Informe um e-mail válido ou deixe o campo em branco.", "error")
        return False
    if data["nascimento"]:
        try:
            date.fromisoformat(data["nascimento"])
        except ValueError:
            flash("A data de nascimento informada é inválida.", "error")
            return False
    return True


def consultation_form_data():
    try:
        paciente_id = int(request.form.get("paciente_id", ""))
    except ValueError:
        paciente_id = 0
    return {
        "paciente_id": paciente_id,
        "data": request.form.get("data", "").strip(),
        "horario": request.form.get("horario", "").strip(),
        "tipo": request.form.get("tipo", "").strip(),
        "status": request.form.get("status", "").strip(),
        "observacoes": request.form.get("observacoes", "").strip() or None,
    }


def valid_consultation(data):
    if not data["paciente_id"]:
        flash("Selecione um paciente para a consulta.", "error")
        return False
    if not data["tipo"]:
        flash("Informe o tipo ou motivo da consulta.", "error")
        return False
    if data["status"] not in CONSULTA_STATUSES:
        flash("Selecione um status válido para a consulta.", "error")
        return False
    try:
        date.fromisoformat(data["data"])
    except ValueError:
        flash("Informe uma data válida para a consulta.", "error")
        return False
    try:
        hour, minute = (int(parte) for parte in data["horario"].split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, TypeError):
        flash("Informe um horário válido para a consulta.", "error")
        return False

    with get_connection() as connection:
        paciente = connection.execute(
            "SELECT id FROM pacientes WHERE id = ?", (data["paciente_id"],)
        ).fetchone()
    if paciente is None:
        flash("O paciente selecionado não foi encontrado.", "error")
        return False
    return True


@app.route("/")
def index():
    with get_connection() as connection:
        total_pacientes = connection.execute(
            "SELECT COUNT(*) AS total FROM pacientes"
        ).fetchone()["total"]
        total_consultas = connection.execute(
            "SELECT COUNT(*) AS total FROM consultas"
        ).fetchone()["total"]
        consultas_hoje = connection.execute(
            "SELECT COUNT(*) AS total FROM consultas WHERE data = date('now', 'localtime')"
        ).fetchone()["total"]
        proximas_consultas = connection.execute(
            """
            SELECT c.id, c.data, c.horario, c.tipo, c.status, p.nome AS paciente_nome
            FROM consultas AS c
            JOIN pacientes AS p ON p.id = c.paciente_id
            WHERE c.data >= date('now', 'localtime') AND c.status != 'Cancelada'
            ORDER BY c.data ASC, c.horario ASC
            LIMIT 5
            """
        ).fetchall()
    return render_template(
        "index.html",
        total_pacientes=total_pacientes,
        total_consultas=total_consultas,
        consultas_hoje=consultas_hoje,
        proximas_consultas=proximas_consultas,
    )


@app.route("/pacientes")
def pacientes():
    termo = request.args.get("q", "").strip()
    with get_connection() as connection:
        registros = connection.execute(
            """
            SELECT id, nome, nascimento, telefone, email
            FROM pacientes
            ORDER BY id DESC
            """
        ).fetchall()
    # A busca linear e a ordenação Bubble Sort ficam visíveis nesta listagem.
    resultados = linear_search_patients(registros, termo)
    resultados = bubble_sort_patients(resultados)
    return render_template("pacientes.html", pacientes=resultados, termo=termo)


@app.route("/pacientes/novo", methods=["GET", "POST"])
def cadastrar_paciente():
    if request.method == "POST":
        dados = patient_form_data()
        if valid_patient(dados):
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO pacientes (nome, nascimento, telefone, email, observacoes)
                    VALUES (:nome, :nascimento, :telefone, :email, :observacoes)
                    """,
                    dados,
                )
            flash("Paciente cadastrado com sucesso.", "success")
            return redirect(url_for("pacientes"))
    return render_template("cadastrar_paciente.html")


@app.route("/pacientes/<int:paciente_id>/editar", methods=["GET", "POST"])
def editar_paciente(paciente_id):
    with get_connection() as connection:
        paciente = connection.execute(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        ).fetchone()
    if paciente is None:
        abort(404)

    if request.method == "POST":
        dados = patient_form_data()
        if valid_patient(dados):
            dados["id"] = paciente_id
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE pacientes
                    SET nome = :nome, nascimento = :nascimento, telefone = :telefone,
                        email = :email, observacoes = :observacoes
                    WHERE id = :id
                    """,
                    dados,
                )
            flash("Cadastro do paciente atualizado.", "success")
            return redirect(url_for("pacientes"))
        paciente = {**paciente, **dados}
    return render_template("editar_paciente.html", paciente=paciente)


@app.route("/pacientes/<int:paciente_id>/excluir", methods=["POST"])
def excluir_paciente(paciente_id):
    with get_connection() as connection:
        paciente = connection.execute(
            "SELECT id FROM pacientes WHERE id = ?", (paciente_id,)
        ).fetchone()
        if paciente is None:
            abort(404)
        quantidade = connection.execute(
            "SELECT COUNT(*) AS total FROM consultas WHERE paciente_id = ?",
            (paciente_id,),
        ).fetchone()["total"]
        if quantidade:
            flash(
                "Este paciente possui consultas. Remova ou reassocie as consultas antes de excluir.",
                "error",
            )
        else:
            connection.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
            flash("Paciente excluído com sucesso.", "success")
    return redirect(url_for("pacientes"))


@app.route("/consultas")
def consultas():
    status_filtro = request.args.get("status", "")
    where_clause = ""
    parametros = ()
    if status_filtro in CONSULTA_STATUSES:
        where_clause = "WHERE c.status = ?"
        parametros = (status_filtro,)
    with get_connection() as connection:
        registros = connection.execute(
            f"""
            SELECT c.id, c.data, c.horario, c.tipo, c.status, p.nome AS paciente_nome
            FROM consultas AS c
            JOIN pacientes AS p ON p.id = c.paciente_id
            {where_clause}
            ORDER BY c.data DESC, c.horario DESC
            """,
            parametros,
        ).fetchall()
    return render_template(
        "consultas.html",
        consultas=registros,
        status_filtro=status_filtro if status_filtro in CONSULTA_STATUSES else "",
        statuses=CONSULTA_STATUSES,
    )


def get_patients_for_form():
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, nome FROM pacientes ORDER BY nome ASC"
        ).fetchall()


@app.route("/consultas/novo", methods=["GET", "POST"])
def cadastrar_consulta():
    if request.method == "POST":
        dados = consultation_form_data()
        if valid_consultation(dados):
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO consultas
                        (paciente_id, data, horario, tipo, status, observacoes)
                    VALUES
                        (:paciente_id, :data, :horario, :tipo, :status, :observacoes)
                    """,
                    dados,
                )
            flash("Consulta cadastrada com sucesso.", "success")
            return redirect(url_for("consultas"))
        return render_template(
            "cadastrar_consulta.html",
            pacientes=get_patients_for_form(),
            consulta=dados,
            statuses=CONSULTA_STATUSES,
        )
    return render_template(
        "cadastrar_consulta.html",
        pacientes=get_patients_for_form(),
        consulta={},
        statuses=CONSULTA_STATUSES,
    )


@app.route("/consultas/<int:consulta_id>/editar", methods=["GET", "POST"])
def editar_consulta(consulta_id):
    with get_connection() as connection:
        consulta = connection.execute(
            "SELECT * FROM consultas WHERE id = ?", (consulta_id,)
        ).fetchone()
    if consulta is None:
        abort(404)

    if request.method == "POST":
        dados = consultation_form_data()
        if valid_consultation(dados):
            dados["id"] = consulta_id
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE consultas
                    SET paciente_id = :paciente_id, data = :data, horario = :horario,
                        tipo = :tipo, status = :status, observacoes = :observacoes
                    WHERE id = :id
                    """,
                    dados,
                )
            flash("Consulta atualizada com sucesso.", "success")
            return redirect(url_for("consultas"))
        consulta = {**consulta, **dados}
    return render_template(
        "editar_consulta.html",
        consulta=consulta,
        pacientes=get_patients_for_form(),
        statuses=CONSULTA_STATUSES,
    )


@app.route("/consultas/<int:consulta_id>/excluir", methods=["POST"])
def excluir_consulta(consulta_id):
    with get_connection() as connection:
        consulta = connection.execute(
            "SELECT id FROM consultas WHERE id = ?", (consulta_id,)
        ).fetchone()
        if consulta is None:
            abort(404)
        connection.execute("DELETE FROM consultas WHERE id = ?", (consulta_id,))
    flash("Consulta excluída com sucesso.", "success")
    return redirect(url_for("consultas"))


@app.route("/api/pacientes")
def api_pacientes():
    with get_connection() as connection:
        registros = connection.execute(
            """
            SELECT id, nome, nascimento, telefone, email
            FROM pacientes
            ORDER BY nome ASC
            """
        ).fetchall()
    return jsonify([dict(paciente) for paciente in registros])


with app.app_context():
    initialize_database()


if __name__ == "__main__":
    # Debug pode ser ativado localmente, mas nunca quando APP_ENV for production.
    app.run(debug=APP_ENV != "production" and os.environ.get("FLASK_DEBUG") == "1")
