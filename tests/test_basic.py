import json
import logging
import os
import threading
import time

import pika
import pytest

from teed_worker.worker import Worker


class MockLoggingHandler(logging.Handler):
    """
    Mock logging handler to check for expected logs.

    Messages are available from an instance's ``messages`` dict, in order, indexed by
    a lowercase log level string (e.g., 'debug', 'info', etc.).

    """

    def __init__(self, *args, **kwargs):
        self.messages = {
            "debug": [],
            "info": [],
            "warning": [],
            "error": [],
            "critical": [],
        }
        super(MockLoggingHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        # Store a message from ``record`` in the instance's ``messages`` dict.
        # noinspection PyBroadException
        try:
            self.messages[record.levelname.lower()].append(record.getMessage())
        except Exception:
            self.handleError(record)

    def reset(self):
        self.acquire()
        try:
            for message_list in self.messages.values():
                message_list.clear()
        finally:
            self.release()


@pytest.fixture(scope="module")
def rabbitmq_connection():
    """Set up RabbitMQ connection"""

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
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def rabbitmq_channel(rabbitmq_connection):
    """Open RabbitMQ channel"""

    channel = rabbitmq_connection.channel()
    yield channel


@pytest.fixture(scope="module")
def rabbitmq_queue(rabbitmq_channel):
    """RabbitMQ queue"""

    queue_name = "test-queue"
    rabbitmq_channel.queue_declare(queue=queue_name, durable=True)
    yield queue_name
    rabbitmq_channel.queue_delete(queue=queue_name)


@pytest.fixture(scope="module")
def start_worker(request, rabbitmq_queue):
    """Teed worker and logging"""

    # configure logging, attache mocked handler
    # which stored the logging messages in a dict[list]
    # per logging level
    logging.config.fileConfig("logging.conf")
    consumer_log = logging.getLogger("workerLogger")
    consumer_log_handler = MockLoggingHandler(level=logging.DEBUG)
    consumer_log.addHandler(consumer_log_handler)
    consumer_log_messages = consumer_log_handler.messages

    # create worker and start it in a separate thread
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    username = os.environ.get("RABBITMQ_USERNAME", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    worker = Worker(host, port, username, password, rabbitmq_queue)

    def start_consuming(worker):
        worker.start_consuming()

    def stop_consumer():
        worker.stop_consuming()
        thread.join()

    # Start the worker in a separate thread
    thread = threading.Thread(
        target=start_consuming,
        args=(worker,),
    )
    thread.start()

    # stop consumer when test ends
    # request is a inner pytest object representing the test
    request.addfinalizer(stop_consumer)

    return consumer_log_messages


def message_in_log(message: str, log: list[str]) -> bool:
    """Check if a give message is in the log entries list"""

    return any(m == message for m in log)


def test_send_json(start_worker, rabbitmq_channel, rabbitmq_queue):
    # fetch log messages
    consumer_log_messages = start_worker

    # Send a test message
    message_data = {"message": "Test message"}
    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=rabbitmq_queue,
        body=json.dumps(message_data),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
        ),
    )

    # Wait a moment for the message to be processed
    time.sleep(1)

    # check log content
    info_messages = consumer_log_messages.get("info")
    assert message_in_log("Connection opened", info_messages)
    assert message_in_log("Channel created", info_messages)
    assert message_in_log("Queue test-queue declared", info_messages)
    assert message_in_log("Ready to consume messages", info_messages)
    assert message_in_log(
        "Start consuming, listening to test-queue queue", info_messages
    )

    debug_messages = consumer_log_messages.get("debug")
    assert message_in_log(f"Received message: {message_data}", debug_messages)


def test_send_non_json(start_worker, rabbitmq_channel, rabbitmq_queue):
    # fetch log messages
    consumer_log_messages = start_worker

    # Send a test message
    message = "Hello!"
    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=rabbitmq_queue,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
        ),
    )

    # Wait a moment for the message to be processed
    time.sleep(1)

    # check log content
    info_messages = consumer_log_messages.get("info")
    assert message_in_log("Connection opened", info_messages)
    assert message_in_log("Channel created", info_messages)
    assert message_in_log("Queue test-queue declared", info_messages)
    assert message_in_log("Ready to consume messages", info_messages)
    assert message_in_log(
        "Start consuming, listening to test-queue queue", info_messages
    )

    debug_messages = consumer_log_messages.get("debug")
    assert message_in_log("Error! Message content type isn't JSON", debug_messages)
