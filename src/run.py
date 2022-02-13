from sanic import Sanic, response, Request
from sanic_cors import CORS

import api

app = Sanic(__name__)
CORS(app)


@app.route("/summary")
async def summary(request):
    return response.json(await api.summary(), status=200)


@app.route("/<section>/<path>")
async def timetable(request: Request, section: str, path: str):
    path = path.replace('*', '_')
    return response.json(await api.table(section.lower().capitalize(), path), status=200)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
