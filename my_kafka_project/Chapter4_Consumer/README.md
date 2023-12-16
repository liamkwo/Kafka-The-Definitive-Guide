### 컨슈머와 컨슈머 그룹

---
카프카에서 데이터를 읽는 애플리케이션은 토픽을 구독하고 구독한 토픽들로부터 메시지를 받기 위해 **KafkaConsumer**를 사용합니다.

- 컨슈머 객체(KafkaConsumer)를 생성하고, 해당 토픽을 구독하고, 받은 메시지를 받아 검사하고 결과를 써야하는 애플리케이션이 존재한다고 했을 때, 만약 프로듀서가 이 애플리케이션이 검사할 수 있는 속도 보다 더 빠른 속도로 토픽에 메시지를 쓰고 이 데이터를 읽고 처리하는 컨슈머가 하나뿐이라면, 메시지처리가 계속해서 뒤로 밀리게 될 것 입니다. 때문에 여러 개의 프로듀서가 동일한 토픽에 메시지를 쓰듯이, 여러 개의 컨슈머가 같은 토픽으로부터 데이터를 분할해서 읽어올 수 있어야 합니다.
- 카프카 컨슈머는 보통 컨슈머 그룹의 일부로써 작동합니다. 동일한 컨슈머 그룹에 속한 여러 개의 컨슈머들이 동일한 토픽을 구독할 경우, 각각의 컨슈머는 해당 토픽에서 서로 다른 파티션의 메시지를 받게됩니다.

