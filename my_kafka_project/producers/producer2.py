# #!/usr/bin/env python
#
# """스키마 레지스트리 사용하기
#
# - chapter3 3.5.3 72p.
#
# """
#
# from random import choice
# from argparse import ArgumentParser, FileType
# from configparser import ConfigParser
# from confluent_kafka import avro, KafkaException
# from confluent_kafka.avro import AvroProducer
#
# avro_schema = """{
#     "type": "record",
#     "name": "Purchase",
#     "fields": [
#         {"name": "user_id", "type": "string"},
#         {"name": "product", "type": "string"}
#     ]
# }"""
#
# if __name__ == "__main__":
#     parser = ArgumentParser()
#     parser.add_argument("config_file", type=FileType('r'))
#     args = parser.parse_args()
#
#     config_parser = ConfigParser()
#     config_parser.read_file(args.config_file)
#     config = dict(config_parser['default'])
#
#     avro_producer_config = {
#         'bootstrap.servers': config['bootstrap.servers'],
#         'schema.registry.url': 'http://localhost:8081',
#     }
#
#     value_schema = avro.loads(avro_schema)
#
#     try:
#         avro_producer = AvroProducer(avro_producer_config, default_value_schema=value_schema)
#     except KafkaException as e:
#         print(f"Failed to create AvroProducer: {e}")
#         exit(1)
#
#     def acked(err, msg):
#         if err:
#             print('ERROR: 메시지 전송 실패: {}'.format(err))
#         else:
#             print("메시지 전송 결과 {topic}: key = {key:12} value = {value:12}".format(
#                 topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))
#
#     topic = "purchases"
#     user_ids = ['kwongmin Lim', 'Eunwoo Cho', 'JinWooHyun']
#     products = ['카프카 핵심 가이드', '쿠버네티스 교과서', '개발자 온보딩 가이드', 'Clean Code']
#     for _ in range(3):
#         user_id = choice(user_ids)
#         product = choice(products)
#
#         avro_producer.produce(
#             topic=topic,
#             value={
#                 'user_id': user_id,
#                 'product': product,
#             },
#             callback=acked
#         )
#
#     avro_producer.flush()
