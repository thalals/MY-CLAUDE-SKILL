# Kotlin 문법·주석·컬렉션

> 읽는 때: Kotlin 코드를 쓰거나 고칠 때. 색인은 `index.md`.

### 기본 원칙 (보강 4 · 최근 11-02, 병합 2 · 최근 11-10)
- `val` 우선·`var` 최소화, data class 불변. null safety, 컬렉션 연산(`map`/`filter`/`fold`)·expression-bodied 함수 우선, 명령형 루프 지양
- 인자 2개 이상이면 모두 named arguments, 1개면 위치 기반(람다 단독 호출·builder/DSL 예외) — 같은 타입 파라미터 순서 실수 방지. 모듈 간 위임 호출(호출부 → `{Domain}Writer` → `{Domain}CommandService`)도 예외 없음
- private 호출은 `this.` 명시, 여러 줄 리스트/인자는 후행 쉼표, Backing Property 는 `private var _x: T?` + `val x: T get() = _x ?: …`
- object 유틸 호출 형태는 다수 패턴을 grep 해 따른다 — 다수가 static import(`isXxx()`)면 `{Utils}.isXxx()` 를 섞지 않는다
- 람다 파라미터가 도메인 개념(status/entity)이고 다른 메서드 인자로 넘기면 `it` 대신 명시적 이름, 단순 프로퍼티 접근·짧은 판정은 `it` — 넘길 땐 이름이 "무엇을 넘기는지" 드러낸다

### 컬렉션 파이프라인 — mutable 누적 대신 함수형 불변 반환, 중복 제거는 그룹핑/분할 앞에 (2026-06-12, 보강 1 · 최근 11-10, 병합 1 · 최근 11-10)
- `mutableListOf` + add 대신 `map`/`flatMap`/`mapNotNull` 로 불변 반환, 분기 결과는 분기별 리스트 반환 후 flatMap. 분기마다 다른 종류의 컬렉션이 정말 필요할 때만 한쪽만 mutable 허용
- 루프로 `mutableMapOf` 를 채우는 그룹 누적도 같다 — `mapNotNull`(항목 → 키·값 쌍) → `groupBy { 키 }` → 그룹별 처리 파이프라인으로 쓴다. 항목별 실패·건너뜀을 모으는 기존 리스트(다건 에러 수집)만 남긴다
- `groupBy`/`partition`/`chunked` 안쪽 `distinct` 금지 — 나누기 전 원본에 `distinctBy { 키 }`(키가 정확히 한 그룹에만). 앞으로 빼면 입력 순서 의존(첫 등장 유지) — 발생 가능한 입력이면 어느 쪽이 남는지 테스트로 고정. 그룹핑 필요 여부는 dedup 위치와 별개
- **왜:** 함수형 변환은 입력→출력 매핑이 한눈에 보이고, 그룹 안 distinct 는 "키 하나당 처리 한 번" 불변식을 보장하지 못한다

### 분기는 expression-style `if / else` — 선언 후 할당·체이닝·가드 분리로 우회하지 않기 (2026-06-24, 보강 1 · 최근 10-14, 병합 2 · 최근 10-28)
- `val x: T?` 선언 후 분기 할당 금지 — `val x = if (조건) A else B`, 한쪽 분기에만 필요한 로직은 그 분기 안/early-return 으로
- `else` 회피용 `takeUnless ?.let ?:` 체이닝·가드 private 메서드 금지, 뒤에 공통 후처리가 이어지면 early-return 도 금지 — 회피 요청이 와도 대안이 더 읽기 나쁘면 `if / else` 유지 제안
- **왜:** declare-then-assign 은 가변처럼 읽히고 nullable 선언은 null 체크를 전가하며, 우회안은 모두 원래보다 읽기 나쁘다

### Comments Policy (보강 4 · 최근 11-02)
- 설명 주석 금지 — 네이밍으로 self-documenting, 주석은 변경되지 않는 내용에만. 새 메서드의 "무엇을 하는지" KDoc 도 금지, 오버로드 구분은 파라미터 이름/타입으로
- `.http` 샘플도 동일 — 바디 위 설명·값 출처·"교체 필요" `#` 주석 없이 요청 제목(`###`)과 변수만, 출처·가정·주의점은 대화 보고에만
- 상수/셋의 멤버십 이유·적용 시점도 "이름 대신 한 줄 주석" 을 대안으로 내지 않고 이름 안에서 해결
- 형제 overload 와 파라미터가 아니라 동작이 다른 점(이벤트 미발행 등)을 주석으로 설명하게 되면 그 차이가 곧 이름(`createOf` + 주석 ❌ → `createWithoutEvent`). 모듈 간 포트(`{Domain}Writer`)의 메서드명은 계약(`create`)만, 구현 차이는 서비스 메서드명에

