---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_4338229675a811f1a7da5254006c9bbf
    ReservedCode1: 61PoQ7pZk1OVrygXStpstB/GHqEXTfP+TvykIsY5xg4Ee4kdoZg8jUu31p4miFImsGn3KA9lYm7oAYTbxMCXg0i+27baW2/1JV5472vuIXhGXPEuIn6ga4MEWtHQ2Fa7Kky4zZHzKIOyaOq7Zcl5l20P8hnBPBCy0vkt+OJ9VmRX8YpppP8opLwWQXs=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_4338229675a811f1a7da5254006c9bbf
    ReservedCode2: 61PoQ7pZk1OVrygXStpstB/GHqEXTfP+TvykIsY5xg4Ee4kdoZg8jUu31p4miFImsGn3KA9lYm7oAYTbxMCXg0i+27baW2/1JV5472vuIXhGXPEuIn6ga4MEWtHQ2Fa7Kky4zZHzKIOyaOq7Zcl5l20P8hnBPBCy0vkt+OJ9VmRX8YpppP8opLwWQXs=
---

# SPEC.md — 垂直科研全流程Agent API契约文档

> **版本**: v1.4  
> **最后更新**: 2026-07-04  
> **变更**: 全部 62 项代码质量缺陷修复完成（P0 13/P1 25/P2 13/P3 11），详见 docs/ISSUE_TRACKER.md

---

## 模块编号映射表

> 本章节号与 M-number 并非一一对应。以下为交叉映射，供文档交叉引用时使用。

| 章节号 | M-number | 模块名称 |
|--------|----------|---------|
| 模块0 | M0 | 基础设施 |
| 模块1 | M1 | 用户体系 |
| 模块2 | M2 | 文献检索 |
| 模块3 | M3 | 文献阅读+个人知识库 |
| 模块4 | M5 | AI写作辅助 |
| 模块5 | M6 | Docker仿真沙箱 |
| 模块6 | M7 | 四级协作空间 |
| 模块7 | M8 | 防篡改日志 |
| 模块8 | M9 | 算法商城 |
| 模块9 | M1-ext | 核心服务增强 |
| 模块10 | M3-ext | 知识库增强 |
| 模块11 | — | 安全与分享 |
| 模块12 | — | 预编排工作流 |

---

## 目录

