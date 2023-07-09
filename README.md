# teed-worker

A RabbitMQ consumer for processing teed jobs

# Install and run RabbitMQ server in docker

docker pull rabbitmq
docker run -d --hostname my-rabbitmq -p 15672:15672 -p 5672:5672 --name my-rabbitmq rabbitmq:3-management
docker logs rabbitmq

# Run worker

```bash
python worker.py
```

# Send message to queue

```bash
python new_task.py "Hello!"
```
