# teed-worker

A RabbitMQ consumer for processing teed jobs.
A job is encoded as JSON and sent as text to the queue.
The worker, and teed lib, have been tested to run in Linux.

# Install and run RabbitMQ server in docker

docker pull rabbitmq
docker run -d --hostname my-rabbitmq -p 15672:15672 -p 5672:5672 --name my-rabbitmq rabbitmq:3-management
docker logs my-rabbitmq

# Install

With latest teed release in test.pypi.org.

The pyarrow package is needed by teed, the version >=11.0 isn't available in test.pypi.org.

It needs to be installed separately.

```bash
pip install -r requirements.txt
pip install pyarrow
pip install -i https://test.pypi.org/simple/ teed==0.0.8.2
```

# Run worker

```bash
python teed_worker/worker.py
```

# Send JSON message to queue

In this example we are requesting

the bulkcm.split of file bulkcm.xml

in s3://data/093b1603-240b-4660-9bad-861caee1e7a8/in

to s3://data/093b1603-240b-4660-9bad-861caee1e7a8/out

```bash
message_empty="{
  \"uuid\": \"093b1603-240b-4660-9bad-861caee1e7a8\",
  \"created_on\": \"2023-07-22 18:24:47\",
  \"created_by\": \"joaomg\",
  \"type\": \"bulkcm_split\",
  \"state\": \"todo\",
  \"args\": {
    \"file_path\": \"\",
    \"output_dir\": \"\"
  }
}"
echo "${message_empty}" | jq
python new_task.py ${message_empty}
```

# Test

```bash
pip install -r requirements.dev.txt
pytest tests
```
