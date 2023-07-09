import json
import os
import sys
import threading
import time
from io import StringIO


import pika
import pytest

from teed_worker.worker import Worker


@pytest.fixture(scope="module")
def rabbitmq_connection():
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
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def rabbitmq_channel(rabbitmq_connection):
    channel = rabbitmq_connection.channel()
    yield channel


@pytest.fixture(scope="module")
def rabbitmq_queue(rabbitmq_channel):
    queue_name = "test_queue"
    rabbitmq_channel.queue_declare(queue=queue_name, durable=True)
    yield queue_name
    rabbitmq_channel.queue_delete(queue=queue_name)


@pytest.fixture(scope="module")
def start_worker(request, rabbitmq_queue):
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    username = os.environ.get("RABBITMQ_USERNAME", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    worker = Worker(host, port, username, password, rabbitmq_queue)

    def start_consuming(worker, buffer):
        sys.stdout = buffer
        worker.start_consuming()

    # Start the worker in a separate thread
    buffer = StringIO()
    thread = threading.Thread(
        target=start_consuming,
        args=(
            worker,
            buffer,
        ),
    )
    thread.start()

    def stop_consumer():
        print("Stopping consumer thread...")
        worker.stop_consuming()
        thread.join()

    request.addfinalizer(stop_consumer)

    return buffer


def test_send_json(start_worker, rabbitmq_channel, rabbitmq_queue, capsys):
    buffer = start_worker

    # Send a test message
    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=rabbitmq_queue,
        body=json.dumps({"message": "Test message"}),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
        ),
    )

    # Wait a moment for the message to be processed
    time.sleep(1)

    # check buffer for the thread output
    buffer_contents = (buffer.getvalue()).strip()
    assert "Starting worker, listening to test_queue queue" in buffer_contents

    # check capsys fixture for the callback output
    captured = capsys.readouterr()
    assert captured.out.strip() == "Received message: {'message': 'Test message'}"


def test_send_non_json(start_worker, rabbitmq_channel, rabbitmq_queue, capsys):
    buffer = start_worker

    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=rabbitmq_queue,
        body="Test message",
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
        ),
    )

    time.sleep(1)

    buffer_contents = (buffer.getvalue()).strip()
    assert "Starting worker, listening to test_queue queue" in buffer_contents

    captured = capsys.readouterr()
    assert captured.out.strip() == "Error! Message content type isn't JSON."
