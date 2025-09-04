from __future__ import annotations

import os
from glob import glob
import typing as t

import importlib_resources
from tutor import hooks
from tutormfe.hooks import PLUGIN_SLOTS
from tutor.__about__ import __version_suffix__

from .__about__ import __version__

# ------------------------------------------------------------------------------
# Handle version suffix in nightly mode
# ------------------------------------------------------------------------------
if __version_suffix__:
    __version__ += "-" + __version_suffix__

# ------------------------------------------------------------------------------
# Theme configuration
# ------------------------------------------------------------------------------
config: t.Dict[str, t.Dict[str, t.Any]] = {
    "defaults": {
        "VERSION": __version__,
        "WELCOME_MESSAGE": "Plataforma de entrenamiento digital educativo para instituciones públicas y de interés educativo",
        "PRIMARY_COLOR": "#82c5be",
        "ACCENT_COLOR": "#A67F00",
        "HIGHLIGHT_COLOR": "#FFE19F",
        "ENABLE_DARK_TOGGLE": True,
        # Footer links are dictionaries with a "title" and "url"
        # To remove all links, run:
        # tutor config save --set INDIGO_FOOTER_NAV_LINKS=[]
        "FOOTER_NAV_LINKS": [
            {"title": "Sobre el proyecto", "url": "/about"},
            {"title": "Boletín informativo", "url": "https://mail.mexicox.gob.mx/lists/?p=subscribe"},
            {"title": "Código de honor", "url": "/honor"},
            {"title": "Aviso de privacidad", "url": "/tos"},
            {"title": "Preguntas frecuentes", "url": "/help"},
            {"title": "Contacto", "url": "/contact"},
            {"title": "Soporte", "url": "https://soporte.mexicox.gob.mx"},
        ],
    },
    "unique": {},
    "overrides": {},
}
# ------------------------------------------------------------------------------
# Templates and static assets
# ------------------------------------------------------------------------------
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    str(importlib_resources.files("mexicoxmx") / "templates")
)
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items([
    ("mexicoxmx", "build/openedx/themes"),
    ("mexicoxmx/env.config.jsx", "plugins/mfe/build/mfe"),
])
hooks.Filters.ENV_PATTERNS_INCLUDE.add_items([
    r"mexicoxmx/lms/static/sass/partials/lms/theme/",
    r"mexicoxmx/cms/static/sass/partials/cms/theme/",
])

# init tasks script
with open(
    os.path.join(
        str(importlib_resources.files("mexicoxmx") / "templates"),
        "mexicoxmx", "tasks", "init.sh",
    ),
    encoding="utf-8",
) as task_file:
    hooks.Filters.CLI_DO_INIT_TASKS.add_item(("lms", task_file.read()))

# ------------------------------------------------------------------------------
# Override Docker image names
# ------------------------------------------------------------------------------
@hooks.Filters.CONFIG_DEFAULTS.add(priority=hooks.priorities.LOW)
def _override_openedx_docker_image(
    items: list[tuple[str, t.Any]]
) -> list[tuple[str, t.Any]]:
    openedx_image = ""
    mfe_image = ""
    for k, v in items:
        if k == "DOCKER_IMAGE_OPENEDX":
            openedx_image = v
        elif k == "MFE_DOCKER_IMAGE":
            mfe_image = v
    if openedx_image:
        items.append(("DOCKER_IMAGE_OPENEDX", f"{openedx_image}-mexicoxmx"))
    if mfe_image:
        items.append(("MFE_DOCKER_IMAGE", f"{mfe_image}-mexicoxmx"))
    return items


# ------------------------------------------------------------------------------
# Load all config entries into Tutor
# ------------------------------------------------------------------------------
hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"INDIGO_{key}", value) for key, value in config["defaults"].items()]
)
hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"INDIGO_{key}", value) for key, value in config["unique"].items()]
)
hooks.Filters.CONFIG_OVERRIDES.add_items(
    list(config["overrides"].items())
)

# ------------------------------------------------------------------------------
# NPM patches for Indigo branding
# ------------------------------------------------------------------------------
indigo_styled_mfes = [
    "learning",
    "learner-dashboard",
    "profile",
    "account",
    "discussions",
]

