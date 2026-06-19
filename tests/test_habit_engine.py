"""
LAWA2 习惯引擎 — 综合测试
"""
import pytest
import asyncio
from datetime import date

pytestmark = pytest.mark.asyncio


# ── Action Engine 单元测试 ──

class TestActionEngine:
    """ActionEngine 核心逻辑测试"""

    def test_calculate_xp_basic(self):
        from src.engine.action_engine import ActionEngine
        ae = ActionEngine()
        assert ae.calculate_xp('read_one_post', 30) == 5
        assert ae.calculate_xp('say_one_thing', 10) == 8
        assert ae.calculate_xp('look_up_one', 15) == 3
        assert ae.calculate_xp('write_one_sentence', 60) == 10

    def test_calculate_xp_with_duration_bonus(self):
        from src.engine.action_engine import ActionEngine
        ae = ActionEngine()
        # 超出默认时长应有加成
        xp_normal = ae.calculate_xp('read_one_post', 30)
        xp_long = ae.calculate_xp('read_one_post', 90)
        assert xp_long > xp_normal

    def test_calculate_xp_with_streak(self):
        from src.engine.action_engine import ActionEngine
        ae = ActionEngine()
        xp_no_streak = ae.calculate_xp('say_one_thing', 10)
        xp_streak = ae.calculate_xp('say_one_thing', 10, streak_bonus=7)
        assert xp_streak > xp_no_streak

    def test_calculate_xp_max_cap(self):
        from src.engine.action_engine import ActionEngine
        ae = ActionEngine()
        # 加成应有限度
        xp = ae.calculate_xp('read_one_post', 9999, streak_bonus=999)
        assert xp <= 100  # 不出现异常大值

    def test_list_habits(self):
        from src.engine.action_engine import ActionEngine
        habits = ActionEngine.list_available_habits()
        assert 'read_one_post' in habits
        assert 'say_one_thing' in habits
        assert len(habits) == 5

    def test_get_habit_info(self):
        from src.engine.action_engine import ActionEngine
        info = ActionEngine.get_habit_info('read_one_post')
        assert info is not None
        assert info['base_xp'] == 5
        assert 'icon' in info
        assert info['name'] == '读一条资讯'

    def test_invalid_habit(self):
        from src.engine.action_engine import ActionEngine
        assert ActionEngine.get_habit_info('nonexistent') is None


# ── Reward Engine 单元测试 ──

class TestRewardEngine:
    """RewardEngine 核心逻辑测试"""

    def test_reward_templates(self):
        from src.engine.reward_engine import REWARD_TEMPLATES
        assert 'vocab_discovery' in REWARD_TEMPLATES
        assert 'vocab_blossom' in REWARD_TEMPLATES
        assert len(REWARD_TEMPLATES) == 6

    def test_reward_surprise_levels(self):
        from src.engine.reward_engine import REWARD_TEMPLATES
        # vocab_blossom 是稀有奖励
        assert REWARD_TEMPLATES['vocab_blossom']['surprise_level'] == 5
        # 基础奖励 surprise 较低
        assert REWARD_TEMPLATES['culture_egg']['surprise_level'] == 2

    def test_reward_xp_bonus(self):
        from src.engine.reward_engine import REWARD_TEMPLATES
        # 稀有奖励 XP 更高
        assert REWARD_TEMPLATES['vocab_blossom']['xp_bonus'] == 20
        assert REWARD_TEMPLATES['culture_egg']['xp_bonus'] == 3

    def test_get_reward_info(self):
        from src.engine.reward_engine import RewardEngine
        info = RewardEngine.get_reward_info('pattern_finding')
        assert info is not None
        assert info['name'] == '兴趣模式发现'
        assert len(info['messages']) >= 1

    def test_invalid_reward(self):
        from src.engine.reward_engine import RewardEngine
        assert RewardEngine.get_reward_info('invalid') is None


# ── Trigger Engine 单元测试 ──

class TestTriggerEngine:
    """TriggerEngine 核心逻辑测试"""

    def test_seed_content_count(self):
        from src.engine.trigger_engine import SEED_CONTENT
        assert len(SEED_CONTENT) >= 4
        assert len(SEED_CONTENT['news_brief']) >= 5

    def test_seed_content_has_vocab_hints(self):
        from src.engine.trigger_engine import SEED_CONTENT
        for category, items in SEED_CONTENT.items():
            for item in items:
                assert 'vocab_hints' in item
                assert 'difficulty' in item
                assert 'text' in item

    def test_content_type_choice(self):
        from src.engine.trigger_engine import TriggerEngine
        te = TriggerEngine()
        # 不同时段应有不同默认内容类型
        morning = te._choose_content_type('morning')
        assert morning in ['news_brief', 'fun_fact']
        noon = te._choose_content_type('noon')
        assert noon in ['social_post', 'fun_fact']
        evening = te._choose_content_type('evening')
        assert evening in ['vocab_card', 'news_brief']


# ── Investment Engine 单元测试 ──

class TestInvestmentEngine:
    """InvestmentEngine 核心逻辑测试"""

    def test_vocab_stages(self):
        from src.engine.investment_engine import VOCAB_STAGES
        assert 'seed' in VOCAB_STAGES
        assert 'fruit' in VOCAB_STAGES
        assert len(VOCAB_STAGES) == 5
        assert VOCAB_STAGES['seed']['emoji'] == '🌰'
        assert VOCAB_STAGES['bloom']['emoji'] == '🌼'

    def test_milestones(self):
        from src.engine.investment_engine import MILESTONES
        assert 'first_action' in MILESTONES
        assert '30_day_streak' in MILESTONES
        assert 'level_5' in MILESTONES
        assert MILESTONES['first_action']['celebration_type'] == 'confetti'


