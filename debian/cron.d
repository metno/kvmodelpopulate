#
# Regular cron jobs for the kvalobs-model-populate package
#

TZ=UTC
LOGFILE="/var/log/kvalobs/kvmodelpopulate_cron_last_run.log"

#15 4,16 * * *    kvalobs    /usr/bin/kvmodelpopulate -l/var/log/kvalobs/kvalobs_model_populate.log --log-level=info --no-progress-bar 2>/dev/null
15 */2 * * *    kvalobs    /usr/bin/kvmodelpopulate -l/var/log/kvalobs/kvalobs_model_populate.log --log-level=info --no-progress-bar &>${LOGFILE}
