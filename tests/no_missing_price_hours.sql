-- Anchor to the declared sample calendar so a completely missing day also fails.
-- UTC avoids confusing 23/25-hour Europe/Berlin DST days with missing data.
with expected as (
    select expected_hour
    from generate_series(
        timestamp '{{ var("sample_start") }}',
        timestamp '{{ var("sample_end_exclusive") }}' - interval '1 hour',
        interval '1 hour'
    ) as hours(expected_hour)
), actual as (
    select timestamp_utc, count(*) as observation_count
    from {{ ref('stg_prices') }}
    group by timestamp_utc
)
select coalesce(e.expected_hour, a.timestamp_utc) as failing_hour,
       coalesce(a.observation_count, 0) as observation_count
from expected e
full outer join actual a on e.expected_hour = a.timestamp_utc
where e.expected_hour is null or coalesce(a.observation_count, 0) <> 1
