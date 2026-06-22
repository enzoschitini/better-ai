import argparse
import copy
import json
from typing import Any, Dict

from dotenv import load_dotenv

from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.deep_research.tavily_research.test.research_payloads import build_test_cases


def print_json(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2, ensure_ascii=True, default=str))


def list_cases(cases: Dict[str, Dict[str, Any]]) -> None:
    print("Casos disponiveis:\n")
    for case_name, case in cases.items():
        print(f"- {case_name}")
        print(f"  metodo: {case['method']}")
        print(f"  descricao: {case['description']}")


def run_case(
    researcher: TavilyDeepResearch,
    case_name: str,
    case: Dict[str, Any],
    request_id: str | None,
) -> None:
    params = copy.deepcopy(case["params"])

    if case["method"] == "get_research_status":
        if request_id:
            params["request_id"] = request_id

    print_json(f"REQUEST {case_name}", {"method": case["method"], "params": params})

    method = getattr(researcher, case["method"])
    response = method(params)

    print_json(f"RESPONSE {case_name}", response)

    if case["method"] == "start_research" and isinstance(response, dict):
        new_request_id = response.get("request_id")
        if new_request_id:
            print(f"\nrequest_id capturado: {new_request_id}")
            print("Use este valor em --request-id para consultar status.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testador Tavily para todas as modalidades/metodos do wrapper atual."
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Nome do caso para executar (ex.: search_general_basic).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Executa todos os casos disponiveis.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista todos os casos e encerra.",
    )
    parser.add_argument(
        "--request-id",
        type=str,
        default=None,
        help="Request ID para o caso get_research_status.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    cases = build_test_cases()

    if args.list:
        list_cases(cases)
        return

    if not args.case and not args.all:
        print("Informe --list, --case <nome> ou --all")
        return

    researcher = TavilyDeepResearch()

    if args.all:
        for case_name, case in cases.items():
            run_case(researcher, case_name, case, args.request_id)
        return

    if args.case not in cases:
        print(f"Caso invalido: {args.case}")
        print("Use --list para ver os nomes validos.")
        return

    run_case(researcher, args.case, cases[args.case], args.request_id)


if __name__ == "__main__":
    main()


# Exemplos:
# python -m src.deep_research.tavily_research.test.tavily_test --list
# python -m src.deep_research.tavily_research.test.tavily_test --all
# python -m src.deep_research.tavily_research.test.tavily_test --case search_general_basic
# python -m src.deep_research.tavily_research.test.tavily_test --case search_general_advanced
# python -m src.deep_research.tavily_research.test.tavily_test --case search_news_mode
# python -m src.deep_research.tavily_research.test.tavily_test --case search_domain_filters
# python -m src.deep_research.tavily_research.test.tavily_test --case get_context
# python -m src.deep_research.tavily_research.test.tavily_test --case qna
# python -m src.deep_research.tavily_research.test.tavily_test --case extract_content
# python -m src.deep_research.tavily_research.test.tavily_test --case map_site
# python -m src.deep_research.tavily_research.test.tavily_test --case crawl_site
# python -m src.deep_research.tavily_research.test.tavily_test --case get_company
# python -m src.deep_research.tavily_research.test.tavily_test --case start_research
# python -m src.deep_research.tavily_research.test.tavily_test --case get_research_status --request-id <ID>