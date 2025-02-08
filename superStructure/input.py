import boto3
import logging
import time
import random
from typing import Any, Dict, List

from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

from webscrap import webscrap  # Assumed to be defined elsewhere

logging.basicConfig(level=logging.INFO, format="%(message)s")

AWS_REGION = "us-east-1"

FINAL_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
SUMMARIZATION_MODEL_ID = "us.amazon.nova-pro-v1:0"
MAX_TOKENS_SUMMARY = 2500  # Adjust if necessary

# Global maximum number of retries for converse calls.
MAX_RETRIES = 5


def invoke_converse_with_retries(client: boto3.client, **kwargs) -> Dict[str, Any]:
    """
    Invokes client.converse() with retry logic and exponential backoff.
    Retries if a ClientError is raised with error code "ThrottlingException".
    
    :param client: A boto3 client for the Bedrock runtime.
    :param kwargs: All arguments to pass to client.converse.
    :return: The API response.
    :raises Exception: If the maximum number of retries is exceeded.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = client.converse(**kwargs)
            return response
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ThrottlingException":
                # Add random jitter to avoid thundering herd issues.
                wait = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(
                    f"ThrottlingException encountered (attempt {attempt + 1}/{MAX_RETRIES}). "
                    f"Retrying in {wait:.1f} seconds..."
                )
                time.sleep(wait)
            else:
                logging.error(f"Non-throttling error encountered: {e}")
                raise
    raise Exception("Max retries exceeded for converse call.")


def summarize_page(title: str, link: str, content: str, client: boto3.client) -> str:
    """
    Summarizes a page's content by invoking the Converse API.
    
    :param title: Title of the page.
    :param link: URL of the page.
    :param content: The scraped content.
    :param client: Bedrock runtime client.
    :return: The summary text (or a fallback substring of content).
    """
    system_prompt = [{
        "text": (
            f"Summarize the following webpage content in a concise manner. The page title is '{title}' and its URL is {link}. "
            "Focus on extracting the most important details that would be useful for answering questions about the company."
        )
    }]
    conversation = [{
        "role": "user",
        "content": [{"text": f"Content: {content}"}]
    }]
    try:
        response = invoke_converse_with_retries(
            client,
            modelId=SUMMARIZATION_MODEL_ID,
            messages=conversation,
            system=system_prompt,
            inferenceConfig={"maxTokens": MAX_TOKENS_SUMMARY, "temperature": 0.5, "topP": 0.9},
        )
        summary_text = response["output"]["message"]["content"][0]["text"]
        logging.info(f"Summary for '{title}' obtained.")
        return summary_text.strip()
    except Exception as e:
        logging.error(f"Error summarizing page '{title}': {e}")
        # Fallback: return a truncated version if summarization fails.
        return content[:500]


def create_critical_investigation_questions(scraped_sources: List[str], investigation_question: str) -> List[str]:
    """
    Generates critical follow-up investigation questions based on scraped sources.
    
    :param scraped_sources: List of texts scraped from various sources.
    :param investigation_question: The overall investigation question.
    :return: A list of critical follow-up questions.
    """
    def get_critical_question_tool_spec() -> Dict[str, Any]:
        return {
            "toolSpec": {
                "name": "CriticalQuestion_Tool",
                "description": "Tool for generating a single critical follow-up investigation question.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "A critical follow-up investigation question based on the provided sources."
                            }
                        },
                        "required": ["question"]
                    }
                }
            }
        }

    def invoke_critical_question_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
        # In production, this would invoke an external service.
        return {
            "toolUseId": payload.get("toolUseId"),
            "content": {
                "question": payload.get("input", {}).get("question", "")
            }
        }

    sources_text = "\n\n".join(scraped_sources)
    system_prompt_text = (
        f"You are a discerning investigator. You have been provided with multiple scraped sources as context "
        f"for the following investigation question: '{investigation_question}'.\n\n"
        f"Scraped sources:\n{sources_text}\n\n"
        "Based on the analysis of these sources and the overall investigation question, generate a list of critical "
        "follow-up questions that probe for serious issues, red flags, or gaps in the information. "
        "Do NOT output the questions as one block of text. Instead, for each question, call the 'CriticalQuestion_Tool' "
        "by issuing a tool call. Each tool call must have an input JSON with a field 'question' containing one "
        "critical investigation question."
    )
    system_prompt = [{"text": system_prompt_text}]
    user_message_text = (
        f"Generate separate critical follow-up investigation questions for the overall question: "
        f"'{investigation_question}' using tool calls, based on the provided sources."
    )
    conversation = [{"role": "user", "content": [{"text": user_message_text}]}]
    tool_config = {"tools": [get_critical_question_tool_spec()]}
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    collected_questions: List[str] = []
    MAX_RECURSIONS = 5

    def process_model_response(conversation: List[Dict[str, Any]], recursion: int):
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        if recursion <= 0:
            logging.warning("Max recursion reached; stopping further requests.")
            return

        try:
            response = invoke_converse_with_retries(
                client,
                modelId=model_id,
                messages=conversation,
                system=system_prompt,
                toolConfig=tool_config
            )
        except Exception as e:
            logging.error(f"Error during converse call: {e}")
            return

        stop_reason = response.get("stopReason", "")
        assistant_message = response.get("output", {}).get("message", {})
        conversation.append(assistant_message)

        tool_uses = [block["toolUse"] for block in assistant_message.get("content", [])
                      if "toolUse" in block]

        if tool_uses:
            tool_result_contents = []
            for tu in tool_uses:
                tool_response = invoke_critical_question_tool(tu)
                question_text = tool_response["content"].get("question", "").strip()
                if question_text:
                    logging.info(f"Collected critical question: {question_text}")
                    collected_questions.append(question_text)
                tool_result_contents.append({
                    "toolResult": {
                        "toolUseId": tool_response["toolUseId"],
                        "content": [{"json": tool_response["content"]}]
                    }
                })
            conversation.append({"role": "user", "content": tool_result_contents})
            process_model_response(conversation, recursion - 1)
        elif stop_reason != "end_turn" and len(collected_questions) < 5:
            conversation.append({
                "role": "user",
                "content": [{"text": "Please provide additional critical investigation questions using tool calls."}]
            })
            process_model_response(conversation, recursion - 1)
        else:
            return

    process_model_response(conversation, MAX_RECURSIONS)
    return collected_questions


def create_questions_list(company_name: str) -> List[str]:
    """
    Generates due diligence questions for a company by having the model call a tool for each question.
    
    :param company_name: Name of the company.
    :return: A list of due diligence questions.
    """
    def get_question_tool_spec() -> Dict[str, Any]:
        return {
            "toolSpec": {
                "name": "Question_Tool",
                "description": "Tool for registering an individual due diligence question.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "A due diligence question about the company."
                            }
                        },
                        "required": ["question"]
                    }
                }
            }
        }

    def invoke_question_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "toolUseId": payload.get("toolUseId"),
            "content": {
                "question": payload.get("input", {}).get("question", "")
            }
        }

    system_prompt_text = (
        f"You are a highly experienced financial analyst. For the company '{company_name}', "
        "generate a list of due diligence questions fit for external research. Do NOT output the questions as one block of text. "
        "Instead, for each question, call the 'Question_Tool' by issuing a tool call. "
        "Each tool call must have an input JSON with a field 'question' containing one due diligence question. "
        "Ensure that the questions cover areas such as financial performance, market position, management, "
        "operational risks, regulatory compliance, competitive landscape, growth strategy, and potential red flags."
    )
    system_prompt = [{"text": system_prompt_text}]
    user_message_text = f"Generate separate due diligence questions for '{company_name}' using tool calls."
    conversation = [{"role": "user", "content": [{"text": user_message_text}]}]
    tool_config = {"tools": [get_question_tool_spec()]}
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    collected_questions: List[str] = []
    MAX_RECURSIONS = 5

    def process_model_response(conversation: List[Dict[str, Any]], recursion: int):
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        if recursion <= 0:
            logging.warning("Max recursion reached; stopping further requests.")
            return

        try:
            response = invoke_converse_with_retries(
                client,
                modelId=model_id,
                messages=conversation,
                system=system_prompt,
                toolConfig=tool_config
            )
        except Exception as e:
            logging.error(f"Error during converse call: {e}")
            return

        stop_reason = response.get("stopReason", "")
        assistant_message = response.get("output", {}).get("message", {})
        conversation.append(assistant_message)

        tool_uses = [block["toolUse"] for block in assistant_message.get("content", [])
                      if "toolUse" in block]

        if tool_uses:
            tool_result_contents = []
            for tu in tool_uses:
                tool_response = invoke_question_tool(tu)
                question_text = tool_response["content"].get("question", "").strip()
                if question_text:
                    logging.info(f"Collected question: {question_text}")
                    collected_questions.append(question_text)
                tool_result_contents.append({
                    "toolResult": {
                        "toolUseId": tool_response["toolUseId"],
                        "content": [{"json": tool_response["content"]}]
                    }
                })
            conversation.append({"role": "user", "content": tool_result_contents})
            process_model_response(conversation, recursion - 1)
        elif stop_reason != "end_turn" and len(collected_questions) < 10:
            conversation.append({
                "role": "user",
                "content": [{"text": "Please provide additional due diligence questions using tool calls."}]
            })
            process_model_response(conversation, recursion - 1)
        else:
            return

    process_model_response(conversation, MAX_RECURSIONS)
    return collected_questions


def ask_question(input_query: str, company_name: str) -> str:
    """
    Given an input query and company name, this function scrapes relevant pages,
    summarizes them, and uses the consolidated summaries as context to answer the question.
    
    :param input_query: The question to answer.
    :param company_name: The name of the company.
    :return: The answer text from the model.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    webscrap_result = webscrap(input_query)
    if not webscrap_result:
        logging.error("No webscrap results found.")
        return ""
    
    summaries = []
    for title, (link, content) in webscrap_result.items():
        summary = summarize_page(title, link, content, client)
        summaries.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")
    combined_summary = "\n\n".join(summaries)
    
    user_message = (
        f"Answer the question: {input_query} about the company, {company_name}. "
        f"Use the following summarized web search results to inform your answer:\n\n{combined_summary}"
        f"Make the results as accurate and informative, and information dense as possible.  Include interesting analysis and write in full sentence super information dense well written paragraphs"
    )
    conversation = [{"role": "user", "content": [{"text": user_message}]}]

    try:
        response = invoke_converse_with_retries(
            client,
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        #print(response_text)
        return response_text
    except Exception as e:
        logging.error(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


def process_questions(questions_list: List[str], company_name: str) -> None:
    """
    Processes multiple questions concurrently using a thread pool.
    
    :param questions_list: List of questions to ask.
    :param company_name: The company name to include in the query.
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_question = {
            executor.submit(ask_question, question, company_name): question
            for question in questions_list
        }
        return_me_result = []
        for future in as_completed(future_to_question):
            question = future_to_question[future]
            try:
                result = future.result()
                #print(f"\nResults for question: '{question}'")
                #print(result)
                return_me_result.append([question, result])
            except Exception as e:
                print(f"Exception for question '{question}': {str(e)}")
        return return_me_result


def enter_company_name(company_name: str) -> None:
    """
    For a given company name, generates a list of due diligence questions and processes them.
    
    :param company_name: The name of the company.
    """
    # You may use a hard-coded list or dynamically generate one:
    questions_list = create_questions_list(company_name)
    return process_questions(questions_list, company_name)


# Example usage:
print(enter_company_name("Perplexity"))
