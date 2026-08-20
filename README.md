# Ofertas de Mercado Público para CRL Coffee

Lista diaria de **licitaciones** y **compras ágiles** del Estado de Chile que encajan con lo que vende [Coffee Roasting Labs](https://www.crlcoffee.cl): café de especialidad en grano, tostado a pedido, con envío a todo Chile.

El programa habla con las APIs oficiales de ChileCompra:

- Licitaciones: `https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json`
- Compra Ágil: `https://api2.mercadopublico.cl/v2/compra-agil`

No inventa oportunidades: baja las fichas públicas, las filtra y las ordena según tu rubro.

## Qué prioriza

| Prioridad | Qué significa para ti |
| --- | --- |
| **Excelente** | Piden café en grano, tostado o de especialidad (UNSPSC `50201706`). Es tu producto. |
| **Buena** | Compra de café o insumos de cafetería donde puedes ofertar grano. |
| **Regular** | Instantáneo / tipo Nescafé. Puedes cotizar un equivalente, pero no es tu fuerte. |
| **Servicio** | Coffee break o catering. No es venta de grano; aparece aparte por si te interesa el canal. |
| **Descartada** | Concesión de cafetería, reparación de máquinas o “especialidad” médica. |

Ejemplos reales que el puntaje ya reconoce:

- *1 kilo de café de especialidad de granos selectos, tostados* → excelente
- *10 kilos de café 100% grano arábica + máquina en comodato* → excelente / buena
- *Tarro similar a Nescafé 400 g* → regular
- *Servicio de coffe break para 13 personas* → servicio

## 1. Pide tu ticket (obligatorio)

La API es gratuita, pero ChileCompra identifica cada consulta con un ticket personal.

1. Entra a [https://www.chilecompra.cl/api/](https://www.chilecompra.cl/api/)
2. Acepta los términos e inicia sesión con **Clave Única**
3. Completa el formulario con motivo **Solicitud de Ticket**
4. Revisa el correo (también spam): llega un código tipo UUID

Guárdalo. No lo subas a GitHub ni lo pegues en el código.

## 2. Corre hoy mismo en tu computador

Necesitas Python 3.10 o superior (viene en macOS y en Ubuntu).

```bash
export MERCADO_PUBLICO_TICKET='pega-aqui-tu-ticket'
python3 -m crl_ofertas --salida reportes
```

Se generan:

- `reportes/ofertas-hoy.html` — ábrelo en el navegador
- `reportes/ofertas-hoy.json` — para Excel u otras herramientas
- `reportes/ofertas-AAAA-MM-DD.csv` — planilla del día

Solo grano, sin coffee break:

```bash
python3 -m crl_ofertas --solo-productos
```

Enviar el HTML por correo (si tienes SMTP):

```bash
python3 -m crl_ofertas --email tu@correo.cl \
  --smtp-host smtp.gmail.com --smtp-user tu@gmail.com --smtp-password 'app-password'
```

## 3. Que corra solo todas las mañanas

### En GitHub (recomendado)

1. En el repositorio: **Settings → Secrets and variables → Actions**
2. Crea el secreto `MERCADO_PUBLICO_TICKET` con tu ticket
3. El flujo `.github/workflows/ofertas-diarias.yml` corre cada día a las 08:00 hora de Chile y deja el reporte en `reportes/`

También puedes lanzarlo a mano: pestaña **Actions → Ofertas diarias CRL Coffee → Run workflow**.

### En tu Mac o PC (cron)

```cron
0 8 * * * cd /ruta/del/repo && MERCADO_PUBLICO_TICKET=tu-ticket python3 -m crl_ofertas --salida reportes
```

## Cómo cotizar después

1. Abre el HTML del día
2. Copia el **código** (ej. `635-450-COT26` o `2697-35-LE26`)
3. Búscalo en [Mercado Público](https://www.mercadopublico.cl) e ingresa con tu usuario de proveedor
4. En Compra Ágil el plazo suele ser de 24–48 horas: conviene revisar el reporte en la mañana

CRL Coffee ya ofrece venta mayorista a cafeterías, oficinas y gastronomía. Las fichas que piden **grano arábica / especialidad / tostado** son las que más se parecen a tu catálogo (Brasil Fazenda Furnas, Colombia La Reserva, Etiopía Limu, etc.).

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

Fuente de los datos: Dirección ChileCompra / Mercado Público. El ticket tiene un tope diario de consultas; este programa reutiliza búsquedas y solo pide el detalle de las fichas que ya parecen de café.
