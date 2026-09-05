#!/usr/bin/env python3
"""Genera HTML interactivo + ZIP + CSV para poder descargar/usar la planilla sin GitHub."""

import base64
import csv
import math
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XLSX = ROOT / "factibilidad-cuartos-tostado-club.xlsx"
LOGO = ROOT / "logo-coffee-roasting-labs.png"
HTML = ROOT / "factibilidad-cuartos-tostado-club.html"
ZIPP = ROOT / "factibilidad-cuartos-tostado-club.zip"
CSV = ROOT / "factibilidad-cuartos-tostado-club.csv"

xlsx_b64 = base64.b64encode(XLSX.read_bytes()).decode("ascii")
logo_b64 = base64.b64encode(LOGO.read_bytes()).decode("ascii")


def clp(n):
    n = int(round(n))
    neg = n < 0
    s = f"{abs(n):,}".replace(",", ".")
    return ("-" if neg else "") + "$" + s


# Números del caso base (para el CSV estático)
kg, merma, peso, merma_emp = 1000, 0.18, 250, 0.02
iva, verde, maquila, bolsa, etiq, venta = 0.19, 9990, 1500, 300, 80, 6000
kgt = kg * (1 - merma)
cu = int(kgt / (peso / 1000))
bol = math.ceil(cu * (1 + merma_emp))
costos = {
    "verde": kg * verde,
    "maquila": kg * maquila,
    "bolsas": bol * bolsa,
    "etiq": bol * etiq,
}
ct = sum(costos.values())
vn = cu * venta
ut = vn - ct

rows_csv = [
    ["Coffee Roasting Labs — Factibilidad cuartos Tostado Club"],
    ["Todos los precios son NETOS (sin IVA). IVA 19%."],
    [],
    ["PARAMETROS"],
    ["Kg café verde", 1000],
    ["Merma tostado", "18%"],
    ["Peso cuarto (g)", 250],
    ["Precio verde $/kg", 9990],
    ["Maquila $/kg (sobre verde)", 1500],
    ["Bolsa $/un", 300],
    ["Etiqueta $/un", 80],
    ["Venta cuarto $/un", 6000],
    [],
    ["CONVERSION"],
    ["Kg tostados", kgt],
    ["Cuartos", cu],
    ["Bolsas a comprar", bol],
    [],
    ["COSTOS NETOS DEL LOTE"],
    ["Café verde", costos["verde"]],
    ["Maquila", costos["maquila"]],
    ["Bolsas", costos["bolsas"]],
    ["Etiquetas", costos["etiq"]],
    ["TOTAL COSTO", ct],
    ["Venta neta", vn],
    ["Utilidad neta", ut],
    ["Margen", f"{ut/vn:.1%}"],
    ["Costo por cuarto", round(ct / cu, 2)],
    ["Caja a desembolsar c/IVA", round(ct * 1.19)],
    [],
    ["ESCENARIOS PRECIO VERDE"],
    ["Precio verde $/kg", "Costo lote", "Utilidad lote", "Margen", "Costo/cuarto"],
]
resto = ct - costos["verde"]
for p in (9000, 9500, 9990, 10000, 10500):
    tot = p * kg + resto
    u = vn - tot
    rows_csv.append([p, tot, u, f"{u/vn:.1%}", round(tot / cu, 2)])

with CSV.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerows(rows_csv)

