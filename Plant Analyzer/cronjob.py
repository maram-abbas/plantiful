# Package Scheduler.
from apscheduler.schedulers.blocking import BlockingScheduler

# Main cronjob function.
from analyzer import main

# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
# Job is scheduled to run every 12 hours
scheduler.add_job(main, "interval", seconds=43200)

scheduler.start()