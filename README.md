# 카프카 공부를 위한 Repository(Kafka: The Definitive Guide)

## File Setting

1. [Confluent Cloud Console](https://confluent.cloud/home)에서 클러스터 생성
2. **API keys** 섹션으로 가서 API key 생성
3. **Topics** 섹션으로 가서 topic 생성 (테스트를 위해 purchases 생성)
4. poetry로 **my_kafka_project** 프로젝트 생성 
   - `petry add confluent-kafka`
5. **getting_started.ini** 파일 세팅

## 3장

- 카프카에 메시지를 쓰려면 3개의 필수 속상값을 가지는 프로듀서 객체를 생성해야한다.
  - bootstrap.servers: 카프카 클러스터와 첫 연결을 생성하기 위해 프로듀서가 사용할 브로커의 host:port 목록이다.
    - 브로커 중 하나가 작동을 정지하는 경우에도 프로듀서가 클러스터에 연결할 수 있도록 최소 2개 이상을 지정할 것을 권장한다. 
  - key.serializer: 카프카에 쓸 레코드의 키의 값을 직렬화하기 위해 사용하는 시리얼라이저 클래스의 이름이다.
  - value.serializer: 카프카에 쓸 레코드의 밸류값을 직렬화하기 위해 사용하는 시리얼라이저 클래스의 이름이다.
- 스키마 레지스트리
  - 개요: 카프카는 프로듀서가 메시지를 보낸 후 컨슈머가 소비하려고 할 때 누가 보낸 메시지인지 확인할 수 있는 방법이 없다. 그래서 Producer가 메시지를 기존에 보내던 것과 다른 스키마 형식으로 보낸다면 Consumer는 바뀐 메시지를 받았을 때 문제가 크게 발생할 수도 있다.
  - 스키마 레지스트리는 프로듀서와 컨슈머가 주고 받으려는 메시지의 스키마를 서로 알게 해주고 호환을 강제한다
  - Consumer는 카프카 로부터 바이너리 데이터를 받는데, 이 데이터에는 스키마 ID 가 포함되어 ID를 통해 스키마 레지스트리에서 스키마 정보를 가져와서 사용한다.
  - 장점
    - 잘못된 스키마를 가진 메시지를 전달하고자 한다면 스키마 레지스트리에 등록되는 과정에서 실패가 되고, 카프카에 메시지가 전달되지 않는다.
    - 스키마의 버전관리가 가능해진다.
  - 단점
    - 스키마 레지스트리 서버를 관리해야한다.(운영포인트 증가)
    - 스키마 레지스트리에 장애가 발생하는 경우 정상적으로 메시지를 전달하지 못한다. 
