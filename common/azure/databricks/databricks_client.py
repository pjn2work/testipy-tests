from datetime import datetime, timezone
from functools import lru_cache
from logging import RootLogger
from time import sleep
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import BaseRun, Run, RunLifeCycleState, RunTask
from polling import TimeoutException, poll

from .databricks_token_provider import DatabricksTokenProvider


API_VERSION = "2.1"

JOB_COMPLETE_TIMEOUT = 30 * 60
JOB_START_TIMEOUT = 1 * 60
JOB_POLL_TIME = 1 * 60
JOB_QUEUE_TIMEOUT = 20 * 60
JOB_NAME = "current_job"
CURRENT_JOB_COMPLETE_TIMEOUT = 30 * 60


class JobRunnerError(Exception):
    pass


class JobQueuerResult:
    def __init__(self) -> None:
        self.successful: dict[str, str] = {}
        self.failed: dict[str, JobRunnerError] = {}
        self.all_successful = True

    def add_success(self, key: str, job_id: str) -> None:
        self.successful[key] = job_id

    def add_failed(self, key: str, job_runner_exception: JobRunnerError) -> None:
        self.failed[key] = job_runner_exception
        self.all_successful = False


class DatabricksClient:
    def __init__(
        self,
        server_hostname: str,
        databricks_token_provider: DatabricksTokenProvider,
        default_cluster_id: str | None = None,
        job_complete_time_out: int = JOB_COMPLETE_TIMEOUT,
    ):
        self.databricks_hostname: str = server_hostname
        self.databricks_token_provider: DatabricksTokenProvider = (
            databricks_token_provider
        )
        self.token_value: str = self.databricks_token_provider.get_token()

        self.client: WorkspaceClient | None = None
        self._job_ids = self._get_job_ids()
        self._default_cluster_id = default_cluster_id
        self.job_complete_time_out = job_complete_time_out

    def _get_databricks_client(self) -> WorkspaceClient:
        if self.client is None or self.databricks_token_provider.is_expiring():
            self.token_value = self.databricks_token_provider.get_token()
            self.client = WorkspaceClient(
                host=self.databricks_hostname, token=self.token_value
            )

        return self.client

    def _get_job_ids(self) -> dict[str, int]:
        """Gets job list from Databricks and returns a dict of names and ids."""

        all_jobs = self._get_databricks_client().jobs.list()

        return {job.settings.name: job.job_id for job in all_jobs}

    def get_job_id(self, job_name: str) -> int:
        """Gets the id of a job from the name."""

        return self._job_ids[job_name]

    @classmethod
    def run_state(cls, run: BaseRun | Run | RunTask) -> str:
        return (
            run.state.result_state.value
            if run.state.result_state is not None
            else run.state.life_cycle_state.value
        )

    def get_runs(self, job_name: str, active_only: bool = False) -> list[BaseRun]:
        """Gets a list of runs for a given job name.

        Runs are sorted in descending order by start time.
        """

        job_id = self.get_job_id(job_name)
        result = self._get_databricks_client().jobs.list_runs(
            job_id=job_id,
            active_only=active_only,
            completed_only=False,
        )
        return list(result)

    def _get_initial_run_state(
        self, run_id: str | int, timeout: int = JOB_START_TIMEOUT
    ) -> str:
        """Wait for a job run state to progress from 'QUEUED' or 'PENDING' and return the new run state.

        Raises a `TimeoutException` if the run state is still pending after `timeout` seconds.
        """

        try:
            poll(
                lambda: self._get_databricks_client()
                .jobs.get_run(run_id)
                .state.life_cycle_state
                not in {RunLifeCycleState.QUEUED, RunLifeCycleState.PENDING},
                step=1,
                timeout=timeout,
            )
            resp = self._get_databricks_client().jobs.get_run(run_id)
            return DatabricksClient.run_state(resp)

        except TimeoutException as te:
            raise TimeoutException(
                f"Poll for job run ID '{run_id}' timed out - job run still pending."
            ) from te

    def wait_for_run_complete(self, run_id: str | int) -> str:
        """Poll for job run completion and return job result state.

        Raises a TimeoutException if the poll times out.
        """

        try:
            poll(
                lambda: self._get_databricks_client()
                .jobs.get_run(run_id)
                .state.life_cycle_state
                not in {
                    RunLifeCycleState.RUNNING,
                    RunLifeCycleState.QUEUED,
                    RunLifeCycleState.PENDING,
                },
                step=JOB_POLL_TIME,
                timeout=self.job_complete_time_out,
            )
            resp = self._get_databricks_client().jobs.get_run(run_id)
            return DatabricksClient.run_state(resp)

        except TimeoutException as te:
            raise TimeoutException(
                f"Poll for job run ID '{run_id}' timed out - job did not complete within {JOB_COMPLETE_TIMEOUT} seconds."
            ) from te

    def _repair_run(
        self,
        run_id: str | int,
        params: dict[str, Any] | None = None,
        latest_repair_id: str | int | None = None,
    ) -> str | int:
        """Repair a job run, rerunning all the tasks in the workflow.
        Returns the repair ID and the result state of the repaired run
        (or `None` if wait_for_complete is `False`).
        """

        resp = self._get_databricks_client().jobs.get_run(run_id)
        tasks = [task.task_key for task in resp.tasks]
        latest_repair_run = (
            self._get_databricks_client()
            .jobs.repair_run(
                run_id,
                rerun_tasks=tasks,
                notebook_params=params,
            )
            .response
        )

        return latest_repair_run.repair_id

    def _queue_skipped_run(
        self,
        job_name: str,
        params: dict[str, Any] | None,
        run_id: str | int,
        max_concurrent_runs: int = 1,
    ):
        """If the job run has been skipped, queue until the number of running instances
        of the given job is less than the maximum number of concurrent runs for that job.

        Returns the latest repair ID of the job run.
        """

        try:
            poll(
                lambda: len(
                    [
                        run
                        for run in self.get_runs(job_name)
                        if DatabricksClient.run_state(run)
                        in {
                            RunLifeCycleState.PENDING.value,
                            RunLifeCycleState.RUNNING.value,
                        }
                    ]
                )
                < max_concurrent_runs,
                step=JOB_POLL_TIME,
                timeout=JOB_QUEUE_TIMEOUT,
            )
            return self._repair_run(run_id, params)

        except TimeoutException as te:
            raise TimeoutException(
                f"Failed to start {job_name} job - current runs did not complete within "
                f"{JOB_COMPLETE_TIMEOUT} seconds."
            ) from te

    def run_job(
        self,
        job_name: str,
        params: dict[str, Any] | list[dict[str, Any]] | None = None,
        max_concurrent_runs: int = 1,
        wait_for_job_to_complete: bool = True,
    ) -> tuple[str | int, str]:
        """Run job and wait for completion, returning job run result state.

        If multiple job run parameters are provided, run a job for each.
        Each run will be queued if the initial result is 'SKIPPED' and the
        function will only return when all runs have completed.

        Returns a tuple containing job run IDs and corresponding result states,
        or a list of tuples if the provided `params` is a list.
        """

        multiple_runs = isinstance(params, list)
        ls_params = params if multiple_runs else [params]
        job_id = self.get_job_id(job_name)

        ls_run_id = []
        for params in ls_params:
            resp = (
                self._get_databricks_client()
                .jobs.run_now(job_id, notebook_params=params)
                .response
            )
            ls_run_id.append(resp.run_id)

        # Necessary because skipped runs initially show as 'RUNNING'
        sleep(30)

        for run_id, params in zip(ls_run_id, ls_params, strict=True):
            if self._get_initial_run_state(run_id) == "SKIPPED":
                self._queue_skipped_run(job_name, params, run_id, max_concurrent_runs)

        runs = []
        if wait_for_job_to_complete:
            for run_id in ls_run_id:
                result = self.wait_for_run_complete(run_id)
                runs.append((run_id, result))
        else:
            for run_id in ls_run_id:
                resp = self._get_databricks_client().jobs.get_run(run_id)
                result = DatabricksClient.run_state(resp)
                runs.append((run_id, result))

        return runs if multiple_runs else runs[0]

    def get_task_run_result(self, run_id: str | int, task_name: str) -> str:
        """Returns task result state for a given task name and job run id."""

        resp = self._get_databricks_client().jobs.get_run(run_id, include_history=True)

        # Check task name exists for the job
        task_names = []
        for task in resp.tasks:
            task_names.append(task.task_key)
        assert task_name in task_names

        latest_task_run = next(
            task for task in reversed(resp.tasks) if task.task_key == task_name
        )
        return DatabricksClient.run_state(latest_task_run)

    def get_job_tasks_by_run_id(
        self,
        job_run_id: str | int,
        filter_by_name: str = None,
        filter_by_state: str = None,
    ) -> list[RunTask] | None:
        tasks = reversed(self.client.jobs.get_run(job_run_id).tasks)
        tasks = [
            task
            for task in tasks
            if (not filter_by_name or task.task_key == filter_by_name)
            and (not filter_by_state or task.state.result_state.value == filter_by_state)
        ]
        return tasks

    def get_latest_job_run_where_substring_in_params(
        self,
        job_name: str,
        substring: str,
        job_name_prefix: str = "",
        wait_for_complete: bool = True,
    ) -> str | None:
        """Gets latest run of a job with a parameter value containing `substring`.

        Locate latest job run for a given job name where a substring is present
        in the job parameters and wait for the job to complete, returning job
        run result state (default), or return run_id if wait_for_complete.
        Returns None if no runs are found with the given substring.
        """

        job_runs = self.get_runs(job_name=job_name_prefix + job_name)
        filtered_runs = [
            run
            for run in job_runs
            if run.overriding_parameters and run.overriding_parameters.notebook_params
        ]
        run_id = next(
            (
                run.run_id
                for run in filtered_runs
                if any(
                    substring in parameter_value
                    for parameter_value in run.overriding_parameters.notebook_params.values()
                )
            ),
            None,
        )
        return (
            self.wait_for_run_complete(run_id)
            if (wait_for_complete and run_id)
            else run_id
        )

    def get_current_run_for_correlation_id(
        self,
        correlation_id: str,
        job_name_prefix: str = "",
        logger: RootLogger | None = None,
        poll_msg: str | None = None,
    ) -> BaseRun | None:
        """Gets a run of the current job for a given correlation id.

        Returns `None` if no job run is found for the correlation id.
        """

        if logger is not None and poll_msg is not None:
            logger.info(
                f"{poll_msg} at {datetime.now(timezone.utc).strftime('%H:%M:%S')}"
            )

        return next(
            (
                job_run
                for job_run in self.get_runs(job_name=job_name_prefix + JOB_NAME)
                if correlation_id
                == job_run.overriding_parameters.notebook_params.get("CorrelationId")
            ),
            None,
        )

    def wait_for_current_job_to_start(
        self, correlation_id: str, job_name_prefix: str = ""
    ):
        """Waits for the current job for a given correlation id to start."""

        poll(
            lambda: self.get_current_run_for_correlation_id(
                correlation_id, job_name_prefix=job_name_prefix
            ),
            step=JOB_POLL_TIME,
            timeout=CURRENT_JOB_COMPLETE_TIMEOUT,
        )

    @staticmethod
    def _contains_running_job(job_runs: list[BaseRun]) -> bool:
        for job_run in job_runs:
            job_name = job_run.run_name or ""
            if job_run.state.life_cycle_state == RunLifeCycleState.RUNNING:
                print(f"Ongoing [{job_name}] job. Will wait")
                return True
        return False

    def wait_for_jobs_to_start(self, job_name: str):
        try:
            # Wait for the job to start running
            poll(
                lambda: self._contains_running_job(
                    job_runs=self.get_runs(job_name=job_name)
                ),
                step=JOB_POLL_TIME,
                timeout=JOB_START_TIMEOUT,
            )

        except TimeoutException as te:
            raise TimeoutException(
                f"Poll for {job_name} job timed out - job did not complete within {JOB_START_TIMEOUT} seconds."
            ) from te

    def wait_for_jobs_to_complete(self, job_name: str):
        try:
            poll(
                lambda: self._contains_running_job(
                    job_runs=self.get_runs(job_name=job_name)
                )
                is False,
                step=JOB_POLL_TIME,
                timeout=JOB_COMPLETE_TIMEOUT,
            )

        except TimeoutException as te:
            raise TimeoutException(
                f"Poll for {job_name} job timed out - job did not complete within {JOB_COMPLETE_TIMEOUT} seconds."
            ) from te

    @lru_cache()  # noqa: B019
    def get_result_of_job_run_with_param(
        self,
        job_name: str,
        param_key: str,
        param_value: str,
    ) -> JobQueuerResult:
        """
        returns a JobQueuerResult with result of job run with a specific parameter.
        """

        job_queuer_result = JobQueuerResult()

        run_id = self.get_latest_job_run_where_substring_in_params(
            job_name=job_name,
            substring=param_value,
        )

        if run_id is None:
            job_queuer_result.add_failed(
                key=JOB_NAME,
                job_runner_exception=JobRunnerError(
                    f"{JOB_NAME} job run with '{param_key}': '{param_value}' does not exist"
                ),
            )
            return job_queuer_result

        if run_id == "SUCCESS":
            job_queuer_result.add_success(key=JOB_NAME, job_id=run_id)
            return job_queuer_result

        else:
            job_queuer_result.add_failed(
                key=JOB_NAME,
                job_runner_exception=JobRunnerError(
                    f"{JOB_NAME} job run with '{param_key}': '{param_value}' failed"
                ),
            )
            return job_queuer_result
