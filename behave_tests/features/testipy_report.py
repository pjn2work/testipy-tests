import os
import traceback

from behave.model import Feature, Scenario, ScenarioOutline, Step, Status
from behave.runner import Context

from behave_tests.features.steps import import_steps_modules, load_module

# Import all testipy methods here
from testipy.configs.enums_data import STATE_SKIPPED, STATE_PASSED, STATE_FAILED, STATE_FAILED_KNOWN_BUG
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import ParseStartArguments
from testipy.engine.models import (
    PackageAttr, SuiteAttr, TestMethodAttr,
    mark_packages_suites_methods_ids,
    show_test_structure
)
from testipy.reporter import SuiteDetails, PackageDetails, TestDetails
from testipy.reporter.report_manager import ReportManager, build_report_manager_with_reporters
from testipy.helpers.data_driven_testing import endTest


ORIGINAL_ENVIRONMENT_PY = "env.py"
BASE_FOLDER = os.path.dirname(__file__)
TESTIPY_ARGS = f"-tf {BASE_FOLDER} -r web -rid 1"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TestipyReporting(metaclass=Singleton):
    tear_up_executed: bool = False
    tear_down_executed: bool = False

    package_before_all_context: list = []
    rm: ReportManager = None

    testipy_selected_tests: dict[str, PackageAttr] = None
    testipy_current_package: PackageDetails = None
    testipy_env_py_module = None
    testipy_env_py_suite: SuiteDetails = None

    def get_env_py_module(self):
        return self.testipy_env_py_module

    def get_env_py_suite(self) -> SuiteDetails:
        return self.testipy_env_py_suite

    def get_selected_tests(self) -> dict[str, PackageAttr]:
        return self.testipy_selected_tests

    def get_current_package(self) -> PackageDetails:
        return self.testipy_current_package

    @staticmethod
    def get_current_suite(context: Context) -> SuiteDetails:
        return context.testipy_current_suite

    @staticmethod
    def get_current_test(context: Context) -> TestDetails:
        return context.testipy_current_test

    def test_step(self, context: Context, description: str, reason_of_state: str = "ok", take_screenshot: bool = False, exc_value: BaseException = None, td: TestDetails = None):
        get_rm().test_step(
            current_test=td or self.get_current_test(context),
            state=STATE_FAILED if exc_value else STATE_PASSED,
            reason_of_state=str(exc_value) if exc_value else reason_of_state,
            take_screenshot=take_screenshot,
            description=description,
            exc_value=exc_value
        )

    def test_info(self, context: Context, info: str, level: str = "DEBUG", attachment: dict = None, td: TestDetails = None):
        get_rm().test_info(
            current_test=td or self.get_current_test(context),
            info=info,
            level=level,
            attachment=attachment
        )


_testipy_reporting = TestipyReporting()


class TestipyStep():
    def __init__(self, context: Context, description: str, reason_of_state: str = "ok", td: TestDetails = None):
        self.context: Context = context
        self.description: str = description
        self.reason_of_state: str = reason_of_state
        self.td: TestDetails = td or _testipy_reporting.get_current_test(self.context)

    def __enter__(self):
        get_rm().show_status(f"Executing step {self.description}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        get_rm().test_step(
            current_test=self.td,
            state=STATE_FAILED if exc_val else STATE_PASSED,
            reason_of_state=str(exc_val) if exc_val else self.reason_of_state,
            description=self.description,
            exc_value=exc_val
        )
        if exc_val:
            get_rm().test_info(
                current_test=self.td,
                info=traceback.format_exc(),
                level="ERROR",
            )
            raise exc_val


def get_rm(testipy_init_args: str = None) -> ReportManager:
    if _testipy_reporting.rm is None:
        if testipy_init_args is None:
            testipy_init_args = TESTIPY_ARGS
        ap = ArgsParser.from_str(testipy_init_args)
        sa = ParseStartArguments(ap).get_start_arguments()

        _testipy_reporting.rm = build_report_manager_with_reporters(ap, sa)
    return _testipy_reporting.rm


def get_package_and_suite_by_filename(feature: Feature) -> tuple[str, str, str]:
    """Split values
    Args:
        filename: str = "behave_tests/features/pkg01/tutorial01.feature"
    Returns:
        Tuple[str, str, str] = (behave_tests.features.pkg01, tutorial01, tutorial01.feature)
    """
    filename = feature.filename

    package_name = str(os.path.dirname(filename).replace(os.path.sep, "."))
    filename = os.path.basename(filename)
    suite_name = feature.name

    return package_name, suite_name, filename


