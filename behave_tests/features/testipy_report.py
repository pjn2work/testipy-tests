import os
import traceback

from dataclasses import dataclass
from typing import Callable

from behave.model import Feature, Scenario, ScenarioOutline, Tag, Step, Status
from behave.runner import Context
from testipy.helpers.handle_assertions import ExpectedError

from behave_tests.features.common import (
    import_steps_modules, load_module, Singleton,
    clear_context_data_bucket, should_run
)

# Import all testipy methods here
from testipy.configs.enums_data import STATE_SKIPPED, STATE_PASSED, STATE_FAILED, STATE_FAILED_KNOWN_BUG
from testipy.configs.default_config import separator_package
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import ParseStartArguments
from testipy.models import PackageAttr, SuiteAttr, TestMethodAttr, SuiteDetails, PackageDetails, TestDetails
from testipy.models.attr import mark_packages_suites_methods_ids, show_test_structure
from testipy.reporter.report_manager import ReportManager, TestStep, build_report_manager_with_reporters
from testipy.helpers.data_driven_testing import endTest


ORIGINAL_ENVIRONMENT_PY = "environment_.py"
ORIGINAL_STEPS_FOLDER = "steps_"
BASE_FOLDER = os.path.dirname(__file__)
TESTIPY_ARGS = f"-tf {BASE_FOLDER} -r web -r-web-port 9204 -rid 1 -r html"
REMOVE_PACKAGE_PREFIX = "behave_tests.features."

class TestipyReporting(metaclass=Singleton):

    @dataclass
    class EnvironmentPy:
        module: Callable = None
        folder_path: str = ""
        sd: SuiteDetails = None

        def clear(self):
            self.module = None
            self.folder_path = ""
            self.sd = None

    tear_up_executed: bool = False
    tear_down_executed: bool = False

    package_before_all_context: list = []
    rm: ReportManager = None
    loaded_steps_folders: set = set()

    testipy_selected_tests: dict[str, PackageAttr] = None
    testipy_started_packages: dict[str, PackageDetails] = {}
    testipy_current_package: PackageDetails = None
    testipy_env_py = EnvironmentPy()

    def get_env_py_module(self) -> Callable:
        return self.testipy_env_py.module

    def get_env_py_suite(self) -> SuiteDetails:
        return self.testipy_env_py.sd

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

    def test_info(self, context: Context, info: str, level: str = "DEBUG", attachment: dict = None, td: TestDetails = None, true_html = False):
        get_rm().test_info(
            current_test=td or self.get_current_test(context),
            info=info,
            level=level,
            attachment=attachment,
            true_html=true_html
        )

    def start_new_package(self, package_name: str, /, *, raise_if_not_found: bool) -> PackageDetails:
        if package_name in self.testipy_started_packages:
            pd = self.testipy_started_packages[package_name]
        else:
            pd = self.get_current_package()
            if pd and pd.name != package_name:
                self.end_package(pd)

            pat: PackageAttr = _testipy_reporting.get_selected_tests().get(package_name)
            if pat is None:
                if raise_if_not_found:
                    raise ValueError(f"package {package_name} not found!")
                pat = PackageAttr(package_name)
            self.testipy_started_packages[package_name] = pd = get_rm().startPackage(pat)

        self.testipy_current_package = pd
        return self.get_current_package()

    def end_package(self, pd: PackageDetails):
        if pd is not None and pd.get_endtime() is None:
            get_rm().end_package(pd)


_testipy_reporting = TestipyReporting()


def test_info(context: Context, info: str, level: str = "DEBUG", attachment: dict = None, td: TestDetails = None, true_html: bool = False):
    _testipy_reporting.test_info(
        context=context,
        info=info,
        level=level,
        attachment=attachment,
        td=td,
        true_html=true_html
    )


def test_step(context: Context, description: str, reason_of_state: str = "ok", take_screenshot: bool = False, exc_value: BaseException = None, td: TestDetails = None):
    _testipy_reporting.test_step(
        context=context,
        description=description,
        reason_of_state=reason_of_state,
        take_screenshot=take_screenshot,
        exc_value=exc_value,
        td=td
    )


