```mermaid
erDiagram
    %% ユーザー管理
    USERS {
        int user_id PK
        string name UK
        string password_hash
        enum role "manager,member,coach,director"
        int grade "学年(部員のみ)"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% 測定記録
    MEASUREMENT_RECORDS {
        int record_id PK
        int user_id FK
        date measurement_date
        decimal run_50m "50m走(秒)"
        decimal base_running "ベースランニング(秒)"
        decimal long_throw "遠投(m)"
        decimal straight_speed "ストレート球速(km/h)"
        decimal hit_speed "打球速度(km/h)"
        decimal swing_speed "スイング速度(km/h)"
        decimal bench_press "ベンチプレス(kg)"
        decimal squat "スクワット(kg)"
        enum status "draft,pending_member,pending_coach,approved"
        int created_by FK
        datetime created_at
        datetime updated_at
    }

    %% 承認履歴
    APPROVAL_HISTORY {
        int approval_id PK
        int record_id FK
        int approver_id FK
        enum approver_type "member,coach"
        enum action "approved,rejected"
        text comment
        datetime approved_at
    }

    %% 通知
    NOTIFICATIONS {
        int notification_id PK
        int user_id FK
        int record_id FK
        enum type "approval_request,approval_completed,record_updated"
        string title
        text message
        boolean is_read
        datetime created_at
    }

    %% 部員管理（退部・引退管理）
    MEMBER_STATUS {
        int status_id PK
        int user_id FK
        enum status "active,withdrawn,retired"
        date status_date
        text reason
        int updated_by FK
        datetime created_at
    }

    %% リレーションシップ
    USERS ||--o{ MEASUREMENT_RECORDS : "測定対象"
    USERS ||--o{ MEASUREMENT_RECORDS : "記録作成者"
    USERS ||--o{ APPROVAL_HISTORY : "承認者"
    USERS ||--o{ NOTIFICATIONS : "通知対象"
    USERS ||--o{ MEMBER_STATUS : "ステータス対象"
    USERS ||--o{ MEMBER_STATUS : "更新者"
    
    MEASUREMENT_RECORDS ||--o{ APPROVAL_HISTORY : "承認対象"
    MEASUREMENT_RECORDS ||--o{ NOTIFICATIONS : "関連記録"
```

    <!-- %% システム設定（測定項目管理）
    MEASUREMENT_ITEMS {
        int item_id PK
        string category "走力,肩力,打力,筋力"
        string item_name
        string unit
        boolean is_active
        int display_order
    } -->
