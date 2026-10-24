# Running on BigQuery

**not yet verified on BigQuery**

Only DuckDB has executed the models and all 44 existing tests. Offline parsing or compilation of BigQuery SQL does not prove that a cloud build works. No Google Cloud project or credentials were created by the implementation.

Local setup result: `dbt parse --target bigquery` succeeded with the optional adapter installed. A normal compile attempt then stopped with "Your default credentials were not found". A separate offline smoke check rendered the model SQL with anonymous local credentials and socket access disabled. This checks templating only. Authentication is still an unresolved prerequisite for the user to complete, and no cloud query was executed.

## 1. Create your sandbox project

These account and credential steps are for you to perform.

1. Sign in to [BigQuery Studio](https://console.cloud.google.com/bigquery) with your Google account. Accept the Google terms yourself if prompted.
2. Choose **Create project**. Use a globally unique project ID, for example `energy-analytics-YOUR-SUFFIX`, and note the exact ID.
3. Keep billing disabled. Do not activate a free trial or attach a billing account. The [BigQuery sandbox](https://cloud.google.com/bigquery/docs/sandbox) works without a credit card. Verify the sandbox notice is present.
4. In **APIs & Services > Library**, select the project and enable **BigQuery API** (`bigquery.googleapis.com`). This is not a request to enable billing.
5. In BigQuery Explorer, open the project's menu and choose **Create dataset**. Name it `energy_analytics`, set its location to **EU**, and retain the sandbox expiration settings. Use this same location below.

The small sample is intended to fit sandbox limits. Sandbox tables expire after 60 days. DML and streaming are unavailable, so this project uses seed load jobs and full table rebuilds, not incremental models. Consult the linked Google documentation for current quotas and account restrictions.

## 2. Choose your authentication method

### Option A: gcloud application default login

This avoids downloading a service account key. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) if necessary. In PowerShell, from the repository root:

```powershell
$env:DBT_BQ_PROJECT = 'YOUR-EXACT-PROJECT-ID'
$env:DBT_BQ_DATASET = 'energy_analytics'
$env:DBT_BQ_LOCATION = 'EU'
$env:DBT_BQ_METHOD = 'oauth'
Remove-Item Env:GOOGLE_APPLICATION_CREDENTIALS -ErrorAction SilentlyContinue
gcloud auth login
gcloud config set project $env:DBT_BQ_PROJECT
gcloud services enable bigquery.googleapis.com --project $env:DBT_BQ_PROJECT
gcloud auth application-default login
gcloud auth application-default set-quota-project $env:DBT_BQ_PROJECT
```

Complete both browser sign-in flows yourself. Ordinary `gcloud auth login` alone is not application default authentication. ADC stores credentials outside the repository. You do not paste any token into this project. The identity needs BigQuery Job User on the project and BigQuery Data Editor on the already-created dataset. The owner of a personal sandbox project normally already has the required access.

### Option B: service account

1. Open **IAM & Admin > Service accounts > Create service account** in your project. Name it `energy-analytics-dbt`.
2. Grant **BigQuery Job User** on the project. On the `energy_analytics` dataset's **Sharing > Permissions**, grant this service account **BigQuery Data Editor**.
3. If your organization permits service account keys, open the account's **Keys** tab and create a JSON key yourself. Save it outside the repository, for example `C:\Users\YOUR-NAME\gcp-credentials\energy-analytics.json`. If keys are blocked, use option A or your organization's approved method.
4. In PowerShell set:

   ```powershell
   $env:DBT_BQ_PROJECT = 'YOUR-EXACT-PROJECT-ID'
   $env:DBT_BQ_DATASET = 'energy_analytics'
   $env:DBT_BQ_LOCATION = 'EU'
   $env:DBT_BQ_METHOD = 'service-account'
   $env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\Users\YOUR-NAME\gcp-credentials\energy-analytics.json'
   ```

Use one method at a time. Never commit, upload or screenshot a private key, ADC file or token. The committed profile contains environment-variable lookups, not credential values. `.gitignore` also excludes local credential directories and common key filenames; storing keys outside the repository is the primary safeguard.

## 3. Install the optional adapter separately

The existing `.venv`, `requirements.txt`, DuckDB profile and `data/energy.duckdb` remain the normal local setup. In PowerShell:

```powershell
py -3.12 -m venv .venv-bigquery
.\.venv-bigquery\Scripts\python.exe -m pip install -r requirements-bigquery.txt
$env:DBT_SEND_ANONYMOUS_USAGE_STATS = 'false'
```

On the prepared checkout `.venv-bigquery` may already exist. On Linux/macOS use `.venv-bigquery/bin/` executables. See [dbt's BigQuery configuration](https://docs.getdbt.com/docs/local/connect-data-platform/bigquery-setup) for the authentication fields.

## 4. Check access, load seeds, and build

With the variables from your selected authentication method still set:

```powershell
.\.venv-bigquery\Scripts\dbt.exe debug --profiles-dir . --target bigquery --target-path target/bigquery
.\.venv-bigquery\Scripts\dbt.exe seed --profiles-dir . --target bigquery --full-refresh --target-path target/bigquery
.\.venv-bigquery\Scripts\dbt.exe build --profiles-dir . --target bigquery --full-refresh --target-path target/bigquery
```

`--full-refresh` is intentional for this fixed sandbox sample. It rebuilds only the project relations in the selected dataset. Do not point this demo at a dataset containing unrelated production tables with the same names. The explicit seed command loads all three committed CSV files; build then rebuilds and tests the whole project. No Docker is involved.

Expected, **not yet observed on BigQuery**: 3 seeds, 5 model tables and 44 passing data tests, with `PASS=52` in the complete build summary. The dataset should contain `raw_prices`, `partner_sales`, `commission_rules`, `stg_prices`, `stg_partner_sales`, `int_daily_price_stats`, `mart_monthly_partner_commission` and `mart_monthly_price_report`.

The explicit `--target-path target/bigquery` keeps BigQuery artifacts under `target/bigquery/`, so these cloud commands do not replace the normal DuckDB `target/run_results.json`. Keep this flag on any additional BigQuery commands. The database paths and default target stay unchanged. Return to DuckDB with:

```powershell
.\.venv\Scripts\dbt.exe build --profiles-dir . --target dev
```

## 5. Screenshots and run record

1. Screenshot BigQuery Explorer with your dataset expanded and all eight tables visible. Show the sandbox notice if possible. Save `docs/screenshots/bigquery-dataset.jpg`.
2. Screenshot the terminal showing `target='bigquery'`, the completed model/test counts, and the final build summary. Save `docs/screenshots/bigquery-build.jpg`.
3. Record actual counts, date, any failure and how you fixed it in the README's **Running on BigQuery** result table. Until a real cloud build completes, retain **not yet verified on BigQuery**. If you share the screenshots and run output in this chat, the README can be updated from that evidence. Do not include secrets.
4. Check January P01's `commission_eur` is **65.10**, the statement mart has **10** rows, and the monthly price report has **744** January hours and **696** February hours.

## Differences and failures to report honestly

- BigQuery uses `NUMERIC`, `INT64`, and `ARRAY<INT64>` where DuckDB uses bounded `DECIMAL`, integer types and a list. Prices are still UTC and commission is still rounded to cents. Some average types and their displayed trailing zeros differ. Any actual numeric mismatch is a failure to investigate, not a reason to weaken a test.
- Small dispatch macros handle numeric casts, month formatting/truncation and the cheapest-hour array. The existing two SQL test files and all YAML test definitions are unchanged. A BigQuery-only test wrapper translates the existing calendar generator syntax and leaves its full-outer-join completeness assertions intact.
- A default project name of `not-configured` lets the normal DuckDB profile load without Google variables. Set your actual project before using the BigQuery target.
- `DefaultCredentialsError` usually means ADC login is missing or a service account path is wrong. `Access Denied` requires checking the selected identity's project/dataset roles. Dataset not found or location mismatch requires matching `DBT_BQ_LOCATION` to the dataset. Sandbox limitations, organization policies and API restrictions may still prevent a run. Do not enable billing to work around them for this project.
- The local regression script that intentionally deletes rows from DuckDB is a DuckDB check. Do not run those mutations in the BigQuery sandbox; `dbt build --target bigquery` runs the unchanged non-mutating dbt tests.
- BigQuery is optional and is not run by GitHub Actions. CI continues to use DuckDB only.
