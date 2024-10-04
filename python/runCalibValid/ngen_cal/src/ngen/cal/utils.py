"""
This module contains utility functions for executing calibration and validation run.

@author: Nels Frazer, Xia Feng
"""

from contextlib import contextmanager
from email.mime.text import MIMEText
from os import getcwd, chdir, PathLike
import smtplib
from typing import Union

@contextmanager
def pushd(path: Union[str, PathLike]) -> None:
    """Change current working directory to the given path.

    Parameters
    ----------
    path : New directory path 

    Returns
    ----------
    None

    """
    # Save current working directory
    cwd = getcwd()

    # Change the directory
    chdir(path)
    try:
        yield 
    finally:
        chdir(cwd)


def complete_msg(basinid: str, run_name: str, path: Union[str, PathLike]=None, user_email: str=None) -> None:
        """Send email notification to user if run is completed.

        Parameters
        ----------
        basinid : Basin ID
        run_name : Calibration or validation run
        path : Work directory 
        user_email : User email address 

        Returns
        ----------
        None

        """
        if user_email:
            subject = run_name.capitalize()  + ' Run for {}'.format(basinid) + ' Is Completed'
            content = subject + ' at ' + path if path else subject 
            msg = MIMEText(content)
            msg['Subject'] = subject
            msg['From'] = 'foo@example.com'
            msg['To'] = user_email
            try:
                server = smtplib.SMTP('foo-server-name')
                server.sendmail(msg['From'], user_email, msg.as_string())
            except Exception as e:
                print(e)
                print('completion email ' + 'for {}'.format(basinid) + "can't be sent")
            finally:
                server.quit()
        else:
            print(content)
