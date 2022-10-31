from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import JSONResponse
from routers import user_controller, shop_controller, product_controller, shoppingcart_controller, notify_controller,score_controller,ads_controller,admin_controller
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
from pydantic.error_wrappers import ValidationError
from fastapi_versioning import VersionedFastAPI

app = FastAPI(debug=True)

subapi = FastAPI(debug=True,openapi_tags= [user_controller.tag_meta, shop_controller.tag_meta, product_controller.tag_meta, shoppingcart_controller.tag_meta, notify_controller.tag_meta,
    score_controller.tag_meta,ads_controller.tag_meta,admin_controller.tag_meta])
subapi.include_router(user_controller.router)
subapi.include_router(shop_controller.router)
subapi.include_router(product_controller.router)
subapi.include_router(shoppingcart_controller.router)
subapi.include_router(notify_controller.router)
subapi.include_router(score_controller.router)
subapi.include_router(ads_controller.router)
subapi.include_router(admin_controller.router)

@subapi.exception_handler(ValidationError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )

subapi = VersionedFastAPI(subapi,
    version_format='{major}',
    prefix_format='/v{major}',
    default_version=(1, 0),
    enable_latest=True,)

subapi.add_middleware(
    CORSMiddleware,
    # allow_origin_regex='^https?\:\/\/shopu[\w\W]*.5xcampus.com',
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=360,
)
# app.mount("/"+API_PREFIX,subapi)
app.mount("/",subapi)

class Login(BaseModel):
    username: str
    password: str = None

    @classmethod
    def as_form(cls, username: str = Form(...), password: str = Form(None)):
        return cls(username=username, password=password)

@app.post("/", tags=['Hello'])
async def root(login_data: Login = Depends(Login.as_form)):
    return {"username": login_data.username, "password": login_data.password}
    # return {"message": "Hello World"}


