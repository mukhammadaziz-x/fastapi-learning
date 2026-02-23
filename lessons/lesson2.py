from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

@app.get('/news/feed/')
async def news_feed(search: Annotated[str | None, Query(max_length=50, min_length=5)] = None):
    return {'news': ['News1', 'News2', 'News3'], 'search_key': search}