"""
Event Bus System - Xử lý async events giữa các services
Sử dụng RabbitMQ cho async communication
"""
import json
import asyncio
from typing import Callable, Dict, List, Any
from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractConnection, AbstractChannel
import structlog
import os

logger = structlog.get_logger()

class EventBus:
    """Centralized event bus để publish/subscribe events"""
    
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.exchange_name = os.getenv("RABBITMQ_EXCHANGE", "fitness_events")
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
    
    async def connect(self):
        """Kết nối đến RabbitMQ"""
        try:
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.declare_exchange(
                self.exchange_name,
                type="topic",
                durable=True
            )
            logger.info("EventBus connected to RabbitMQ", 
                       exchange=self.exchange_name)
        except Exception as e:
            logger.error("Failed to connect EventBus", error=str(e))
            raise
    
    async def disconnect(self):
        """Ngắt kết nối RabbitMQ"""
        if self.connection:
            await self.connection.close()
    
    async def publish(self, event_type: str, data: Dict[str, Any], 
                     routing_key: str = None):
        """
        Publish event đến RabbitMQ
        
        Args:
            event_type: Loại event (e.g., 'payment.completed', 'user.created')
            data: Dữ liệu event
            routing_key: RabbitMQ routing key (nếu None, dùng event_type)
        """
        if not self.channel:
            await self.connect()
        
        routing_key = routing_key or event_type
        payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        message = Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            content_encoding="utf-8"
        )
        
        try:
            await self.channel.default_exchange.publish(
                message,
                routing_key=routing_key
            )
            logger.info("Event published", 
                       event_type=event_type, 
                       routing_key=routing_key)
        except Exception as e:
            logger.error("Failed to publish event", 
                        event_type=event_type, 
                        error=str(e))
            raise
    
    async def subscribe(self, event_type: str, handler: Callable, 
                       queue_name: str = None):
        """
        Subscribe đến events
        
        Args:
            event_type: Loại event (e.g., 'payment.*' for wildcard)
            handler: Async function để xử lý event
            queue_name: Tên queue (nếu None, tạo unique queue)
        """
        if not self.channel:
            await self.connect()
        
        queue_name = queue_name or f"{event_type}_{id(handler)}"
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(self.exchange_name, routing_key=event_type)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        event_data = json.loads(message.body.decode())
                        await handler(event_data)
                except Exception as e:
                    logger.error("Error processing event", 
                               event_type=event_type, 
                               error=str(e))
        
        self.subscribers.setdefault(event_type, []).append(handler)


# Singleton instance
event_bus = EventBus()


# Event types constants
class Events:
    """Định nghĩa tất cả event types trong hệ thống"""
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role_changed"
    
    # Payment events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    
    # Workout events
    WORKOUT_CREATED = "workout.created"
    WORKOUT_COMPLETED = "workout.completed"
    WORKOUT_UPDATED = "workout.updated"
    
    # Nutrition events
    MEAL_LOGGED = "meal.logged"
    MEAL_UPDATED = "meal.updated"
