"""One local job and one monthly schedule. Start UI/daemon with dagster dev."""
from dagster import Definitions, ScheduleDefinition, job, op

from scripts.run_pipeline import export_outputs, run_dbt


@op
def build_dbt() -> bool:
    run_dbt('build')
    return True


@op
def export_monthly_statement(build_succeeded: bool) -> str:
    if not build_succeeded:
        raise RuntimeError('dbt build must pass before exporting')
    return export_outputs()


@job
def monthly_analytics_job():
    export_monthly_statement(build_dbt())


monthly_schedule = ScheduleDefinition(
    name='monthly_analytics_schedule',
    job=monthly_analytics_job,
    cron_schedule='0 6 1 * *',
    execution_timezone='Europe/Berlin',
    description='Rebuild the fixed offline sample and export all available partner-month statements on the first day at 06:00 Berlin time.',
)

defs = Definitions(jobs=[monthly_analytics_job], schedules=[monthly_schedule])

if __name__ == '__main__':
    result = monthly_analytics_job.execute_in_process()
    if not result.success:
        raise SystemExit(1)