def tear_up(context: Context):
    if _testipy_reporting.tear_up_executed:
        return

    def _create_test_attr(sat: SuiteAttr, test_name: str, scenario, comment: str):
        tma = sat.get_test_method_by_name(test_name)
        if tma is None:
            tma = TestMethodAttr(sat, test_name, comment=comment)
            tma.tags = {str(tag) for tag in scenario.tags if not str(tag).startswith("tc:")}
            tma.method_obj = scenario
            tma.test_number = " ".join([str(tag)[3:] for tag in scenario.tags if str(tag).startswith("tc:")])
        return tma

    def _should_run(
            context: Context, iterator: list[Feature | ScenarioOutline | Scenario]
    ) -> list[Feature | ScenarioOutline | Scenario]:
        return [x for x in iterator if x.should_run(config=context._config)]

    packages: dict[str, PackageAttr] = {}
    _testipy_reporting.testipy_selected_tests = packages

    for feature in _should_run(context, iterator=context._runner.features):
        package_name, suite_name, filename = get_package_and_suite_by_filename(feature)

        pa = packages.get(package_name)
        if pa is None:
            packages[package_name] = pa = PackageAttr(package_name)

        sat = pa.get_suite_by_name(suite_name)
        if sat is None:
            sat = SuiteAttr(pa, filename, suite_name, comment="\n".join(feature.description))
            sat.tags = {str(tag) for tag in feature.tags}
            sat.suite_obj = feature

        for scenario in _should_run(context, iterator=feature.scenarios):
            if isinstance(scenario, ScenarioOutline):
                for example in _should_run(context, iterator=scenario.scenarios):
                    tma = _create_test_attr(sat, example.name, example, comment="\n".join(scenario.description))
            else:
                tma = _create_test_attr(sat, scenario.name, scenario, comment="\n".join(scenario.description))

    mark_packages_suites_methods_ids(list(packages.values()))

    get_rm()._startup_(list(packages.values()))
    _testipy_reporting.tear_up_executed = True

    context.testipy_reporting = _testipy_reporting


def tear_down(context: Context):
    if _testipy_reporting.tear_down_executed:
        return

    pd: PackageDetails = _testipy_reporting.get_current_package()

    _call_env_after_all(context)

    get_rm().end_package(pd)
    get_rm()._teardown_("")

    _testipy_reporting.tear_down_executed = True


def start_feature(context: Context, feature: Feature):
    package_name, suite_name, _ = get_package_and_suite_by_filename(feature)
    tests: dict[str, PackageAttr] = _testipy_reporting.get_selected_tests()
    pat: PackageAttr = tests.get(package_name)
    if pat is None:
        raise ValueError(f"package {package_name} not found!")

    pd: PackageDetails = _testipy_reporting.get_current_package()
    if pd is None:
        _testipy_reporting.testipy_current_package = pd = get_rm().startPackage(pat)
        _call_env_before_all(context, feature)
    elif pd.name != package_name:
        get_rm().end_package(pd)
        _call_env_after_all(context)

        _testipy_reporting.testipy_current_package = pd = get_rm().startPackage(pat)
        _call_env_before_all(context, feature)
    else:
        _load_behave_context(context)
        if context.testipy_env_py_exception:
            raise context.testipy_env_py_exception

    sat: SuiteAttr = pat.get_suite_by_name(suite_name)
    if sat is None:
        raise ValueError(f"suite {suite_name} not found!")

    sd: SuiteDetails = get_rm().startSuite(pd, sat)
    context.testipy_current_suite = sd


def end_feature(context: Context, feature: Feature):
    _close_any_unclosed_tests(context)

    sd: SuiteDetails = _testipy_reporting.get_current_suite(context)
    get_rm().end_suite(sd)

    context.testipy_current_suite = None


def start_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    sd: SuiteDetails = _testipy_reporting.get_current_suite(context)
    tma: TestMethodAttr = sd.suite_attr.get_test_method_by_name(scenario.name)
    if tma is None:
        raise ValueError(f"scenario {scenario.name} not found!")

    names = tma.name.split(" -- ")
    if len(names) == 2:
        test_name, usecase_name = names
    else:
        test_name, usecase_name = tma.name, ""

    td: TestDetails = get_rm().startTest(sd.set_current_test_method_attr(tma), test_name=test_name, usecase=usecase_name)
    context.testipy_current_test = td


def end_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    current_test: TestDetails = _testipy_reporting.get_current_test(context)

    _log_messages_to_test(context, current_test)

    endTest(get_rm(), current_test)
    context.testipy_current_test = None

    _close_any_unclosed_tests(context)


def end_step(context: Context, step: Step):
    def _get_status(status: Status | int) -> str:
        _STATUS = {
            0: STATE_SKIPPED,
            1: STATE_SKIPPED,
            2: STATE_PASSED,
            3: STATE_FAILED,
            4: STATE_FAILED,
            5: STATE_FAILED,
        }
        if isinstance(status, int):
            return _STATUS.get(status, STATE_FAILED_KNOWN_BUG)
        if isinstance(status, Status):
            return _STATUS.get(status.value, STATE_FAILED_KNOWN_BUG)
        raise ValueError(f"Unexpected status value: {status}")

    td: TestDetails = _testipy_reporting.get_current_test(context)
    if step.exception:
        info = "".join(traceback.format_tb(step.exc_traceback, limit=-2))
        get_rm().test_info(
            current_test=td,
            info=info,
            level="ERROR"
        )
    get_rm().test_step(
        current_test=td,
        state=_get_status(step.status),
        reason_of_state=str(step.exception) if step.exception else "ok",
        description=f"{step.keyword} {step.name}",
        exc_value=step.exception
    )


