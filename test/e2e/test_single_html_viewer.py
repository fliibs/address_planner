"""Cross-repository, real-browser proof for the SQLite single-HTML report."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from address_planner import (
    AddressSpace,
    Field,
    ReadOnly,
    ReadWrite,
    RegSpace,
    Register,
)


def _model() -> AddressSpace:
    register = Register("control", bit=32, description="control register")
    register.add(
        Field("enable", 1, sw_access=ReadWrite, hw_access=ReadOnly),
        offset=0,
    )
    register.add(
        Field("ready", 1, sw_access=ReadOnly, hw_access=ReadWrite),
        offset=1,
    )
    bank = RegSpace("peripheral", 256, description="peripheral bank")
    bank.add(register, offset=16)
    top = AddressSpace("e2e_soc", 4096, description="E2E system")
    top.add(bank, offset=1024)
    return top


def test_generated_single_html_opens_offline_and_queries_on_demand(tmp_path):
    selenium = pytest.importorskip("selenium")
    del selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.ui import WebDriverWait

    chrome = os.environ.get("CHROME_BINARY") or shutil.which("google-chrome")
    if not chrome:
        pytest.skip("Google Chrome is required for the single-HTML E2E test")

    model = _model()
    output_root = tmp_path / "generated"
    # No template path is supplied: this proves the normal Address Planner API
    # uses the versioned Viewer template shipped inside the Python package.
    model.generate(str(output_root))
    html = output_root / model.module_name / "html" / f"{model.module_name}_address_map.html"
    legacy_json = output_root / model.module_name / "html" / "data.json"
    assert html.is_file()
    assert not legacy_json.exists(), "legacy JSON must be opt-in"
    assert not list(html.parent.glob("*.sqlite")), "intermediate database must not be delivered"

    options = Options()
    options.binary_location = chrome
    for argument in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ):
        options.add_argument(argument)
    options.set_capability(
        "goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"}
    )

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    try:
        driver.get(html.resolve().as_uri())
        wait.until(
            lambda active: active.find_element(
                By.CSS_SELECTOR, '[data-testid="viewer-status"]'
            ).get_attribute("data-status")
            in ("ready", "error")
        )
        status = driver.find_element(
            By.CSS_SELECTOR, '[data-testid="viewer-status"]'
        ).get_attribute("data-status")
        if status != "ready":
            pytest.fail(
                driver.find_element(By.CSS_SELECTOR, '[data-testid="viewer-error"]').text
            )

        assert driver.find_element(
            By.CSS_SELECTOR, '[data-testid="node-name-1"]'
        ).text == "e2e_soc"
        assert not driver.find_elements(
            By.CSS_SELECTOR, '[data-testid="node-name-2"]'
        ), "AddressSpace children appeared before expansion"

        driver.find_element(
            By.CSS_SELECTOR, '[data-testid="expand-node-1"]'
        ).click()
        wait.until(
            expected.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '[data-testid="node-name-2"]'), "peripheral"
            )
        )
        assert not driver.find_elements(
            By.CSS_SELECTOR, '[data-testid="node-name-3"]'
        ), "Register appeared before its Bank was expanded"

        driver.find_element(
            By.CSS_SELECTOR, '[data-testid="expand-node-2"]'
        ).click()
        wait.until(
            expected.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '[data-testid="node-name-3"]'), "control"
            )
        )
        assert not driver.find_elements(
            By.CSS_SELECTOR, '[data-testid^="field-name-"]'
        ), "Fields appeared before their Register was selected"

        # Select via an address cell to prove the full Register row is interactive,
        # rather than only the name text.
        driver.find_element(
            By.CSS_SELECTOR, '[data-testid="node-row-3"] .numeric-cell'
        ).click()
        wait.until(
            expected.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '[data-testid="field-name-f:3:0"]'), "enable"
            )
        )
        fields = [
            element.text
            for element in driver.find_elements(
                By.CSS_SELECTOR, '[data-testid^="field-name-"]'
            )
        ]
        assert fields == ["enable", "ready"]

        unexpected_requests = []
        document_url = html.resolve().as_uri()
        for entry in driver.get_log("performance"):
            message = json.loads(entry["message"])["message"]
            if message["method"] == "Network.requestWillBeSent":
                url = message["params"]["request"]["url"]
                if url != document_url and not url.startswith(("blob:", "data:")):
                    unexpected_requests.append(url)
        assert unexpected_requests == []
        assert [
            entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE"
        ] == []
    finally:
        driver.quit()