![컨슈머 이미지](https://private-user-images.githubusercontent.com/63140834/289796925-114a45d5-a3f7-4126-b4ae-09ac19f7e7dd.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTEiLCJleHAiOjE3MDIzNzA4MTcsIm5iZiI6MTcwMjM3MDUxNywicGF0aCI6Ii82MzE0MDgzNC8yODk3OTY5MjUtMTE0YTQ1ZDUtYTNmNy00MTI2LWI0YWUtMDlhYzE5ZjdlN2RkLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFJV05KWUFYNENTVkVINTNBJTJGMjAyMzEyMTIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjMxMjEyVDA4NDE1N1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTM0NjI1MDA0Yzg3OWEzZjdlNDI4MmZhZWM0MDU0MmFjMjllNWFkZGU3OTkzM2QyYTZkMDkzMzZjMTYzYTYyNzUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.AjoLmgaB26sYM8mosksLrup_zAzeafYRrPwG1OtTXVo)

- 파티션 개수보다 컨슈머 그룹에 속한 컨슈머가 더 많을 때 유후 컨슈머 발생
- 토픽에서 메시지를 읽거나 처리하는 규모를 확장하기 위해서는 이미 존재하는 컨슈머 그룹에 새로운 컨슈머 추가
- 토픽에 쓰여진 데이터를 여러 용도로 사용할 수 있을 수 있도록 1개 이상의 토픽에 대해 모든 메시지를 받아야하는 새로운 컨슈머 그룹 생성 가능

---

#### 리밸런스
컨슈머에 할당된 파티션을 다른 컨슈머에게 할당해주는 작업을 **리밸런스**라고 합니다.

- 조급한 리밸런스
	- 모든 파티션 할당을 해제한 뒤 읽기 작업을 정지시킨 후 파티션을 재할당 합니다.
	- 전체 컨슈머 그룹에 대해 짧은 시간 동안 작업을 멈추게합니다.
- 협력적 리밸런스
	1. 컨슈머 그룹 리더(가장 먼저 그룹에 참여한 컨슈머)가 다른 컨슈머들에게 각자에게 해당된 파디션 중 일부가 재할당된다고 통보
	2. 컨슈머들은 해당 파티션에서 데이터를 읽어오는 것을 멈추고 해당 파티션에 대한 소유권 포기
	3. 컨슈머 그룹 리더가 포기된 파티션을 새로 할당 
- 2.4 이후로 조급한 리밸런스가 기본값이었지만, 3.1부터는 협력적 리밸런스가 기본값임. 조급한 리밸런스는 추후 삭제될 예정이라고함

**컨슈머** **그룹 코디네이터**는 특정 컨슈머 그룹을 관리하는 브로커입니다
- 컨슈머 그룹의 컨슈머는 폴링하거나 커밋할 때 **하트비트** 메시지를 백그라운드 스레드로 그룹 코디네이터에게 전달합니다.
- 그룹 코디네이터가 일정 시간 동안 컨슈머의 하트비트를 받지 못하면, 해당 컨슈머는 작업이 불가한 것으로 판단하고 리밸런스를 실행합니다.

**group.instance.id**를 설정하여 정적 그룹 멤버십을 설정할 수 있습니다.
- 그룹 코디네이터는 그룹 내 각 멤버에 대한 파티션 할당을 캐시해 두고 있기 때문에 정적 멤버가 다시 조인해 들어온다고 해도 리밸런스를 발생시키지 않습니다.
- **group.instance.id**는 유니크 해야하며, 같은 id를 가진 컨슈머가 같은 그룹에 조인할 경우 에러가 발생합니다.
- **session.timeout.ms**옵션을 설정하여 정적 멤버십에 대한 리밸런싱을 조절할 수 있습니다.(적절한 시간 설정 필요 90p 중간부분)

##### 예시
`session.timeout.ms=30000`로 가정했을 때,

![컨슈머 리벨런싱](https://private-user-images.githubusercontent.com/63140834/289796620-1d02d5ca-3ba2-4460-8cb7-56c0f8ed4eaa.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTEiLCJleHAiOjE3MDIzNzA3NDEsIm5iZiI6MTcwMjM3MDQ0MSwicGF0aCI6Ii82MzE0MDgzNC8yODk3OTY2MjAtMWQwMmQ1Y2EtM2JhMi00NDYwLThjYjctNTZjMGY4ZWQ0ZWFhLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFJV05KWUFYNENTVkVINTNBJTJGMjAyMzEyMTIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjMxMjEyVDA4NDA0MVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWE3YzQwZTMwODNmYTdlYjU0MjE2OTVkMzhmMTBmMmU5NTA4ZjAwZjgzYmY3M2M2NmQ2NmEyNTA0ZDA3OWZkMGImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.quNGdsqL88i-jKHtx_xTk9PGQp6KzyLd72KKLw_EHjg)

- 표준 컨슈머 사용시
	1. 컨슈머 오류 발생시 해당 컨슈머를 제거 후 즉시 리벨런싱
	2. 컨슈머가 다시 조인하고 한번 더 리벨런싱
- 정적 멤버십을 적용한 컨슈머 사용시
	1. `session.timeout.ms=30000` 를 설정한 3초 동안 리벨런싱을 안함
	2. 만약 장애 이후 설정한 시간내에 복구되면 캐시되어져 있는 기존과 동일한 파티션에 할당

---

#### 카프카 레코드 읽어오기

- **KafkaConsumer** 인스턴스 생성
- 프로듀서와는 반대로 **바이트 배열을 객체로 변환**
- 컨슈머 필수 설정
	- bootstrap.servers
		- 카프카 브로커 `host/port` 목록
	- key.deserializer
		- message 키를 역직렬화하는 클래스 지정
	- value.deserializer
		- message 값을 역직렬화하는 클래스 지정
	- group.id
		- 컨슈머 그룹을 지정
		- confluent kafka에서는 필수 값

---

#### 1개 이상의 토픽 구독 하기
- `subscribe()`메서드는 토픽 목록을 매개변수로 받기 때문에 사용법이 간단함
- 카프카 클러스트에 파티션이 매우 많다면 토픽을 필터링하는 작업은 클라이언트에서 이루어짐
- 정규식을 매개변수로 사용해서 subscribe를 호출할 수 도 있음
	- 정규식으로 지정할 경우 컨슈머는 전체 토픽과 파티션에 대한 정보를 브로커에 일정한 간격으로 요청
	- 토픽의 목록이 크고 컨슈머도 굉장히 많으며, 파티션의 목록도 크다면 상당한 오버헤드를 발생시킬 수 있음
- 예) 모든 parchase 토픽 구독

```python
topic_pattern = "purchase.*"  
consumer.subscribe(pattern=topic_pattern)
```

---

#### 폴링루프
- 컨슈머의 토픽 구독 요청이 정상적으로 처리되면, 서버에 추가 데이터가 들어왔는지 `poll()`하는 무한 루프(**폴링 루프**)
	- poll은 레코드들이 저장된 List객체를 리턴
		- 각각의 레코드는 저장되어있던 토픽, 파티션, 파티션에서 오프셋, 키/벨류를 포함
	- 그리고 이 List를 반복해 가며 각각의 레코드를 처리
	- 처리가 끝날 때 결과물을 데이터 저장소에 쓰거나 이미 저장된 레코드를 갱신
	- **max.poll.interval.ms**에 지정된 시간 이상으로 호출 되지 않을 경우 컨슈머는 죽은것으로 판정
		- 때문에 폴링 루프 안에서는 예측 불가능한 시간 동안 블록되는 작업은 피해야함

---

##### 폴링 루프가 추가로 하는일
- 새로운 컨슈머에서 최초로 `poll()`을 호출하면
	1. 이 메소드에서 `GroupCoordinator`를 찾고,
	2. 컨슈머 그룹에 추가시키고,
	3. 해당 컨슈머에게 할당된 파티션 내역을 받음
- 리밸런스가 생길 때 필요한 처리
- 컨슈머가 계속 살아 동작할 수 있게 해주는 **하트비트 전송**

---

#### 컨슈머 설정
- [컨플루언트 컨슈머 설정 docs](https://docs.confluent.io/platform/current/installation/configuration/consumer-configs.html)
- fetch.min.bytes(df: 1)
	- 컨슈머가 브로커로부터 데이터 가져올 수 있는 최소 사이즈로, 만약 가져오는 데이터가 지정한 사이즈보다작으면 요청에 응답하지 않고, 데이터가 누적될 때 까지 기다림
	- 값이 증가시킬 수록 처리량이 작은 상황에서 지연 또한 증가할 수 있음
- fetch.max.wait.ms(df: 500)
	- fetch.min.bytes에 설정된 데이터보다 데이터 양이 적은 경우 요청에 응답을 기다리는 최대 시간
	- 만약 fatch.min.bytes이 1mb고 fetch.max.wait.ms이 100밀리초일 경우 두 조건 중 하나가 만족하면 리턴
- fetch.max.bytes(df: 52428800 (50 mebibytes))
	- 컨슈머가 브로커로부터 데이터 가져올 수 있는 최대 사이즈
		- 기본 값은 50mb
	- 만약 브로커가 보내는 첫번 째 레코드 배치의 크기가 이 설정 값을 넘길 경우, 제한 값을 무시하고 배치를 그대로 전송
		- <span style='color:#eb3b5a'>이것은 컨슈머가 읽기 작업을 계속해서 진행할 수 있도록 보장해줌</span>
- max.poll.records(df: 500)
	- 폴링루프에서 poll()을 호출할 때마다 리턴되는 최대 레코드 수를 지정함
- max.partition.fetch.bytes(df: 1048576 (1 mebibyte))
	- 서버가 파티션 별로 리턴하는 최대 바이트 수를 결정함
- session.timeout.ms(df:45000)
    - 컨슈머와 브로커 사이의 세션 타임 아웃 시간으로, 브로커와 컨슈머가 신호를 주고받지 않고도 살아있는 것으로 판단하는 시간
    - 컨슈머가 그룹 코디네이터에게 하트비트를 해당 시간만큼 보내지 않으면, 해당 컨슈머는 장애가 생겼다고 판단하여 컨슈머 그룹은 리밸런스를 실행함
      > 원래 기본 값은 10초였으나 순간 적인 부하 집중과 네트워크 불안정이 자주 발생하는 클라우드 환경에는 적절치 않아서 3.0이후에 45초로  변경
- heartbeat.interval.ms(df: 3000)
    - 카프카 컨슈머가 그룹 코디네이터에게 얼마나 자주 하트비트를 보낼 것인지 조정함
      > 일반적으로, session.timeout.ms의 1/3 정도로 설정한다는 규칙이 있는데 더이상 이 규칙은 유효하지 않다.
- max.poll.interval.ms(df: 300000 (5 minutes))
	- 하트비트는 백그라운드 스레드에 의해 전송된다. 만약 카프카에서 레코드를 읽어오는 메인 스레드는 데드락이 걸렸는데 백그라운드 스레드는 멀쩡히 하트비트를 전송하고 있을 수도 있다. 따라서 poll 주기를 설정하여 장애를 판단하는데 사용한다.
	- 타임아웃이 발생한다면 백그라운드 스레드는 브로커로 하여금 컨슈머가 죽어서 리밸런스가 수행되어야 한다는 걸 알 수 있도록 <span style='color:#f7b731'>"leave group"</span> 요청을 보낸 뒤, 하트비트 전송을 중단한다.
- default.api.timeout.ms(df: 60000 (1 minute))
	- API를 호출할 때 명시적인 타임아웃을 지정하지 않는 한, 거의 모든 컨슈머 API 호출에 적용되는 타임아웃 값.
	- 이 값이 적용되지 않는 중요한 예외로는 poll() 메서드가 있다.
- request.timeout.ms(df: 30000 (30 seconds))
	- 컨슈머가 브로커의 응답을 기다리는 최대 시간으로, 지정한 시간만큼 요청에 대한 응답이 안오면 재연결을 시도한다.
- auto.offset.reset (df: latest) 
    - 카프카에서 초기 오프셋이 없거나, 커밋된 오프셋이 유효하지 않을 때 다음 옵션으로 리셋한다.
        - earlist: 맨 처음부터 데이터를 읽는 방식
        - latest: 가장 최신의 레코드부터 읽기 시작
        - none: 유효하지 않은 오프셋을 읽으려하면(이전 오프셋값을 찾지 못하면) 에러를 발생시킵니다.
- enable.auto.commit (df: true)
    - 컨슈머가 자동으로 오프셋을 커밋할지 안할지 설정하는 옵션
    - auto.commit.interval.ms (df: 5000ms = 5sec)
    	- 주기적으로 오프셋을 커밋하는 시간
- partition.assignment.strategy(df: Range)
	- 어느 컨슈머에게 어느 파티션이 할당될지를 결정하는 역할 
	- Range(org.apache.kafka.clients.consumer.RangeAssignor)
		- 컨슈머가 구독하는 각 토픽의 파티션들을 연속된 그룹으로 나누어 할당해준다.
		- 무조건 0부터 순서대로 할당해준다.
	- RoundRobin(org.apache.kafka.clients.consumer.RoundRobinAssignor)
		- 모든 토픽의 모든 파티션을 파티션의 순서대로 하나씩 컨슈머에게 할당해준다.
		- 예시) C1: T1(0), T1(2), T2(1), C2: T1(1), T2(0), T2(2)
		- 만약 컨슈머간 구독해오는 토픽이 다른 경우 할당 불균형이 발생할 가능성이 있다.
			- C2가 T3를 구독하고 있으면 T3도 C2가 전담하는데, 라운드로빈도 동작하게된다.
			- https://velog.io/@hyun6ik/Apache-Kafka-Partition-Assignment-Strategy
	- Sticky(org.apache.kafka.clients.consumer.StickyAssignor)
		- Sticky 할당자는 파티션들을 가능한 한 균등하게 할당하고 리벨런스가 발생했을 때 기존의 할당을 최대한 유지하기 위한 목표를 가지고 있다.
		- Rounb Robin과 같이 동작하지만, C1이 C2에 비해 2개이상 적은 파티션이 할당되어져 있으면 C2에 할당되지 않는다.
		- 리밸런싱할 경우 RoundRobin의 경우 전체를 다시 순서대로 할당하는 반면에, Sticky는 기존 할당은 유지하면서, 나머지 부분을 재할당한다.
	- Cooperative Sticky(org.apache.kafka.clients.consumer.CooperativeStickyAssignor)
		- Sticky할당자와 기본적으로 동일하지만 협력적 리밸런싱을 지원한다.
- client.id(df: "")
	- 브로커가 요청을 보낸 클라이언트를 식별하는 id
- client.rack(df: "")
	- 클라이언트가 위치한 영역을 식별할 수 있게 해주는 설정 값
- group.instance.id(df: null)
	- 컨슈머에 정적 그룹 멤버십 기능을 적용하기 위해 사용되는 설정
- receive.buffer.bytes(df: 65536 (64 kibibytes)), send.buffer.bytes(df: 131072 (128 kibibytes))
	- 데이터를 읽거나 쓸 때 소켓이 사용하는 TCP의 수신 및 수신 버퍼의 크기
	- -1로 잡아 놓으면 운영체제 기본값 사용
	- 다른 데이터센터에 있는 브로커와 통신하는 프로듀서나 컨슈머의 경우 이 값을 올려 잡는게 좋음
		- 대체로 이러한 네트워크 회선은 지연을 크고 대역폭이 낮기 때문
- offsets.retention.minutes(df: 10080)
	- [컨플루언트 브로커 설정 Docs](https://docs.confluent.io/platform/current/installation/configuration/broker-configs.html)
	- 브로커 설정이지만 컨슈머 작동에 큰 영향을 끼침
	- 컨슈머 그룹이 각 파티션에 대해 커밋한 마지막 오프셋 값은 카프카에 의해 보존되기 때문에 재할당, 재시작을 한 경우에도 가져다 쓸 수 있다. 하지만 그룹이 비게 된다면 카프카는 커밋된 오프셋을  이 설정값에 지정된 기간 동안만 보관한다.
	- 커밋된 오프셋이 삭제된 상태에서 그룹이 다시 활동을 시작하면, 완전히 새로운 컨슈머 그룹인 것처럼 작동한다.

---

#### 오프셋과 커밋
- 카프카에서는 파티션에서의 현재 위치를 업데이트 하는 작업을 **오프셋 커밋** 이라고한다.
  > 카프카는 레코드를 개별적으로 커밋하지 않는다. 대신 컨슈머는 파티션에서 성공적으로 처리해 낸 마지막 메시지를 커밋함으로써 그 앞의 모든 메시지들 역시 성공적으로 처리되었음을 암묵적으로 나타낸다.
- 카프카에 특수 토픽인 `__consumer_offsets` 토픽에 각 파티션별로 커밋된 오프셋을 업데이트하도록 하는 메시지를 보냄으로써 이루어진다. 만약 컨슈머가 크래시 되거나 새로운 컨슈머가 추가될 경우 리밸런스가 발생하는데, 이전에 처리하던 파티션과 다른 파티션을 할당 받을 수 있다. 그래서 각 파티션의 마지막으로 커밋된 메시지를 읽어온 뒤 거기서부터 처리를 재개한다.
- p. 102 이후에 있는 예제 필요

1. 자동커밋
   - `enable.auto.commit을 true`로 잡아주면 컨슈머는 5초에 한 번, poll()을 통해 잡은 마지막 메시지의 오프셋을 커밋한다.
       - 5초는 기본 값으로 **auto.commit.interval.ms**으로 설정 해줄 수 있다.
   - 자동커밋은 매우 편리하지만 중복 메시지와 같은 문제가 발생할 수 있기 때문에, 동작에 대해 완벽하게 이해하고 사용하는 것이 중요하다.
       - 예시) 만약 파티션에 메시지 5를 컨슈머A에게 보내다가 컨슈머 B가 추가되면서 리밸런스되면, 파티션에 대한 마지막 커밋은 4로 되어 있기 때문에 컨슈머 B는 메시지 5을 가져오게 된다. 하지만 메시지 5는 컨슈머A에 이미 가져왔던 메시지로 중복될 수 있다.

2. 현재 오프셋 커밋하기(수동 커밋 - 동기)
	- `enable.auto.commit을 false`로 설정
	- `commitSync()` 메서드는 poll()이 마지막으로 리턴한 오프셋을 커밋한 뒤 성공적으로 완료되면 리턴, 실패하면 예외를 발생한다.
		- 만약 poll()에서 리턴된 모든 레코드의 처리가 완료되기 전에 `commitSync()`를 호출하게 되면 애플리케이션이 크래시되었을 때 커밋은 되었지만 아직 처리되지 않은 메시지들이 누락될 수 도 있다.
		- 또, 레코드를 처리하는 와중에 크래시가 발생하면 마지막 메시지 배치의 맨 앞 레코드 에서부터 리밸런스 시작 시점까지 모든 레코드가 두 번 처리될 수 도 있다.
	- 브로커가 커밋 요청에 응답할 때까지 애플리케이션이 블록된다는 단점도 존재한다. -> 데이터 처리량이 늦어질 수 있다.

3. 비동기적 커밋
	- `enable.auto.commit을 false`로 설정
	-  `commitAsync()` 메서드는 재시도를 하지 않는다.
		- 예시) 오프셋 2000을 커밋하는 요청을 보냈는데, 일시적인 통신 장애로 브로커가 해당 요청을 못 받았다. 그 사이 다른 배치를 처리한 뒤 성공적으로 오프셋 3000을 커밋한다. 이 시점에서 앞의 커밋을 재시도해서 성공한다면 3000까지 처리되서 커밋이 완료된 다음에 2000이 커밋되는 사태가 발생할 수 있다.
		- 순차적으로 단조증가하는 번호를 사용하여 비동기적 커밋을 재시도할 때 순서를 맞출 수 있다.
			- 커밋할 때마다 카운터를 1씩 증가하여 `commitAsync()` 콜백에 해당 번호를 넣음  -> 콜백에 주어진 번호와 현재 번호 비교
			- 콜백의 번호가 더 크면 재시도 아니면 진행

