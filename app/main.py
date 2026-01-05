from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.schema import schema
from app.database import engine, Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Database Initialization
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup():
    await init_models()

# Mount GraphQL - Apply Rate Limiting here
# Limit: 5 requests per minute per IP
graphql_app = GraphQLRouter(schema, context_getter=lambda request=None: {"request": request})

@app.post("/graphql")
@limiter.limit("10/minute") # Strict rate limiting for demo
async def handle_graphql(request: Request, response: Response):
    return await graphql_app.handle_request(request=request)

@app.get("/")
async def root():
    return {"message": "Financial Data Microservice Running"}