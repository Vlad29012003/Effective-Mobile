import json

from loguru import logger


class LoggingMiddleware:
    SENSITIVE_FIELDS = {
        "password",
        "token",
        "csrfmiddlewaretoken",
        "secret",
        "authorization",
        "refresh",
        "access",
    }
    SENSITIVE_HEADERS = {"authorization", "cookie"}
    IGNORE_PATHS = {
        "/health/": True,
        "/api/v1/schema/": True,
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logger

    def __call__(self, request):
        if self.IGNORE_PATHS.get(request.path, False):
            return self.get_response(request)

        self.log_request(request)

        response = self.get_response(request)

        self.log_response(request, response)

        return response

    def log_request(self, request):
        user_info = self.get_user_info(request)

        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.content_type

            if "application/json" in content_type:
                try:
                    request_data = json.loads(request.body.decode("utf-8") if request.body else {})
                except Exception as e:
                    request_data = f"Unable to decode JSON body: {str(e)}"
            else:
                try:
                    request_data = request.POST.dict()
                except Exception:
                    raw = request.body.decode("utf-8") if request.body else ""
                    request_data = dict(x.split("=") for x in raw.split("&") if "=" in x)
        else:
            request_data = dict(request.GET)

        scrubbed_data = self.scrub(request_data)
        scrubbed_headers = self.scrub_headers(request.headers)

        self.logger.debug(
            "Before processing request: {method} {full_path}",
            method=request.method,
            full_path=request.get_full_path(),
        )
        self.logger.debug("User info: {user_info}", user_info=user_info)
        self.logger.debug("Request headers: {headers}", headers=scrubbed_headers)
        self.logger.debug("Request data: {data}", data=scrubbed_data)

    def log_response(self, request, response):
        user_info = self.get_user_info(request)
        content_type = response.get("Content-Type", "")

        self.logger.debug(
            "After processing request: {method} {full_path}",
            method=request.method,
            full_path=request.get_full_path(),
        )
        self.logger.debug("User info: {user_info}", user_info=user_info)
        self.logger.debug("Response status: {status_code}", status_code=response.status_code)

        if "text/html" in content_type or "javascript" in content_type:
            self.logger.debug(
                "Response is {content_type}, skipping body logging.",
                content_type=content_type,
            )
            return

        try:
            raw_content = response.content.decode("utf-8")
            if "application/json" in content_type:
                data = json.loads(raw_content)
                response_data = self.scrub(data)
            else:
                response_data = raw_content[:1000]
        except Exception as e:
            response_data = f"Unable to decode response body: {str(e)}"

        self.logger.debug("Response data: {response_data}", response_data=response_data)

    def get_user_info(self, request):
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
            return f"User ID: {user_id}: {request.user.username}"
        else:
            return "Anonymous user"

    def scrub(self, obj):
        """
        Recursively masks sensitive fields in dicts and lists.
        """
        if isinstance(obj, dict):
            scrubbed = {}
            for k, v in obj.items():
                key_lower = k.lower()
                # Mask if key contains any sensitive substring
                if any(s in key_lower for s in self.SENSITIVE_FIELDS):
                    scrubbed[k] = "[FILTERED]"
                else:
                    scrubbed[k] = self.scrub(v)
            return scrubbed
        if isinstance(obj, list):
            return [self.scrub(v) for v in obj]
        return obj

    def scrub_headers(self, headers):
        """
        Masks sensitive headers.
        """
        scrubbed = {}
        for k, v in headers.items():
            key_lower = k.lower()
            if key_lower in self.SENSITIVE_HEADERS:
                scrubbed[k] = "[FILTERED]"
            else:
                scrubbed[k] = v
        return scrubbed
