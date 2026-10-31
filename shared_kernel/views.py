from django.http import JsonResponse
from django.urls import path

from .health import app_readiness_checks, core_readiness_checks, probe_response, run_checks


def liveness(_request):
    return JsonResponse({"success": True})


def readiness(_request):
    checks = run_checks({**core_readiness_checks(), **app_readiness_checks()})
    return probe_response(checks)



