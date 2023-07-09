import json
import os
import signal
import sys

import pika


class Worker:
    def callback(self, ch, method, properties, body):
        if properties.content_type == "application/json":
            message_data = json.loads(body.decode())
            print(f"Received message: {message_data}")
            # Process the received message here
        else:
            print("Error! Message content type isn't JSON.")

    def handle_kill_signal(self, signum, frame):
        self._channel.stop_consuming()
        print("Received kill signal. Gracefully terminating the consumer.")
        sys.exit(0)

    def __init__(
        self, host: str, port: int, username: str, password: str, queue_name: str
    ) -> None:
        # Set up RabbitMQ connection parameters
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host,
                port,
                virtual_host="/",
                credentials=pika.PlainCredentials(
                    username,
                    password,
                ),
            )
        )

        # Create a channel
        channel = connection.channel()

        # Declare the queue from which to consume
        channel.queue_declare(queue_name, durable=True)

        # Set up the callback function to handle incoming messages
        channel.basic_consume(
            queue=queue_name, on_message_callback=self.callback, auto_ack=True
        )

        self._queue_name = queue_name
        self._channel = channel

    def start_consuming(self):
        print(f"Starting worker, listening to {self._queue_name} queue.")

        # Start consuming messages
        self._channel.start_consuming()

    def stop_consuming(self):
        self._channel.stop_consuming()


def main():
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    username = os.environ.get("RABBITMQ_USERNAME", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    queue_name = os.environ.get("QUEUE_NAME", "default-queue")

    worker = Worker(host, port, username, password, queue_name)

    # Register the signal handler for the kill signal (SIGINT)
    signal.signal(signal.SIGINT, worker.handle_kill_signal)

    # Start working...
    worker.start_consuming()


# The following block is executed when the script is run directly
if __name__ == "__main__":
    main()
