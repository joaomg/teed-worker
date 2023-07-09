import os
import threading
import time
from queue import Queue

import pika
import pytest


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
    rabbitmq_channel.queue_declare(queue=queue_name)
    yield queue_name
    rabbitmq_channel.queue_delete(queue=queue_name)


@pytest.fixture(scope="module")
def start_consumer(request, rabbitmq_connection, rabbitmq_queue):
    shared_data = Queue()

    def callback(ch, method, properties, body):
        print("Received message:", body.decode())
        shared_data.put(body.decode())

    channel = rabbitmq_connection.channel()
    channel.basic_consume(
        queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True
    )

    # Start the consumer in a separate thread
    thread = threading.Thread(target=channel.start_consuming)
    thread.start()

    def stop_consumer():
        print("Stopping consumer thread...")
        channel.stop_consuming()
        thread.join()

    request.addfinalizer(stop_consumer)
    return shared_data


def test_send_message(start_consumer, rabbitmq_channel, rabbitmq_queue):
    shared_data = start_consumer

    # Send a test message
    message = "Test message"
    rabbitmq_channel.basic_publish(
        exchange="", routing_key=rabbitmq_queue, body=message
    )

    # Wait a moment for the message to be processed
    time.sleep(1)

    print("Checking variables...")

    # Perform assertions based on the message processing
    assert not shared_data.empty()
    processed_message = shared_data.get()
    assert processed_message == message