4. 동기적 커밋과 비동기적 커밋 함께 사용하기(p.108)
	- 컨슈머를 닫기 전 혹은 리밸런스 전 마지막 커밋일 때 추가확인을 할 수 있음
	- 일반적인 상황에서는 `commitAsync()`를 사용한다.
	- 컨슈머를 닫는 상황에서는 `commitSync()`를 사용하여 문제가 발생하면 재시도를 반복한다.

---

#### 리밸런스 리스너
- 컨슈머는 종료하기 전이나 리밸런싱이 시작되기 전에 정리 작업을 해줘야 함
- 컨슈머 API는 컨슈머에 파티션이 할당되거나 해제될 때 사용자의 코드가 실행되도록 하는 메커니즘을 제공
	- subscribe()를 호출할 때 ConsumerRebalanceListener를 전달하면 됨
	- ConsumerRebalance에는 3개의 메서드를 구현할 수 있음
- p. 111 및 [ConsumerRebalanceListener 구현 예시](https://velog.io/@on5949/Kafka-ConsumerRebalanceListener%EC%9D%98-%EC%98%AC%EB%B0%94%EB%A5%B8-%EA%B5%AC%ED%98%84) 예제 필요

1. onPartitionsAssigned
    - 파티션이 컨슈머에게 재할당된 후에 **컨슈머가 메시지를 읽기 시작하기 전**에 호출
    - 파티션과 함께 사용할 상태를 적재, 필요한 오프셋을 탐색하는 등의 준비 작업 수행
    - 컨슈머가 그룹에 문제없이 조인하려면, 모든 준비 작업은 **max.poll.timeout.ms** 안에 완료되어야 함
        - **max.poll.timeout.ms**이 **max.poll.interval.ms**를 말하는 걸까..?

2. onPartitionsRevoked
    - 컨슈머가 할당받았던 파티션이 **할당 해제될 때** 사용
    - **조급한** 리밸런스 알고리즘이 사용되었을 경우에는
        - 컨슈머가 메시지 읽기를 멈춘 뒤, 그리고 리밸런스가 시작되기 전에 호출됨
    - **협력적** 리밸런스 알고리즘이 사용되었을 경우에는
        - 메서드는 리밸런스가 완료될 때, **컨슈머에서 할당 해제되어야 할 파티션들에 대해서만 호출됨**
        - 여기서 오프셋을 커밋 해주어야 파티션을 다음에 할당받는 컨슈머가 시작할 지점을 알아낼 수 있다.

3. onPartitionsLost
	- 협력적 리밸런스 알고리즘이 사용되었을 경우, 할당된 파티션이 리밸런스 알고리즘에 의해 해제 되기 전에 다른 컨슈머에 먼저 할당된 예외적인 상황에서만 호출됨
	- 만약 이 메서드를 구현하지 않았을 경우, **onPartitionsRevoked**가 대신 호출됨

---

#### 특정 오프셋의 레코드 읽어오기
- **seekToBeginning**
	- 파티션의 맨 앞에서부터 모든 메시지 조회(오프셋을 파티션의 처음으로 이동)
- **seekToEnd**
	- 앞의 메시지는 전부 건너뛰고 파티션에 새로 들어온 메시지부터 읽기 시작(오프셋을 파티션 끝으로 이동)

---

#### 폴링 루프를 벗어나는법
- 컨슈머를 종료하고자 할 때, 컨슈머가 `poll()`을 오랫동안 기다리고 있더라고 즉시 루프를 탈출하고 싶다면 다른 스레드에서 `consumer.wakeup()`를 활용
- 이는 `poll()`이 `WakeupException`을 발생시키며 중단되거나, 대기중이 아닐 경우에는 다음 번에 처음으로 `poll()`을 호출할 때 예외를 발생시킴
	- `WakeupException`를 딱히 처리해 줄 필요는 없지만, `consumer.close`는 호출해야함

---

#### 독립 실행 컨슈머
- 컨슈머 그룹은 컨슈머들에게 파티션을 자동으로 할당해주고, 리밸런싱해주고, 스케일 아웃까지 제공함
- 하지만 하나의 컨슈머가 토픽의 모든 파티션으로부터 데이터를 읽어와야 하거나 토픽의 특정 파티션으로부터 데이터를 읽어야할 경우, 컨슈머 그룹이나 리밸런스가 필요하지 않음
- p. 122 예제 필요

---

[참고자료]
- [컨플루언트 컨슈머 설정 docs](https://docs.confluent.io/platform/current/installation/configuration/consumer-configs.html)
- [컨플루언트 브로커 설정 Docs](https://docs.confluent.io/platform/current/installation/configuration/broker-configs.html)
- https://velog.io/@hyun6ik/Apache-Kafka-Partition-Assignment-Strategy
- [컨슈머 리밸런싱](https://baebalja.tistory.com/628)
- https://www.conduktor.io/kafka/kafka-consumer-important-settings-poll-and-internal-threads-behavior/#Kafka-Consumer-Fetch-Behavior-1

---