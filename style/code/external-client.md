# 외부 시스템 연동

> 읽는 때: 외부 API 클라이언트·DTO·Admin/Schedule API·Mock 을 만들거나 고칠 때. 색인은 `index.md`.

### RestClient 구성·baseUrl·인코딩 (2026-04-16, 병합 1 · 최근 10-28)
- `@HttpExchange` interface + `HttpServiceProxyFactory`, `JdkClientHttpRequestFactory`(Virtual Thread). `ExternalClientLogger.log()` 로깅 interceptor(예외 시에도), `ExternalInterfaceException` 에러 핸들러
- `@GetExchange` 에 API 전체 경로 명시, baseUrl 은 도메인만 — URL 경로 중복 같은 설정 문제는 코드(`@GetExchange` 경로)로 우회하지 않고 env 파일을 수정(코드를 바꾸면 API 스펙 정의가 왜곡된다)
- EUC-KR 같은 비표준 인코딩 확인 필수 — interceptor 로깅도 response charset 에 맞게 디코딩

### 브랜드/법인별 추상화 (2026-04-16, 보강 1 · 최근 09-08, 병합 1 · 최근 11-10)
- Properties: `Map<BrandType, Config>` 패턴, 단일 브랜드로 시작해도 브랜드별 구조. Properties 는 순수 데이터 클래스 — reverse map/역방향 조회 메서드를 넣지 않고 조회 로직은 사용처에
- 법인마다 정책이 다른 값 결정(배송 서비스 코드 매핑)의 최상위 분기 축은 carrier 같은 기술 축이 아니라 법인(corporation), carrier 선택은 별도 결정 지점(enum/selector)으로 — 정책의 소유 주체는 비즈니스 주체라 기술 축으로 분기하면 법인별 차이를 표현할 곳이 없다

### 외부 연동 silent 실패 함정 — 응답 body 의 ok/status 필드, ShedLock 의 LockProvider 의존 (2026-05-13, 병합 1 · 최근 11-10)
- **응답 검증:** Slack 등 다수 API 는 HTTP 200 + `body.ok = false` 로 실패를 알린다 — `isSuccessful` 만 검사하면 silent fail. ①HTTP status ②body 의 `ok`/`status`/`success` 둘 다 통과해야 성공, 실패는 println 이 아니라 `logger.error`
- **ShedLock:** `@SchedulerLock` 이 있어도 Provider(Hazelcast)가 클러스터 형성에 실패하면 락이 JVM 로컬로 silent degrade → 전 인스턴스가 락 획득 → N중 실행
- 점검: ①부팅 로그 `Members {size:N}` 가 인스턴스 수와 같은지(size:1 이면 standalone) ②정확성 critical 하면 fail-loud Provider(DynamoDB/Redis) 검토 ③진입 시점 `cluster.members.size`+IP 임시 로그로 실측 ④실행 카운트 모니터링 — 어노테이션·Bean 만 보면 정상처럼 보인다

### ClientSelector — 현재 시스템의 데이터 구조에서 도출 (2026-05-28)
- Selector 작성 전 ①Properties 의 key 별 필드가 RestClient 설정에 흡수되는지/외부 참조가 필요한지 ②노출 범위(client 만 vs 메타 포함) ③부가 책임(검증/매핑) ④호출부 사용 패턴을 분석해 가장 단순한 형태(`select(key): Client` / 래퍼 / service 형)를 도출 — 다른 시스템의 Selector 모양을 그대로 따르지 않는다(dead field 만 남는다)

### 외부 API DTO 필드는 도메인 이름 + 어노테이션으로 원본 매핑 (2026-05-28, 보강 3 · 최근 10-29)
- body/`@RequestParam`/`@PathVariable` 모두 Kotlin 이름은 의미 있는 도메인 이름(`stDate` → `startDate`), 외부 원본명은 어노테이션(`@field:JsonProperty("orderIds")`) — 이름이 완전히 같으면 어노테이션 생략. 외부 발급 식별자는 `origin{Resource}{Id|No}` prefix 로 기존 도메인 식별자명과 통일
- `.http` 요청 변수명도 같은 식별자명 그대로 — 행위 prefix 없이 기존 http 파일 변수명에 맞춘다
- `origin` 앞에 출처 한정어(`source~`)를 겹치지 않는다 — 한정어 없는 `origin{Resource}{Concept}` 로, 같은 외부 개념은 응답·요청·저장 VO 에서 한 이름으로
- **왜:** 외부마다 다른 식별자명에 도메인이 종속되면 시스템 추가 시 전체 수정 — origin prefix 가 "외부 발급"을 즉시 알린다

### MockController 응답은 실 응답 예시 기반 + 식별자 분기 (2026-05-28)
- 실 응답 예시를 companion object 의 const JSON 으로, `when (식별자)` 분기로 케이스별 반환(else 기본 케이스 포함). 반환 타입 `String` + `produces = APPLICATION_JSON_VALUE` — DTO 미매핑 필드도 실 응답 그대로 보존. 예시 N개를 받으면 N개 모두 분기로 — 식별자만 바꿔 시나리오 재현 가능해야 한다

