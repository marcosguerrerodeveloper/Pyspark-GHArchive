# Fase 0 — Exploración de un fichero horario de GH Archive

Fichero inspeccionado: `2026-08-12-14.json.gz`

Generado por `exploracion/analizar_hora.py`. Todo lo que sigue está
observado en los datos, no inferido de la documentación.


## 1. Volumen

| Medida | Valor |
|---|---|
| Tamaño comprimido | 22,891,223 bytes (21.83 MiB) |
| Tamaño descomprimido | 111,671,173 bytes (106.50 MiB) |
| Ratio de compresión | 4.88× |
| Eventos | 162,301 |
| Líneas no parseables | 0 |
| `created_at` mínimo | 2026-08-12T14:00:00Z |
| `created_at` máximo | 2026-08-12T14:59:59Z |

## 2. Tipos de evento

| Tipo | Eventos | % |
|---|---:|---:|
| `PushEvent` | 148,551 | 91.53% |
| `CreateEvent` | 7,734 | 4.77% |
| `DeleteEvent` | 3,804 | 2.34% |
| `PullRequestEvent` | 770 | 0.47% |
| `IssuesEvent` | 461 | 0.28% |
| `IssueCommentEvent` | 385 | 0.24% |
| `PullRequestReviewEvent` | 228 | 0.14% |
| `PullRequestReviewCommentEvent` | 147 | 0.09% |
| `WatchEvent` | 118 | 0.07% |
| `ReleaseEvent` | 51 | 0.03% |
| `ForkEvent` | 35 | 0.02% |
| `MemberEvent` | 8 | 0.00% |
| `PublicEvent` | 5 | 0.00% |
| `CommitCommentEvent` | 3 | 0.00% |
| `GollumEvent` | 1 | 0.00% |

## 5. Duplicados por `id`

**1 `id` aparecen más de una vez** (2 eventos implicados).

| `id` | Repeticiones | ¿Contenido idéntico? |
|---|---:|---|
| `13173052275` | 2 | sí |

## 6. Truncamiento de commits en `PushEvent`

`PushEvent` analizados: **148,551**

Claves realmente presentes en `payload`:

| Clave | Ocurrencias | Cobertura |
|---|---:|---:|
| `repository_id` | 148,551 | 100.00% |
| `push_id` | 148,551 | 100.00% |
| `ref` | 148,551 | 100.00% |
| `head` | 148,551 | 100.00% |
| `before` | 148,551 | 100.00% |

**Ni `commits` ni `size` existen en el payload.** La pregunta del
truncamiento queda respondida por la vía inesperada: no hay array de
commits que truncar. `PushEvent` aporta el hecho del push (quién, a qué
repo, a qué rama, cuándo) y los SHA `head`/`before`, pero no el detalle
de los commits ni su número.

## 4. ¿Está el lenguaje del repo en `PullRequestEvent`?

**Es el supuesto crítico de la pregunta de negocio 1.**

`PullRequestEvent` analizados: 770

Antes de buscar el lenguaje, qué trae de verdad `payload.pull_request`:

| Clave | Ocurrencias | Cobertura |
|---|---:|---:|
| `url` | 770 | 100.00% |
| `id` | 770 | 100.00% |
| `number` | 770 | 100.00% |
| `head` | 770 | 100.00% |
| `base` | 770 | 100.00% |

| Ruta candidata | Existe la clave | No nula | Cobertura |
|---|---:|---:|---:|
| `payload.pull_request.base.repo.language` | 0 | 0 | 0.00% |
| `payload.pull_request.head.repo.language` | 0 | 0 | 0.00% |
| `repo.language` | 0 | 0 | 0.00% |
| `payload.repository.language` | 0 | 0 | 0.00% |

## 7. Señales de bot disponibles

- Actores con login: **162,301**
- Logins terminados en `[bot]`: **16,547** de **380** cuentas distintas (10.20% de los eventos)

| Bot | Eventos |
|---|---:|
| `github-actions[bot]` | 12,875 |
| `dependabot[bot]` | 847 |
| `renovate[bot]` | 380 |
| `pull[bot]` | 357 |
| `cursor[bot]` | 265 |
| `github-merge-queue[bot]` | 259 |
| `swa-synthetics[bot]` | 107 |
| `trunk-io[bot]` | 86 |
| `codelinaro-mirror-sync[bot]` | 82 |
| `vercel[bot]` | 60 |
| `coderabbitai[bot]` | 57 |
| `swa-runner-app[bot]` | 57 |
| `chatgpt-codex-connector[bot]` | 35 |
| `devin-ai-integration[bot]` | 31 |
| `copybara-service[bot]` | 30 |
| `arena-ai-coding-agent[bot]` | 28 |
| `aws-connector-for-github[bot]` | 27 |
| `shipmateapp[bot]` | 24 |
| `konflux-staging[bot]` | 22 |
| `claude[bot]` | 20 |

Campos de tipo de usuario observados:

| Ruta y valor | Ocurrencias |
|---|---:|
| `payload.issue.user.type=User` | 762 |
| `payload.issue.user.type=Bot` | 84 |

## 8. Campos temporales del PR por acción

Sin esto no hay pregunta de negocio 2 (latencia hasta review y hasta merge).

Acciones observadas en `PullRequestEvent`:

| Acción | Eventos |
|---|---:|
| `opened` | 265 |
| `merged` | 245 |
| `labeled` | 216 |
| `unlabeled` | 25 |
| `closed` | 10 |
| `assigned` | 8 |
| `reopened` | 1 |

