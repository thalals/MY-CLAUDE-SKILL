# 네이밍·URL 경로

> 읽는 때: 클래스·메서드·필드·enum·DTO·환경변수 이름이나 API 경로를 정할 때. 색인은 `index.md`.

### 필드·파라미터·환경변수 네이밍 (2026-04-16, 보강 1 · 최근 11-05, 병합 1 · 최근 10-28)
- 컬렉션은 복수형(`items`), 타입명 포함 금지(`itemList` ❌)
- 컬렉션에서 일부를 걸러 낸 로컬 변수는 제외 조건(`{xs}Except{Y}`·`non{Y}{Xs}`)이 아니라 그 부분집합이 쓰이는 역할로 짓고 같은 블록 형제 변수의 어휘에 맞춘다(`{role}{Xs}` ↔ `{role}Amount`) — 부정형은 의미를 되짚게 하고 길어서 줄을 넘긴다
- Instant 는 `DateTime` 접미사 금지 — 조회 범위 → `startAt`/`endAt`, 라이프사이클 시점 → `startedAt`/`endedAt`(`createdAt` 결), 호출부 로컬 변수도 통일. `~At` 은 timeline 의 한 점, `~edAt` 은 이미 발생한 시점
- 인증/시크릿 환경변수는 `_API_KEY`/`_API_SECRET`(Basic Auth 비밀번호도 `_AUTH_PASSWORD` ❌) — YAML 키·데이터 클래스 필드·Secret Manager 키(lowercase)까지 통일해 검색·변경·매핑을 자연스럽게. 외부 시스템의 내부 명칭(api_id 등)도 그대로 쓰지 않고 실제 용도로(시크릿을 담으면 `secret`) — 이름과 용도가 어긋나면 혼란을 만든다

### Enum 네이밍 — 접미사·도메인 맥락·시스템 매핑 패턴 (2026-04-16, 보강 2 · 최근 09-11, 병합 1 · 최근 10-28)
- `XXType`/`XXStatus`/`XXEvent` 접미사 필수, 단일 명사형도 예외 없음(`XxxConfirmation` ❌). companion 에 `fromName()`/`fromCode()` 팩토리
- 범용 이름보다 사용 도메인 이름(배송 도메인의 B2B/B2C 는 `OrderType` ❌ → `DeliveryType`). 시스템별 매핑 enum 은 `{System}{Concept}` — 추가 전 동일 개념의 기존 enum 네이밍 확인, 의미만 맞는 새 이름 금지
- 값 추가 시 동사 빈도로 고르지 않는다 — 기존 값을 ①자기 객체 조작 ②외부 도메인 사건 두 계열로 가른 뒤 새 값이 속한 계열의 어휘를 따르고, ②면 원인 도메인의 기존 표현(에러 상수·필드명)을 grep 해 동사를 맞춘다
- **왜:** 다른 계열의 동사는 나란히 놓였을 때 주체를 오독시키고, 일관된 네이밍이 검색·발견을 쉽게 한다

### 채널 게이트 EnumSet 은 멤버 나열이 아니라 "그 채널에서 필수인 행위" 로 — `{SUBJECT}_{ACTION}_REQUIRED_CHANNELS` (2026-10-20)
- 멤버(`A_B`)·수단(`MANUAL_…`) 대신 필수가 되는 행위(`{SUBJECT}_APPROVAL_REQUIRED_CHANNELS`), 멤버가 같아도 이유가 다르면 셋을 분리
- 수식어 명사는 단수(`OPERATOR_CLAIM`)·머리 명사만 복수(`CHANNELS`). "manual" 처럼 뒤 명사에 따라 뜻이 뒤집히는 일반어 대신 코드의 정확한 용어(enum 값 `CS_OPERATOR` → `OPERATOR_CLAIM`). 멤버십 술어는 셋 이름 그대로 `is{…}RequiredChannels()`(임의 단수화 금지)
- **왜:** 멤버 나열은 브랜드별 동명 채널 포함 여부가 안 보이고 멤버가 바뀌면 이름이 거짓이 된다. 이유가 이름에 있어야 같은 멤버의 두 셋이 왜 둘인지 드러난다

### DTO 네이밍 — 동사형 segment 지양, 클라이언트 메서드명과 일치 (2026-04-16, 보강 1 · 최근 09-28, 병합 1 · 최근 10-28)
- `Dto` 금지. REST `XXRequest`/`XXResponse`, Kafka `XXMessage`, Spring Event `XXEvent`
- 단순 조회 → `{System}{Resource}Response`, 명시적 액션 있는 응답만 `{System}{Resource}{Action}Response`. `Query`/`Search`/`Get` 같은 동사형 금지 — HTTP 메서드와 중복
- `{Resource}{Action}` 은 외부 객체명이 아니라 우리 클라이언트 메서드의 행위명 — `upsert{Resource}` 면 `{System}{Resource}UpsertRequest`(외부 객체명 기반 ❌), 재처리 이벤트 enum 도 `UPSERT_{RESOURCE}`

### 클래스 네이밍은 단순하게 (2026-04-22, 보강 3 · 최근 10-28)
- 패턴/행위를 과도하게 넣지 않기 — `[System][Layer]` 최소 형태(`{System}Service` 로 충분), 같은 레이어에 여러 클래스가 필요할 때만 행위 추가. 공용 DTO·nested class 도 외부 문서 서술을 옮긴 긴 합성 이름 대신 `[System][Concept][Layer]`
- 메서드명도 대비되는 형제 메서드가 없으면 출처/대상 한정어를 붙이지 않는다(`isXxxIn{System}` ❌ — 수신자·파라미터가 출처를 말한다)
- 보조 레코드 엔티티는 '부모 엔티티 + 레코드 역할'(`{Parent}{Concept}WaitlistEntity`) — 값의 저장소가 아니라 값을 기다리는 목록이라는 역할이 보여야 한다. 개념어가 형제 타입명과 겹치면(`returnXxx` ↔ `RETURN` 타입) 전 타입을 포괄하는 공통 용어(`pickupXxx`)로, 채널 필드명은 원본 DTO 에만

