from fastapi import FastAPI, Query, Path
from typing import Annotated

app = FastAPI()

# feed_query = Query(max_length=50, min_length=5, pattern="[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+") # pattern yordamida emailni to'g'ri kiritish qoidasi ko'rsatilgan.
# @app.get('/news/feed/')
# async def news_feed(search: Annotated[str | None, feed_query] = None):
#     return {'news': ['News1', 'News2', 'News3'], 'search_key': search}

# feed_query = Query(max_length=50, min_length=5)
# @app.get('/news/feed/')
# async def news_feed(search: Annotated[str | None, feed_query] = "all"):
#     return {'news': ['News1', 'News2', 'News3'], 'search_key': search}

# feed_query = Query(max_length=50)
# @app.get('/news/feed/')
# async def news_feed(search: Annotated[list[str] | None, feed_query] = "all"):
#     return {'news': ['News1', 'News2', 'News3'], 'search_key': search}

# feed_query = Query(max_length=50, title="Qidiruv kaliti", description="Lorem ipsum", alias="news-query", include_in_schema=False)
# @app.get('/news/feed/')
# async def news_feed(search: Annotated[str, feed_query] = "all"):
#     return {'news': ['News1', 'News2', 'News3'], 'search_key': search}

# @app.get('/news/feed/{category}')
# async def news_feed(category: str, search: str = "all"):
#     return {'news': ['News1', 'News2', 'News3'], 'category': category, 'search_key': search}

@app.get('/news/feed/{new_id}')
async def news_feed(
        new_id: Annotated[int, Path(title="Yangilik id", gt=0, le=1000)],
        search: str = "all"):
    return {'news': ['News1', 'News2', 'News3'], 'new_id': new_id, 'search_key': search}