**Ningún campo temporal del PR está presente en el payload.** La latencia
no se puede leer: hay que derivarla del `created_at` de los propios
eventos, uniéndolos por `payload.pull_request.id`.

| Acción | `created_at` | `updated_at` | `closed_at` | `merged_at` | `merged` | Total |
|---|---:|---:|---:|---:|---:|---:|
| `assigned` | 0 | 0 | 0 | 0 | 0 | 8 |
| `closed` | 0 | 0 | 0 | 0 | 0 | 10 |
| `labeled` | 0 | 0 | 0 | 0 | 0 | 216 |
| `merged` | 0 | 0 | 0 | 0 | 0 | 245 |
| `opened` | 0 | 0 | 0 | 0 | 0 | 265 |
| `reopened` | 0 | 0 | 0 | 0 | 0 | 1 |
| `unlabeled` | 0 | 0 | 0 | 0 | 0 | 25 |

## 9. Identificador estable de PR entre eventos

Determina con qué clave se unen `PullRequestEvent` y `PullRequestReviewEvent`.

| Tipo de evento | Ruta | Presente |
|---|---|---:|
| `PullRequestEvent` | `payload.pull_request.id` | 770 |
| `PullRequestEvent` | `payload.pull_request.number` | 770 |
| `PullRequestEvent` | `payload.number` | 770 |
| `PullRequestReviewCommentEvent` | `payload.pull_request.id` | 147 |
| `PullRequestReviewCommentEvent` | `payload.pull_request.number` | 147 |
| `PullRequestReviewEvent` | `payload.pull_request.id` | 228 |
| `PullRequestReviewEvent` | `payload.pull_request.number` | 228 |

## 3. Esquema observado del `payload`


### `PullRequestEvent`  (770 eventos)

| Ruta | Tipos observados | Ocurrencias |
|---|---|---:|
| `payload.action` | `str`×770 | 770 |
| `payload.assignee` | `dict`×8 | 8 |
| `payload.assignee.avatar_url` | `str`×8 | 8 |
| `payload.assignee.events_url` | `str`×8 | 8 |
| `payload.assignee.followers_url` | `str`×8 | 8 |
| `payload.assignee.following_url` | `str`×8 | 8 |
| `payload.assignee.gists_url` | `str`×8 | 8 |
| `payload.assignee.gravatar_id` | `str`×8 | 8 |
| `payload.assignee.html_url` | `str`×8 | 8 |
| `payload.assignee.id` | `int`×8 | 8 |
| `payload.assignee.login` | `str`×8 | 8 |
| `payload.assignee.node_id` | `str`×8 | 8 |
| `payload.assignee.organizations_url` | `str`×8 | 8 |
| `payload.assignee.received_events_url` | `str`×8 | 8 |
| `payload.assignee.repos_url` | `str`×8 | 8 |
| `payload.assignee.site_admin` | `bool`×8 | 8 |
| `payload.assignee.starred_url` | `str`×8 | 8 |
| `payload.assignee.subscriptions_url` | `str`×8 | 8 |
| `payload.assignee.type` | `str`×8 | 8 |
| `payload.assignee.url` | `str`×8 | 8 |
| `payload.assignee.user_view_type` | `str`×8 | 8 |
| `payload.assignees` | `list`×8 | 8 |
| `payload.assignees[]` | `dict`×8 | 8 |
| `payload.assignees[].avatar_url` | `str`×8 | 8 |
| `payload.assignees[].events_url` | `str`×8 | 8 |
| `payload.assignees[].followers_url` | `str`×8 | 8 |
| `payload.assignees[].following_url` | `str`×8 | 8 |
| `payload.assignees[].gists_url` | `str`×8 | 8 |
| `payload.assignees[].gravatar_id` | `str`×8 | 8 |
| `payload.assignees[].html_url` | `str`×8 | 8 |
| `payload.assignees[].id` | `int`×8 | 8 |
| `payload.assignees[].login` | `str`×8 | 8 |
| `payload.assignees[].node_id` | `str`×8 | 8 |
| `payload.assignees[].organizations_url` | `str`×8 | 8 |
| `payload.assignees[].received_events_url` | `str`×8 | 8 |
| `payload.assignees[].repos_url` | `str`×8 | 8 |
| `payload.assignees[].site_admin` | `bool`×8 | 8 |
| `payload.assignees[].starred_url` | `str`×8 | 8 |
| `payload.assignees[].subscriptions_url` | `str`×8 | 8 |
| `payload.assignees[].type` | `str`×8 | 8 |
| `payload.assignees[].url` | `str`×8 | 8 |
| `payload.assignees[].user_view_type` | `str`×8 | 8 |
| `payload.label` | `dict`×233, `null`×8 | 241 |
| `payload.label.color` | `str`×233 | 233 |
| `payload.label.default` | `bool`×233 | 233 |
| `payload.label.description` | `str`×140, `null`×93 | 233 |
| `payload.label.id` | `int`×233 | 233 |
| `payload.label.name` | `str`×233 | 233 |
| `payload.label.node_id` | `str`×233 | 233 |
| `payload.label.url` | `str`×233 | 233 |
| `payload.labels` | `list`×241 | 241 |
| `payload.labels[]` | `dict`×233 | 233 |
| `payload.labels[].color` | `str`×233 | 233 |
| `payload.labels[].default` | `bool`×233 | 233 |
| `payload.labels[].description` | `str`×168, `null`×65 | 233 |
| `payload.labels[].id` | `int`×233 | 233 |
| `payload.labels[].name` | `str`×233 | 233 |
| `payload.labels[].node_id` | `str`×233 | 233 |
| `payload.labels[].url` | `str`×233 | 233 |
| `payload.number` | `int`×770 | 770 |
| `payload.pull_request` | `dict`×770 | 770 |
| `payload.pull_request.base` | `dict`×770 | 770 |
| `payload.pull_request.base.ref` | `str`×770 | 770 |
| `payload.pull_request.base.repo` | `dict`×770 | 770 |
| `payload.pull_request.base.repo.id` | `int`×770 | 770 |
| `payload.pull_request.base.repo.name` | `str`×770 | 770 |
| `payload.pull_request.base.repo.url` | `str`×770 | 770 |
| `payload.pull_request.base.sha` | `str`×770 | 770 |
| `payload.pull_request.head` | `dict`×770 | 770 |
| `payload.pull_request.head.ref` | `str`×770 | 770 |
| `payload.pull_request.head.repo` | `dict`×770 | 770 |
| `payload.pull_request.head.repo.id` | `int`×770 | 770 |
| `payload.pull_request.head.repo.name` | `str`×770 | 770 |
| `payload.pull_request.head.repo.url` | `str`×770 | 770 |
| `payload.pull_request.head.sha` | `str`×770 | 770 |
| `payload.pull_request.id` | `int`×770 | 770 |
| `payload.pull_request.number` | `int`×770 | 770 |
| `payload.pull_request.url` | `str`×770 | 770 |