### 이름이 주장하는 판정·상태는 그 레이어·분기에서 실제여야 (2026-09-23, 병합 1 · 최근 10-28)
- 데이터를 제공만 하는 상류 객체(코어 read/응답)의 이름에 하류(어댑터)의 판정 개념을 섞지 않는다 — 그 도메인에 없는 개념이면 중립 네이밍(`get{판정어}{X}()` ❌), 판정하는 하류(`is{판정어}()`)만 그 개념어를 쓴다
- 여러 분기에서 쓰는 변수에 `confirmed~` 같은 상태 형용사를 붙이지 않는다 — 기존 이름이라도 내가 추가한 분기(취소 등)에서 거짓이 되면 타입·출처 기반 중립 이름(`{system}OrderResponse`)으로 함께 바꾼다
- **왜:** 판정 개념은 판정하는 레이어의 것이고, `cancelUnconfirmable{X}(x = confirmed{X})` 처럼 거짓인 이름은 읽는 사람을 오도한다

### 메서드 네이밍 — 조회는 반환 구조, 동사는 호출 의도 (2026-04-16, 보강 2 · 최근 11-02, 병합 1 · 최근 10-28)
- Service: `getXX`/`getXXs`, Optional 반환 금지, private 도 `get`(`find` ❌). Repository: JpaRepository `findXX`(Optional), 커스텀 `findXX`(nullable), QueryDsl `fetchXX`/`fetchAllXX`
- 조회/집계는 반환 자료구조가 드러나게 — `get{Value}MapBy{Key}`(그룹핑 맵)·`get{Value}SumBy{Key}`(집계)·`get{Value}(key)`(단건). 주체는 **반환 대상**, 키는 `By{Key}`(`get{Key}()` ❌). 로컬 변수명도 동일, 구조가 바뀌면 동기화
- `distribute` 는 한 입력을 여러 채널로 흩뿌릴 때만, 단일 시스템 전송/갱신은 `send`/`update` — 같은 도메인 형제 facade 메서드를 grep 해 통일(URL segment/Request DTO 도)
- `get` 은 이미 있는 값을 꺼낼 때만 — 입력을 조합해 새 값을 만드는 함수(구분자 결합 식별자·포맷 조립)는 `generate{Concept}(a, b)`(`get{Concept}(a, b)` ❌), `get` 이면 호출부가 저장된 값의 조회로 오독한다
- **왜:** 시그니처만 보고 반환 구조와 호출 의도를 알아야 정의로 점프하지 않는다

### URL Path — 행위 segment 와 HTTP 메서드 (2026-04-16, 보강 2 · 최근 11-02)
- `/v1/{api-type}/{domain}/{behavior}/...` — api-type: api, internal-api, admin-api, batch-api
- behavior 는 행위만(`{domain}/collect-{object}`) — 대상 데이터의 상태(`-waiting`)는 경로가 아니라 엔티티명이 가진다
- 리소스 update/replace 는 `POST .../send` ❌ → `PUT /v1/{api-type}/{domain}/{resource}`, 도메인 행위(취소/승인 등 상태 전이)만 POST + segment
- internal-api 의 행위 POST 는 대상 식별자(주문번호 등)를 path variable 이 아니라 body 에 — `POST /v1/internal-api/{domain}/{behavior}` + body `{ orderNo, … }`. 같은 컨트롤러의 형제 엔드포인트가 이미 그 형태면 그대로 따른다
- 외부 스펙이 준 경로라도 우리 API 경로는 프로젝트 컨벤션 우선(외부 계약이 강제할 때만 예외)

## 더 신경써야 할 것

### 네이밍 신중 — 기존 패턴·도메인 용어, 보편 용어는 실사용처 분석 선행 (2026-04-16, 보강 1 · 최근 10-20, 병합 2 · 최근 11-10)
- 첫 네이밍부터 프로젝트 기존 패턴·도메인 용어에 맞추고 애매하면 먼저 질문 (사용자가 직접 자주 정정해온 영역)
- 보강(10-20): 네이밍 추천 요청은 전 사용처·형제 상수 관례·티켓 용어를 확인한 뒤 추천 1 + 대안 표(장점/단점). 사용자 후보는 ①문법(형용사는 바로 뒤 명사를 수식 — 위치가 바뀌면 뜻이 뒤집힘) ②의미 ③코드 전제(현재 코드가 실제 그렇게 동작하는지 grep) 세 축으로 판정. 사용자가 "다음 티켓에서 반영 예정" 이라 밝힌 범위는 목표 범위로 인정해 그 기준으로 명명하고 현재 미적용 사실만 보고
- 보편/추상 용어 제안: 통념의 추상 단어(`STANDARD`/`EXPRESS` 류)로 옵션을 만들지 말고 ①실사용 주체 나열 ②카테고리×주체 표 ③모든 주체가 동일 의미로 쓰는 축 추출 ④그 축에서 옵션 도출. 통념 옵션도 비교용으로 병기 — 보편 용어의 근거는 실사용처들의 의미 일치이고 통념 단어는 주체마다 의미가 다를 수 있다
- **왜:** 사용자가 의도한 도메인 어휘("manual" = 운영자 생성 경로)를 놓치면 이름이 의미를 배반한다
