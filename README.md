# Generador de RUT chileno

Genera y valida RUTs de Chile cuyo **dígito verificador** cumple el algoritmo módulo 11.

Los números son sintéticos: sirven para pruebas y desarrollo, no identifican personas ni empresas reales.

## Uso en el navegador

Abre [`web/index.html`](web/index.html) en el navegador (no necesita servidor). Desde ahí puedes:

- generar uno o varios RUTs
- elegir rango de persona natural o empresa
- copiar los resultados
- validar un RUT escrito a mano

## Uso en la terminal

```bash
python3 src/rut.py
python3 src/rut.py -n 10 --tipo persona
python3 src/rut.py --validar 12.345.678-5
```

También puedes importar el módulo:

```python
from src.rut import generar_rut, validar_rut, calcular_dv

rut = generar_rut()
print(rut)                 # 12.345.678-5
print(validar_rut(str(rut)))
print(calcular_dv(12345678))  # 5
```

## Algoritmo del dígito verificador

1. Recorrer el cuerpo del RUT de derecha a izquierda.
2. Multiplicar cada dígito por la serie `2, 3, 4, 5, 6, 7` (y repetir).
3. Sumar los productos y calcular `11 - (suma % 11)`.
4. Si el resultado es `11`, el dígito es `0`. Si es `10`, el dígito es `K`. En otro caso, es el número obtenido.

## Pruebas

```bash
python3 -m unittest tests.test_rut
node --experimental-vm-modules web/test-rut.mjs
```
