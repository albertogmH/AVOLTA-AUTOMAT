# Contexto Del Proyecto: AVOLTA AUTOMAT

Contexto especifico registrado en esta ubicacion por peticion expresa del usuario.
Describe el estado inspeccionado; no sustituye las instrucciones compartidas ni
establece nuevas politicas, permisos o gates de validacion.

## Objetivo Y Alcance

- Producto/dominio: automatizar trabajo operativo de Avolta, principalmente con
	scripts Python, Playwright y consola; incluye una aplicacion de tiendas con API
	reutilizable para consulta y mantenimiento de datos.
- Comportamiento: scripts por tarea con entradas CSV/Excel o preguntas por consola;
	interfaz web y operaciones CRUD sobre una base SQLite de tiendas.
- Usuarios: mantenedor del repositorio y operadores de estas tareas; perfiles,
	volumen de uso y requisitos de disponibilidad no confirmados.
- Alcance historico de DOC-CONTEXT: completar solo este documento con hechos verificables y
	desconocidos explicitos. Fuera de alcance: aplicacion, instrucciones compartidas,
	enrutamiento de agentes, dependencias, politica de seguridad y gates existentes.
- CAT-STRUCT: reorganizar magentoCategoryActions, mantener la compatibilidad de
	checkCategoryEnabled y las salvaguardas de escritura, comprobar offline y despues
	registrar aqui la estructura preferida. No introduce arquitectura ni dependencias.

## Arquitectura

- Stack: Python >=3.10 segun README. requirements.txt declara deep-translator,
	Flask, openpyxl, playwright y python-dotenv sin versiones fijadas; versiones
	instaladas no verificadas.
- Entradas: python3 <carpeta>/main.py desde la raiz. Ejemplo inspeccionado:
	checkBrandCategories/main.py usa Playwright sincrono, Chromium visible y preguntas
	de consola para elegir divisiones y marca; consulta marcas, categorias y colecciones.
- Reutilizacion: utils/config.py carga configuracion con python-dotenv y centraliza
	divisiones, rutas y credenciales; utils/functions.py contiene login_magento_admin.
	Los scripts importan estos componentes; no se ha confirmado una capa comun de API
	que conecte todas las automatizaciones con storesDB.
- Integraciones: administracion Magento por division y configuracion de la app en
	STAGING y PROD (APP_STAGING_URL, APP_PROD_URL). magentoCategoryActions cuenta con
	mocks, SQLite temporal y HTML inerte servido en loopback para pruebas aisladas;
	no son sustitutos verificados de una instancia real de Magento.
- Datos: storesDB/build_db.py genera storesDB/stores.db desde utils/stores.xlsx y
	utils/websites.xlsx. Enriquece tiendas por prefijo de URL, priorizando el mas largo.
	El constructor elimina la base previa: no es una migracion incremental.
- Aplicacion: storesDB/app.py usa Flask y sqlite3; storesDB/templates y storesDB/static
	contienen la interfaz. La base generada no se incluye en Git segun README;
	la disponibilidad local de la base y los Excel de entrada no se ha comprobado.
- API JSON: GET / muestra la interfaz; GET /api/filters devuelve opciones;
	GET /api/stores admite search, division, region, country, has_active_store, active
	y language. Los filtros de lista admiten parametros repetidos o separados por comas;
	active=1 selecciona Active y active=0 incluye inactivos y valores vacios.
- Escrituras: POST /api/stores devuelve {"id": ...} con estado 201;
	PUT /api/stores/<int:store_pk> y DELETE /api/stores/<int:store_pk> usan el id interno
	de SQLite, no store_id. PUT reemplaza TODOS los campos editables; los omitidos
	quedan NULL. language se deriva del primer segmento de store_url, no se almacena.
- Compatibilidad: se trabaja en macOS; README usa activacion de entorno tipo Unix.
	Compatibilidad completa con otros sistemas no verificada; el arranque de Flask
	intenta utilizar pgrep y lsof.

## Estructura Preferida De Scripts

- Una carpeta por tarea y preferentemente un solo main.py de produccion. Mantener
	imports estandar, Playwright y utilidades compartidas al principio, despues de
	resolver la raiz cuando se ejecuta directamente desde una subcarpeta.
- Reutilizar utils.config para divisiones, credenciales y URLs, y
	utils.functions.login_magento_admin para login; no duplicar estos componentes.
	Funciones pequenas y explicitas para cada accion y sus validaciones necesarias;
	evitar capas genericas, clases nuevas y orquestadores anidados sin necesidad.
- Mantener main() protegido por if __name__ == "__main__": importar no debe pedir
	entradas, abrir navegador, autenticar ni ejecutar acciones. La carga compartida
	de configuracion local sigue el comportamiento existente de utils.config.