# ── Habit Model 单元测试 ──

class TestHabitModels:
    """数据模型字段验证"""

    def test_habit_model_fields(self):
        from src.models.habit import MicroHabitLog
        assert hasattr(MicroHabitLog, 'habit_code')
        assert hasattr(MicroHabitLog, 'xp_earned')
        assert hasattr(MicroHabitLog, 'completion_status')

    def test_feed_model_fields(self):
        from src.models.habit import DailyInfoFeed
        assert hasattr(DailyInfoFeed, 'original_text')
        assert hasattr(DailyInfoFeed, 'difficulty_level')
        assert hasattr(DailyInfoFeed, 'user_interaction')

    def test_reward_model_fields(self):
        from src.models.habit import VariableReward
        assert hasattr(VariableReward, 'reward_type')
        assert hasattr(VariableReward, 'surprise_level')
        assert hasattr(VariableReward, 'xp_bonus')

    def test_asset_model_fields(self):
        from src.models.habit import LanguageAsset
        assert hasattr(LanguageAsset, 'asset_type')
        assert hasattr(LanguageAsset, 'word_count')

    def test_milestone_model_fields(self):
        from src.models.habit import GrowthMilestone
        assert hasattr(GrowthMilestone, 'milestone_code')
        assert hasattr(GrowthMilestone, 'celebration_type')

    def test_config_model_fields(self):
        from src.models.habit import UserHabitConfig
        assert hasattr(UserHabitConfig, 'trigger_time_slot')
        assert hasattr(UserHabitConfig, 'feed_enabled')


# ── 集成测试 ──

@pytest.mark.integration
class TestIntegration:
    """E2E 集成测试（需要数据库）"""

    async def test_full_habit_flow(self, db_session):
        """完整微行为流程"""
        from src.engine.action_engine import ActionEngine
        user_id = 'integ_test_user'
        
        result = await ActionEngine().record_habit(user_id, 'read_one_post', 30, db=db_session)
        assert result['xp_earned'] >= 1
        assert result['habit_log_id'] is not None

    async def test_feed_and_action(self, db_session):
        """信息流 + 行为联动"""
        from src.engine.trigger_engine import TriggerEngine
        from src.engine.action_engine import ActionEngine
        user_id = 'feed_test_user'
        
        feed = await TriggerEngine().get_feed(user_id, 'morning', db=db_session)
        assert feed['feed_id'] is not None
        
        result = await ActionEngine().record_habit(
            user_id, 'read_one_post', 45,
            feed_id=feed['feed_id'],
            db=db_session,
        )
        assert result['xp_earned'] >= 1

    async def test_daily_reward(self, db_session):
        """每日首次推送奖励"""
        from src.engine.trigger_engine import TriggerEngine
        import uuid
        user_id = f'reward_test_{uuid.uuid4().hex[:8]}'
        
        feed = await TriggerEngine().get_feed(user_id, 'morning', db=db_session)
        assert feed['is_first_today'] == True
        if feed.get('reward'):
            assert feed['reward']['xp_bonus'] >= 1

    async def test_garden_status(self, db_session):
        """语言花园状态"""
        from src.engine.investment_engine import InvestmentEngine
        from src.engine.action_engine import ActionEngine
        
        user_id = 'garden_test_user'
        await ActionEngine().record_habit(user_id, 'read_one_post', 30, db=db_session)
        
        garden = await InvestmentEngine().get_garden_status(user_id)
        assert 'habit_level' in garden
        assert 'total_xp' in garden
        assert 'by_stage' in garden

    async def test_milestone_detection(self, db_session):
        """里程碑检测"""
        from src.engine.investment_engine import InvestmentEngine
        from src.engine.action_engine import ActionEngine
        
        import uuid
        user_id = f'ms_test_{uuid.uuid4().hex[:8]}'
        await ActionEngine().record_habit(user_id, 'read_one_post', 30, db=db_session)
        
        milestones = await InvestmentEngine().check_milestones(user_id)
        assert any(m['code'] == 'first_action' for m in milestones)


# ── 并发测试 ──

@pytest.mark.stress
class TestConcurrency:
    """并发行为记录"""

    async def test_concurrent_actions(self):
        """并发记录多个行为（每个行为使用独立 session）"""
        from src.engine.action_engine import ActionEngine
        user_id = 'concurrent_user'
        
        async def record_one():
            from src.database.main import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                return await ActionEngine().record_habit(user_id, 'read_one_post', 30, db=session)
        
        tasks = [record_one() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r['xp_earned'] >= 1 for r in results)


# ── 错误处理测试 ──

class TestErrorHandling:
    """边界情况"""

    def test_invalid_habit_code_static(self):
        from src.engine.action_engine import ActionEngine
        # 静态方法应返回 None
        assert ActionEngine.get_habit_info('nonexistent') is None

    async def test_nonexistent_user_garden(self, db_session):
        """不存在的用户查询花园"""
        from src.engine.investment_engine import InvestmentEngine
        garden = await InvestmentEngine().get_garden_status('nonexistent_user')
        assert garden['total_xp'] == 0
        assert garden['habit_level'] == 1