for mfe in indigo_styled_mfes:
    hooks.Filters.ENV_PATCHES.add_item(
        (
            f"mfe-dockerfile-post-npm-install-{mfe}",
            """
RUN npm install @edly-io/indigo-frontend-component-footer@^3.0.0
RUN npm install '@edx/frontend-component-header@npm:@edly-io/indigo-frontend-component-header@^4.0.0'
RUN npm install '@edx/brand@npm:@edly-io/indigo-brand-openedx@^2.2.2'
""",
        ),
    )

hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-dockerfile-post-npm-install-authn",
        "RUN npm install '@edx/brand@npm:@edly-io/indigo-brand-openedx@^2.2.2'",
    )
)

# ------------------------------------------------------------------------------
# Inyectar colores y componentes en TODOS los MFEs
# ------------------------------------------------------------------------------
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-env-config-runtime-definitions",
        f"""
// --- Componente Footer Indigo ---
const {{ default: IndigoFooter }} = await import('@edly-io/indigo-frontend-component-footer');

// --- Colores personalizados MexicoXMX (todos los MFEs) ---
MFE_CONFIG['PRIMARY_COLOR']   = '{config['defaults']['PRIMARY_COLOR']}';
MFE_CONFIG['SECONDARY_COLOR'] = '{config['defaults']['ACCENT_COLOR']}';
MFE_CONFIG['HIGHLIGHT_COLOR'] = '{config['defaults']['HIGHLIGHT_COLOR']}';
"""
    )
)

# ------------------------------------------------------------------------------
# Include dark-theme.js in Django PIPELINE and toggle flag
# ------------------------------------------------------------------------------
hooks.Filters.ENV_PATCHES.add_items([
    (
        "openedx-common-assets-settings",
        """
javascript_files = ['base_application', 'application', 'certificates_wv']
dark_theme_filepath = ['mexicoxmx/js/dark-theme.js']

for filename in javascript_files:
    if filename in PIPELINE['JAVASCRIPT']:
        PIPELINE['JAVASCRIPT'][filename]['source_filenames'] += dark_theme_filepath
"""
    ),
    (
        "openedx-lms-development-settings",
        """
javascript_files = ['base_application', 'application', 'certificates_wv']
dark_theme_filepath = ['mexicoxmx/js/dark-theme.js']

for filename in javascript_files:
    if filename in PIPELINE['JAVASCRIPT']:
        PIPELINE['JAVASCRIPT'][filename]['source_filenames'] += dark_theme_filepath

MFE_CONFIG['INDIGO_ENABLE_DARK_TOGGLE'] = {{ INDIGO_ENABLE_DARK_TOGGLE }}
"""
    ),
    (
        "openedx-lms-production-settings",
        """
MFE_CONFIG['INDIGO_ENABLE_DARK_TOGGLE'] = {{ INDIGO_ENABLE_DARK_TOGGLE }}
"""
    ),
])

# ------------------------------------------------------------------------------
# Load any additional patches from mexicoxmx/patches/
# ------------------------------------------------------------------------------
for path in glob(
    os.path.join(
        str(importlib_resources.files("mexicoxmx") / "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

# ------------------------------------------------------------------------------
# Footer slot widgets
# ------------------------------------------------------------------------------


for mfe in indigo_styled_mfes:
    PLUGIN_SLOTS.add_item(
        (
            mfe,
            "footer_slot",
            """
            {
                op: PLUGIN_OPERATIONS.Hide,
                widgetId: 'default_contents',
            },
            {
                op: PLUGIN_OPERATIONS.Insert,
                widget: {
                    id: 'default_contents',
                    type: DIRECT_PLUGIN,
                    priority: 1,
                    RenderWidget: <IndigoFooter />,
                },
            },
            {
                op: PLUGIN_OPERATIONS.Insert,
                widget: {
                    id: 'read_theme_cookie',
                    type: DIRECT_PLUGIN,
                    priority: 2,
                    RenderWidget: AddDarkTheme,
                },
            },
            """
        ),
    )