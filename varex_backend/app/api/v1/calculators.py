from fastapi import APIRouter

from app.varex_calculators.api.v1 import (
    httpd,
    ihs,
    iis,
    k8s,
    nginx,
    ohs,
    os_linux,
    podman,
    redis,
    tomcat,
)

router = APIRouter()

router.include_router(nginx.router, prefix="/nginx", tags=["Calculators - NGINX"])
router.include_router(redis.router, prefix="/redis", tags=["Calculators - Redis"])
router.include_router(tomcat.router, prefix="/tomcat", tags=["Calculators - Tomcat"])
router.include_router(httpd.router, prefix="/httpd", tags=["Calculators - HTTPD"])
router.include_router(ohs.router, prefix="/ohs", tags=["Calculators - OHS"])
router.include_router(ihs.router, prefix="/ihs", tags=["Calculators - IHS"])
router.include_router(iis.router, prefix="/iis", tags=["Calculators - IIS"])
router.include_router(podman.router, prefix="/podman", tags=["Calculators - Podman"])
router.include_router(k8s.router, prefix="/k8s", tags=["Calculators - Kubernetes"])
router.include_router(os_linux.router, prefix="/os", tags=["Calculators - Linux OS"])