- Flujo legible: preguntas -> preparacion -> variables de resultados, errores y
	tiempo -> with sync_playwright -> Chromium headless=False -> bucle de divisiones
	-> credenciales/login compartido -> accion -> cierre en finally -> RESULTS y
	tiempo transcurrido. En categorias se aisla cada division con su propio contexto,
	se bloquean service workers y el login usa timeout=60000.
- Consola de categorias: menu vertical, divisiones 5, 5,6, div5 o all validadas y
	canonicas, categoria positiva. Un titulo por division/idioma con prompt
	EN Category name (leave it blank to skip): ; vacio omite el grupo. Conservar
	Unicode y espacios exactos hasta 255 caracteres. Resumen EN -> "titulo", cabecera
	de division si hay varias; solo y/n, y confirma y n recoge todos los nombres otra
	vez. EXCLUDED avisa sin ACK; un plan vacio termina antes de navegador/login.
- Consultar storesDB/stores.db existente en modo SQLite read-only sin Flask ni
	reconstruccion. Usar store_id de Magento, nunca la PK SQLite; rechazar duplicados
	contradictorios y no inferir idiomas de datos ambiguos. div7 sigue sin mapeo
	autoritativo de idioma; div10 no tiene grupos fiables segun el estado conocido,
	no actualizado con datos reales durante CAT-STRUCT.
- Conservar validacion estricta de categoria, tienda y origen antes de escribir,
	ausencia de reintentos y verificacion tras recarga.
	Hay dos validadores: el estricto previo a escribir (orden id/<id>/store/<store>/,
	key opcional) y uno tolerante tras guardar (id y store en cualquier orden, key
	opcional, sin query) que reporta como error distinto la redireccion a
	catalog/category/index/. Ambos admiten /key/.../ opcional sin aceptar otro
	ambito, origen, userinfo, query o fragmento.
	Distinguir guardados verificados, envio incierto y ningun guardado transmitido.
