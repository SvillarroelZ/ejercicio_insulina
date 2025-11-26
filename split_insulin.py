
CLEAN_FILE = "preproinsulin_seq_clean.txt"

def split_insulin(clean_file=CLEAN_FILE):
    """Divide la preproinsulina limpia en los segmentos solicitados."""

    # Leer la secuencia limpia
    with open(clean_file, "r") as f:
        seq = f.read().strip()

    print(f"Longitud recibida: {len(seq)} aminoácidos")

    # Verificar longitud correcta
    if len(seq) != 110:
        print("ERROR: La secuencia NO tiene 110 caracteres. Revisa el archivo limpio.")
        return

    # -----------------------------
    # Cortes según el laboratorio
    # -----------------------------
    ls_seq = seq[0:24]     # aa 1-24 -> 24 aa
    b_seq  = seq[24:54]    # aa 25-54 -> 30 aa
    c_seq  = seq[54:89]    # aa 55-89 -> 35 aa
    a_seq  = seq[89:110]   # aa 90-110 -> 21 aa

    # -----------------------------
    # Guardar en archivos
    # -----------------------------
    with open("lsinsulin_seq_clean.txt", "w") as f:
        f.write(ls_seq)

    with open("binsulin_seq_clean.txt", "w") as f:
        f.write(b_seq)

    with open("cinsulin_seq_clean.txt", "w") as f:
        f.write(c_seq)

    with open("ainsulin_seq_clean.txt", "w") as f:
        f.write(a_seq)

    # -----------------------------
    # Verificación
    # -----------------------------
    print("\nArchivos generados:")
    print(f"lsinsulin_seq_clean.txt -> {len(ls_seq)} caracteres (esperado: 24)")
    print(f"binsulin_seq_clean.txt  -> {len(b_seq)} caracteres (esperado: 30)")
    print(f"cinsulin_seq_clean.txt  -> {len(c_seq)} caracteres (esperado: 35)")
    print(f"ainsulin_seq_clean.txt  -> {len(a_seq)} caracteres (esperado: 21)")


# Ejecutar automáticamente
if __name__ == "__main__":
    split_insulin()