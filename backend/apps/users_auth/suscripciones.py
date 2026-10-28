"""Servicio central de planes y suscripciones (SaaS - paso 5).
Toda verificación de límites y funcionalidades pasa por aquí, para que la
regla viva en un solo lugar del backend:
- límites del plan: sucursales, personal y productos;
- funcionalidades del plan: delivery, vestidor virtual, chatbot de clientes,
  reportes con IA y reporte comparativo entre sucursales;
- operar (crear, editar, eliminar) con la suscripción vencida.
Los errores de plan responden {"detail": "<mensaje>", "codigo": "<código>"}
para que la web y el móvil los reconozcan sin depender del texto:
"plan_no_permitido" (403) y "suscripcion_vencida" (402).
Los pagos de renovación o cambio de plan se cobran con Stripe en modo test
(tarjeta 4242 4242 4242 4242): no hay dinero real.
"""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import BasePermission
from .models import PagoSuscripcion, PlanSuscripcion, Suscripcion
# Tipo de cambio para mostrar los precios en bolivianos (configurable con
# TIPO_CAMBIO_BOB en settings o variable de entorno; por defecto 12).
TIPO_CAMBIO_BOB = Decimal(str(getattr(settings, "TIPO_CAMBIO_BOB", 12)))
FUNCIONES = {
    "delivery": "el delivery a domicilio",
    "vestidor_virtual": "el vestidor virtual",
    "chatbot_clientes": "el chatbot para clientes",
    "reportes_ia": "el asistente y los reportes con IA",
    "comparativo_sucursales": "el reporte comparativo entre sucursales",
    "modo_offline": "el modo sin conexión",
}
LIMITES = {
    "max_sucursales": "sucursales",
    "max_personal": "usuarios del personal",
    "max_productos": "productos",
}
class ErrorDePlan(APIException):
    """Base de los errores de plan: el cuerpo lleva el mensaje y un código fijo."""
    def __init__(self, detail=None, code=None):
        """Arma la respuesta {"detail": mensaje, "codigo": código del error}."""
        mensaje = detail if detail is not None else self.default_detail
        super().__init__({"detail": mensaje, "codigo": self.default_code}, code)
class PlanNoPermitido(ErrorDePlan):
    """La operación no está incluida en el plan o supera su límite."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Tu plan no permite esta operación."
    default_code = "plan_no_permitido"
class SuscripcionVencida(ErrorDePlan):
    """La suscripción de la empresa venció: no puede operar hasta renovar."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "La suscripción de tu empresa venció. Renueva el plan para seguir operando."
    default_code = "suscripcion_vencida"
def en_bolivianos(monto_usd):
    """Convierte un monto en dólares a bolivianos con el tipo de cambio configurado."""
    return (Decimal(monto_usd) * TIPO_CAMBIO_BOB).quantize(Decimal("0.01"), ROUND_HALF_UP)
