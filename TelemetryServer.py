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

    def send_undelivered(self):
        rows = localDB.undelivered()
        for row in rows:
            datetime = int(row[0])
            value = row[1]
            msg_string = f"{{\"timestamp\":{datetime}," + \
                       f"\"FarmId\" :\"{self.FarmId}\"," + \
                       f"\"LineId\" : {self.LineId}," + \
                       "\"metric\":\"count\"," + \
                       f"\"value\":{value}}}\n" 
            success = self.publish_message(msg_string) 
            if(success == True):
                localDB.updateStatus(row[0])
            
        

    def send_count(self, N, datetime ):
        #prepare string for sending and saves to local DB sqlite3
        datetime = int(datetime)
        msg_string = f"{{\"timestamp\":{datetime}," + \
                   f"\"FarmId\" :\"{self.FarmId}\"," + \
                   f"\"LineId\" : {self.LineId}," + \
                   "\"metric\":\"count\"," + \
                   f"\"value\":{N}}}\n" 
        #if message delivered success col in local db set 1 else 0
        success = self.publish_message(msg_string) 
        localDB.insert(datetime, N, success)  
        if(success == True):
            self.send_undelivered()
        return success
