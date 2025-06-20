from aiohttp import web
async def handle(request):
    html = """
    <html>
        <head><title>Hola</title></head>
        <body>
            <h1>Hola, mundo desde Python (async)</h1>
            <p>Este HTML viene desde un string con aiohttp.</p>
        </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

app = web.Application()
app.router.add_get('/', handle)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8000)