def set_feature_step_reason_of_state(context: Context, reason_of_state: str):
    context.testipy_reason_of_state = reason_of_state


class TestipyStep(TestStep):
    def __init__(self, context: Context, description: str, reason_of_state: str = "ok", take_screenshot: bool = False, td: TestDetails = None):
        td = td or _testipy_reporting.get_current_test(context)
        if td is None:
            raise ValueError(f"Cannot execute step without TestDetails")
        super(TestipyStep, self).__init__(td, description, reason_of_state, take_screenshot=take_screenshot)


def get_rm(testipy_init_args: str = None) -> ReportManager:
    if _testipy_reporting.rm is None:
        if testipy_init_args:
            testipy_init_args = f"-tf {BASE_FOLDER} {testipy_init_args}"
        else:
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

    package_name = str(os.path.dirname(filename).replace(os.path.sep, separator_package)).removeprefix(REMOVE_PACKAGE_PREFIX)
    filename = os.path.basename(filename)
    suite_name = feature.name

    return package_name, suite_name, filename


def tear_up(context: Context):
    if _testipy_reporting.tear_up_executed:
        return

    get_rm(context.config.userdata.get("testipy"))

    def _create_test_attr(sat: SuiteAttr, test_name: str, scenario, comment: str):
        tma = sat.get_test_method_by_name(test_name)
        if tma is None:
            tma = TestMethodAttr(sat, test_name, comment=comment)
            tma.tags = {str(tag) for tag in scenario.tags if not str(tag).startswith("tc:")}
            tma.method_obj = scenario
            tma.test_number = " ".join([str(tag)[3:] for tag in scenario.tags if str(tag).startswith("tc:")])
        return tma

    packages: dict[str, PackageAttr] = {}
    _testipy_reporting.testipy_selected_tests = packages

    for feature in should_run(context, iterator=context._runner.features):
        package_name, suite_name, filename = get_package_and_suite_by_filename(feature)

        pat = packages.get(package_name)
        if pat is None:
            packages[package_name] = pat = PackageAttr(package_name)

        sat = pat.get_suite_by_name(suite_name)
        if sat is None:
            sat = SuiteAttr(pat, filename, suite_name, comment="\n".join(feature.description))
            sat.tags = {str(tag) for tag in feature.tags}
            sat.suite_obj = feature

        for scenario in should_run(context, iterator=feature.scenarios):
            if isinstance(scenario, ScenarioOutline):
                for example in should_run(context, iterator=scenario.scenarios):
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

    _call_env_after_all(context)

    _testipy_reporting.end_package(_testipy_reporting.get_current_package())
    get_rm()._teardown_("")

    _testipy_reporting.tear_down_executed = True


def start_tag(context: Context, tag: Tag):
    _call_env_before_tag(context, tag)


def end_tag(context: Context, tag: Tag):
    _call_env_after_tag(context, tag)


def __get_package_for_feature(context: Context, feature: Feature, feature_package_name: str) -> PackageDetails:
    feature_folder_path = os.path.dirname(feature.filename)
    env_folder_path = _get_env_folder_path(feature_folder_path)
    is_new_env = env_folder_path != _testipy_reporting.testipy_env_py.folder_path or _testipy_reporting.get_current_package() is None
    is_same_folder_feature_vs_env = feature_folder_path == env_folder_path

    pd: PackageDetails = _testipy_reporting.start_new_package(feature_package_name, raise_if_not_found=True)

    if is_new_env:
        _call_env_after_all(context)
        _call_env_before_all(context, env_folder_path)
    else:
        _load_behave_context(context)

    if not is_same_folder_feature_vs_env:
        _load_steps_from_folder(feature_folder_path)

    return pd


