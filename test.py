#!/usr/bin/env python3

from sanic import Blueprint, Sanic, response

from sanic_prometheus import monitor

app = Sanic('test_app')
test_bp = Blueprint('test')


@test_bp.route('/home', methods=['GET'])
async def home(request):
    return response.json({'success': 'you are home'})


# app setup must happen at module level (not under __main__) so that
# Sanic's spawned worker processes see it when they re-import this module
monitor(app).expose_endpoint()
app.blueprint(test_bp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, auto_reload=False,
            access_log=True, debug=True)
