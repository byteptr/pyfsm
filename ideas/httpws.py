from dataclasses import dataclass, field
from graphviz import Digraph
import asyncio
import websockets
import random
from aiohttp import web
import aiofiles 

class pyfsm_http_visualizer: 
    def __init__(self, http_port:int=8000, ws_port:int=8765, html_template='aioftest.html'):
        self.http_port = http_port
        self.ws_port = ws_port
        self.html_template = html_template
        self.app = None

    async def http_startup(self): 
        pass

    async def http_cleanup(self): 
        pass


    async def http_handle(self, request):
        async with aiofiles.open('aioftest.html', 'r') as fd: 
            html = await fd.read()
        return web.Response(text=html, content_type='text/html')

    async def start_http_server(self):
        self.app = web.Application()
        self.app.router.add_get('/', self.http_handle)
        self.app.on_startup.append(self.http_startup)
        self.app.on_cleanup.append(self.http_cleanup)


# app = web.Application()
# app.router.add_get('/', handle)
#
# if __name__ == '__main__':
#     web.run_app(app, host='127.0.0.1', port=8000)
#
