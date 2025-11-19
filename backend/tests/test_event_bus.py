"""
Unit tests for Event Bus
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.event_bus import EventBus, Events
import json


@pytest.mark.event_bus
class TestEventBus:
    """Test EventBus class"""
    
    @pytest.fixture
    def event_bus(self):
        """Create EventBus instance"""
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, event_bus):
        """Test successful connection to RabbitMQ"""
        with patch('services.event_bus.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_connection.channel.return_value = mock_channel
            mock_connect.return_value = mock_connection
            
            await event_bus.connect()
            
            assert event_bus.connection is not None
            assert event_bus.channel is not None
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, event_bus):
        """Test connection failure handling"""
        with patch('services.event_bus.connect_robust') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await event_bus.connect()
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing an event"""
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        event_data = {"user_id": 123, "email": "test@example.com"}
        await event_bus.publish(Events.USER_CREATED, event_data)
        
        mock_exchange.publish.assert_called_once()
        call_args = mock_exchange.publish.call_args
        message = call_args[0][0]
        routing_key = call_args[1]["routing_key"]
        
        assert routing_key == Events.USER_CREATED
        assert b"user.created" in message.body
    
    @pytest.mark.asyncio
    async def test_publish_with_custom_routing_key(self, event_bus):
        """Test publishing event with custom routing key"""
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        await event_bus.publish(
            Events.PAYMENT_COMPLETED,
            {"amount": 99.99},
            routing_key="payment.stripe.completed"
        )
        
        call_args = mock_exchange.publish.call_args
        routing_key = call_args[1]["routing_key"]
        
        assert routing_key == "payment.stripe.completed"
    
    @pytest.mark.asyncio
    async def test_disconnect(self, event_bus):
        """Test disconnection from RabbitMQ"""
        event_bus.connection = AsyncMock()
        
        await event_bus.disconnect()
        
        event_bus.connection.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self, event_bus):
        """Test disconnection when not connected"""
        event_bus.connection = None
        
        # Should not raise exception
        await event_bus.disconnect()
    
    def test_events_constants_defined(self):
        """Test that all event constants are defined"""
        assert Events.USER_CREATED == "user.created"
        assert Events.PAYMENT_COMPLETED == "payment.completed"
        assert Events.WORKOUT_CREATED == "workout.created"
        assert Events.MEAL_LOGGED == "meal.logged"
        assert Events.AUDIT_LOG_CREATED == "audit.log_created"


@pytest.mark.event_bus
class TestEventPublishing:
    """Test event publishing scenarios"""
    
    @pytest.mark.asyncio
    async def test_publish_multiple_events(self):
        """Test publishing multiple events in sequence"""
        event_bus = EventBus()
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        events = [
            (Events.USER_CREATED, {"user_id": 1}),
            (Events.PAYMENT_COMPLETED, {"amount": 50}),
            (Events.WORKOUT_CREATED, {"duration": 30}),
        ]
        
        for event_type, data in events:
            await event_bus.publish(event_type, data)
        
        assert mock_exchange.publish.call_count == 3
    
    @pytest.mark.asyncio
    async def test_publish_with_timestamp(self):
        """Test that published events include timestamp"""
        event_bus = EventBus()
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        await event_bus.publish(Events.USER_CREATED, {"user_id": 1})
        
        call_args = mock_exchange.publish.call_args
        message = call_args[0][0]
        body = json.loads(message.body.decode())
        
        assert "timestamp" in body
        assert "event_type" in body
        assert "data" in body


@pytest.mark.event_bus
class TestEventBusEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_publish_with_none_data(self):
        """Test publishing with None data"""
        event_bus = EventBus()
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        await event_bus.publish(Events.PAYMENT_FAILED, None)
        
        mock_exchange.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_with_large_data(self):
        """Test publishing with large data payload"""
        event_bus = EventBus()
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        event_bus.channel.default_exchange = mock_exchange
        
        large_data = {
            "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        }
        
        await event_bus.publish(Events.WORKOUT_COMPLETED, large_data)
        
        mock_exchange.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_failure_logging(self):
        """Test that publish failures are logged"""
        event_bus = EventBus()
        event_bus.channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_exchange.publish.side_effect = Exception("Publish failed")
        event_bus.channel.default_exchange = mock_exchange
        
        with pytest.raises(Exception):
            await event_bus.publish(Events.USER_CREATED, {"user_id": 1})
