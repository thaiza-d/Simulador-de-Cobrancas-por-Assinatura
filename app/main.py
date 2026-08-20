from fastapi import FastAPI
from .routes.auth import auth_router
from .routes.cobrancas import router
from .dependencies import scheduler
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

scheduler.start()

app.include_router(auth_router)
app.include_router(router)