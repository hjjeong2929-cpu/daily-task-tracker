# 설치 가이드

터미널에서 진행하는 부분과 GitHub 웹/앱에서 클릭으로 진행하는 부분이 섞여 있어요. 순서대로 따라오시면 됩니다.

## 1. GitHub에 새 저장소 만들기

1. github.com 로그인 → 우측 상단 `+` → **New repository**
2. Repository name: 예) `daily-task-tracker`
3. Public/Private 아무거나 (Private이어도 Actions는 무료)
4. README/.gitignore/license는 **추가하지 않고** 빈 저장소로 생성
5. 생성 후 나오는 저장소 주소 복사 (예: `https://github.com/내아이디/daily-task-tracker.git`)

## 2. 로컬 파일을 저장소에 올리기

받은 zip 압축을 풀고 그 폴더로 이동해서 아래 명령을 순서대로 실행합니다.

```bash
cd daily-task-tracker

git init
git add .
git commit -m "chore: 할일 관리 프로젝트 초기 설정"
git branch -M main
git remote add origin https://github.com/내아이디/daily-task-tracker.git
git push -u origin main
```

`내아이디`는 본인 GitHub 아이디로 바꿔주세요.

## 3. Actions 권한 켜기 (★ 가장 중요, 안 하면 전부 실패)

1. 저장소 → **Settings** → 좌측 **Actions** → **General**
2. 하단 **Workflow permissions**에서 **"Read and write permissions"** 선택
3. **Save**

## 4. 워크플로 첫 실행해보기

1. 저장소 → **Actions** 탭
2. `Morning - Create Tasks & Digest` 선택 → **Run workflow** 로 수동 실행
   - 성공하면 Issues 탭에 오늘의 반복 이슈 + "📋 오늘의 할 일" 이슈가 생깁니다.
3. `Evening - Nudge & Update Stats` 도 한 번 수동 실행
   - 성공하면 README.md 통계가 갱신된 커밋이 자동으로 생깁니다.

## 5. GitHub Projects 보드 만들기 (우선순위/진행상황 한눈에 보기)

1. 저장소 → **Projects** 탭 → **New project** → **Board** 템플릿 선택
2. 기본 컬럼(Todo / In Progress / Done)을 그대로 쓰거나 원하는 대로 수정
3. 우측 상단 **⋯ (메뉴)** → **Workflows** 클릭 → 아래 두 가지를 켜기
   - **"Item added to project"** 대신, **저장소 Issues와 자동 연동**하려면 프로젝트 화면에서 **+ Add item** → **Add from repository**로 이 저장소를 연결한 뒤, Workflows에서 **"Auto-add to project"** 를 켜고 조건을 "이슈가 열릴 때"로 설정하세요. 그러면 새로 생기는 이슈가 자동으로 보드에 올라옵니다.
   - **"Item closed"** → **Status: Done**으로 설정해두면, 이슈를 Close하는 순간 보드에서도 자동으로 Done 칸으로 이동합니다.
4. 보드 화면에서 **Group by** 를 **Labels**로 바꾸면 P1/P2/P3별로 묶여서 보여서, 우선순위 파악이 훨씬 쉬워집니다.

(이 단계는 GitHub 화면에서 클릭 몇 번으로 끝나고, 코드 수정은 필요 없어요.)

## 6. 휴대폰 푸시 알림 켜기 (이메일 없이 알림 받기)

**iOS**: GitHub 앱 → Profile → Settings → Notifications → **"Assignments to issues or pull requests"** 켜기
**Android**: GitHub 앱 → Profile → Settings → Configure Notifications → 동일 항목 켜기

이 토글만 켜두면, 매일 아침 자동 생성된 이슈가 나에게 할당될 때마다 이메일 없이 휴대폰 푸시로만 알림이 옵니다.

## 7. 실제로 사용하기

- 아침: 휴대폰 푸시 알림 확인, 또는 GitHub 앱에서 "📋 오늘의 할 일" 이슈 열어보기
- 완료할 때마다: 해당 이슈 Close (Projects 보드에도 자동 반영됨)
- 급한 일이 생기면: 이슈에 `P1` 라벨 추가
- 새로운 반복 작업을 추가하고 싶으면: `tasks.yml` 수정 후 push

## 문제 해결

- **이슈/댓글/커밋이 하나도 안 만들어져요** → 3단계(Workflow permissions)를 다시 확인하세요. 저장소가 아니라 **조직(Organization) 설정**에서 막혀 있을 수도 있어요.
- **Projects 보드에 이슈가 자동으로 안 올라와요** → 5단계의 "Auto-add to project" workflow가 켜져 있는지, 조건이 올바른지 확인하세요.
- **푸시 알림이 안 와요** → 6단계 토글 확인 + GitHub 앱 자체의 시스템 알림 권한(휴대폰 설정)도 켜져 있는지 확인하세요.
- **시간대를 바꾸고 싶어요** → `.github/workflows/*.yml`의 `cron` 값을 수정하세요. GitHub Actions의 cron은 항상 UTC 기준입니다.
