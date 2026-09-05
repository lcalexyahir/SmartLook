import json
from common.utils import log_audit


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                body = json.loads(request.body) if request.body else {}
                log_audit(
                    usuario=request.user,
                    accion=request.method,
                    tabla_afectada=request.path,
                    registro_id=None,
                    descripcion=f"{request.method} {request.path}",
                    datos_nuevo=body,
                )
            except Exception:
                pass

        return response