def _log_messages_to_test(context: Context, current_test: TestDetails):
    # Access captured output
    stdout_output = context.stdout.getvalue()
    stderr_output = context.stderr.getvalue()
    log_output = context.log_stream.getvalue()

    rm: ReportManager = get_rm()
    if stdout_output:
        rm.test_info(current_test, f"stdout:\n{stdout_output}", level="INFO")
    if stderr_output:
        rm.test_info(current_test, f"stderr:\n{stderr_output}", level="ERROR")
    if log_output:
        rm.test_info(current_test, f"logging:\n{log_output}", level="DEBUG")


def _call_env_before_all(context: Context, feature: Feature):
    context.testipy_env_py_exception = None
    try:
        file_path: str = os.path.dirname(feature.filename)
        env_filename = os.path.join(file_path, ORIGINAL_ENVIRONMENT_PY)
        _load_steps_from_folder(file_path)

        pd: PackageDetails = _testipy_reporting.get_current_package()
        sat: SuiteAttr = _get_suite_attr_by_name(pd.package_attr, ORIGINAL_ENVIRONMENT_PY, ORIGINAL_ENVIRONMENT_PY)
        sd: SuiteDetails = get_rm().startSuite(pd, sat)

        _testipy_reporting.testipy_env_py_suite = context.testipy_current_suite = sd

        _testipy_reporting.testipy_env_py_module = module = load_module(env_filename, raise_on_error=False)
        if module is not None and hasattr(module, "before_all"):
            td = start_independent_test(context, "Before All")
            context.testipy_current_test = td
            try:
                module.before_all(context)
            except Exception as exc:
                get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description=f"{ORIGINAL_ENVIRONMENT_PY} before_all call", exc_value=exc)
                end_independent_test(td)
                _close_any_unclosed_tests(context)
                raise RuntimeError(f"Failed to call {env_filename} before_all.\n{exc}") from exc

            end_independent_test(td)
            _close_any_unclosed_tests(context)

        context.testipy_current_test = None
        _save_behave_context(context)
    except Exception as exc:
        context.testipy_env_py_exception = exc
        _save_behave_context(context)
        raise


def _call_env_after_all(context: Context):
    _load_behave_context(context)
    context.testipy_current_suite = _testipy_reporting.get_env_py_suite()

    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "after_all"):
        td = start_independent_test(context, "After All")
        context.testipy_current_test = td
        try:
            module.after_all(context)
        except Exception as exc:
            get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description=f"{ORIGINAL_ENVIRONMENT_PY} before_all call", exc_value=exc)

        end_independent_test(td)
        _close_any_unclosed_tests(context)

    context.testipy_current_test = None
    get_rm().end_suite(_testipy_reporting.get_env_py_suite())

    _testipy_reporting.testipy_env_py_module = None
    _testipy_reporting.testipy_env_py_suite = None


def _save_behave_context(context: Context):
    _testipy_reporting.package_before_all_context = [frame for frame in context.__dict__["_stack"]]


def _load_behave_context(context: Context):
    context.__dict__["_stack"] = [frame for frame in _testipy_reporting.package_before_all_context]


def start_independent_test(context: Context, test_name: str, usecase: str = "") -> TestDetails:
    sd: SuiteDetails = _testipy_reporting.get_current_suite(context)

    test_attr: TestMethodAttr = _get_test_attr_by_name(sd.suite_attr, test_name)
    td: TestDetails = get_rm().startTest(sd, test_attr, usecase=usecase)

    return td


def end_independent_test(td: TestDetails) -> None:
    endTest(get_rm(), td)


def _close_any_unclosed_tests(context: Context):
    sd: SuiteDetails = _testipy_reporting.get_current_suite(context)
    for tests in sd.test_manager._tests_running_by_meid.values():
        for test in tests:
            endTest(get_rm(), test, end_reason="auto-closed")


def _get_suite_attr_by_name(package_attr: PackageAttr, suite_name: str, suite_filename: str = "") -> SuiteAttr:
    suite_attr: SuiteAttr = package_attr.get_suite_by_name(suite_name)

    if suite_attr is None:
        suite_attr = SuiteAttr(package_attr, suite_filename, suite_name)
        suite_attr.suite_id = package_attr.get_max_suite_id()

    return suite_attr

def _get_test_attr_by_name(suite_attr: SuiteAttr, test_name: str) -> TestMethodAttr:
    test_attr: TestMethodAttr = suite_attr.get_test_method_by_name(test_name)
    if test_attr is None:
        meid = max([package_attr.get_max_test_method_id() for package_attr in _testipy_reporting.get_selected_tests().values()])
        test_attr = TestMethodAttr(suite_attr, test_name)
        test_attr.method_id = meid

    return test_attr


def _load_steps_from_folder(file_path: str):
    import_steps_modules(os.path.join(file_path, "_steps"))
