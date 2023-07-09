import os
import signal
import sys

import pika


def callback(ch, method, properties, body):
    print("Received message:", body.decode())
    # Process the received message here


def handle_kill_signal(signum, frame):
    print("Received kill signal. Gracefully terminating the consumer.")
    sys.exit(0)


# Register the signal handler for the kill signal (SIGINT)
signal.signal(signal.SIGINT, handle_kill_signal)

# Set up RabbitMQ connection parameters
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

# Create a channel
channel = connection.channel()

# Queue
queue_name = os.environ.get("QUEUE_NAME", "default-queue")

# Declare the queue from which to consume
channel.queue_declare(queue_name, durable=True)

# Set up the callback function to handle incoming messages
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print(f"Starting worker, listening to {queue_name} queue.")

# Start consuming messages
channel.start_consuming()
