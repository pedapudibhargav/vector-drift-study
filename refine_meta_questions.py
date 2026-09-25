#!/usr/bin/env python3
"""Remove meta-template questions and UI scrape noise from benchmark_questions_200_final.json."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FINAL_PATH = ROOT / "data" / "benchmark_questions_200_final.json"
SOURCE_PATH = ROOT / "data" / "benchmark_questions_200.json"
API_BASE = "http://localhost:8000"

TARGET_IDS = [
    12, 16, 18, 20, 21, 23, 28, 31, 32, 34, 35, 61, 64, 68, 69, 70, 71, 72, 73, 74,
    77, 78, 85, 90, 92, 94, 96,
]

# (question_text, expected_answer_summary, required_chunk_substrings)
REFINEMENTS: dict[int, tuple[str, str, list[str]]] = {
    12: (
        "How much cheaper is Claude 3 Haiku on Amazon Bedrock compared to Claude Instant per 1,000 tokens?",
        "Claude 3 Haiku costs up to 68 percent of the price per 1,000 input/output tokens compared to Claude Instant, with higher levels of intelligence.",
        ["68 percent", "1,000 input/output tokens"],
    ),
    16: (
        "Which agent frameworks and SDKs can developers use with Amazon Bedrock AgentCore?",
        "Developers can start with LangChain, OpenAI Agents SDK, Claude Agent SDK, Strands SDK, or their own framework, and deploy with any model.",
        ["LangChain", "Strands SDK"],
    ),
    18: (
        "How much text can Anthropic Claude models process in a single context window on Amazon Bedrock?",
        "Claude's context window translates to roughly 150,000 words, or over 500 pages of material.",
        ["150,000 words", "500 pages"],
    ),
    20: (
        "How much text can Anthropic Claude models process in a single context window on Amazon Bedrock?",
        "Claude's context window translates to roughly 150,000 words, or over 500 pages of material.",
        ["150,000 words", "500 pages"],
    ),
    21: (
        "Which Bedrock customer improved developer support search accuracy by 20%?",
        "Adobe transformed developer support with 20% better search accuracy using Amazon Bedrock.",
        ["Adobe", "20% better search accuracy"],
    ),
    23: (
        "What does Amazon Bedrock Custom Model Import allow teams to do with existing customized models?",
        "With Custom Model Import, you can import your existing customized models and register them as imported models on Amazon Bedrock.",
        ["Custom Model Import", "imported models"],
    ),
    28: (
        "What must developers do in the Amazon Bedrock console before using foundation models?",
        "After setting up your Amazon Bedrock IAM role, you can sign into the Amazon Bedrock console and request access to foundation models.",
        ["request access to foundation models"],
    ),
    31: (
        "Which AI21 Labs model family is available on Amazon Bedrock?",
        "The Jamba 1.5 family of models by AI21 Labs is now available in Amazon Bedrock.",
        ["Jamba 1.5", "Amazon Bedrock"],
    ),
    32: (
        "Which agent frameworks can use Amazon Bedrock Managed Knowledge Base as a retriever?",
        "Bedrock Managed Knowledge Base can be configured as a retriever for agent frameworks including Strands Agents, LangChain, CrewAI, and LlamaIndex.",
        ["Strands Agents", "LangChain", "LlamaIndex"],
    ),
    34: (
        "How can developers use Bedrock Marketplace models with native Bedrock tools?",
        "You can access models through Bedrock's unified APIs and use them natively with Bedrock tools such as Agents, Knowledge Bases, and Guardrails.",
        ["unified APIs", "Knowledge Bases", "Guardrails"],
    ),
    35: (
        "What architecture does Meta Llama 4 use on Amazon Bedrock?",
        "Llama 4 uses native multimodality, mixture-of-experts architecture, expanded context windows, and optimized computational efficiency.",
        ["mixture-of-experts", "Llama 4"],
    ),
    61: (
        "What EC2 instance type did AWS announce for right-sizing single-GPU ML workloads in the August 18, 2025 roundup?",
        "Amazon EC2 Single GPU P5 instances are now generally available, offering an EC2 P5 size with one NVIDIA H100 GPU for cost-effective ML and HPC workloads.",
        ["Single GPU P5", "NVIDIA H100"],
    ),
    64: (
        "How does Amazon SageMaker enforce fine-grained access to data and models?",
        "Teams can consistently define and enforce access policies using a single permission model with fine-grained access controls through Amazon SageMaker Catalog.",
        ["fine-grained access controls", "SageMaker Catalog"],
    ),
    68: (
        "How does SageMaker Canvas help non-technical users build machine learning models?",
        "SageMaker Canvas accelerates innovation by democratizing ML development across all skill levels regardless of coding expertise.",
        ["democratizing ML development"],
    ),
    69: (
        "How does Amazon SageMaker Catalog help users find data and AI assets?",
        "Amazon SageMaker Catalog supports semantic search with generative AI-created metadata and lets users ask Amazon Q Developer in natural language to find data.",
        ["semantic search", "Amazon Q Developer"],
    ),
    70: (
        "How does SageMaker Clarify help detect bias in machine learning models?",
        "SageMaker Clarify runs bias analysis on specified input features and provides visual reports with metrics and measurements of potential bias.",
        ["potential bias", "bias analysis"],
    ),
    71: (
        "By what percentage did NatWest Group reduce time for data users to access new tools with Amazon SageMaker?",
        "NatWest Group reduced the time required for data users to access new tools by around 50% using Amazon SageMaker.",
        ["50%", "NatWest"],
    ),
    72: (
        "How does SageMaker Data and AI Governance help identify sensitive data in pipelines?",
        "Teams can automatically identify sensitive information within pipelines using Amazon Comprehend.",
        ["Amazon Comprehend", "sensitive information"],
    ),
    73: (
        "What performance improvements can SageMaker Ground Truth customized models deliver?",
        "SageMaker Ground Truth customized models demonstrate measurable improvements over baseline metrics in speed, accuracy, or cost efficiency.",
        ["measurable improvements", "cost efficiency"],
    ),
    74: (
        "How much faster can SageMaker data processing deliver insights compared to traditional open source systems?",
        "SageMaker Data Processing delivers insights up to 2x faster than traditional open source systems with performant API-compatible runtimes.",
        ["2x faster", "open source"],
    ),
    77: (
        "What is the next generation of Amazon SageMaker described as in the FAQs?",
        "The next generation of SageMaker is a unified platform for data, analytics, and AI with integrated access to all data and tools for analytics and AI.",
        ["unified platform for data, analytics, and AI"],
    ),
    78: (
        "What SageMaker AI capability does the getting started page highlight for pretraining foundation models?",
        "SageMaker AI offers tools to pretrain FMs from scratch so they can be used internally or offered to other teams.",
        ["pretrain FMs from scratch"],
    ),
    85: (
        "What platform is Amazon SageMaker Catalog built on?",
        "Amazon SageMaker Catalog is built on Amazon DataZone to help teams govern and collaborate on data and AI assets.",
        ["Amazon DataZone", "SageMaker Catalog"],
    ),
    90: (
        "How did Salesforce use Amazon SageMaker HyperPod according to the SageMaker AI customers page?",
        "Salesforce turned isolated nodes into a high-performance GPU fabric with Amazon SageMaker HyperPod.",
        ["Salesforce", "HyperPod"],
    ),
    92: (
        "How does Managed MLflow integrate with SageMaker Model Registry?",
        "Managed MLflow includes a purpose-built integration that automatically synchronizes models registered in MLflow with SageMaker Model Registry.",
        ["MLflow", "SageMaker Model Registry"],
    ),
    94: (
        "When did AWS discontinue support for SageMaker Ground Plus?",
        "AWS discontinued support for SageMaker Ground Plus on June 30, 2026.",
        ["SageMaker Ground Plus", "June 30, 2026"],
    ),
    96: (
        "What performance improvements can SageMaker Ground Truth customized models deliver?",
        "SageMaker Ground Truth customized models demonstrate measurable improvements over baseline metrics in speed, accuracy, or cost efficiency.",
        ["measurable improvements", "cost efficiency"],
    ),
}

BONUS_FIXES: dict[int, tuple[str, str, list[str]]] = {
    76: (
        "By how much can hosting multiple models on a single SageMaker endpoint reduce deployment costs?",
        "Hosting multiple models on the same instance can better utilize underlying accelerators, reducing deployment costs by up to 50%.",
        ["up to 50%", "multiple models"],
    ),
    135: (
        "What up-front or ongoing commitment is required to get started with AWS on the Advertising & Marketing case studies page?",
        "You can set up an AWS account with just a few clicks without any up-front or on-going commitment.",
        ["up-front or on-going commitment", "few clicks"],
    ),
}

META_QUESTION_RE = re.compile(
    r"(?i)(what specific capability does the|page describe\?|page cite\?|page mention\?)"
)

UI_MARKUP_RE = re.compile(
    r"(?i)("
    r"^#{1,6}\s|"
    r"\n#{1,6}\s|"
    r"displaying\s+0-0|"
    r"request a demo|"
    r"(?:^|\n)loading(?:\n|$)|"
    r"(?:^|\n)filter(?:\n|$)|"
    r"did you find what you were looking for|"
    r"learn more\n\n###|"
    r"amazon bedrock\s*\n\s*\*\s+overview|"
    r"watch the video"
    r")"
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def fetch_chunk_text(url: str) -> str:
    q = urllib.parse.urlencode({"url": url})
    with urllib.request.urlopen(f"{API_BASE}/api/dataset/urls/text?{q}", timeout=60) as resp:
        data = json.load(resp)
    return "\n".join(c.get("text", "") for c in data.get("chunks", []))


def contains(haystack: str, needle: str) -> bool:
    return normalize(needle) in normalize(haystack)


def is_meta_question(text: str) -> bool:
    return bool(META_QUESTION_RE.search(text))


def has_ui_markup(text: str) -> bool:
    return bool(UI_MARKUP_RE.search(text))


def write_outputs(benchmark: dict) -> None:
    benchmark["total_questions"] = 200
    benchmark["source_manifest"] = "group-200.json"
    FINAL_PATH.write_text(json.dumps(benchmark, indent=2) + "\n")

    part1 = [q for q in benchmark["questions"] if int(q["question_id"].split("_")[1]) <= 100]
    part2 = [q for q in benchmark["questions"] if int(q["question_id"].split("_")[1]) > 100]
    buf = [
        "{",
        '  "total_questions": 200,',
        '  "source_manifest": "group-200.json",',
        '  "questions": [',
    ]
    for i, q in enumerate(part1):
        block = json.dumps(q, indent=4)
        indented = "\n".join("    " + line for line in block.splitlines())
        buf.append(indented + ("," if i < len(part1) - 1 or part2 else ""))
    buf.append("    // --- Part 2: Generated questions q_101 to q_200 (corpus_id 101-200) ---")
    for i, q in enumerate(part2):
        block = json.dumps(q, indent=4)
        indented = "\n".join("    " + line for line in block.splitlines())
        buf.append(indented + ("," if i < len(part2) - 1 else ""))
    buf.extend(["  ]", "}"])
    SOURCE_PATH.write_text("\n".join(buf) + "\n")


def main() -> int:
    benchmark = json.loads(FINAL_PATH.read_text())
    q_by_num = {int(q["question_id"].split("_")[1]): q for q in benchmark["questions"]}
    log: list[str] = []
    errors: list[str] = []

    all_fixes = {**REFINEMENTS, **BONUS_FIXES}
    for q_num in sorted(set(TARGET_IDS) | set(BONUS_FIXES)):
        if q_num not in all_fixes:
            errors.append(f"q_{q_num:03d}: missing refinement entry")
            continue
        question, answer, anchors = all_fixes[q_num]
        entry = q_by_num[q_num]
        chunk_text = fetch_chunk_text(entry["target_url"])
        missing = [a for a in anchors if not contains(chunk_text, a)]
        if missing:
            errors.append(f"q_{q_num:03d}: chunk missing anchors {missing}")
            continue
        entry["question_text"] = question
        entry["expected_answer_summary"] = answer
        log.append(f"q_{q_num:03d}: refined")

    # Scan all questions for remaining meta/UI issues
    meta_remaining = []
    ui_remaining = []
    for q in benchmark["questions"]:
        qid = q["question_id"]
        if "page describe" in q["question_text"].lower():
            meta_remaining.append(qid)
        if has_ui_markup(q["expected_answer_summary"]):
            ui_remaining.append(qid)

    validation = benchmark.get("validation", {})
    validation["meta_refinement"] = {
        "refined_ids": [f"q_{n:03d}" for n in TARGET_IDS],
        "refinement_log": log,
        "errors": errors,
    }
    benchmark["validation"] = validation
    write_outputs(benchmark)

    print("=" * 50)
    print("META-QUESTION REFINEMENT REPORT")
    print("=" * 50)
    print(f"Questions refined          : {len(log)}")
    print(f"Anchor validation errors   : {len(errors)}")
    print(f"'page describe' remaining : {len(meta_remaining)}")
    print(f"UI markup in answers       : {len(ui_remaining)}")
    print("=" * 50)
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    if meta_remaining:
        for qid in meta_remaining:
            print(f"  META: {qid}")
    if ui_remaining:
        for qid in ui_remaining:
            print(f"  UI: {qid}")
    if not errors and not meta_remaining and not ui_remaining:
        print("All checks passed: 0 meta-template questions, 0 UI-scrape answers.")
    return 1 if errors or meta_remaining or ui_remaining else 0


if __name__ == "__main__":
    sys.exit(main())
