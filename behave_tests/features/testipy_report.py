import os
import importlib.util

from behave.model import Feature, Scenario, ScenarioOutline, Step, Status
from behave.runner import Context

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


BASE_FOLDER = os.path.dirname(__file__)
TESTIPY_ARGS = f"-tf {BASE_FOLDER} -r junit -r excel -r log -r web -rid 1"


class TestipyContext:
    tear_up_executed: bool = False
    tear_down_executed: bool = False

    rm: ReportManager = None

    testipy_selected_tests: dict[str, PackageAttr] = None
    testipy_current_package: PackageDetails = None
    testipy_env_py = None
    testipy_env_py_suite: SuiteDetails = None

    def get_env_py_module(self):
        return self.testipy_env_py

    def get_env_py_suite(self) -> SuiteDetails:
        return self.testipy_env_py_suite

    def get_selected_tests(self) -> dict[str, PackageAttr]:
        return self.testipy_selected_tests

    def get_current_package(self) -> PackageDetails:
        return self.testipy_current_package

    def get_current_suite(self, context: Context) -> SuiteDetails:
        return context.testipy_current_suite

    def get_current_test(self, context: Context) -> TestDetails:
        return context.testipy_current_test

    def get_current_independent_test(self, context: Context) -> TestDetails:
        return context.testipy_independent_test

_testipy_context = TestipyContext()


def get_rm(testipy_init_args: str = TESTIPY_ARGS) -> ReportManager:
    if _testipy_context.rm is None:
        ap = ArgsParser.from_str(testipy_init_args)
        sa = ParseStartArguments(ap).get_start_arguments()

        _testipy_context.rm = build_report_manager_with_reporters(ap, sa)
    return _testipy_context.rm


def get_package_and_suite_by_filename(filename: str) -> tuple[str, str, str]:
    """Split values
    Args:
        filename: str = "behave_tests/features/pkg01/tutorial01.feature"
    Returns:
        Tuple[str, str, str] = (behave_tests.features.pkg01, tutorial01, tutorial01.feature)
    """
    package_name = str(os.path.dirname(filename).replace("/", "."))
    filename = os.path.basename(filename)
    suite_name = os.path.splitext(filename)[0]
    return package_name, suite_name, filename


def tear_up(context: Context):
    if _testipy_context.tear_up_executed:
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
    _testipy_context.testipy_selected_tests = packages

    for feature in _should_run(context, iterator=context._runner.features):
        package_name, suite_name, filename = get_package_and_suite_by_filename(feature.filename)

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
    _testipy_context.tear_up_executed = True

    context.testipy_context = _testipy_context


def tear_down(context: Context):
    if _testipy_context.tear_down_executed:
        return

    _call_env_after_all(context)

    get_rm().end_package(_testipy_context.get_current_package())
    get_rm()._teardown_("")

    _testipy_context.tear_down_executed = True


def start_feature(context: Context, feature: Feature):
    package_name, suite_name, _ = get_package_and_suite_by_filename(feature.filename)

    tests: dict[str, PackageAttr] = _testipy_context.get_selected_tests()
    pat: PackageAttr = tests.get(package_name)
    if pat is None:
        raise ValueError(f"package {package_name} not found!")

    pd: PackageDetails = _testipy_context.get_current_package()
    if pd is None:
        _testipy_context.testipy_current_package = pd = get_rm().startPackage(pat)
        _call_env_before_all(context, os.path.dirname(feature.filename))
    elif pd.name != package_name:
        get_rm().end_package(pd)
        _call_env_after_all(context)

        _testipy_context.testipy_current_package = pd = get_rm().startPackage(pat)
        _call_env_before_all(context, os.path.dirname(feature.filename))

    sat: SuiteAttr = pat.get_suite_by_name(suite_name)
    if sat is None:
        raise ValueError(f"suite {suite_name} not found!")

    sd: SuiteDetails = get_rm().startSuite(pd, sat)
    context.testipy_current_suite = sd


def end_feature(context: Context, feature: Feature):
    sd: SuiteDetails = _testipy_context.get_current_suite(context)
    get_rm().end_suite(sd)
    context.testipy_current_suite = None


def start_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    sd: SuiteDetails = _testipy_context.get_current_suite(context)
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
    current_test: TestDetails = _testipy_context.get_current_test(context)

    _log_messages_to_test(context, current_test)

    endTest(get_rm(), current_test)
    context.testipy_current_test = None


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

    get_rm().test_step(
        current_test=_testipy_context.get_current_test(context),
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


def _call_env_before_all(context: Context, file_path: str):
    file_name = "env.py"
    file_path = os.path.join(file_path, file_name)

    pd: PackageDetails = _testipy_context.get_current_package()
    sat: SuiteAttr = _get_suite_attr_by_name(pd.package_attr, "package_setup", file_name)
    sd: SuiteDetails = get_rm().startSuite(pd, sat)

    _testipy_context.testipy_env_py_suite = context.testipy_current_suite = sd

    _testipy_context.testipy_env_py = module = load_module(file_path, raise_on_error=False)
    if module is not None and hasattr(module, "before_all"):
        td = start_independent_test(context, test_name="Before All")
        try:
            module.before_all(context, get_rm(), td)
            end_independent_test(context)
        except Exception as exc:
            get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description=f"{file_name} before_all call", exc_value=exc)
            end_independent_test(context)
            raise RuntimeError(f"Failed to call {file_path} before_all.\n{exc}") from exc


def _call_env_after_all(context: Context):
    context.testipy_current_suite = _testipy_context.get_env_py_suite()

    module = _testipy_context.get_env_py_module()
    if module is not None and hasattr(module, "after_all"):
        td = start_independent_test(context, test_name="After All")
        try:
            module.after_all(context, get_rm(), td)
        except Exception as exc:
            get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description="env.py before_all call", exc_value=exc)
        end_independent_test(context)

    get_rm().end_suite(_testipy_context.get_env_py_suite())

    _testipy_context.testipy_env_py = None
    _testipy_context.testipy_env_py_suite = None


def start_independent_test(context: Context, test_name: str, usecase: str = "") -> TestDetails:
    sd: SuiteDetails = _testipy_context.get_current_suite(context)

    test_attr: TestMethodAttr = _get_test_attr_by_name(sd.suite_attr, test_name)
    td: TestDetails = get_rm().startTest(sd, test_attr, usecase=usecase)

    context.testipy_independent_test = td

    return td


def end_independent_test(context: Context) -> None:
    endTest(get_rm(), _testipy_context.get_current_independent_test(context))

    context.testipy_independent_test = None


def _get_suite_attr_by_name(package_attr: PackageAttr, suite_name: str, suite_filename: str = "") -> SuiteAttr:
    suite_attr: SuiteAttr = package_attr.get_suite_by_name(suite_name)

    if suite_attr is None:
        suite_attr = SuiteAttr(package_attr, suite_filename, suite_name)
        suite_attr.suite_id = package_attr.get_max_suite_id()

    return suite_attr

def _get_test_attr_by_name(suite_attr: SuiteAttr, test_name: str) -> TestMethodAttr:
    test_attr: TestMethodAttr = suite_attr.get_test_method_by_name(test_name)
    if test_attr is None:
        meid = max([package_attr.get_max_test_method_id() for package_attr in _testipy_context.get_selected_tests().values()])
        test_attr = TestMethodAttr(suite_attr, test_name)
        test_attr.method_id = meid

    return test_attr


def load_module(file_path: str, raise_on_error: bool = True) -> object:
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        if module_name != '__init__':
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as exc:
        if raise_on_error:
            raise exc
    return None
