# Fase 4: Pruebas de Carga en Entorno Simulado de PYME

**Autores:** Lina María Andrade Gómez, Juan José Barrera Gracia, Andrés Mauricio Mesa Franco  

---

## Descripción General

La fase 4 simula un entorno real de PYME (pequeña y mediana empresa) mediante pruebas de carga con Locust. Se crean tres escenarios realistas basados en datos de tráfico de empresas colombianas e internacionales, validando el comportamiento del WAF bajo diferentes cargas.

---

## Objetivos

1. **Simular tráfico real:** Crear escenarios de carga basados en datos de pymes.
2. **Validar WAF:** Evaluar comportamiento bajo diferentes cargas
3. **Medir rendimiento:** Analizar consumo de CPU y RAM.

---
## Estructura del repositorio

````
Stage4-WAF-Evaluation/
│
├── docs/
│   └── DocumentacionFaseIV.pdf
│
└── scripts/
    ├── load_traffic/
    │   └── locustfile.py
    │
    └── monitoring/
        ├── visualization/
        │   └── graph.py
        │
        └── collection/
            └── coraza.sh
````

## Fundamentos Matemáticos

### Ley de Little

La Ley de Little establece el número promedio de usuarios concurrentes en un sistema:

```
Uc = V × D

Donde:
  Uc = Usuarios concurrentes
  V  = Visitas esperadas por minuto
  D  = Duración promedio de cada sesión (minutos)
```

**Ejemplo - Escenario 1:**
```
V = 8,000 visitas/mes ÷ 30 días ÷ 10 horas ÷ 60 min
V ≈ 0.45 visitas/minuto

D = 4 minutos (duración promedio sesión)

Uc = 0.45 × 4 = 1.8 ≈ 2 usuarios concurrentes
```

---

## Conceptos Clave

### Tráfico en PYMEs Colombianas

**Fuentes:**
- HubSpot 2023: Encuesta sobre distribución de tráfico en empresas estadounidenses
- DashThis & Google Analytics: Duración promedio de sesión 2-4 minutos
- ConvertCart 2024: Duración promedio global ~4.41 minutos

**Supuestos:**
- Duración sesión: **4 minutos** (consenso internacional)
- Horas productivas: **10 horas/día** (laboral)
- Tráfico malicioso: **5%** (aproximación realista)

### Usuarios Concurrentes vs. Usuarios en Prueba

**Calculados:** Basados en Ley de Little  
**En Prueba:** Mayor para agregar carga adicional y validar tolerancia

---

## Endpoints Utilizados

Se usan **8 endpoints** de DVWA (SQLi y Comand Inj. cuentan con endpoint GET y POST):

| # | Endpoint | Método | Vulnerabilidad |
|---|----------|--------|-----------------|
| 1 | `/vulnerabilities/sqli/` | GET/POST | SQL Injection |
| 2 | `/vulnerabilities/sqli_blind/` | GET | Blind SQLi |
| 3 | `/vulnerabilities/exec/` | GET/POST | Command Injection |
| 4 | `/vulnerabilities/xss_r/` | GET | Reflected XSS |
| 5 | `/vulnerabilities/xss_s/` | POST | Stored XSS |
| 6 | `/vulnerabilities/fi/` | GET | File Inclusion |

---

## Ejecución de escenarios

```bash
# Escenario 1: Bajo
locust -f locustfile.py --host=http://100.118.62.112:8090  \
--users 20 --spawn-rate 5 --run-time 5m --headless \
--csv escenario_bajo

# Escenario 2: Medio
locust -f locustfile.py --host=http://100.118.62.112:8090 \
--users 50 --spawn-rate 10 --run-time 5m --headless \
--csv escenario_medio

# Escenario 3: Alto
locust -f locustfile.py --host=http://100.118.62.112:8090 \
--users 100 --spawn-rate 15 --run-time 5m --headless \
--csv escenario_alto
```

## Monitoreo

**Archivo:** `/scripts/collection/coraza.sh`

**Recopilación de datos:**

```
pidstat -u -r -p <PID> 2 > coraza_stats.txt
```

**Formato de salida:**

```
02:43:22 PM   UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
02:43:24 PM  1000     31346    1.50    1.00    0.00    0.00    2.50     1  coraza

02:43:22 PM   UID       PID  minflt/s  majflt/s     VSZ     RSS   %MEM  Command
02:43:24 PM  1000     31346    550.50      0.00 1976616   22224   0.14  coraza
...
```

### Visualización

**Procedimiento:**

```
python3 /scripts/monitoring/visualization/graph.py
```
---
## Referencias

### Documentación Locust
- [Locust Official Docs](https://docs.locust.io/)
- [Locust GitHub](https://github.com/locustio/locust)

### Investigación Tráfico
- [HubSpot 2023 Survey](https://blog.hubspot.com/)
- [ConvertCart 2024](https://convertcart.com/)
- [DashThis Analytics](https://dashthis.com/)

### Teoría de Colas
- [Ley de Little Wikipedia](https://en.wikipedia.org/wiki/Little%27s_law)
- [Graves & Little Papers](https://scholar.google.com/)

---
