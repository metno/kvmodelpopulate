#
# Regular cron jobs for the kvalobs-model-populate package
#

TZ=UTC

15 4,16 * * *    kvalobs    /usr/bin/kvalobs_model_populate -l/var/log/kvalobs/kvalobs_model_populate.log --log-level=info --no-progress-bar 2>/dev/null

