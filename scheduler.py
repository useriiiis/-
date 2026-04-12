"""Scheduler for daily automated email sending."""

import schedule
import time
from datetime import datetime
from config import SEND_TIME
from run_daily import run_daily_pipeline


def job():
    """Scheduled daily job."""
    print(f"\n{'='*60}")
    print(f"  Scheduled job triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    try:
        run_daily_pipeline(send_email=True)
    except Exception as e:
        print(f"[Scheduler] Pipeline error: {e}")


def start_scheduler():
    """Start the daily scheduler."""
    print(f"╔{'═'*58}╗")
    print(f"║  ALPHA SIGNAL - Daily Scheduler{' '*26}║")
    print(f"║  Scheduled send time: {SEND_TIME}{' '*(35-len(SEND_TIME))}║")
    print(f"║  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{' '*18}║")
    print(f"╚{'═'*58}╝")

    schedule.every().day.at(SEND_TIME).do(job)

    # Also run on weekdays at a secondary time for market close summary
    # schedule.every().monday.at("16:30").do(job)
    # schedule.every().tuesday.at("16:30").do(job)
    # schedule.every().wednesday.at("16:30").do(job)
    # schedule.every().thursday.at("16:30").do(job)
    # schedule.every().friday.at("16:30").do(job)

    print(f"\nNext run: {schedule.next_run()}")
    print("Waiting for scheduled time... (Press Ctrl+C to stop)\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys

    if "--now" in sys.argv:
        print("Running immediately...")
        job()
    else:
        start_scheduler()
