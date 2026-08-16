# Decisiones

Cada entrada en cinco líneas: qué decidí, qué alternativas había, por qué esa,
qué me cuesta.

---

## D1 — Entorno de ejecución: Windows nativo con JDK 17 x64

- **Qué**: el backfill de PySpark corre en Windows nativo, no en WSL2.
- **Alternativas**: WSL2 (Ubuntu), que se parece más al runner de Actions.
- **Por qué**: la máquina ya está montada ahí y el lago cabe en `D:` sin la
  penalización de acceso que WSL sufre sobre `/mnt/d`.
- **Coste**: hay que instalar `winutils.exe` y `hadoop.dll`, y la capa Hadoop
  en Windows produce errores opacos. Se valida con la prueba de humo −1.5.
- **Reversible**: sí. Si −1.5 falla, se migra a WSL2 antes de invertir más.

## D2 — Repositorio público en GitHub desde el inicio

- **Qué**: repo público creado con `gh` bajo `marcosguerrerodeveloper`.
- **Alternativas**: git solo local hasta tener algo que enseñar.
- **Por qué**: el criterio de éxito nº 1 es una URL permanente, y GitHub Pages
  y los minutos ilimitados de Actions solo aplican en repos públicos.
- **Coste**: todo el historial es visible desde el primer commit, incluidos los
  tanteos. Obliga a no commitear nunca datos crudos ni secretos.

## D3 — Fase 0 sobre un único fichero horario

- **Qué**: la exploración inicial se hace sobre una sola hora.
- **Alternativas**: una hora de tres momentos separados en el tiempo, para
  detectar cambios de esquema a lo largo del histórico.
- **Por qué**: es lo que pide `CLAUDE.md` y mantiene el checkpoint corto.
- **Coste**: un cambio de esquema en el histórico no se detecta ahora; puede
  aparecer a mitad del backfill. Se mitiga en la Fase 2 haciendo que la lectura
  de bronze falle ruidosamente ante un campo inesperado, en vez de silenciarlo.

## D4 — Lago de datos en `D:/gharchive-data`

- **Qué**: `raw/`, `bronze/` y `silver/` viven en `D:`, fuera del repo.
- **Alternativas**: `C:`, o un subdirectorio del propio proyecto.
- **Por qué**: `C:` tiene 90 GB libres y `D:` 1.378 GB. Fuera del repo, además,
  hace imposible commitear datos crudos por accidente.
- **Coste**: la ruta no es portable. Se absorbe leyéndola de `GHA_DATA_DIR`,
  con `D:/gharchive-data` solo como valor por defecto.

## D5 — winutils de terceros para desbloquear Spark en Windows

- **Qué**: `winutils.exe` y `hadoop.dll` de `cdarlint/winutils` (rama
  hadoop-3.3.6) en `C:\hadoop\bin`, con `HADOOP_HOME` fijado.
- **Alternativas**: migrar a WSL2 (plan B de D1), o compilar winutils desde las
  fuentes de Hadoop con Visual Studio.
- **Por qué**: la prueba de humo −1.5 confirmó que sin ellos Spark no escribe
  Parquet en Windows. Es el atajo estándar y mantiene D1 en pie; compilar son
  horas para un proyecto de portfolio.
- **Coste**: son binarios mantenidos por un particular, no por Apache, y la
  versión 3.3.6 no coincide exactamente con el Hadoop 3.3.4 que empaqueta
  PySpark 3.5.3. Verificado en la práctica: escribe y relee Parquet
  particionado sin error. Reversible borrando `C:\hadoop`.

## D6 — `PYSPARK_PYTHON` se fija en código, no en el entorno

- **Qué**: cada job hace `os.environ.setdefault("PYSPARK_PYTHON", sys.executable)`.
- **Alternativas**: exportar la variable en el perfil de PowerShell o en un
  script de arranque.
- **Por qué**: en Windows los workers de Python no heredan el venv y Spark
  muere con "Python worker failed to connect back". Fijarlo en código hace que
  el job funcione con solo invocar el intérprete correcto, sin ritual previo.
