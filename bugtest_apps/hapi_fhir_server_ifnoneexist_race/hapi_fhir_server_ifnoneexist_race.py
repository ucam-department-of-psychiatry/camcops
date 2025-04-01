#!/usr/bin/env python

r"""
hapi_fhir_server_ifnoneexist_race.py

Minimal example to test HAPI FHIR (https://hapifhir.io/) server for an
If-None-Exists race condition -- can we create two records inappropriately?

Test environment (client side):

- an 8-core machine with 8 threads
- Ubuntu 20.04
- Python 3.8.10
- pip install 'fhirclient @ git+https://github.com/ucam-department-of-psychiatry/client-py@128bbe3c2194a51ba6ff8cf880ef2fdb9bfcc2d6#egg=fhirclient-4.0.0.1'
  ... which implements https://github.com/smart-on-fhir/client-py/pull/105
- pip install requests==2.26.0

If things go well (CORRECT behaviour), only one instance is created with the
given "value". The creation returns "201 Created"; subsequent attempts return
"200 OK".

If this goes wrong (BUG behaviour), then two (or more -- I've seen 8/8) threads
create the same object, despite the "ifNoneExist" parameter, and then
subsequent create operations fail with an HTTPError like:

    Failed to CREATE resource with match URL
    \"identifier=https://some_system|value1\"
    because this search matched 2 resources

(It says "2 resources" even if 6 or 8 creation operations succeeded.)

As of 2021-11-03,

    docker run -p 8080:8080 hapiproject/hapi:latest  # BUG OBSERVED SOMETIMES
    docker run -p 8080:8080 hapiproject/hapi:v5.5.1  # BUG OBSERVED SOMETIMES
    docker run -p 8080:8080 hapiproject/hapi:v5.5.0  # BUG OBSERVED SOMETIMES
    docker run -p 8080:8080 hapiproject/hapi:v5.4.1  # BUG OBSERVED SOMETIMES
    docker run -p 8080:8080 hapiproject/hapi:v5.4.0  # always error 404

At v5.4.0, all requests give an HTTP 404 error containing:

    The origin server did not find a current representation for the target
    resource or is not willing to disclose that one exists.

Reported at https://github.com/hapifhir/hapi-fhir/issues/3141.

"""  # noqa

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from multiprocessing import cpu_count
from typing import Any, Dict

from fhirclient.client import FHIRClient
from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhirclient.models.identifier import Identifier
from fhirclient.models.questionnaire import Questionnaire
from fhirclient.server import FHIRNotFoundException
from rich_argparse import RichHelpFormatter
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)


def print_json(prefix: str, x: Dict[str, Any], indent: int = None) -> None:
    log.info(f"{prefix}{json.dumps(x, indent=indent)}")


def make_bundle(value: str, sp_unique: bool = False) -> Bundle:
    system = "https://some_system"
    jd = {
        "type": "transaction",
        "entry": [
            BundleEntry(
                jsondict={
                    "request": BundleEntryRequest(
                        jsondict={
                            "method": "POST",
                            "url": "Questionnaire",
                            "ifNoneExist": f"identifier={system}|{value}",
                        }
                    ).as_json(),
                    "resource": Questionnaire(
                        jsondict={
                            "name": "some_questionnaire_name",
                            "status": "active",
                            "identifier": [
                                Identifier(
                                    jsondict={"system": system, "value": value}
                                ).as_json()
                            ],
                        }
                    ).as_json(),
                }
            ).as_json()
        ],
    }
    # Note: the .as_json() conversions are necessary.
    if sp_unique:
        raise NotImplementedError(
            "sp_unique method not implemented; see "
            "https://github.com/hapifhir/hapi-fhir/issues/3141"
        )
    return Bundle(jsondict=jd)


def single_test_insert_if_none_exists(
    url: str, value: str, proc_num: int = 1, sp_unique: bool = False
) -> None:
    app_id = "hapi_fhir_server_ifnoneexist_race"
    client = FHIRClient(settings={"api_base": url, "app_id": app_id})
    bundle = make_bundle(value=value, sp_unique=sp_unique)
    print_json(f"[{proc_num}] Bundle: ", bundle.as_json())
    try:
        response = bundle.create(client.server)
        print_json(f"[{proc_num}] Success: ", response)
    except HTTPError as e:
        log.error(f"[{proc_num}] Error from FHIR server: {e.response.text}")
    except FHIRNotFoundException as e:
        # Incidentally, this is NOT CAUGHT. I don't understand why.
        # The exception falls through to the generic "Exception", below.
        # At that point, type(e) gives: <class 'server.FHIRNotFoundException'>,
        # but isinstance(e, FHIRNotFoundException) gives False.
        # Manual creation/type testing works.
        log.error(
            f"[{proc_num}] FHIR server says not found: {e.response.text}"
        )
    except Exception as e:
        x = e.response.text if hasattr(e, "response") else ""
        log.error(f"[{proc_num}] Error from fhirclient ({type(e)}): {e}{x}")


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "--url",
        default="http://localhost:8080/fhir",
        help="FHIR server API URL",
    )
    parser.add_argument(
        "--value",
        default="value1",
        help="Value field for object to be created. If no bug is observed at "
        "first, change this to a new value and try again.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=cpu_count(),
        help="Number of simultaneous threads",
    )
    parser.add_argument(
        "--serial", action="store_true", help="Use serial mode, not parallel"
    )
    parser.add_argument(
        "--sp_unique",
        action="store_true",
        help="Enforce uniqueness via a Combo Search Index Parameter; "
        "https://smilecdr.com/docs/fhir_repository/custom_search_parameters.html#uniqueness",  # noqa
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d:%(levelname)s: %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def thread_fn(i_: int) -> None:
        single_test_insert_if_none_exists(
            url=args.url,
            value=args.value,
            sp_unique=args.sp_unique,
            proc_num=i_,
        )

    gen_i = range(1, args.n + 1)
    if args.serial:
        for i in gen_i:
            thread_fn(i)
    else:
        with ThreadPoolExecutor(max_workers=args.n) as executor:
            executor.map(thread_fn, gen_i)


if __name__ == "__main__":
    main()