class SuscripcionService:
    """Reglas de planes y suscripciones de las empresas."""
    # ------------------------------------------------------------ consulta
    @staticmethod
    def de_empresa(empresa):
        """Suscripción de la empresa, o None si no tiene.
        Si su fecha ya pasó, la marca como VENCIDA para que el estado
        guardado coincida con la realidad.
        """
        suscripcion = Suscripcion.objects.select_related("id_plan").filter(
            id_empresa=empresa
        ).first()
        if suscripcion and suscripcion.estado == "ACTIVA" and not suscripcion.vigente:
            suscripcion.estado = "VENCIDA"
            suscripcion.save(update_fields=["estado", "fecha_actualizacion"])
        return suscripcion
    @staticmethod
    def esta_vigente(empresa_id):
        """True si la empresa tiene una suscripción activa y no vencida."""
        return Suscripcion.objects.filter(
            id_empresa_id=empresa_id,
            estado="ACTIVA",
            fecha_vencimiento__gte=timezone.localdate(),
        ).exists()
    @staticmethod
    def verificar_vigente(empresa):
        """Devuelve la suscripción vigente o lanza SuscripcionVencida."""
        suscripcion = SuscripcionService.de_empresa(empresa)
        if suscripcion is None:
            raise SuscripcionVencida(f"{empresa.nombre} no tiene una suscripción activa.")
        if not suscripcion.vigente:
            raise SuscripcionVencida(
                f"La suscripción de {empresa.nombre} venció el "
                f"{suscripcion.fecha_vencimiento:%d/%m/%Y}. Renueva el plan para seguir operando."
            )
        return suscripcion
    # ------------------------------------------------------------ reglas
    @staticmethod
    def verificar_limite(empresa, limite, usados):
        """Lanza PlanNoPermitido si 'usados' ya alcanzó el límite del plan (None = ilimitado)."""
        plan = SuscripcionService.verificar_vigente(empresa).id_plan
        maximo = getattr(plan, limite)
        if maximo is not None and usados >= maximo:
            raise PlanNoPermitido(
                f"Tu plan {plan.nombre} permite hasta {maximo} {LIMITES[limite]} y "
                f"{empresa.nombre} ya tiene {usados}. Cambia a un plan superior para agregar más."
            )
    @staticmethod
    def verificar_limite_sucursales(empresa):
        """Límite de sucursales del plan."""
        from apps.catalog.models import Sucursal
        usadas = Sucursal.objects.filter(id_empresa=empresa).count()
        SuscripcionService.verificar_limite(empresa, "max_sucursales", usadas)
    @staticmethod
    def verificar_limite_personal(empresa):
        """Límite de usuarios del personal (todos los usuarios de la empresa)."""
        from .models import Usuario
        usados = Usuario.objects.filter(id_empresa=empresa).count()
        SuscripcionService.verificar_limite(empresa, "max_personal", usados)
    @staticmethod
    def verificar_limite_productos(empresa):
        """Límite de productos del catálogo de la empresa."""
        from apps.catalog.models import Producto
        usados = Producto.objects.filter(id_empresa=empresa).count()
        SuscripcionService.verificar_limite(empresa, "max_productos", usados)
    @staticmethod
    def verificar_funcion(empresa, funcion):
        """Lanza PlanNoPermitido si el plan de la empresa no incluye la funcionalidad."""
        plan = SuscripcionService.verificar_vigente(empresa).id_plan
        if not getattr(plan, funcion, False):
            raise PlanNoPermitido(
                f"El plan {plan.nombre} de {empresa.nombre} no incluye {FUNCIONES[funcion]}."
            )
    @staticmethod
    def validar_cambio(empresa, plan):
        """Verifica que la empresa quepa en los límites del plan al que quiere pasar."""
        from apps.catalog.models import Producto, Sucursal
        from .models import Usuario
        if not plan.estado:
            raise ValidationError({"id_plan": "Ese plan no está disponible."})
        usados = {
            "max_sucursales": Sucursal.objects.filter(id_empresa=empresa).count(),
            "max_personal": Usuario.objects.filter(id_empresa=empresa).count(),
            "max_productos": Producto.objects.filter(id_empresa=empresa).count(),
        }
        for limite, cantidad in usados.items():
            maximo = getattr(plan, limite)
            if maximo is not None and cantidad > maximo:
                raise PlanNoPermitido(
                    f"{empresa.nombre} tiene {cantidad} {LIMITES[limite]} y el plan "
                    f"{plan.nombre} permite {maximo}. Reduce esa cantidad antes de cambiar de plan."
                )
    # ------------------------------------------------------------ pagos (Stripe test)
    @staticmethod
    def iniciar_pago(empresa, plan, usuario):
        """Crea el PaymentIntent de Stripe (modo test) para pagar un periodo del plan.
        Devuelve (pago, client_secret). El frontend confirma el pago con
        Stripe.js y luego llama a confirmar_pago con la referencia.
        """
        SuscripcionService.validar_cambio(empresa, plan)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(Decimal(plan.precio_usd) * 100),
                currency="usd",
                description=f"SmartLook {plan.nombre} - {empresa.nombre}",
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
        except stripe.error.StripeError as exc:
            raise ValidationError({"error": f"No se pudo iniciar el pago: {exc}"})
        pago = PagoSuscripcion.objects.create(
            id_empresa=empresa,
            id_plan=plan,
            id_usuario=usuario,
            monto_usd=plan.precio_usd,
            monto_bob=en_bolivianos(plan.precio_usd),
            tipo_cambio=TIPO_CAMBIO_BOB,
            referencia_pago=intent.id,
        )
        return pago, intent.client_secret
    @staticmethod
    @transaction.atomic
    def confirmar_pago(empresa, referencia_pago):
        """Verifica el pago en Stripe y aplica el plan pagado a la suscripción.
        - Mismo plan y suscripción vigente: el periodo se suma al vencimiento.
        - Plan distinto o suscripción vencida: el nuevo periodo empieza hoy.
        """
        from apps.sales.integrations.stripe_payment import PagoRechazadoError, verificar_pago
        pago = PagoSuscripcion.objects.select_for_update().select_related("id_plan").filter(
            id_empresa=empresa, referencia_pago=referencia_pago, estado="PENDIENTE"
        ).first()
        if pago is None:
            raise ValidationError({"error": "No hay un pago pendiente con esa referencia."})
        try:
            verificar_pago(referencia_pago)
        except PagoRechazadoError as exc:
            pago.estado = "FALLIDO"
            pago.save(update_fields=["estado"])
            raise ValidationError({"error": f"Pago rechazado: {exc}"})
        plan = pago.id_plan
        SuscripcionService.validar_cambio(empresa, plan)
        hoy = timezone.localdate()
        suscripcion = SuscripcionService.de_empresa(empresa)
        if suscripcion is None:
            suscripcion = Suscripcion(id_empresa=empresa, id_plan=plan, fecha_inicio=hoy)
            suscripcion.fecha_vencimiento = hoy + timedelta(days=plan.dias_periodo)
        elif suscripcion.vigente and suscripcion.id_plan_id == plan.id_plan:
            suscripcion.fecha_vencimiento += timedelta(days=plan.dias_periodo)
        else:
            suscripcion.id_plan = plan
            suscripcion.fecha_inicio = hoy
            suscripcion.fecha_vencimiento = hoy + timedelta(days=plan.dias_periodo)
        suscripcion.estado = "ACTIVA"
        suscripcion.save()
        pago.estado = "PAGADO"
        pago.fecha_pago = timezone.now()
        pago.save(update_fields=["estado", "fecha_pago"])
        return suscripcion, pago
def requiere_funcion(funcion):
    """Crea un permiso DRF que exige que el plan de la empresa incluya 'funcion'.
    El SUPER_ADMIN (operador de la plataforma) no tiene empresa ni plan y
    siempre pasa.
    """
    class PlanIncluyeFuncion(BasePermission):
        """Permiso DRF generado para una funcionalidad del plan."""
        def has_permission(self, request, view):
            """Verifica suscripción vigente y que el plan incluya la funcionalidad."""
            usuario = request.user
            if not getattr(usuario, "is_authenticated", False):
                return False
            if usuario.roles.filter(nombre="SUPER_ADMIN").exists():
                return True
            if usuario.id_empresa_id is None:
                return False
            SuscripcionService.verificar_funcion(usuario.id_empresa, funcion)
            return True
    PlanIncluyeFuncion.__name__ = f"PlanIncluye_{funcion}"
    return PlanIncluyeFuncion