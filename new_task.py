import os
import sys

import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "localhost"),
        port=os.environ.get("RABBITMQ_PORT", 5672),
        virtual_host="/",
        credentials=pika.PlainCredentials(
            os.environ.get("RABBITMQ_USERNAME", "guest"),
            os.environ.get("RABBITMQ_PASSWORD", "guest"),
        ),
    )
)
channel = connection.channel()

queue_name = os.environ.get("QUEUE_NAME", "default-queue")

channel.queue_declare(queue=queue_name, durable=True)

message = " ".join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(
    exchange="",
    routing_key=queue_name,
    body=message,
    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
)
print(" [x] Sent %r" % message)
connection.close()
