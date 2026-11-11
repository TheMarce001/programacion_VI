# Guion del demo (≈ 10 minutos)

Cada paso indica qué **indicador de la rúbrica** cubre. Conviene ensayarlo 2 o 3 veces.

**La noche anterior (en la notebook con la que vas a presentar)**
- Copiar el proyecto y ejecutar `python main.py` una vez, para comprobar que abre. Ejecutar también
  `python -m unittest -v`: tienen que pasar las 32 pruebas.
- Llevar una copia de respaldo (pendrive y GitHub) por si falla la notebook.
- Recorrer este guion completo al menos una vez, en voz alta y con el reloj.

**Justo antes de presentar**
- Borrar `accountstore.db` para empezar con los datos de ejemplo limpios (se crea sola al abrir).
- Tener dos terminales abiertas en la carpeta `accountstore_escritorio`, el informe abierto y
  `datos/esquema.sql`, `logica/gestor.py` y `datos/repositorio.py` abiertos en el editor.
- Cerrar otros programas y notificaciones (WhatsApp, correo) para que no aparezcan durante el demo.
- Usuarios: `admin / Admin2026!` · `supervisor / Super2026!` · `cobranza / Cobra2026!`
- Hacer **primero los datos inválidos y después el caso correcto**: así se ve que la lista no cambió.

---

## Parte 1 — Problema y diseño (2 min) · indicadores 1.1 a 2.3

Con el [INFORME](INFORME.md) abierto:
1. Problema real: AccountStore hoy usa una planilla. Sus dificultades son la sobreventa, que no hay
   relaciones reales, los datos inconsistentes y que cualquiera puede modificar todo (§1.1).
2. Usuarios y necesidades (§1.2), objetivo general (§1.3), módulos incluidos y excluidos (§1.4).
3. Pantallas y navegación (§2.1), modelo de datos (§2.2) y la regla de negocio **RN1: capacidad
   de la cuenta** (§2.3).

## Parte 2 — Sesión y seguridad (1,5 min) · indicadores 5.2 y 4.1

4. `python main.py` → intentar `admin` con una clave equivocada → *"Usuario o contraseña incorrectos"*.
5. Ingresar como `admin / Admin2026!`. Mostrar el nombre y el rol en el menú lateral.
6. En la otra terminal: `python inspeccionar_bd.py usuarios` → se ve `clave_hash` y `clave_sal`, **no
   la contraseña**. Explicar PBKDF2 + sal + 600 000 iteraciones (`logica/seguridad.py`).

## Parte 3 — Proceso principal (3 min) · indicadores 3.1 a 3.4

7. **Cuentas y servicios:** `netflix01` está **LLENA (5 de 5)** y `netflix02` tiene 5 libres.
8. **Suscripciones → Nueva venta:**
   - Cliente **Jorge Villalba**, servicio **Netflix**. El sistema propone `netflix02` porque tiene lugar.
   - Perfiles **2**, meses **3**. Mostrar que calcula el vencimiento y **Gs. 180.000** (RN2, RN4).
9. **Dato inválido primero** (3.4):
   - Cambiar la cuenta a **netflix01** y guardar → *"La cuenta … está llena (5 de 5)"* (RN1).
   - Volver a netflix02, poner meses **15** y guardar → *"La cantidad de meses debe estar entre 1 y 12"*.
   - Fecha **31/02/2026** → *"La fecha … no es válida"*.
   - Cerrar el diálogo y mostrar que la lista **no cambió**: no se guardó nada.
10. Repetir la venta con datos correctos → **Guardar venta** → mensaje con vencimiento y monto (3.1).
11. La venta aparece seleccionada en la lista, leída de la base (3.3). La tarjeta **Cobrado en el
    mes** sube en Gs. 180.000. Doble clic → **Historial de pagos** (pago VENTA registrado por el
    usuario). En **Cuentas y servicios**, netflix02 ahora tiene 3 libres.
12. Filtro **Vencidas** → aparece *Diego Ramírez* → **Renovar** 1 mes → renueva **desde hoy**
    (RN5, 3.2).

## Parte 4 — Base de datos (2 min) · indicadores 4.1 a 4.4

13. Abrir `datos/esquema.sql`: PK `id` en cada tabla y FK con `REFERENCES … ON DELETE RESTRICT`.
    Mencionar `PRAGMA foreign_keys = ON` en `datos/conexion.py` (4.1).
