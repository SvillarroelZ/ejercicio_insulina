import re

INPUT_FILE = "preproinsulin-seq.txt"
OUTPUT_FILE = "preproinsulin-seq-clean.txt"

def clean_preproinsulin(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    """Limpia la preproinsulina eliminando ORIGIN, números, //, espacios y saltos de línea."""

    # Leer archivo original
    with open(input_file, "r") as f:
        data = f.read()

    # 1. Eliminar explícitamente las palabras ORIGIN y //
    data = data.replace("ORIGIN", "")
    data = data.replace("//", "")

    # 2. Eliminar números, espacios, tabs y saltos de línea
    data = re.sub(r"[0-9\s]", "", data)

    # 3. Dejar SOLO letras, en minúscula
    clean_seq = re.sub(r"[^a-zA-Z]", "", data).lower()

    # Guardar archivo limpio
    with open(output_file, "w") as f:
        f.write(clean_seq)

    # Verificación
    print(f"Archivo limpio creado: {output_file}")
    print(f"Longitud final: {len(clean_seq)} caracteres")

    if len(clean_seq) == 110:
        print("Longitud correcta: 110 aminoácidos.")
    else:
        print("ADVERTENCIA: la longitud NO es 110. Revisa el archivo original.")

    return clean_seq


if __name__ == "__main__":
    clean_preproinsulin()