<details><summary>Ejemplo real de <code>PullRequestEvent</code></summary>

```json
{
  "actor": {
    "avatar_url": "https://avatars.githubusercontent.com/u/39814207?",
    "display_login": "pull",
    "gravatar_id": "",
    "id": 39814207,
    "login": "pull[bot]",
    "url": "https://api.github.com/users/pull[bot]"
  },
  "created_at": "2026-08-12T14:00:09Z",
  "id": "13170617687",
  "payload": {
    "action": "labeled",
    "label": {
      "color": "ededed",
      "default": false,
      "description": null,
      "id": 6469516813,
      "name": ":arrow_heading_down: pull",
      "node_id": "LA_kwDOJfE0fc8AAAABgZz-DQ",
      "url": "https://api.github.com/repos/davidsolomon21cn/llama.cpp/labels/:arrow_heading_down:%20pull"
    },
    "labels": [
      {
        "color": "ededed",
        "default": false,
        "description": null,
        "id": 6469516813,
        "name": ":arrow_heading_down: pull",
        "node_id": "LA_kwDOJfE0fc8AAAABgZz-DQ",
        "url": "https://api.github.com/repos/davidsolomon21cn/llama.cpp/labels/:arrow_heading_down:%20pull"
      }
    ],
    "number": 1437,
    "pull_request": {
      "base": {
        "ref": "master",
        "repo": {
          "id": 636564605,
          "name": "llama.cpp",
          "url": "https://api.github.com/repos/davidsolomon21cn/llama.cpp"
        },
        "sha": "89e0aa6fd362617d9073e0dafc18e41241521572"
      },
      "head": {
        "ref": "master",
        "repo": {
          "id": 612354784,
          "name": "llama.cpp",
          "url": "https://api.github.com/repos/ggml-org/llama.cpp"
        },
        "sha": "9558fa44c92746a58dd07ad1bf0c889715b938a6"
      },
      "id": 4262949744,
      "number": 1437,
      "url": "https://api.github.com/repos/davidsolomon21cn/llama.cpp/pulls/1437"
    }
  },
  "public": true,
  "repo": {
    "id": 636564605,
    "name": "davidsolomon21cn/llama.cpp",
    "url": "https://api.github.com/repos/davidsolomon21cn/llama.cpp"
  },
  "type": "PullRequestEvent"
}
```

</details>


### `PullRequestReviewEvent`  (228 eventos)

