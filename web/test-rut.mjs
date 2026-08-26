import { calcularDv, generarRuts, validarRut } from "./rut.js";

const casos = [
  [11111111, "1"],
  [22222222, "2"],
  [12345678, "5"],
  [1000005, "K"],
  [1000013, "0"],
];

let fallos = 0;
for (const [cuerpo, dv] of casos) {
  const obtenido = calcularDv(cuerpo);
  if (obtenido !== dv) {
    console.error(`DV incorrecto para ${cuerpo}: esperado ${dv}, obtuvo ${obtenido}`);
    fallos += 1;
  }
}

const generados = generarRuts(40, "persona");
for (const rut of generados) {
  const valor = `${rut.cuerpo}-${rut.dv}`;
  if (!validarRut(valor) || calcularDv(rut.cuerpo) !== rut.dv) {
    console.error(`RUT generado inválido: ${valor}`);
    fallos += 1;
  }
}

if (validarRut("11.111.111-2") || !validarRut("11.111.111-1")) {
  console.error("La validación no distingue RUTs válidos de inválidos.");
  fallos += 1;
}

if (fallos) {
  process.exit(1);
}

console.log("ok");