with zipfile.ZipFile(ZIPP, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(XLSX, XLSX.name)
    z.write(CSV, CSV.name)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Factibilidad cuartos Tostado Club — Coffee Roasting Labs</title>
<style>
  :root {{
    --cafe: #3c2415;
    --cafe2: #6b3f2a;
    --dorado: #c4a35a;
    --crema: #fbf6f0;
    --crema2: #f3ede3;
    --input: #fff3cd;
    --verde: #1f7a4d;
    --verdeb: #d8f3e2;
    --rojo: #9b2335;
    --rojob: #f8d7da;
    --texto: #1a1a1a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    background: var(--crema);
    color: var(--texto);
    font-size: 15px;
    line-height: 1.45;
  }}
  header {{
    background: var(--cafe);
    color: #fff;
    padding: 20px 24px 18px;
    border-bottom: 4px solid var(--dorado);
  }}
  header .wrap {{ max-width: 1100px; margin: 0 auto; display: flex; gap: 18px; align-items: center; }}
  header img {{ width: 88px; height: 88px; border-radius: 8px; background: #000; }}
  header h1 {{ margin: 0 0 4px; font-size: 22px; }}
  header p {{ margin: 0; color: #f3ede3; font-size: 13px; }}
  .bar {{
    background: var(--dorado);
    color: var(--cafe);
    padding: 10px 24px;
    font-weight: 600;
    font-size: 14px;
  }}
  .bar .wrap {{ max-width: 1100px; margin: 0 auto; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
  .btn {{
    display: inline-block;
    background: var(--cafe);
    color: #fff;
    text-decoration: none;
    padding: 10px 16px;
    border-radius: 6px;
    border: 0;
    font-weight: 700;
    cursor: pointer;
    font-size: 14px;
  }}
  .btn.gold {{ background: var(--cafe2); }}
  .btn:hover {{ opacity: 0.92; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 20px 16px 48px; }}
  h2 {{
    font-size: 16px;
    color: #fff;
    background: var(--cafe2);
    padding: 8px 12px;
    margin: 22px 0 10px;
    border-radius: 4px;
  }}
  .grid {{ display: grid; grid-template-columns: 1fr 160px; gap: 6px 12px; align-items: center; }}
  @media (min-width: 720px) {{
    .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  }}
  label {{ font-size: 13px; color: var(--cafe); }}
  input, select {{
    background: var(--input);
    border: 2px solid var(--dorado);
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 15px;
    font-weight: 700;
    color: var(--cafe);
    width: 100%;
    text-align: right;
    font-family: inherit;
  }}
  .note {{ font-size: 12px; color: #5c534a; margin: 8px 0 0; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 12px 0; }}
  .kpi {{
    background: #fff;
    border: 1px solid #d4c4b0;
    border-radius: 8px;
    padding: 12px;
  }}
  .kpi .t {{ font-size: 12px; color: var(--cafe2); }}
  .kpi .v {{ font-size: 22px; font-weight: 800; color: var(--cafe); margin-top: 4px; }}
  .veredicto {{
    padding: 18px;
    border-radius: 8px;
    text-align: center;
    font-size: 28px;
    font-weight: 800;
    margin: 12px 0;
    border: 2px solid var(--dorado);
  }}
  .ok {{ background: var(--verdeb); color: var(--verde); }}
  .no {{ background: var(--rojob); color: var(--rojo); }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    font-size: 13px;
  }}
  th, td {{
    border: 1px solid #d4c4b0;
    padding: 7px 8px;
    text-align: right;
  }}
  th {{ background: var(--cafe); color: #fff; font-weight: 600; text-align: center; }}
  td:first-child, th:first-child {{ text-align: left; }}
  tr.total {{ background: var(--cafe); color: #fff; font-weight: 700; }}
  tr.total td {{ color: #fff; border-color: #6b3f2a; }}
  tr.hi {{ background: var(--verdeb); font-weight: 700; }}
  .si {{ color: var(--verde); font-weight: 800; }}
  .nope {{ color: var(--rojo); font-weight: 800; }}
  footer {{ max-width: 1100px; margin: 0 auto; padding: 8px 16px 32px; font-size: 12px; color: #5c534a; }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <img src="data:image/png;base64,{logo_b64}" alt="Coffee Roasting Labs" />
    <div>
      <h1>Factibilidad — cuartos para Tostado Club</h1>
      <p>Tostaduría Erik Berwart Araya EIRL · Coffee Roasting Labs · RUT 77.586.349-8<br>
      Lote de 1 tonelada de café verde · precios netos (IVA 19% aparte)</p>
    </div>
  </div>
</header>
<div class="bar">
  <div class="wrap">
    <a class="btn" id="dl-xlsx" download="factibilidad-cuartos-tostado-club.xlsx">⬇ Descargar Excel (.xlsx)</a>
    <button class="btn gold" type="button" id="dl-csv">⬇ Descargar CSV (Excel Chile)</button>
    <span>Si GitHub no deja bajar el .xlsx, usa estos botones. Cambia las celdas amarillas y se recalcula.</span>
  </div>
</div>
<main>
  <div id="veredicto" class="veredicto ok">FACTIBLE</div>
  <p id="veredicto-txt" class="note" style="text-align:center;margin-top:-6px"></p>

  <div class="kpis">
    <div class="kpi"><div class="t">Cuartos producidos</div><div class="v" id="k-cuartos">—</div></div>
    <div class="kpi"><div class="t">Kg tostados</div><div class="v" id="k-kgt">—</div></div>
    <div class="kpi"><div class="t">Costo por cuarto</div><div class="v" id="k-cc">—</div></div>
    <div class="kpi"><div class="t">Utilidad por cuarto</div><div class="v" id="k-uc">—</div></div>
    <div class="kpi"><div class="t">Utilidad neta del lote</div><div class="v" id="k-ut">—</div></div>
    <div class="kpi"><div class="t">Margen neto</div><div class="v" id="k-mg">—</div></div>
    <div class="kpi"><div class="t">Caja a desembolsar (c/IVA)</div><div class="v" id="k-caja">—</div></div>
    <div class="kpi"><div class="t">Verde máximo para no perder</div><div class="v" id="k-vmax">—</div></div>
  </div>

  <div class="cols">
    <div>
      <h2>1. Volumen y proceso</h2>
      <div class="grid">
        <label>Kg café verde a comprar</label><input id="kgVerde" type="number" value="1000">
        <label>Merma de tostado (%)</label><input id="mermaTostado" type="number" value="18" step="0.1">
        <label>Peso del cuarto (g)</label><input id="pesoCuarto" type="number" value="250">
        <label>Merma de empaque extra (%)</label><input id="mermaEmpaque" type="number" value="2" step="0.1">
      </div>
      <h2>2. Precios netos (sin IVA)</h2>
      <div class="grid">
        <label>IVA (%)</label><input id="iva" type="number" value="19" step="0.1">
        <label>Café verde caso base ($/kg)</label><input id="precioVerde" type="number" value="9990">
        <label>Maquila ($/kg)</label><input id="maquila" type="number" value="1500">
        <label>Maquila se cobra sobre</label>
        <select id="maquilaSobre"><option>Verde</option><option>Tostado</option></select>
        <label>Bolsa 250 g ($/un)</label><input id="precioBolsa" type="number" value="300">
        <label>Etiqueta ($/un)</label><input id="precioEtiq" type="number" value="80">
        <label>Venta al cliente por cuarto ($)</label><input id="precioVenta" type="number" value="6000">
      </div>
    </div>
    <div>
      <h2>3. Costos opcionales del lote</h2>
      <div class="grid">
        <label>Flete / logística ($ lote)</label><input id="flete" type="number" value="0">
        <label>Mano de obra empaque ($/cuarto)</label><input id="mo" type="number" value="0">
        <label>Otros ($ lote)</label><input id="otros" type="number" value="0">
        <label>Margen mínimo aceptable (%)</label><input id="margenObj" type="number" value="25" step="0.5">
      </div>
      <p class="note">Bolsas: supuesto $300 neto (Funsmart ≈ $286, Cafestore ≈ $700). Pon 0 si las pone Tostado Club. Lo mismo para etiquetas.</p>
      <h2>4. Escenarios precio verde ($/kg neto)</h2>
      <div class="grid">
        <label>A</label><input id="escA" type="number" value="9000">
        <label>B</label><input id="escB" type="number" value="9500">
        <label>C (base)</label><input id="escC" type="number" value="9990">
        <label>D</label><input id="escD" type="number" value="10000">
        <label>E</label><input id="escE" type="number" value="10500">
      </div>
    </div>
  </div>

  <h2>Lote — estado de resultados (caso base)</h2>
  <table id="tbl-lote">
    <thead><tr><th>Ítem</th><th>Base</th><th>Costo neto</th><th>% costo</th><th>Por cuarto</th><th>Con IVA</th></tr></thead>
    <tbody></tbody>
  </table>

  <h2>Escenarios de precio del café verde</h2>
  <table id="tbl-esc">
    <thead></thead>
    <tbody></tbody>
  </table>
</main>
<footer>
  Documento interno Coffee Roasting Labs. No es una cotización al cliente.
  El botón Excel descarga la planilla original con fórmulas. Si cambias números aquí, usa el CSV.
</footer>
<script>
const XLSX_B64 = "{xlsx_b64}";
function b64ToBlob(b64, mime) {{
  const bin = atob(b64);
  const len = bin.length;
  const arr = new Uint8Array(len);
  for (let i = 0; i < len; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], {{ type: mime }});
}}
document.getElementById("dl-xlsx").href = URL.createObjectURL(
  b64ToBlob(XLSX_B64, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
);

function n(id) {{
  const v = parseFloat(document.getElementById(id).value);
  return Number.isFinite(v) ? v : 0;
}}
function clp(x) {{
  const n = Math.round(x);
  return (n < 0 ? "-" : "") + "$" + Math.abs(n).toLocaleString("es-CL");
}}
function clpd(x) {{
  return (x < 0 ? "-" : "") + "$" + Math.abs(x).toLocaleString("es-CL", {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
}}
function pct(x) {{ return (x * 100).toLocaleString("es-CL", {{ maximumFractionDigits: 1 }}) + "%"; }}
function num(x, d=0) {{ return x.toLocaleString("es-CL", {{ maximumFractionDigits: d, minimumFractionDigits: d }}); }}

function loteDe(precioVerde, p) {{
  const costoVerde = p.kgVerde * precioVerde;
  const costoMaquila = p.kgMaquila * p.maquila;
  const costoBolsas = p.bolsas * p.precioBolsa;
  const costoEtiq = p.bolsas * p.precioEtiq;
  const costoMO = p.cuartos * p.mo;
  const costoTotal = costoVerde + costoMaquila + costoBolsas + costoEtiq + costoMO + p.flete + p.otros;
  const venta = p.cuartos * p.precioVenta;
  const utilidad = venta - costoTotal;
  const margen = venta === 0 ? 0 : utilidad / venta;
  return {{
    costoVerde, costoMaquila, costoBolsas, costoEtiq, costoMO,
    costoTotal, venta, utilidad, margen,
    costoCuarto: p.cuartos === 0 ? 0 : costoTotal / p.cuartos,
    costoKgTostado: p.kgTostado === 0 ? 0 : costoTotal / p.kgTostado,
    utilidadCuarto: p.precioVenta - (p.cuartos === 0 ? 0 : costoTotal / p.cuartos),
    cajaSalida: costoTotal * (1 + p.iva),
    cajaEntrada: venta * (1 + p.iva),
    ivaPagar: (venta - costoTotal) * p.iva,
    flujo: (venta - costoTotal) * (1 + p.iva),
    factible: margen >= p.margenObj,
    resto: costoTotal - costoVerde
  }};
}}

function params() {{
  const kgVerde = n("kgVerde");
  const merma = n("mermaTostado") / 100;
  const pesoG = n("pesoCuarto");
  const mermaEmp = n("mermaEmpaque") / 100;
  const kgTostado = kgVerde * (1 - merma);
  const kgPorCuarto = pesoG / 1000;
  const cuartos = kgPorCuarto === 0 ? 0 : Math.floor(kgTostado / kgPorCuarto);
  const sobranteG = (kgTostado - cuartos * kgPorCuarto) * 1000;
  const bolsas = Math.ceil(cuartos * (1 + mermaEmp));
  const maquilaSobre = document.getElementById("maquilaSobre").value;
  const kgMaquila = maquilaSobre === "Tostado" ? kgTostado : kgVerde;
  return {{
    kgVerde, merma, pesoG, mermaEmp, kgTostado, kgPorCuarto, cuartos, sobranteG, bolsas, kgMaquila,
    iva: n("iva") / 100,
    precioVerde: n("precioVerde"),
    maquila: n("maquila"),
    precioBolsa: n("precioBolsa"),
    precioEtiq: n("precioEtiq"),
    precioVenta: n("precioVenta"),
    flete: n("flete"),
    mo: n("mo"),
    otros: n("otros"),
    margenObj: n("margenObj") / 100,
    esc: [n("escA"), n("escB"), n("escC"), n("escD"), n("escE")]
  }};
}}

function calc() {{
  const p = params();
  const b = loteDe(p.precioVerde, p);
  const vmax = p.kgVerde === 0 ? 0 : (b.venta - b.resto) / p.kgVerde;

  const ok = b.factible;
  const v = document.getElementById("veredicto");
  v.textContent = ok ? "FACTIBLE" : "REVISAR";
  v.className = "veredicto " + (ok ? "ok" : "no");
  document.getElementById("veredicto-txt").textContent = ok
    ? "El margen neto supera el mínimo de " + pct(p.margenObj) + " definido abajo."
    : "El margen queda bajo el mínimo de " + pct(p.margenObj) + ". Sube precio, baja verde/maquila o empaque.";

  document.getElementById("k-cuartos").textContent = num(p.cuartos);
  document.getElementById("k-kgt").textContent = num(p.kgTostado, 1) + " kg";
  document.getElementById("k-cc").textContent = clp(b.costoCuarto);
  document.getElementById("k-uc").textContent = clp(b.utilidadCuarto);
  document.getElementById("k-ut").textContent = clp(b.utilidad);
  document.getElementById("k-mg").textContent = pct(b.margen);
  document.getElementById("k-caja").textContent = clp(b.cajaSalida);
  document.getElementById("k-vmax").textContent = clp(vmax) + "/kg";

  const items = [
    ["Café verde", num(p.kgVerde) + " kg", b.costoVerde],
    ["Maquila (tostado)", num(p.kgMaquila, 1) + " kg", b.costoMaquila],
    ["Bolsas", num(p.bolsas) + " un", b.costoBolsas],
    ["Etiquetas", num(p.bolsas) + " un", b.costoEtiq],
    ["Mano de obra empaque", num(p.cuartos) + " un", p.cuartos * p.mo],
    ["Flete / logística", "1 lote", p.flete],
    ["Otros", "1 lote", p.otros],
  ];
  let body = items.map(([n, base, c]) =>
    `<tr><td>${{n}}</td><td>${{base}}</td><td>${{clp(c)}}</td><td>${{pct(b.costoTotal ? c/b.costoTotal : 0)}}</td><td>${{clp(p.cuartos ? c/p.cuartos : 0)}}</td><td>${{clp(c*(1+p.iva))}}</td></tr>`
  ).join("");
  body += `<tr class="total"><td>TOTAL COSTO LOTE</td><td></td><td>${{clp(b.costoTotal)}}</td><td>100%</td><td>${{clp(b.costoCuarto)}}</td><td>${{clp(b.cajaSalida)}}</td></tr>`;
  body += `<tr class="hi"><td>Venta neta / utilidad</td><td>${{num(p.cuartos)}} cuartos</td><td>${{clp(b.venta)}}</td><td>${{pct(b.margen)}}</td><td>${{clp(b.utilidadCuarto)}}</td><td>${{clp(b.cajaEntrada)}}</td></tr>`;
  document.querySelector("#tbl-lote tbody").innerHTML = body;

  const labels = ["A","B","C base","D","E"];
  let head = "<tr><th>Indicador</th>" + labels.map(l => `<th>${{l}}</th>`).join("") + "</tr>";
  const rows = [
    ["Precio verde $/kg", p.esc.map(clp)],
    ["Costo total lote", p.esc.map(pr => clp(loteDe(pr, p).costoTotal))],
    ["Costo por cuarto", p.esc.map(pr => clp(loteDe(pr, p).costoCuarto))],
    ["Utilidad neta lote", p.esc.map(pr => clp(loteDe(pr, p).utilidad))],
    ["Margen neto", p.esc.map(pr => pct(loteDe(pr, p).margen))],
    ["¿Cumple margen objetivo?", p.esc.map(pr => loteDe(pr, p).factible
      ? '<span class="si">SÍ</span>' : '<span class="nope">NO</span>')],
    ["Caja a desembolsar c/IVA", p.esc.map(pr => clp(loteDe(pr, p).cajaSalida))],
  ];
  document.querySelector("#tbl-esc thead").innerHTML = head;
  document.querySelector("#tbl-esc tbody").innerHTML = rows.map(r =>
    "<tr><td>" + r[0] + "</td>" + r[1].map(c => "<td>"+c+"</td>").join("") + "</tr>"
  ).join("");
}}

function downloadCsv() {{
  const p = params();
  const b = loteDe(p.precioVerde, p);
  const lines = [
    ["Indicador", "Valor"],
    ["Kg verde", p.kgVerde],
    ["Merma tostado", p.merma],
    ["Cuartos", p.cuartos],
    ["Kg tostados", p.kgTostado],
    ["Costo lote neto", Math.round(b.costoTotal)],
    ["Venta neta", Math.round(b.venta)],
    ["Utilidad neta", Math.round(b.utilidad)],
    ["Margen", b.margen],
    ["Costo por cuarto", Math.round(b.costoCuarto)],
    ["Caja c/IVA", Math.round(b.cajaSalida)],
    [],
    ["Escenario verde", "Utilidad", "Margen", "Costo/cuarto"],
    ...p.esc.map(pr => {{
      const x = loteDe(pr, p);
      return [pr, Math.round(x.utilidad), x.margen, Math.round(x.costoCuarto)];
    }})
  ];
  const csv = "\\uFEFF" + lines.map(r => r.join(";")).join("\\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], {{ type: "text/csv;charset=utf-8" }}));
  a.download = "factibilidad-cuartos-tostado-club.csv";
  a.click();
}}

document.getElementById("dl-csv").addEventListener("click", downloadCsv);
document.querySelectorAll("input, select").forEach(el => el.addEventListener("input", calc));
calc();
</script>
</body>
</html>
"""

HTML.write_text(html, encoding="utf-8")
print("HTML", HTML, "bytes", HTML.stat().st_size)
print("ZIP", ZIPP, "bytes", ZIPP.stat().st_size)
print("CSV", CSV, "bytes", CSV.stat().st_size)
