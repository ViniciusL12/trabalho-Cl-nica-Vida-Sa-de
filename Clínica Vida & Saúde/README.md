# Clínica Vida & Saúde

Sistema demonstrativo de gestão de pacientes e consultas, feito com Python, Flask, SQLite, HTML, CSS e JavaScript. Os registros iniciais são fictícios e servem somente para demonstração. Não utilize este projeto para armazenar dados reais de saúde sem uma avaliação de segurança, privacidade e conformidade legal.

## O que o sistema oferece

- Painel com totais de pacientes, consultas e consultas de hoje.
- Cadastro, listagem, pesquisa, edição e exclusão de pacientes.
- Cadastro, listagem, edição, alteração de status e exclusão de consultas.
- Associação de cada consulta a um paciente.
- Filtro de consultas por status e listagem de próximas consultas.
- API JSON em `GET /api/pacientes`.
- Busca linear e ordenação Bubble Sort demonstradas na listagem de pacientes.
- Banco SQLite criado automaticamente em `instance/clinica.db`.
- Botão de modo escuro na barra superior e textos ampliados para melhor leitura.
- Banner visual responsivo com a recepção da clínica em `static/img/clinica.png`.
- Máscara de telefone brasileiro em cadastros, com normalização também no servidor antes de salvar no SQLite.

## Executar no Windows

1. Instale o Python 3.10 ou mais recente em [python.org](https://www.python.org/downloads/). Durante a instalação, marque **Add Python to PATH**.
2. Abra o PowerShell ou o Terminal do VS Code na pasta do projeto.
3. Crie um ambiente virtual:

   ```powershell
   py -m venv .venv
   ```

4. Ative o ambiente virtual:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   Se o PowerShell bloquear a ativação, execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` uma vez e tente ativar novamente. Como alternativa, no Prompt de Comando use `.\.venv\Scripts\activate.bat`.

5. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Inicie o sistema:

   ```powershell
   python app.py
   ```

7. Abra `http://127.0.0.1:5000` no navegador. Para parar o servidor, volte ao terminal e pressione `Ctrl+C`.

O arquivo do banco de dados é criado automaticamente na primeira execução em `instance\clinica.db`. O banco fica fora do Git e seus registros locais não são apagados ao iniciar o sistema.

## API

Acesse `http://127.0.0.1:5000/api/pacientes` para receber os pacientes em JSON.

## Publicar no Render

O `Procfile` inicia o app com Gunicorn (`web: gunicorn app:app`). No Render, configure:

- **Root Directory:** deixe em branco se `app.py`, `Procfile` e `requirements.txt` estiverem na raiz do repositório. Se o projeto estiver dentro de uma subpasta do repositório, informe o caminho dessa subpasta.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- Variável `APP_ENV=production`
- Variável `SECRET_KEY` com um valor aleatório forte, mantido somente nas variáveis de ambiente do Render.

As dependências de produção estão fixadas em `requirements.txt` para instalações reproduzíveis. Antes de publicar, confirme também que esses arquivos foram enviados ao branch conectado ao serviço no GitHub. Se o Render disser que não encontra `requirements.txt`, confira o Root Directory e se o arquivo está nesse branch.

O modo debug é desligado por padrão e não pode ser ativado com `APP_ENV=production`. O SQLite dentro do disco local de um serviço hospedado pode não ser persistente em todos os tipos de serviço/implantação; configure um disco persistente, defina `DATABASE_PATH` para um caminho dentro dele ou use um banco gerenciado. Este exemplo não inclui autenticação e não deve receber informações reais de pacientes.
