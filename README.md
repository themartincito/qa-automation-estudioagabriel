# QA Automation — estudioagabriel.com.ar

Proyecto de QA automatizado end-to-end sobre un sitio de producción real (estudio jurídico), enfocado en **diagnosticar, documentar y corregir** un problema de performance — desde la detección hasta el fix aplicado en el código fuente.

> Este no es un demo sobre un sitio de prueba: es un caso real, con un cliente real, un bug real, y un fix real.

**En números:**

- 📉 **−83% de peso de página** (2,275 KB → 387 KB), medido en producción, no estimado
- 🐛 **2 fixes reales** aplicados y verificados con Lighthouse antes/después
- 🔴 **1 bug crítico de infraestructura** encontrado (DNS) y trackeado como test automatizado
- ✅ **18 tests** parametrizados sobre 2 dominios (Playwright + pytest)

## El problema

El sitio tardaba en cargar y no había forma sistemática de saber por qué. El objetivo fue construir una suite de QA automatizado que permitiera:

1. Medir objetivamente la performance (Lighthouse CI).
2. Validar comportamiento funcional y de red bajo distintas condiciones (Playwright).
3. Encontrar la causa raíz con evidencia, no con suposiciones.
4. Aplicar el fix y dejar un test de regresión que impida que el problema vuelva.

## Qué encontré

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| 1 | Imagen de 1.92 MB sin optimizar = 84% del peso total de la página | Alto (performance) | ✅ Diagnosticado, fix aplicado y **verificado en producción** |
| 2 | DNS del dominio falla (SERVFAIL) contra resolvers públicos (Google/Cloudflare) — el sitio es inalcanzable para una porción de usuarios | Crítico (disponibilidad) | 🔴 Detectado y trackeado (requiere acción del proveedor de hosting) |
| 3 | El LCP real (título del hero) estaba bloqueado por Google Fonts cargado de forma síncrona | Medio (performance) | ✅ Fix aplicado y verificado (render-blocking eliminado; LCP casi no bajó — ver Hallazgo #4) |
| 4 | Tras eliminar el bloqueo de fuentes, el `<h1>` sigue tardando ~1.3-1.4s en pintar después de tener todo disponible ("element render delay") — probablemente CSS/JS propio del sitio | Medio (performance) | 🟡 Identificado con datos concretos, no investigado en profundidad (fuera de alcance de este ciclo) |

Detalle completo, con evidencia y métricas antes/después medidas contra el sitio real en producción: [`reports/root-cause-analysis.md`](reports/root-cause-analysis.md)

**Resultado del fix de la imagen (medido en vivo, no estimado):**

| | Antes | Después | Cambio |
|---|---|---|---|
| Peso de la imagen principal | 1,920 KB (PNG) | 33 KB (WebP) | **−98.3%** |
| Peso total de la página (desktop) | 2,275 KB | **387 KB** | **−83%** |
| Peso total de la página (mobile) | 2,275 KB | **354 KB** | **−84%** |
| Test de regresión `test_page_weight_budget` | ❌ FAILED | ✅ PASSED | — |

**La cadena de hallazgos honesta (así fue en la práctica, no en retrospectiva prolija):**

1. El peso de página bajó ~83% con el fix de la imagen, pero el *Largest Contentful Paint* casi no se movió.
2. Investigando por qué, encontré que el elemento LCP real nunca fue esa imagen — es el título del hero, y estaba bloqueado por la carga síncrona de Google Fonts (Hallazgo #3).
3. Apliqué el fix de fuentes (patrón preload+swap) y lo verifiqué: el render-blocking desapareció por completo, pero el LCP **tampoco** mejoró significativamente.
4. Volví a investigar con el desglose de fases de Lighthouse: la fuente ya no es el problema, ahora el retraso está en el "element render delay" (~1.3-1.4s), probablemente CSS/JS propio del sitio (Hallazgo #4, sin resolver por ahora).

No todo fix "obvio" mueve la métrica que uno espera, y seguir investigando en vez de conformarse con el primer número que mejora es justamente el trabajo de QA. Evidencia completa de cada paso en [`reports/root-cause-analysis.md`](reports/root-cause-analysis.md).

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
git clone https://github.com/themartincito/qa-automation-estudioagabriel.git
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

## Próximos pasos / mejoras futuras

- **Corregir el problema de DNS** (Hallazgo #2) — requiere acción del proveedor de hosting sobre `dns1/2/3.outergate.online`.
- **Investigar el "element render delay" de ~1.3-1.4s** (Hallazgo #4) — con el bloqueo de fuentes ya eliminado, el `<h1>` del hero sigue tardando ese tiempo en pintar. Candidato principal: el bloque `<style>` inline del sitio, bastante grande. Requiere profiling de CSS/JS en el hilo principal, no solo cambios de carga de recursos.
- **Self-hosting de Google Fonts** — evaluado conscientemente y descartado *para este ciclo* en favor del patrón preload+swap (menor riesgo, un solo commit reversible). Serviría los `.woff2` desde el propio dominio en vez de depender de `fonts.gstatic.com`, eliminando por completo la dependencia externa. Es la opción de mejor performance posible, pero de mayor esfuerzo — queda como candidato para una próxima iteración una vez validado el impacto del fix actual.
- Corregir la codificación de caracteres del HTML (artefactos tipo `Ã­`, `â€“` detectados en el texto).

## Nota sobre el entorno de testing

Durante el desarrollo encontré que el Chromium que descarga Playwright por defecto no arrancaba en el entorno de Windows usado (error de dependencias del sistema operativo). Lo diagnostiqué (`sxstrace`, verificación de Visual C++ Redistributable) y resolví configurando Playwright para usar Microsoft Edge (`--browser-channel=msedge`) en vez del Chromium embebido — documentado en `pytest.ini`. Un ejemplo más de troubleshooting real de entorno, no solo de "código que anduvo a la primera".

## Sobre este proyecto

Lo armé para mi portfolio como QA/Support Specialist, usando el sitio real del estudio jurídico de mi mamá como caso de estudio. El foco no fue solo "correr Lighthouse una vez", sino construir algo reproducible: tests parametrizados, un test de regresión para el bug encontrado, un hallazgo de infraestructura documentado y trackeado como *known issue*, y dos fixes reales aplicados al código fuente con evidencia de impacto medida en producción.

## Autor

**Martín Lautaro Sosa Gabriel** — QA / Support Specialist

🔗 [linkedin.com/in/martinlautarososa](https://www.linkedin.com/in/martinlautarososa/)

---

📍 GBA · CABA · Buenos Aires, Argentina
