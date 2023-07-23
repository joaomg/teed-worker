import datetime
import json
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

queue_name = os.environ.get("QUEUE_NAME", "teed-worker")

channel.queue_declare(queue=queue_name, durable=True)

print(len(sys.argv))

message_data = (
    json.loads(" ".join(sys.argv[1:]))
    if len(sys.argv) > 1
    else {
        "message": "Hello World",
        "timestamp": datetime.datetime.now().timestamp(),
    }
)

json_message = json.dumps(message_data)

channel.basic_publish(
    exchange="",
    routing_key=queue_name,
    body=json_message,
    properties=pika.BasicProperties(
        content_type="application/json",
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
    ),
)
print(" [x] Sent %r" % json_message)
connection.close()
