# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _logger.info("Computing exception name for failed jobs")
        _compute_jobs_new_values(env)


def _compute_jobs_new_values(env):
    job_exc_infos = env["queue.job"].search(
        [("state", "=", "failed"), ("exc_info", "!=", False)]
    ).read(fields=["exc_info"])
    for job_row in job_exc_infos:
        exception_details = _get_exception_details(job_row["exc_info"])
        if exception_details:
            job = env["queue.job"].browse(job_row["id"])
            job.write(exception_details)


def _get_exception_details(exc_info):
    for line in reversed(exc_info.splitlines()):
        if _find_exception(line):
            name, msg = line.split(":", 1)
            return {
                "exc_name": name.strip(),
                "exc_message": msg.strip("()', \""),
            }


def _find_exception(line):
    # Just a list of common errors.
    # If you want to target others, add your own migration step for your db.
    exceptions = (
        "Error:",  # catch all well named exceptions
        # other live instance errors found
        "requests.exceptions.MissingSchema",
        "botocore.errorfactory.NoSuchKey",
    )
    for exc in exceptions:
        if exc in line:
            return exc
