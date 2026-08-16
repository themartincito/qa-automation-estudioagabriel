# QA Automation — estudioagabriel.com.ar

Proyecto de QA automatizado end-to-end sobre un sitio de producción real (estudio jurídico), enfocado en **diagnosticar, documentar y corregir** un problema de performance — desde la detección hasta el fix aplicado en el código fuente.

> Este no es un demo sobre un sitio de prueba: es un caso real, con un cliente real, un bug real, y un fix real.

## El problema

El sitio tardaba en cargar y no había forma sistemática de saber por qué. El objetivo fue construir una suite de QA automatizado que permitiera:

1. Medir objetivamente la performance (Lighthouse CI).
2. Validar comportamiento funcional y de red bajo distintas condiciones (Playwright).
3. Encontrar la causa raíz con evidencia, no con suposiciones.
4. Aplicar el fix y dejar un test de regresión que impida que el problema vuelva.

## Qué encontré

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| 1 | Imagen de 1.92 MB sin optimizar = 84% del peso total de la página | Alto (performance) | ✅ Diagnosticado y fix aplicado |
| 2 | DNS del dominio falla (SERVFAIL) contra resolvers públicos (Google/Cloudflare) — el sitio es inalcanzable para una porción de usuarios | Crítico (disponibilidad) | 🔴 Detectado y trackeado (requiere acción del proveedor de hosting) |

Detalle completo, con evidencia y métricas antes/después: [`reports/root-cause-analysis.md`](reports/root-cause-analysis.md)

**Resultado del fix de la imagen:**

| | Antes | Después |
|---|---|---|
| Peso de la imagen principal | 1,920 KB (PNG) | 33 KB (WebP) |
| Peso total de la página | 2,275 KB | ~415 KB (estimado) |
| Ahorro | — | **98.3%** en la imagen, ~82% en el total de la página |

## Stack

- **Playwright (Python) + pytest** — tests funcionales, de disponibilidad, de presupuesto de peso de página y de emulación de red (3G/4G vía Chrome DevTools Protocol)
- **Lighthouse CI / Lighthouse CLI** — auditoría de performance, en perfiles desktop y mobile
- **dnspython** — test automatizado de resolución DNS contra resolvers públicos
- **Pillow** — generación de los assets optimizados (WebP/JPEG) para el fix

## Qué cubre la suite de tests

```
tests/
├── conftest.py               # dominios, perfiles de red, presupuesto de página
├── test_availability.py      # status 200, redirect HTTP→HTTPS, título de página (2 dominios)
├── test_dns_resolution.py    # resolución DNS contra Google/Cloudflare (xfail trackeado)
└── test_performance.py       # presupuesto de peso de página + tiempos de carga bajo 3G/4G/sin throttling
```

18 tests en total, parametrizados sobre ambos dominios del sitio (`estudioagabriel.com.ar` y `estudioagabriel.ar`).

## Cómo correrlo

```bash
# 1. Clonar y entrar al proyecto
git clone <este-repo>
cd qa-automation-estudioagabriel

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install msedge

# 3. Correr la suite de Playwright
pytest -v
# Reporte HTML en reports/playwright-report/report.html

# 4. Correr Lighthouse CI (requiere Node.js)
npm install
npm run lighthouse:desktop
npm run lighthouse:mobile
```

## Estructura del proyecto

```
qa-automation-estudioagabriel/
├── tests/                       # suite de Playwright + pytest
├── reports/
│   ├── root-cause-analysis.md   # análisis técnico completo con evidencia
│   ├── lighthouse/              # reportes HTML/JSON de Lighthouse (desktop + mobile)
│   ├── optimized-assets/        # imagen original vs. optimizada, con comparación
│   └── playwright-report/       # reporte HTML de la última corrida de tests
├── lighthouserc.desktop.js
├── lighthouserc.mobile.js
├── pytest.ini
├── requirements.txt
└── package.json
```

## Nota sobre el entorno de testing

Durante el desarrollo encontré que el Chromium que descarga Playwright por defecto no arrancaba en el entorno de Windows usado (error de dependencias del sistema operativo). Lo diagnostiqué (`sxstrace`, verificación de Visual C++ Redistributable) y resolví configurando Playwright para usar Microsoft Edge (`--browser-channel=msedge`) en vez del Chromium embebido — documentado en `pytest.ini`. Un ejemplo más de troubleshooting real de entorno, no solo de "código que anduvo a la primera".

## Sobre este proyecto

Lo armé para mi portfolio como QA/Support Specialist, usando el sitio real del estudio jurídico de mi mamá como caso de estudio. El foco no fue solo "correr Lighthouse una vez", sino construir algo reproducible: tests parametrizados, un test de regresión para el bug encontrado, un hallazgo de infraestructura documentado y trackeado como *known issue*, y un fix real aplicado al código fuente con evidencia de impacto.

---

📍 GBA · CABA · Buenos Aires, Argentina
