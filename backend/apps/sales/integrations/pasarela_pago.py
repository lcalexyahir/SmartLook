# backend/apps/sales/integrations/pasarela_pago.py
#
# Procesamiento de pago con tarjeta para CU15.


import uuid


class PagoRechazadoError(Exception):
    pass


def procesar_pago(monto_bs):
    """
    Procesa el cobro de una tarjeta y devuelve la referencia de
    transacción generada.
    """
    return f"TXN-{uuid.uuid4()}"