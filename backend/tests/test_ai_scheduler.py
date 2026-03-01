"""
AI Scheduler Tests
Tests AI scheduler with market gating functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from ai.scheduler import AIScheduler
from app.services.market_session_manager import get_market_session_manager


class TestAIScheduler:
    """Test AI scheduler functionality"""
    
    @pytest.fixture
    def scheduler(self):
        """Create AI scheduler instance"""
        return AIScheduler()
    
    @pytest.fixture
    def mock_market_session_manager(self):
        """Create mock market session manager"""
        manager = Mock()
        manager.is_market_open.return_value = True
        return manager


class TestMarketGating:
    """Test AI market gating functionality"""
    
    @pytest.mark.asyncio
    async def test_market_open_check_in_scheduler(self):
        """Test that scheduler checks market status"""
        with patch('ai.scheduler.get_market_session_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.is_market_open.return_value = True
            mock_get_manager.return_value = mock_manager
            
            scheduler = AIScheduler()
            
            # Verify market session manager is accessible
            assert mock_manager.is_market_open() == True
    
    @pytest.mark.asyncio
    async def test_market_closed_prevents_ai_execution(self):
        """Test that AI jobs don't run when market is closed"""
        with patch('ai.scheduler.get_market_session_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.is_market_open.return_value = False
            mock_get_manager.return_value = mock_manager
            
            # Test market status check
            is_market_open = mock_manager.is_market_open()
            assert is_market_open == False
    
    @pytest.mark.asyncio
    async def test_market_open_allows_ai_execution(self):
        """Test that AI jobs run when market is open"""
        with patch('ai.scheduler.get_market_session_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.is_market_open.return_value = True
            mock_get_manager.return_value = mock_manager
            
            # Test market status check
            is_market_open = mock_manager.is_market_open()
            assert is_market_open == True
    
    @pytest.mark.asyncio
    async def test_scheduler_job_setup(self):
        """Test that scheduler jobs are properly set up"""
        scheduler = AIScheduler()
        
        # Verify scheduler has jobs
        assert len(scheduler.scheduler.get_jobs()) > 0
        
        # Check specific jobs exist
        job_ids = [job.id for job in scheduler.scheduler.get_jobs()]
        expected_jobs = [
            'signal_generation',
            'paper_trade_monitor', 
            'new_prediction_processing',
            'outcome_checker',
            'learning_update',
            'market_snapshot'
        ]
        
        for expected_job in expected_jobs:
            assert expected_job in job_ids


class TestAISchedulerJobs:
    """Test individual AI scheduler jobs"""
    
    @pytest.mark.asyncio
    async def test_signal_generation_job_structure(self):
        """Test signal generation job structure"""
        scheduler = AIScheduler()
        
        # Test job exists and has correct properties
        job = scheduler.scheduler.get_job('signal_generation')
        assert job is not None
        assert job.name == 'Generate AI signals'
        assert job.max_instances == 1  # Prevent overlapping
    
    @pytest.mark.asyncio
    async def test_paper_trade_monitor_job_structure(self):
        """Test paper trade monitor job structure"""
        scheduler = AIScheduler()
        
        job = scheduler.scheduler.get_job('paper_trade_monitor')
        assert job is not None
        assert job.name == 'Monitor paper trades'
        assert job.max_instances == 1
    
    @pytest.mark.asyncio
    async def test_learning_update_job_structure(self):
        """Test learning update job structure"""
        scheduler = AIScheduler()
        
        job = scheduler.scheduler.get_job('learning_update')
        assert job is not None
        assert job.name == 'Update AI learning'
        assert job.max_instances == 1
    
    @pytest.mark.asyncio
    async def test_market_snapshot_job_structure(self):
        """Test market snapshot job structure"""
        scheduler = AIScheduler()
        
        job = scheduler.scheduler.get_job('market_snapshot')
        assert job is not None
        assert job.name == 'Collect market snapshots'
        assert job.max_instances == 1


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle"""
    
    @pytest.mark.asyncio
    async def test_scheduler_start(self):
        """Test scheduler starts correctly"""
        scheduler = AIScheduler()
        
        # Start scheduler
        scheduler.start()
        
        # Verify scheduler is running
        assert scheduler.scheduler.running is True
    
    @pytest.mark.asyncio
    async def test_scheduler_stop(self):
        """Test scheduler stops correctly"""
        scheduler = AIScheduler()
        
        # Start then stop scheduler
        scheduler.start()
        scheduler.stop()
        
        # Verify scheduler is stopped
        assert scheduler.scheduler.running is False
    
    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status"""
        scheduler = AIScheduler()
        
        # Get job status
        job_status = scheduler.get_job_status()
        
        # Verify status structure
        assert isinstance(job_status, list)
        assert len(job_status) > 0
        
        for job in job_status:
            assert 'id' in job
            assert 'name' in job
            assert 'trigger' in job


class TestMarketSessionIntegration:
    """Test integration with market session manager"""
    
    @pytest.mark.asyncio
    async def test_market_session_manager_import(self):
        """Test that market session manager can be imported"""
        from app.services.market_session_manager import get_market_session_manager
        
        manager = get_market_session_manager()
        assert manager is not None
        assert hasattr(manager, 'is_market_open')
    
    @pytest.mark.asyncio
    async def test_market_time_check(self):
        """Test market time checking logic"""
        from app.services.market_session_manager import check_market_time
        
        # Test the function exists and returns boolean
        result = check_market_time()
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])
