import pika
import localDB

class TelemetryServer():
    def __init__(self, host, port, FarmId, LineId, queue="eggsQueue"):
        self.credentials = pika.PlainCredentials('admin','admin')
        self.host = host
        self.port = port
        self.queue = queue
        self.FarmId = FarmId
        self.LineId = LineId
    
    def publish_message(self, message):
        #sends message to RMQserver
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(self.host,
                                                                           self.port,
                                                                           '/',
                                                                           self.credentials))
            channel = connection.channel()
            channel.confirm_delivery()
            channel.queue_declare(queue=self.queue, durable=True)
            channel.basic_publish(exchange='clickhouse-exchange',
                                 routing_key = self.queue,
                                 body = message)
            connection.close()
            return True
        except Exception as e:
            print("AMQP Connection Error:", e)     
            return False

    def send_count(self, N, datetime ):
        #prepare string for sending and saves to local DB sqlite3
        datetime = int(datetime)
        msg_string = f"{{\"timestamp\":{datetime}," + \
                   f"\"FarmId\" :\"{self.FarmId}\"," + \
                   f"\"LineId\" : {self.LineId}," + \
                   "\"metric\":\"count\"," + \
                   f"\"value\":{N}}}\n" 

        success = self.publish_message(msg_string)
        localDB.insert(datetime, N, success)  
        return success
