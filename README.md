# SupportHub

API de gestão de chamados técnicos, desenvolvida em Django + Django Rest Framework.

🔗 **Aplicação publicada:** https://supporthub-led7.onrender.com ([documentação interativa](https://supporthub-led7.onrender.com/api/docs/))

## Índice

- [Objetivo do projeto](#objetivo-do-projeto)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar localmente (sem Docker)](#como-rodar-localmente-sem-docker)
- [Como rodar com Docker Compose](#como-rodar-com-docker-compose)
- [Migrações](#migrações)
- [Criando um superusuário](#criando-um-superusuário)
- [Populando o banco com dados de exemplo (seed)](#populando-o-banco-com-dados-de-exemplo-seed)
- [Notificação por e-mail (assíncrona)](#notificação-por-e-mail-assíncrona)
- [Rodando os testes](#rodando-os-testes)
- [Documentação da API (Swagger/Redoc)](#documentação-da-api-swaggerredoc)
- [CORS (integração com o frontend)](#cors-integração-com-o-frontend)
- [Endpoints principais](#endpoints-principais)
- [Exemplos de requisições](#exemplos-de-requisições)
- [CI — Integração Contínua](#ci--integração-contínua)
- [CD — Entrega Contínua](#cd--entrega-contínua)
- [Roadmap / Pendências](#roadmap--pendências)

## Objetivo do projeto

O SupportHub é uma API RESTful para gestão de chamados técnicos de uma empresa de suporte. Permite que **clientes** abram chamados e acompanhem apenas os próprios, enquanto **atendentes** e **administradores** têm visibilidade total, podendo classificar, priorizar e atualizar o andamento de qualquer chamado.

O projeto cobre o ciclo completo de uma API back-end pronta pra produção: modelagem de dados, autenticação e permissões por perfil, testes automatizados, containerização e pipelines de integração/entrega contínua.

## Tecnologias utilizadas

**Linguagem e framework**
- Python 3.12
- Django 6.0
- Django Rest Framework

**Banco de dados**
- PostgreSQL 16

**Autenticação e API**
- JWT via `djangorestframework-simplejwt`
- `django-filter` (filtros e busca)
- `drf-spectacular` (documentação OpenAPI/Swagger/Redoc)
- `django-cors-headers` (libera acesso do frontend em outra origem)

**Infraestrutura**
- Docker / Docker Compose
- Gunicorn (servidor WSGI de produção)
- GitHub Actions (CI/CD)
- GitHub Container Registry — ghcr.io (registry de imagens)

**Tarefas assíncronas e e-mail**
- Celery + Redis (fila de tarefas assíncronas)
- Brevo (envio de e-mail transacional)

**Testes**
- pytest / pytest-django

**Ferramentas de desenvolvimento** (dev-only, não vão pro runtime/produção)
- `pre-commit` (verificação local de schema OpenAPI antes do commit)

## Estrutura do repositório

```
supporthub/
├── .github/
│   └── workflows/
│       ├── ci.yml              # roda a suite de testes a cada push/PR
│       └── docker-publish.yml  # builda e publica a imagem no ghcr.io a cada tag de versão
├── backend/
│   ├── core/                   # settings, urls, celery.py e email.py (Brevo)
│   ├── users/                   # usuário customizado (perfis) + comandos create_user/seed
│   ├── customers/               # cadastro de clientes
│   ├── categories/              # categorias de chamados
│   ├── tickets/                 # chamados técnicos + tasks.py (notificação assíncrona)
│   ├── interactions/            # histórico de interações dos chamados
│   ├── scripts/
│   │   ├── entrypoint.sh         # entrypoint do container (migrations/seed/gunicorn/worker)
│   │   └── check_openapi.py      # usado pelo hook de pre-commit
│   ├── conftest.py               # fixtures compartilhadas dos testes (pytest)
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── openapi.yml                # schema OpenAPI exportado (ver seção de Documentação)
│   ├── Dockerfile
│   ├── .dockerignore
│   └── manage.py
├── frontend/                     # (ainda não implementado — ver Roadmap)
├── compose.yaml                  # sobe banco, redis, backend e worker do celery juntos
├── .pre-commit-config.yaml       # hook local: valida se o openapi.yml está atualizado
├── LICENSE
└── README.md
```

Cada app Django dentro de `backend/` segue a mesma organização interna: `models.py`, `serializers.py`, `views.py`, `admin.py`, `tests.py` e `migrations/`.

## Como rodar localmente (sem Docker)

O Django roda direto via ambiente virtual, mas ainda precisa de um PostgreSQL acessível — a forma mais simples é subir só o banco via Docker (não precisa da aplicação em container pra isso).

```bash
cd backend

# ambiente virtual
python -m venv venv
venv\Scripts\Activate.ps1        # Windows (PowerShell)
# source venv/bin/activate       # Linux/Mac

pip install -r requirements.txt

# variáveis de ambiente
cp .env.example .env             # ajuste os valores se necessário

# banco de dados (só o Postgres, via Docker, na raiz do repositório)
cd ..
docker compose up -d db
cd backend

# migrações e execução
python manage.py migrate
python manage.py runserver
```

A API fica disponível em `http://localhost:8000`.

## Como rodar com Docker Compose

Sobe 4 serviços, cada um em seu container: `db` (PostgreSQL), `redis`, `backend` (API) e `worker` (Celery, processa os e-mails assíncronos).

```bash
# na raiz do repositório (onde está o compose.yaml)
cp backend/.env.example backend/.env   # ajuste os valores se necessário

docker compose up -d --build
```

Isso constrói a imagem do backend (`backend/Dockerfile`, reaproveitada tanto pelo `backend` quanto pelo `worker`, diferenciados pela variável `PROCESS_TYPE`), sobe o Postgres e o Redis com healthcheck, e só inicia `backend`/`worker` depois que as dependências estiverem prontas (`depends_on: condition: service_healthy`).

A API fica disponível em `http://localhost:8000`.

Para parar os containers (mantendo os dados do banco):

```bash
docker compose down
```

Para parar e apagar também o volume do banco:

```bash
docker compose down -v
```

## Migrações

**Local (venv):**

```bash
cd backend
python manage.py migrate
```

**Via Docker Compose (ambiente de desenvolvimento):** as migrations **não** rodam automaticamente — o `compose.yaml` da raiz define `RUN_MIGRATIONS: "false"` de propósito, pra manter controle manual sobre quando o schema do banco muda.

```bash
docker compose exec backend python manage.py migrate
```

**Em produção:** o entrypoint da imagem (`backend/entrypoint.sh`) roda `migrate` automaticamente antes de iniciar o Gunicorn, sempre que o container sobe — basta não definir `RUN_MIGRATIONS=false` (esse é o comportamento padrão da imagem publicada no `ghcr.io`).

Se algum model for alterado, gere a migration correspondente antes de aplicar:

```bash
python manage.py makemigrations
```

## Criando um superusuário

O projeto tem um comando customizado (`create_user`) que já cria o usuário com o `role` (perfil) desejado — quando o perfil é `admin`, `is_staff` e `is_superuser` são setados automaticamente.

```bash
python manage.py create_user --username admin --role admin --password "sua_senha" --email admin@supporthub.com
```

Outros perfis disponíveis: `cliente` (padrão, se `--role` for omitido) e `atendente`.

```bash
python manage.py create_user --username atendente1 --role atendente --password "sua_senha"
```

`--email` é opcional (fica em branco se omitido). Se `--password` for omitido, a senha é pedida de forma segura (sem aparecer no terminal). Via Docker Compose, prefixe com `docker compose exec backend`.

## Populando o banco com dados de exemplo (seed)

Há um comando `seed` que cria, de forma **idempotente** (rodar de novo não duplica nada), um conjunto inicial de dados:

- Usuário `admin` (perfil administrador)
- Usuário `atendente1` (perfil atendente)
- As 5 categorias sugeridas no case (Erro no sistema, Solicitação de acesso, Problema financeiro, Suporte técnico, Dúvida geral)
- 3 clientes fictícios (`cliente1`, `cliente2`, `cliente3`), cada um já com o próprio cadastro de `Customer`

```bash
python manage.py seed
```

**Senha dos usuários criados:** vem da variável de ambiente `SEED_PASSWORD`.

- Em desenvolvimento (`DEBUG=True`), se `SEED_PASSWORD` não estiver definida, o comando usa uma senha padrão insegura e avisa isso no terminal — só pra facilitar testar localmente.
- Em produção (`DEBUG=False`), `SEED_PASSWORD` é **obrigatória** — o comando recusa rodar sem ela (`CommandError`), pra nunca criar usuários com senha previsível num ambiente real.

**Execução automática:** o `entrypoint.sh` do container roda `seed` automaticamente a cada start, logo após o `migrate` (controlado pela variável `RUN_SEED`, análoga ao `RUN_MIGRATIONS`). Em desenvolvimento (`compose.yaml`), isso vem desativado (`RUN_SEED: "false"`) — rode manualmente quando quiser. **Em produção (Render), como não há acesso a shell, isso roda sozinho a cada deploy** — por isso é essencial cadastrar `SEED_PASSWORD` (e uma `DJANGO_SECRET_KEY` própria) nas variáveis de ambiente do serviço antes do primeiro deploy, senão o container falha ao subir.

## Notificação por e-mail (assíncrona)

Quando um chamado muda de **status** (via API, por atendente/admin), o cliente recebe um e-mail automático — processado em segundo plano por um worker Celery, sem bloquear a requisição HTTP.

**Debounce:** a notificação não é enviada na hora — ela é agendada com um atraso (30s por padrão). Se o status mudar de novo dentro dessa janela, só a **última** mudança efetivamente dispara o e-mail (as anteriores são descartadas silenciosamente). Isso evita mandar um e-mail para cada edição rápida em sequência.

**Envio via Brevo, com fallback automático:** a função `core/email.py` só chama a API do Brevo se `BREVO_API_KEY` e `BREVO_SENDER_EMAIL` estiverem configuradas no ambiente. Caso contrário, o e-mail é apenas **impresso no console** (`[EMAIL:CONSOLE] ...`) — útil em desenvolvimento, ou enquanto a verificação de domínio no Brevo ainda não foi concluída.

```bash
# .env
REDIS_URL=redis://localhost:6379/0    # broker do Celery
BREVO_API_KEY=
BREVO_SENDER_EMAIL=
```

**Requer o worker rodando.** Via `docker compose up`, ele já sobe junto (serviço `worker`). Rodando localmente sem Docker, é preciso iniciar o worker manualmente numa aba separada:

```bash
cd backend
celery -A core worker --loglevel=info
```

Sem o worker ativo, as tasks ficam enfileiradas no Redis aguardando alguém processá-las — o e-mail simplesmente não sai até o worker rodar.

## Rodando os testes

A suíte usa `pytest` + `pytest-django`, com fixtures compartilhadas em `conftest.py` (usuários de cada perfil, categoria, cliente e chamado de teste). Precisa do Postgres acessível (mesma exigência do resto do projeto).

**Local (venv):**

```bash
cd backend
pytest -v
```

**Via Docker Compose:**

```bash
docker compose exec backend pytest -v
```

Pra rodar só os testes de um app específico:

```bash
pytest tickets/tests.py -v
```

## Documentação da API (Swagger/Redoc)

A documentação é gerada automaticamente a partir dos serializers e viewsets (via `drf-spectacular`), com a API rodando localmente (`http://localhost:8000`):

| Rota | Descrição |
|---|---|
| `/api/schema/` | Schema OpenAPI 3.0 bruto (YAML) |
| `/api/docs/` | Swagger UI — interface interativa, permite testar os endpoints direto no navegador |
| `/api/redoc/` | Redoc — documentação estática, navegação mais limpa |

Para testar endpoints autenticados pelo Swagger UI: gere um token em `/api/token/`, clique em **Authorize** no topo da página e informe `Bearer <access_token>`.

**Auto-preenchimento do token:** o template do Swagger UI foi customizado (`backend/templates/drf_spectacular/swagger_ui.js`) para detectar automaticamente as respostas de `/api/token/` e `/api/token/refresh/` — assim que uma dessas chamadas retorna com sucesso, o `access` token é aplicado automaticamente no **Authorize**, sem precisar copiar e colar manualmente.

O arquivo [`backend/openapi.yml`](backend/openapi.yml) é uma cópia estática do schema, versionada no repositório — útil pra importar em ferramentas como Postman/Insomnia sem precisar da API rodando. Sempre que a API mudar, regenere com:

```bash
python manage.py spectacular --file openapi.yml
```

**Verificação automática (local):** há um hook de `pre-commit` que bloqueia o commit se `openapi.yml` estiver desatualizado em relação a mudanças em `models.py`, `serializers.py`, `views.py` ou `urls.py`. Pra ativar (uma vez, por clone):

```bash
pip install pre-commit
pre-commit install
```

O hook roda com o Python ativo no terminal — ative o `venv` antes de commitar.

## CORS (integração com o frontend)

As origens permitidas vêm da variável `CORS_ALLOWED_ORIGINS` (lista separada por vírgula, **com o esquema incluído**, ex.: `http://localhost:5173`). Sem essa variável definida, o default cobre as portas comuns de Vite/CRA em desenvolvimento:

```bash
# .env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

⚠️ Origens sem o esquema (`http://`/`https://`) fazem o Django recusar subir (`corsheaders.E013`) — `manage.py check` acusa isso antes mesmo de tentar rodar o servidor.

## Endpoints principais

**Autenticação**

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/token/` | Login — retorna `access` e `refresh` tokens (JWT) |
| POST | `/api/token/refresh/` | Renova o `access` token a partir do `refresh` |

**Categorias** — CRUD completo; escrita restrita a `admin`, leitura para qualquer autenticado

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/categories/` | Lista categorias |
| POST | `/api/categories/` | Cria categoria (admin) |
| GET/PATCH/DELETE | `/api/categories/{id}/` | Detalhe/atualiza/remove categoria (admin) |

**Clientes** — cliente vê/edita só o próprio cadastro; atendente/admin veem todos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/customers/` | Lista clientes (escopo depende do perfil) |
| POST | `/api/customers/` | Cria cadastro de cliente |
| GET/PATCH | `/api/customers/{id}/` | Detalhe/atualiza cliente |
| DELETE | `/api/customers/{id}/` | Desativa cliente (soft delete — admin/atendente) |

**Chamados** — cliente vê/cria só os próprios; atendente/admin têm acesso total e controlam status/prioridade/responsável

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/tickets/` | Lista chamados (aceita filtros e busca — ver abaixo) |
| POST | `/api/tickets/` | Abre um chamado |
| GET/PATCH/DELETE | `/api/tickets/{id}/` | Detalhe/atualiza/remove chamado |
| GET | `/api/tickets/{id}/interactions/` | Lista o histórico de interações do chamado |
| POST | `/api/tickets/{id}/interactions/` | Registra uma nova interação no chamado |

Filtros disponíveis em `/api/tickets/`: `?status=`, `?priority=`, `?category=`, `?customer=`, `?assigned_to=`, `?search=` (busca por título/descrição), `?page=`.

**Documentação e administração**

| Rota | Descrição |
|---|---|
| `/api/schema/`, `/api/docs/`, `/api/redoc/` | Documentação da API (ver seção específica) |
| `/admin/` | Django Admin |

## Exemplos de requisições

> Os payloads abaixo evitam acentos de propósito — alguns terminais (Git Bash no Windows, principalmente) corrompem caracteres acentuados dentro de `curl -d '...'`, causando erro de encoding no servidor. Fora isso, a API aceita normalmente texto acentuado em UTF-8.

**1. Login (obter token JWT)**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "sua_senha"}'
```

Resposta:
```json
{ "refresh": "eyJhbGciOi...", "access": "eyJhbGciOi..." }
```

Use o `access` no header `Authorization: Bearer <access_token>` nas próximas requisições.

**2. Criar uma categoria (admin)**

```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Erro no sistema", "description": "Falhas e bugs reportados pelo cliente"}'
```

**3. Cadastrar-se como cliente**

```bash
curl -X POST http://localhost:8000/api/customers/ \
  -H "Authorization: Bearer <access_token_do_cliente>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria Silva", "email": "maria@exemplo.com", "phone": "11999990000"}'
```

**4. Abrir um chamado (cliente)**

```bash
curl -X POST http://localhost:8000/api/tickets/ \
  -H "Authorization: Bearer <access_token_do_cliente>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Nao consigo logar", "description": "Erro 500 ao acessar o sistema", "category": 1}'
```

`customer`, `status`, `priority` e `assigned_to` não podem ser definidos pelo cliente — são preenchidos automaticamente ou restritos a atendente/admin.

**5. Atendente altera status e assume o chamado**

```bash
curl -X PATCH http://localhost:8000/api/tickets/1/ \
  -H "Authorization: Bearer <access_token_do_atendente>" \
  -H "Content-Type: application/json" \
  -d '{"status": "em_atendimento", "priority": "alta", "assigned_to": 2}'
```

**6. Filtrar chamados**

```bash
curl "http://localhost:8000/api/tickets/?status=aberto&priority=alta&search=login" \
  -H "Authorization: Bearer <access_token>"
```

**7. Registrar uma interação no chamado**

```bash
curl -X POST http://localhost:8000/api/tickets/1/interactions/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Ja verificamos o problema, aguardando confirmacao do cliente."}'
```

## CI — Integração Contínua

Definido em [`.github/workflows/ci.yml`](.github/workflows/ci.yml), roda automaticamente a cada `push` (qualquer branch) e a cada `pull request` pra `main`:

1. Faz checkout do código
2. Sobe um serviço PostgreSQL (com healthcheck)
3. Instala as dependências (`pip install -r requirements.txt`)
4. Roda as migrations contra o banco de teste
5. Executa a suíte de testes (`pytest -v`)

Se qualquer etapa falhar, o workflow falha e fica visível na aba **Actions** do repositório — inclusive em pull requests, antes do merge.

## CD — Entrega Contínua

**Aplicação publicada:** https://supporthub-led7.onrender.com (documentação interativa em [`/api/docs/`](https://supporthub-led7.onrender.com/api/docs/))

O fluxo de entrega é totalmente automatizado a partir de uma tag de versão:

1. Cria-se e envia-se uma tag (`git tag vX.Y.Z && git push origin vX.Y.Z`)
2. O workflow [`docker-publish.yml`](.github/workflows/docker-publish.yml) builda a imagem e publica no GitHub Container Registry com duas tags: a da versão (`ghcr.io/ki-kneip/supporthub:vX.Y.Z`) e `:latest`
3. Ainda no mesmo workflow, um último step dispara o **deploy hook do Render** (URL armazenada como secret `RENDER_DEPLOY_HOOK`, no Environment `Prod` do repositório)
4. O serviço no Render está configurado para rodar a partir da imagem `ghcr.io/ki-kneip/supporthub:latest` — ao receber o hook, ele puxa a imagem recém-publicada e reinicia

Ou seja: **nenhuma etapa manual** é necessária para colocar uma nova versão no ar além de taguear e dar push — build, publicação da imagem e deploy acontecem em cadeia.

Como o `entrypoint.sh` da imagem roda `migrate` e `seed` automaticamente antes do Gunicorn subir (ver seções [Migrações](#migrações) e [Populando o banco com dados de exemplo (seed)](#populando-o-banco-com-dados-de-exemplo-seed)), o ambiente de produção fica pronto para uso — incluindo um usuário `admin` e dados de exemplo — sem precisar de acesso a shell no Render.

## Roadmap / Pendências

> Espaço reservado para o que ainda falta implementar: frontend e outras evoluções futuras do projeto.

**Frontend**
- Ainda não implementado. Pasta `frontend/` reservada na raiz do repositório para essa etapa futura.

**Diferenciais do case ainda não implementados**
- Relatório de cobertura de testes (`pytest-cov` / `coverage.py`)
- Registro de logs estruturado

**Observação sobre o e-mail transacional:** o domínio de envio no Brevo ainda não foi verificado — os e-mails atualmente saem pelo remetente de sandbox deles. Funciona (testado com credenciais reais), mas a entregabilidade/remetente final deve melhorar após a verificação de domínio ser concluída.

**Observação sobre os tokens JWT:** avaliei mover `access`/`refresh` para cookies `httpOnly` (mais seguro contra roubo via XSS que `localStorage`) e decidi não fazer essa mudança neste case — é viável tecnicamente, mas adiciona complexidade (CORS com credentials, proteção CSRF, flags de cookie variando por ambiente) desnecessária para um projeto de avaliação técnica. Os tokens continuam sendo retornados no corpo da resposta de `/api/token/`.
