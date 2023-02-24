def pytest_runtest_logreport(report):  # type:ignore
    report.nodeid = ">" + report.nodeid[-75:]
