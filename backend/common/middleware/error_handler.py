from django.http import JsonResponse


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        return JsonResponse(
            {
                "error": True,
                "message": str(exception),
                "path": request.path,
            },
            status=500,
        )