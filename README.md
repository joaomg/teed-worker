# teed-worker

A RabbitMQ consumer for processing teed jobs.
A job is encoded as JSON and sent as text to the queue.

# Install and run RabbitMQ server in docker

docker pull rabbitmq
docker run -d --hostname my-rabbitmq -p 15672:15672 -p 5672:5672 --name my-rabbitmq rabbitmq:3-management
docker logs my-rabbitmq

# Run worker

```bash
python teed_worker/worker.py
```

# Send JSON message to queue

```bash
python new_task.py "{\"message_count\": 1, \"message_body\": \"Hello for the first time\"}"
```

# Test

```bash
pytest tests
```
