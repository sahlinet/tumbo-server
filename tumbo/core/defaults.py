CORE_VHOST="/core"
CORE_SENDER_USERNAME="fastapp-w"
CORE_RECEIVER_USERNAME="fastapp-r"

HEARTBEAT_QUEUE="heartbeat_queue"
ASYNC_RESPONSE_QUEUE="async_callback"
LOGS_QUEUE="logs"

SENDER_PERMISSIONS={"scope":"client","configure":".*","write":".*","read":""}
RECEIVER_PERMISSIONS={"scope":"client","configure":".*","write":"","read":".*"}

WORKER_VHOST_PERMISSIONS={"scope":"client","configure":".*","write":".*","read":".*"}
SERVER_VHOST_PERMISSIONS=WORKER_VHOST_PERMISSIONS

HEARTBEAT_READER_PERMISSIONS="heartbeat-r"
RABBITMQ_SERVER_USER = "fastapp"