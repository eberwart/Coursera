const MULTIPLICADORES = [2, 3, 4, 5, 6, 7];

const RANGOS = {
  persona: { min: 1_000_000, max: 27_000_000 },
  empresa: { min: 50_000_000, max: 99_999_999 },
  cualquiera: { min: 1_000_000, max: 99_999_999 },
};

export function calcularDv(cuerpo) {
  const texto = String(cuerpo).trim();
  if (!/^\d+$/.test(texto) || Number(texto) <= 0) {
    throw new Error("El cuerpo del RUT debe ser un entero positivo.");
  }

  let suma = 0;
  let multiplicador = 0;
  for (const digito of [...texto].reverse()) {
    suma += Number(digito) * MULTIPLICADORES[multiplicador];
    multiplicador = (multiplicador + 1) % MULTIPLICADORES.length;
  }

  const resto = 11 - (suma % 11);
  if (resto === 11) return "0";
  if (resto === 10) return "K";
  return String(resto);
}

export function limpiarRut(valor) {
  return String(valor).replace(/[^0-9kK]/g, "").toUpperCase();
}

export function formatearRut(cuerpo, dv, conPuntos = true) {
  const numero = conPuntos
    ? Number(cuerpo).toLocaleString("es-CL")
    : String(Number(cuerpo));
  return `${numero}-${dv}`;
}

export function validarRut(valor) {
  const limpio = limpiarRut(valor);
  if (limpio.length < 2) return false;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  try {
    return calcularDv(cuerpo) === dv;
  } catch {
    return false;
  }
}

export function generarRut(tipo = "cualquiera") {
  const rango = RANGOS[tipo] ?? RANGOS.cualquiera;
  const cuerpo = aleatorioEntero(rango.min, rango.max);
  const dv = calcularDv(cuerpo);
  return { cuerpo, dv };
}

export function generarRuts(cantidad = 1, tipo = "cualquiera") {
  const n = Math.max(1, Number(cantidad) || 1);
  return Array.from({ length: n }, () => generarRut(tipo));
}

function aleatorioEntero(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
