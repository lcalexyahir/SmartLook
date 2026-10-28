"""Configura las 4 empresas (tenants) de SmartLook en Santa Cruz.

Uso:
    python manage.py seed_tenants
    python manage.py seed_tenants --password OtraClave123

Estado final que deja el comando:
    LOOK FASHION: los datos reales que ya existían (antes empresa "smartlook"):
        sucursales Ventura, Centro y Plan 3000, solo poleras, historial de
        ventas, órdenes y reservas, y sus usuarios.
    MODA ANDINA:  copia de las sucursales, catálogo (poleras) y stock de
        LOOK FASHION, sin historial de ventas.
    URBAN SNAKE:  una sucursal en Plan 3000 y catálogo vacío.
    YAHLEX:       una sucursal en Plan 3000, catálogo vacío, rodrigo y los
        cajeros que ya existían.
    CLIENTES:     globales a la plataforma (sin empresa): pueden comprar y
        reservar en cualquier empresa.

Es idempotente: se puede ejecutar varias veces (por ejemplo en local y
luego en Neon) y siempre converge al mismo estado. Todo corre en una sola
transacción: si algo falla, no se aplica ningún cambio.
"""
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import ProtectedError, RestrictedError, Sum

from apps.catalog.models import (
    Categoria,
    Ciudad,
    Coleccion,
    Marca,
    Pais,
    Producto,
    ProductoProveedor,
    ProductoVariante,
    Proveedor,
    Sucursal,
    Temporada,
)
from apps.inventory.models import InventoryMovement, StockItem
from apps.reservations.models import FittingReservation
from apps.sales.models import Cart, Devolucion, Order, PosSale
from apps.users_auth.models import Cliente, Empresa, Rol, Usuario, UsuarioRol

SLUG_ANTERIOR = "smartlook"  # empresa por defecto creada por la migración 0005

# slug -> (nombre, dominio de correo)
EMPRESAS = {
    "look-fashion": ("LOOK FASHION", "lookfashion.com"),
    "moda-andina": ("MODA ANDINA", "modaandina.com"),
    "urban-snake": ("URBAN SNAKE", "urbansnake.com"),
    "yahlex": ("YAHLEX", "yahlex.com"),
}

CIUDAD = "Santa Cruz de la Sierra"
PLAN_3000 = {
    "direccion": "Plan 3000, Santa Cruz",
    "latitud": Decimal("-17.821700"),
    "longitud": Decimal("-63.128600"),
}

# Sucursales originales de LOOK FASHION: nombre anterior -> nombre nuevo.
SUCURSALES_RENOMBRAR = {
    "SmartLook Ventura Mall": "LOOK FASHION Ventura",
    "SmartLook Centro": "LOOK FASHION Centro",
    "SmartLook La Paz": "LOOK FASHION Plan 3000",
}

# Personal existente que pasa a YAHLEX: correo -> zona de su sucursal
# (None = sin sucursal, como el administrador).
PERSONAL_YAHLEX = {
    "rodrigo@gmail.com": None,
    "diegol@gmail.com": "Plan 3000",
    "diegom@gmail.com": "Plan 3000",
}

ROLES_PERSONAL = ["SUPER_ADMIN", "ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO", "REPARTIDOR"]

# Usuarios de prueba: (correo, correo anterior, nombres, rol, empresa, sucursal).
# "sucursal" es la zona dentro de la empresa (None = sin sucursal). Los
# clientes no llevan empresa (None) porque son globales.
USUARIOS = [
    ("admin@lookfashion.com", "admin@urban-style.test", "Admin", "ADMIN_EMPRESA", "look-fashion", None),
    ("encargado@lookfashion.com", "encargado@urban-style.test", "Encargado", "ENCARGADO_SUCURSAL", "look-fashion", "Ventura"),
    ("cajero@lookfashion.com", "cajero@urban-style.test", "Cajero", "CAJERO", "look-fashion", "Ventura"),
    ("cliente@lookfashion.com", "cliente@urban-style.test", "Cliente", "CLIENTE", None, None),
    ("admin@modaandina.com", "admin@moda-andina.test", "Admin", "ADMIN_EMPRESA", "moda-andina", None),
    ("encargado@modaandina.com", "encargado@moda-andina.test", "Encargado", "ENCARGADO_SUCURSAL", "moda-andina", "Ventura"),
    ("cajero@modaandina.com", "cajero@moda-andina.test", "Cajero", "CAJERO", "moda-andina", "Ventura"),
    ("cliente@modaandina.com", "cliente@moda-andina.test", "Cliente", "CLIENTE", None, None),
    ("admin@urbansnake.com", None, "Admin", "ADMIN_EMPRESA", "urban-snake", None),
    ("admin@yahlex.com", None, "Admin", "ADMIN_EMPRESA", "yahlex", None),
]

