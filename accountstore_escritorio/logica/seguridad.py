"""Hash de contraseñas con PBKDF2-HMAC-SHA256 y sal aleatoria.

- La contraseña NUNCA se guarda: se guarda su hash (un resumen que no se
  puede revertir para obtener la contraseña).
- La sal es un valor aleatorio distinto para cada usuario: si dos usuarios
  tienen la misma contraseña, sus hashes igual son diferentes.
- PBKDF2 repite el cálculo muchas veces (ITERACIONES) para que probar
  millones de contraseñas por fuerza bruta sea muy lento.
"""
import hashlib
import hmac
import secrets

ALGORITMO = "sha256"
# Valor recomendado por OWASP para PBKDF2-HMAC-SHA256.
# Si se cambia, las contraseñas ya guardadas dejan de coincidir.
ITERACIONES = 600_000


def generar_hash(clave, sal_hex=None):
    """Devuelve (hash, sal) en hexadecimal. Si no se da una sal, crea una nueva."""
    if sal_hex is None:
        sal_hex = secrets.token_hex(16)          # 16 bytes aleatorios = 128 bits
    hash_bytes = hashlib.pbkdf2_hmac(ALGORITMO, clave.encode("utf-8"),
                                     bytes.fromhex(sal_hex), ITERACIONES)
    return hash_bytes.hex(), sal_hex


def verificar_clave(clave, hash_guardado, sal_hex):
    """Calcula el hash de la clave ingresada con la MISMA sal y lo compara."""
    hash_calculado, _ = generar_hash(clave, sal_hex)
    # compare_digest compara en tiempo constante (no revela cuántos caracteres coinciden).
    return hmac.compare_digest(hash_calculado, hash_guardado)
