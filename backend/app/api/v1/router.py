from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, health, jobs,
    sessions, messaging, contacts, templates, broadcasts, autoreplies, apikeys, gateway, wa_webhook,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(jobs.router)

# WhatsApp gateway
api_router.include_router(sessions.router)
api_router.include_router(messaging.router)
api_router.include_router(contacts.router)
api_router.include_router(templates.router)
api_router.include_router(broadcasts.router)
api_router.include_router(autoreplies.router)
api_router.include_router(apikeys.router)
api_router.include_router(gateway.router)
api_router.include_router(wa_webhook.router)
