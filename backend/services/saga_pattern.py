"""
Saga Pattern - Xử lý distributed transactions giữa các services
Sử dụng orchestration pattern với event bus
"""
from enum import Enum
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import structlog
from services.event_bus import event_bus, Events
import json

logger = structlog.get_logger()


class SagaStatus(str, Enum):
    """Trạng thái của saga"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


class SagaStep:
    """Một bước trong saga transaction"""
    
    def __init__(
        self,
        name: str,
        action: Callable,
        compensation: Callable,
        event_type: str = None
    ):
        self.name = name
        self.action = action
        self.compensation = compensation
        self.event_type = event_type
        self.status = SagaStatus.PENDING
        self.result = None
        self.error = None
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute step action"""
        try:
            self.status = SagaStatus.IN_PROGRESS
            self.result = await self.action(context)
            logger.info(f"Step {self.name} completed", result=self.result)
            return self.result
        except Exception as e:
            self.error = str(e)
            logger.error(f"Step {self.name} failed", error=str(e))
            raise
    
    async def compensate(self, context: Dict[str, Any]) -> None:
        """Execute compensation (rollback)"""
        try:
            logger.info(f"Compensating step {self.name}")
            await self.compensation(context)
        except Exception as e:
            logger.error(f"Compensation failed for {self.name}", error=str(e))


class Saga:
    """
    Saga Orchestrator - Quản lý distributed transactions
    Giải quyết vấn đề consistency giữa các services
    
    Ví dụ: Payment -> Update User Status -> Create Workout Access
    Nếu bất kỳ bước nào fail, all steps được compensate (rollback)
    """
    
    def __init__(self, saga_id: str, saga_type: str):
        self.saga_id = saga_id
        self.saga_type = saga_type
        self.status = SagaStatus.PENDING
        self.steps: List[SagaStep] = []
        self.completed_steps: List[SagaStep] = []
        self.context: Dict[str, Any] = {"saga_id": saga_id}
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
    
    def add_step(self, step: SagaStep) -> "Saga":
        """Thêm step vào saga"""
        self.steps.append(step)
        return self  # For chaining
    
    async def execute(self) -> Dict[str, Any]:
        """Execute saga transaction"""
        try:
            self.status = SagaStatus.IN_PROGRESS
            logger.info(
                f"Saga {self.saga_type} started",
                saga_id=self.saga_id,
                total_steps=len(self.steps)
            )
            
            # Execute all steps
            for step in self.steps:
                try:
                    result = await step.execute(self.context)
                    self.context[f"{step.name}_result"] = result
                    self.completed_steps.append(step)
                    
                    # Publish event if defined
                    if step.event_type:
                        await event_bus.publish(
                            step.event_type,
                            {
                                "saga_id": self.saga_id,
                                "step": step.name,
                                "result": result
                            }
                        )
                
                except Exception as e:
                    logger.error(
                        f"Saga failed at step {step.name}",
                        saga_id=self.saga_id,
                        error=str(e)
                    )
                    
                    # Compensate completed steps
                    await self._compensate()
                    self.status = SagaStatus.FAILED
                    raise
            
            # All steps completed successfully
            self.status = SagaStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            
            logger.info(
                f"Saga {self.saga_type} completed successfully",
                saga_id=self.saga_id,
                duration=(self.completed_at - self.created_at).total_seconds()
            )
            
            return {
                "saga_id": self.saga_id,
                "status": self.status,
                "context": self.context
            }
        
        except Exception as e:
            raise
    
    async def _compensate(self) -> None:
        """Compensate completed steps in reverse order"""
        self.status = SagaStatus.COMPENSATING
        logger.info(
            f"Starting compensation for saga {self.saga_id}",
            steps_to_compensate=len(self.completed_steps)
        )
        
        # Execute compensations in reverse order
        for step in reversed(self.completed_steps):
            await step.compensate(self.context)
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại của saga"""
        return {
            "saga_id": self.saga_id,
            "saga_type": self.saga_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "result": step.result
                }
                for step in self.steps
            ]
        }


# Predefined Saga Templates cho common workflows

class PaymentSaga(Saga):
    """
    Saga cho payment workflow:
    1. Charge user via Stripe
    2. Update user subscription status
    3. Create workout access
    4. Send confirmation email
    """
    
    def __init__(self, saga_id: str, payment_data: Dict[str, Any]):
        super().__init__(saga_id, "payment")
        self.payment_data = payment_data
    
    async def build(self):
        """Build payment saga steps"""
        async def charge_user(context):
            # Mock: Call Stripe API
            return {
                "transaction_id": "txn_123",
                "amount": self.payment_data["amount"],
                "status": "completed"
            }
        
        async def compensate_charge(context):
            # Refund transaction
            logger.info("Refunding payment", txn_id=context.get("charge_user_result", {}).get("transaction_id"))
        
        async def update_subscription(context):
            # Update user subscription in database
            return {"subscription_status": "active"}
        
        async def compensate_subscription(context):
            # Cancel subscription
            logger.info("Cancelling subscription")
        
        async def create_access(context):
            # Create workout access
            return {"access_level": "premium"}
        
        async def compensate_access(context):
            # Revoke access
            logger.info("Revoking access")
        
        self.add_step(SagaStep(
            "charge_user",
            charge_user,
            compensate_charge,
            Events.PAYMENT_COMPLETED
        ))
        
        self.add_step(SagaStep(
            "update_subscription",
            update_subscription,
            compensate_subscription,
            Events.SUBSCRIPTION_CREATED
        ))
        
        self.add_step(SagaStep(
            "create_access",
            create_access,
            compensate_access
        ))
        
        return self


class WorkoutSaga(Saga):
    """
    Saga cho workout creation workflow:
    1. Create workout record
    2. Calculate calories
    3. Update user stats
    """
    
    def __init__(self, saga_id: str, workout_data: Dict[str, Any]):
        super().__init__(saga_id, "workout")
        self.workout_data = workout_data
    
    async def build(self):
        """Build workout saga steps"""
        async def create_workout(context):
            return {"workout_id": "w_123", "status": "created"}
        
        async def compensate_workout(context):
            logger.info("Deleting workout")
        
        async def calculate_calories(context):
            return {"calories_burned": 250}
        
        async def compensate_calories(context):
            logger.info("Reverting calorie calculation")
        
        async def update_stats(context):
            return {"stats_updated": True}
        
        async def compensate_stats(context):
            logger.info("Reverting stats")
        
        self.add_step(SagaStep(
            "create_workout",
            create_workout,
            compensate_workout,
            Events.WORKOUT_CREATED
        ))
        
        self.add_step(SagaStep(
            "calculate_calories",
            calculate_calories,
            compensate_calories
        ))
        
        self.add_step(SagaStep(
            "update_stats",
            update_stats,
            compensate_stats
        ))
        
        return self


# Saga Registry - Track all running sagas
class SagaRegistry:
    """Central registry để track all running sagas"""
    
    def __init__(self):
        self.sagas: Dict[str, Saga] = {}
    
    def register(self, saga: Saga) -> None:
        """Register saga"""
        self.sagas[saga.saga_id] = saga
    
    def get(self, saga_id: str) -> Optional[Saga]:
        """Get saga by ID"""
        return self.sagas.get(saga_id)
    
    def remove(self, saga_id: str) -> None:
        """Remove saga from registry"""
        if saga_id in self.sagas:
            del self.sagas[saga_id]
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status của tất cả sagas"""
        return [saga.get_status() for saga in self.sagas.values()]


# Singleton instance
saga_registry = SagaRegistry()
