import os
import redis
import tornado.web
import tornado.websocket
import tornado.template

r = redis.StrictRedis(host='localhost')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        loader = tornado.template.Loader(os.getcwd())
        self.write(loader.load('html/index.html').generate(**{'events': r.lrange("events", 0, -1)}))


threads = []
def stop_all():
    for thread in threads:
        thread.stop()

class EvenetsHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.p = r.pubsub()
        self.p.subscribe(**{'events':self.event})
        self.thread = self.p.run_in_thread(sleep_time=0.001)
        threads.append(self.thread)

    def event(self, message):
        self.write_message(message['data'])

    def on_close(self):
        self.thread.stop()