- **Coste**: dos líneas repetidas en cada entrypoint. Se centralizarán en un
  único helper de sesión de Spark en la Fase 2.

## D7 — El lenguaje del repo no está en los datos: la pregunta 1 se reformula

- **Qué**: la pregunta de negocio 1 pierde el corte por lenguaje del repo.
- **Alternativas**: enriquecer con la API de GitHub (5.000 req/h autenticado),
  o derivar un proxy desde las extensiones de fichero de los commits.
- **Por qué**: se comprobaron cuatro rutas candidatas en 770 `PullRequestEvent`
  y **ninguna existe**; el objeto `repo` solo trae `id`, `name` y `url`. La
  segunda opción mete una dependencia de red y de token que choca con "todo
  corre en Actions gratis"; la tercera es imposible, porque tampoco hay array
  de commits.
- **Coste**: el dashboard no podrá segmentar la actividad de bots por lenguaje.
  Se dice como limitación explícita en el README en lugar de disimularlo.

## D8 — La latencia de PR se deriva de los eventos, no de campos del payload

- **Qué**: los tiempos hasta primer review y hasta merge se calculan restando
  el `created_at` de eventos unidos por `payload.pull_request.id`.
- **Alternativas**: leer `created_at` / `merged_at` del propio PR, que es como
  estaba planteada la pregunta 2.
- **Por qué**: esos campos no existen en el payload recortado. El `id` del PR
  sí está al 100 % en los tres tipos de evento relevantes, y `payload.action`
  trae `merged` como valor propio, sin tener que inferirlo de `closed` + flag.
- **Coste**: amplifica la censura por los bordes de la ventana. Obliga a
  cohortar por fecha de apertura y a descartar explícitamente las cohortes sin
  madurar y los merges huérfanos, en vez de promediarlo todo.

## D9 — El entregable de la Fase 0 se separa en dos ficheros

- **Qué**: `analizar_hora.py` genera `docs/exploracion_datos.md` (tablas y
  ejemplos crudos); `docs/exploracion.md` lo escribo a mano con conclusiones.
- **Alternativas**: un único fichero generado, o uno único escrito a mano.
- **Por qué**: el anexo se regenera al analizar otra hora y machacaría
  cualquier análisis escrito encima; y las implicaciones sobre las preguntas de
  negocio no las puede redactar un script.
- **Coste**: hay que releer el anexo y actualizar las conclusiones a mano si se
  analiza otra hora. Es trabajo consciente, que es justo lo que se quiere aquí.

## D10 — La descarga se ejecuta en GitHub Actions, no en local

- **Qué**: la Fase 0 descarga y analiza en un runner de Actions, que publica el
  informe y el `.gz` como artefactos temporales.
- **Alternativas**: usar una VPN tipo Cloudflare WARP en local, o esperar a que
  el bloqueo remita.
- **Por qué**: `data.gharchive.org` resuelve a `188.114.96.5` / `.97.5`, y la
  conexión TCP al 443 no se establece desde esta red mientras que otros
  destinos sí. Verificado fuera de Claude Code, sin proxy ni VPN configurados,
  así que el bloqueo es aguas arriba del router. El runner tiene salida limpia
  y el coste sigue siendo 0 € en un repo público.
- **Coste**: **no resuelve el backfill grande**, que debe correr en local por
  diseño. Si el bloqueo persiste, la Fase 1 se queda sin máquina donde correr y
  habrá que decidir entre VPN o replantear dónde vive el backfill.

---

## Revisión de D7 y D8 (2026-08-16)

Ambas se tomaron mirando **solo** una hora de 2026, y la comparación entre años
las deja obsoletas en parte. Se conservan porque el registro de decisiones es
un histórico, no un documento de estado.

- **D7 queda revocada.** El lenguaje del repo **sí existe** en
  `payload.pull_request.base.repo.language`, con ~90 % de cobertura estable
  entre 2016 y 2025-10-08. La pregunta 1 conserva el corte por lenguaje si la
  ventana se sitúa en el histórico rico. Lo que era cierto —y sigue siéndolo—
  es que en el formato posterior a 2025-10-09 no está.
