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
