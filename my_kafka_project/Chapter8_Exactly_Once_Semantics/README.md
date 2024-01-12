## **정확히 한 번** 의미 구조

카프카의 **정확히 한 번** 의미 구조는 두 개의 핵심 기능인 <span style='color:#f7b731'>멱등적 프로듀서(idempotent producer)</span>와 <span style='color:#f7b731'>트랜잭션 의미 구조</span>의 조합으로 이루어 진다.

- **멱등적 프로듀서**는 재시도로 인해 발생하는<span style='color:#f7b731'> 중복을 방지</span>한다.
- **트랜잭션 의미 구조**는 스트림 처리 애플리케이션에서 <span style='color:#f7b731'>정확히 한 번 처리를 보장</span>한다.



### 멱등적 프로듀서

동일한 작업을 여러 번 실행해도 한번 실행한 것과 같은 결과가 같은 서비스를 **멱등적**이라고 한다. 데이터베이스에서는 흔히 다음과 같이 설명한다.

1. `UPDATE t SET x=x+1 where y=5
	- 멱등적이지 않음. 1을 세 번 호출하면 한 번 호출한 것과 결과가 다르다.
2. `UPDATE t SET x=18 where y=5`
	- 멱등적이다. 몇 번을 호출하든 x는 18이다.


카프카 프로듀서는 <span style='color:#f7b731'>멱등성 의미 구조가 아닌 최소 한 번의 의미 구조를 가지도록 프로듀서를 설정한다면</span>, 프로듀서가 메시지 전송을 재시도함으로써 메시지가 최소 한 번 이상 도착할 수 있는 불확실성이 존재하게 된다. 즉, **중복을 발생**시킬 수 있다. 이것의 고전적인 예시는 다음과 같이 설명할 수 있다.

1. 파티션 리더가 프로듀서로부터 레코드를 받아서 팔로워들에게 성공적으로 복제한다.
2. 프로듀서에게 응답을 보내기 전, 파티션 리더가 있는 브로커에 크래시가 발생한다.
3. 프로듀서 입장에서는 응답을 받지 못한 채 타임아웃이 발생하고, 메시지를 재전송한다.
4. 재전송된 메시지가 새 리더에게 도착하는데, 이 메시지는 이미 저장되어져 있다.

카프카의 멱등적 프로듀서 기능은 자동으로 이러한 중복을 탐지하고 처리함으로써 이 문제를 해결한다.


#### 멱등적 프로듀서의 작동 원리

1. 멱등적 프로듀서 기능을 키면 모든 메시지는 고유한 **프로듀서 ID(producer ID, PID)** 와 **시퀀스 넘버(sequence ID)** 를 가지게 된다.
2. <span style='color:#f7b731'>대상 토픽 및 파티션과 이 두 값을 합치면</span> 각 메시지의 **고유한 식별자**가 된다.
3. 각 브로커는 해당 브로커에 할당된 모든 파티션들에 쓰여진 마지막 5개 메시지들을 추적하기 위해 이 고유 식별자를 사용한다.
	- 파티션별로 추적되어야 하는 시퀀스 넘버의 수를 제한하고 싶다면 프로듀서의 `max.in.flights.requests.per.connection` 설정 값이 5 이하로 잡혀 있어야 한다.
4. 브로커가 예전에 받은 적이 있는 메시지를 받게 될 경우, 적절한 에러를 발생시킴으로써 중복 메시지를 거부한다.
	- 이 에러는 프로듀서에 로깅도 되고 지푯값에도 반영되지만, 예외가 발생한 것은 아니기 때문에 사용자에게 정보를 보내지는 않는다.
	- 프로듀서 클라이언트에서는 <span style='color:#f7b731'>record-error-rate 지푯값</span>을 확인함으로써 에러를 확인할 수 있다.
5. 만약 브로커가 예상보다 높은 시퀀스 넘버를 받게 된다면, <mark style='background:#8854d0'>'out of order sequence number'</mark> 에러를 발생시킨다.
	- 트랜잭션 기능 없이 멱등적 프로듀서만 사용하고 있다면 이 에러는 무시해도 된다.

 > <mark style='background:#8854d0'>'out of order sequence number'</mark> 에러가 발생한 뒤에도 프로듀서가 정상 작동한다면, 이 에러는 보통 프로듀서와 브로커 사이에 메시지 유실이 있었음을 의미한다. 만약 브로커가 2번 메시지 다음 27번을 받았다면, 3번 부터 26번까지 뭔가가 일어난 것이다. 로그에 이러한 에러가 찍혀있다면, **프로듀서와 브로커 설정을 재점검**하고 **프로듀서 설정이 고신뢰성을 위해 권장되는 값으로 잡혀있는지**, 아니면 **언클린 리더 선출이 발생했는지** 여부를 확인해야한다.



작동이 실패했을 경우 멱등적 프로듀서가 어떻게 처리하는지 다음 경우로 예를 들어보자.

1️⃣ **프로듀서 재시작**

- 프로듀서에 장애가 발생할 경우, 보통 <span style='color:#f7b731'>새 프로듀서를 생성해서 장애가 난 프로듀서를 대체</span>한다.
- 프로듀서가 시작될 때 <span style='color:#f7b731'>멱등적 프로듀서 기능이 켜져 있을 경우</span>, 프로듀서는 초기화 과정에서 카프카 브로커로부터 **프로듀서 ID를 생성**한다.
- 트랜잭션 기능을 켜지 않았을 경우, 프로듀서를 초기화할 때마다 **완전히 새로운 ID를 생성**한다. 즉, 프로듀서에 장애가 발생해서 대신 투입된 새 프로듀서가 기존 프로듀서가 이미 전송한 메시지를 다시 전송할 경우, <span style='color:#f7b731'>브로커는 메시지에 중복이 발생했음을 알아채지 못한다.</span>
	- 두 메시지가 **서로 다른 프로듀서 ID**와 **시퀀스 넘버**를 갖는 만큼 서로 다른 것으로 취급한다.


2️⃣ **브로커 장애**

브로커 장애가 발생할 경우, 컨트롤러는 장애가 난 브로커가 리더를 맡고 있었던 파티션들에 대해 **새 리더를 선출**한다. 그렇다면 새 리더는  어느 시퀀스 넘버까지 쓰였는지 어떻게 알까?

1. 리더는 새 메시지가 쓰여질 때마다 인-메모리 프로듀서 상태에 저장된 **최근 5개의 시퀀스 넘버를 업데이트**한다.
2. 팔로워는 <span style='color:#f7b731'>리더로부터 새로운 메시지를 복제할 때마다</span> **자체적인 인-메모리 버퍼를 업데이트**한다. 즉, 팔로워가 리더가 된 시점에는 이미 메모리 안에 최근 5개의 시퀀스 넘버를 가지고 있다.
3. 따라서 아무 이슈나 지연 없이, 새로 쓰여진 메시지의 유효성 검증이 재개될 수 있는 것이다.

하지만, 여기서 예전 리더가 다시 돌아온다면 어떤 일이 벌어질까?

1. <span style='color:#f7b731'>브로커는 종료되거나 새 세그먼트가 생성될 때마다</span> **프로듀서 상태에 대한 스냅샷을 파일 형태로 저장**한다.
2. 브로커가 시작되면 일단 파일에서 최신 상태를 읽어 온다.
3. 현재 리더로부터 복제한 레코드를 사용해서 **프로듀서 상태를 업데이트 함으로써 최신 상태를 복구**한다.
4. 그래서 이 브로커가 다시 리더를 맡을 준비가 될 시점에는 시퀀스 넘버를 가지고 있게 된다.

만약 브로커가 크래시 나서 최신 스냅샷이 업데이트되지 않는다면 어떻게 될까?

1. **프로듀서 ID**와 **시퀀스 넘버**는 둘 다 <span style='color:#f7b731'>카프카 로그에 저장되는 메시지 형식의 일부</span>다. 
2. 크래시 복구 작업이 진행되는 동안 프로듀서 상태는 더 오래 된 스냅샷뿐만 아니라 각 파티션 최신 세그먼트의 메시지들 역시 사용해서 복구된다.
3. 복구 작업이 완료되는 대로 **새로운 스냅샷 파일이 저장**된다.

만약 메시지가 없다면 어떻게 될까?

1. 보존 기한은 2시간인데 지난 두 시간동안 메시지가 하나도 들어오지 않은 토픽이 있다.(브로커가 크래시 날 경우, 프로듀서 상태를 복구하기 위해 사용할 수 있는 메시지 역시 없을 것이다.)
2. 다행히 **메시지가 없다는 얘기는 중복이 없다는 얘기**이다.
3. 이 경우 즉시 새 매시지를 받기 시작해서 새로 들어오는 메시지들을 기준으로 프로듀서 상태를 생성할 수 있다.


#### 멱등적 프로듀서의 한계

- 카프카의 멱등적 프로듀서의 내부 로직으로 인한 재시도가 발생할 경우 생기는 중복만을 방지한다.
- 동일한 메시지를 가지고 `producer.send()`를 두 번 호출하면 멱등적 프로듀서가 개입 하지 않는 만큼 중복된 메시지가 생기게 된다.
- 여러 개의 인스턴스를 띄우거나 하나의 인스턴스에서 여러 개의 프로듀서를 띄웠을 때, 이러한 프로듀서들 중 두 개가 동일한 메시지를 전송하려 시도할 경우, 멱등적 프로듀서는 중복을 잡아내지 못한다.

> 멱등적 프로듀서는 **프로듀서 자체의 재시도 메커니즘(프로듀서, 네트워크, 브로커 에러로 인해 발생하는)** 에 의한 중복만을 방지할 뿐, 그 이상은 하지 않는다.


#### 멱등적 프로듀서 사용법

프로듀서 설정에 `enable.idempotence=true`를 추가해준다.

- 만약 프로듀서에 `acks=all`설정이 이미 잡혀 있다면, 성능에는 큰 차이가 없을 것이다.
- Kafka 3.0 이후로는 defalut가 true이다.


멱등성 프로듀서 기능을 활성화시키면 바뀌는 것들

- 프로듀서 ID를 받아오기 위해 프로듀서 시동 과정에서 API를 하나 더 호출한다.
- 전송되는 각각의 레코드 배치에는 **프로듀서 ID와 배치 내 첫 메시지의 시퀀스 넘버가 포함**된다.
	- 각 메시지의 시퀀스 넘버는 첫 메시지의 시퀀스 넘버에 변화량을 더하면 나온다.
	- 이 새 필드들은 각 메시지에 96비트를 추가한다. 따라서 <span style='color:#f7b731'>대부분의 경우 작업 부하에 어떠한 오버헤드도 되지 않는다.</span>
		- 프로듀서 ID는 long 타입이고, 시퀀스 넘버는 integer 타입이다.
- 브로커들은 모든 프로듀서 인스턴스에서 들어온 레코드 배치의 **시퀀스 넘버를 검증해서 메시지 중복을 방지**한다.
- 장애가 발생하더라도 각 파티션에 쓰여지는 메시지들의 순서는 보장된다.



### 트랜잭션


카프카의 트랜잭션 기능은<span style='color:#f7b731'> 스트림 처리 애플리케이션을 위해 특별히 개발</span>되었다. 즉 스트림 처리 애플리케이션의 기본 패턴인 **읽기-처리-쓰기 패턴**에서 사용되도록 개발되었다.


#### 트랜잭션이 해결하는 문제

트랜잭션이 해결해야하는 문제가 어떤것이 있을 수 있을까?


1️⃣ **애플리케이션 크래시로 인한 처리**

원본 클러스터로부터 메시지를 읽어서 처리한 뒤 애플리케이션은 두 가지를 해야하는데, 하나는 **결과를 출력 토픽에 쓰는 것**이고 다른 하나는 **우리가 읽어 온 메시지의 오프셋을 커밋**한다.

컨슈머가 크래시 날 경우 리밸런스가 발생하고, 컨슈머가 읽어오고 있던 파티션들은 다른 컨슈머로 재할당된다.  컨슈머는 새로 할당된 파티션의 마지막으로 커밋된 오프셋으로부터 레코드를 읽어 온다. 즉, 마지막으로 커밋된 오프셋에서부터 크래시가 난 시점까지 애플리케이션에 처리된 모든 레코드들은 다시 처리되어 결과 역시 출력토픽에 다시 쓰여지기 때문에 **중복이 발생**할 수 있다.


2️⃣ **좀비 애플리케이션에 의해 발생하는 재처리**

좀비는 출력 토픽으로 데이터를 쓸 수 있으며 **중복된 결과가 발생**할 수 있다.


#### 트랜잭션은 어떻게 **정확히 한 번**을 보장 할까?

- 트랜잭션을 사용해서 **원자적 다수 파티션 쓰기**를 수행하려면 **트랜잭션적 프로듀서**를 사용해야 한다. 
	- 트랜잭션적 프로듀서와 일반 프로듀서의 차이는 `transactional.id` 설정이 잡혀 있고 `initTransactions()`을 호출해서 초기화해주는것 밖에 없다.
	- `transactional.id`의 주 용도는 재시작 후에도 동일한 프로듀서를 식별하는 것이다.
	- `producer.id`와는 달리 `transactional.id`는 프로듀서 설정의 일부이고 재시작을 하더라도 값이 유지된다.
- 카프카 브로커는 `transactional.id`에서 `producer.id`로의 대응관계를 유지하다가 만약 이미 있는 `transactional.id` 프로듀서가 `initTransactions()`를 다시 호출하면 <span style='color:#f7b731'>새로운 랜덤 값이 아닌 이전에 쓰던</span> **producer.id** 값을 할당해 준다.


애플리케이션의 <span style='color:#f7b731'>좀비 인스턴스가 중복 프로듀서를 생성하는 것을 방지</span>하려면 **좀비 펜싱(zombie fencing)** 혹은 애플리케이션의 **좀비 인스턴스가 출력 스트림에 결과를 쓰는 것**을 방지할 필요가 있다.


가장 일반적인 좀비 펜싱 방법인 에포크를 사용하는 방법이 쓰인다.

1. 카프카는 트랜잭션적 프로듀서가 초기화를 위해 `initTransactions()`를 호출하면 `transactional.id`에 해당하는 에포크 값을 증가시킨다.
2. 같은 `transactional.id`를 가지고 있지만 **에포크 값이 낮은 프로듀서**가 <span style='color:#f7b731'>메시지 전송, 트랜잭션 커밋, 트랜잭션 중단 요청</span>을 보낼 경우 FenceProducer에러가 발생한다. ➡️ 즉, 좀비가 중복 레코드를 쓰는것이 불가능 하다.


`isolation.level` 설정 값으로 트랜잭션 기능을 써서 쓰여진 메시지들을 읽어오는 방식을 제어할 수 있다.

- `isolation.level=read_committed`일 경우
	- 토픽들을 구독한 뒤 `consumer.poll()`을 호출하면 **커밋된 트랙잭션에 속한 메시지**나 **처음부터 트랜잭션에 속하지 않는 메시지**만 리턴된다.
	- 메시지 읽기 순서를 보장하기 위해 이 모드에서는 아직 진행중인 트랜잭션이 **처음으로 시작된 시점(Last Stable Offset, LSO)** 이후에 쓰여진 메시지는 리턴되지 않는다.
		- 이 메시지들은 트랜잭션이 프로듀서에 의해 커밋되거나 중단될 때까지, 혹은 `transaction.timeout.ms` 설정값만큼 시간이 지나 브로커가 트랜잭션을 중단시킬 때까지 보류된다.
		- <span style='color:#f7b731'>이렇게 트랜잭션이 오랫동안 닫히지 않고 있으면 컨슈머들이 지체되면서 종단 지연이 길어진다.</span>
- `isolation.level=read_uncommitted`일 경우
	- 진행중이거나 중단 된 트랜잭션에 속하는 것들 포함, 모든 레코드가 리턴된다.


스트림 처리 애플리케이션은 입력 토픽이 트랜잭션 없이 쓰여졌을 경우에도 **정확히 한 번** 출력을 보장한다. **원자적 다수 파티션 쓰기 기능**은 <span style='color:#f7b731'>만약 출력 레코드가 출력 토픽에 커밋되었을 경우</span>, <span style='color:#f7b731'>입력 레코드의 오프셋 역시 해당 컨슈머에 대해 커밋되는 것을 보장</span>한다. 결과적으로 입력 레코드는 다시 처리되지 않는다.


#### 트랜잭션으로 해결할 수 없는 문제들

카프카의 트랜잭션 기능은 <span style='color:#f7b731'>다수의 파티션에 대한 원자적 쓰기 기능을 제공</span>하고 스트림 처리 애플리케이션에서 <span style='color:#f7b731'>좀비 프로듀서를 방지하기 위한 목적</span>으로 추가되었다.

카프카의 트랜잭션 기능은 다음과 같은 상황의 **정확히 한 번**은 보장하지 못한다.

1️⃣ **스트림 처리에 있어서의 부수 효과**

스트림 처리 애플리케이션의 처리 단계에 사용자에 이메일을 보내는 작업이 포함되어져 있다고 했을때, **정확히 한 번** 의미 구조를 활성화해도 <span style='color:#f7b731'>카프카에 쓰여지는 레코드에만 적용되는 것</span>이기 때문에, 해당 이메일이 한 번만 발송되지 않는다.


2️⃣ **카프카 토픽에서 읽어서 데이터베이스에 쓰는 경우**

하나의 트랜잭션에서 외부 데이터베이스에는 결과를 쓰고, 카프카에는 오프셋을 커밋할 수 있도록 해주는 메커니즘은 없다. 
- 대신 4장에서 설명한 것처럼 오프셋을 데이터베이스에 저장하도록 할 수는 있다.
- 이렇게 하면 하나의 트랜잭션에서 데이터와 오프셋을 동시에 데이터베이스에 커밋할 수 있다.

> 마이크로서비스에는 하나의 원자적 트랜잭션 안에서 데이터베이스도 업데이트하고 카프카에 메시지도 써야 하는 경우가 종종 있다. 이것을 해결하기 위해 **아웃박스 패턴(outbox pattern)** 이 있다. 마이크로서비스는 <span style='color:#f7b731'>아웃박스라고 불리는 카프카 토픽에 메시지를 쓰는 작업까지만 하고, 별도의 메시지 중계 서비스가 카프카로부터 메시지를 읽어와서 데이터베이스를 업데이트</span>한다.


3️⃣ **데이터베이스에서 읽어서, 카프카에 쓰고, 여기서 다시 다른 데이터베이스에 쓰는 경우**

- 카프카 트랜잭션은 **종단 보장(end-to-end -guarantee)** 에 필요한 기능을 가지고 있지 않다.
	- 트랜잭션이 너무 오래 켜져있어서 종단 보장이 안된다는 뜻인가?
- 트랜잭션의 <span style='color:#f7b731'>경계를 알 수 있는 방법이 없기 때문에</span> 언제 트랜잭션이 시작되었는지, 끝났는지, 레코드 중 어느 정도를 읽었는지 알 수 없다.


4️⃣ **한 클러스터에서 다른 클러스터로 데이터 복제**

- 하나의 클러스터에서 다른 클러스터로 데이터를 복사할 때 **미러메이커 2.0**을 이용하면 <span style='color:#f7b731'>‘정확히 한 번’을 보장</span>할 수 있지만 이것이 트랜잭션의 원자성을 보장하지는 않는다.
- 만약 어플리케이션이 여러 개의 레코드와 오프셋을 트랜잭션적으로 쓰고, 미러메이커 2.0이 이 레코드들을 다른 카프카 클러스터에 복사한다면, 복사 과정에서 트랜잭션 속성이나 보장 같은 것은 유실된다.


5️⃣ **발행/구독 패턴**

- 발행/구독 패턴에서 read_committed 모드가 설정된 컨슈머들은 중단된 트랜잭션에 속한 레코드들을 보지 못한다. 오프셋 커밋 로직이 어떻게 되어있는지에 따라 컨슈머들은 메시지를 한 번 이상 처리할 가능성이 존재한다.


#### 트랜잭션 ID와 펜싱

아파치 카프카 2.5부터 트랜잭션 ID와 컨슈머 그룹 메타데이터를 함께 사용하는 펜싱을 도입하였다. 프로듀서의 오프셋 커밋 메서드를 호출할 때 단순한 컨슈머 그룹 ID가 아닌, 컨슈머 그룹 메타데이터를 인수로 전달한다.

- 추가


#### 트랜잭션의 작동 원리

- 카프카 트랜잭션 기능의 기본적인 알고리즘은 **찬디-램포트 스냅샷(Chandy-Lamport snapshot)** 의 영향을 받았다. 
	- 찬디-램포트 스냅샷 알고리즘은 통신 채널을 통해 **마커(marker)** 라 불리는 컨트롤 메시지를 보내고, 이 마커의 도착을 기준으로 일관적인 상태를 결정한다.
- 카프카의 트랜잭션은 다수의 파티션에 대해 <span style='color:#f7b731'>트랜잭션이 커밋되었거나 중단된 것을 표시하기 위해</span> 마커 메시지를 사용한다.

일부 파티션에만 커밋 메시지가 쓰여진 상태에서 프로듀서가 크래시 날 경우를 대비하기 위해 카프카 트랜잭션은 2단계 커밋과 트랜잭션 로그를 사용해서 이 문제를 해결했다.

1. 현재 진행중인 트랜잭션이 존재함을 로그에 기록한다. 연관된 파티션들 역시 함께 기록한다.
2. 로그에 커밋 혹은 중단 시도를 기록한다.
3. 모든 파티션에 트랜잭션 마커를 쓴다.
4. 트랜잭션이 종료됨을 로그에 쓴다.

위의 단계를 **Chapter 8 p. 218에 있는 코드**의 트랜잭션 API 호출의 내부를 따라가면서, <span style='color:#f7b731'>알고리즘이 실제로 동작하는 원리</span>를 살펴보자.

> 트랜잭션을 사용하기 위해서는 enable.auto.commit 옵션은 꼭 꺼야한다! `setOffsetsToTransaction` 를 사용해서 커밋을 한다.

<span style='color:#eb3b5a'>블로그 글쓸 때 책에 예제말고도 컨플루언트 파이썬 예제를 사용해서 글쓰자!</span>

1. 트랜잭션을 시작하기 전에, 프로듀서는 `initTransaction()`를 호출해서 <span style='color:#f7b731'>트랜잭션 프로듀서임을 등록</span>한다.
	1. 이 요청을 이 트랜잭션 프로듀서의 트랜잭션 코디네이터 역할을 맡을 브로커로 보내면, 각 브로커는 전체 프로듀서의 트랜잭션 코디네이터 역할을 나눠서 맡는다.
	2. **각 트랜잭션 코디네이터**는 트랜잭션 ID에 해당하는 <span style='color:#f7b731'>트랜잭션 로그 파티션의 리더 브로커가 맡는다.</span>
2. `initTransaction()` API 는 <span style='color:#f7b731'>코디네이터에 새 트랜잭션 ID 를 등록</span>하거나, <span style='color:#f7b731'>기존 트랜잭션 ID의 에포크 값을 증가</span>시킨다.
	1. 에포크 값을 증가시킴으로써 <span style='color:#f7b731'>좀비가 되었을 수 있는 기존 프로듀서들을 펜싱</span>한다.
3. `beginTensaction()`을 호출하여 프로듀서에 현재 진행중인 트랜잭션이 있음을 알려준다.
4. 브로커 쪽의 트랜잭션 코디네이터는 여전히 트랜잭션이 시작됨을 모른다.
5. <span style='color:#f7b731'>프로듀서가 새로운 파티션에 레코드를 전송할 때 마다</span> 브로커에 `AddPartitionsToTxn` 요청을 보냄으로써 현재 <span style='color:#f7b731'>이 프로듀서에 진행중인 프로듀서가 있음</span>을 알린다. 
	1. 이 정보는 트랜잭션 로그에 기록된다.
6. 트랜잭션이 커밋되기 전에 이 트랜잭션에서 처리한 레코드들의 오프셋부터 커밋한다.
	1. `setOffsetsToTransaction()`을 호출하면 <span style='color:#f7b731'>트랜잭션 코디네이터로 오프셋과 컨슈머 그룹 ID가 포함된 요청이 전송</span>된다.
	2. 트랜잭션 코디네이터는 컨슈머 그룹 ID로 컨슈머 그룹 코디네이터를 찾고 오프셋을 커밋한다.
7. `commitTransaction()`이나 `abortTransaction()`을 호출하여 트랜잭션 코디네이터에 <span style='color:#f7b731'>EndTxn 요청을 전송</span>한다.
	1. **`abortTransaction`**: 현재 진행 중인 트랜잭션을 취소하고, 모든 이전에 발행된 메시지들을 롤백한다.
	2. **`commitTransaction` (트랜잭션 커밋):** 현재 진행 중인 트랜잭션을 커밋하며, 트랜잭션 내에서 발행된 모든 메시지를 실제로 Kafka에 반영한다.
8. 트랜잭션 코디네이터는 <span style='color:#f7b731'>트랜잭션 로그에 커밋 혹은 중단 시도를 기록</span>한다.
9. 트랜잭션 코디네이터는 <span style='color:#f7b731'>트랜잭션에 포함된 모든 파티션에 커밋 마커</span>를 쓴 다음 트랜잭션 <span style='color:#f7b731'>로그에 커밋이 성공되었음을 기록</span>한다.
	1. 만약 커밋 시도는 로그에 기록되었지만 전체 과정이 완료되기 전에 트랜잭션 코디네이터가 종료되거나 크래시 날 경우, 새 트랜잭션 코디네이터가 선출되어 로그에 대한 커밋 작업을 대신 마무리한다.
	2. 만약 트랜잭션이 `transaction.timeout.ms`에 <span style='color:#f7b731'>설정된 시간 내에 커밋되지도, 중단되지도 않는다면</span> 트랜잭션 코디네이터는 자동으로 **트랜잭션을 중단**한다.


### 트랜잭션 성능

- 트랜잭션은 프로듀서에 약간의 오버헤드를 발생시킨다.
- 프로듀서에 있어서 트랜잭션 오버헤드는 트랜잭션에 포함된 메시지 수와는 무관하다.
	- 트랜잭션마다 맣은 수의 메시지를 집어넣는 것이 상대적으로 오버헤드가 적으며, 동기적으로 실행되는 단계의 수도 줄어든다. 결과적으로 처리량이 증가한다.
- 컨슈머에서는 커밋 마커를 읽어올 때 약간의 오버헤드가 있다.
	- read_committed 모드