from fastapi import FastAPI

app = FastAPI()

@app.get('/news/feed/')
async def news_feed(search: str):
    return {'news': ['News1', 'News2', 'News3'], 'search_key': search}