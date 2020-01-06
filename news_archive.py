#!/usr/bin/env python3

import datetime
import imaplib
import json
import subprocess
import sys
from typing import Optional


def main(args) -> None:
    simulate = '--test' in args
    verbose = '--verbose' in args
    
    try:
        _run(verbose)
    except Exception as e:
        if simulate:
            raise
        else:
            _notifylocal(
                title='news_archive',
                subtitle='Execution error',
                message='%s: %s' % (type(e).__name__, str(e)))


def _run(verbose: bool) -> None:
    import news_archive_config as config
    
    min_date = (
        datetime.date.today() - 
        datetime.timedelta(days=config.MAX_AGE_DAYS)
    )

    imap = imaplib.IMAP4_SSL(config.HOSTNAME, config.PORT)
    imap.login(config.USER, config.PASSWORD)
    try:
        imap.select(config.FROM_MAILBOX)

        # Search for messages to move
        criteria = '(BEFORE %s)' % _format_rfc2822_date(min_date)
        #criteria = 'ALL'  # for debugging
        (status, data) = imap.search(None, criteria)
        assert status.startswith('OK')
        message_ids = data[0].split()  # ex: [b'1', b'2'] or []

        # Move messages
        if len(message_ids) > 0:
            if verbose: print('Moving %d message(s)...' % len(message_ids))
            
            (status, data) = imap.copy(b':'.join(message_ids), config.TO_MAILBOX)
            assert status.startswith('OK')
            
            (status, data) = imap.store(b':'.join(message_ids), '+FLAGS', '\\Deleted')
            assert status.startswith('OK')
    finally:
        imap.logout()


def _format_rfc2822_date(date: datetime.date) -> str:
    month_name = [
        None,
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec",
    ][date.month]
    return '%d-%s-%d' % (date.day, month_name, date.year)


def _notifylocal(
        message: str,
        subtitle: Optional[str]=None,
        title: Optional[str]=None) -> None:
    script = 'display notification %s' % json.dumps(message)
    if title is not None:
        script += ' with title %s' % json.dumps(title)
    if subtitle is not None:
        script += ' subtitle %s' % json.dumps(subtitle)
    subprocess.call(
        ['/usr/bin/osascript', '-e', script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main(sys.argv[1:])
