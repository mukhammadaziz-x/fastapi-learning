from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

# feed_query = Query(max_length=50, min_length=5, pattern="[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+") # pattern yordamida emailni to'g'ri kiritish qoidasi ko'rsatilgan.
# @app.get('/news/feed/')
# async def news_feed(search: Annotated[str | None, feed_query] = None):
#     return {'news': ['News1', 'News2', 'News3'], 'search_key': search}

feed_query = Query(max_length=50, min_length=5)
@app.get('/news/feed/')
async def news_feed(search: Annotated[str | None, feed_query] = "all"):
    return {'news': ['News1', 'News2', 'News3'], 'search_key': search}