- Guardado (CAT-CLICKSAVE, por peticion del usuario): se hace pulsando el boton Save
	de la propia pagina (#save[data-form-role=save]) y esperando la recarga de
	navegacion; despues se verifica el ambito y que el nombre persistido sea el titulo
	con use_default[name] desmarcado. Las comprobaciones previas a escribir se
	mantienen (id de categoria en titulo/h1, store_id oculto igual al pedido). No hay
	interceptor de rutas ni analisis de payload: el guard anterior se elimino a peticion
	del usuario. Contrato medido antes (CAT-SAVE, div6 categoria 2780): Save envia un
	POST AJAX validate/ y luego un POST de formulario a save/ con 302 a la pagina de
	edicion; el clic real y la recarga no se han ejecutado en vivo tras este cambio.
	Los IDs de categoria y tienda son por division.
- Carga de pagina de categoria (como getCLPBlock y checkBrandCategories): goto ->
	wait_for_load_state('networkidle') acotado y tolerante -> loader del formulario
	oculto -> div.fieldset-wrapper[data-index=general] (un div, no un fieldset) y Nombre
	visibles -> (al escribir) checkbox use_default[name] y store_id presentes, todo con
	locator.wait_for (60000 ms), sin wait_for_function ni sleeps fijos; si ya esta
	cargado, continuar al instante. Leer datos solo despues de esperar. El error nombra
	el componente ausente y una pagina de login falla de inmediato. Un fallo por tienda o login de division no detiene la ejecucion:
	se registra (division, store_id, motivo, estado), se sigue con la siguiente tienda
	en pagina nueva sin reintentos y RESULTS lista cada fallo; salida 1 si hubo alguno.
- Mantener pruebas offline cerca de la tarea, reutilizando fixtures existentes;
	no abrir test.html, que referencia assets de produccion. Esta estructura registra
	la preferencia solicitada, no cambia permisos ni gates de las instrucciones.

## Validacion

Preparacion documentada, desde la raiz del repositorio (no ejecutada en DOC-CONTEXT):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
cp .env.example .env
```

- Completar .env localmente antes de tareas autenticadas; no publicar sus valores.
- Comandos operativos, no pruebas: python3 getStoreIDByURL/main.py,
	python3 storesDB/build_db.py y python3 storesDB/app.py. Los dos ultimos requieren
	los datos locales indicados; construir la base reemplaza su contenido existente.
- Prueba enfocada de documentacion: contrastar rutas Flask mediante AST sin importar
	la aplicacion, dependencias, referencias a archivos versionados y secciones completas;
	comprobar ASCII y git diff --check. No demuestra el funcionamiento de la aplicacion.
- Pruebas de categorias ejecutadas con dependencias y Chromium ya instalados:

```bash
.venv/bin/python -B -m unittest discover -s magentoCategoryActions -p 'test_*.py' -v
```

- Resultado observado CAT-STRUCT, 2026-10-29: 59 pruebas OK en 113.933 segundos.
	Cobertura: prompts y no-op, mappings SQLite de solo lectura, ambitos y payloads,
	aislamiento/cierre, avisos de guardado y Chromium con guardado/recarga incluyendo
	redirects keyed 302/303 y rechazo de otro store. El helper compartido real se
	prueba con formulario y shell retardados, rechazo, sesion existente, formulario
	de otro origen loopback sin credenciales y timeouts con un solo submit como maximo.
- No se probo autenticacion real de div8 ni compatibilidad live del proveedor o
	serializacion Magento. No hubo login externo, solicitudes a produccion ni
	escrituras en la base real. La suite no demuestra autorizacion del servidor real.
- Lint, chequeo de tipos, build y CI: comandos/resultados globales no confirmados.
- Gates: siguen vigentes AGENTS.md y agent-system/workflows/feature-delivery.md,
	incluidos los requisitos de usuario/proyecto y especialistas segun la ruta.
	La tarea historica DOC-CONTEXT tuvo ruta Minimal por ser documentacion factual sin cambios de
	comportamiento: requeria comprobacion enfocada e inspeccion final del coordinador.
	En aquella tarea no se requerian especialistas independientes por defecto; no exime
	cambios de comportamiento futuros de QA ni de revisiones obligatorias.
- Seguridad: no se ha confirmado un comando de auditoria aprobado. En DOC-CONTEXT
	no se ejecutaron servidores, navegadores, automatizaciones externas ni pruebas contra
	produccion; no eran necesarios para contrastar documentacion ni se contaron como pases.
	CAT-STRUCT si ejecuto servidores loopback y Chromium con fixtures inertes; las
	pruebas locales no equivalen a un dictamen de auditoria independiente.

## Seguridad Y Autoridad

- Datos sensibles: credenciales Magento/app, archivos de entrada y datos de tiendas.
	Limites de confianza: consola/CSV/Excel, administraciones externas y JSON de la API
	que escribe SQLite. No se han verificado clasificacion ni retencion de esos datos.
- Variables de credenciales observadas (solo nombres): MAGENTO_USERNAME,
	MAGENTO_PASSWORD_DIV1 a MAGENTO_PASSWORD_DIV10, APP_USERNAME y APP_PASSWORD.
	README indica mantener .env fuera de Git y no publicar credenciales ni datos confidenciales.
- Estado actual: la API Flask inspeccionada no implementa autenticacion/autorizacion.
	El arranque local usa normalmente http://127.0.0.1:5000, admite PORT y activa
	debug=True. No se han confirmado requisitos de acceso o un despliegue de produccion;
	la existencia de configuracion PROD no constituye autorizacion para utilizarla.
- Cautela operativa: kill_previous_instances y free_port pueden enviar SIGKILL a
	otras instancias o a procesos que ocupen el puerto preferido al arrancar app.py.
- Autoridad: siguen vigentes las aprobaciones humanas de las instrucciones compartidas
	para commit, push, merge, despliegue, produccion y Git destructivo. No hay permisos
	adicionales confirmados para operar sistemas externos. El alcance historico DOC-CONTEXT solo autorizaba
	esta edicion documental y comprobaciones locales de lectura, sin cambiar .env ni datos.

## Entrega

- Aceptacion historica DOC-CONTEXT: contexto en espanol ASCII, secciones utiles conservadas,
	hechos trazables a README e implementaciones y desconocidos explicitos; unico
	archivo modificado: agent-system/templates/project-context.md.
- Finalizacion historica DOC-CONTEXT: evidencia real de las comprobaciones enfocadas e inspeccion del
	coordinador segun la ruta Minimal, sin autoaprobacion del desarrollador. Gates de
	CI adicionales y criterios funcionales globales no confirmados; no se inventan ni
	se dispensan los gates compartidos existentes.
- Integracion historica DOC-CONTEXT: arbol Git limpio comunicado al asignar la tarea; un solo escritor,
	sin delegacion, copias del contexto, commits ni cambios ajenos al archivo asignado.
- CAT-STRUCT partio de un arbol sucio conocido y archivos de categorias sin tracking;
	conservo el baseline en /tmp/CAT-STRUCT.9ubeRy para comparar el delta sin tocar el
	indice Git. Cambios del desarrollador: main.py y pruebas de magentoCategoryActions,
	README y este contexto. Wrapper y helper compartido sin cambios en esta asignacion.
	Las pruebas del desarrollador no son aprobacion: quedan pendientes QA, Security,
	Reviewer independientes e inspeccion del coordinador para la entrega Sensitive.
- Responsable del contexto: mantenedor del repositorio; identidad no confirmada.
	Ultima actualizacion: 2026-10-29; CAT-STRUCT incluye la ejecucion offline indicada,
	no validacion funcional contra sistemas externos.