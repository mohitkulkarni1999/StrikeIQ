"""
WebSocket Connection Tests
Tests WebSocket connection management and status detection
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from app.services.websocket_market_feed import WebSocketFeedManager, WebSocketMarketFeed
from app.services.market_session_manager import get_market_session_manager


class TestWebSocketConnection:
    """Test WebSocket connection lifecycle"""
    
    @pytest.fixture
    def ws_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketFeedManager()
    
    @pytest.fixture
    def mock_feed(self):
        """Create mock WebSocket feed"""
        feed = Mock(spec=WebSocketMarketFeed)
        feed.is_connected = False
        feed.running = False
        feed.start = AsyncMock()
        feed.disconnect = AsyncMock()
        return feed
    
    @pytest.mark.asyncio
    async def test_start_feed_when_not_running(self, ws_manager, mock_feed):
        """Test starting feed when not running"""
        ws_manager.feed = mock_feed
        mock_feed.running = False
        
        result = await ws_manager.start_feed()
        
        assert result == mock_feed
        mock_feed.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_feed_when_already_running(self, ws_manager, mock_feed):
        """Test starting feed when already running"""
        ws_manager.feed = mock_feed
        mock_feed.running = True
        
        result = await ws_manager.start_feed()
        
        assert result == mock_feed
        mock_feed.start.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_feed_when_available(self, ws_manager, mock_feed):
        """Test getting feed when available"""
        ws_manager.feed = mock_feed
        mock_feed.running = True
        
        result = await ws_manager.get_feed()
        
        assert result == mock_feed
    
    @pytest.mark.asyncio
    async def test_get_feed_when_not_available(self, ws_manager):
        """Test getting feed when not available"""
        result = await ws_manager.get_feed()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cleanup_all(self, ws_manager, mock_feed):
        """Test cleanup of all feeds"""
        ws_manager.feed = mock_feed
        
        await ws_manager.cleanup_all()
        
        mock_feed.disconnect.assert_called_once()
        assert ws_manager.feed is None
    
    def test_is_connected_property(self, ws_manager, mock_feed):
        """Test is_connected property"""
        # Test when no feed
        assert ws_manager.is_connected is False
        
        # Test when feed exists but not connected
        ws_manager.feed = mock_feed
        mock_feed.is_connected = False
        assert ws_manager.is_connected is False
        
        # Test when feed exists and connected
        mock_feed.is_connected = True
        assert ws_manager.is_connected is True


class TestWebSocketStatusDetection:
    """Test WebSocket status detection for LIVE/SNAPSHOT/OFFLINE"""
    
    @pytest.mark.asyncio
    async def test_live_status_when_connected(self):
        """Test LIVE status when WebSocket is connected"""
        manager = WebSocketFeedManager()
        feed = Mock()
        feed.is_connected = True
        feed.running = True
        manager.feed = feed
        
        assert manager.is_connected is True
    
    @pytest.mark.asyncio
    async def test_offline_status_when_not_connected(self):
        """Test OFFLINE status when WebSocket is not connected"""
        manager = WebSocketFeedManager()
        
        assert manager.is_connected is False
    
    @pytest.mark.asyncio
    async def test_snapshot_mode_fallback(self):
        """Test SNAPSHOT mode as fallback when WebSocket fails"""
        # This would be tested in the actual useLiveMarketData hook
        # For now, we test that the manager reports disconnected
        manager = WebSocketFeedManager()
        
        assert manager.is_connected is False


if __name__ == "__main__":
    pytest.main([__file__])
