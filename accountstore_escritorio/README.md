# AccountStore Escritorio

Sistema de escritorio para gestionar la venta de perfiles de plataformas de streaming
(clientes, cuentas con capacidad de perfiles, vencimientos, renovaciones, bajas y pagos).
Hecho en **Python + Tkinter + SQLite**, con usuarios y roles.

- 📄 [Informe del proyecto](docs/INFORME.md): problema, diseño, base de datos, seguridad y planificación.
- 🎬 [Guion del demo](docs/GUION_DEMO.md): pasos de la presentación y preparación para la defensa.

## Requisitos

- **Python 3.10 o superior.** En Windows, el instalador de python.org ya incluye Tkinter y SQLite
  (dejar marcada la opción *tcl/tk and IDLE*).
- No hay que instalar librerías externas: solo se usa la biblioteca estándar.

## Cómo ejecutar

```bash
cd accountstore_escritorio
python main.py
```

La primera vez se crea `accountstore.db` con datos de ejemplo. Para volver a empezar de cero,
borrar ese archivo.

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2026!` | Administrador |
| `supervisor` | `Super2026!` | Supervisor |
| `cobranza` | `Cobra2026!` | Pagos y vencimientos |

## Herramientas para la defensa

```bash
python -m unittest -v              # 39 pruebas automáticas
python inspeccionar_bd.py          # muestra las tablas (por ejemplo: python inspeccionar_bd.py usuarios)
python demo_restricciones.py       # SQL inválido directo a la base: SQLite lo rechaza
```

## Estructura

```
main.py          arranque
interfaz/        pantallas Tkinter (sin SQL)
logica/          reglas de negocio, validaciones, permisos y hash de contraseñas
datos/           conexión, esquema SQL y todas las consultas (parametrizadas)
pruebas/         pruebas con unittest
docs/            informe, guion y capturas
```
