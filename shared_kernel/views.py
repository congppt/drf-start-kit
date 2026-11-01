from django.http import JsonResponse
from django.urls import path

from .health import all_readiness_checks, probe_response, run_checks


def liveness(_request):
    return JsonResponse({"success": True})


def readiness(_request):
    checks = run_checks(all_readiness_checks())
    return probe_response(checks)
