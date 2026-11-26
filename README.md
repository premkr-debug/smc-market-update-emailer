# Market ki Halchal - automated HTML email (free)
Daily at ~3:50 PM IST (Mon-Fri) GitHub builds:
  docs/email.html          -> preview in browser
  docs/email-source.txt    -> HTML source, copy-paste into WebEngage "Custom HTML"
  docs/subject.txt         -> subject line for the day
Holidays are skipped automatically. Test anytime: Actions > Run workflow (set variable FORCE=1 on non-trading days).
Local preview with sample data: python market_update.py --demo
