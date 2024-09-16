import os

from behave.model import Feature, Scenario, ScenarioOutline, Step, Status
from behave.runner import Context

# Import all testipy methods here
from testipy.configs import enums_data
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


_STATUS = {
    0: enums_data.STATE_SKIPPED,
    1: enums_data.STATE_SKIPPED,
    2: enums_data.STATE_PASSED,
    3: enums_data.STATE_FAILED,
    4: enums_data.STATE_FAILED,
    5: enums_data.STATE_FAILED,
}

class TestipyReporter:
    rm: ReportManager = None
    last_package_details: PackageDetails = None
_reporter = TestipyReporter()


def get_rm(testipy_init_args: str = "-r junit -r excel -r log -r web -rid 1") -> ReportManager:
    if _reporter.rm is None:
        ap = ArgsParser.from_str(testipy_init_args)
        sa = ParseStartArguments(ap).get_start_arguments()

        _reporter.rm = build_report_manager_with_reporters(ap, sa)
    return _reporter.rm


def tear_up(context: Context):
    def _create_test_attr(sat: SuiteAttr, test_name: str, scenario):
        tma = sat.get_test_method_by_name(test_name)
        if tma is None:
            tma = TestMethodAttr(sat, test_name)
            tma.tags = scenario.tags
            tma.method_obj = scenario
        return tma

    def _should_run(
            context: Context, iterator: list[Feature | ScenarioOutline | Scenario]
    ) -> list[Feature | ScenarioOutline | Scenario]:
        return [x for x in iterator if x.should_run(config=context._config)]

    packages: dict[str, PackageAttr] = {}

    for feature in _should_run(context, iterator=context._runner.features):
        package_name = str(os.path.dirname(feature.filename).replace("/", "."))
        filename = os.path.basename(feature.filename)
        suite_name = os.path.splitext(filename)[0]

        pa = packages.get(package_name)
        if pa is None:
            packages[package_name] = pa = PackageAttr(package_name)

        sat = pa.get_suite_by_name(suite_name)
        if sat is None:
            sat = SuiteAttr(pa, filename, suite_name)
            sat.tags = feature.tags
            sat.suite_obj = feature

        # print("1>", feature.filename, feature.name, feature.tags)

        for scenario in _should_run(context, iterator=feature.scenarios):
            if isinstance(scenario, ScenarioOutline):
                # print("  2>", scenario, scenario.tags)
                for example in _should_run(context, iterator=scenario.scenarios):
                    tma = _create_test_attr(sat, example.name, example)
                    # print("    3.1>", example, example.tags)
            else:
                tma = _create_test_attr(sat, scenario.name, scenario)
                # print("    3.0>", scenario, scenario.tags)

    mark_packages_suites_methods_ids(list(packages.values()))

    context.testipy_selected_tests = packages
    context.testipy_current_package = None

    get_rm()._startup_(list(packages.values()))

    print(show_test_structure(context.testipy_selected_tests.values()))


def tear_down(context: Context):
    get_rm().end_package(_reporter.last_package_details)
    get_rm()._teardown_("")


def start_feature(context: Context, feature: Feature):
    package_name = str(os.path.dirname(feature.filename).replace("/", "."))
    filename = os.path.basename(feature.filename)
    suite_name = os.path.splitext(filename)[0]

    tests: dict[str, PackageAttr] = context.testipy_selected_tests
    pat: PackageAttr = tests.get(package_name)
    if pat is None:
        raise ValueError(f"package {package_name} not found!")

    pd: PackageDetails = context.testipy_current_package
    if pd is None:
        context.testipy_current_package = pd = get_rm().startPackage(pat)
    elif pd.name != package_name:
        get_rm().end_package(pd)
        context.testipy_current_package = pd = get_rm().startPackage(pat)
    _reporter.last_package_details = pd

    sat: SuiteAttr = pat.get_suite_by_name(suite_name)
    if sat is None:
        raise ValueError(f"suite {suite_name} not found!")

    sd: SuiteDetails = get_rm().startSuite(pd, sat)
    context.testipy_suite_details = feature.testipy_suite_details = sd

def end_feature(context: Context, feature: Feature):
    get_rm().end_suite(feature.testipy_suite_details)


def start_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    sd: SuiteDetails = scenario.feature.testipy_suite_details
    tma: TestMethodAttr = sd.suite_attr.get_test_method_by_name(scenario.name)
    if tma is None:
        raise ValueError(f"scenario {scenario.name} not found!")

    td: TestDetails = get_rm().startTest(sd.set_current_test_method_attr(tma))
    context.testipy_test_details = scenario.testipy_test_details = td

def end_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    endTest(get_rm(), scenario.testipy_test_details)


def get_status(status: Status | int) -> str:
    if isinstance(status, int):
        return _STATUS.get(status, enums_data.STATE_FAILED_KNOWN_BUG)
    if isinstance(status, Status):
        return _STATUS.get(status.value, enums_data.STATE_FAILED_KNOWN_BUG)
    raise ValueError(f"Unexpected status value: {status}")


def end_step(context: Context, step: Step):
    get_rm().test_step(
        current_test=context.testipy_test_details,
        state=get_status(step.status),
        reason_of_state=str(step.exception) if step.exception else "ok",
        description=f"{step.keyword} {step.name}",
        exc_value=step.exception
    )
