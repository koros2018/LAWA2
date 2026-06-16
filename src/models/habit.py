"""
LAWA 养成引擎 — 习惯数据模型

§2.3 设计文档对应：
  - user_habit_config: 用户习惯配置
  - daily_info_feed: 每日信息流记录
  - micro_habit_log: 微习惯日志
  - variable_reward: 可变奖励记录
  - language_asset: 语言资产
  - growth_milestone: 成长里程碑
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.main import Base


def _utcnow():
    return datetime.now(timezone.utc)


class UserHabitConfig(Base):
    """用户习惯配置"""
    __tablename__ = "user_habit_config"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trigger_time_slot: Mapped[str] = mapped_column(String(20), default="morning,noon,evening")  # 触发时段
    info_source_prefs: Mapped[str] = mapped_column(JSON, default=list)  # 内容偏好 ['news','social','tech']
    action_prefs: Mapped[str] = mapped_column(JSON, default=list)  # 行为偏好 ['read','listen','speak','write']
    reward_frequency: Mapped[str] = mapped_column(String(20), default="balanced")  # casual|balanced|intense
    feed_enabled: Mapped[bool] = mapped_column(default=True)
    morning_time: Mapped[str] = mapped_column(String(5), default="07:30")  # 晨间推送时间
    noon_time: Mapped[str] = mapped_column(String(5), default="12:30")
    evening_time: Mapped[str] = mapped_column(String(5), default="21:00")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f"<UserHabitConfig user={self.user_id} trigger={self.trigger_time_slot}>"


class DailyInfoFeed(Base):
    """每日信息流记录"""
    __tablename__ = "daily_info_feed"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    feed_date: Mapped[datetime] = mapped_column(Date, default=_utcnow)
    source: Mapped[str] = mapped_column(String(30))  # news|tweet|video|article|vocab_card|cultural_tip
    source_url: Mapped[str] = mapped_column(Text, nullable=True)
    original_text: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(String(10), default="medium")  # easy|medium|hard|native
    user_interaction: Mapped[str] = mapped_column(String(20), default="pending")  # pending|read|listened|responded|skipped
    vocab_extracted: Mapped[str] = mapped_column(JSON, default=list)  # 自动提取的词汇列表
    comprehension_score: Mapped[float] = mapped_column(Float, nullable=True)  # 理解度评分 0-1
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<DailyInfoFeed {self.source} user={self.user_id[:8]}...>"


class MicroHabitLog(Base):
    """微习惯日志"""
    __tablename__ = "micro_habit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    habit_code: Mapped[str] = mapped_column(String(30))  # read_one_post|listen_one_min|say_one_thing|write_one_sentence|look_up_one
    triggered_by: Mapped[str] = mapped_column(String(20), default="trigger_engine")  # trigger_engine|manual
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completion_status: Mapped[str] = mapped_column(String(10), default="completed")  # completed|partial|skipped
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    feed_id: Mapped[str] = mapped_column(String(36), nullable=True)  # 关联的信息流
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<MicroHabitLog {self.habit_code} +{self.xp_earned}xp>"


class VariableReward(Base):
    """可变奖励记录"""
    __tablename__ = "variable_reward"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    reward_type: Mapped[str] = mapped_column(String(30))  # vocab_discovery|comprehension_breakthrough|culture_egg|pattern_finding|cross_language
    reward_value: Mapped[str] = mapped_column(JSON)  # 奖励详情
    surprise_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    xp_bonus: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<VariableReward {self.reward_type} lvl{self.surprise_level}>"


class LanguageAsset(Base):
    """语言资产（Investment核心）"""
    __tablename__ = "language_asset"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    asset_type: Mapped[str] = mapped_column(String(30))  # vocab_collection|sentence_book|diary_entry|interaction_log
    asset_data: Mapped[str] = mapped_column(JSON)  # 具体内容
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<LanguageAsset {self.asset_type} wc={self.word_count}>"


class SocialSceneLog(Base):
    """社交场景预演记录"""
    __tablename__ = "social_scene_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    scene_code: Mapped[str] = mapped_column(String(40))  # ordering_food|greeting|group_chat|pub_talk|meme_explain
    scene_name: Mapped[str] = mapped_column(String(100))  # 场景名称（本地化）
    native_text: Mapped[str] = mapped_column(Text)  # 用户母语表达
    learn_text: Mapped[str] = mapped_column(Text)  # 目标语言表达
    difficulty: Mapped[str] = mapped_column(String(10), default="easy")  # easy|medium|hard
    understanding_level: Mapped[str] = mapped_column(String(10), default="understand")  # understand|use|create
    practiced: Mapped[int] = mapped_column(Integer, default=0)  # 预演次数
    last_practiced: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<SocialSceneLog {self.scene_code} lvl={self.understanding_level}>"


class SocialVocab(Base):
    """社交词汇/网络用语"""
    __tablename__ = "social_vocab"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    word: Mapped[str] = mapped_column(String(100))  # 词/短语
    meaning: Mapped[str] = mapped_column(Text)  # 含义解释
    scene_example: Mapped[str] = mapped_column(Text)  # 场景例句
    category: Mapped[str] = mapped_column(String(30))  # net_slang|reply_template|meme|life_scene
    understanding_level: Mapped[str] = mapped_column(String(10), default="understand")
    learned_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_reviewed: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<SocialVocab {self.word} ({self.category})>"


class BridgeInteraction(Base):
    """双向桥梁交互记录"""
    __tablename__ = "bridge_interaction"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    partner_id: Mapped[str] = mapped_column(String(36))  # 语伴ID（MVP中固定为 'bob'/'alice'）
    level: Mapped[int] = mapped_column(Integer, default=1)  # 桥梁等级 1-5
    direction: Mapped[str] = mapped_column(String(10))  # send|receive
    native_text: Mapped[str] = mapped_column(Text)  # 母语内容
    learn_text: Mapped[str] = mapped_column(Text)  # 翻译/目标语言内容
    polished_text: Mapped[str] = mapped_column(Text, nullable=True)  # AI润色后
    partner_reply: Mapped[str] = mapped_column(Text, nullable=True)  # 模拟语伴回复
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<BridgeInteraction Lv.{self.level} {self.direction}>"


class GrowthMilestone(Base):
    """成长里程碑"""
    __tablename__ = "growth_milestone"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    milestone_code: Mapped[str] = mapped_column(String(40))  # first_100_words|first_native_post|7_day_streak
    milestone_name: Mapped[str] = mapped_column(String(100))
    milestone_description: Mapped[str] = mapped_column(Text, nullable=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    celebration_type: Mapped[str] = mapped_column(String(20), default="badge")  # confetti|story|badge

    def __repr__(self):
        return f"<GrowthMilestone {self.milestone_code} ({self.celebration_type})>"
