from testipy.helpers import prettify
from testipy.reporter import ReportManager
import requests
from thread_regulator import create_regular
from thread_regulator.graphs import PerformanceGraphs


def call_endpoint(user, **kwargs):
    response = requests.get("http://127.0.0.1:8000/info", timeout=1)
    return response.status_code == 200
    #return True


def notify_per_sec(stats_dict, rm: ReportManager):
    rps = stats_dict["rps"]
    success_ratio = round(stats_dict["success_ratio"]*100)
    ok = stats_dict["ok"]
    ko = stats_dict["ko"]

    rm.show_status(f"{rps=} {ok=}/{ko=} {success_ratio=}%")


class SuiteNFT:

    def test_call_1_time(self, ma, rm: ReportManager, ncycles=1, param=None):
        current_test = rm.startTest(ma)

        # call end-point
        response = requests.get("http://127.0.0.1:8000/info", timeout=1)

        # assert for status-code
        assert response.status_code == 200, f"Expected 200 got {response.status_code}"

        # log response
        rm.test_info(current_test, f"Received: {response.json()}")

        # close test
        rm.testPassed(current_test, f"took {response.elapsed}")

    def test_call_5s(self, ma, rm: ReportManager, ncycles=1, param=None):
        current_test = rm.startTest(ma)

        # start throughput test
        tr = create_regular(users=20, rps=1000, duration_sec=5, executions=None)
        tr.set_notifier(notify_method=notify_per_sec, every_sec=1, notify_method_args=(rm, ))
        tr.start(call_endpoint)

        # log statistics
        statistics = tr.get_statistics_as_dict()
        rm.test_info(current_test, f"Received:\n{prettify(statistics)}")

        # save performance results to .xls file
        pg = PerformanceGraphs()
        pg.collect_data(tr)
        pg.save_data("nft_results")

        # assert results
        assert statistics['ko'] == 0, f"had {statistics['ko']} failures!"
        assert statistics['rps'] > 800, f"RPS={statistics['rps']} too low!"