- **D8 se mantiene, pero por otro motivo.** Los campos temporales sí existen en
  el histórico rico, así que la latencia se puede leer. Derivarla igualmente de
  los eventos deja de ser una necesidad y pasa a ser una elección: es la única
  vía que funciona en los dos formatos, y sirve de contraste contra los campos.

## D11 — Ventana histórica: 2024-10-09 → 2025-10-08

- **Qué**: un año de backfill que termina justo antes del cambio de formato.
- **Alternativas**: histórico más largo (varios años), o ventana reciente que
  incluya el formato nuevo.
- **Por qué**: es el tramo más largo con esquema homogéneo y payload completo
  que cabe en un año natural. Da cohortes de doce meses para la pregunta 3,
  lenguaje para la 1 y campos temporales para la 2, y esquiva tanto el tramo
  degradado como la frontera de formato.
- **Coste**: los datos terminan en octubre de 2025, así que el dashboard no
  será "actual" en su serie rica. El incremental diario aportará datos nuevos,
  pero con métricas limitadas y visualmente separados.

## D12 — El pipeline soporta los dos esquemas, detectados por campos

- **Qué**: bronze y silver aceptan el formato completo y el reducido, decidiendo
  por presencia de campos y no por fecha.
- **Alternativas**: soportar solo el formato rico y congelar el proyecto en
  octubre de 2025, o soportar solo el nuevo y renunciar al histórico.
- **Por qué**: la Fase 5 exige un cron diario, que necesariamente corre sobre
  el formato nuevo. Discriminar por fecha codificaría el 2025-10-09 en el
  código, y si la fuente vuelve a cambiar habría que tocarlo otra vez.
- **Coste**: el esquema de silver tendrá columnas nulas en el tramo reciente
  (lenguaje, latencias, conteo de commits), y los tests de calidad deben
  tolerarlo por tramo en vez de exigir cobertura uniforme.

## D13 — El tramo 2025-10-09 → 2025-10-14 se excluye como hueco conocido

- **Qué**: seis días marcados como no utilizables, no como días flojos.
- **Alternativas**: ingerirlos y dejar que el análisis los absorba.
- **Por qué**: traen entre 588 y 1.346 eventos por hora frente a los ~150.000
  esperados, un 0,4 %. No son datos escasos, son datos ausentes, y una serie
  temporal que los incluya muestra un desplome que no ocurrió en GitHub.
- **Coste**: hay que arrastrar una lista de huecos conocidos desde la ingesta
  hasta el dashboard. Queda fuera de la ventana de D11 de todos modos, pero el
  mecanismo hace falta igual para el incremental.

## D14 — La bisección del cambio de formato se hace en Actions

- **Qué**: `comparar_horas.py` más un workflow parametrizado por lista de
  fechas; cinco tandas para acotar el cambio de un rango de diez años a un día.
- **Alternativas**: descargar el histórico en local y comparar allí.
- **Por qué**: la red local no llega a GH Archive (D10), y el runner además
  paraleliza la descarga de varias fechas sin tocar la máquina del autor.
- **Coste**: cada iteración cuesta un ciclo de commit, push y espera. A cambio,
  el procedimiento queda registrado y es reproducible por cualquiera.

## D15 — D11 se confirma: un año de histórico rico cabe en disco

- **Qué**: se mantiene la ventana `2024-10-09 → 2025-10-08` del D11.
- **Alternativas**: acortarla a seis meses, o filtrar tipos de evento en bronze,
  que eran las dos salidas previstas si no cabía.
- **Por qué**: medido un día completo real (2025-08-13) son 2,012 GiB, que
  proyectan **~734 GiB al año** contra los 1.283 GiB libres de `D:`. Ocupa el
  57 % del disco, y el `.gz` se borra en cuanto la hora entra en bronze, así que
  el pico real es bastante menor que esa suma.
- **Coste**: el margen es cómodo pero no infinito, y obliga a que el borrado
  del crudo vaya al día en vez de acumularse hasta el final del backfill.
