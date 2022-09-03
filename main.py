from fastapi import FastAPI, status, HTTPException

from models import (
    InstagramUser,
    HashtagSearch
)
from instabot import (
    authenticate_username_password,
    hashtag_search
)


app = FastAPI()

@app.post("/insta-auth", status_code=status.HTTP_201_CREATED)
def instagram_auth(user: InstagramUser):
    creds_addr = authenticate_username_password(user.username, user.password)
    if creds_addr == None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='unforeseen exception!')
    return {'details': creds_addr}


@app.post("/scrap-hashtag")
def scrap_hashtag(hashtagsearch: HashtagSearch):
    try:
        medias = hashtag_search(hashtagsearch.credpath, hashtagsearch.hashtag)
    except:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='hashtag search failed!')
    return {'medias': medias}