| Ruta | Tipos observados | Ocurrencias |
|---|---|---:|
| `payload.action` | `str`×228 | 228 |
| `payload.pull_request` | `dict`×228 | 228 |
| `payload.pull_request.base` | `dict`×228 | 228 |
| `payload.pull_request.base.ref` | `str`×228 | 228 |
| `payload.pull_request.base.repo` | `dict`×228 | 228 |
| `payload.pull_request.base.repo.id` | `int`×228 | 228 |
| `payload.pull_request.base.repo.name` | `str`×228 | 228 |
| `payload.pull_request.base.repo.url` | `str`×228 | 228 |
| `payload.pull_request.base.sha` | `str`×228 | 228 |
| `payload.pull_request.head` | `dict`×228 | 228 |
| `payload.pull_request.head.ref` | `str`×228 | 228 |
| `payload.pull_request.head.repo` | `dict`×228 | 228 |
| `payload.pull_request.head.repo.id` | `int`×228 | 228 |
| `payload.pull_request.head.repo.name` | `str`×228 | 228 |
| `payload.pull_request.head.repo.url` | `str`×228 | 228 |
| `payload.pull_request.head.sha` | `str`×228 | 228 |
| `payload.pull_request.id` | `int`×228 | 228 |
| `payload.pull_request.number` | `int`×228 | 228 |
| `payload.pull_request.url` | `str`×228 | 228 |
| `payload.review` | `dict`×228 | 228 |
| `payload.review._links` | `dict`×228 | 228 |
| `payload.review._links.html` | `dict`×228 | 228 |
| `payload.review._links.html.href` | `str`×228 | 228 |
| `payload.review._links.pull_request` | `dict`×228 | 228 |
| `payload.review._links.pull_request.href` | `str`×228 | 228 |
| `payload.review.body` | `str`×118, `null`×110 | 228 |
| `payload.review.commit_id` | `str`×228 | 228 |
| `payload.review.html_url` | `str`×228 | 228 |
| `payload.review.id` | `int`×228 | 228 |
| `payload.review.node_id` | `str`×228 | 228 |
| `payload.review.pull_request_url` | `str`×228 | 228 |
| `payload.review.state` | `str`×228 | 228 |
| `payload.review.submitted_at` | `str`×228 | 228 |
| `payload.review.updated_at` | `str`×228 | 228 |
| `payload.review.user` | `dict`×228 | 228 |
| `payload.review.user.avatar_url` | `str`×228 | 228 |
| `payload.review.user.events_url` | `str`×228 | 228 |
| `payload.review.user.followers_url` | `str`×228 | 228 |
| `payload.review.user.following_url` | `str`×228 | 228 |
| `payload.review.user.gists_url` | `str`×228 | 228 |
| `payload.review.user.gravatar_id` | `str`×228 | 228 |
| `payload.review.user.html_url` | `str`×228 | 228 |
| `payload.review.user.id` | `int`×228 | 228 |
| `payload.review.user.login` | `str`×228 | 228 |
| `payload.review.user.node_id` | `str`×228 | 228 |
| `payload.review.user.organizations_url` | `str`×228 | 228 |
| `payload.review.user.received_events_url` | `str`×228 | 228 |
| `payload.review.user.repos_url` | `str`×228 | 228 |
| `payload.review.user.site_admin` | `bool`×228 | 228 |
| `payload.review.user.starred_url` | `str`×228 | 228 |
| `payload.review.user.subscriptions_url` | `str`×228 | 228 |
| `payload.review.user.type` | `str`×228 | 228 |
| `payload.review.user.url` | `str`×228 | 228 |
| `payload.review.user.user_view_type` | `str`×228 | 228 |

<details><summary>Ejemplo real de <code>PullRequestReviewEvent</code></summary>

```json
{
  "actor": {
    "avatar_url": "https://avatars.githubusercontent.com/u/175209400?",
    "display_login": "prabash-moj",
    "gravatar_id": "",
    "id": 175209400,
    "login": "prabash-moj",
    "url": "https://api.github.com/users/prabash-moj"
  },
  "created_at": "2026-08-12T14:00:00Z",
  "id": "13170607218",
  "org": {
    "avatar_url": "https://avatars.githubusercontent.com/u/2203574?",
    "gravatar_id": "",
    "id": 2203574,
    "login": "ministryofjustice",
    "url": "https://api.github.com/orgs/ministryofjustice"
  },
  "payload": {
    "action": "created",
    "pull_request": {
      "base": {
        "ref": "main",
        "repo": {
          "id": 789053149,
          "name": "hmpps-book-a-video-link-api",
          "url": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api"
        },
        "sha": "fdb688bc6d480f976ca1d132c65587fc34465980"
      },
      "head": {
        "ref": "task/BAVL-1426-show-all-appointments-in-vidoe-rooms",
        "repo": {
          "id": 789053149,
          "name": "hmpps-book-a-video-link-api",
          "url": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api"
        },
        "sha": "461d12006146387fa5eb766f6f999127917c2ea8"
      },
      "id": 4262664172,
      "number": 696,
      "url": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api/pulls/696"
    },
    "review": {
      "_links": {
        "html": {
          "href": "https://github.com/ministryofjustice/hmpps-book-a-video-link-api/pull/696#pullrequestreview-4917306224"
        },
        "pull_request": {
          "href": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api/pulls/696"
        }
      },
      "body": null,
      "commit_id": "461d12006146387fa5eb766f6f999127917c2ea8",
      "html_url": "https://github.com/ministryofjustice/hmpps-book-a-video-link-api/pull/696#pullrequestreview-4917306224",
      "id": 4917306224,
      "node_id": "PRR_kwDOLwf-3c8AAAABJRgjcA",
      "pull_request_url": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api/pulls/696",
      "state": "approved",
      "submitted_at": "2026-08-12T13:57:51Z",
      "updated_at": "2026-08-12T13:57:51Z",
      "user": {
        "avatar_url": "https://avatars.githubusercontent.com/u/175209400?v=4",
        "events_url": "https://api.github.com/users/prabash-moj/events{/privacy}",
        "followers_url": "https://api.github.com/users/prabash-moj/followers",
        "following_url": "https://api.github.com/users/prabash-moj/following{/other_user}",
        "gists_url": "https://api.github.com/users/prabash-moj/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/prabash-moj",
        "id": 175209400,
        "login": "prabash-moj",
        "node_id": "U_kgDOCnF7uA",
        "organizations_url": "https://api.github.com/users/prabash-moj/orgs",
        "received_events_url": "https://api.github.com/users/prabash-moj/received_events",
        "repos_url": "https://api.github.com/users/prabash-moj/repos",
        "site_admin": false,
        "starred_url": "https://api.github.com/users/prabash-moj/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/prabash-moj/subscriptions",
        "type": "User",
        "url": "https://api.github.com/users/prabash-moj",
        "user_view_type": "public"
      }
    }
  },
  "public": true,
  "repo": {
    "id": 789053149,
    "name": "ministryofjustice/hmpps-book-a-video-link-api",
    "url": "https://api.github.com/repos/ministryofjustice/hmpps-book-a-video-link-api"
  },
  "type": "PullRequestReviewEvent"
}
```

