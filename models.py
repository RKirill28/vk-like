from pydantic import BaseModel, Field


class PostModel(BaseModel):
    item_id: int = Field(alias='id')
    track_code: str
    type: str
    owner_id: int


class PostsResponseModel(BaseModel):
    count: int
    items: list[PostModel]
    next_from: int


class ErrorModel(BaseModel):
    error_code: int
    error_msg: str
    redirect_uri: str = ""


class ErrorResponseModel(BaseModel):
    error: ErrorModel


class CaptchaResponseModel(BaseModel):
    status: str


class CheckCaptchaResponseModel(BaseModel):
    status: str
    success_token: str


class AddLikeModel(BaseModel):
    type: str
    owner_id: int
    item_id: int
    track_code: str
