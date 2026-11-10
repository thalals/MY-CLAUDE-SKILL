# Kafka·DynamoDB

> 읽는 때: Kafka 발행·소비, Avro, DynamoDB 엔티티를 다룰 때. 색인은 `index.md`.

### 설계 원칙·Entity·Repository (보강 1 · 최근 10-28, 병합 2 · 최근 11-10)
- Access Pattern 표를 먼저 정의하고 Key 설계. 싱글 테이블(PK prefix 로 Entity 구분), TTL 은 필요한 경우에만
- 같은 테이블에 새 관심사(대기 목록 등)를 두면 기존 엔티티에 status 값·필드를 추가하지 않고 PK prefix 가 다른 별도 엔티티 클래스로 — 없는 상태 enum 을 만들지 않는다
- 중복 수집 방지 마커(수집 완료 레코드)는 최초 수집 시점에 대기 레코드와 함께 1회 기록 — 후속 스케줄러는 발행 + 자기 레코드 삭제만, 마커를 다시 쓰지 않는다. 쓰기 순서는 대기 → 마커, 삭제는 발행 성공 뒤
- `@DynamoDbBean` + `@DynamoDbPartitionKey`/`@DynamoDbSortKey`, `@DynamoDbAttribute("snake_case")`. 커스텀 타입은 `@DynamoDbConvertedBy` + `AttributeConverter`(Spring Bean 주입 불가 — 리플렉션 직접 생성)
- `DynamoDbEnhancedClient` + `DynamoDbTable`. 조회 `QueryConditional.keyEqualTo()`/`getItem(Key)`, 저장 `putItem`, 삭제 `deleteItem(Key)`

### Avro·토픽 — Update vs Updated 구분 (2026-04-16, 병합 1 · 최근 10-28)
- Schema `src/main/avro/{domain}/`, Enum 은 String 으로 정의(Kotlin 에서 변환), `newBuilder().setXX().build()`. 토픽은 `{domain}.updated` 형식 — 도메인 액션 기반, 시스템별 네이밍 금지
- `{domain}.update`(인바운드, Consumer 수신) ≠ `{domain}.updated`(아웃바운드, Producer 발행) — Avro 스키마도 별개(`XxxUpdateMessage` vs `XxxUpdatedMessage`). 사용자가 정확한 클래스명을 언급하면 그 이름 그대로 검색(자동 보정 금지), 발행 시 토픽 프로퍼티도 검증
- **왜:** 필드 구성·발행 토픽이 다르다 — 유사 이름 혼동은 잘못된 흐름 발행으로 이어진다

### 선후 의존이 있는 두 발행은 토픽 간 순서 설계 대신 선행을 동기 REST 로 끝내고 발행 (2026-11-02)
- 수신측이 X 를 먼저 반영해야 Y 가 올바르게 처리되는데(예: 취소 반영 뒤 수집) X·Y 가 다른 토픽이면 순서 장치(폴링 게이트, 새 이벤트 타입 + 컨슈머 트랜잭션 재구성)를 만들지 않는다 — X 를 수신측 동기 API 로 호출해 응답을 받은 뒤 Y 를 발행. 수신측 API 가 없으면 호출 자리를 todo 주석 placeholder 로 두고 API 추가는 별도 단계로
- 수신측 API 는 "응답 = 반영 완료" 가 성립해야 한다 — 저장과 상태 전이를 같은 트랜잭션에서 동기 처리(비동기 리스너면 응답 뒤에도 경합 창이 남는다), 요청 식별자로 멱등
- **왜:** 다른 토픽·리스너 사이에 Kafka 는 순서를 보장하지 않고, 순서 장치는 시간 가정이거나 양쪽 변경이 큰 구조다 — 동기 호출 한 번이 가장 단순한 인과 보장. "상태변경=Kafka" 원칙의 예외는 후행 발행이 선행 결과에 의존할 때
