from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from enum import Enum

"""
Task example in JSON
{
  "uuid": "093b1603-240b-4660-9bad-861caee1e7a8",
  "created_on": "2023-07-22 18:24:47",
  "created_by": "joaomg",
  "type": "bulkcm_split",
  "state": "todo",
  "args": {}
}

{
    "uuid": "093b1603-240b-4660-9bad-861caee1e7a8",
    "created_on": "2023-07-22 18:24:47",
    "created_on_by": "joaomg",
    "type": "bulkcm_split",
    "state": "todo",
    "args": {
        "file_path": "s3://{ACCESS_KEY}:{SECRET_KEY}@data/093b1603-240b-4660-9bad-861caee1e7a8/in/bulkcm.xml?scheme=http&endpoint_override=localhost:9000",
        "output_dir": "s3://{ACCESS_KEY}:{SECRET_KEY}@data/093b1603-240b-4660-9bad-861caee1e7a8/out?scheme=http&endpoint_override=localhost:9000",
    },
}
"""


class Type(str, Enum):
    bulkcm_probe = "bulkcm_probe"
    bulkcm_split = "bulkcm_split"
    bulkcm_parse = "bulkcm_parse"
    meas_parte = "meas_parse"


class State(str, Enum):
    todo = "todo"
    done = "done"
    done_with_error = "done_with_error"
    failed = "failed"


class Task(BaseModel):
    uuid: UUID  # uuid that identifies the task in the Teed processing system (attributed by teed-service on task creation)
    parent_task_uuid: Optional[
        UUID
    ] = None  # if the task is a child-task then it has a parent
    created_on: datetime  # creation datetime in UTC
    created_by: str  # who created_on the task, usually teed-service
    processed_on: Optional[
        datetime
    ] = None  # processed datetime in UTC (the datetime when a teed-worked finished working on the task)
    processed_by: Optional[str] = None  # the teed-worker who finished the task
    type: Type  # the teed operation which the task represents
    state: State  # the current state of the task
    args: Dict[str, str]  # the arguments needed to perform the task