</details>


### `IssuesEvent`  (461 eventos)

| Ruta | Tipos observados | Ocurrencias |
|---|---|---:|
| `payload.action` | `str`×461 | 461 |
| `payload.assignee` | `dict`×20, `null`×3 | 23 |
| `payload.assignee.avatar_url` | `str`×20 | 20 |
| `payload.assignee.events_url` | `str`×20 | 20 |
| `payload.assignee.followers_url` | `str`×20 | 20 |
| `payload.assignee.following_url` | `str`×20 | 20 |
| `payload.assignee.gists_url` | `str`×20 | 20 |
| `payload.assignee.gravatar_id` | `str`×20 | 20 |
| `payload.assignee.html_url` | `str`×20 | 20 |
| `payload.assignee.id` | `int`×20 | 20 |
| `payload.assignee.login` | `str`×20 | 20 |
| `payload.assignee.node_id` | `str`×20 | 20 |
| `payload.assignee.organizations_url` | `str`×20 | 20 |
| `payload.assignee.received_events_url` | `str`×20 | 20 |
| `payload.assignee.repos_url` | `str`×20 | 20 |
| `payload.assignee.site_admin` | `bool`×20 | 20 |
| `payload.assignee.starred_url` | `str`×20 | 20 |
| `payload.assignee.subscriptions_url` | `str`×20 | 20 |
| `payload.assignee.type` | `str`×20 | 20 |
| `payload.assignee.url` | `str`×20 | 20 |
| `payload.assignee.user_view_type` | `str`×20 | 20 |
| `payload.assignees` | `list`×23 | 23 |
| `payload.assignees[]` | `dict`×20 | 20 |
| `payload.assignees[].avatar_url` | `str`×20 | 20 |
| `payload.assignees[].events_url` | `str`×20 | 20 |
| `payload.assignees[].followers_url` | `str`×20 | 20 |
| `payload.assignees[].following_url` | `str`×20 | 20 |
| `payload.assignees[].gists_url` | `str`×20 | 20 |
| `payload.assignees[].gravatar_id` | `str`×20 | 20 |
| `payload.assignees[].html_url` | `str`×20 | 20 |
| `payload.assignees[].id` | `int`×20 | 20 |
| `payload.assignees[].login` | `str`×20 | 20 |
| `payload.assignees[].node_id` | `str`×20 | 20 |
| `payload.assignees[].organizations_url` | `str`×20 | 20 |
| `payload.assignees[].received_events_url` | `str`×20 | 20 |
| `payload.assignees[].repos_url` | `str`×20 | 20 |
| `payload.assignees[].site_admin` | `bool`×20 | 20 |
| `payload.assignees[].starred_url` | `str`×20 | 20 |
| `payload.assignees[].subscriptions_url` | `str`×20 | 20 |
| `payload.assignees[].type` | `str`×20 | 20 |
| `payload.assignees[].url` | `str`×20 | 20 |
| `payload.assignees[].user_view_type` | `str`×20 | 20 |
| `payload.issue` | `dict`×461 | 461 |
| `payload.issue.active_lock_reason` | `null`×461 | 461 |
| `payload.issue.assignee` | `null`×380, `dict`×81 | 461 |
| `payload.issue.assignee.avatar_url` | `str`×81 | 81 |
| `payload.issue.assignee.events_url` | `str`×81 | 81 |
| `payload.issue.assignee.followers_url` | `str`×81 | 81 |
| `payload.issue.assignee.following_url` | `str`×81 | 81 |
| `payload.issue.assignee.gists_url` | `str`×81 | 81 |
| `payload.issue.assignee.gravatar_id` | `str`×81 | 81 |
| `payload.issue.assignee.html_url` | `str`×81 | 81 |
| `payload.issue.assignee.id` | `int`×81 | 81 |
| `payload.issue.assignee.login` | `str`×81 | 81 |
| `payload.issue.assignee.node_id` | `str`×81 | 81 |
| `payload.issue.assignee.organizations_url` | `str`×81 | 81 |
| `payload.issue.assignee.received_events_url` | `str`×81 | 81 |
| `payload.issue.assignee.repos_url` | `str`×81 | 81 |
| `payload.issue.assignee.site_admin` | `bool`×81 | 81 |
| `payload.issue.assignee.starred_url` | `str`×81 | 81 |
| `payload.issue.assignee.subscriptions_url` | `str`×81 | 81 |
| `payload.issue.assignee.type` | `str`×81 | 81 |
| `payload.issue.assignee.url` | `str`×81 | 81 |
| `payload.issue.assignee.user_view_type` | `str`×81 | 81 |
| `payload.issue.assignees` | `list`×461 | 461 |
| `payload.issue.assignees[]` | `dict`×81 | 81 |
| `payload.issue.assignees[].avatar_url` | `str`×81 | 81 |
| `payload.issue.assignees[].events_url` | `str`×81 | 81 |
| `payload.issue.assignees[].followers_url` | `str`×81 | 81 |
| `payload.issue.assignees[].following_url` | `str`×81 | 81 |
| `payload.issue.assignees[].gists_url` | `str`×81 | 81 |
| `payload.issue.assignees[].gravatar_id` | `str`×81 | 81 |
| `payload.issue.assignees[].html_url` | `str`×81 | 81 |
| `payload.issue.assignees[].id` | `int`×81 | 81 |
| `payload.issue.assignees[].login` | `str`×81 | 81 |
| `payload.issue.assignees[].node_id` | `str`×81 | 81 |
| `payload.issue.assignees[].organizations_url` | `str`×81 | 81 |
| `payload.issue.assignees[].received_events_url` | `str`×81 | 81 |
| `payload.issue.assignees[].repos_url` | `str`×81 | 81 |
| `payload.issue.assignees[].site_admin` | `bool`×81 | 81 |
| `payload.issue.assignees[].starred_url` | `str`×81 | 81 |
| `payload.issue.assignees[].subscriptions_url` | `str`×81 | 81 |
| `payload.issue.assignees[].type` | `str`×81 | 81 |
| `payload.issue.assignees[].url` | `str`×81 | 81 |
| `payload.issue.assignees[].user_view_type` | `str`×81 | 81 |
| `payload.issue.body` | `str`×449, `null`×12 | 461 |
| `payload.issue.closed_at` | `null`×365, `str`×96 | 461 |
| `payload.issue.comments` | `int`×461 | 461 |
| `payload.issue.comments_url` | `str`×461 | 461 |
| `payload.issue.created_at` | `str`×461 | 461 |
| `payload.issue.events_url` | `str`×461 | 461 |
| `payload.issue.html_url` | `str`×461 | 461 |
| `payload.issue.id` | `int`×461 | 461 |
| `payload.issue.issue_dependencies_summary` | `dict`×461 | 461 |
| `payload.issue.issue_dependencies_summary.blocked_by` | `int`×461 | 461 |
| `payload.issue.issue_dependencies_summary.blocking` | `int`×461 | 461 |
| `payload.issue.issue_dependencies_summary.total_blocked_by` | `int`×461 | 461 |
| `payload.issue.issue_dependencies_summary.total_blocking` | `int`×461 | 461 |
| `payload.issue.issue_field_values` | `list`×184 | 184 |
| `payload.issue.labels` | `list`×461 | 461 |
| `payload.issue.labels[]` | `dict`×350 | 350 |
| `payload.issue.labels[].color` | `str`×350 | 350 |
| `payload.issue.labels[].default` | `bool`×350 | 350 |
| `payload.issue.labels[].description` | `str`×314, `null`×36 | 350 |
| `payload.issue.labels[].id` | `int`×350 | 350 |
| `payload.issue.labels[].name` | `str`×350 | 350 |
| `payload.issue.labels[].node_id` | `str`×350 | 350 |
| `payload.issue.labels[].url` | `str`×350 | 350 |
| `payload.issue.labels_url` | `str`×461 | 461 |
| `payload.issue.locked` | `bool`×461 | 461 |
| `payload.issue.milestone` | `null`×339, `dict`×122 | 461 |
| `payload.issue.milestone.closed_at` | `null`×120, `str`×2 | 122 |
| `payload.issue.milestone.closed_issues` | `int`×122 | 122 |
| `payload.issue.milestone.created_at` | `str`×122 | 122 |
| `payload.issue.milestone.creator` | `dict`×122 | 122 |
| `payload.issue.milestone.creator.avatar_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.events_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.followers_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.following_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.gists_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.gravatar_id` | `str`×122 | 122 |
| `payload.issue.milestone.creator.html_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.id` | `int`×122 | 122 |
| `payload.issue.milestone.creator.login` | `str`×122 | 122 |
| `payload.issue.milestone.creator.node_id` | `str`×122 | 122 |
| `payload.issue.milestone.creator.organizations_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.received_events_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.repos_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.site_admin` | `bool`×122 | 122 |
| `payload.issue.milestone.creator.starred_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.subscriptions_url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.type` | `str`×122 | 122 |
| `payload.issue.milestone.creator.url` | `str`×122 | 122 |
| `payload.issue.milestone.creator.user_view_type` | `str`×122 | 122 |
| `payload.issue.milestone.description` | `str`×112, `null`×10 | 122 |
| `payload.issue.milestone.due_on` | `null`×115, `str`×7 | 122 |
| `payload.issue.milestone.html_url` | `str`×122 | 122 |
| `payload.issue.milestone.id` | `int`×122 | 122 |
| `payload.issue.milestone.labels_url` | `str`×122 | 122 |
| `payload.issue.milestone.node_id` | `str`×122 | 122 |
| `payload.issue.milestone.number` | `int`×122 | 122 |
| `payload.issue.milestone.open_issues` | `int`×122 | 122 |
| `payload.issue.milestone.state` | `str`×122 | 122 |
| `payload.issue.milestone.title` | `str`×122 | 122 |
| `payload.issue.milestone.updated_at` | `str`×122 | 122 |
| `payload.issue.milestone.url` | `str`×122 | 122 |
| `payload.issue.node_id` | `str`×461 | 461 |
| `payload.issue.number` | `int`×461 | 461 |
| `payload.issue.parent_issue_url` | `str`×68 | 68 |
| `payload.issue.performed_via_github_app` | `null`×445, `dict`×16 | 461 |
| `payload.issue.performed_via_github_app.client_id` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.created_at` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.description` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.events` | `list`×16 | 16 |
| `payload.issue.performed_via_github_app.events[]` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.external_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.html_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.id` | `int`×16 | 16 |
| `payload.issue.performed_via_github_app.name` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.node_id` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner` | `dict`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.avatar_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.events_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.followers_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.following_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.gists_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.gravatar_id` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.html_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.id` | `int`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.login` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.node_id` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.organizations_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.received_events_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.repos_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.site_admin` | `bool`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.starred_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.subscriptions_url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.type` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.url` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.owner.user_view_type` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions` | `dict`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.actions` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.administration` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.checks` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.contents` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.deployments` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.discussions` | `str`×5 | 5 |
| `payload.issue.performed_via_github_app.permissions.emails` | `str`×11 | 11 |
| `payload.issue.performed_via_github_app.permissions.issues` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.members` | `str`×6 | 6 |
| `payload.issue.performed_via_github_app.permissions.merge_queues` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.metadata` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.profile` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.pull_requests` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.repository_hooks` | `str`×4 | 4 |
| `payload.issue.performed_via_github_app.permissions.repository_projects` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.secret_scanning_alerts` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.security_events` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.statuses` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.permissions.vulnerability_alerts` | `str`×1 | 1 |
| `payload.issue.performed_via_github_app.permissions.workflows` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.slug` | `str`×16 | 16 |
| `payload.issue.performed_via_github_app.updated_at` | `str`×16 | 16 |
| `payload.issue.pinned_comment` | `null`×461 | 461 |
| `payload.issue.reactions` | `dict`×461 | 461 |
| `payload.issue.reactions.+1` | `int`×461 | 461 |
| `payload.issue.reactions.-1` | `int`×461 | 461 |
| `payload.issue.reactions.confused` | `int`×461 | 461 |
| `payload.issue.reactions.eyes` | `int`×461 | 461 |
| `payload.issue.reactions.heart` | `int`×461 | 461 |
| `payload.issue.reactions.hooray` | `int`×461 | 461 |
| `payload.issue.reactions.laugh` | `int`×461 | 461 |
| `payload.issue.reactions.rocket` | `int`×461 | 461 |
| `payload.issue.reactions.total_count` | `int`×461 | 461 |
| `payload.issue.reactions.url` | `str`×461 | 461 |
| `payload.issue.repository_url` | `str`×461 | 461 |
| `payload.issue.state` | `str`×461 | 461 |
| `payload.issue.state_reason` | `null`×363, `str`×98 | 461 |
| `payload.issue.sub_issues_summary` | `dict`×461 | 461 |
| `payload.issue.sub_issues_summary.completed` | `int`×461 | 461 |
| `payload.issue.sub_issues_summary.percent_completed` | `int`×461 | 461 |
| `payload.issue.sub_issues_summary.total` | `int`×461 | 461 |
| `payload.issue.timeline_url` | `str`×461 | 461 |
| `payload.issue.title` | `str`×461 | 461 |
| `payload.issue.type` | `null`×159, `dict`×25 | 184 |
| `payload.issue.type.color` | `str`×25 | 25 |
| `payload.issue.type.created_at` | `str`×25 | 25 |
| `payload.issue.type.description` | `str`×25 | 25 |
| `payload.issue.type.id` | `int`×25 | 25 |
| `payload.issue.type.is_enabled` | `bool`×25 | 25 |
| `payload.issue.type.name` | `str`×25 | 25 |
| `payload.issue.type.node_id` | `str`×25 | 25 |
| `payload.issue.type.updated_at` | `str`×25 | 25 |
| `payload.issue.updated_at` | `str`×461 | 461 |
| `payload.issue.url` | `str`×461 | 461 |
| `payload.issue.user` | `dict`×461 | 461 |
| `payload.issue.user.avatar_url` | `str`×461 | 461 |
| `payload.issue.user.events_url` | `str`×461 | 461 |
| `payload.issue.user.followers_url` | `str`×461 | 461 |
| `payload.issue.user.following_url` | `str`×461 | 461 |
| `payload.issue.user.gists_url` | `str`×461 | 461 |
| `payload.issue.user.gravatar_id` | `str`×461 | 461 |
| `payload.issue.user.html_url` | `str`×461 | 461 |
| `payload.issue.user.id` | `int`×461 | 461 |
| `payload.issue.user.login` | `str`×461 | 461 |
| `payload.issue.user.node_id` | `str`×461 | 461 |
| `payload.issue.user.organizations_url` | `str`×461 | 461 |
| `payload.issue.user.received_events_url` | `str`×461 | 461 |
| `payload.issue.user.repos_url` | `str`×461 | 461 |
| `payload.issue.user.site_admin` | `bool`×461 | 461 |
| `payload.issue.user.starred_url` | `str`×461 | 461 |
| `payload.issue.user.subscriptions_url` | `str`×461 | 461 |
| `payload.issue.user.type` | `str`×461 | 461 |
| `payload.issue.user.url` | `str`×461 | 461 |
| `payload.issue.user.user_view_type` | `str`×461 | 461 |
| `payload.label` | `dict`×245, `null`×1 | 246 |
| `payload.label.color` | `str`×245 | 245 |
| `payload.label.default` | `bool`×245 | 245 |
| `payload.label.description` | `str`×198, `null`×47 | 245 |
| `payload.label.id` | `int`×245 | 245 |
| `payload.label.name` | `str`×245 | 245 |
| `payload.label.node_id` | `str`×245 | 245 |
| `payload.label.url` | `str`×245 | 245 |
| `payload.labels` | `list`×246 | 246 |
| `payload.labels[]` | `dict`×245 | 245 |
| `payload.labels[].color` | `str`×245 | 245 |
| `payload.labels[].default` | `bool`×245 | 245 |
| `payload.labels[].description` | `str`×223, `null`×22 | 245 |
| `payload.labels[].id` | `int`×245 | 245 |
| `payload.labels[].name` | `str`×245 | 245 |
| `payload.labels[].node_id` | `str`×245 | 245 |
| `payload.labels[].url` | `str`×245 | 245 |

<details><summary>Ejemplo real de <code>IssuesEvent</code></summary>

```json
{
  "actor": {
    "avatar_url": "https://avatars.githubusercontent.com/u/155946767?",
    "display_login": "SUYOUNGKIM24",
    "gravatar_id": "",
    "id": 155946767,
    "login": "SUYOUNGKIM24",
    "url": "https://api.github.com/users/SUYOUNGKIM24"
  },
  "created_at": "2026-08-12T14:00:09Z",
  "id": "13170616788",
  "payload": {
    "action": "opened",
    "issue": {
      "active_lock_reason": null,
      "assignee": null,
      "assignees": [],
      "body": "Create a Dockerfile and docker-compose.yml for local development environment.",
      "closed_at": null,
      "comments": 0,
      "comments_url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6/comments",
      "created_at": "2026-08-12T14:00:08Z",
      "events_url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6/events",
      "html_url": "https://github.com/SUYOUNGKIM24/project-yljevhfq/issues/6",
      "id": 5131709881,
      "issue_dependencies_summary": {
        "blocked_by": 0,
        "blocking": 0,
        "total_blocked_by": 0,
        "total_blocking": 0
      },
      "labels": [],
      "labels_url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6/labels{/name}",
      "locked": false,
      "milestone": null,
      "node_id": "I_kwDOT2YY_88AAAABMd-tuQ",
      "number": 6,
      "performed_via_github_app": null,
      "pinned_comment": null,
      "reactions": {
        "+1": 0,
        "-1": 0,
        "confused": 0,
        "eyes": 0,
        "heart": 0,
        "hooray": 0,
        "laugh": 0,
        "rocket": 0,
        "total_count": 0,
        "url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6/reactions"
      },
      "repository_url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq",
      "state": "open",
      "state_reason": null,
      "sub_issues_summary": {
        "completed": 0,
        "percent_completed": 0,
        "total": 0
      },
      "timeline_url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6/timeline",
      "title": "Add Docker support",
      "updated_at": "2026-08-12T14:00:08Z",
      "url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq/issues/6",
      "user": {
        "avatar_url": "https://avatars.githubusercontent.com/u/155946767?v=4",
        "events_url": "https://api.github.com/users/SUYOUNGKIM24/events{/privacy}",
        "followers_url": "https://api.github.com/users/SUYOUNGKIM24/followers",
        "following_url": "https://api.github.com/users/SUYOUNGKIM24/following{/other_user}",
        "gists_url": "https://api.github.com/users/SUYOUNGKIM24/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/SUYOUNGKIM24",
        "id": 155946767,
        "login": "SUYOUNGKIM24",
        "node_id": "U_kgDOCUuPDw",
        "organizations_url": "https://api.github.com/users/SUYOUNGKIM24/orgs",
        "received_events_url": "https://api.github.com/users/SUYOUNGKIM24/received_events",
        "repos_url": "https://api.github.com/users/SUYOUNGKIM24/repos",
        "site_admin": false,
        "starred_url": "https://api.github.com/users/SUYOUNGKIM24/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/SUYOUNGKIM24/subscriptions",
        "type": "User",
        "url": "https://api.github.com/users/SUYOUNGKIM24",
        "user_view_type": "public"
      }
    }
  },
  "public": true,
  "repo": {
    "id": 1332091135,
    "name": "SUYOUNGKIM24/project-yljevhfq",
    "url": "https://api.github.com/repos/SUYOUNGKIM24/project-yljevhfq"
  },
  "type": "IssuesEvent"
}
```

</details>


### `PushEvent`  (148,551 eventos)

| Ruta | Tipos observados | Ocurrencias |
|---|---|---:|
| `payload.before` | `str`×148,551 | 148,551 |
| `payload.head` | `str`×148,551 | 148,551 |
| `payload.push_id` | `int`×148,551 | 148,551 |
| `payload.ref` | `str`×148,551 | 148,551 |
| `payload.repository_id` | `int`×148,551 | 148,551 |

<details><summary>Ejemplo real de <code>PushEvent</code></summary>

```json
{
  "actor": {
    "avatar_url": "https://avatars.githubusercontent.com/u/302074889?",
    "display_login": "gardnerrandall510",
    "gravatar_id": "",
    "id": 302074889,
    "login": "gardnerrandall510",
    "url": "https://api.github.com/users/gardnerrandall510"
  },
  "created_at": "2026-08-12T14:00:03Z",
  "id": "17486924228",
  "payload": {
    "before": "eb2119bcd8df5f4da9d1b70cfb9c69b83c775bc0",
    "head": "15c0e70e4432cc04e549e90e9f9326d03708bb4c",
    "push_id": 39806989356,
    "ref": "refs/heads/main",
    "repository_id": 1330736154
  },
  "public": true,
  "repo": {
    "id": 1330736154,
    "name": "gardnerrandall510/ruu",
    "url": "https://api.github.com/repos/gardnerrandall510/ruu"
  },
  "type": "PushEvent"
}
```

</details>
