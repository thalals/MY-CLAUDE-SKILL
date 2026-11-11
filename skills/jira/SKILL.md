---
name: jira
description: Use when the user provides a Jira ticket number to analyze, plan, implement, and write unit tests for the ticket's requirements
argument-hint: <ticket-number>
---

# Jira Ticket Workflow

Jira 티켓 번호를 받아 분석 → 계획 → **단위 테스트 작성 → 구현** 순서로 진행한다 (TDD).

## 사용법

```
/jira OMS-2347
```

## 실행 절차

### 1단계: 티켓 분석

1. **Jira 티켓 조회** — Atlassian MCP(`getJiraIssue`)로 티켓 내용 조회
   - 티켓 번호는 대문자로 변환 (예: `oms-2347` → `OMS-2347`)
   - 제목, 설명, 하위 작업, 연결된 이슈, 첨부 링크 확인
2. **연결된 이슈/링크 확인** — 티켓 내 링크(노션, 외부 문서 등)가 있으면 WebFetch / Notion MCP 등으로 읽기
3. **관련 문서 읽기** — CLAUDE.md의 Pre-flight Document Check 테이블에 따라 관련 문서 Read

### 2단계: 작업 계획

1. **영향 범위 분석** — 티켓 요구사항이 현재 프로젝트의 어느 모듈/패키지에 해당하는지 파악
2. **기존 코드 탐색** — 관련 코드를 Grep/Glob으로 찾아 현재 구조 파악
3. **단위 테스트 대상 식별** — 신규/수정 코드 중 단위 테스트 대상을 먼저 추려낸다
   - 대상: VO / enum / 일급 컬렉션 / Group / 변환·분기·예외·derived properties
   - 대상 아님: Facade, Controller, Client interface, Service(명시 요청 시에만), 단순 request/response DTO (변환 로직 없음)
4. **작업 목록 작성 (TaskCreate)** — **단위 테스트 작성 태스크가 구현 태스크보다 먼저 오도록** 순서대로 나열
5. **사용자 확인** — 계획을 사용자에게 보여주고 확인받은 후 다음 단계 진행

### 3단계: 단위 테스트 먼저 작성

- 2단계에서 식별된 테스트 대상에 대해 **구현 코드 전에** 단위 테스트부터 작성한다
- TEAM-CONVENTIONS.md 의 테스트 코드 작성 가이드 + 사용자 스타일 파일의 단위테스트 작성 대상 룰 준수
  - Kotest BehaviorSpec (VO/Group) 또는 DescribeSpec (단순 enum/static)
  - Given-When-Then 엄격 준수, 한국어 설명
  - Fixture Monkey 로 데이터 생성, MockK 로 협력자만 mock
- 테스트가 컴파일은 되지만 실패하는 상태(red) 까지 작성하고, 다음 단계에서 통과(green) 시킨다
- 테스트 대상이 없는 작업이면 이 단계를 건너뛴다 (이유를 한 줄로 보고)

### 4단계: 구현

- 작성한 단위 테스트가 통과하도록 구현한다
- TEAM-CONVENTIONS.md 및 사용자 스타일 파일의 규칙 준수
- 컴파일 확인: `./gradlew build --exclude-task test`
- 테스트 실행: `./gradlew test --tests "*.{TestClassName}"`

## 규칙

- 계획 단계에서 사용자 확인 없이 다음 단계로 넘어가지 않는다
- **단위 테스트는 구현보다 먼저 작성한다 (TDD).** 테스트 대상이 없는 작업만 예외
- 커밋은 하지 않는다 — 사용자가 별도로 요청할 때만 수행
- 티켓 범위 밖의 작업은 하지 않는다
