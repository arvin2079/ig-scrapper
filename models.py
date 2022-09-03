from pydantic import BaseModel


class InstagramUser(BaseModel):
    username: str
    password: str

class HashtagSearch(BaseModel):
    hashtag: str
    credpath: str