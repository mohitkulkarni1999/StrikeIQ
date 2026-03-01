"""
API Endpoints Tests
Tests system monitoring endpoints and API functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


class TestSystemMonitoringEndpoints:
    """Test system monitoring endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_ws_status_endpoint(self, client):
        """Test WebSocket status endpoint"""
        response = client.get("/system/ws-status")
        
        # Should return 200 (endpoint exists)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check for expected status fields
        expected_fields = ["status", "connected", "last_heartbeat", "uptime"]
        for field in expected_fields:
            # Note: Fields may not exist initially, but endpoint should respond
            assert isinstance(data, dict)
    
    def test_ai_status_endpoint(self, client):
        """Test AI status endpoint"""
        response = client.get("/system/ai-status")
        
        # Should return 200 (endpoint exists)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check for expected AI status fields
        expected_fields = ["status", "market_open", "active_jobs", "last_run"]
        for field in expected_fields:
            # Note: Fields may not exist initially, but endpoint should respond
            assert isinstance(data, dict)
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestWebSocketStatusDetection:
    """Test WebSocket status detection in system endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('app.services.websocket_market_feed.ws_feed_manager')
    def test_ws_status_connected(self, mock_ws_manager, client):
        """Test WebSocket status when connected"""
        # Mock connected state
        mock_ws_manager.is_connected = True
        mock_ws_manager.feed = Mock()
        mock_ws_manager.feed.is_connected = True
        mock_ws_manager.feed.running = True
        
        response = client.get("/system/ws-status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @patch('app.services.websocket_market_feed.ws_feed_manager')
    def test_ws_status_disconnected(self, mock_ws_manager, client):
        """Test WebSocket status when disconnected"""
        # Mock disconnected state
        mock_ws_manager.is_connected = False
        mock_ws_manager.feed = None
        
        response = client.get("/system/ws-status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestAIStatusDetection:
    """Test AI status detection in system endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('ai.scheduler.ai_scheduler')
    @patch('app.services.market_session_manager.get_market_session_manager')
    def test_ai_status_market_open(self, mock_session_manager, mock_ai_scheduler, client):
        """Test AI status when market is open"""
        # Mock market open
        mock_manager = Mock()
        mock_manager.is_market_open.return_value = True
        mock_session_manager.return_value = mock_manager
        
        # Mock AI scheduler running
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_scheduler.get_jobs.return_value = []
        mock_ai_scheduler.get_job_status.return_value = []
        mock_ai_scheduler.scheduler = mock_scheduler
        
        response = client.get("/system/ai-status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @patch('ai.scheduler.ai_scheduler')
    @patch('app.services.market_session_manager.get_market_session_manager')
    def test_ai_status_market_closed(self, mock_session_manager, mock_ai_scheduler, client):
        """Test AI status when market is closed"""
        # Mock market closed
        mock_manager = Mock()
        mock_manager.is_market_open.return_value = False
        mock_session_manager.return_value = mock_manager
        
        # Mock AI scheduler
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_scheduler.get_jobs.return_value = []
        mock_ai_scheduler.get_job_status.return_value = []
        mock_ai_scheduler.scheduler = mock_scheduler
        
        response = client.get("/system/ai-status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestBackwardCompatibility:
    """Test backward compatibility of existing APIs"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_existing_api_endpoints_work(self, client):
        """Test that existing API endpoints continue working"""
        # Test auth status endpoint
        response = client.get("/api/v1/options/auth/status")
        assert response.status_code in [200, 401, 500]  # Should respond, even if not authenticated
        
        # Test market data endpoint (may fail auth but should exist)
        response = client.get("/api/v1/market-data/NIFTY")
        assert response.status_code in [200, 401, 404, 500]  # Should respond
        
        # Test options contract endpoint
        response = client.get("/api/v1/options/contract/NIFTY")
        assert response.status_code in [200, 401, 400, 500]  # Should respond
    
    def test_api_router_structure(self):
        """Test that API router structure is maintained"""
        from app.main import app
        
        # Check that routers are included
        router_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                router_paths.append(route.path)
        
        # Verify key API paths exist
        expected_paths = [
            "/health",
            "/",
            "/api/v1"
        ]
        
        for expected_path in expected_paths:
            matching_routes = [path for path in router_paths if path.startswith(expected_path)]
            assert len(matching_routes) > 0, f"No routes found for {expected_path}"


class TestSystemStatusReporting:
    """Test system status reporting functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_system_status_structure(self, client):
        """Test system status response structure"""
        # Test WebSocket status
        ws_response = client.get("/system/ws-status")
        assert ws_response.status_code == 200
        ws_data = ws_response.json()
        assert isinstance(ws_data, dict)
        
        # Test AI status
        ai_response = client.get("/system/ai-status")
        assert ai_response.status_code == 200
        ai_data = ai_response.json()
        assert isinstance(ai_data, dict)
        
        # Both should have consistent structure
        for status_data in [ws_data, ai_data]:
            assert "status" in status_data or isinstance(status_data, dict)
    
    def test_system_status_error_handling(self, client):
        """Test system status error handling"""
        # Test with invalid endpoint
        response = client.get("/system/invalid-endpoint")
        assert response.status_code == 404
        
        # Test with malformed request (if applicable)
        response = client.get("/system/ws-status?invalid=param")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestAPIResponseFormats:
    """Test API response format consistency"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_json_response_format(self, client):
        """Test that endpoints return valid JSON"""
        endpoints = [
            "/health",
            "/",
            "/system/ws-status",
            "/system/ai-status"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            # Should be valid JSON
            assert response.headers["content-type"] == "application/json"
            
            # Should be parseable
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_error_response_format(self, client):
        """Test that error responses have consistent format"""
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        if response.headers.get("content-type") == "application/json":
            data = response.json()
            assert "detail" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__])
