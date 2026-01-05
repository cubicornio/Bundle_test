from __future__ import annotations
from typing import Dict, List, Any


def get_submodule_guidelines() -> List[Dict[str, Any]]:
    """
    Index de reglas/consideraciones para desarrollar submódulos.
    - Agrupado por categorías.
    - Cada punto tiene id único, title, summary, bullets.
    - Puedes agregar un partial HTML por id en: templates/_partials/guidelines/<id>.html
    """
    return [
        {
        "group_id": "architecture",
        "title": "Arquitectura y Estructura",
        "icon": "layers",
        "items": [
            {
                "id": "arch-01",
                "title": "Estructura base del submódulo",
                "summary": "Organiza el módulo con separación clara: domain / application / infrastructure / interface.",
                "bullets": [
                    "Empieza por el core (domain) y avanza hacia afuera (interface).",
                    "Evita lógica de negocio en templates o rutas.",
                    "Define desde el inicio la carpeta templates/static del submódulo.",
                ],
            },
            {
                "id": "arch-02",
                "title": "Flujo recomendado de construcción",
                "summary": "Orden correcto: DDL/tablas → ORM → casos de uso → UI (forms/CRUD).",
                "bullets": [
                    "Si ya existe estructura de tablas, empieza por ahí (modelos ORM).",
                    "Luego define casos de uso (create/update/list/detail).",
                    "Recién al final arma los forms/CRUD con campos reales del ORM.",
                ],
            },
            {
                "id": "arch-03",
                "title": "Convenciones de módulos y nombres",
                "summary": "Mantén naming consistente en carpetas, rutas, templates y recursos.",
                "bullets": [
                    "Usa un prefijo estable (ej: submodule_*, registry_*, etc.).",
                    "Evita nombres genéricos (helpers.py, utils.py) sin propósito claro.",
                    "No mezclar responsabilidades dentro de un mismo archivo.",
                ],
            },
        ],
    },
    {
        "group_id": "data",
        "title": "Datos, ORM y CRUD",
        "icon": "database",
        "items": [
            {
                "id": "data-01",
                "title": "DDL primero: tablas → ORM",
                "summary": "Si tienes tablas definidas, lo más eficiente es mapear el ORM antes de inventar UI.",
                "bullets": [
                    "Asegura tipos correctos: DECIMAL, VARCHAR, TEXT, DATETIME, NULL/NOT NULL.",
                    "Define claves primarias y campos meta (created_at, updated_at, etc.).",
                    "No diseñes forms sin tener claro el DDL final.",
                ],
            },
            {
                "id": "data-02",
                "title": "Regla de naming: Tabla = ORM = variable",
                "summary": "Los nombres deben ser iguales para evitar confusiones y bugs al escalar.",
                "bullets": [
                    "Nombre de tabla en DB igual al nombre del modelo ORM (misma “identidad”).",
                    "Variables que representan colecciones/listados también siguen el naming.",
                    "Si necesitas alias, que sean mínimos y consistentes.",
                ],
            },
            {
                "id": "data-03",
                "title": "Forms y campos: el DDL manda",
                "summary": "Los inputs deben mapear 1:1 a campos reales, sin inventar nombres.",
                "bullets": [
                    "name=\"campo\" debe coincidir con el campo del DDL/ORM.",
                    "Nunca renderizar 'None'/'null' como texto en inputs.",
                    "Normaliza: None → '' en UI, '' → NULL en backend al guardar.",
                ],
            },
            {
                "id": "data-04",
                "title": "Forms complejos: modo Simple vs Completo (variant_control)",
                "summary": "Para formularios complejos, habilita 2 variantes: simple y completa.",
                "bullets": [
                    "Incluye: {% include 'core_ui/partials/variant_control.html' %}",
                    "Simple = mínimos campos, Completo = todo (detallado).",
                    "Persistir preferencia del usuario (localStorage) cuando aplique.",
                ],
            },
            {
                "id": "data-05",
                "title": "Campos meta y trazabilidad",
                "summary": "Toda tabla importante debe poder auditarse.",
                "bullets": [
                    "created_at, updated_at, annulled_at (si aplica).",
                    "actor info: user_id/username cuando guardes cambios.",
                    "Evita deletes duros si el módulo lo necesita auditable.",
                ],
            },
        ],
    },
    {
        "group_id": "backend",
        "title": "Backend e Integración",
        "icon": "server",
        "items": [
            {
                "id": "be-01",
                "title": "Casos de uso antes que endpoints",
                "summary": "Primero define el comportamiento (use cases), luego lo expones vía rutas.",
                "bullets": [
                    "Use cases: create, update, list, detail, archive.",
                    "Validaciones y reglas de negocio viven en application/domain.",
                    "Rutas (Flask) deben ser delgadas: parsean + llaman use case.",
                ],
            },
            {
                "id": "be-02",
                "title": "Repositorios y boundaries",
                "summary": "Acceso a DB o servicios externos encapsulado en repositorios/adapters.",
                "bullets": [
                    "Infra: repositories para DB, adapters para APIs.",
                    "Application no conoce SQL crudo si puedes evitarlo.",
                    "Centraliza transformaciones DTO/ORM para consistencia.",
                ],
            },
            {
                "id": "be-03",
                "title": "Tips Flask (si aplica): endpoints y url_for",
                "summary": "Evita errores de endpoint cuidando naming y organización de rutas.",
                "bullets": [
                    "Evita duplicar nombres de funciones en blueprints.",
                    "Mantén nombres de blueprint estables.",
                    "Si algo falla, revisa request.endpoint y url_for(...) con nombre completo.",
                ],
            },
            {
                "id": "be-04",
                "title": "Errores y respuestas (HTML/JSON)",
                "summary": "Respuestas coherentes según el tipo de vista.",
                "bullets": [
                    "HTML: flash + redirect si corresponde.",
                    "JSON: {ok:false,error:'...'} con status correcto.",
                    "No filtrar stacktrace al usuario final.",
                ],
            },
        ],
    },
    {
        "group_id": "frontend",
        "title": "Frontend y UX",
        "icon": "layout",
        "items": [
            {
                "id": "fe-01",
                "title": "Listados y estados vacíos",
                "summary": "Todo listado debe manejar: loading, empty, error.",
                "bullets": [
                    "Empty state con CTA (crear nuevo).",
                    "Skeleton/loading suave si hay fetch.",
                    "Mensaje claro si no hay permisos o no hay data.",
                ],
            },
            {
                "id": "fe-02",
                "title": "CRUD usable (UX práctica)",
                "summary": "El CRUD debe ser rápido y sin fricción.",
                "bullets": [
                    "Confirmaciones para acciones destructivas.",
                    "Botones claros: Guardar / Guardar y nuevo / Cancelar.",
                    "Evita forms eternos: usa variant simple vs completo.",
                ],
            },
            {
                "id": "fe-03",
                "title": "Consistencia visual (Core UI)",
                "summary": "Usa componentes/partials del Core UI para mantener look & feel.",
                "bullets": [
                    "Reusar partials (alerts, cards, buttons, tooltips).",
                    "Mantener spacing, tamaños y tipografías consistentes.",
                    "No inventar 4 estilos distintos para el mismo patrón.",
                ],
            },
        ],
    },
    {
        "group_id": "security",
        "title": "Seguridad y Accesos",
        "icon": "shield",
        "items": [
            {
                "id": "sec-01",
                "title": "Contexto de negocio y aislamiento",
                "summary": "Todo se ejecuta con un business context activo y aislado.",
                "bullets": [
                    "No aceptar business_id desde querystring como fuente confiable.",
                    "Siempre derivar contexto desde sesión/token cuando exista.",
                    "Aislar data por tenant (sin mezclar business).",
                ],
            },
            {
                "id": "sec-02",
                "title": "Permisos (RBAC) aplicados en backend",
                "summary": "Toda acción debe validar permisos, no solo ocultar botones.",
                "bullets": [
                    "view/create/update/archive controlados por guards.",
                    "En UI: ocultar acciones si no hay permiso (pero igual validar en backend).",
                    "Logs mínimos por acción sensible.",
                ],
            },
            {
                "id": "sec-03",
                "title": "Validaciones y sanitización",
                "summary": "Sanitiza parámetros y evita inputs inseguros.",
                "bullets": [
                    "Validar IDs esperados (alnum, etc.) cuando aplique.",
                    "Evitar construir SQL/paths con strings del usuario.",
                    "Limitar uploads/paths y usar send_from_directory con cuidado.",
                ],
            },
        ],
    },
    {
        "group_id": "quality",
        "title": "Calidad, Operación y Mantenimiento",
        "icon": "wrench",
        "items": [
            {
                "id": "qa-01",
                "title": "Logging y trazabilidad mínima",
                "summary": "Cada write importante debe quedar trazable.",
                "bullets": [
                    "Loggear: actor, business, acción, id afectado.",
                    "Errores con logger.exception para debug real.",
                    "No spamear logs, pero sí registrar lo importante.",
                ],
            },
            {
                "id": "qa-02",
                "title": "Testing mínimo recomendado",
                "summary": "Pruebas básicas de casos de uso y smoke web.",
                "bullets": [
                    "Unit tests a use cases críticos.",
                    "Smoke: landing/listado responde 200 con contexto.",
                    "Fixtures para actor_ctx y business_ctx.",
                ],
            },
            {
                "id": "qa-03",
                "title": "Configuración y despliegue",
                "summary": "Variables de entorno claras y comportamiento predecible.",
                "bullets": [
                    "Secrets solo en env vars, no hardcode.",
                    "Timeouts razonables a servicios externos.",
                    "Errores controlados (sin romper toda la UI).",
                ],
            },
        ],
    },
    ]
