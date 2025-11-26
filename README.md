# Peso molecular de Insulina en Python

Este repositorio contiene varios scripts en Python que trabajan con la secuencia de la **preproinsulina humana** para:

- Limpiar una secuencia obtenida en formato tipo FASTA/GenBank.
- Dividir la preproinsulina en sus cadenas biológicas (A, B, C y péptido señal).
- Calcular el peso molecular aproximado de la insulina madura.
- Calcular el carga neta de la insulina a distintos valores de pH.

---

## Scripts incluidos

- `cleaner.py`: limpia la secuencia de preproinsulina obtenida en formato de anotación, dejando solo la cadena continua de aminoácidos.
- `split-insulin.py`: divide la preproinsulina en sus cuatro partes biológicas: péptido señal, cadena B, cadena A y péptido conector C.
- `string-insulin.py`: calcula el peso molecular aproximado de la insulina madura a partir de su secuencia.
- `net-charge.py`: calcula la carga neta de la insulina entre pH 0 y 14.

---

## Requisitos

- Python 3.6 o superior (idealmente **Python 3.10**).

---

## Descripción de archivos

---

### 1. `cleaner.py`

Este script procesa una secuencia de preproinsulina en formato similar a GenBank, por ejemplo:

ORIGIN
1 malwmrllpl lallalwgpd paaafvnqhl cgshlvealy lvcgergffy tpktrreaed
61 lqvgqvelgg gpgagslqpl alegslqkrg iveqcctsic slyqlenycn
//

Su función es limpiar la cadena eliminando:

- La palabra `ORIGIN`
- Números de posición (1, 61, etc.)
- Espacios en blanco
- El cierre `//`

Dejando como resultado únicamente la secuencia continua.

Esta secuencia limpia se usa en los demás scripts.

---

### 2. `split-insulin.py`

Este script toma la cadena limpia de preproinsulina y la divide en sus cuatro componentes biológicos:

| Parte | Secuencia |
|-------|-----------|
| **lsInsulin** (péptido señal) | `malwmrllpllallalwgpdpaaa` |
| **cInsulin** (péptido conector C) | `rreaedlqvgqvelgggpgagslqplalegslqkr` |
| **bInsulin** (cadena B) | `fvnqhlcgshlvealylvcgergffytpkt` |
| **aInsulin** (cadena A) | `giveqcctsicslyqlenycn` |

Esto permite construir luego la insulina madura, que está compuesta por la cadena A y B.

---

### 3. `string-insulin.py`

Este script:

1. Define la secuencia de preproinsulina.
2. Define las partes: péptido señal, cadena B, cadena A y C-peptide.
3. Construye la insulina madura concatenando `bInsulin + aInsulin`.
4. Imprime:
   - La secuencia completa de la preproinsulina.
   - La secuencia de la cadena A.
5. Define un diccionario `aaWeights` con el peso molecular promedio de cada aminoácido.
6. Cuenta cuántas veces aparece cada aminoácido en la insulina.
7. Calcula el peso molecular aproximado como: peso total = Σ (cantidad AA) * (peso AA)
8. Compara con el valor de referencia: 5807.63
9. Muestra el porcentaje de error del cálculo.

---

### 4. `net-charge.py`

Este script calcula la carga neta de la insulina entre pH 0 y 14 usando pKa aproximadas para:

- Extremos N-terminal y C-terminal.
- Cadenas laterales ionizables (Lys, Arg, Asp, Glu, His, Tyr, Cys).

Pasos del script:

1. Define pKa relevantes.
2. Para cada pH entre 0 y 14:
   - Calcula la fracción protonada/deprotonada de cada grupo.
   - Suma todas las cargas parciales.
3. Imprime una tabla: pH | carga neta

Esto permite estimar el punto isoeléctrico (pI) de la insulina.

---

## Cómo ejecutar los scripts

Desde una terminal:

```bash
python3 cleaner.py
python3 split-insulin.py
python3 string-insulin.py
python3 net-charge.py