# Datos de prueba de la primera versión de este comando (se eliminan).
SLUGS_PRUEBA = ["moda-andina", "urban-style"]
TEXTO_PRODUCTO_PRUEBA = "producto de prueba de"
SUCURSALES_PRUEBA = [
    "Moda Andina - Centro",
    "Moda Andina - Equipetrol",
    "Urban Style - La Paz",
    "Urban Style - Cochabamba",
]
CATEGORIAS_PRUEBA = ["Poleras", "Pantalones", "Chaquetas", "Hoodies", "Joggers", "Gorras"]
MARCAS_PRUEBA = ["Andina Wear", "Urban Street"]
TEMPORADAS_PRUEBA = ["Primavera-Verano 2026"]
PROVEEDORES_PRUEBA = ["Textiles del Oriente S.R.L.", "Confecciones Altiplano S.A."]


class Command(BaseCommand):
    """Comando que deja las 4 empresas de SmartLook configuradas en Santa Cruz."""

    help = "Configura LOOK FASHION, MODA ANDINA, URBAN SNAKE y YAHLEX (multitenant)."

    def add_arguments(self, parser):
        """Define la contraseña de los usuarios de prueba."""
        parser.add_argument(
            "--password",
            default="Admin12345",
            help="Contraseña de los usuarios de prueba (por defecto Admin12345).",
        )

    def handle(self, *args, **options):
        """Ejecuta todos los pasos dentro de una única transacción."""
        password = options["password"]
        with transaction.atomic():
            empresas = self._preparar_empresas()
            self._asignar_huerfanos(empresas["look-fashion"])
            self._limpiar_datos_de_prueba()
            self._ordenar_look_fashion(empresas["look-fashion"])
            self._copiar_empresa(empresas["look-fashion"], empresas["moda-andina"])
            for slug in ("urban-snake", "yahlex"):
                self._asegurar_sucursal_plan_3000(empresas[slug])
            self._asegurar_usuarios(empresas, password)
            self._mover_personal_a_yahlex(empresas["yahlex"])
            self._liberar_clientes()
            self._eliminar_empresa_prueba("urban-style")
            self._asignar_responsables(empresas)
        self._imprimir_resumen(password)

    # ------------------------------------------------------------------
    # Empresas y sucursales
    # ------------------------------------------------------------------

    def _preparar_empresas(self):
        """Crea o renombra las 4 empresas y devuelve un diccionario slug -> Empresa."""
        anterior = Empresa.objects.filter(slug=SLUG_ANTERIOR).first()
        if anterior and not Empresa.objects.filter(slug="look-fashion").exists():
            anterior.slug = "look-fashion"
            anterior.save(update_fields=["slug"])
            self._log("Empresa 'smartlook' convertida en LOOK FASHION.")

        empresas = {}
        for slug, (nombre, dominio) in EMPRESAS.items():
            empresa, _ = Empresa.objects.get_or_create(
                slug=slug, defaults={"nombre": nombre, "estado": "ACTIVA"}
            )
            empresa.nombre = nombre
            empresa.correo_contacto = f"admin@{dominio}"
            empresa.estado = "ACTIVA"
            empresa.save(update_fields=["nombre", "correo_contacto", "estado"])
            empresas[slug] = empresa
        return empresas

    def _asignar_huerfanos(self, empresa):
        """Asigna a la empresa los registros que quedaron sin empresa.

        Hasta el paso 2 las vistas no asignan empresa al crear registros, así
        que lo creado desde web/móvil en ese tiempo pertenece a la empresa
        original (LOOK FASHION). SUPER_ADMIN y clientes no se tocan.
        """
        modelos = [
            Sucursal, Categoria, Marca, Temporada, Coleccion, Producto, Proveedor,
            StockItem, InventoryMovement, FittingReservation, Order, PosSale,
            Devolucion, Cart,
        ]
        for modelo in modelos:
            modelo.objects.filter(id_empresa__isnull=True).update(id_empresa=empresa)
        # Personal sin empresa (los clientes y el SUPER_ADMIN no llevan empresa).
        Usuario.objects.filter(
            id_empresa__isnull=True,
            roles__nombre__in=["ADMIN_EMPRESA", "ENCARGADO_SUCURSAL", "CAJERO", "REPARTIDOR"],
        ).update(id_empresa=empresa)

    def _ciudad_santa_cruz(self):
        """Devuelve la ciudad de Santa Cruz (catálogo global), creándola si falta."""
        ciudad = Ciudad.objects.filter(nombre__iexact=CIUDAD).first()
        if ciudad is None:
            pais, _ = Pais.objects.get_or_create(nombre="Bolivia")
            ciudad = Ciudad.objects.create(id_pais=pais, nombre=CIUDAD)
        return ciudad

    def _asegurar_sucursal_plan_3000(self, empresa):
        """Garantiza que la empresa tenga su sucursal '<EMPRESA> Plan 3000'."""
        referencia = Sucursal.objects.filter(nombre="LOOK FASHION Plan 3000").first()
        _sucursal, creada = Sucursal.objects.get_or_create(
            id_empresa=empresa,
            nombre=f"{empresa.nombre} Plan 3000",
            defaults={
                "id_ciudad": self._ciudad_santa_cruz(),
                "estado": "ACTIVA",
                "dias_atencion": referencia.dias_atencion if referencia else None,
                "horario_atencion": referencia.horario_atencion if referencia else None,
                **PLAN_3000,
            },
        )
        if creada:
            self._log(f"Sucursal '{empresa.nombre} Plan 3000' creada.")

    # ------------------------------------------------------------------
    # Limpieza de los datos de prueba de la versión anterior
    # ------------------------------------------------------------------

    def _limpiar_datos_de_prueba(self):
        """Elimina productos, sucursales y catálogo de prueba creados antes."""
        empresas_prueba = Empresa.objects.filter(slug__in=SLUGS_PRUEBA)
        productos = Producto.objects.filter(
            id_empresa__in=empresas_prueba,
            descripcion__contains=TEXTO_PRODUCTO_PRUEBA,
        )
        cantidad = productos.count()
        if cantidad:
            productos.delete()
            self._log(f"{cantidad} productos de prueba eliminados.")

        sucursales = Sucursal.objects.filter(
            id_empresa__in=empresas_prueba, nombre__in=SUCURSALES_PRUEBA
        )
        cantidad = sucursales.count()
        if cantidad:
            StockItem.objects.filter(id_sucursal__in=sucursales).delete()
            InventoryMovement.objects.filter(id_sucursal__in=sucursales).delete()
            sucursales.delete()
            self._log(f"{cantidad} sucursales de prueba eliminadas.")

        filtro = {"id_empresa__in": empresas_prueba, "producto__isnull": True}
        Categoria.objects.filter(nombre__in=CATEGORIAS_PRUEBA, **filtro).delete()
        Marca.objects.filter(nombre__in=MARCAS_PRUEBA, **filtro).delete()
        Temporada.objects.filter(nombre__in=TEMPORADAS_PRUEBA, **filtro).delete()
        # La tabla producto_proveedor no tiene columna "id" (su clave es
        # id_producto + id_proveedor), así que no se usa en JOINs del ORM:
        # solo se leen sus ids de proveedor.
        con_productos = ProductoProveedor.objects.values_list("id_proveedor_id", flat=True)
        Proveedor.objects.filter(
            id_empresa__in=empresas_prueba,
            nombre_empresa__in=PROVEEDORES_PRUEBA,
        ).exclude(id_proveedor__in=con_productos).delete()

    def _eliminar_empresa_prueba(self, slug):
        """Elimina una empresa de prueba si ya no tiene datos asociados."""
        empresa = Empresa.objects.filter(slug=slug).first()
        if empresa is None:
            return
        try:
            empresa.delete()
            self._log(f"Empresa de prueba '{slug}' eliminada.")
        except (ProtectedError, RestrictedError):
            self._log(f"AVISO: la empresa '{slug}' aún tiene datos; no se eliminó.")

    # ------------------------------------------------------------------
    # LOOK FASHION: sucursales y solo poleras
    # ------------------------------------------------------------------

    def _ordenar_look_fashion(self, empresa):
        """Renombra las sucursales originales y deja el catálogo solo con poleras."""
        for anterior, nuevo in SUCURSALES_RENOMBRAR.items():
            sucursal = Sucursal.objects.filter(id_empresa=empresa, nombre=anterior).first()
            if sucursal is None:
                continue
            sucursal.nombre = nuevo
            if nuevo.endswith("Plan 3000"):
                sucursal.id_ciudad = self._ciudad_santa_cruz()
                for campo, valor in PLAN_3000.items():
                    setattr(sucursal, campo, valor)
            sucursal.save()
            self._log(f"Sucursal '{anterior}' renombrada a '{nuevo}'.")

        self._eliminar_productos_que_no_son_poleras(empresa)

    def _eliminar_productos_que_no_son_poleras(self, empresa):
        """Borra los productos que no son poleras y limpia ventas que quedan vacías."""
        productos = Producto.objects.filter(id_empresa=empresa).exclude(
            tipo_prenda__icontains="polera"
        )
        if not productos.exists():
            return

        variantes = ProductoVariante.objects.filter(id_producto__in=productos)
        ids_ordenes = set(
            Order.objects.filter(orderitem__id_variante__in=variantes)
            .values_list("id_orden", flat=True)
        )
        ids_ventas = set(
            PosSale.objects.filter(items__id_variante__in=variantes)
            .values_list("id_venta", flat=True)
        )
        ids_reservas = set(
            FittingReservation.objects.filter(items__id_variante__in=variantes)
            .values_list("id_reserva", flat=True)
        )
        ids_categorias = set(productos.values_list("id_categoria_id", flat=True))
        nombres = list(productos.values_list("nombre", flat=True))

        # Borra productos con sus variantes, stock, movimientos y detalles.
        productos.delete()
        self._log(f"Productos eliminados (no son poleras): {', '.join(nombres)}.")

        # Órdenes: se borran las que quedaron sin prendas y se recalcula el
        # total del resto (total = subtotal de prendas + costo de envío).
        for orden in Order.objects.filter(id_orden__in=ids_ordenes):
            subtotal = orden.orderitem_set.aggregate(s=Sum("subtotal"))["s"]
            if subtotal is None:
                orden.delete()
            else:
                orden.total = subtotal + orden.costo_envio
                orden.save(update_fields=["total"])

        # Ventas POS: mismo criterio (total = suma de subtotales).
        for venta in PosSale.objects.filter(id_venta__in=ids_ventas):
            subtotal = venta.items.aggregate(s=Sum("subtotal"))["s"]
            if subtotal is None:
                venta.delete()
            else:
                venta.total = subtotal
                venta.save(update_fields=["total"])

        FittingReservation.objects.filter(
            id_reserva__in=ids_reservas, items__isnull=True
        ).delete()
        Devolucion.objects.filter(id_empresa=empresa, items__isnull=True).delete()
        Categoria.objects.filter(
            id_categoria__in=ids_categorias, producto__isnull=True
        ).delete()

    # ------------------------------------------------------------------
    # Copia de LOOK FASHION a MODA ANDINA
    # ------------------------------------------------------------------

    @staticmethod
    def _clonar(objeto, **cambios):
        """Inserta una copia del objeto (nueva clave primaria) con los cambios dados."""
        objeto.pk = None
        objeto._state.adding = True
        for campo, valor in cambios.items():
            setattr(objeto, campo, valor)
        objeto.save()
        return objeto

    @staticmethod
    def _copiar_proveedores_de_producto(id_producto_origen, producto_copia, proveedores):
        """Copia los vínculos producto-proveedor de un producto a su copia.

        La tabla producto_proveedor no tiene columna "id" (su clave es
        id_producto + id_proveedor), por eso se inserta con SQL directo en
        lugar de save(), que intentaría devolver ese "id" inexistente.
        """
        enlaces = ProductoProveedor.objects.filter(
            id_producto_id=id_producto_origen
        ).values_list("id_proveedor_id", "codigo_proveedor", "costo_compra", "estado")
        with connection.cursor() as cursor:
            for id_proveedor, codigo, costo, estado in enlaces:
                if id_proveedor not in proveedores:
                    continue
                cursor.execute(
                    "INSERT INTO producto_proveedor "
                    "(id_producto, id_proveedor, codigo_proveedor, costo_compra, "
                    "estado, fecha_asignacion) VALUES (%s, %s, %s, %s, %s, NOW())",
                    [
                        producto_copia.id_producto,
                        proveedores[id_proveedor].id_proveedor,
                        codigo,
                        costo,
                        estado,
                    ],
                )

    def _copiar_empresa(self, origen, destino):
        """Copia sucursales, catálogo y stock de origen a destino (solo si destino está vacío)."""
        tiene_datos = (
            Sucursal.objects.filter(id_empresa=destino).exists()
            or Producto.objects.filter(id_empresa=destino).exists()
        )
        if tiene_datos:
            return

        sucursales = {}
        for sucursal in Sucursal.objects.filter(id_empresa=origen).order_by("id_sucursal"):
            anterior = sucursal.pk
            nombre = sucursal.nombre.replace(origen.nombre, destino.nombre)
            sucursales[anterior] = self._clonar(sucursal, id_empresa=destino, nombre=nombre)

        def copiar_tabla(modelo):
            """Copia todas las filas de un modelo del catálogo y devuelve id viejo -> copia."""
            mapa = {}
            for fila in modelo.objects.filter(id_empresa=origen).order_by("pk"):
                anterior = fila.pk
                mapa[anterior] = self._clonar(fila, id_empresa=destino)
            return mapa

        categorias = copiar_tabla(Categoria)
        marcas = copiar_tabla(Marca)
        temporadas = copiar_tabla(Temporada)
        colecciones = copiar_tabla(Coleccion)
        proveedores = copiar_tabla(Proveedor)

        variantes = {}
        for producto in Producto.objects.filter(id_empresa=origen).order_by("id_producto"):
            id_anterior = producto.pk
            copia = self._clonar(
                producto,
                id_empresa=destino,
                id_categoria=categorias[producto.id_categoria_id],
                id_marca=marcas.get(producto.id_marca_id),
                id_temporada=temporadas.get(producto.id_temporada_id),
                id_coleccion=colecciones.get(producto.id_coleccion_id),
            )
            variantes_origen = ProductoVariante.objects.filter(
                id_producto_id=id_anterior
            ).order_by("id_variante")
            for variante in variantes_origen:
                anterior = variante.pk
                codigo = variante.codigo_producto
                variantes[anterior] = self._clonar(
                    variante,
                    id_producto=copia,
                    codigo_producto=f"MA-{codigo}"[:50] if codigo else None,
                )
            self._copiar_proveedores_de_producto(id_anterior, copia, proveedores)

        for stock in StockItem.objects.filter(id_empresa=origen):
            if stock.id_sucursal_id not in sucursales or stock.id_variante_id not in variantes:
                continue
            sucursal = sucursales[stock.id_sucursal_id]
            variante = variantes[stock.id_variante_id]
            self._clonar(stock, id_empresa=destino, id_sucursal=sucursal, id_variante=variante)
            if stock.cantidad > 0:
                InventoryMovement.objects.create(
                    id_empresa=destino,
                    id_sucursal=sucursal,
                    id_variante=variante,
                    tipo_movimiento="ENTRADA",
                    cantidad=stock.cantidad,
                    motivo=f"Stock inicial copiado de {origen.nombre}",
                )

        self._log(
            f"{destino.nombre}: copiadas {len(sucursales)} sucursales, "
            f"{Producto.objects.filter(id_empresa=destino).count()} productos y su stock."
        )

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------

    def _asegurar_usuarios(self, empresas, password):
        """Crea o actualiza los usuarios de prueba de cada empresa."""
        for correo, correo_anterior, nombres, rol_nombre, slug, zona in USUARIOS:
            empresa = empresas[slug] if slug else None
            sucursal = None
            if empresa and zona:
                sucursal = Sucursal.objects.filter(
                    id_empresa=empresa, nombre=f"{empresa.nombre} {zona}"
                ).first()

            usuario = Usuario.objects.filter(correo=correo).first()
            if usuario is None and correo_anterior:
                usuario = Usuario.objects.filter(correo=correo_anterior).first()
            if usuario is None:
                usuario = Usuario(correo=correo, estado="ACTIVO")

            usuario.correo = correo
            usuario.nombres = nombres
            usuario.apellidos = empresa.nombre if empresa else "Prueba"
            usuario.password_hash = make_password(password)
            usuario.estado = "ACTIVO"
            usuario.id_empresa = empresa
            usuario.id_sucursal = sucursal
            usuario.save()

            rol, _ = Rol.objects.get_or_create(nombre=rol_nombre, defaults={"estado": True})
            UsuarioRol.objects.get_or_create(id_usuario=usuario, id_rol=rol)

            if rol_nombre == "CLIENTE":
                Cliente.objects.get_or_create(id_usuario=usuario)

    def _mover_personal_a_yahlex(self, yahlex):
        """Pasa a rodrigo y a los cajeros existentes a YAHLEX."""
        for correo, zona in PERSONAL_YAHLEX.items():
            usuario = Usuario.objects.filter(correo=correo).first()
            if usuario is None:
                self._log(f"AVISO: no existe el usuario {correo}; se omite.")
                continue
            sucursal = None
            if zona:
                sucursal = Sucursal.objects.filter(
                    id_empresa=yahlex, nombre=f"{yahlex.nombre} {zona}"
                ).first()
            usuario.id_empresa = yahlex
            usuario.id_sucursal = sucursal
            usuario.save(update_fields=["id_empresa", "id_sucursal"])

    def _liberar_clientes(self):
        """Deja sin empresa a los usuarios que solo son clientes (clientes globales)."""
        ids_personal = Usuario.objects.filter(
            roles__nombre__in=ROLES_PERSONAL
        ).values_list("id_usuario", flat=True)
        Usuario.objects.filter(roles__nombre="CLIENTE").exclude(
            id_usuario__in=list(ids_personal)
        ).update(id_empresa=None, id_sucursal=None)

    def _asignar_responsables(self, empresas):
        """Define admin@<dominio> como administrador responsable de cada empresa."""
        for slug, (_nombre, dominio) in EMPRESAS.items():
            admin = Usuario.objects.filter(correo=f"admin@{dominio}").first()
            empresa = empresas[slug]
            if admin and empresa.id_administrador_id != admin.id_usuario:
                empresa.id_administrador = admin
                empresa.save(update_fields=["id_administrador"])

    # ------------------------------------------------------------------
    # Salida
    # ------------------------------------------------------------------

    def _log(self, mensaje):
        """Escribe un mensaje de progreso en consola."""
        self.stdout.write(f"- {mensaje}")

    def _imprimir_resumen(self, password):
        """Muestra el estado final de cada empresa y sus usuarios."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Empresas configuradas:"))
        for slug in EMPRESAS:
            empresa = Empresa.objects.get(slug=slug)
            nombres = Sucursal.objects.filter(id_empresa=empresa).order_by(
                "id_sucursal"
            ).values_list("nombre", flat=True)
            sucursales = ", ".join(nombres) or "-"
            self.stdout.write(
                f"  {empresa.nombre}: sucursales [{sucursales}] | "
                f"productos {empresa.productos.count()} | stock {empresa.stock_items.count()} | "
                f"usuarios {empresa.usuarios.count()}"
            )
        clientes = Usuario.objects.filter(roles__nombre="CLIENTE", id_empresa__isnull=True)
        self.stdout.write(f"  CLIENTES globales: {clientes.count()}")
        self.stdout.write("")
        self.stdout.write(f"Usuarios de prueba (contraseña: {password}):")
        for correo, *_resto in USUARIOS:
            self.stdout.write(f"  {correo}")