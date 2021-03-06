#!/usr/bin/env python
'''Asterisk external test suite usage report

Copyright (C) 2016, Digium, Inc.
Scott Griepentrog <sgriepentrog@digium.com>

This program is free software, distributed under the terms of
the GNU General Public License Version 2.
'''

import sys
import yaml

sys.path.append('lib/python')

TESTS_CONFIG = "tests.yaml"
TEST_CONFIG = "test-config.yaml"


class Test:
    def __init__(self, path):
        self.path = path
        self.test_config = load_yaml_config("%s/%s" % (path, TEST_CONFIG))

        properties = self.test_config.get('properties', {})
        self.tags = properties.get('tags', ['none'])
        self.dependencies = [repr(d)
                             for d in properties.get('dependencies', [])]

        test_modules = self.test_config.get('test-modules', {})
        test_objects = test_modules.get('test-object', {})
        if not isinstance(test_objects, list):
            test_objects = [test_objects]
        self.test_objects = [obj.get('typename', 'test-run')
                             for obj in test_objects]
        modules = test_modules.get('modules', {})
        self.test_modules = [module.get('typename', '-error-')
                             for module in modules]


class TestSuite:
    def __init__(self):
        self.tests = self._parse_test_yaml("tests")

    def _parse_test_yaml(self, test_dir):
        tests = []

        config = load_yaml_config("%s/%s" % (test_dir, TESTS_CONFIG))
        if not config:
            return tests

        for t in config["tests"]:
            for val in t:
                path = "%s/%s" % (test_dir, t[val])
                if val == "test":
                    tests.append(Test(path))
                elif val == "dir":
                    tests += self._parse_test_yaml(path)

        return tests

    def unique(self, key):
        result = set()
        for test in self.tests:
            result = result.union(getattr(test, key))
        result = list(set(result))
        result.sort(key=str.lower)
        return result

    def occurances(self, **kwargs):
        match = []
        for test in self.tests:
            for key, value in kwargs.items():
                if value in getattr(test, key):
                    match.append(test)
                    continue

        return len(match)

    def results_for(self, key):
        print(key.title() + ":")
        things = self.unique(key)
        width = max(len(t) for t in things)
        results = [(self.occurances(**{key: t}), t) for t in things]
        results.sort(key=lambda tup: tup[0], reverse=True)
        for (count, name) in results:
            print("\t%-*s %5d" % (width, name, count))
        print("")


def load_yaml_config(path):
    """Load contents of a YAML config file to a dictionary"""
    try:
        f = open(path, "r")
    except IOError:
        # Ignore errors for the optional tests/custom folder.
        if path != "tests/custom/tests.yaml":
            print("Failed to open %s" % path)
        return None
    except:
        print("Unexpected error: %s" % sys.exc_info()[0])
        return None

    config = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    return config


def main(argv=None):
    print("Testsuite Module Usage and Coverage Report")
    print("")
    test_suite = TestSuite()
    print("Number of tests:", len(test_suite.tests))
    print("")
    test_suite.results_for('tags')
    test_suite.results_for('test_objects')
    test_suite.results_for('test_modules')
    test_suite.results_for('dependencies')

if __name__ == "__main__":
    sys.exit(main() or 0)
