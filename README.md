# ¡Hola! 👋 Bienvenidos al Proyecto AgroExtensión Digital 🌱🚜

Este es el repositorio principal de nuestro proyecto `agro_extension_digital_project`.
Nuestra misión es revolucionar la extensión agrícola digital, conectando a agricultores y técnicos con información y herramientas de vanguardia. ¡Vamos a sembrar el futuro juntos! 🚀

## ¿Qué encontrarás aquí dentro? 📂

Este monorepo está organizado en varias carpetas clave. ¡Echa un vistazo!

*   **`agents/`** 🤖
    *   Aquí viven nuestros agentes inteligentes. Son los cerebritos 🧠 que procesan información, interactúan con los usuarios y ayudan a tomar mejores decisiones en el campo.

*   **`cicd/`** ⚙️
    *   ¡La magia de la Integración y Entrega Continua (CI/CD)! Contiene todos los scripts y configuraciones para automatizar las pruebas, despliegues y que todo funcione como un reloj suizo 🇨🇭.

*   **`notebooks/`** 🔬
    *   ¡El laboratorio de los científicos de datos! Cuadernos de Jupyter listos para explorar, analizar, visualizar datos y prototipar nuevas ideas. ¡Pura experimentación!

*   **`webhook-application/`** 📲
    *   El corazón de nuestras comunicaciones, especialmente con WhatsApp. Esta aplicación maneja los webhooks para recibir y enviar mensajes, conectando a los usuarios con nuestros servicios al instante.

## Entorno de Desarrollo con Dev Containers 🐳💻

¡Para facilitarte la vida y asegurar que todos tengamos un ambiente de desarrollo consistente, este proyecto está configurado para usar **Dev Containers** (Contenedores de Desarrollo) en VS Code!

**¿Qué es un Dev Container?** 🤔

Es básicamente un entorno de desarrollo Docker completamente configurado. Cuando abres este proyecto en VS Code y tienes la extensión de "Dev Containers" instalada, VS Code puede construir y conectarse a un contenedor Docker que tiene todas las herramientas y dependencias que necesitas ya preinstaladas y listas para usar. ¡Así te olvidas de los problemas de "en mi máquina sí funciona"! 😉

**¿Qué incluye nuestro Dev Container?** 🧰

Este proyecto viene con un Dev Container basado en Ubuntu 22.04.5 LTS que incluye:

*   🌲 **Git:** Una versión actualizada, lista para que gestiones tu código.
*   🐳 **Docker CLI:** Para que puedas correr y gestionar otros contenedores Docker desde dentro del Dev Container.
*   🏗️ **Terraform CLI:** Para gestionar tu infraestructura como código.
    *   Opcionalmente, también puede incluir `TFLint` (para linting de Terraform) y `Terragrunt` (para mantener tu configuración de Terraform DRY).
*   🐍 **Python:** Con las herramientas necesarias para los proyectos de Python aquí incluidos.
*   🛠️ **Herramientas comunes de línea de comandos de Linux:** `curl`, `wget`, `zip`, `unzip`, `tar`, `grep`, `find`, etc.

**¿Cómo usarlo?** ✨

1.  **Instala la extensión "Dev Containers"** en VS Code (si aún no la tienes). Su ID es `ms-vscode-remote.remote-containers`.
2.  Abre este proyecto en VS Code.
3.  VS Code debería detectar la configuración del Dev Container (`.devcontainer/devcontainer.json`) y preguntarte si quieres "Reabrir en Contenedor" ("Reopen in Container"). ¡Dale que sí!
4.  VS Code construirá la imagen del contenedor (la primera vez puede tardar un poco) y luego se conectará a él.
5.  ¡Listo! Ya estás trabajando dentro de un ambiente preconfigurado y aislado.

Esto asegura que todos los colaboradores tengan las mismas versiones de herramientas y un entorno de desarrollo idéntico, simplificando la incorporación y reduciendo problemas de configuración.

## ¡Manos a la Obra! 🛠️ Guía de Inicio Rápido

### Configuración y Ejecución del Self-Hosted Runner de GitHub Actions 🏃💨

Para que nuestras automatizaciones (GitHub Actions) funcionen en nuestra propia infraestructura (self-hosted), necesitas configurar y luego ejecutar un runner.

#### 1. Configuración Inicial del Runner (Solo la primera vez o si necesitas reconfigurar)

Si es la primera vez que configuras un runner en esta máquina o necesitas registrar uno nuevo:

