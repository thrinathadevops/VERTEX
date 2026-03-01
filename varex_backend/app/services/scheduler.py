# PATH: varex_backend/app/services/scheduler.py
# Subscription expiry + daily cleanup jobs using APScheduler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from datetime import datetime
import os

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

from app.db.session import AsyncSessionLocal
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.core.logger import structured_logger as logger

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
_scheduler_lock_file = None
_scheduler_lock_owner = False


async def expire_subscriptions_job():
    """Runs daily at 00:05 IST - expires overdue subscriptions and downgrades roles."""
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()
            result = await db.execute(
                select(Subscription)
                .where(Subscription.status == SubscriptionStatus.active)
                .where(Subscription.expiry_date < now)
                .where(Subscription.expiry_date.isnot(None))
            )
            subs = result.scalars().all()
            count = 0
            for sub in subs:
                sub.status = SubscriptionStatus.expired
                user_result = await db.execute(select(User).where(User.id == sub.user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.role = UserRole.free_user
                count += 1

            await db.commit()
            if count:
                logger.info(f"Scheduler: expired {count} subscriptions")
        except Exception as e:
            logger.error(f"expire_subscriptions_job failed: {e}", exc_info=True)
            await db.rollback()


async def send_expiry_reminders_job():
    """Runs daily at 09:00 IST - sends 3-day expiry reminder emails."""
    from datetime import timedelta
    import httpx
    from app.core.config import settings

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()
            in_3_days = now + timedelta(days=3)
            result = await db.execute(
                select(Subscription)
                .where(Subscription.status == SubscriptionStatus.active)
                .where(Subscription.expiry_date.between(now, in_3_days))
            )
            subs = result.scalars().all()
            for sub in subs:
                user_result = await db.execute(select(User).where(User.id == sub.user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    expiry_str = sub.expiry_date.strftime("%d %B %Y") if sub.expiry_date else "soon"
                    if settings.SENDGRID_API_KEY:
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                "https://api.sendgrid.com/v3/mail/send",
                                headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                                json={
                                    "personalizations": [{"to": [{"email": user.email}]}],
                                    "from": {"email": settings.FROM_EMAIL, "name": "VAREX Technologies"},
                                    "subject": "Your VAREX subscription expires in 3 days",
                                    "content": [{
                                        "type": "text/html",
                                        "value": f"""
                                        <h2>Hi {user.name},</h2>
                                        <p>Your <strong>{sub.plan_type.value}</strong> subscription expires on <strong>{expiry_str}</strong>.</p>
                                        <p>Renew now to keep access to all premium content and features.</p>
                                        <a href="{settings.FRONTEND_URL}/pricing" style="background:#0ea5e9;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;margin:16px 0">Renew Subscription</a>
                                        <p>- VAREX Technologies</p>
                                        """
                                    }]
                                }
                            )
                    else:
                        logger.warning(f"Skipping expiry email for {user.email} (no SendGrid key)")
            logger.info(f"Scheduler: sent {len(subs)} expiry reminder emails")
        except Exception as e:
            logger.error(f"send_expiry_reminders_job failed: {e}", exc_info=True)


def _acquire_scheduler_lock() -> bool:
    """Allow only one worker process to run APScheduler jobs."""
    global _scheduler_lock_file, _scheduler_lock_owner

    if fcntl is None:
        _scheduler_lock_owner = True
        return True

    lock_path = os.getenv("SCHEDULER_LOCK_PATH", "/tmp/varex_scheduler.lock")
    _scheduler_lock_file = open(lock_path, "w")

    try:
        fcntl.flock(_scheduler_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _scheduler_lock_owner = True
        return True
    except BlockingIOError:
        _scheduler_lock_owner = False
        return False


def start_scheduler():
    if scheduler.state == STATE_RUNNING:
        return

    if not _acquire_scheduler_lock():
        logger.info("APScheduler skipped in this worker (lock owned by another worker)")
        return

    scheduler.add_job(
        expire_subscriptions_job,
        CronTrigger(hour=0, minute=5, timezone="Asia/Kolkata"),
        id="expire_subscriptions",
        replace_existing=True,
    )
    scheduler.add_job(
        send_expiry_reminders_job,
        CronTrigger(hour=9, minute=0, timezone="Asia/Kolkata"),
        id="expiry_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started - jobs: expire_subscriptions, expiry_reminders")


def stop_scheduler():
    global _scheduler_lock_file, _scheduler_lock_owner

    if scheduler.state == STATE_RUNNING:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")

    if _scheduler_lock_owner and _scheduler_lock_file and fcntl is not None:
        try:
            fcntl.flock(_scheduler_lock_file.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass

    if _scheduler_lock_file:
        try:
            _scheduler_lock_file.close()
        except Exception:
            pass

    _scheduler_lock_file = None
    _scheduler_lock_owner = False
