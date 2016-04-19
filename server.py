import pika
import redis
import tornado.ioloop
import tornado.web
from pika import adapters
from handlers import EvenetsHandler, MainHandler, stop_all


class AMQPConsumer(object):
    def __init__(self, amqp_url):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with

        """
        self._connection = None
        self._channel = None
        self._url = amqp_url

    def connect(self):
        return adapters.TornadoConnection(pika.URLParameters(self._url),
                                          self.on_connection_open)


    def on_connection_open(self, unused_connection):
        self._connection.channel(on_open_callback=self.on_channel_open)


    def on_channel_open(self, channel):
        self._channel = channel
        self._channel.queue_declare(self.on_queue_declareok, 'events')


    def on_queue_declareok(self, method_frame):
        self._channel.basic_consume(self.on_message, queue='events')


    def on_message(self, channel, method, header, body):
        r = redis.StrictRedis(host='localhost')
        r.lpush('events', body)
        r.publish('events', body)
        self._channel.basic_ack(method.delivery_tag)

    def run(self):
        self._connection = self.connect()
        try:
            self._connection.ioloop.start()
        except KeyboardInterrupt:
            stop_all()




if __name__ == "__main__":
    app = tornado.web.Application([
        (r'/events', EvenetsHandler),
        (r'/', MainHandler),
    ])
    app.listen(8888)
    c = AMQPConsumer('amqp://localhost')
    c.run()
