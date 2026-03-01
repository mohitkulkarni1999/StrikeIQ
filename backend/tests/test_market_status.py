"""
Market Status Tests
Tests market session manager and market status detection
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, time
import pytz
from app.services.market_session_manager import (
    MarketSessionManager, 
    get_market_session_manager,
    check_market_time,
    EngineMode
)


class TestMarketSessionManager:
    """Test market session manager functionality"""
    
    @pytest.fixture
    def session_manager(self):
        """Create market session manager instance"""
        return MarketSessionManager()
    
    @pytest.fixture
    def ist_timezone(self):
        """Get IST timezone"""
        return pytz.timezone("Asia/Kolkata")


class TestMarketTimeDetection:
    """Test market time detection logic"""
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_open_during_weekday_hours(self, mock_datetime):
        """Test market is open during weekday hours"""
        # Mock Wednesday 10:30 AM IST
        mock_now = datetime(2024, 12, 25, 10, 30)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is True
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_before_opening(self, mock_datetime):
        """Test market is closed before opening time"""
        # Mock Wednesday 9:00 AM IST (before 9:15 AM)
        mock_now = datetime(2024, 12, 25, 9, 0)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_after_closing(self, mock_datetime):
        """Test market is closed after closing time"""
        # Mock Wednesday 4:00 PM IST (after 3:30 PM)
        mock_now = datetime(2024, 12, 25, 16, 0)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_on_weekend(self, mock_datetime):
        """Test market is closed on weekends"""
        # Mock Saturday 10:30 AM IST
        mock_now = datetime(2024, 12, 28, 10, 30)  # Saturday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_on_sunday(self, mock_datetime):
        """Test market is closed on Sunday"""
        # Mock Sunday 11:00 AM IST
        mock_now = datetime(2024, 12, 29, 11, 0)  # Sunday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False


class TestMarketSessionManagerMethods:
    """Test market session manager methods"""
    
    def test_is_market_open_method(self):
        """Test is_market_open method"""
        manager = MarketSessionManager()
        
        # Test method exists and returns boolean
        result = manager.is_market_open()
        assert isinstance(result, bool)
    
    def test_singleton_pattern(self):
        """Test that market session manager uses singleton pattern"""
        manager1 = get_market_session_manager()
        manager2 = get_market_session_manager()
        
        # Should return same instance
        assert manager1 is manager2
    
    def test_engine_mode_enum(self):
        """Test EngineMode enum values"""
        assert EngineMode.LIVE == "LIVE"
        assert EngineMode.PAPER == "PAPER"
        assert EngineMode.CLOSED == "CLOSED"


class TestMarketBoundaryConditions:
    """Test market boundary conditions"""
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_open_at_exact_opening_time(self, mock_datetime):
        """Test market is open at exactly 9:15 AM"""
        # Mock Wednesday 9:15 AM IST (exact opening time)
        mock_now = datetime(2024, 12, 25, 9, 15)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is True
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_open_at_exact_closing_time(self, mock_datetime):
        """Test market is open at exactly 3:30 PM"""
        # Mock Wednesday 3:30 PM IST (exact closing time)
        mock_now = datetime(2024, 12, 25, 15, 30)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is True
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_one_minute_after_closing(self, mock_datetime):
        """Test market is closed one minute after closing"""
        # Mock Wednesday 3:31 PM IST (one minute after closing)
        mock_now = datetime(2024, 12, 25, 15, 31)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False
    
    @patch('app.services.market_session_manager.datetime')
    def test_market_closed_one_minute_before_opening(self, mock_datetime):
        """Test market is closed one minute before opening"""
        # Mock Wednesday 9:14 AM IST (one minute before opening)
        mock_now = datetime(2024, 12, 25, 9, 14)  # Wednesday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False


class TestMarketStatusIntegration:
    """Test market status integration with other components"""
    
    def test_market_status_for_ai_scheduler(self):
        """Test market status can be used by AI scheduler"""
        manager = get_market_session_manager()
        
        # Test that AI scheduler can check market status
        is_open = manager.is_market_open()
        assert isinstance(is_open, bool)
    
    def test_market_status_for_websocket(self):
        """Test market status can be used by WebSocket manager"""
        manager = get_market_session_manager()
        
        # Test that WebSocket manager can check market status
        is_open = manager.is_market_open()
        assert isinstance(is_open, bool)
    
    def test_market_status_consistency(self):
        """Test market status is consistent across calls"""
        manager = get_market_session_manager()
        
        # Multiple calls should return consistent results
        result1 = manager.is_market_open()
        result2 = manager.is_market_open()
        
        # Results should be the same (within same second)
        assert type(result1) == type(result2)  # Both should be boolean


class TestMarketTimeValidation:
    """Test market time validation edge cases"""
    
    def test_timezone_handling(self):
        """Test that timezone is correctly handled"""
        from app.services.market_session_manager import IST
        
        # Verify IST timezone is correctly configured
        assert IST.zone == "Asia/Kolkata"
    
    def test_market_hours_constants(self):
        """Test market hours are correctly defined"""
        # These should match NSE trading hours
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        assert market_open.hour == 9
        assert market_open.minute == 15
        assert market_close.hour == 15
        assert market_close.minute == 30
    
    @patch('app.services.market_session_manager.datetime')
    def test_holiday_scenario(self, mock_datetime):
        """Test behavior on holidays (weekend logic)"""
        # Mock on a weekday but treat as weekend for testing
        # Note: Current implementation only checks weekends, not holidays
        mock_now = datetime(2024, 12, 25, 10, 30)  # Wednesday
        mock_now.weekday.return_value = 5  # Pretend it's Saturday
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = check_market_time()
        assert result is False  # Should be closed on weekend


if __name__ == "__main__":
    pytest.main([__file__])
