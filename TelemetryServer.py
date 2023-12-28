import pika
import time

class TelemetryServer():
    def __init__(self, host, port, FarmId, LineId, queue="eggsQueue"):
        self.credentials = pika.PlainCredentials('admin','admin')
        self.host = host
        self.port = port
        self.queue = queue
        self.FarmId = FarmId
        self.LineId = LineId
    
    def publish_message(self, message):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(self.host,
                                                                           self.port,
                                                                           '/',
                                                                           self.credentials))
            channel = connection.channel()
            channel.queue_declare(queue=self.queue, durable=True)
            channel.basic_publish(exchange='clickhouse-exchange',
                                 routing_key = self.queue,
                                 body = message)
            connection.close()

        except pika.exceptions.AMQPConnectionError as e:
            print("AMQP Connection Error:", e)     

    def send_count(self, N ):
        datetime = int(time.time())
        msg_string = f"{{\"timestamp\":{datetime}," + \
                   f"\"FarmId\" :\"{self.FarmId}\"," + \
                   f"\"LineId\" : {self.LineId}," + \
                   "\"metric\":\"count\"," + \
                   f"\"value\":{N}}}\n" 
        self.publish_message(msg_string)
