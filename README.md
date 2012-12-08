Provide similar functionalities as offered by [FollowUpThen.com][1] and
[FollowUp.cc][2]. This script should be run both as email handler and also
under cron.

Cron:-

   */5 * * * * /path/to/followup/followup.py send > /dev/null 2>&1 

Above run the script every 5 minutes so you can have notification down to 5 minutes
interval. For email handler, just put the path to the script in your email server
configuration and make sure the script is executable. It will read the email from
stdin.

[1]:http://www.followupthen.com/
[2]:http://www.followup.cc/