def start_feature(context: Context, feature: Feature):
    feature_package_name, suite_name, _ = get_package_and_suite_by_filename(feature)
    _testipy_reporting.testipy_current_package = pd = __get_package_for_feature(context, feature, feature_package_name)

    sat: SuiteAttr = pd.package_attr.get_suite_by_name(suite_name)
    if sat is None:
        raise ValueError(f"suite {suite_name} not found!")

    context.testipy_current_suite = get_rm().startSuite(pd, sat)

    if context.testipy_env_py_exception is None:
        _call_env_before_feature(context, feature)


def end_feature(context: Context, feature: Feature):
    _close_any_unclosed_tests(context)

    if context.testipy_env_py_exception is None:
        _call_env_after_feature(context, feature)

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

    if context.testipy_env_py_exception is None:
        _call_env_before_scenario(context, scenario)
    else:
        raise context.testipy_env_py_exception


def end_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    if context.testipy_env_py_exception is None:
        _call_env_after_scenario(context, scenario)

    current_test: TestDetails = _testipy_reporting.get_current_test(context)

    _log_messages_to_test(context, current_test)
    if current_test.get_test_step_counters().get_last_state():
        endTest(get_rm(), current_test)
    else:
        status = _get_status(scenario.status)
        reason_of_state = "ok" if status == STATE_PASSED else scenario.error_message
        current_test.rm.end_test(current_test, status, reason_of_state, scenario.exception)
    context.testipy_current_test = None

    _close_any_unclosed_tests(context)


def start_step(context: Context, step: Step):
    set_feature_step_reason_of_state(context, "ok")


def end_step(context: Context, step: Step):
    td: TestDetails = _testipy_reporting.get_current_test(context)
    if step.exception:
        if isinstance(step.exception, ExpectedError):
            reason_of_state = str(step.exception)
            step.status = Status.passed
            step.exception = None
            step.exc_traceback = None
        else:
            reason_of_state = str(step.exception)
            info = f"{type(step.exception)} {reason_of_state}\n" + "".join(traceback.format_tb(step.exc_traceback, limit=-2))
            get_rm().test_info(
                current_test=td,
                info=f"{step.keyword} {step.name}\n{info}",
                level="ERROR"
            )
    else:
        reason_of_state = context.testipy_reason_of_state
    get_rm().test_step(
        current_test=td,
        state=_get_status(step.status),
        reason_of_state=reason_of_state,
        description=f"{step.keyword} {step.name}",
        exc_value=step.exception
    )


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


def _log_messages_to_test(context: Context, current_test: TestDetails):
    # Access captured output
    stdout_output = context.stdout.getvalue()
    stderr_output = context.stderr.getvalue()
    # log_output = context.log_stream.getvalue()

    rm: ReportManager = get_rm()
    if stdout_output:
        rm.test_info(current_test, f"stdout:\n{stdout_output}", level="INFO")
    if stderr_output:
        rm.test_info(current_test, f"stderr:\n{stderr_output}", level="ERROR")
    # if log_output:
    #     rm.test_info(current_test, f"logging:\n{log_output}", level="DEBUG")


def _get_env_folder_path(folder_path: str) -> str:
    while folder_path:
        if BASE_FOLDER.endswith(folder_path):
            return ""
        env_filename = os.path.join(folder_path, ORIGINAL_ENVIRONMENT_PY)
        if os.path.exists(env_filename):
            return folder_path
        folder_path = os.path.dirname(folder_path)
    return ""


