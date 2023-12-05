#!/usr/bin/env python

from random import choice
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config_file", type=FileType('r'))
    args = parser.parse_args()

    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    producer = Producer(config)

    def acked(err, msg):
        if err:
            print('ERROR: 메시지 전송 실패: {}'.format(err))
        else:
            print("메시지 전송 결과 {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    topic = "purchases"
    user_ids = ['kwongmin Lim', 'Eunwoo Cho', 'JinWooHyun']
    products = ['카프카 핵심 가이드', '쿠버네티스 교과서', '개발자 온보딩 가이드', 'Clean Code']
    for _ in range(3):

        user_id = choice(user_ids)
        product = choice(products)
        producer.produce(topic, product, user_id, callback=acked)

    producer.flush()
