"""Clasificacion de actores automaticos.

La pregunta de negocio 1 no distingue solo bot de humano: separa la
automatizacion clasica de los agentes de IA, que es la parte interesante. Aqui
vive esa clasificacion, en un solo sitio y como listas explicitas, para que se
pueda discutir y ampliar sin tocar el job.

Las listas se contrastan contra el login SIN el sufijo "[bot]".

Criterio: un login solo entra aqui si se ha visto en los datos o si es un
servicio conocido y verificable. No se inventan patrones.
"""

# Agentes que escriben o revisan codigo por su cuenta. Es la categoria que da
# sentido a la pregunta 1: no es CI, es trabajo que antes hacia una persona.
AGENTES_IA = {
    "cursor",
    "devin-ai-integration",
    "chatgpt-codex-connector",
    "claude",
    "coderabbitai",
    "arena-ai-coding-agent",
    "copilot",
    "copilot-swe-agent",
    "sweep-ai",
    "codium-ai",
    "ellipsis-dev",
    "graphite-app",
    # Anadidos tras ver los datos: estaban cayendo en bot_otro con volumen
    # alto, y son asistentes de codigo, no CI.
    "gemini-code-assist",
    "amazon-q-developer",
    "lovable-dev",
    "qodo-merge-pro",
    "cubic-dev-ai",
}

# Actualizadores de dependencias. Volumen alto y comportamiento muy regular.
BOTS_DEPENDENCIAS = {
    "dependabot",
    "dependabot-preview",
    "renovate",
    "renovate-bot",
    "pyup-bot",
    "greenkeeper",
    "snyk-bot",
}

# Integracion continua, despliegue y automatizacion de repositorio.
BOTS_CI = {
    "github-actions",
    "github-merge-queue",
    "vercel",
    "netlify",
    "circleci",
    "travis-ci",
    "codecov",
    "sonarcloud",
    "trunk-io",
    "copybara-service",
    "codelinaro-mirror-sync",
    "pull",
    "imgbot",
    "allcontributors",
    # Anadidos tras ver los datos, por volumen en bot_otro.
    "swa-runner-app",
    "swa-synthetics",
    "sonarqubecloud",
    "mergify",
    "kodiakhq",
    "openshift-ci",
    "amazon-codecatalyst",
    "codecatalyst-integ",
    "aws-connector-for-github",
    "cloudflare-workers-and-pages",
    "trunk-staging-io",
    "netlify",
    "azure-pipelines",
}

CLASE_HUMANO = "humano"
CLASE_AGENTE_IA = "agente_ia"
CLASE_BOT_DEPENDENCIAS = "bot_dependencias"
CLASE_BOT_CI = "bot_ci"
CLASE_BOT_OTRO = "bot_otro"


def mapa_clases() -> dict:
    """Devuelve {login_sin_sufijo: clase} para construir el mapeo en Spark."""
    mapa = {}
    for login in AGENTES_IA:
        mapa[login] = CLASE_AGENTE_IA
    for login in BOTS_DEPENDENCIAS:
        mapa[login] = CLASE_BOT_DEPENDENCIAS
    for login in BOTS_CI:
        mapa[login] = CLASE_BOT_CI
    return mapa