- [第1章：产品定义](#第1章产品定义)
- [第2章：功能模块详细规格](#第2章功能模块详细规格)
  - [模块0：基础设施 (M0)](#模块0基础设施-m0)
  - [模块1：用户体系 (M1)](#模块1用户体系-m1)
  - [模块2：文献检索 (M2)](#模块2文献检索-m2)
  - [模块3：文献阅读+个人知识库 (M3)](#模块3文献阅读个人知识库-m3)
  - [模块4：AI写作辅助 (M5)](#模块4ai写作辅助-m5)
    - [Plan 模式](#plan-模式-p0-a)
    - [LaTeX + Mermaid 渲染](#latex--mermaid-渲染-p0-f)
  - [模块5：Docker仿真沙箱 (M6)](#模块5docker仿真沙箱-m6)
    - [科研绘图 Skill](#科研绘图-skill-p0-h)
    - [论文配图自动化](#论文配图自动化-p0-l)
  - [模块6：四级协作空间 (M7)](#模块6四级协作空间-m7)
  - [模块7：防篡改日志 (M8)](#模块7防篡改日志-m8)
  - [模块8：算法商城 (M9)](#模块8算法商城-m9)
  - [模块9：核心服务增强 (M1-ext)](#模块9核心服务增强-m1-ext)
  - [模块10：知识库增强 (M3-ext)](#模块10知识库增强-m3-ext)
  - [模块11：安全与分享](#模块11安全与分享)
  - [模块12：预编排工作流](#模块12预编排工作流)
- [第3章：数据模型](#第3章数据模型)
- [第4章：通用规范](#第4章通用规范)
- [第5章：开发顺序与依赖关系图](#第5章开发顺序与依赖关系图)
- [第6章：验收Checklist](#第6章验收checklist)

---

# 第1章：产品定义

## 1.1 一句话定位

国内唯一全链路科研垂直Agent平台，覆盖「本科生 → 硕士生 → 博士生 → 导师 → 实验室 → 高校三管理部门」，集文献检索、硬件实验、仿真算法、论文专利、校内管理、学术诚信溯源于一体，主打高校B端私有化采购 + C端师生订阅双市场。

## 1.2 目标用户画像

| 用户角色 | 核心痛点 | 本产品解决方案 |
|---------|---------|--------------|
| **本科生** | 课程论文无从下手、毕业设计缺乏文献支撑、检索技能薄弱 | 智能文献检索入门引导 + AI写作辅助 + 参考文献格式自动生成 |
| **硕士生** | 文献管理混乱、实验数据散落、论文写作效率低 | 个人知识库 + 文献批注 + AI润色降重 + 参考文献格式化导出 |
| **博士生** | 深度文献综述耗时巨大、仿真环境搭建复杂、专利申报流程繁琐、投稿返修跟踪困难 | 多源文献聚合 + Docker沙箱一键仿真 + AI综述初稿 + 投稿状态追踪 |
| **导师** | 课题组管理碎片化、成果台账人工维护、任务下发靠群聊、经费使用不透明 | 四级协作空间 + 任务下发/提交闭环 + 成果自动归档 + 经费可视化管控 |
| **高校三部门** | 图书馆资源利用率低、教务处学术不端检测被动、科研处成果统计靠Excel | 图书馆资源管理面板 + 防篡改研学日志（学术诚信溯源）+ 成果自动统计报表 |

## 1.3 核心价值主张

不是"又一个文献检索工具"，而是**"科研全流程操作系统"**。

```
选题 → 文献 → 实验 → 写作 → 专利 → 投稿 → 归档 → 团队协作
  └──────────────── 一个平台闭环完成 ────────────────┘
                    所有数据永久留存
```

**差异化对比：**

| 维度 | 知网/万方 | Zotero | Overleaf | 本产品 |
|------|----------|--------|----------|--------|
| 文献检索 | ✅ | ❌ | ❌ | ✅ 多源聚合 |
| 文献管理 | ❌ | ✅ | ❌ | ✅ 知识库+批注 |
| AI写作 | ❌ | ❌ | ❌ | ✅ 溯源标注 |
| 仿真实验 | ❌ | ❌ | ❌ | ✅ Docker沙箱 |
| 团队协作 | ❌ | ❌ | ✅ 仅写作 | ✅ 全流程四级空间 |
| 学术诚信 | ❌ | ❌ | ❌ | ✅ 链式哈希防篡改 |
| 高校管理 | ❌ | ❌ | ❌ | ✅ 三部门面板 |

---

# 第2章：功能模块详细规格

---

## 模块0：基础设施 (M0)

### 功能概述
提供项目骨架、数据库连接、鉴权中间件、统一错误处理、日志记录等基础能力，是所有上层模块的运行时底座。

### 用户场景

**场景1：系统运维人员部署健康检查**
运维人员需要确认服务是否正常运行，通过 `/health` 端点获取服务状态、数据库连接状态及版本信息，用于监控告警系统集成。

**场景2：前端应用获取公共配置**
前端启动时调用配置接口，获取当前环境（生产/测试）、文件上传大小限制、支持的OAuth登录方式列表等公开配置，无需登录即可访问。

**场景3：后端中间件拦截未授权请求**
任意API请求到达时，鉴权中间件检查请求头中的 `Authorization: Bearer {token}`，若缺失或过期则返回 `1002`（未登录）或 `1003`（Token过期），统一拦截无需每个接口自行判断。

### 核心价值
- 不用此模块：每个微服务各自实现鉴权和错误处理，碎片化且存在安全漏洞
- 用了此模块：所有API共享同一套鉴权、日志、错误码体系，零成本接入
- 与竞品差异：采用 FastAPI 中间件 + PostgreSQL pgvector，原生支持向量检索，为后续AI语义搜索预留基础设施

### API端点清单

#### `GET /health`

功能说明：健康检查

请求参数：无

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "db_connected": true,
    "uptime_seconds": 3600
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`5000` 数据库连接失败

---

#### `GET /api/v1/health`

功能说明：健康检查（v1）

请求参数：无

响应格式：同 `/health`，额外包含 Redis 连接状态

---

#### `GET /api/v1/health/db`

功能说明：数据库健康检查

请求参数：无

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "db_connected": true,
    "db_version": "PostgreSQL 15.8",
    "pool_size": 20,
    "active_connections": 3
  }
}
```

---

#### `GET /api/v2/health`

功能说明：健康检查（v2）

请求参数：无

响应格式：同 `/api/v1/health`

---

### 模型聊天与 Provider 管理

> SciAgent 支持多 AI 模型提供商（混元、DeepSeek 等）的统一网关管理。用户可配置个人使用的模型组合。

#### `POST /api/v1/models/chat`

功能说明：发送对话消息（同步）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 否 | 对话ID（新建对话则留空） |
| model | string | 是 | 模型名称，如 `
hunyuan-turbo` |
| messages | array[object] | 是 | 消息列表 [{role, content}] |
| temperature | float | 否 | 采样温度（0.0~2.0，默认0.7） |
| max_tokens | integer | 否 | 最大输出长度 |

#### `POST /api/v1/models/chat/stream`

功能说明：发送对话消息（SSE 流式）

参数同 `POST /api/v1/models/chat`，响应为 SSE 流式输出。

#### `GET /api/v1/models/providers`

功能说明：获取所有模型提供商

请求头：`Authorization: Bearer {access_token}`（仅管理员）

#### `POST /api/v1/models/providers`

功能说明：注册新模型提供商

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 提供商名称 |
| base_url | string | 是 | API 端点地址 |
| api_key | string | 是 | API 密钥 |
| models | array[string] | 是 | 支持的模型列表 |
| is_enabled | boolean | 否 | 是否启用 |

#### `PUT /api/v1/models/providers/{id}`

功能说明：更新提供商配置

#### `DELETE /api/v1/models/providers/{id}`

功能说明：删除提供商

#### `GET /api/v1/models/configs`

功能说明：获取当前用户的模型配置

请求头：`Authorization: Bearer {access_token}`

#### `POST /api/v1/models/configs`

功能说明：创建个人模型配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_name | string | 是 | 模型名称 |
| provider | string | 是 | 提供商名称 |
| parameters | object | 否 | 自定义参数（temperature/max_tokens 等） |

#### `PUT /api/v1/models/configs/{id}`

功能说明：更新模型配置

#### `DELETE /api/v1/models/configs/{id}`

功能说明：删除模型配置

#### `GET /api/v1/models/available`

功能说明：获取当前可用的模型列表

请求头：`Authorization: Bearer {access_token}`

---

### 定时任务

#### `GET /api/v1/scheduled-tasks`

功能说明：获取当前用户的定时任务列表

请求头：`Authorization: Bearer {access_token}`

#### `POST /api/v1/scheduled-tasks`

功能说明：创建定时任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 任务类型：search_alert / literature_push / report_generation |
| cron_expression | string | 是 | Cron 表达式 |
| params | object | 否 | 任务参数 |

#### `DELETE /api/v1/scheduled-tasks/{id}`

功能说明：删除定时任务

---

#### `GET /api/v1/config`

功能说明：获取前端公共配置（无需鉴权）

请求参数：无

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "env": "production",
    "max_upload_size_mb": 50,
    "oauth_providers": ["wechat"],
    "app_name": "SciAgent",
    "version": "1.0.0"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 模块1：用户体系 (M1)

### 功能概述
提供多方式注册/登录、JWT Token鉴权、个人信息管理、角色权限控制，是整个平台的身份认证与授权中心。

### 用户场景

**场景1：本科生首次注册并登录**
大一新生张三通过邮箱 `zhangsan@university.edu.cn` 注册账号，系统发送验证邮件，张三点击验证链接后设置密码完成注册。之后使用邮箱+密码登录，获取 access_token，进入平台开始文献检索。

**场景2：导师通过手机号快速登录**
导师李教授在出差途中，使用手机号+短信验证码快速登录，查看课题组最新任务提交情况，审批学生的实验方案。Token 2小时后自动过期，使用 refresh_token 静默续期，无需重新输入验证码。

**场景3：校级管理员配置角色权限**
学校信息化办公室管理员将某位导师的账号升级为"校级管理员"角色，该导师获得全校范围的防篡改日志审计权限和成果统计报表访问权限。

### 核心价值
- 不用此模块：各自实现登录导致安全漏洞，角色权限混乱
- 用了此模块：统一的JWT鉴权体系，access_token短时效+refresh_token长时效的安全策略，四级角色精细权限控制
- 与竞品差异：微信扫码登录接口预留，为高校企业微信集成做准备；角色体系支持导师管理员和校级管理员，覆盖B端采购需求

### API端点清单

#### `POST /api/v1/auth/register/email`

功能说明：邮箱注册

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码（最少8位，含大小写+数字） |
| nickname | string | 否 | 昵称 |

请求示例：
```json
{
  "email": "zhangsan@tsinghua.edu.cn",
  "password": "SciAgent2026!",
  "nickname": "张三"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 10001,
    "email": "zhangsan@tsinghua.edu.cn",
    "nickname": "张三",
    "email_verified": false
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 参数校验失败（邮箱格式错误/密码太弱）、`2002` 邮箱已被注册

---

#### `POST /api/v1/auth/register/phone`

功能说明：手机号注册

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号（11位） |
| sms_code | string | 是 | 短信验证码 |
| password | string | 是 | 密码 |
| nickname | string | 否 | 昵称 |

请求示例：
```json
{
  "phone": "13800138000",
  "sms_code": "123456",
  "password": "SciAgent2026!",
  "nickname": "李四"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 10002,
    "phone": "138****8000",
    "nickname": "李四",
    "phone_verified": true
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 参数校验失败、`1001` 短信验证码错误或过期、`2002` 手机号已被注册

---

#### `POST /api/v1/auth/send-sms`

功能说明：发送短信验证码

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| scene | string | 是 | 场景：register / login / reset_password |

请求示例：
```json
{
  "phone": "13800138000",
  "scene": "register"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": {
    "expire_seconds": 300
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 发送频率过高（60秒内重复发送）

---

#### `POST /api/v1/auth/login/email`

功能说明：邮箱+密码登录

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |

请求示例：
```json
{
  "email": "zhangsan@tsinghua.edu.cn",
  "password": "SciAgent2026!"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "user_id": 10001,
      "email": "zhangsan@tsinghua.edu.cn",
      "nickname": "张三",
      "role": "user",
      "institution": "清华大学",
      "avatar_url": "https://cdn.sciagent.cn/avatars/10001.png"
    }
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 邮箱或密码错误、`1003` 账号已被禁用

---

#### `POST /api/v1/auth/login/phone`

功能说明：手机号+验证码登录

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| sms_code | string | 是 | 短信验证码 |

请求示例：
```json
{
  "phone": "13800138000",
  "sms_code": "123456"
}
```

响应格式：（同邮箱登录，返回 Token + 用户信息）

---

#### `POST /api/v1/auth/login/wechat`

功能说明：微信扫码登录（预留接口）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 微信OAuth授权码 |

请求示例：
```json
{
  "code": "081abc123def456"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "user_id": 10003,
      "nickname": "王五",
      "role": "user",
      "wechat_union_id": "oxxxxx",
      "avatar_url": "https://thirdwx.qlogo.cn/xxxx"
    }
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/auth/refresh`

功能说明：刷新Token

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

请求示例：
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 7200
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1003` refresh_token 过期或无效

---

#### `POST /api/v1/auth/logout`

功能说明：登出（使当前Token失效）

请求头：`Authorization: Bearer {access_token}`

请求参数：无

响应格式：
```json
{
  "code": 0,
  "message": "已登出",
  "data": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/auth/reset-password`

功能说明：密码找回/重置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是（邮箱方式时） | 邮箱地址（与phone二选一） |
| phone | string | 是（手机方式时） | 手机号（与email二选一） |
| sms_code | string | 否 | 短信验证码（手机方式必填） |
| new_password | string | 是 | 新密码 |

请求示例：
```json
{
  "email": "zhangsan@tsinghua.edu.cn",
  "new_password": "NewPass2026!"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "密码重置成功，请重新登录",
  "data": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/auth/reset-password-confirm`

功能说明：确认密码重置（邮箱验证 Token 方式）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 邮箱中的重置 Token |
| new_password | string | 是 | 新密码 |

---

#### `POST /api/v1/auth/me/change-password`

功能说明：修改密码（已登录状态）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码 |

---

#### `GET /api/v1/user/profile`

功能说明：获取个人信息

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 10001,
    "email": "zhangsan@tsinghua.edu.cn",
    "phone": "138****8000",
    "nickname": "张三",
    "avatar_url": "https://cdn.sciagent.cn/avatars/10001.png",
    "role": "user",
    "institution": "清华大学",
    "department": "计算机科学与技术系",
    "created_at": "2026-01-15T08:30:00Z",
    "updated_at": "2026-06-20T14:22:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `PUT /api/v1/user/profile`

功能说明：更新个人信息

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar_url | string | 否 | 头像URL |
| institution | string | 否 | 所属机构 |
| department | string | 否 | 院系/部门 |

请求示例：
```json
{
  "nickname": "张三（计算机系）",
  "department": "计算机科学与技术系"
}
```

响应格式：（同 GET /api/v1/user/profile）

---

#### `PUT /api/v1/admin/users/{user_id}/role`

功能说明：管理员变更用户角色

请求头：`Authorization: Bearer {access_token}`（需要校级管理员权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是（路径参数） | 目标用户ID |
| role | string | 是（请求体） | 新角色：user / admin / super_admin |

请求示例：
```json
{
  "role": "admin"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "角色更新成功",
  "data": {
    "user_id": 10001,
    "role": "admin"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1004` 权限不足、`2001` 用户不存在

---

## 模块2：文献检索 (M2)

### 功能概述
提供多数据源聚合的文献检索能力，以科应API为主要数据源，架构预留多源接入能力。支持关键词检索、DOI精确查询、高级筛选、检索历史保存。

### 用户场景

**场景1：博士生深度文献调研**
博士生小王正在准备博士开题报告，主题是"基于强化学习的机器人路径规划"。他在搜索框中输入 `reinforcement learning AND path planning AND robotics`（英文）+ `强化学习 路径规划`（中文），设定年份范围为 2020-2026，期刊限定为 IEEE/ACM 系列。系统从科应API等多源聚合返回 156 条结果，按引用数排序。小王浏览前 40 条后将检索条件保存为"开题文献检索 v1"，以便后续复用。

**场景2：本科生按DOI查找一篇指定论文**
本科生小李的课程论文需要引用一篇特定论文，导师给了 DOI `10.1038/s41586-023-06891-8`。小李在DOI精确查询入口粘贴DOI，系统直接返回该论文完整信息（标题、作者、期刊、摘要、引用数、OA状态），无需在大量结果中翻找。

**场景3：导师追踪领域最新动态**
导师张教授希望追踪"钙钛矿太阳能电池"领域的最新论文。他设定检索条件后点击"保存检索"，系统每周自动执行检索并将新增结果推送到他的知识库"待阅"文件夹。

### 核心价值
- 不用此模块：师生需在知网、Web of Science、Google Scholar、arXiv等多个平台间反复切换检索，效率极低
- 用了此模块：一个搜索框覆盖科应API等多个数据源，结果聚合去重，一次检索替代多次跨平台操作
- 与竞品差异：架构层面预留多源聚合能力（非简单iframe嵌入），检索历史可保存为"课题"持续追踪新文献

### API端点清单

#### `GET /api/v2/papers/search`

功能说明：关键词检索文献（支持中英文，含 DOI 精确查询）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 检索关键词，支持AND/OR/NOT逻辑、中英文 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20，最大100 |
| year_from | integer | 否 | 起始年份 |
| year_to | integer | 否 | 截止年份 |
| journal | string | 否 | 期刊名称（模糊匹配） |
| author | string | 否 | 作者名（模糊匹配） |
| subject | string | 否 | 学科分类 |
| sort_by | string | 否 | 排序：relevance / citation_count / date |
| sources | string | 否 | 数据源限定，逗号分隔（默认全部）：keying |

请求示例：
```
GET /api/v2/papers/search?q=reinforcement+learning+AND+robotics&year_from=2020&year_to=2026&page=1&page_size=20&sort_by=citation_count
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "paper_id": "p_100001",
        "title": "Deep Reinforcement Learning for Robotic Manipulation: A Survey",
        "authors": ["Smith J.", "Wang L.", "Chen K."],
        "abstract": "This survey provides a comprehensive overview...",
        "doi": "10.1109/TRO.2025.1234567",
        "journal": "IEEE Transactions on Robotics",
        "year": 2025,
        "volume": "41",
        "issue": "3",
        "pages": "1234-1256",
        "citation_count": 89,
        "oa_status": "gold",
        "source": "keying",
        "subjects": ["cs.RO", "cs.AI"]
      }
    ],
    "total": 156,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`3001` 数据源不可用、`3002` 检索超时

---

> **已合并**：DOI 精确查询已合并到 `GET /api/v2/papers/search?doi={doi}` 参数中。无需独立端点。

---

#### `GET /api/v2/papers/history`

功能说明：获取检索历史

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "history_id": 5001,
        "query": "reinforcement learning AND path planning",
        "filters": {
          "year_from": 2020,
          "year_to": 2026,
          "journal": "IEEE"
        },
        "result_count": 156,
        "saved_as": "开题文献检索 v1",
        "created_at": "2026-06-15T10:30:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v2/papers/history`

功能说明：保存当前检索条件

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 检索关键词 |
| filters | object | 否 | 筛选条件 |
| saved_as | string | 否 | 自定义名称 |

请求示例：
```json
{
  "query": "reinforcement learning AND path planning",
  "filters": {
    "year_from": 2020,
    "year_to": 2026
  },
  "saved_as": "开题文献检索 v1"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "检索已保存",
  "data": {
    "history_id": 5001
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v2/papers/{paper_id}`

功能说明：获取文献详情

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| paper_id | string | 是（路径参数） | 文献ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "paper_id": "p_100001",
    "title": "Deep Reinforcement Learning for Robotic Manipulation: A Survey",
    "authors": ["Smith J.", "Wang L.", "Chen K."],
    "abstract": "This survey provides a comprehensive overview of deep reinforcement learning methods applied to robotic manipulation tasks. We categorize existing approaches into model-free, model-based, and sim-to-real transfer methods...",
    "doi": "10.1109/TRO.2025.1234567",
    "journal": "IEEE Transactions on Robotics",
    "year": 2025,
    "volume": "41",
    "issue": "3",
    "pages": "1234-1256",
    "citation_count": 89,
    "oa_status": "gold",
    "source": "keying",
    "subjects": ["cs.RO", "cs.AI"],
    "keywords": ["reinforcement learning", "robotics", "manipulation"],
    "references": [
      {"title": "Mastering the game of Go...", "doi": "10.1038/nature24270"},
      {"title": "Continuous control with deep reinforcement learning", "doi": "10.48550/arXiv.1509.02971"}
    ],
    "raw_metadata": {
      "publisher": "IEEE",
      "language": "en",
      "publication_date": "2025-03-15",
      "references_count": 234
    }
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`2001` 文献不存在

---

## 模块3：文献阅读+个人知识库 (M3)

### 功能概述
提供文献收藏、分类管理、批注高亮、参考文献格式导出、引用关系图谱、阅读历史记录等个人知识管理能力。

### 用户场景

**场景1：硕士生构建个人知识库**
硕士生小陈正在进行"联邦学习隐私保护"方向的论文阅读。他将检索到的 45 篇相关论文按主题分类到三个文件夹：`差分隐私方法`、`同态加密方法`、`安全多方计算`。对每篇文献阅读后标记状态：`待读/已读/精读`，并将关键论文设为收藏。论文阅读过程中对核心段落做高亮标注和个人笔记。

**场景2：博士生导出参考文献**
博士生小刘的毕业论文需要插入参考文献，格式要求为 GB/T 7714。他在知识库中勾选已读的 87 篇文献，一键导出为 GB/T 7714 格式的 `.bib` 文件，直接导入 LaTeX 项目。同时支持 APA、IEEE、MLA 格式切换。

**场景3：导师通过引用关系图谱发现关键文献**
导师张教授对某篇综述论文使用"引用关系图谱"功能，系统可视化展示该论文的引用链：被哪些论文引用、引用了哪些经典文献。图谱中高亮显示高被引论文，帮助课题组快速定位该领域的奠基性工作。

### 核心价值
- 不用此模块：文献散落在本地文件夹，格式引用手动复制粘贴易出错，无法追踪阅读进度
- 用了此模块：云端知识库永久留存，格式化引用一键导出，阅读批注与文献绑定不丢失
- 与竞品差异：Zotero 仅管理不分析；本产品融合了引用关系图谱，可视化呈现知识脉络

### API端点清单

#### `POST /api/v3/papers`

功能说明：添加文献到个人知识库

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| paper_id | string | 是 | 文献ID |
| folder | string | 否 | 目标文件夹路径，如 `差分隐私方法` |
| tags | array[string] | 否 | 标签列表 |

请求示例：
```json
{
  "paper_id": "p_100001",
  "folder": "差分隐私方法",
  "tags": ["联邦学习", "核心论文"]
}
```

响应格式：
```json
{
  "code": 0,
  "message": "已添加到知识库",
  "data": {
    "library_id": 20001,
    "paper_id": "p_100001",
    "folder": "差分隐私方法",
    "tags": ["联邦学习", "核心论文"],
    "added_at": "2026-07-02T09:15:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`2002` 文献已在知识库中

---

#### `GET /api/v3/papers`

功能说明：获取知识库文献列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| folder | string | 否 | 按文件夹筛选 |
| tag | string | 否 | 按标签筛选 |
| read_status | string | 否 | 按阅读状态：unread / reading / finished |
| is_favorited | boolean | 否 | 是否仅收藏 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "library_id": 20001,
        "paper": {
          "paper_id": "p_100001",
          "title": "Deep Reinforcement Learning for Robotic Manipulation",
          "authors": ["Smith J.", "Wang L."],
          "journal": "IEEE TRO",
          "year": 2025,
          "citation_count": 89
        },
        "folder": "差分隐私方法",
        "tags": ["联邦学习", "核心论文"],
        "is_favorited": true,
        "read_status": "finished",
        "notes_count": 3,
        "added_at": "2026-07-02T09:15:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `PUT /api/v3/papers/{library_id}`

功能说明：更新知识库文献信息（移动文件夹、修改标签、标记状态）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_id | integer | 是（路径参数） | 知识库条目ID |
| folder | string | 否 | 新文件夹 |
| tags | array[string] | 否 | 新标签列表（覆盖） |
| read_status | string | 否 | 阅读状态：unread / reading / finished |
| is_favorited | boolean | 否 | 是否收藏 |

请求示例：
```json
{
  "folder": "同态加密方法",
  "read_status": "reading",
  "is_favorited": true
}
```

响应格式：
```json
{
  "code": 0,
  "message": "更新成功",
  "data": {
    "library_id": 20001,
    "folder": "同态加密方法",
    "read_status": "reading",
    "is_favorited": true
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `DELETE /api/v3/papers/{library_id}`

功能说明：从知识库移除文献

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_id | integer | 是（路径参数） | 知识库条目ID |

响应格式：
```json
{
  "code": 0,
  "message": "已从知识库移除",
  "data": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v3/annotations`

功能说明：添加文献批注（高亮/笔记）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_id | integer | 是 | 知识库条目ID |
| highlighted_text | string | 否 | 高亮文本片段 |
| note | string | 否 | 笔记内容 |
| position_data | object | 否 | 位置信息（页码、段落、坐标） |

请求示例：
```json
{
  "library_id": 20001,
  "highlighted_text": "federated learning enables collaborative model training without sharing raw data",
  "note": "联邦学习的核心定义，用于论文引言部分",
  "position_data": {
    "page": 3,
    "paragraph": 2,
    "start_offset": 120,
    "end_offset": 210
  }
}
```

响应格式：
```json
{
  "code": 0,
  "message": "批注已保存",
  "data": {
    "annotation_id": 30001,
    "created_at": "2026-07-02T09:30:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v3/annotations`

功能说明：获取文献批注列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_id | integer | 是 | 知识库条目ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "annotations": [
      {
        "annotation_id": 30001,
        "highlighted_text": "federated learning enables collaborative model training...",
        "note": "联邦学习的核心定义",
        "position_data": {"page": 3, "paragraph": 2},
        "created_at": "2026-07-02T09:30:00Z"
      }
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `DELETE /api/v3/annotations/{annotation_id}`

功能说明：删除批注

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "批注已删除",
  "data": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v3/export-citation`

功能说明：导出参考文献格式

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_ids | array[integer] | 是 | 知识库条目ID列表 |
| format | string | 是 | 格式：gbt7714 / apa / ieee / mla |
| output | string | 否 | 输出形式：json / bibtex / plain_text，默认 json |

请求示例：
```
GET /api/v3/export-citation?library_ids=20001,20002,20003&format=gbt7714&output=bibtex
```

响应格式（bibtex）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "format": "gbt7714",
    "output": "bibtex",
    "citations": "@article{smith2025deep,\n  author={Smith J. and Wang L. and Chen K.},\n  title={Deep Reinforcement Learning for Robotic Manipulation: A Survey},\n  journal={IEEE Transactions on Robotics},\n  year={2025},\n  volume={41},\n  number={3},\n  pages={1234-1256}\n}\n..."
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v3/citation-graph/{paper_id}`

功能说明：获取文献引用关系图谱

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| paper_id | string | 是（路径参数） | 文献ID |
| depth | integer | 否 | 图谱深度，默认2，最大3 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "center": {
      "paper_id": "p_100001",
      "title": "Deep RL for Robotic Manipulation"
    },
    "nodes": [
      {"paper_id": "p_100002", "title": "Mastering Go", "cited_by_center": true, "citation_count": 12000},
      {"paper_id": "p_100003", "title": "Sim-to-Real Transfer", "cites_center": true, "citation_count": 340}
    ],
    "edges": [
      {"from": "p_100001", "to": "p_100002", "relation": "cites"},
      {"from": "p_100003", "to": "p_100001", "relation": "cites"}
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v3/reading-history`

功能说明：获取阅读历史记录

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "paper_id": "p_100001",
        "title": "Deep RL for Robotic Manipulation",
        "last_read_at": "2026-07-02T14:30:00Z",
        "read_duration_seconds": 1800,
        "read_pages": 15
      }
    ],
    "total": 67,
    "page": 1,
    "page_size": 20,
    "total_pages": 4
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v3/folders`

功能说明：创建知识库文件夹

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 文件夹名称 |
| parent_folder | string | 否 | 父文件夹名称 |

请求示例：
```json
{
  "name": "差分隐私方法",
  "parent_folder": "联邦学习"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "文件夹已创建",
  "data": {
    "folder_path": "联邦学习/差分隐私方法"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v3/folders`

功能说明：获取知识库文件夹树

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "folders": [
      {
        "name": "联邦学习",
        "paper_count": 25,
        "children": [
          {"name": "差分隐私方法", "paper_count": 12},
          {"name": "同态加密方法", "paper_count": 8},
          {"name": "安全多方计算", "paper_count": 5}
        ]
      }
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 模块4：AI写作辅助 (M5)

### 功能概述
基于知识库文献提供AI写作辅助能力，包括文献综述初稿生成、中英文学术润色、语句降重、AI内容溯源标注、目标期刊格式匹配、参考文献自动格式化插入。

### 用户场景

**场景1：博士生生成文献综述初稿**
博士生小王在知识库中选定了 35 篇核心文献，点击"生成综述初稿"。AI分析这些文献的主题分布、时间脉络和方法演进，生成一篇结构化的综述初稿（含引言、方法分类、研究进展、未来展望）。每段 AI 生成内容末尾自动标注 `[AI生成, 参考文献: Smith 2025, Wang 2024, Chen 2023]` 的来源溯源标记。小王基于初稿修改完善，最终产出自己的综述论文。

**场景2：硕士生进行学术降重**
硕士生小陈写完了论文初稿，查重率偏高。他使用"AI降重"功能，选定需要降重的段落。AI在保持学术原意的前提下，对句式结构进行改写，用同义学术表达替换高频词汇。降重后的段落仍保留原有引用关系，且不改变技术事实和数据。

**场景3：本科生按目标期刊格式化投稿**
本科生小李的课程论文导师建议投某学报。小李在AI写作模块中选择目标期刊《计算机学报》，系统自动调整论文格式：标题层级、参考文献引用风格、图表编号规范、中英文摘要格式。参考文献自动从知识库中拉取并按期刊要求格式化插入。

### 核心价值
- 不用此模块：写作效率低，格式调整耗时，查重降重靠人工盲改
- 用了此模块：AI辅助提效但不替代学术判断，每段AI内容有源可查（溯源机制为学术诚信保驾护航）
- 与竞品差异：市面上AI写作工具都不做溯源标注——本产品的 AI 生成内容**必须**标注生成来源和引用文献，这是与 ChatGPT 类通用工具的根本区别

### API端点清单

#### `POST /api/v5/writing/literature-review`

功能说明：根据选定文献生成文献综述初稿

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_ids | array[integer] | 是 | 知识库中选定的文献ID列表，最多50篇 |
| topic | string | 否 | 综述主题（不填则自动推断） |
| language | string | 否 | 输出语言：zh / en，默认 zh |
| structure | array[string] | 否 | 自定义结构，如 ["引言", "方法分类", "研究进展"] |

请求示例：
```json
{
  "library_ids": [20001, 20002, 20005, 20008],
  "topic": "联邦学习中的差分隐私保护方法",
  "language": "zh",
  "structure": ["引言", "方法分类", "代表性工作", "研究挑战", "未来展望"]
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40001,
    "title": "联邦学习中的差分隐私保护方法——文献综述",
    "content": "## 引言\n\n联邦学习（Federated Learning）作为一种分布式机器学习范式...[AI生成, 参考文献: McMahan 2017]\n\n## 方法分类\n\n当前基于差分隐私的联邦学习保护方法可分为三类...[AI生成, 参考文献: Abadi 2016, Geyer 2017]\n\n...",
    "ai_generated_ratio": 0.85,
    "source_papers": [
      {"paper_id": "p_100001", "title": "Deep RL for Robotic Manipulation", "sections": ["引言"]},
      {"paper_id": "p_100005", "title": "DP-SGD in Federated Settings", "sections": ["方法分类", "代表性工作"]}
    ],
    "status": "draft",
    "created_at": "2026-07-02T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 文献数量为0或超过50篇

---

#### `POST /api/v5/writing/polish`

功能说明：中英文学术润色

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待润色文本 |
| language | string | 是 | 目标语言：zh / en |
| style | string | 否 | 风格：academic（默认）/ concise / elaborate |

请求示例：
```json
{
  "text": "我们的方法在多个数据集上都取得了较好的结果，比其他方法都要好一些。",
  "language": "zh",
  "style": "academic"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "polished_text": "本方法在ImageNet、CIFAR-100及COCO三个基准数据集上均取得了最优性能，相较于基线方法平均提升3.2个百分点。[AI润色，原始内容由用户提供]",
    "changes_summary": "将模糊表述'较好'替换为具体数值，将'比其他方法好'改为学术化表述'最优性能'，补充数据集名称。"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v5/writing/rephrase`

功能说明：语句降重（保持学术原意前提下改写）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待降重文本 |
| language | string | 是 | 语言：zh / en |
| intensity | string | 否 | 降重强度：light / moderate / aggressive，默认 moderate |

请求示例：
```json
{
  "text": "Federated learning is a machine learning setting where the goal is to train a high-quality centralized model while training data remains distributed over a large number of clients.",
  "language": "en",
  "intensity": "moderate"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "rephrased_text": "Federated learning constitutes a distributed ML paradigm wherein a central model achieves high performance without raw data leaving the edge devices—training occurs locally across numerous clients, with only model updates shared. [AI降重，原始语义保留: McMahan et al., 2017]",
    "similarity_score": 0.42,
    "note": "相似度越低表示改写幅度越大。当前改写保持了原意但调整了句式结构和词汇选择。"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v5/writing/documents/{document_id}/trace`

功能说明：获取AI生成内容溯源详情

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是（路径参数） | 文档ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40001,
    "ai_generated_ratio": 0.85,
    "segments": [
      {
        "text": "联邦学习作为一种分布式机器学习范式...",
        "is_ai_generated": true,
        "source_papers": [
          {"paper_id": "p_100001", "title": "Communication-Efficient Learning of Deep Networks", "relevance": "high"}
        ]
      },
      {
        "text": "我们在此基础上提出了改进方案...",
        "is_ai_generated": false,
        "source_papers": []
      }
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v5/writing/format-for-journal`

功能说明：按目标期刊格式化文档

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |
| journal_name | string | 是 | 目标期刊名称 |

请求示例：
```json
{
  "document_id": 40001,
  "journal_name": "计算机学报"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "格式化完成",
  "data": {
    "document_id": 40001,
    "journal": "计算机学报",
    "changes": [
      "标题层级调整为 1/1.1/1.1.1 三级结构",
      "参考文献格式切换为 GB/T 7714",
      "摘要字数限制 300 字以内"
    ],
    "updated_at": "2026-07-02T10:30:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v5/writing/insert-citation`

功能说明：在文档指定位置自动格式化插入参考文献

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |
| library_ids | array[integer] | 是 | 要引用的知识库条目ID列表 |
| insert_position | integer | 是 | 插入位置（文档内偏移量） |
| format | string | 否 | 引用格式：numeric / author_year，默认 numeric |

请求示例：
```json
{
  "document_id": 40001,
  "library_ids": [20001, 20002],
  "insert_position": 450,
  "format": "numeric"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "引用已插入",
  "data": {
    "document_id": 40001,
    "inserted_citation": "[1,2]",
    "references_appended": [
      "[1] Smith J., Wang L. Deep RL for Robotic Manipulation. IEEE TRO, 2025.",
      "[2] Geyer R.C. et al. Differentially Private Federated Learning. arXiv, 2017."
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v5/writing/documents`

功能说明：获取写作文档列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 筛选状态：draft / writing / finished |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "document_id": 40001,
        "title": "联邦学习综述",
        "status": "draft",
        "ai_generated_ratio": 0.85,
        "updated_at": "2026-07-02T10:30:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `PUT /api/v5/writing/documents/{document_id}`

功能说明：更新文档内容

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是（路径参数） | 文档ID |
| content | string | 否 | 更新后的内容 |
| title | string | 否 | 更新后的标题 |

请求示例：
```json
{
  "content": "## 引言\n\n更新后的内容..."
}
```

响应格式：
```json
{
  "code": 0,
  "message": "文档已更新",
  "data": {
    "document_id": 40001,
    "updated_at": "2026-07-02T10:45:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### Plan 模式（P0-A）

#### 功能概述
强制五阶段写作流程，将 AI 写作从"一键生成"升级为"结构化协作"模式。用户在大纲阶段即可介入调整，每一节独立生成、独立确认，最终合并为完整文档，确保学术逻辑严谨可控。

#### 五阶段流程

```
大纲生成 → 用户确认 → 逐节生成 → 逐节确认 → 最终合并
```

1. **大纲生成**：AI 根据主题和知识库文献自动生成结构化大纲（含章节标题、各节要点摘要）
2. **用户确认**：用户审阅大纲，可增删改章节、调整顺序、修改要点
3. **逐节生成**：按确认后的大纲逐节生成正文（含引用标注），每次只生成一节
4. **逐节确认**：用户对每节内容确认/修改/重新生成，确认后锁定该节
5. **最终合并**：所有节点确认完毕后，合并为完整文档，生成溯源报告

#### API端点清单

##### `POST /api/v5/writing/plan`

功能说明：生成写作大纲

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| topic | string | 是 | 写作主题 |
| library_ids | array[integer] | 否 | 关联的知识库文献ID列表 |
| language | string | 否 | 输出语言：zh / en，默认 zh |
| requirements | string | 否 | 额外要求（如字数限制、风格偏好） |

请求示例：
```json
{
  "topic": "联邦学习中的差分隐私保护方法综述",
  "library_ids": [20001, 20002, 20005],
  "language": "zh",
  "requirements": "综述长度约8000字，面向期刊投稿"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": "plan_a1b2c3d4",
    "topic": "联邦学习中的差分隐私保护方法综述",
    "sections": [
      {
        "sid": "s1",
        "title": "引言",
        "summary": "介绍联邦学习背景及隐私保护需求，阐述综述目的和结构",
        "status": "pending",
        "content": null,
        "confirmed": false
      },
      {
        "sid": "s2",
        "title": "差分隐私基础",
        "summary": "回顾差分隐私的数学定义、隐私预算、组合定理等基础理论",
        "status": "pending",
        "content": null,
        "confirmed": false
      },
      {
        "sid": "s3",
        "title": "联邦学习中的差分隐私方法分类",
        "summary": "按用户级/样本级差分隐私分类综述现有方法",
        "status": "pending",
        "content": null,
        "confirmed": false
      },
      {
        "sid": "s4",
        "title": "研究挑战与未来方向",
        "summary": "总结当前方法的局限性并展望未来研究方向",
        "status": "pending",
        "content": null,
        "confirmed": false
      },
      {
        "sid": "s5",
        "title": "结论",
        "summary": "总结全文贡献与核心发现",
        "status": "pending",
        "content": null,
        "confirmed": false
      }
    ],
    "status": "outline_generated",
    "created_at": "2026-07-03T09:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v5/writing/plan/{plan_id}`

功能说明：查看大纲详情

请求头：`Authorization: Bearer {access_token}`

响应格式：同 `POST /api/v5/writing/plan` 的 data 部分，含各节当前生成状态。

---

##### `POST /api/v5/writing/plan/{plan_id}/sections/{sid}/generate`

功能说明：逐节生成正文

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| plan_id | string | 是（路径参数） | 大纲ID |
| sid | string | 是（路径参数） | 节ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": "plan_a1b2c3d4",
    "sid": "s2",
    "title": "差分隐私基础",
    "content": "## 差分隐私基础\n\n差分隐私（Differential Privacy, DP）由 Dwork 等人于 2006 年首次提出...[AI生成, 参考文献: Dwork 2006]\n\n...",
    "status": "generated",
    "confirmed": false
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v5/writing/plan/{plan_id}/finalize`

功能说明：确认合并所有节为完整文档

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| plan_id | string | 是（路径参数） | 大纲ID |

响应格式：
```json
{
  "code": 0,
  "message": "文档合并完成",
  "data": {
    "document_id": 40010,
    "title": "联邦学习中的差分隐私保护方法综述",
    "sections_count": 5,
    "ai_generated_ratio": 0.88,
    "status": "finished"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 存在未确认的节，无法合并

---

##### `GET /api/v5/writing/documents/{document_id}/trace`

功能说明：获取文档溯源报告（Plan模式文档同样适用）

请求头：`Authorization: Bearer {access_token}`

（响应格式同 M5 原有溯源端点，增加每节级别的溯源统计）

##### `GET /api/v5/writing/documents/{document_id}/atomic-trace`

功能说明：获取句子级原子溯源详情（v2.0 溯源格式）

请求头：`Authorization: Bearer {access_token}`

返回逐句的溯源信息，包含 `trace_type`（5 种：direct_citation / method_from / conclusion_from / ai_synthesis / ai_original）和 `confidence`（3 级：high / medium / low），详见 P0-D 原子溯源引擎说明。

#### 数据模型：WritingPlan

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| plan_id | VARCHAR(64) | UNIQUE, NOT NULL | 大纲唯一标识 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| topic | VARCHAR(500) | NOT NULL | 写作主题 |
| sections | JSONB | NOT NULL | 节列表，每项含 sid/title/summary/status/content/confirmed |
| status | VARCHAR(20) | DEFAULT 'outline_generated' | outline_generated / generating / finalized |
| language | VARCHAR(5) | DEFAULT 'zh' | 输出语言 |
| document_id | BIGINT | FK → documents.id, NULLABLE | 关联的最终文档ID（合并后赋值） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

---

### LaTeX + Mermaid 渲染（P0-F）

#### 功能概述
writing_service 文档内容模型升级，新增 `content_blocks` 字段支持混合内容块。文档不再只是纯 Markdown 文本，而是可包含 LaTeX 数学公式、Mermaid 图表、代码块、表格等结构化内容块，前端按块类型分别渲染。

#### ContentBlock 类型

| 类型 | 说明 | 渲染方式 |
|------|------|---------|
| `text` | Markdown 纯文本 | 标准 Markdown 渲染 |
| `latex` | LaTeX 数学公式（行内/块级） | MathJax / KaTeX 渲染 |
| `mermaid` | Mermaid 图表（流程图/时序图/甘特图等） | Mermaid.js 渲染 |
| `table` | 结构化表格 | 表格组件渲染 |
| `code` | 代码块（含语法高亮） | Prism.js / highlight.js 渲染 |

#### 数据模型变更

`documents` 表新增字段：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| content_blocks | JSONB | DEFAULT '[]' | 内容块列表，每项含 type/content/metadata |

content_blocks 示例：
```json
[
  {"type": "text", "content": "## 引言\n\n联邦学习作为一种分布式机器学习范式..."},
  {"type": "latex", "content": "\\epsilon-\\text{differential privacy}: \\Pr[M(D) \\in S] \\leq e^\\epsilon \\cdot \\Pr[M(D') \\in S]"},
  {"type": "mermaid", "content": "graph TD\n  A[用户数据] --> B[本地训练]\n  B --> C[梯度加密]\n  C --> D[中央聚合]"},
  {"type": "table", "content": "| 方法 | 隐私预算 ε | 准确率 |\n|------|-----------|--------|\n| DP-SGD | 8.0 | 92.3% |\n| PATE | 4.0 | 89.1% |"},
  {"type": "code", "content": "def dp_sgd(model, data, epsilon):\n    ..."}
]
```

> **向后兼容**：`content` 字段（纯 Markdown）保留，`content_blocks` 为可选增强。前端优先渲染 `content_blocks`，为空时回退渲染 `content`。

---

## 模块5：代码沙箱 (M6) - ✅ 已实现

### 功能概述
提供安全的代码执行环境。Python 代码通过 `subprocess`（timeout=30s）本地执行，R/Julia 等其他语言以 mock 模式返回。适用于论文实验复现、算法快速验证、教学演示等场景。

### 当前实现状态

| 端点 | 状态 | 说明 |
|------|------|------|
| `POST /api/v6/sandbox/execute` | ✅ | Python subprocess 执行，R/Julia mock |
| `GET /api/v6/sandbox/executions/{id}` | ✅ | 查询执行结果（mock 返回演示数据） |
| `GET /api/v6/sandbox/status` | ✅ | 服务健康状态 + supported_languages |

Docker 集成预留（`docker_available: false`），未来版本通过 Docker 沙箱实现完整隔离。

### API端点清单

#### `POST /api/v6/sandbox/execute`

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| language | string | 是 | `python` / `r` / `julia` |
| code | string | 是 | 代码内容 |
| timeout | integer | 否 | Python 时生效（1-30s），默认 30 |

请求示例：
```json
{ "language": "python", "code": "print(1+1)", "timeout": 30 }
```

响应格式：
```json
{
  "code": 0, "message": "success",
  "data": {
    "execution_id": "exec-a1b2c3d4",
    "language": "python",
    "stdout": "2\n", "stderr": "",
    "exit_code": 0, "status": "completed"
  }
}
```

#### `GET /api/v6/sandbox/executions/{execution_id}`

查询执行记录详情。mock 模式下返回演示数据。

#### `GET /api/v6/sandbox/status`

```json
{ "status": "ok", "mock_mode": false, "docker_available": false, "supported_languages": ["python", "r", "julia"] }
```

---

### 科研绘图 Skill（P0-H）

#### 功能概述
内置 5 类学术图表模板（柱状图、折线图、箱线图、热力图、火山图）及通用自定义渲染。在 Docker 沙箱内执行绘图代码，输出 300 DPI 的 base64 PNG 图像，确保字体嵌入、中英文混排正确渲染。

#### 5 类模板

| 模板 | 端点 | 适用场景 |
|------|------|---------|
| 柱状图 | `/api/v1/plot/bar` | 对比实验、消融研究、方法性能对比 |
| 折线图 | `/api/v1/plot/line` | 训练曲线、收敛分析、时间序列趋势 |
| 箱线图 | `/api/v1/plot/box` | 数据分布对比、异常值检测、多组统计 |
| 热力图 | `/api/v1/plot/heatmap` | 相关性矩阵、特征重要性、混淆矩阵 |
| 火山图 | `/api/v1/plot/volcano` | 差异表达分析、显著性 vs 效应量可视化 |

#### API端点清单

##### `POST /api/v1/plot/bar`

##### `POST /api/v1/plot/line`

##### `POST /api/v1/plot/box`

##### `POST /api/v1/plot/heatmap`

##### `POST /api/v1/plot/volcano`

功能说明：生成指定类型的学术图表（5 个端点参数结构类似，以 bar 为例）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| data | object | 是 | 绘图数据（x/y 轴数据、分组标签等） |
| title | string | 否 | 图表标题 |
| x_label | string | 否 | X 轴标签 |
| y_label | string | 否 | Y 轴标签 |
| style | string | 否 | 配色方案：nature/science/ieee/grayscale，默认 science |
| width | integer | 否 | 图像宽度（px），默认 1600 |
| height | integer | 否 | 图像高度（px），默认 1200 |

请求示例（柱状图）：
```json
{
  "data": {
    "categories": ["DP-SGD", "PATE", "FedAvg+DP", "Ours"],
    "values": [0.923, 0.891, 0.945, 0.967],
    "errors": [0.012, 0.015, 0.010, 0.008]
  },
  "title": "各方法在 CIFAR-10 上的准确率对比",
  "x_label": "方法",
  "y_label": "准确率",
  "style": "science"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "format": "png",
    "dpi": 300,
    "width_px": 1600,
    "height_px": 1200,
    "mime_type": "image/png"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v1/plot/templates`

功能说明：获取可用图表模板列表

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "templates": [
      {"type": "bar", "name": "柱状图", "description": "适用于方法对比和消融实验"},
      {"type": "line", "name": "折线图", "description": "适用于训练曲线和趋势分析"},
      {"type": "box", "name": "箱线图", "description": "适用于数据分布对比"},
      {"type": "heatmap", "name": "热力图", "description": "适用于相关性矩阵和混淆矩阵"},
      {"type": "volcano", "name": "火山图", "description": "适用于差异表达分析"}
    ],
    "custom_supported": true
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/plot/custom`

功能说明：自定义渲染（用户提供 matplotlib/seaborn 代码片段）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | matplotlib/seaborn 绘图代码（自动注入 plt.savefig） |
| data | object | 否 | 绘图数据（注入到代码执行上下文） |

请求示例：
```json
{
  "code": "import matplotlib.pyplot as plt\nfig, ax = plt.subplots()\nax.scatter(data['x'], data['y'], c=data['c'], cmap='viridis')\nax.set_title('Custom Scatter Plot')",
  "data": {
    "x": [1, 2, 3, 4, 5],
    "y": [10, 20, 25, 30, 35],
    "c": [0.1, 0.3, 0.5, 0.7, 0.9]
  }
}
```

响应格式：同模板端点，返回 base64 PNG。

---

### 论文配图自动化（P0-L）

#### 功能概述
对沙箱输出的原始图像进行学术级自动美化。统一 DPI 为 300、应用 seaborn 学术风格、优化字号与配色方案、自动添加编号题注。支持多图拼接为 panel 图和灰度转换。

#### API端点清单

##### `POST /api/v1/plot/enhance`

功能说明：自动美化图像

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image_base64 | string | 是 | 原始图像 base64 |
| style | string | 否 | 风格：seaborn / nature / ieee，默认 seaborn |
| target_dpi | integer | 否 | 目标 DPI，默认 300 |

请求示例：
```json
{
  "image_base64": "iVBORw0KGgo...",
  "style": "nature",
  "target_dpi": 300
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "image_base64": "iVBORw0KGgo...",
    "format": "png",
    "dpi": 300,
    "enhancements_applied": [
      "字体替换为 Times New Roman 10pt",
      "坐标轴样式优化",
      "配色方案切换为 nature 调色板",
      "分辨率提升至 300 DPI"
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/plot/panel`

功能说明：多图拼接为 panel 图（如 Figure 1(a)(b)(c)(d)）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| images | array[object] | 是 | 子图列表，每项含 image_base64 / label / caption |
| layout | string | 是 | 布局：grid_2x2 / grid_1x3 / grid_3x1 / horizontal / vertical |
| title | string | 否 | 总标题 |
| style | string | 否 | 风格，默认 seaborn |

请求示例：
```json
{
  "images": [
    {"image_base64": "...", "label": "(a)", "caption": "准确率对比"},
    {"image_base64": "...", "label": "(b)", "caption": "隐私预算分析"},
    {"image_base64": "...", "label": "(c)", "caption": "收敛曲线"},
    {"image_base64": "...", "label": "(d)", "caption": "通信开销"}
  ],
  "layout": "grid_2x2",
  "title": "Figure 1: Performance Evaluation of DP-FL Methods"
}
```

响应格式：同 enhance，返回拼接后的单张 base64 PNG。

---

##### `POST /api/v1/plot/grayscale`

功能说明：学术灰度转换（满足某些期刊印刷要求）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image_base64 | string | 是 | 原始图像 base64 |

响应格式：返回灰度版 base64 PNG。

---

## 模块6：四级协作空间 (M7)

### 功能概述
提供五级嵌套协作空间（校级 > 院系 > 导师课题组 > 班级 > 私人好友小组），支持文献共享池、任务下发与提交、科研动态流、共享资源额度分配。

### 用户场景

**场景1：导师创建课题组空间并下发任务**
导师张教授创建"智能机器人课题组"协作空间（级别：lab），邀请 8 名学生加入。他在空间中下发任务："下周组会前完成《Deep RL for Robotics》论文复现"，指定博士生小王为负责人。小王收到任务通知后，在截止日期前提交复现代码和实验报告。

**场景2：跨课题组文献共享**
计算机系的两个课题组"CV组"和"NLP组"在院系级别空间中共享文献池。CV组的一位学生发现一篇关于 CLIP 模型的综述，添加到院系共享文献池，NLP组的同学也能看到并收藏到自己的知识库。

**场景3：院系管理员查看科研动态**
院系教务秘书在院系空间中查看"科研动态流"，了解各课题组本周的文献阅读量、沙箱使用量、论文提交进展。系统自动生成周报模板供院系例会使用。

### 核心价值
- 不用此模块：课题组沟通靠微信群，文件靠网盘，任务靠口头传达，成果无归集
- 用了此模块：五级权限体系精准管理，任务闭环（下发→提交→反馈），文献/算力资源共享可控
- 与竞品差异：不是简单的"群组"功能，而是五级层级 + 精细角色（超级管理员/导师/博士组长/普通学生/只读访客）+ 资源配额分配的组合

### API端点清单

#### `POST /api/v1/workspaces`

功能说明：创建协作空间

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 空间名称 |
| level | string | 是 | 层级：school / college / lab / class / friends |
| parent_id | integer | 否 | 父空间ID（创建子空间时使用） |
| description | string | 否 | 空间描述 |

请求示例：
```json
{
  "name": "智能机器人课题组",
  "level": "lab",
  "parent_id": 10,
  "description": "张教授课题组，研究方向：机器人路径规划与强化学习"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "协作空间创建成功",
  "data": {
    "workspace_id": 100,
    "name": "智能机器人课题组",
    "level": "lab",
    "owner_id": 10010,
    "created_at": "2026-07-02T09:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/workspaces/{workspace_id}/members`

功能说明：邀请成员加入协作空间

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 被邀请用户ID |
| role | string | 是 | 角色：admin / leader / member / viewer |

请求示例：
```json
{
  "user_id": 10002,
  "role": "leader"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "成员已添加",
  "data": {
    "workspace_id": 100,
    "user_id": 10002,
    "role": "leader",
    "joined_at": "2026-07-02T09:05:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1004` 只有 super_admin 或 admin 可添加成员、`2002` 用户已在空间中

---

#### `GET /api/v1/workspaces/{workspace_id}/members`

功能说明：获取空间成员列表

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "members": [
      {
        "user_id": 10010,
        "nickname": "张教授",
        "role": "super_admin",
        "joined_at": "2026-06-01T08:00:00Z"
      },
      {
        "user_id": 10002,
        "nickname": "小王",
        "role": "leader",
        "joined_at": "2026-07-02T09:05:00Z"
      },
      {
        "user_id": 10003,
        "nickname": "小李",
        "role": "member",
        "joined_at": "2026-07-02T09:05:00Z"
      }
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `PUT /api/v1/workspaces/{workspace_id}/members/{user_id}`

功能说明：修改成员角色

请求头：`Authorization: Bearer {access_token}`（需要 super_admin 权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | string | 是（请求体） | 新角色：admin / leader / member / viewer |

请求示例：
```json
{
  "role": "admin"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "角色已更新",
  "data": {
    "workspace_id": 100,
    "user_id": 10002,
    "role": "admin"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}`

功能说明：移除成员

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

响应格式：
```json
{
  "code": 0,
  "message": "成员已移除",
  "data": null,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/workspaces/invitations/{id}/accept`

功能说明：接受协作空间邀请

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是（路径参数） | 邀请ID |

响应格式：
```json
{
  "code": 0,
  "message": "已加入协作空间",
  "data": {
    "workspace_id": 100,
    "role": "member"
  }
}
```

---

#### `POST /api/v1/workspaces/invitations/{id}/decline`

功能说明：拒绝协作空间邀请

请求头：`Authorization: Bearer {access_token}`

---

#### `POST /api/v1/workspaces/{workspace_id}/shared-papers`

功能说明：添加文献到协作空间共享池

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| library_ids | array[integer] | 是 | 知识库条目ID列表 |

请求示例：
```json
{
  "library_ids": [20001, 20002]
}
```

响应格式：
```json
{
  "code": 0,
  "message": "文献已共享",
  "data": {
    "shared_count": 2
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v1/workspaces/{workspace_id}/shared-papers`

功能说明：获取协作空间共享文献池

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "paper_id": "p_100001",
        "title": "Deep RL for Robotic Manipulation",
        "shared_by": {"user_id": 10002, "nickname": "小王"},
        "shared_at": "2026-07-02T09:15:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/workspaces/{workspace_id}/tasks`

功能说明：导师下发任务

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 任务标题 |
| description | string | 否 | 任务描述 |
| assignee_ids | array[integer] | 是 | 指派学生ID列表 |
| due_date | string | 否 | 截止日期（ISO 8601） |
| priority | string | 否 | 优先级：low / medium / high，默认 medium |

请求示例：
```json
{
  "title": "复现 Deep RL for Robotics 论文实验",
  "description": "使用Docker沙箱复现论文Section 4中的实验，产出代码和实验报告",
  "assignee_ids": [10002],
  "due_date": "2026-07-09T23:59:59Z",
  "priority": "high"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "任务已下发",
  "data": {
    "task_id": 50001,
    "title": "复现 Deep RL for Robotics 论文实验",
    "assignees": [10002],
    "due_date": "2026-07-09T23:59:59Z",
    "created_at": "2026-07-02T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v1/workspaces/{workspace_id}/tasks/{task_id}/submit`

功能说明：学生提交任务成果

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 否 | 提交说明 |
| attachments | array[object] | 否 | 附件（文件路径或沙箱文件引用） |

请求示例：
```json
{
  "content": "已完成论文复现，详见附件实验报告。主要发现：在MuJoCo环境中...",
  "attachments": [
    {"type": "document", "document_id": 40002},
    {"type": "sandbox_file", "session_id": "sess_abc123", "file_path": "/output/results.csv"}
  ]
}
```

响应格式：
```json
{
  "code": 0,
  "message": "任务已提交",
  "data": {
    "task_id": 50001,
    "submitter_id": 10002,
    "status": "submitted",
    "submitted_at": "2026-07-05T16:30:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v1/workspaces/{workspace_id}/feed`

功能说明：获取组内科研动态流

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "event_type": "task_submitted",
        "user": {"user_id": 10002, "nickname": "小王"},
        "summary": "小王提交了任务「复现 Deep RL 论文实验」",
        "target": {"type": "task", "task_id": 50001},
        "created_at": "2026-07-05T16:30:00Z"
      },
      {
        "event_type": "paper_shared",
        "user": {"user_id": 10003, "nickname": "小李"},
        "summary": "小李在共享池添加了 3 篇文献",
        "target": {"type": "papers", "paper_ids": ["p_100042", "p_100043", "p_100044"]},
        "created_at": "2026-07-05T15:00:00Z"
      }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v1/workspaces/{workspace_id}/quota`

功能说明：查看空间内成员算力配额分配

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "workspace_id": 100,
    "total_allocated": {
      "cpu_seconds_per_day": 36000,
      "gpu_seconds_per_day": 7200
    },
    "members": [
      {
        "user_id": 10002,
        "nickname": "小王",
        "cpu_quota": 14400,
        "gpu_quota": 3600,
        "used_today": {"cpu": 8400, "gpu": 1200}
      },
      {
        "user_id": 10003,
        "nickname": "小李",
        "cpu_quota": 7200,
        "gpu_quota": 1800,
        "used_today": {"cpu": 1200, "gpu": 0}
      }
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 模块7：防篡改日志 (M8)

### 功能概述
自动记录所有研学行为（检索、阅读、写作、实验），采用应用层哈希链校验确保日志不可删除/不可修改，提供管理员审计面板和日志完整性校验报告。

### 用户场景

**场景1：教务处调查学术不端举报**
教务处收到匿名举报，指控某研究生论文数据造假。管理员登录审计面板，输入该生学号和时间范围，系统展示其完整的研学行为日志链：文献检索记录、阅读时长、沙箱仿真运行日志、AI写作溯源标注。哈希链校验确认日志未被篡改，所有数据可追溯。

**场景2：导师查看课题组成员研究活跃度**
导师张教授在审计面板中查看课题组近30天的研学活跃度报告：每位成员的文献阅读量、检索次数、沙箱使用时长、写作字数统计。张教授发现两名学生近期活跃度骤降，主动约谈了解情况。

**场景3：校级管理员生成日志完整性校验报告**
学校信息化办公室每学期需要对各院系的科研诚信系统进行审计。管理员一键导出防篡改日志的完整性校验报告，报告包含哈希链连续性验证结果、异常日志告警、按用户/时间/行为类型的统计摘要。报告可作为教育部学科评估的支撑材料。

### 核心价值
- 不用此模块：学术不端检测依赖事后查重，无法追溯研究过程全貌
- 用了此模块：从"结果检测"升级为"过程可追溯"，全程哈希链保证不可篡改，为学术诚信提供技术底座
- 与竞品差异：不依赖外部区块链（成本高、响应慢），采用应用层哈希链实现同等防篡改效果，可私有化部署

### API端点清单

> **重要**：以下所有日志写入操作由系统后台自动触发，无需前端或用户手动调用。API端点仅用于审计查询。

#### `GET /api/v1/admin/activity-logs`

功能说明：管理员查询研学行为日志

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 否 | 按用户筛选 |
| action_type | string | 否 | 行为类型：search / read / write / sandbox / submit |
| date_from | string | 否 | 起始日期（ISO 8601） |
| date_to | string | 否 | 截止日期（ISO 8601） |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

请求示例：
```
GET /api/v1/admin/activity-logs?user_id=10002&date_from=2026-06-01&date_to=2026-07-01&page=1&page_size=20
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "log_id": 800001,
        "user_id": 10002,
        "action_type": "search",
        "action_detail": {
          "query": "reinforcement learning",
          "result_count": 156,
          "source": "keying"
        },
        "prev_hash": "0xabc123def456...",
        "current_hash": "0xbcd234efg567...",
        "ip_address": "192.168.1.100",
        "device_fingerprint": "fp_abc123def456",
        "created_at": "2026-06-15T10:30:00Z"
      }
    ],
    "total": 3542,
    "page": 1,
    "page_size": 20,
    "total_pages": 178
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1004` 权限不足（非管理员）

---

#### `GET /api/v1/admin/activity-logs/verify`

功能说明：生成日志完整性校验报告

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 否 | 按用户校验（不填则全局校验） |
| date_from | string | 否 | 起始日期 |
| date_to | string | 否 | 截止日期 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "report_id": "verify_20260702_001",
    "scope": {
      "user_id": null,
      "date_from": "2026-01-01",
      "date_to": "2026-07-02"
    },
    "summary": {
      "total_logs": 125000,
      "verified_logs": 125000,
      "broken_chains": 0,
      "anomalies": 0
    },
    "hash_chain_status": "HEALTHY",
    "verified_at": "2026-07-02T14:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v1/admin/activity-logs/statistics`

功能说明：获取行为统计摘要

请求头：`Authorization: Bearer {access_token}`（需要 admin 或以上权限）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workspace_id | integer | 否 | 按协作空间筛选 |
| date_from | string | 否 | 起始日期 |
| date_to | string | 否 | 截止日期 |
| group_by | string | 否 | 聚合维度：user / action_type / date，默认 date |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "period": {"from": "2026-06-01", "to": "2026-06-30"},
    "statistics": [
      {"date": "2026-06-01", "search_count": 120, "read_count": 85, "write_count": 12, "sandbox_count": 8},
      {"date": "2026-06-02", "search_count": 98, "read_count": 72, "write_count": 15, "sandbox_count": 6}
    ],
    "totals": {
      "search_count": 3542,
      "read_count": 2100,
      "write_count": 340,
      "sandbox_count": 156
    }
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 模块8：算法商城 (M9) - ✅ 已实现

### 功能概述
提供算法模板的浏览、执行与结果查询。支持 mock 种子数据（30 个算法，5 类别），当数据库为空时自动回退 mock 模式，确保 API 可用性。

### 当前实现状态

| 端点 | 状态 | 说明 |
|------|------|------|
| `GET /api/v9/algorithms` | ✅ | 分页浏览算法（DB 优先，空库时回退 mock 数据） |
| `GET /api/v9/algorithms/{id}` | ✅ | 算法详情（支持 mock-alg-xxx 格式 ID） |
| `POST /api/v9/algorithms/{id}/execute` | ✅ | 执行算法（mock 返回执行记录） |
| `GET /api/v9/executions` | ✅ | 分页查询执行历史 |
| `GET /api/v9/executions/{id}` | ✅ | 执行详情 |

**种子算法**：30 个 mock 算法，覆盖文本分析、图像处理、数据挖掘、统计建模、网络分析 5 类别。

### API端点清单

#### `POST /api/v9/algorithms`

功能说明：上传算法模板

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 算法名称 |
| description | string | 否 | 算法描述 |
| visibility | string | 是 | 权限：private / group / public_free / paid |
| price_cents | integer | 否 | 价格（分），仅 paid 时需要 |
| files | array[object] | 是 | 算法文件列表（代码+文档+环境配置） |
| tags | array[string] | 否 | 标签 |

请求示例：
```json
{
  "name": "图神经网络节点分类模板",
  "description": "基于PyG实现的GCN/GAT/GraphSAGE节点分类模板，含Cora数据集示例",
  "visibility": "group",
  "tags": ["GNN", "node classification", "PyG"]
}
```

响应格式：
```json
{
  "code": 0,
  "message": "算法模板上传成功",
  "data": {
    "algorithm_id": 90001,
    "version": "1.0.0",
    "created_at": "2026-07-02T11:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v9/algorithms`

功能说明：浏览算法商城

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| visibility | string | 否 | 筛选权限级别 |
| tag | string | 否 | 按标签筛选 |
| keyword | string | 否 | 关键词搜索 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "algorithm_id": 90001,
        "name": "图神经网络节点分类模板",
        "author": {"user_id": 10002, "nickname": "小王"},
        "visibility": "group",
        "tags": ["GNN", "PyG"],
        "downloads": 12,
        "rating": 4.5,
        "latest_version": "1.0.0"
      }
    ],
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v9/algorithms/{algorithm_id}`

功能说明：获取算法模板详情

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "algorithm_id": 90001,
    "name": "图神经网络节点分类模板",
    "description": "基于PyG实现的GCN/GAT/GraphSAGE...",
    "author": {"user_id": 10002, "nickname": "小王"},
    "visibility": "group",
    "price_cents": 0,
    "tags": ["GNN", "node classification", "PyG"],
    "versions": [
      {"version": "1.0.0", "changelog": "初始版本", "created_at": "2026-07-02"}
    ],
    "downloads": 12,
    "rating": 4.5,
    "reviews": [
      {"user": {"nickname": "小李"}, "rating": 5, "comment": "非常好用！", "created_at": "2026-07-02"}
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v9/algorithms/{algorithm_id}/purchase`

功能说明：购买付费算法

> ⚠️ 计划中，尚未实现 — 依赖支付网关对接

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "购买成功",
  "data": {
    "transaction_id": "txn_20260702_001",
    "algorithm_id": 90005,
    "price_cents": 9900,
    "purchased_at": "2026-07-02T14:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v9/algorithms/{algorithm_id}/versions`

功能说明：上传新版本

> ⚠️ 计划中，尚未实现

请求头：`Authorization: Bearer {access_token}`（仅作者可操作）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | 是 | 版本号（语义化版本） |
| changelog | string | 是 | 变更日志 |
| files | array[object] | 是 | 更新文件列表 |

请求示例：
```json
{
  "version": "1.1.0",
  "changelog": "新增GraphSAGE支持，优化GAT内存占用"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "新版本已发布",
  "data": {
    "algorithm_id": 90001,
    "version": "1.1.0",
    "created_at": "2026-07-05T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `GET /api/v9/algorithms/transactions`

功能说明：获取交易记录（卖家视角）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "transaction_id": "txn_20260702_001",
        "algorithm_id": 90005,
        "algorithm_name": "工业缺陷检测模板",
        "buyer": {"user_id": 10020, "nickname": "赵六"},
        "price_cents": 9900,
        "platform_fee_cents": 1980,
        "net_income_cents": 7920,
        "created_at": "2026-07-02T14:00:00Z"
      }
    ],
    "total": 23,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

#### `POST /api/v9/algorithms/{algorithm_id}/execute`

功能说明：在沙箱中执行算法模板

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parameters | object | 否 | 算法参数 |
| dataset_id | integer | 否 | 数据集ID |

响应格式：
```json
{
  "code": 0,
  "message": "算法已提交执行",
  "data": {
    "execution_id": 50001,
    "status": "queued"
  }
}
```

---

#### `GET /api/v9/executions/{execution_id}`

功能说明：查询算法执行状态

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution_id": 50001,
    "algorithm_id": 90001,
    "status": "running",
    "progress": 45,
    "started_at": "2026-07-03T10:00:00Z"
  }
}
```

---

#### `GET /api/v9/executions/{execution_id}/result`

功能说明：获取算法执行结果

请求头：`Authorization: Bearer {access_token}`

响应格式：包含 stdout、stderr、输出文件列表、运行时长和资源用量。

---

#### `GET /api/v9/algorithms/{algorithm_id}/reviews`

功能说明：获取算法评价列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

---

#### `POST /api/v9/algorithms/{algorithm_id}/reviews`

功能说明：提交算法评价

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rating | integer | 是 | 评分（1-5） |
| comment | string | 否 | 评价内容 |

---

---

## 模块9：核心服务增强 (M1-ext)

### 功能概述
为核心模块（检索、写作、沙箱、格式转换）提供统一的弹性防护层。包含失败降级引擎、SSE流式进度反馈和学术规范自查三大子模块，确保系统在高负载或外部依赖异常时仍能优雅降级而非硬崩溃。

### 用户场景

**场景1：检索源不可用时自动降级**
博士生小王的检索关键词命中科应API，但科应服务暂时不可用（503）。降级引擎检测到超时后自动切换为本地缓存文献检索，并提示用户"当前检索结果来自本地缓存，部分最新文献可能未收录"。整个过程用户无感知中断，检索仍然返回可用结果。

**场景2：实时查看AI写作进度**
用户触发文献综述生成后，前端通过 SSE 连接实时接收 6 阶段进度推送：searching → reading → analyzing → planning → writing → finalizing。每个阶段显示具体进度百分比和当前状态描述（如"正在阅读第 12/35 篇文献..."）。

**场景3：投前自查论文格式规范**
用户在投稿前使用学术规范自查功能，系统自动检查：格式（标题层级、图表编号、参考文献格式）、结构（IMRaD完整性）、引用完整性（是否存在孤立的文中引用而无对应参考文献条目）。生成自查报告并标注不合规项。

---

### 失败降级引擎（P0-C）

#### 功能概述
为 5 类核心场景提供预设的降级策略，当外部依赖或内部服务异常时自动切换备用路径，避免用户操作被硬阻断。

#### 降级场景矩阵

| 场景 | 触发条件 | 降级策略 | 用户提示 |
|------|---------|---------|---------|
| 搜索超时 | 科应API > 30s 无响应 | 切换本地缓存 + SQLite 全文检索 | "部分结果来自本地缓存" |
| 沙箱不可用 | Docker daemon 连接失败 | 提示用户稍后重试，保留代码草稿 | "沙箱服务暂时不可用" |
| LLM 配额耗尽 | API 余额不足或速率限制 | 切换备用模型（混元→DeepSeek 或反之） | "已切换至备用模型" |
| 写作服务过载 | 并发请求超阈值 | 进入排队队列，前端轮询状态 | "当前排队第 X 位" |
| 格式转换失败 | LibreOffice / Pandoc 异常 | 保留原始文件，提示手动转换 | "格式转换失败，请重试" |

#### 实现文件

- `app/services/degradation.py`：降级策略注册与执行引擎

#### API

降级引擎为内部中间件，不暴露独立 API。各服务通过 `degradation.registry` 注册降级回调，异常发生时自动触发。

---

### SSE 流式进度反馈（P0-B）

#### 功能概述
基于 `ProgressManager` 异步事件总线的 SSE (Server-Sent Events) 流式进度推送。将长耗时任务拆解为 6 个标准阶段，每个阶段携带进度百分比与状态描述，前端通过 EventSource 连接实时订阅。

#### 6 阶段定义

| 阶段 | 标识 | 说明 | 典型进度范围 |
|------|------|------|------------|
| 检索中 | `searching` | 多源文献检索与去重 | 0-15% |
| 阅读中 | `reading` | AI 阅读并分析选定文献 | 16-35% |
| 分析中 | `analyzing` | 主题聚类、方法脉络提取 | 36-50% |
| 规划中 | `planning` | 大纲生成与结构优化 | 51-65% |
| 写作中 | `writing` | 逐节生成正文+引用标注 | 66-90% |
| 完成中 | `finalizing` | 格式整理、溯源报告生成 | 91-100% |

#### SSE 事件格式

```
event: progress
data: {"stage": "writing", "progress": 72, "message": "正在生成第 3/5 节：研究挑战与未来方向..."}

event: complete
data: {"document_id": 40010, "ai_generated_ratio": 0.88}
```

#### 集成范围

ProgressManager 已集成到以下服务：
- M2 文献检索（searching → 结束）
- M5 AI写作辅助（searching → finalizing，完整 6 阶段）
- M6 Docker沙箱（running → 单阶段百分比）

#### API端点清单

##### `GET /api/v1/progress/{task_id}`

功能说明：查询任务进度

请求头：`Authorization: Bearer {access_token}`

响应为 SSE 流，事件格式同上。

##### `POST /api/v1/progress/tasks`

功能说明：创建带进度追踪的任务

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 任务类型：search / write / sandbox |
| params | object | 否 | 任务参数 |

---

### 学术规范自查（P0-K）

#### 功能概述
提供投稿前自动检查工具，覆盖格式、结构、引用完整性三大维度，生成规范自查报告。

#### API端点清单

##### `POST /api/v1/academic-check/format`

功能说明：格式规范检查

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |
| journal | string | 否 | 目标期刊（自动加载对应格式规范） |

请求示例：
```json
{
  "document_id": 40010,
  "journal": "计算机学报"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40010,
    "checks": [
      {"item": "标题层级", "status": "pass", "detail": "使用 1/1.1/1.1.1 三级结构，符合规范"},
      {"item": "图表编号", "status": "fail", "detail": "图 3 缺少编号，共发现 2 处缺失"},
      {"item": "参考文献格式", "status": "pass", "detail": "全部 35 条引用符合 GB/T 7714 格式"},
      {"item": "摘要字数", "status": "fail", "detail": "摘要 342 字，超出 300 字限制"}
    ],
    "pass_rate": "50%",
    "checked_at": "2026-07-03T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/academic-check/structure`

功能说明：结构完整性检查（IMRaD）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40010,
    "structure": {
      "introduction": "found",
      "methods": "found",
      "results": "found",
      "discussion": "missing",
      "conclusion": "found"
    },
    "suggestions": ["缺少独立的 Discussion 章节，建议从 Conclusion 中拆分"],
    "overall": "incomplete"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/academic-check/citations`

功能说明：引用完整性检查

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40010,
    "total_citations_in_text": 35,
    "total_references": 33,
    "orphan_citations": [
      {"marker": "[34]", "context": "...as shown in recent work [34]..."},
      {"marker": "[35]", "context": "...consistent with [35]..."}
    ],
    "unreferenced_entries": [],
    "overall": "issue_found"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 模块10：知识库增强 (M3-ext)

### 功能概述
在 M3 文献阅读+个人知识库基础上增加三层记忆系统、对话搜索管理和原子级溯源引擎，实现用户行为的长期记忆、对话的灵活组织和AI生成内容的精确溯源。

---

### 三层记忆系统（P0-G）

#### 功能概述
自动记录用户行为与偏好，构建 UserProfile（长期偏好）、TopicMemory（课题级知识沉淀）、SessionContext（会话上下文）三层记忆体系。每日凌晨 3:00 自动归档短期记忆到长期存储。

#### 三层架构

| 层级 | 名称 | 生命周期 | 内容示例 |
|------|------|---------|---------|
| L1 | UserProfile | 永久 | 研究方向偏好、常用期刊、写作风格习惯 |
| L2 | TopicMemory | 课题周期 | 课题进展、关键文献清单、实验参数记录 |
| L3 | SessionContext | 会话期间 | 当前搜索词、阅读中的文献、草稿状态 |

#### MemoryEngine 自动写入 Hook

MemoryEngine 通过 Hook 机制在以下模块自动写入记忆：
- **M2 文献检索**：记录搜索偏好 → UserProfile
- **M3 知识库**：记录阅读偏好和批注模式 → TopicMemory
- **M5 AI写作**：记录写作风格和结构偏好 → UserProfile
- **M6 沙箱**：记录常用实验参数 → TopicMemory

#### API端点清单

##### `GET /api/v1/memory/profile`

功能说明：获取用户长期偏好（UserProfile）

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "research_interests": ["联邦学习", "差分隐私", "分布式优化"],
    "preferred_journals": ["IEEE TIFS", "NeurIPS", "CCS"],
    "writing_style": {"language": "zh", "verbosity": "concise", "citation_format": "numeric"},
    "last_updated": "2026-07-03T03:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v1/memory/topics`

##### `POST /api/v1/memory/topics`

##### `GET /api/v1/memory/topics/{topic_id}`

##### `PUT /api/v1/memory/topics/{topic_id}`

##### `DELETE /api/v1/memory/topics/{topic_id}`

功能说明：课题记忆管理（TopicMemory）

支持 CRUD 操作，topic 数据模型包含：
- `topic_id`：课题唯一标识
- `title`：课题名称
- `keywords`：关键词列表
- `papers`：关联文献清单
- `notes`：课题笔记
- `experiments`：实验参数快照
- `created_at` / `updated_at`

---

##### `GET /api/v1/memory/session`

功能说明：获取当前会话上下文

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_abc123",
    "active_searches": ["differential privacy federated learning"],
    "reading_papers": [{"paper_id": "p_100001", "title": "Deep RL for Robotics"}],
    "draft_document": {"document_id": 40010, "status": "writing"},
    "started_at": "2026-07-03T09:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/memory/archive`

功能说明：手动触发记忆归档（通常由凌晨定时任务自动执行）

请求头：`Authorization: Bearer {access_token}`（需要 admin 权限）

响应格式：
```json
{
  "code": 0,
  "message": "归档完成",
  "data": {
    "sessions_archived": 12,
    "topics_updated": 3,
    "profile_updated": true,
    "archived_at": "2026-07-03T03:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### 对话搜索管理（P0-E）

#### 功能概述
提供对话级别的管理能力：重命名、置顶、软删除、回收站恢复、永久删除、标题搜索和全局全文搜索。

#### API端点清单

##### `PUT /api/v1/conversations/{conversation_id}/rename`

功能说明：重命名对话

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 新标题 |

---

##### `POST /api/v1/conversations/{conversation_id}/pin`

##### `POST /api/v1/conversations/{conversation_id}/unpin`

功能说明：置顶/取消置顶对话

请求头：`Authorization: Bearer {access_token}`

---

##### `DELETE /api/v1/conversations/{conversation_id}`

功能说明：软删除对话（移入回收站）

请求头：`Authorization: Bearer {access_token}`

---

##### `GET /api/v1/conversations/trash`

功能说明：查看回收站

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

---

##### `POST /api/v1/conversations/{conversation_id}/restore`

功能说明：从回收站恢复对话

请求头：`Authorization: Bearer {access_token}`

---

##### `DELETE /api/v1/conversations/{conversation_id}/permanent`

功能说明：永久删除对话（不可恢复）

请求头：`Authorization: Bearer {access_token}`

---

##### `GET /api/v1/conversations/search`

功能说明：对话搜索（标题+全文）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| scope | string | 否 | 搜索范围：title / full_text，默认 full_text |

---

### 原子级溯源引擎（P0-D）

#### 功能概述
将 AI 写作溯源从段落级别升级为句子级。每条 AI 生成/辅助的句子携带精确的来源标注，包含溯源类型和置信度。

#### 溯源类型

| 类型 | 标识 | 含义 |
|------|------|------|
| `direct_citation` | 直接引用 | 句子内容直接来源于某篇文献的原文 |
| `method_from` | 方法来源 | 句子描述的方法/技术来自特定文献 |
| `conclusion_from` | 结论来源 | 句子中的结论/发现来自特定文献 |
| `ai_synthesis` | AI 综合 | AI 综合多篇文献后生成的新表述 |
| `ai_original` | AI 原创 | AI 基于知识但不源于特定文献的原创内容 |

#### 置信度

| 级别 | 说明 |
|------|------|
| `high` | 原文高度匹配，可直接验证 |
| `medium` | 语义匹配，经改写后保留原意 |
| `low` | 弱关联，仅供参考 |

#### 溯源报告结构

```json
{
  "document_id": 40010,
  "trace_version": "2.0",
  "segments": [
    {
      "sentence": "差分隐私通过添加校准噪声来保护个体数据不被推断攻击。",
      "trace_type": "direct_citation",
      "sources": [
        {"paper_id": "p_100042", "title": "Calibrating Noise to Sensitivity...", "section": "3.1", "confidence": "high"}
      ]
    },
    {
      "sentence": "近期研究表明，自适应隐私预算分配能显著提升联邦学习中的效用-隐私权衡。",
      "trace_type": "ai_synthesis",
      "sources": [
        {"paper_id": "p_100055", "title": "Adaptive DP in FL", "section": "5.2", "confidence": "medium"},
        {"paper_id": "p_100056", "title": "Utility-Privacy Tradeoff...", "section": "4.3", "confidence": "medium"}
      ]
    }
  ],
  "statistics": {
    "total_sentences": 156,
    "direct_citation": 34,
    "method_from": 18,
    "conclusion_from": 22,
    "ai_synthesis": 45,
    "ai_original": 37
  }
}
```

#### API

溯源引擎复用 M5 已有端点 `GET /api/v5/writing/documents/{document_id}/trace`，返回格式升级为上述 v2.0 结构（句子级定型）。

---

## 模块11：安全与分享

### 功能概述
提供学术文档的加密保护与受控分享能力。`.scix` 格式实现端到端加密打包，分享模式支持链接+水印+权限控制的学术交流场景（如同行评审、合作投稿）。

---

### .scix 加密格式（P0-I）

#### 功能概述
AES-256-GCM 对称加密 + PBKDF2 密钥派生 + Ed25519 非对称签名的三层安全容器。将文档正文、附件、元数据打包为 `.scix`（ZIP容器）加密文件，确保传输和存储安全。

#### scix 文件结构

```
document.scix (ZIP 容器)
├── manifest.json        # 未加密的元信息（文档ID、创建时间、加密算法标识）
├── content.enc          # AES-256-GCM 加密的正文内容
├── assets/
│   ├── figure_1.png.enc # 加密的附件
│   └── data.csv.enc
└── signature.sig        # Ed25519 签名（对 content.enc + assets/* 的签名）
```

#### 加密流程

```
原始文档 → 正文(PBKDF2→AES-256-GCM加密) → content.enc
         → 附件(各自独立加密) → assets/*.enc
         → 签名(Ed25519) → signature.sig
         → ZIP打包 → .scix
```

#### API端点清单

##### `POST /api/v1/scix/encrypt`

功能说明：将文档加密打包为 .scix 格式

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |
| passphrase | string | 是 | 加密密码（PBKDF2 派生密钥） |
| include_assets | boolean | 否 | 是否包含附件，默认 true |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scix_file_url": "https://cdn.sciagent.cn/exports/document_40010.scix",
    "file_size_bytes": 2457600,
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "created_at": "2026-07-03T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `POST /api/v1/scix/decrypt`

功能说明：解密 .scix 文件

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scix_file_path | string | 是 | .scix 文件路径 |
| passphrase | string | 是 | 解密密码 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 40010,
    "content": "## 引言\n\n...",
    "assets": ["figure_1.png", "data.csv"],
    "verified": true
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`1001` 密码错误或文件损坏、`2001` .scix 文件不存在

---

##### `POST /api/v1/scix/keypair`

功能说明：生成 Ed25519 密钥对（用于签名/验证）

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "public_key": "MCowBQYDK2VwAyEA...",
    "created_at": "2026-07-03T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

> 私钥仅在生成时返回一次，不存储于服务端。

---

##### `POST /api/v1/scix/verify`

功能说明：验证 .scix 文件签名完整性

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scix_file_path | string | 是 | .scix 文件路径 |
| public_key | string | 是 | 签名者公钥 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": true,
    "signer": "MCowBQYDK2VwAyEA...",
    "verified_at": "2026-07-03T10:05:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### 分享模式（P0-I）

#### 功能概述
受控分享链接生成与管理。支持设置过期时间、访问次数上限、下载/打印权限、自动水印嵌入。

#### API端点清单

##### `POST /api/v1/share/create`

功能说明：创建分享链接

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档ID |
| expires_at | string | 否 | 过期时间（ISO 8601），不填则永不过期 |
| max_access_count | integer | 否 | 最大访问次数，不填则不限 |
| allow_download | boolean | 否 | 是否允许下载，默认 false |
| allow_print | boolean | 否 | 是否允许打印，默认 false |
| watermark_text | string | 否 | 水印文字（如"仅供同行评审使用"） |

请求示例：
```json
{
  "document_id": 40010,
  "expires_at": "2026-08-03T23:59:59Z",
  "max_access_count": 10,
  "allow_download": false,
  "allow_print": true,
  "watermark_text": "仅供《计算机学报》同行评审使用"
}
```

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "share_token": "share_abc123def456",
    "share_url": "https://sciagent.cn/share/share_abc123def456",
    "expires_at": "2026-08-03T23:59:59Z",
    "max_access_count": 10,
    "access_count": 0
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v1/share/{token}`

功能说明：通过分享链接访问文档（无需登录，Token 鉴权）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是（路径参数） | 分享令牌 |

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_title": "联邦学习中的差分隐私保护方法综述",
    "content": "## 引言\n\n...",
    "watermark": "仅供《计算机学报》同行评审使用",
    "permissions": {
      "allow_download": false,
      "allow_print": true
    },
    "access_count": 3,
    "remaining_access": 7
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

错误码：`2001` 分享链接不存在或已过期、`1004` 访问次数已用完

---

##### `GET /api/v1/share/list`

功能说明：查看我创建的分享列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

---

##### `DELETE /api/v1/share/{token}`

功能说明：撤销分享链接

请求头：`Authorization: Bearer {access_token}`

---

#### 数据模型：share_links

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| token | VARCHAR(128) | UNIQUE, NOT NULL | 分享令牌 |
| document_id | BIGINT | FK → documents.id, NOT NULL | 文档ID |
| creator_id | BIGINT | FK → users.id, NOT NULL | 创建者ID |
| expires_at | TIMESTAMPTZ | NULLABLE | 过期时间 |
| max_access_count | INTEGER | NULLABLE | 最大访问次数 |
| access_count | INTEGER | DEFAULT 0 | 已访问次数 |
| allow_download | BOOLEAN | DEFAULT FALSE | 是否允许下载 |
| allow_print | BOOLEAN | DEFAULT FALSE | 是否允许打印 |
| watermark_text | VARCHAR(255) | NULLABLE | 水印文字 |
| is_revoked | BOOLEAN | DEFAULT FALSE | 是否已撤销 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

---

## 模块12：预编排工作流

### 功能概述
提供 5 种科研全流程预编排工作流，基于 DAG (有向无环图) 编排自动推进。每个工作流包含一系列预定义步骤，上一步完成后自动触发下一步，用户可在任意节点介入调整。

### 5 种工作流

| 工作流 | 标识 | 步骤数 | 适用场景 |
|--------|------|--------|---------|
| 博士开题 | `phd_proposal` | 6 步 | 选题调研 → 文献综述 → 研究方案 → 开题报告 |
| 文献综述 | `lit_review` | 5 步 | 主题确定 → 文献检索 → 分类整理 → 综述撰写 |
| 论文复现 | `reproduction` | 4 步 | 论文分析 → 环境搭建 → 代码复现 → 结果验证 |
| 投稿准备 | `submission` | 4 步 | 格式检查 → 图表优化 → 规范自查 → 打包导出 |
| 答辩准备 | `defense` | 3 步 | 成果汇总 → PPT生成 → 演讲备注 |

### 工作流 DAG 示例：phd_proposal

```
[选题调研] → [文献检索] → [文献分类] → [综述生成]
                                      ↘
                                    [研究方案设计] → [开题报告生成]
```

### 工作流引擎

实现文件：`app/services/workflow_engine.py`

核心机制：
- DAG 依赖解析：自动识别步骤间的前置依赖
- 状态持久化：每步状态（pending/running/completed/failed）写入 `workflow_instances` 表
- 断点续传：工作流中断后可从最后完成步骤恢复
- 人机协作：关键决策节点（如大纲确认）暂停等待用户输入

### API端点清单

##### `GET /api/v1/workflow/list`

功能说明：获取可用工作流列表

请求头：`Authorization: Bearer {access_token}`

响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "workflows": [
      {"type": "phd_proposal", "name": "博士开题", "steps": 6, "estimated_hours": 8},
      {"type": "lit_review", "name": "文献综述", "steps": 5, "estimated_hours": 4},
      {"type": "reproduction", "name": "论文复现", "steps": 4, "estimated_hours": 6},
      {"type": "submission", "name": "投稿准备", "steps": 4, "estimated_hours": 2},
      {"type": "defense", "name": "答辩准备", "steps": 3, "estimated_hours": 3}
    ]
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v1/workflow/{type}`

功能说明：获取指定工作流详情（含步骤定义和 DAG）

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是（路径参数） | 工作流标识 |

---

##### `POST /api/v1/workflow/{type}/start`

功能说明：启动工作流实例

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是（路径参数） | 工作流标识 |
| params | object | 否 | 工作流参数（如 topic/library_ids 等） |

请求示例：
```json
{
  "params": {
    "topic": "联邦学习中的差分隐私保护方法",
    "library_ids": [20001, 20002]
  }
}
```

响应格式：
```json
{
  "code": 0,
  "message": "工作流已启动",
  "data": {
    "instance_id": "wf_abc123",
    "workflow_type": "lit_review",
    "status": "running",
    "current_step": 1,
    "steps": [
      {"step": 1, "name": "主题确定", "status": "running"},
      {"step": 2, "name": "文献检索", "status": "pending"},
      {"step": 3, "name": "分类整理", "status": "pending"},
      {"step": 4, "name": "综述撰写", "status": "pending"},
      {"step": 5, "name": "格式导出", "status": "pending"}
    ],
    "started_at": "2026-07-03T10:00:00Z"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

##### `GET /api/v1/workflow/instances`

功能说明：获取我的工作流实例列表

请求头：`Authorization: Bearer {access_token}`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 筛选：running / completed / failed / paused |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |

---

##### `GET /api/v1/workflow/instances/{instance_id}`

功能说明：获取工作流实例详情（含进度）

请求头：`Authorization: Bearer {access_token}`

---

##### `POST /api/v1/workflow/instances/{instance_id}/pause`

##### `POST /api/v1/workflow/instances/{instance_id}/resume`

##### `POST /api/v1/workflow/instances/{instance_id}/cancel`

功能说明：暂停/恢复/取消工作流实例

请求头：`Authorization: Bearer {access_token}`

---

#### 数据模型：workflow_instances

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| instance_id | VARCHAR(64) | UNIQUE, NOT NULL | 实例唯一标识 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| workflow_type | VARCHAR(50) | NOT NULL | phd_proposal / lit_review / reproduction / submission / defense |
| status | VARCHAR(20) | DEFAULT 'running' | running / paused / completed / failed / cancelled |
| current_step | INTEGER | DEFAULT 1 | 当前执行步骤序号 |
| steps_json | JSONB | NOT NULL | 步骤定义与状态列表 |
| params | JSONB | DEFAULT '{}' | 工作流启动参数 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

---

# 第3章：数据模型

## 3.1 用户表 (users)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键（实现层面采用UUID以获得更好的分布式唯一性和安全性，SPEC 原文记录为 BIGSERIAL） |
| email | VARCHAR(255) | UNIQUE, NULLABLE | 邮箱 |
| phone | VARCHAR(20) | UNIQUE, NULLABLE | 手机号（加密存储） |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| wechat_union_id | VARCHAR(128) | UNIQUE, NULLABLE | 微信 UnionID |
| nickname | VARCHAR(100) | NOT NULL | 昵称 |
| avatar_url | TEXT | NULLABLE | 头像URL |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | 角色：user / admin / super_admin |
| institution | VARCHAR(255) | NULLABLE | 所属机构 |
| department | VARCHAR(255) | NULLABLE | 院系/部门 |
| email_verified | BOOLEAN | DEFAULT FALSE | 邮箱是否验证 |
| phone_verified | BOOLEAN | DEFAULT FALSE | 手机是否验证 |
| is_active | BOOLEAN | DEFAULT TRUE | 账号是否启用 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

## 3.2 文献表 (papers)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| paper_uid | VARCHAR(64) | UNIQUE, NOT NULL | 文献唯一标识（如 `p_100001`） |
| title | TEXT | NOT NULL | 标题 |
| authors | JSONB | NOT NULL, DEFAULT '[]' | 作者列表 |
| abstract | TEXT | NULLABLE | 摘要 |
| doi | VARCHAR(255) | UNIQUE, NULLABLE | DOI |
| journal | VARCHAR(500) | NULLABLE | 期刊名称 |
| year | INTEGER | NULLABLE | 出版年份 |
| volume | VARCHAR(50) | NULLABLE | 卷号 |
| issue | VARCHAR(50) | NULLABLE | 期号 |
| pages | VARCHAR(100) | NULLABLE | 页码 |
| citation_count | INTEGER | DEFAULT 0 | 引用数 |
| oa_status | VARCHAR(20) | NULLABLE | OA状态：gold / green / hybrid / closed |
| source | VARCHAR(50) | NOT NULL | 数据来源：keying 等 |
| subjects | JSONB | DEFAULT '[]' | 学科分类列表 |
| keywords | JSONB | DEFAULT '[]' | 关键词列表 |
| references | JSONB | DEFAULT '[]' | 参考文献列表 |
| raw_metadata | JSONB | DEFAULT '{}' | 原始元数据（完整保留数据源返回） |
| embedding | vector(1536) | NULLABLE | 摘要向量（pgvector，用于语义搜索；当前使用 JSON 实现，后续迭代考虑 pgvector 迁移） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 入库时间 |

## 3.3 用户知识库 (user_library)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| paper_id | BIGINT | FK → papers.id, NOT NULL | 文献ID |
| folder | VARCHAR(500) | NULLABLE | 文件夹路径，如 `联邦学习/差分隐私` |
| tags | JSONB | DEFAULT '[]' | 标签列表 |
| is_favorited | BOOLEAN | DEFAULT FALSE | 是否收藏 |
| read_status | VARCHAR(20) | DEFAULT 'unread' | unread / reading / finished |
| notes | TEXT | NULLABLE | 个人笔记（纯文本摘要） |
| added_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 添加时间 |
| last_read_at | TIMESTAMPTZ | NULLABLE | 最后阅读时间 |

唯一约束：(user_id, paper_id)

## 3.4 文献批注 (annotations)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| library_id | BIGINT | FK → user_library.id, NOT NULL | 知识库条目ID |
| highlighted_text | TEXT | NULLABLE | 高亮文本片段 |
| note | TEXT | NULLABLE | 笔记内容 |
| position_data | JSONB | NULLABLE | 位置信息 {page, paragraph, start_offset, end_offset} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.5 写作文档 (documents)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| title | VARCHAR(500) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | Markdown 正文 |
| ai_generated_ratio | FLOAT | DEFAULT 0 | AI生成内容占比 (0.0~1.0) |
| source_papers | JSONB | DEFAULT '[]' | 来源文献：[{paper_id, sections: [...]}] |
| status | VARCHAR(20) | DEFAULT 'draft' | draft / writing / finished |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

## 3.6 沙箱作业 (sandbox_jobs)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 内部自增 ID |
| job_uid | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | 任务唯一标识（对外暴露） |
| user_id | VARCHAR | NOT NULL, INDEX | FK → users.id |
| language | VARCHAR(20) | NOT NULL | python / r |
| code | TEXT | NOT NULL | 代码内容 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'queued' | queued/pulling/running/completed/failed/timeout/killed |
| container_id | VARCHAR(128) | NULLABLE | Docker 容器 ID |
| image | VARCHAR(255) | NOT NULL | 使用的镜像名 |
| cpu_seconds_used | FLOAT | DEFAULT 0 | CPU 实际用量（秒） |
| memory_peak_mb | FLOAT | DEFAULT 0 | 内存峰值（MB） |
| stdout | TEXT | NULLABLE | 标准输出 |
| stderr | TEXT | NULLABLE | 标准错误 |
| exit_code | INTEGER | NULLABLE | 进程退出码 |
| error_message | TEXT | NULLABLE | 错误信息 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| started_at | TIMESTAMPTZ | NULLABLE | 开始执行时间 |
| finished_at | TIMESTAMPTZ | NULLABLE | 结束时间 |

## 3.7 协作空间 (workspaces)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| name | VARCHAR(255) | NOT NULL | 空间名称 |
| level | VARCHAR(20) | NOT NULL | school / college / lab / class / friends |
| parent_id | BIGINT | FK → workspaces.id, NULLABLE | 父空间ID |
| owner_id | BIGINT | FK → users.id, NOT NULL | 创建者ID |
| description | TEXT | NULLABLE | 空间描述 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.8 协作空间成员 (workspace_members)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| workspace_id | BIGINT | FK → workspaces.id, NOT NULL | 空间ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| role | VARCHAR(20) | NOT NULL | super_admin / admin / leader / member / viewer |
| joined_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 加入时间 |

唯一约束：(workspace_id, user_id)

## 3.9 协作空间共享文献 (workspace_shared_papers)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| workspace_id | BIGINT | FK → workspaces.id, NOT NULL | 空间ID |
| library_id | BIGINT | FK → user_library.id, NOT NULL | 知识库条目ID |
| shared_by | BIGINT | FK → users.id, NOT NULL | 分享者ID |
| shared_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 分享时间 |

唯一约束：(workspace_id, library_id)

## 3.10 协作空间任务 (workspace_tasks)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| workspace_id | BIGINT | FK → workspaces.id, NOT NULL | 空间ID |
| title | VARCHAR(500) | NOT NULL | 任务标题 |
| description | TEXT | NULLABLE | 任务描述 |
| creator_id | BIGINT | FK → users.id, NOT NULL | 下发者ID（导师） |
| assignee_ids | JSONB | NOT NULL, DEFAULT '[]' | 指派学生ID列表 |
| status | VARCHAR(20) | DEFAULT 'pending' | pending / in_progress / submitted / reviewed |
| priority | VARCHAR(10) | DEFAULT 'medium' | low / medium / high |
| due_date | TIMESTAMPTZ | NULLABLE | 截止日期 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.11 任务提交 (task_submissions)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| task_id | BIGINT | FK → workspace_tasks.id, NOT NULL | 任务ID |
| submitter_id | BIGINT | FK → users.id, NOT NULL | 提交者ID |
| content | TEXT | NULLABLE | 提交说明 |
| attachments | JSONB | DEFAULT '[]' | 附件列表 |
| submitted_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 提交时间 |

## 3.12 研学日志 (activity_logs)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| action_type | VARCHAR(50) | NOT NULL | search / read / write / sandbox / submit / ... |
| action_detail | JSONB | NOT NULL, DEFAULT '{}' | 行为详情 |
| prev_hash | VARCHAR(128) | NOT NULL | 前一条日志的哈希值 |
| current_hash | VARCHAR(128) | NOT NULL | 当前日志的哈希值（SHA-256） |
| ip_address | VARCHAR(45) | NULLABLE | 客户端IP |
| device_fingerprint | VARCHAR(255) | NULLABLE | 设备指纹 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 记录时间 |

索引：(user_id, action_type, created_at)

### 哈希链计算规则

```
current_hash = SHA-256(prev_hash + user_id + action_type + action_detail_json + created_at + salt)
```

每条日志的 `current_hash` 成为下一条日志的 `prev_hash`。系统启动时根哈希由部署脚本注入。

## 3.13 检索历史 (search_history)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| query | TEXT | NOT NULL | 检索关键词 |
| filters | JSONB | DEFAULT '{}' | 筛选条件 |
| result_count | INTEGER | DEFAULT 0 | 结果数量 |
| saved_as | VARCHAR(255) | NULLABLE | 自定义保存名称 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 检索时间 |

## 3.14 算法模板 (algorithms) — 预留

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| author_id | BIGINT | FK → users.id, NOT NULL | 作者ID |
| name | VARCHAR(255) | NOT NULL | 算法名称 |
| description | TEXT | NULLABLE | 算法描述 |
| visibility | VARCHAR(20) | NOT NULL | private / group / public_free / paid |
| price_cents | INTEGER | DEFAULT 0 | 价格（分） |
| tags | JSONB | DEFAULT '[]' | 标签 |
| download_count | INTEGER | DEFAULT 0 | 下载次数 |
| avg_rating | FLOAT | DEFAULT 0 | 平均评分 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.15 算法版本 (algorithm_versions) — 预留

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| algorithm_id | BIGINT | FK → algorithms.id, NOT NULL | 算法ID |
| version | VARCHAR(50) | NOT NULL | 版本号 |
| changelog | TEXT | NULLABLE | 变更日志 |
| files_metadata | JSONB | DEFAULT '{}' | 文件元信息 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 发布时间 |

## 3.16 算法交易 (algorithm_transactions) — 预留

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| algorithm_id | BIGINT | FK → algorithms.id, NOT NULL | 算法ID |
| buyer_id | BIGINT | FK → users.id, NOT NULL | 购买者ID |
| price_cents | INTEGER | NOT NULL | 交易价格 |
| platform_fee_cents | INTEGER | NOT NULL | 平台抽成 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 交易时间 |

## 3.17 写作大纲 (writing_plans)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| plan_id | VARCHAR(64) | UNIQUE, NOT NULL | 大纲唯一标识 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| topic | VARCHAR(500) | NOT NULL | 写作主题 |
| sections | JSONB | NOT NULL | 节列表，每项含 sid/title/summary/status/content/confirmed |
| status | VARCHAR(20) | DEFAULT 'outline_generated' | outline_generated / generating / finalized |
| language | VARCHAR(5) | DEFAULT 'zh' | 输出语言 |
| document_id | BIGINT | FK → documents.id, NULLABLE | 关联的最终文档ID |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

## 3.18 用户偏好记忆 (user_profiles)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL, UNIQUE | 用户ID |
| research_interests | JSONB | DEFAULT '[]' | 研究方向偏好列表 |
| preferred_journals | JSONB | DEFAULT '[]' | 常用期刊列表 |
| writing_style | JSONB | DEFAULT '{}' | 写作风格偏好（language/verbosity/citation_format） |
| embedding | vector(1536) | NULLABLE | 偏好向量（用于推荐） |
| last_updated | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 最后更新时间 |

## 3.19 课题记忆 (topic_memories)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| topic_id | VARCHAR(64) | UNIQUE, NOT NULL | 课题唯一标识 |
| title | VARCHAR(500) | NOT NULL | 课题名称 |
| keywords | JSONB | DEFAULT '[]' | 关键词列表 |
| papers | JSONB | DEFAULT '[]' | 关联文献清单 |
| notes | TEXT | NULLABLE | 课题笔记 |
| experiments | JSONB | DEFAULT '[]' | 实验参数快照 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

索引：(user_id, created_at DESC)

## 3.20 会话上下文 (session_contexts)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| session_id | VARCHAR(64) | UNIQUE, NOT NULL | 会话唯一标识 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| active_searches | JSONB | DEFAULT '[]' | 当前会话的检索记录 |
| reading_papers | JSONB | DEFAULT '[]' | 当前阅读中的文献 |
| draft_document | JSONB | NULLABLE | 当前草稿文档引用 |
| expires_at | TIMESTAMPTZ | NOT NULL | 过期时间（会话结束后自动清理） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.21 分享链接 (share_links)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| token | VARCHAR(128) | UNIQUE, NOT NULL | 分享令牌 |
| document_id | BIGINT | FK → documents.id, NOT NULL | 文档ID |
| creator_id | BIGINT | FK → users.id, NOT NULL | 创建者ID |
| expires_at | TIMESTAMPTZ | NULLABLE | 过期时间 |
| max_access_count | INTEGER | NULLABLE | 最大访问次数 |
| access_count | INTEGER | DEFAULT 0 | 已访问次数 |
| allow_download | BOOLEAN | DEFAULT FALSE | 是否允许下载 |
| allow_print | BOOLEAN | DEFAULT FALSE | 是否允许打印 |
| watermark_text | VARCHAR(255) | NULLABLE | 水印文字 |
| is_revoked | BOOLEAN | DEFAULT FALSE | 是否已撤销 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

## 3.22 工作流实例 (workflow_instances)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| instance_id | VARCHAR(64) | UNIQUE, NOT NULL | 实例唯一标识 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| workflow_type | VARCHAR(50) | NOT NULL | phd_proposal / lit_review / reproduction / submission / defense |
| status | VARCHAR(20) | DEFAULT 'running' | running / paused / completed / failed / cancelled |
| current_step | INTEGER | DEFAULT 1 | 当前执行步骤序号 |
| steps_json | JSONB | NOT NULL | 步骤定义与状态列表 |
| params | JSONB | DEFAULT '{}' | 工作流启动参数 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

---

## 3.23 活动日志 (activity_logs)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| target_type | VARCHAR(50) | | 目标类型 |
| target_id | BIGINT | | 目标ID |
| detail | JSONB | DEFAULT '{}' | 操作详情 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(user_id, created_at DESC)`

---

## 3.24 算法评价 (algorithm_reviews)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| algorithm_id | BIGINT | FK → algorithms.id, NOT NULL | 算法ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 评价用户ID |
| rating | INTEGER | NOT NULL | 评分（1-5） |
| comment | TEXT | | 评价内容 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(algorithm_id, created_at DESC)`

外键：`algorithm_id → algorithms.id CASCADE`、`user_id → users.id CASCADE`

---

## 3.25 算法执行记录 (algorithm_executions)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| algorithm_id | BIGINT | FK → algorithms.id, NOT NULL | 算法ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| status | VARCHAR(20) | DEFAULT 'queued' | queued / running / success / failed |
| parameters | JSONB | DEFAULT '{}' | 执行参数 |
| result | JSONB | | 执行结果 |
| started_at | TIMESTAMPTZ | | 开始时间 |
| finished_at | TIMESTAMPTZ | | 结束时间 |

索引：`(user_id, created_at DESC)`、`(algorithm_id)`

外键：`algorithm_id → algorithms.id CASCADE`、`user_id → users.id CASCADE`

---

## 3.26 知识库批注 (annotations)

> 注：`annotation.py` 中未显式定义 `__tablename__`，表名由 SQLAlchemy 按命名规范推断为 `annotations`，与 3.4 为同一张表，此处不再重复定义。

---

## 3.27 订阅记录 (subscriptions)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, UNIQUE, NOT NULL | 用户ID |
| plan | VARCHAR(20) | NOT NULL | 订阅计划：free / pro / team |
| status | VARCHAR(20) | DEFAULT 'active' | active / cancelled / expired |
| current_period_start | TIMESTAMPTZ | NOT NULL | 当前周期开始 |
| current_period_end | TIMESTAMPTZ | NOT NULL | 当前周期结束 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(user_id)`

外键：`user_id → users.id CASCADE`

---

## 3.28 支付记录 (payments)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| amount_cents | INTEGER | NOT NULL | 金额（分） |
| currency | VARCHAR(3) | DEFAULT 'CNY' | 币种 |
| status | VARCHAR(20) | DEFAULT 'pending' | pending / success / failed |
| gateway | VARCHAR(20) | | 支付网关：stripe / wechat / alipay |
| gateway_transaction_id | VARCHAR(128) | | 网关交易ID |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(user_id, created_at DESC)`

外键：`user_id → users.id CASCADE`

---

## 3.29 发票记录 (invoices)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| payment_id | BIGINT | FK → payments.id, NOT NULL | 关联支付ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| invoice_number | VARCHAR(64) | UNIQUE | 发票编号 |
| status | VARCHAR(20) | DEFAULT 'draft' | draft / issued / cancelled |
| issued_at | TIMESTAMPTZ | | 开票时间 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(user_id)`

外键：`payment_id → payments.id CASCADE`、`user_id → users.id CASCADE`

---

## 3.30 优惠券 (coupons)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| code | VARCHAR(32) | UNIQUE, NOT NULL | 优惠码 |
| discount_type | VARCHAR(10) | NOT NULL | percent / fixed |
| discount_value | INTEGER | NOT NULL | 折扣值（百分比或分） |
| valid_from | TIMESTAMPTZ | NOT NULL | 生效时间 |
| valid_to | TIMESTAMPTZ | NOT NULL | 失效时间 |
| max_uses | INTEGER | DEFAULT 1 | 最大使用次数 |
| used_count | INTEGER | DEFAULT 0 | 已使用次数 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(code)`

---

## 3.31 防篡改活动日志 (activity_logs_m8)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| user_id | BIGINT | FK → users.id | 用户ID |
| action | VARCHAR(100) | NOT NULL | 操作类型 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_id | BIGINT | | 资源ID |
| ip_address | INET | | 操作IP |
| user_agent | TEXT | | User-Agent |
| checksum | VARCHAR(64) | NOT NULL | 本条记录校验和 |
| previous_checksum | VARCHAR(64) | | 上一条记录校验和 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

索引：`(user_id, created_at DESC)`、`(created_at DESC)`

外键：`user_id → users.id SET NULL`

---

## 3.32 完整性检查记录 (integrity_checks_m8)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| last_valid_id | BIGINT | | 最后一条有效日志ID |
| broken_at_id | BIGINT | | 第一条断裂日志ID |
| checked_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 检查时间 |
| status | VARCHAR(20) | NOT NULL | pass / fail |
| repaired | BOOLEAN | DEFAULT FALSE | 是否已修复 |

索引：`(checked_at DESC)`

---

## 3.33 Token黑名单 (token_blacklist)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 主键 |
| jti | VARCHAR(64) | UNIQUE, NOT NULL | JWT ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 用户ID |
| expires_at | TIMESTAMPTZ | NOT NULL | Token过期时间 |
| blacklisted_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 拉黑时间 |

索引：`(jti)`、`(user_id)`、`(expires_at)`

外键：`user_id → users.id CASCADE`

---

# 第4章：通用规范

## 4.1 统一API响应格式

所有API响应均采用以下JSON结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | integer | 业务状态码，0 表示成功 |
| message | string | 人类可读的状态信息 |
| data | object / array / null | 响应数据体，无数据时返回 null |
| request_id | string | 唯一请求追踪ID（UUID v4），用于日志关联和问题排查 |

## 4.2 统一错误码体系

| 错误码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 请求正常处理 |
| 1001 | 参数校验失败 | 请求参数不符合规范 |
| 1002 | 未登录 | 缺少或无效的 Authorization Header |
| 1003 | Token过期 | access_token 或 refresh_token 已过期 |
| 1004 | 权限不足 | 当前角色无权执行此操作 |
| 2001 | 资源不存在 | 请求的资源ID在数据库中不存在 |
| 2002 | 资源冲突 | 重复创建（如邮箱已注册、文献已在知识库） |
| 3001 | 数据源不可用 | 科应API等外部数据源连接失败 |
| 3002 | 检索超时 | 检索请求超过30秒未返回 |
| 4001 | 算力配额不足 | 用户当日CPU/GPU配额已用完 |
| 4002 | 会话状态异常 | 沙箱会话已被销毁或不可恢复 |
| 5000 | 服务器内部错误 | 未预期的后端异常 |

## 4.3 分页规范

**请求参数：**

| 参数 | 类型 | 默认值 | 最大值 | 说明 |
|------|------|--------|--------|------|
| page | integer | 1 | — | 页码（1-based） |
| page_size | integer | 20 | 100 | 每页条数 |

**响应格式（统一包裹在 `data` 中）：**

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## 4.4 鉴权方式

**方式**: Bearer Token（JWT）

**Header**: `Authorization: Bearer {access_token}`

**Token有效期**:
- `access_token`: 2小时（7200秒）
- `refresh_token`: 7天（604800秒）

**Token刷新流程**:
1. 客户端检测到 `access_token` 过期（收到 `1003` 错误码）
2. 客户端调用 `POST /api/v1/auth/refresh` 传入 `refresh_token`
3. 服务端验证 `refresh_token` 有效性，返回新的 `access_token` 和 `refresh_token`
4. 客户端更新本地存储的 Token，重试原请求

**JWT Payload 结构**:
```json
{
  "sub": "10001",
  "role": "user",
  "iat": 1751443200,
  "exp": 1751450400,
  "jti": "uuid"
}
```

## 4.5 日志格式

所有API请求自动记录，格式如下（由FastAPI中间件实现）：

```json
{
  "timestamp": "2026-07-02T14:30:00.123Z",
  "method": "GET",
  "path": "/api/v1/search?q=reinforcement+learning",
  "user_id": "10001",
  "ip": "192.168.1.100",
  "user_agent": "SciAgent-Desktop/1.0.0",
  "duration_ms": 245,
  "status_code": 200,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## 4.6 技术架构

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | Python (FastAPI) | 异步高性能，自动生成 OpenAPI 文档 |
| 前端框架 | Next.js (TypeScript) | React SSR，SEO友好，App Router |
| 桌面壳 | Electron | 跨平台桌面应用，支持 Windows / macOS / Linux |
| 数据库 | PostgreSQL 15+ | 主数据库 + pgvector 向量扩展 |
| 缓存 | Redis 7+ | Session、验证码、Token黑名单 |
| 消息队列 | RabbitMQ / Redis Streams | 文献索引、日志持久化异步处理 |
| 容器运行时 | Docker Engine API | 沙箱会话管理 |
| AI服务 | 混元 API + DeepSeek API | 写作辅助、语义搜索 |
| 文献数据源 | 科应 API（主） | 架构预留多源聚合能力 |
| 对象存储 | MinIO / S3 兼容 | 用户上传文件、仿真结果、算法模板文件 |
| 日志系统 | Elasticsearch + Kibana | 运维日志聚合分析（与防篡改日志独立） |

## 4.7 安全规范

- 密码使用 bcrypt (cost=12) 哈希存储
- 手机号使用 AES-256-GCM 加密存储
- 所有API请求强制 HTTPS（生产环境）
- JWT Secret 至少 256 位随机字符串
- 敏感操作（删除/角色变更）需二次确认
- SQL 注入防护：100% 参数化查询（由 SQLAlchemy ORM 保障）
- XSS 防护：输出自动转义（Next.js 默认）
- CORS 白名单：仅允许管理后台配置的域名
- 速率限制：登录接口 5次/分钟/IP；通用API 60次/分钟/用户

---

# 第5章：开发顺序与依赖关系图

```
┌─────────────────────────────────────────────────────┐
│  第1波（同时开工）                                    │
│                                                     │
│  M0 项目骨架+数据库+鉴权中间件                          │
│  M1 用户体系（注册/登录/权限）                          │
│  M2 文献检索（科应API对接+多源聚合架构）                 │
│  M3 文献阅读+个人知识库                                │
│  M4 前端Electron壳+基础UI框架                          │
│                                                     │
│  依赖关系：M1/M2/M3 均依赖 M0                         │
│           M2/M3 均依赖 M1（鉴权）                      │
│           M4 独立启动                                 │
└───────────────────────┬─────────────────────────────┘
                        │ 第1波完成50%后
                        ▼
┌─────────────────────────────────────────────────────┐
│  第2波                                               │
│                                                     │
│  M5 AI写作辅助（依赖M2文献数据、M3知识库）               │
│  M6 Docker仿真沙箱（依赖M0鉴权）                        │
│  M7 四级协作空间（依赖M1用户体系）                      │
│  M8 防篡改日志（依赖M0基础框架）                        │
│                                                     │
│  依赖关系：M5 → M2, M3                               │
│           M6 → M0                                    │
│           M7 → M1                                    │
│           M8 → M0                                    │
└───────────────────────┬─────────────────────────────┘
                        │ 第2波完成
                        ▼
┌─────────────────────────────────────────────────────┐
│  第3波                                               │
│                                                     │
│  M9 算法商城（依赖M1用户体系、M6沙箱）                  │
│                                                     │
│  依赖关系：M9 → M1, M6                               │
└─────────────────────────────────────────────────────┘
```

**里程碑定义：**

| 里程碑 | 完成标准 | 预估时间 |
|--------|---------|---------|
| M0+M1 完成 | 用户可注册、登录、Token鉴权可用 | 第4周 |
| M2+M3 完成 | 文献可检索、可收藏、可导出引用 | 第8周 |
| M4 完成 | Electron桌面壳可运行、基础路由可切换 | 第8周（与M2/M3并行） |
| **Alpha内测** | M0-M4 完成，核心文献检索+管理闭环可用 | 第8周 |
| M5 完成 | AI写作辅助可用（综述/润色/降重+溯源） | 第12周 |
| M6 完成 | Docker沙箱可创建、运行、暂停、恢复 | 第12周 |
| M7 完成 | 协作空间可创建、任务可下发提交 | 第14周 |
| M8 完成 | 防篡改日志哈希链正常运行 | 第14周 |
| **Beta公测** | 所有核心模块完成，师生全流程可用 | 第16周 |
| M9 完成 | 算法商城上线（预留功能） | 第20周 |
| **v1.0正式发布** | 全部模块完成，启动高校B端销售 | 第20周 |

---

# 第6章：验收Checklist

## M0 基础设施

- [ ] 项目骨架创建完成，目录结构符合 FastAPI 规范
- [ ] PostgreSQL 15+ 数据库运行正常，所有核心表创建完成
- [ ] pgvector 扩展已启用，文献表 embedding 列可用
- [ ] JWT 鉴权中间件可用：自动拦截未登录请求，返回 `1002`
- [ ] 统一错误码体系实现：所有端点返回标准 `{code, message, data, request_id}` 格式
- [ ] 统一日志中间件实现：所有请求记录到文件/Elasticsearch
- [ ] Redis 缓存层可用：验证码、Token黑名单功能正常
- [ ] CORS 中间件配置：白名单模式
- [ ] 速率限制中间件配置并测试通过
- [ ] `/health` 端点返回数据库连接状态和版本信息
- [ ] OpenAPI 文档（Swagger UI）可访问

## M1 用户体系

- [ ] 邮箱注册：输入邮箱+密码 → 发送验证邮件 → 点击验证 → 注册完成
- [ ] 邮箱+密码登录：返回 access_token + refresh_token
- [ ] 手机号注册：输入手机号 → 发送短信验证码 → 输入验证码+密码 → 注册完成
- [ ] 手机号+验证码登录：返回 Token
- [ ] 微信扫码登录接口预留：`POST /api/v1/auth/login/wechat` 接口定义完成
- [ ] Token 刷新机制正常：`refresh_token` 过期前可刷新，过期后返回 `1003`
- [ ] 登出功能：Token 加入黑名单，后续请求返回 `1002`
- [ ] 密码找回：邮箱重置密码流程完整可用
- [ ] 个人信息查询和更新：`GET/PUT /api/v1/user/profile`
- [ ] 角色权限控制生效：普通用户访问 `/api/v1/admin/*` 返回 `1004`
- [ ] 管理员变更用户角色：`PUT /api/v1/admin/users/{user_id}/role`

## M2 文献检索

- [ ] 关键词检索：中文检索结果正常
- [ ] 关键词检索：英文检索结果正常
- [ ] 布尔逻辑：AND / OR / NOT 组合检索结果正确过滤
- [ ] DOI 精确查询：输入合法 DOI 返回唯一文献
- [ ] DOI 精确查询：非法/不存在 DOI 返回 `2001`
- [ ] 高级筛选：年份范围过滤正确
- [ ] 高级筛选：期刊名称过滤正确
- [ ] 高级筛选：作者名过滤正确
- [ ] 多数据源聚合：科应API为主数据源，结果格式统一
- [ ] 架构预留：新增数据源仅需实现统一 Adapter 接口
- [ ] 分页功能：page/page_size 参数正确生效，total_pages 计算准确
- [ ] 分页边界：page_size 超过 100 时自动截断为 100
- [ ] 检索历史保存：`POST /api/v2/papers/history` 保存成功
- [ ] 检索历史查询：`GET /api/v2/papers/history` 返回历史列表
- [ ] 文献详情：`GET /api/v2/papers/{paper_id}` 返回完整元数据
- [ ] 错误处理：数据源不可用时返回 `3001`（不崩溃）
- [ ] 错误处理：检索超时时返回 `3002`

## M3 文献阅读+个人知识库

- [ ] 添加文献到知识库：`POST /api/v3/papers` 创建成功
- [ ] 重复添加保护：同一文献再次添加返回 `2002`
- [ ] 知识库列表查询：按文件夹/标签/阅读状态筛选
- [ ] 知识库文献更新：移动文件夹、修改标签、标记状态
- [ ] 知识库文献移除：`DELETE` 后不再出现在列表中
- [ ] 文件夹创建：支持嵌套文件夹，如 `联邦学习/差分隐私`
- [ ] 文件夹树查询：返回层级结构
- [ ] 文献批注添加：高亮文本 + 笔记 + 位置信息完整保存
- [ ] 文献批注查询：按 library_id 返回批注列表
- [ ] 文献批注删除：`DELETE` 后不再出现
- [ ] 参考文献导出：GB/T 7714 格式正确
- [ ] 参考文献导出：APA / IEEE / MLA 格式正确
- [ ] 参考文献导出：bibtex 输出格式正确，可直接用于 LaTeX
- [ ] 引用关系图谱：返回 nodes + edges 结构，可渲染为可视化图
- [ ] 阅读历史记录：记录最后阅读时间和阅读时长
- [ ] 收藏/取消收藏：`is_favorited` 状态正确切换

## M4 前端Electron壳

- [ ] Electron应用可正常启动（Windows / macOS / Linux）
- [ ] 基础路由框架搭建：登录页 / 主页 / 搜索页 / 知识库页
- [ ] Next.js SSR正常渲染
- [ ] API请求代理配置正确（开发模式 + 生产模式）
- [ ] Token自动刷新：拦截器检测到 `1003` 后自动刷新
- [ ] 全局加载状态和错误提示组件
- [ ] 响应式布局适配（桌面为主，平板可选）

## M5 AI写作辅助

- [ ] 文献综述初稿生成：选定文献 → AI生成结构化Markdown
- [ ] AI生成内容溯源：每段标注是否AI生成及来源文献
- [ ] 溯源查看：`GET /api/v5/writing/documents/{id}/trace` 返回分段溯源数据
- [ ] 中文学术润色：输入粗糙文本 → 输出学术化表达
- [ ] 英文学术润色：输入非母语英文 → 输出地道学术英文
- [ ] 语句降重（中文）：相似度明显降低，学术原意保留
- [ ] 语句降重（英文）：Similarity score 低于 0.6
- [ ] 目标期刊格式化：按指定期刊调整格式规范
- [ ] 参考文献自动插入：在指定位置插入格式化引用
- [ ] 文档内容编辑和保存：`PUT /api/v5/writing/documents/{id}`
- [ ] AI生成比例统计准确：`ai_generated_ratio` 字段反映实际占比
- [ ] **溯源标注不可绕过**：确认无API路径可生成不带溯源标记的AI内容

## M6 代码沙箱 ✅

- [✅] `POST /api/v6/sandbox/execute`：Python subprocess 执行 (timeout 30s)，R/Julia mock
- [✅] `GET /api/v6/sandbox/executions/{id}`：查询执行记录
- [✅] `GET /api/v6/sandbox/status`：服务健康状态 + 支持语言列表
- [ ] Docker 隔离模式（预留，docker_available=false）

## M7 四级协作空间

- [ ] 创建协作空间：school / college / lab / class / friends 五级均可创建
- [ ] 邀请成员：指定角色（admin/leader/member/viewer）加入空间
- [ ] 成员列表：`GET /api/v1/workspaces/{id}/members` 返回完整成员+角色
- [ ] 角色变更：super_admin可提升/降低成员角色
- [ ] 移除成员：admin可移除普通成员
- [ ] 权限边界：viewer不可添加文献到共享池，不可下发任务
- [ ] 共享文献池：成员添加文献后其他成员可见
- [ ] 导师下发任务：指定学生、截止日期、优先级
- [ ] 学生提交任务：含文字说明和附件（文档/沙箱文件）
- [ ] 科研动态流：任务提交、文献共享等事件自动记录
- [ ] 算力配额分配：空间管理员可为成员分配不同配额

## M8 防篡改日志

- [ ] 自动记录：检索、阅读、写作、沙箱操作自动写入日志
- [ ] 哈希链：每条日志 `current_hash` = SHA-256(prev_hash + 日志内容)
- [ ] 哈希连续性验证：校验报告中 `broken_chains` 为 0
- [ ] 日志不可删除：无 DELETE 端点暴露
- [ ] 日志不可修改：无 PUT/PATCH 端点暴露
- [ ] 管理员审计面板：按用户/时间/行为类型检索日志
- [ ] 完整性校验报告：一键生成，含统计摘要和哈希链状态
- [ ] 行为统计：按用户/日期聚合的行为统计报表
- [ ] 权限控制：仅 admin/super_admin 可访问审计接口

## M9 算法商城 ✅

- [✅] `GET /api/v9/algorithms`：分页浏览，DB 优先 + 空库自动回退 mock 种子数据
- [✅] `GET /api/v9/algorithms/{id}`：算法详情
- [✅] `POST /api/v9/algorithms/{id}/execute`：算法执行
- [✅] `GET /api/v9/executions`：分页查询执行历史
- [✅] `GET /api/v9/executions/{id}`：执行详情
- [ ] 算法上传与版本管理（预留）

## P0 功能增强（v1.2 新增，全部通过回归测试 292 passed）

- [✅] **P0-A Plan模式**：五阶段写作流程（大纲生成→确认→逐节生成→逐节确认→合并），5 个 API 端点可用
- [✅] **P0-B SSE流式进度反馈**：6 阶段进度推送（searching/reading/analyzing/planning/writing/finalizing），已集成到 M2/M5/M6
- [✅] **P0-C 失败降级引擎**：5 场景降级策略（搜索超时/沙箱不可用/LLM配额/写作过载/格式转换失败），`degradation.py` 实现
- [✅] **P0-D 原子级溯源引擎**：句子级溯源，5 种溯源类型 + 3 级置信度，`GET /api/v5/writing/documents/{id}/trace` 返回 v2.0 结构
- [✅] **P0-E 对话搜索管理**：重命名/置顶/软删除/回收站/永久删除/标题搜索/全局搜索，7 个 API 端点
- [✅] **P0-F LaTeX+Mermaid渲染**：content_blocks 字段支持 5 种混合内容块（text/latex/mermaid/table/code）
- [✅] **P0-G 三层记忆系统**：UserProfile + TopicMemory + SessionContext，凌晨 3:00 自动归档，MemoryEngine Hook 集成到 M2/M3/M5/M6，8 个 API 端点
- [✅] **P0-H 科研绘图Skill**：5 类模板（bar/line/box/heatmap/volcano）+ 通用自定义渲染，300 DPI base64 PNG，6 个 API 端点
- [✅] **P0-I .scix加密格式**：AES-256-GCM + PBKDF2 + Ed25519 签名，ZIP 容器，4 个 API 端点
- [✅] **P0-I 分享模式**：受控分享链接+水印+权限控制（过期/次数/下载/打印），4 个 API 端点
- [✅] **P0-K 学术规范自查**：3 个端点（格式检查/结构检查/引用完整性检查）
- [✅] **P0-L 论文配图自动化**：自动美化（300 DPI / seaborn 风格 / 字号配色优化）+ 多图拼接 panel + 灰度转换，3 个 API 端点

## 预编排工作流

- [✅] **5 种工作流**：phd_proposal (6步) / lit_review (5步) / reproduction (4步) / submission (4步) / defense (3步)
- [✅] **工作流引擎**：DAG 编排自动推进，断点续传，人机协作暂停等待，8 个 API 端点
- [✅] **回归测试**：全量 292 项测试 passed（含原有的 268 项 + P0 新增 24 项）

## 交叉验收场景

- [ ] **全流程串联**：注册 → 登录 → 检索文献 → 添加到知识库 → 批注 → 创建综述 → 润色 → 导出引用 → 沙箱验证实验 → 任务提交 → 日志审计
- [ ] **权限穿透**：普通用户无法访问管理面板、无法查看他人知识库、无法操作非自己所属的空间
- [ ] **并发测试**：100个用户同时检索，响应时间 < 3秒
- [ ] **Token过期测试**：access_token过期后刷新流程平滑，用户无感知
- [ ] **数据持久化**：重启服务后知识库、批注、文档数据不丢失
- [ ] **私有化部署**：支持 Docker Compose 一键部署，所有服务本地运行

---

## 已知缺陷跟踪

代码质量审查发现并修复的全部 62 项缺陷记录在 [docs/ISSUE_TRACKER.md](<D:\projects\sci-agent\docs\ISSUE_TRACKER.md>)。
截至 2026-07-04，全部 P0-P3 已清零（100% 完成）。该文档是开发端对齐的唯一真相源。

---

*本文档为「垂直科研全流程Agent」产品的唯一真相源（Single Source of Truth），所有开发、测试、运维决策均以此为准。任何修改需通过 PR 评审并同步更新本文档。*
*（内容由AI生成，仅供参考）*