### 클래스 본문 멤버 순서 (2026-05-06, 보강 1 · 최근 09-29, 병합 1 · 최근 10-28)
- ①companion object(최상단 — 팩토리가 먼저 보여야 한다) ②프로퍼티 ③nested class ④메서드(public 먼저, private 은 nested class 포함 본문 최하단) — 구조를 인지한 뒤 행위를 읽는다

### nullable 처리 — '없음' 값 중복 금지, negation-first 필터, 람다 비교는 `==` (2026-04-22, 보강 1 · 최근 05-18, 병합 2 · 최근 10-28)
- nullable enum 필드에 `NONE`/`UNSPECIFIED` 를 두지 않는다 — `null` 이 그 역할. non-nullable 이고 명시적 "처리 안 함" 값이 필요할 때만 NONE
- `takeIf { it.isNotBlank() }` 대신 `takeUnless { it.isBlank() }`, nullable String 컬렉션은 `filter { it.field != null }` 대신 `filterNot { it.field.isNullOrBlank() }` — `!= null` 만으로는 빈 문자열이 통과(빈 문자열이 valid 한 드문 도메인만 `!= null`, 기존 필터 패턴에 통일)
- 컬렉션 람다 안 비교는 `none { it.x == y }` — `==` 는 null-safe 라 `mapNotNull` + `!in` 다단계로 풀지 않는다. mapNotNull 은 null 제거 후 별도 가공이나 의도적 필터링일 때만
- **왜:** 같은 의미의 두 표현은 이중 분기를 만들고, 빈 값이 다운스트림에 흘러가면 안 되며, 한 줄 람다가 의도를 그대로 보여준다

### 도메인 조합 키에 Pair 대신 기존 VO 재사용, 컬렉션 원소는 단일 개념 (2026-08-20, 보강 2 · 최근 10-26)
- 조합 키는 기존 조합 VO 를 grep 해 재사용 — `Pair<A, B>` 금지. 원소도 `Pair<Entity, Int>` 같은 이질 묶음 대신 단일 개념(부가 값은 사용 시점에 소유 객체에 조회). 집계로 한 축이 접힌 맵의 키만 남은 축의 단일 키
- 서비스→도메인의 `Map<String, List<String>>`(식별자 → 값들)도 Pair 와 같다 — 같은 식별자의 기존 `common.vo.XxxItem` 류 VO 에 default 필드(`values: List<String> = emptyList()`)를 추가해 `List<VO>` 로, 신설은 재사용할 VO 가 없을 때만
- 라인 식별 차원이 늘면(옵션 id) 조회 키 VO 뿐 아니라 그 라인을 저장하는 기존 VO 에도 nullable 필드(`= null` 기본값)로 확장 — 식별 필드는 레코드의 사실을 완성하는 데이터라 "아직 읽는 곳이 없다" 는 YAGNI 대상이 아니다
- **왜:** Pair 는 first/second 가 의미를 못 드러내고 같은 조합이 형태를 달리해 흩어진다. 키 타입은 데이터의 차원을 반영해야 한다

### 컬렉션은 일급 컬렉션으로 감싸 행위·색인을 내부에 — 1회 매칭은 로컬 색인 (2026-04-16, 보강 1 · 최근 11-02, 병합 1 · 최근 10-28)
- `List<T>` 를 data class 로 감싸고 행위(toMessage 등)를 내부에, companion 에 `from` 팩토리
- 같은 컬렉션에서 키로 여러 번 찾으면 소유 객체(Request/일급 컬렉션) 내부에 `private val … by lazy { associate… }` 색인 + 공개 API 는 `get{Value}(key)` 단건 조회만 — 색인이 안에 숨으면 호출부에 의도만 남고 lazy 는 조회 없는 경로에서 비용 0
- 한 메서드 안의 1회 매칭(요청 목록 ↔ 보유 목록 → 결과 객체 조립)은 로컬 색인 — 요청 키 집합(`toSet()`)으로 보유 목록을 거르고 `associateBy { 키 }` → 요청을 순회하며 `map[키] ?: throw`(식별자 포함). 요청마다 보유 목록을 `filter { it.키 == … }` 로 다시 훑지 않는다