a.  **Ve a la configuración de Actions en tu repositorio de GitHub:**
    *   Navega a tu repositorio en GitHub: [https://github.com/RodrigoVasquez/agro_extension_digital_project](https://github.com/RodrigoVasquez/agro_extension_digital_project)
    *   Haz clic en `Settings` (Configuración) > `Actions` (Acciones) en el menú lateral izquierdo > `Runners`.
    *   Haz clic en el botón `New self-hosted runner` (Nuevo runner auto-hospedado).
b.  **Sigue las instrucciones de GitHub para descargar y configurar:**
    *   GitHub te proporcionará comandos para descargar el software del runner y luego para configurarlo. El comando de configuración se verá algo así (¡asegúrate de usar el token que te proporcione GitHub!):
        ```bash
        ./config.sh --url https://github.com/RodrigoVasquez/agro_extension_digital_project --token TU_TOKEN_DE_RUNNER_PROPORCIONADO_POR_GITHUB
        ```
    *   Asegúrate de ejecutar este comando dentro del directorio `actions-runner/` de este proyecto. Si el directorio no existe, los comandos de GitHub te guiarán para crearlo y descargar el software del runner.
    *   Puedes asignar etiquetas (labels) al runner durante la configuración si es necesario (por ejemplo, `self-hosted,linux,x64`).

#### 2. Ejecución del Runner (Una vez configurado)

Después de que el runner esté configurado, sigue estos pasos para ejecutarlo:

a.  **Autentícate en Google Cloud (si tus actions interactúan con GCP):**
    ```bash
    gcloud auth login
    ```
b.  **Configura tu proyecto en gcloud (ejemplo para no-producción):**
    ```bash
    gcloud config set project agro-extension-digital-npe
    ```
c.  **Autenticación para aplicaciones por defecto de Google Cloud:**
    ```bash
    gcloud auth application-default login
    ```
d.  **¡Lanza el runner!**
    Asegúrate de estar en el directorio `actions-runner/` donde configuraste y donde reside el script `run.sh`.
    ```bash
    cd actions-runner
    nohup ./run.sh &
    cd .. 
    ```
    El comando `nohup` permite que el runner siga ejecutándose en segundo plano incluso si cierras la terminal, y `&` lo envía al background. La salida se guardará en un archivo `nohup.out` dentro del directorio `actions-runner/`.

**Nota:** Si el runner ya está configurado y solo necesitas iniciarlo, puedes saltar directamente a la sección "2. Ejecución del Runner".

### Creación de Buckets en GCS para el Estado de Terraform 🪣☁️

Terraform necesita un lugar seguro para guardar el "estado" de nuestra infraestructura. Usamos Google Cloud Storage (GCS) para esto.

**Consideraciones Clave Antes de Empezar:** ⚠️

*   **Nombres de Bucket Únicos Globalmente:** Los nombres de los buckets en GCS deben ser únicos en todo el universo de Google Cloud. Si los nombres que te damos ya están pillados, tendrás que inventar unos nuevos (puedes añadir un sufijo único, ¡sé creativo!).
*   **Permisos Necesarios:** La cuenta de Google Cloud que uses debe tener los permisos de IAM adecuados (como `roles/storage.admin`) en los proyectos donde vayas a crear los buckets.
*   **`gcloud` CLI Instalado:** Debes tener la herramienta de línea de comandos de Google Cloud (`gcloud`) instalada y autenticada.

#### Bucket 1: Para el Proyecto `agro-extension-digital-npe` (Ambiente de No-Producción) 🧪

*   **Nombre del Bucket Objetivo:** `agro-extension-digital-npe-tf-state-bucket`
*   **ID del Proyecto Objetivo:** `agro-extension-digital-npe`
*   **Ubicación Objetivo:** `us-central1`

**Comandos:**

```bash
# OPCIONAL: Configura tu gcloud para el proyecto NPE.
# Esto te ahorra tener que escribir --project en los siguientes comandos para esta sección.
# gcloud config set project agro-extension-digital-npe

# 1. Crear el bucket GCS para el proyecto NPE
echo "Intentando crear el bucket 'agro-extension-digital-npe-tf-state-bucket' en el proyecto 'agro-extension-digital-npe'..."
gcloud storage buckets create gs://agro-extension-digital-npe-tf-state-bucket \
  --project=agro-extension-digital-npe \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Habilitar el versionado en el bucket NPE
# ¡El versionado es súper recomendado para el estado de Terraform, así puedes recuperar estados anteriores!
echo "Habilitando versionado para el bucket 'agro-extension-digital-npe-tf-state-bucket'..."
gcloud storage buckets update gs://agro-extension-digital-npe-tf-state-bucket \
  --project=agro-extension-digital-npe \
  --versioning

echo "Proceso de creación y configuración de versionado del bucket 'agro-extension-digital-npe-tf-state-bucket' iniciado para el proyecto 'agro-extension-digital-npe'."
```

#### Bucket 2: Para el Proyecto `agro-extension-digital-prd` (Ambiente de Producción) ✨

*   **Nombre del Bucket Objetivo:** `agro-extension-digital-prd-tf-state-bucket`
*   **ID del Proyecto Objetivo:** `agro-extension-digital-prd`
*   **Ubicación Objetivo:** `us-central1` (la mantenemos igual que NPE por simplicidad)

**Comandos:**

```bash
# OPCIONAL: Configura tu gcloud para el proyecto PRD.
# gcloud config set project agro-extension-digital-prd

# 1. Crear el bucket GCS para el proyecto PRD
echo "Intentando crear el bucket 'agro-extension-digital-prd-tf-state-bucket' en el proyecto 'agro-extension-digital-prd'..."
gcloud storage buckets create gs://agro-extension-digital-prd-tf-state-bucket \
  --project=agro-extension-digital-prd \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Habilitar el versionado en el bucket PRD
echo "Habilitando versionado para el bucket 'agro-extension-digital-prd-tf-state-bucket'..."
gcloud storage buckets update gs://agro-extension-digital-prd-tf-state-bucket \
  --project=agro-extension-digital-prd \
  --versioning

echo "Proceso de creación y configuración de versionado del bucket 'agro-extension-digital-prd-tf-state-bucket' iniciado para el proyecto 'agro-extension-digital-prd'."
```

Después de crear estos buckets, ¡no olvides configurar tu backend de Terraform en tus archivos `.tf` para que apunten al bucket correcto para cada ambiente! 😉

### Despliegue de Infraestructura con Terragrunt 🌍🔧

Terragrunt es una herramienta que nos ayuda a mantener nuestra configuración de Terraform DRY (Don't Repeat Yourself), organizada y más fácil de manejar, especialmente cuando tenemos múltiples entornos.

**Prerrequisitos:**

1.  **Terragrunt Instalado:** Asegúrate de tener [Terragrunt instalado](https://terragrunt.gruntwork.io/docs/getting-started/install/) en tu máquina.
2.  **Autenticación con Google Cloud:** Debes estar autenticado con `gcloud` y tener los permisos necesarios para desplegar recursos en los proyectos de GCP correspondientes.
    ```bash
    gcloud auth login
    gcloud auth application-default login
    ```
3.  **Buckets de State Creados:** Asegúrate de haber creado los buckets de GCS para el estado de Terraform como se describe en la sección anterior.

**Pasos para el Despliegue:**

Los comandos de Terragrunt generalmente se ejecutan desde el directorio del entorno específico que quieres gestionar (por ejemplo, `cicd/dev` o `cicd/prd`) o desde un directorio raíz si tienes un `terragrunt.hcl` que los englobe.

1.  **Navega al Directorio del Entorno:**
    *   Para el ambiente de No-Producción (NPE/dev):
        ```bash
        cd cicd/dev
        ```
    *   Para el ambiente de Producción (PRD):
        ```bash
        cd cicd/prd
        ```

2.  **Inicializa Terragrunt (y Terraform):**
    Este comando descarga los providers de Terraform y configura el backend.
    ```bash
    terragrunt init
    ```
    O si quieres inicializar todos los módulos recursivamente (si tienes una estructura con `run-all`):
    ```bash
    terragrunt run-all init
    ```

3.  **Planifica los Cambios:**
    Revisa los cambios que Terragrunt aplicará a tu infraestructura.
    ```bash
    terragrunt plan
    ```
    O para todos los módulos:
    ```bash
    terragrunt run-all plan
    ```

4.  **Aplica los Cambios:**
    Este comando provisionará o modificará tu infraestructura según la configuración.
    ```bash
    terragrunt apply
    ```
    O para todos los módulos (¡usa con precaución, especialmente en producción!):
    ```bash
    terragrunt run-all apply
    ```
    Terragrunt te pedirá confirmación antes de aplicar los cambios.

**Ejemplo de Despliegue Completo para un Entorno (ej. dev):**

```bash
# 1. Asegúrate de estar autenticado en GCP
gcloud auth login
gcloud auth application-default login

# 2. Configura el proyecto de gcloud para el entorno (opcional, pero buena práctica)
gcloud config set project agro-extension-digital-npe # O el ID de tu proyecto dev

# 3. Navega al directorio del entorno
cd cicd/dev

# 4. Inicializa
terragrunt run-all init # O terragrunt init si no usas run-all

# 5. Planifica
terragrunt run-all plan # O terragrunt plan

# 6. Aplica (revisa el plan cuidadosamente antes de este paso)
terragrunt run-all apply # O terragrunt apply
```

**Destruir la Infraestructura (¡CON MUCHO CUIDADO!)** 💣

Si necesitas eliminar la infraestructura gestionada por Terragrunt en un entorno:

```bash
# Navega al directorio del entorno correspondiente (ej. cicd/dev)
cd cicd/dev 
terragrunt run-all destroy # O terragrunt destroy
```
**Siempre revisa el plan de destrucción cuidadosamente antes de confirmar.**

¡Y eso es todo! Con estos pasos deberías poder desplegar tu infraestructura usando Terragrunt. 🚀