import json
import logging
import logging.config
import os
import signal
import sys

import pika


class Worker:
    def __init__(
        self, host: str, port: int, username: str, password: str, queue_name: str
    ) -> None:
        self._logger = logging.getLogger("workerLogger")

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
        self._logger.info("Connection opened")

        # Create a channel
        channel = connection.channel()
        self._logger.info("Channel created")

        # Declare the queue from which to consume
        channel.queue_declare(queue_name, durable=True)
        self._logger.info(f"Queue {queue_name} declared")

        # Set up the callback function to handle incoming messages
        channel.basic_consume(
            queue=queue_name, on_message_callback=self.callback, auto_ack=True
        )
        self._logger.info(f"Ready to consume messages")

        self._queue_name = queue_name
        self._channel = channel

    def callback(self, ch, method, properties, body):
        if properties.content_type == "application/json":
            message_data = json.loads(body.decode())
            self._logger.debug(f"Received message: {message_data}")
            # Process the received message here
            # @@
        else:
            self._logger.debug("Error! Message content type isn't JSON")

    def handle_kill_signal(self, signum, frame):
        self._channel.stop_consuming()
        self._logger.info("Received kill signal. Gracefully terminating the consumer")
        sys.exit(0)

    def start_consuming(self):
        self._logger.info(f"Start consuming, listening to {self._queue_name} queue")
        self._channel.start_consuming()

    def stop_consuming(self):
        self._channel.stop_consuming()


def main():
    logging.config.fileConfig("logging.conf")

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