14. **Clientes → eliminar a Ana Gómez** → rechazado porque tiene suscripciones (FK).
    **Nuevo cliente** con el teléfono `0981 111 222` → rechazado porque ya existe (UNIQUE) (4.2).
15. En la terminal: `python demo_restricciones.py` → 7 intentos de SQL directo, **todos rechazados** por
    SQLite (4.2).
16. **Cerrar el programa** (botón X). Volver a abrir con `python main.py`, ingresar y mostrar que la
    venta de Jorge Villalba sigue ahí (4.3).
17. Explicar el `INSERT` (`repositorio.insertar_venta`) y el `SELECT` (`repositorio.listar_suscripciones`)
    con el §4.4 del informe (4.4).

## Parte 5 — Código y permisos (1,5 min) · indicadores 5.1, 5.3 y 5.4

18. Mostrar las carpetas `interfaz/`, `logica/` y `datos/`. La interfaz no tiene SQL y todo el SQL
    está en `repositorio.py` (5.1).
19. **Cerrar sesión** → ingresar como `cobranza / Cobra2026!` → seleccionar a Ana Gómez → **Dar de baja**
    → *"Su rol «Pagos y vencimientos» no tiene permiso para dar de baja suscripciones"*. Mostrar
    `logica/permisos.py` y que `gestor.dar_de_baja` llama a `exigir_permiso` (5.3).
20. Mostrar una consulta con `?` y `ejecutar_seguro` en `interfaz/comun.py`, que evita cierres
    inesperados (5.4).

## Parte 6 — IA, estado y planificación (1 min) · indicadores 6.3, 7.1 y 7.2

21. Uso de IA y cómo lo verifiqué: `python -m unittest -v` → **32 pruebas OK** (§6).
22. Funcionalidades terminadas, parciales y pendientes, y plan con fechas (§7).

---

## Preparación para la defensa individual (indicadores 6.1 y 6.2)

El docente elegirá un fragmento de código y pedirá una **modificación breve sin IA**. Hay que practicar
estas antes, a mano, y comprobar cada una ejecutando el programa y `python -m unittest`:

| Posible pedido | Dónde se cambia |
|---|---|
| "A VENCER" con 5 días en lugar de 3 | `logica/reglas.py` → `DIAS_AVISO = 5` (luego ajustar `test_estado_por_dias`) |
| Ventas de hasta 6 meses | `logica/reglas.py` → `MESES_MAXIMOS = 6` |
| Que "Pagos y vencimientos" sí pueda dar de baja | `logica/permisos.py` → agregar `"dar_de_baja"` al conjunto de `COBRANZA` |
| Cambiar un mensaje de error | `logica/reglas.py` o `logica/gestor.py`, en el texto del `ErrorValidacion` |
| Contraseña de al menos 10 caracteres | `logica/reglas.py` → `validar_clave_nueva`: `if len(clave) < 10` |
| Mostrar el monto total en el historial | ya existe en `interfaz/suscripciones.py` → `VentanaHistorial` (`sum(...)`) |
| Agregar una columna a la lista | `interfaz/suscripciones.py` → `COLUMNAS` y la tupla de valores en `actualizar()` |
| Nuevo servicio con otra capacidad | desde la sección **Cuentas y servicios**, o en `logica/datos_ejemplo.py` |
| Precio = precio × perfiles × meses con 10 % de descuento desde 6 meses | `logica/reglas.py` → `calcular_monto` |

**Preguntas probables:**
- ¿Por qué el hash lleva sal? → Para que dos contraseñas iguales tengan hashes distintos y no sirvan
  las tablas de hashes precalculados.
- ¿Qué pasa si falla el segundo `INSERT` de la venta? → `with self.conexion:` hace `ROLLBACK` y no
  queda la suscripción sin su pago.
- ¿Por qué el estado no se guarda en la base? → Depende de la fecha de hoy. Si se guardara, quedaría
  desactualizado al día siguiente.
- ¿Para qué sirve `PRAGMA foreign_keys = ON`? → Sin él, SQLite no controla las claves foráneas.
- ¿Qué diferencia hay entre validar en la lógica y en la base? → La lógica da mensajes claros. La base
  es la última barrera, aunque alguien escriba SQL a mano (`demo_restricciones.py`).
- ¿Por qué `?` y no f-strings? → Para evitar la inyección SQL. El dato nunca se interpreta como código SQL.