### Facade 는 트랜잭션 분리가 필요할 때만 — 평소엔 시스템 단위 Service, 외부로 나가는 Internal API 응답은 전용 Response DTO (2026-06-09, 보강 2 · 최근 07-10, 병합 2 · 최근 11-10)
- 도메인 경계가 모호한 프로젝트에서 새 행위(재고/주문/클레임)는 기존 `{System}Service` 에 메서드 추가 — `{System}{Behavior}Service` 사전 분할 금지(책임 비대가 명확해진 시점에). DB 트랜잭션을 거는 도메인이 아니면 Facade 도 불필요 — 외부 연동/수집은 `{System}Service` 에 바로
- Facade 는 트랜잭션 분리가 필요한 외부 서비스 호출이 한 작업 단위에 있을 때만. 외부 호출 없이 도메인 상태만 보고 선행 단계를 자동 수행하는 순차 처리는 도메인 Service 공통 메서드에 두고, 같은 시퀀스를 직접 수행하던 산재 호출부(리스너/컨트롤러/스케줄러)를 grep 으로 수렴(호출자별 차이는 `Instant? = null` + `?:` 선택 파라미터)
- `{Domain}Facade` 관례가 있는 프로젝트에선 cross-reader aggregation·외부 연동을 전용 Service 대신 기존 `{Domain}Facade` 에 — `@Service` 로 두되 클래스레벨 `@Transactional` 금지(Reader 자체 readOnly, 외부 HTTP 는 트랜잭션 밖)
- 다른 모듈이 소비하지 않고 외부(어댑터)로 나가는 Internal API 응답은 공용 `Read` 대신 `{module}/controller/response/` 의 전용 Response DTO. QueryService/Reader 는 raw 조회, 크로스모듈 조합·응답 완성은 Facade — 공용 Read 를 외부 응답으로 흘리면 내부 조회 모델이 외부 계약에 묶인다
- **왜:** 경계 없는 행위별 service 는 책임 불명확·호출부 결정 비용·의존성만 늘리고(YAGNI 의 구조 버전), 상태 전이 규칙이 경로마다 중복되면 진입점별로 동작이 갈린다

### 외부 전송 DTO 조립 — 필드 소스별 4분류 처리 (2026-07-20, 보강 1 · 최근 09-28)
- ①현재 엔티티에 있는 값 → 매핑 ②다른 도메인 소유 값 → `{Domain}Reader` 조회(유사 필드 오대입 금지) ③곧 생길 필드 → 기본값 + 대체 코드 TODO 주석 ④필수인데 부재 → 식별자 포함 fail-fast. 여러 대상은 `readXxxIn` → `associateBy` → `map[key]?.field ?: throw`(N+1 회피)
- ①의 값 형식은 임의로 가공하지 않는다 — 전화번호는 숫자만 남겨 전달, 국가번호 결합·국번 0 제거 같은 외부 스펙 추정 변환(E.164)은 스펙 원문이 요구할 때만
- **왜:** 유사값 대입은 데이터 오염, 필수 부재의 silent 빈값보다 fail-fast 가 안전

## 하지 말아야 할 것

### API 스펙 미확인 상태에서 placeholder 남발 (2026-04-16)
- 실제 호출 구조(단건/다건, GET/POST)는 정확히 반영하고 값만 TODO 로 남긴다
- **왜:** 구조가 실제와 다른 placeholder 는 재설계를 유발한다

### 외부 응답 DTO — 기본값 금지, nullable 은 실 응답/실 데이터 기반 최소 변경 (2026-04-16, 보강 1 · 최근 09-23, 병합 1 · 최근 11-10)
- 외부 API Response 필드에 `= ""`, `= 0` 초기화 금지, nullable 은 `?` 로 — 잘못된 값이 에러 없이 넘어가 문제를 숨긴다
- 실 응답 샘플을 필드×케이스 표로 분류해 비어있을 수 있는 필드만 nullable. 변경 직전 사용자 확인
- 내부 시스템 DTO/projection 필드도 동일 — 실 컬럼/스키마 nullability 그대로(필수 non-null·선택 nullable), "정확하지 않으면 nullable" 식 추측 nullable 금지
- **왜:** 일괄·추측 nullable 은 타입 신호를 잃고 NPE 위험을 다운스트림에 전가한다

### Consumer/외부 서비스의 데이터 구조를 바꾸지 않기 — boundary 에서 처리 (2026-05-15)
- Consumer 의 Entity/VO 는 그대로 두고 매핑 진입점(`create()`/`from(message)`)에서 `?: ""` 등으로 변환. 이후 update 흐름의 빈 값 보강도 함께 추가
- **왜:** Consumer 모델은 여러 producer 와의 계약 — 한 producer 때문에 약화하면 다른 producer 의 의도까지 무너진다

## 더 신경써야 할 것

