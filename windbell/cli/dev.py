import json

import tornado.ioloop
import tornado.web

from datetime import datetime
from windbell.core.io import Windfile

from windbell.utils import pkg_dir
from windbell.utils import extract_config_item


class WindfileHandler(tornado.web.RequestHandler):
    def initialize(self, path=None, **kwargs):
        self.path = path
        self.windfile = Windfile(open(path, 'r').read())
        super().initialize(**kwargs)

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.windfile.json())

    def post(self):
        self.windfile.config = self.get_argument('config')
        self.windfile.template = self.get_argument('template')

        envs = json.loads(self.get_argument('envs'))
        envs = {
            v['key']: v['value']
            for v in envs
        }

        rendered = self.windfile.render(
            data_injected={
                'meta': {
                    'to': self.windfile.config.value['to'][0],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            env_injected=envs
        )

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps({'rendered': rendered}))

    def put(self):
        self.windfile.config = self.get_argument('config')
        self.windfile.template = self.get_argument('template')

        content = self.windfile.dist()

        f = open(self.path, 'w+')
        f.write(content)
        f.close()

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps({'ok': True}))


def cli_dev(args):
    dev_folder = pkg_dir + '/../etc/dev/'

    app = tornado.web.Application([
        (r'/windfile', WindfileHandler,
         {'path': args.file}),
        (r'/(.*)', tornado.web.StaticFileHandler,
         {'path': dev_folder, 'default_filename': 'index.html'})
    ], debug=True)
    app.listen(args.port)

    tornado.ioloop.IOLoop.current().start()
