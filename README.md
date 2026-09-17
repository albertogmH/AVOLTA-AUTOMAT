# AVOLTA AUTOMAT

## Espanol

Coleccion de scripts de automatizacion y una aplicacion web para consultar y gestionar tiendas.

### Requisitos

- Python 3.10 o superior
- `pip`

### Instalacion

Desde la raiz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

`playwright install` descarga los navegadores necesarios para los scripts que usan Playwright.

### Configuracion local

Copie `.env.example` como `.env` y complete las cuatro credenciales locales antes de ejecutar los scripts que requieren autenticacion:

```bash
cp .env.example .env
```

El archivo `.env` esta excluido de Git y no debe subirse al repositorio.

### Ejecutar scripts

Con el entorno virtual activado, ejecuta cualquier script con este formato:

```bash
python3 [carpetaDelScript]/main.py
```

Por ejemplo:

```bash
python3 getStoreIDByURL/main.py
```

Algunos scripts requieren archivos de entrada en `utils/` o solicitan datos por consola.

### Base de datos de tiendas

La base de datos `storesDB/stores.db` no se incluye en el repositorio. Para crearla, asegurese de tener `utils/stores.xlsx` y `utils/websites.xlsx`, y ejecute:

```bash
python3 storesDB/build_db.py
```

Para iniciar la aplicacion web de tiendas:

```bash
python3 storesDB/app.py
```

Abra la URL mostrada en la terminal, normalmente `http://127.0.0.1:5000`.

### Seguridad

No publique credenciales, tokens ni datos confidenciales. Configure los valores locales necesarios antes de ejecutar los scripts y mantengalos fuera del repositorio.

## English

Collection of automation scripts and a web application to browse and manage stores.

### Requirements

- Python 3.10 or later
- `pip`

### Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

`playwright install` downloads the browsers required by scripts that use Playwright.

### Local configuration

Copy `.env.example` to `.env` and complete the four local credentials before running scripts that require authentication:

```bash
cp .env.example .env
```

The `.env` file is excluded from Git and must not be committed to the repository.

### Running scripts

With the virtual environment activated, run any script using this format:

```bash
python3 [scriptFolder]/main.py
```

For example:

```bash
python3 getStoreIDByURL/main.py
```

Some scripts require input files in `utils/` or prompt for values in the terminal.

### Stores database

The `storesDB/stores.db` database is not included in the repository. To build it, ensure `utils/stores.xlsx` and `utils/websites.xlsx` are available, then run:

```bash
python3 storesDB/build_db.py
```

To start the stores web application:

```bash
python3 storesDB/app.py
```

Open the URL printed in the terminal, normally `http://127.0.0.1:5000`.

### Security

Do not publish credentials, tokens, or confidential data. Configure required local values before running the scripts and keep them out of the repository.