# coding: utf-8
"""
订阅者
"""
import os
import sys
import pika

current_dir = os.path.dirname(os.path.realpath(__file__))
current_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
from msgqueue.consume_business import MpMsgConsumer


def start_subscriber():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost', heartbeat=0))
    channel = connection.channel()
    channel.exchange_declare(exchange='mpmsg_exchange', exchange_type='topic')

    channel.queue_declare(queue="mpmsg_queue", durable=True)
    channel.queue_bind(exchange='mpmsg_exchange',
                       queue="mpmsg_queue",
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
