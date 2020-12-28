# coding: utf-8
"""
订阅者
"""
import pika
from msgqueue.consume_business import MpMsgConsumer

print("start subscriber")


def start_subscriber():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost', heartbeat=0))
    channel = connection.channel()
    channel.exchange_declare(exchange='mpmsg_exchange', exchange_type='topic')

    # channel.queue_declare(queue="mpmsg_queue", durable=True)
    # channel.queue_bind(exchange='mpmsg_exchange',
    #                    queue="mpmsg_queue",
    #                    routing_key="mpmsg.*")

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='mpmsg_exchange',
                       queue=queue_name,
                       routing_key="mpmsg.*")

    channel.basic_qos(prefetch_count=1)

    # 消费者 auto_ack=False设置为手动确认消息
    consumer = MpMsgConsumer()
    channel.basic_consume(
        queue="mpmsg_queue",
        on_message_callback=consumer.callback,
        auto_ack=False)

    channel.start_consuming()


if __name__ == "__main__":
    start_subscriber()