### 대량·반복 외부 API 작업 전 제약 프로브 + 대표 케이스 카나리 (2026-07-17, 보강 1 · 최근 07-20)
- 반복/대량 호출 전 읽기 전용 1~2건으로 외부 API 의 실제 제약(날짜 단위 규칙·lookback·페이지 한계)을 프로브 — 내부 검증 코드만 믿지 않기
- 카나리는 전형 항목으로 구성 — 예외 항목이 첫 건이면 "카나리 OK=전체 OK" 착각. 경계 불명확하면 이진 탐색, 요청 범위가 제약으로 축소되면 달성 가능 범위를 먼저 보고
- 보강: 응답 스키마가 티켓/문서/참조 어디에도 없으면 추측 DTO 대신 (승인 하에) dev 최소 요청 실호출로 구조 확보 후 작성
- **왜:** 내부 검증은 외부 제약의 부분집합. 대량 작업 실패는 롤백/재실행 비용이 크다

### 참조 프로젝트 활용 (2026-04-16, 보강 1 · 최근 10-23)
- 외부 연동 작업 시 gentlemonster-oms-backend, tamburins-oms-backend 를 먼저 탐색 — 기존 구현 패턴, API key/sandbox/브랜드 분리 여부, TLS·인증 방식 설정 차이까지 비교 검증
- 보강(10-23): 기존 엔티티·테이블의 재사용 방식(필드 추가 vs PK/SK 재설계)을 정할 때도 같은 저장 패턴을 쓰는 사내 다른 프로젝트의 사용처(같은 테이블의 키 설계·GSI 선례)를 먼저 보고 설계안을 제시한 뒤 작업에 들어간다 — 재사용 티켓에도 "설계 → 확인 → 구현" 순서

### 스케줄 API·새 외부 조회 API 추가 시 Admin API 도 함께 (2026-05-06, 보강 2 · 최근 11-02)
- 동일 facade 호출·동일 시그니처, 인증만 다르게(`schedule-basic-auth` vs `admin-basic-auth`). http 샘플도 양쪽 추가
- 보강(10-14): QA 용 대상 지정 파라미터(특정 주문번호 등)를 한 Admin API(수집)에 추가하면 같은 흐름의 다음 단계 Admin API(확정)에도 같은 파라미터를 계획에 함께 올린다 — 한 건을 끝까지 수동으로 밀 수 있어야 한다. 지정 건에도 기존 시간 조건이 적용되면 즉시 처리용 값(대기 0분 등)을 http 샘플에 같이
- 보강(11-02): 흐름 안에서만 부르는 새 외부 조회 API(취소 내역 조회 등)를 클라이언트에 연동하면 같은 요청 팩토리를 쓰는 admin 조회 엔드포인트(`GET /admin-api/{system}/{channelType}/{domain}/{resource}` + http 샘플)를 계획·보고에 같이 올린다 — 운영·QA 가 흐름이 보내는 요청 그대로 외부 응답을 바로 비교할 수 있어야 한다
- **왜:** 스케줄러 실패·특정 시간대 재수집 시 운영자 수동 통로가 반드시 필요하다

### 외부 API 작업 전 공식 문서로 endpoint 검증 (2026-06-09, 보강 4 · 최근 10-28)
- 호출 코드 추가/변경 전 공식 문서 fetch → 기존 endpoint(path/method/body)와 비교 → 불일치·출처 불명이면 옵션 표로 결정 위임. 인증으로 fetch 불가면 그 한계도 명시
- 응답 DTO 도 공식 문서의 필드 표 기준으로 전수 갱신 — 누락 필드는 형제 DTO 의 nullable 패턴대로 추가, 표에 없고 샘플에만 있는 필드는 형제 DTO 관례를 따르고 제외 여부를 보고. 참조 프로젝트에 같은 DTO 가 있으면 교차 확인
- 엣지 케이스 정책(부분 취소 등)을 설계하기 전에 외부 API 의 식별 단위·파라미터(주문 단위 vs 수량 단위)를 공식 문서 원문으로 확인 — 내부 모델이 표현할 수 있어도 외부에 대응 조작이 없으면 '처리 불가' 로 결론짓고 TODO/보고에 적는다
- 수신측이 사내 counterpart 프로젝트면 그쪽 요청 DTO 정의가 곧 스펙 — 전송 DTO 를 추가·변경할 때 필드 단위로 diff 해 이름·포맷(다건 구분자 포함)을 맞추고, 요청문의 필드명은 개념 지칭으로 보아 수신측 이름을 기본값으로 둔다
- 외부 enum 값의 의미(누가 언제 채우는지, 판매자 API 로 입력 가능한지)는 코드 표만 보지 말고 관련 API 문서와 운영 분포로 교차 확인해 값별 표로 보고 — 설명이 없는 값은 '추정' 으로 표시하고 양쪽 오류 시 영향을 적는다
- **왜:** 기존 endpoint 가 추정/legacy 일 수 있고, 확인 과정에서 더 적합한 API 를 발견하기도 한다
