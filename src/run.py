from sanic import Sanic, response, Request

import api

app = Sanic(__name__)


@app.route("/summary")
async def summary(request):
    return response.json(await api.summary(), status=200)


@app.route("/<section>/<path>")
async def timetable(request: Request, section: str, path: str):
    return response.json(await api.table(section, path), status=200)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