def _call_env_before_all(context: Context, env_folder_path: str):
    clear_context_data_bucket(context)
    context.testipy_env_py_exception = None
    _testipy_reporting.testipy_env_py.folder_path = env_folder_path
    env_package_name = env_folder_path.replace(os.path.sep, separator_package)

    if env_folder_path:
        try:
            pd: PackageDetails = _testipy_reporting.start_new_package(env_package_name, raise_if_not_found=False)
            sat: SuiteAttr = _get_suite_attr_by_name(pd.package_attr, ORIGINAL_ENVIRONMENT_PY, ORIGINAL_ENVIRONMENT_PY)
            sd: SuiteDetails = get_rm().startSuite(pd, sat)

            _testipy_reporting.testipy_env_py.sd = context.testipy_current_suite = sd

            _load_steps_from_folder(env_folder_path)

            env_filename = os.path.join(env_folder_path, ORIGINAL_ENVIRONMENT_PY)
            _testipy_reporting.testipy_env_py.module = module = load_module(env_filename, raise_on_error=False)
            if module is not None and hasattr(module, "before_all"):
                td = start_independent_test(context, "before_all")
                context.testipy_current_test = td
                try:
                    module.before_all(context)
                except Exception as exc:
                    get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description=f"{ORIGINAL_ENVIRONMENT_PY} before_all call", exc_value=exc)
                    end_independent_test(td)
                    _close_any_unclosed_tests(context)
                    raise RuntimeError(f"Failed to call {env_folder_path}/{ORIGINAL_ENVIRONMENT_PY} before_all.\n{exc}") from exc

                end_independent_test(td)
                _close_any_unclosed_tests(context)

            context.testipy_current_test = None
            _save_behave_context(context)
        except Exception as exc:
            context.testipy_env_py_exception = exc
            _save_behave_context(context)
            raise
    else:
        _save_behave_context(context)


def _call_env_after_all(context: Context):
    sd = _testipy_reporting.get_env_py_suite()
    if sd is None:
        return

    _load_behave_context(context)
    context.testipy_current_suite = sd

    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "after_all"):
        td = start_independent_test(context, "after_all")
        context.testipy_current_test = td
        try:
            module.after_all(context)
        except Exception as exc:
            get_rm().test_step(td, state=STATE_FAILED, reason_of_state=str(exc), description=f"{ORIGINAL_ENVIRONMENT_PY} before_all call", exc_value=exc)

        end_independent_test(td)
        _close_any_unclosed_tests(context)

    context.testipy_current_test = None
    get_rm().end_suite(sd)
    _testipy_reporting.end_package(sd.package)
    _testipy_reporting.testipy_env_py.clear()


def _call_env_before_feature(context: Context, feature: Feature):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "before_feature"):
        td = start_independent_test(context, "before_feature")
        context.testipy_current_test = td

        with TestipyStep(context, "before_feature"):
            module.before_feature(context, feature)

        end_independent_test(td)
        _close_any_unclosed_tests(context)
        context.testipy_current_test = None


def _call_env_after_feature(context: Context, feature: Feature):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "after_feature"):
        td = start_independent_test(context, "after_feature")
        context.testipy_current_test = td

        with TestipyStep(context, "after_feature"):
            module.after_feature(context, feature)

        end_independent_test(td)
        _close_any_unclosed_tests(context)
        context.testipy_current_test = None


def _call_env_before_scenario(context: Context, scenario: Scenario):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "before_scenario"):
        with TestipyStep(context, "before_scenario"):
            module.before_scenario(context, scenario)


def _call_env_after_scenario(context: Context, scenario: Scenario):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "after_scenario"):
        with TestipyStep(context, "after_scenario"):
            module.after_scenario(context, scenario)


def _call_env_before_tag(context: Context, tag: Tag):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "before_tag"):
        module.before_tag(context, tag)


def _call_env_after_tag(context: Context, tag: Tag):
    module = _testipy_reporting.get_env_py_module()
    if module is not None and hasattr(module, "after_tag"):
        module.after_tag(context, tag)


def _save_behave_context(context: Context):
    _testipy_reporting.package_before_all_context = list(context.__dict__["_stack"])


def _load_behave_context(context: Context):
    if _testipy_reporting.package_before_all_context:
        context.__dict__["_stack"] = list(_testipy_reporting.package_before_all_context)


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


def _load_steps_from_folder(folder_path: str):
    if folder_path not in _testipy_reporting.loaded_steps_folders:
        _testipy_reporting.loaded_steps_folders.add(folder_path)
        import_steps_modules(os.path.join(folder_path, ORIGINAL_STEPS_FOLDER))
