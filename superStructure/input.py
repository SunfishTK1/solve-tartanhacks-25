import boto3
import logging
import time
import random
from typing import Any, Dict, List

from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError

from webscrap import webscrap  # Assumed to be defined elsewhere

logging.basicConfig(level=logging.INFO, format="%(message)s")

AWS_REGION = "us-east-1"

FINAL_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
SUMMARIZATION_MODEL_ID = "us.amazon.nova-pro-v1:0"
MAX_TOKENS_SUMMARY = 2500  # Adjust if necessary

# Global maximum number of retries for converse calls.
MAX_RETRIES = 1


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


def summarize_page(title: str, link: str, content: str, client: boto3.client, uuid) -> str:
    """
    Summarizes a page's content by invoking the Converse API.
    
    :param title: Title of the page.
    :param link: URL of the page.
    :param content: The scraped content.
    :param client: Bedrock runtime client.
    :return: The summary text (or a fallback substring of content).
    """
    model_ids = ["us.amazon.nova-lite-v1:0"], 
    model_id = ""
    SUMMARIZATION_MODEL_ID = ""
    SUMMARIZATION_MODEL_ID = random.choice(model_ids[0])
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


def create_critical_investigation_questions(scraped_sources: List[str], investigation_question: str, uuid) -> List[str]:
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
        "critical investigation question.  Always mention the company name explicitly in the question."
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
    MAX_RECURSIONS = 1

    def process_model_response(conversation: List[Dict[str, Any]], recursion: int):

        model_ids = ["us.anthropic.claude-3-5-haiku-20241022-v1:0"], 
        model_id = ""
        model_id = random.choice(model_ids[0])
        #model_id = "us.meta.llama3-3-70b-instruct-v1:0"
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
        
        content = assistant_message.get("content", [])
        has_tool = any("toolUse" in block for block in content)
        has_text = any("text" in block for block in content)
        if has_tool and has_text:
            # Keep only tool-use blocks (or alternatively split into two messages)
            assistant_message["content"] = [block for block in content if "toolUse" in block]
        # *** END NEW CODE ***


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
        elif stop_reason != "end_turn" and len(collected_questions) < MAX_RECURSIONS:
            conversation.append({
                "role": "user",
                "content": [{"text": "Please provide additional critical investigation questions using tool calls."}]
            })
            process_model_response(conversation, recursion - 1)
        else:
            return

    process_model_response(conversation, MAX_RECURSIONS)
    return collected_questions


def create_questions_list(company_name: str, uuid, target_question_count: int = 2, max_recursions: int = 3) -> List[str]:
    """
    Generates due diligence questions for a company by having the model call a tool for each question.

    :param company_name: Name of the company.
    :param uuid: A unique identifier (for logging or tracking purposes).
    :param target_question_count: The desired number of due diligence questions to generate.
    :param max_recursions: The maximum number of recursive attempts.
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
        "operational risks, regulatory compliance, competitive landscape, growth strategy, and potential red flags. "
        "Always mention the company name explicitly in the question."
    )
    system_prompt = [{"text": system_prompt_text}]
    user_message_text = f"Generate separate due diligence questions for '{company_name}' using tool calls."
    conversation = [{"role": "user", "content": [{"text": user_message_text}]}]
    tool_config = {"tools": [get_question_tool_spec()]}
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    collected_questions: List[str] = []

    def process_model_response(conversation: List[Dict[str, Any]], recursion: int):
        if recursion <= 0:
            logging.warning("Max recursion reached; stopping further requests.")
            return

        try:
            response = invoke_converse_with_retries(
                client,
                modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0",
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
            # Continue recursion if we haven't yet reached the desired number of questions.
            if len(collected_questions) < target_question_count:
                process_model_response(conversation, recursion - 1)
        elif stop_reason != "end_turn" and len(collected_questions) < target_question_count:
            conversation.append({
                "role": "user",
                "content": [{"text": "Please provide additional due diligence questions using tool calls."}]
            })
            process_model_response(conversation, recursion - 1)
        else:
            return

    process_model_response(conversation, max_recursions)
    # Return only as many questions as requested.
    return collected_questions[:target_question_count]


def ask_question(input_query: str, company_name: str, uuid, depth) -> str:
    """
    Given an input query and company name, this function scrapes relevant pages,
    summarizes them, and uses the consolidated summaries as context to answer the question.
    
    :param input_query: The question to answer.
    :param company_name: The name of the company.
    :return: The answer text from the model.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    model_ids = ["us.amazon.nova-lite-v1:0"],  #"us.anthropic.claude-3-5-haiku-20241022-v1:0", 
    model_id = ""
    model_id = random.choice(model_ids[0])

    webscrap_result = webscrap(input_query)
    if not webscrap_result:
        logging.error("No webscrap results found.")
        return ""
    
    summaries = []
    #for title, (link, content) in webscrap_result.items():
    #    summary = summarize_page(title, link, content, client, uuid)
    #    summaries.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")
    #combined_summary = "\n\n".join(summaries)
    combined_summary = str(webscrap_result.items())

    if depth < 1:
        additional_questions = create_critical_investigation_questions(summaries, input_query, uuid)
        results_2 = process_questions(additional_questions, company_name, uuid, depth + 1)
    else:
        results_2 = []
    
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
        return [response_text, results_2]
    except Exception as e:
        logging.error(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


def process_questions(questions_list: List[str], company_name: str, uuid, depth) -> None:
    """
    Processes multiple questions concurrently using a thread pool.
    
    :param questions_list: List of questions to ask.
    :param company_name: The company name to include in the query.
    """
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_question = {
            executor.submit(ask_question, question, company_name, uuid, depth): question
            for question in questions_list
        }
        return_me_result = []
        for future in as_completed(future_to_question):
            question = future_to_question[future]
            try:
                result = future.result()
                #print(f"\nResults for question: '{question}'")
                #print(result)
                return_me_result.append({ "question" : question, "result" : result[0], "depth" : int(depth), "other_questions" : result[1] })
            except Exception as e:
                print(f"Exception for question '{question}': {str(e)}")
        return return_me_result

def generate_full_report(save_questions: List[Dict[str, Any]], company_name: str, uuid) -> str:
    """
    Generates a comprehensive due diligence and market analysis report based on the research data
    saved in save_questions.
    
    :param save_questions: A list of dictionaries containing due diligence questions and answers.
    :param company_name: The name of the company.
    :param uuid: Unique identifier (for logging or tracking purposes).
    :return: The full report as a text string.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    model_id = FINAL_MODEL_ID

    # Combine the research data from save_questions into a single string.
    research_data = ""
    for item in save_questions:
        question = item.get("question", "")
        answer = item.get("result", "")
        research_data += f"Question: {question}\nAnswer: {answer}\n\n"

    # Create instructions for the full report.
    report_instructions = (
        f"You are a seasoned financial analyst and market researcher. Based on the following due diligence and market research data for '{company_name}', "
        "generate a comprehensive due diligence and market analysis report. The report should include detailed analysis on financial performance, market position, "
        "management quality, operational risks, regulatory compliance, competitive landscape, growth strategy, and potential red flags. "
        "Ensure that the report is well-structured, thorough, and insightful.\n\n"
        f"Research Data:\n{research_data}"
    )
    report_instructions = (
        f"You are a seasoned financial analyst and market researcher. Based on the following due diligence and market research data for '{company_name}', "
        "generate a comprehensive due diligence and market analysis abstract for the report based on the data provided. The report should include detailed analysis on financial performance, market position, "
        "management quality, operational risks, regulatory compliance, competitive landscape, growth strategy, and potential red flags. "
        "Ensure that the report is well-structured, thorough, and insightful.\n\n"
        f"Research Data:\n{research_data}"
    )
    conversation = [{"role": "user", "content": [{"text": report_instructions}]}]

    try:
        response = invoke_converse_with_retries(
            client,
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 1024, "temperature": 0.5, "topP": 0.9},
        )
        full_report_text = response["output"]["message"]["content"][0]["text"]
        logging.info("Full report generated successfully.")
        return full_report_text.strip()
    except Exception as e:
        logging.error(f"Error generating full report: {e}")
        return "Error generating full report."

def enter_company_name(company_name: str, uuid="NONE", industry="NONE") -> None:
    """
    For a given company name, generates a list of due diligence questions and processes them.
    
    :param company_name: The name of the company.
    """
    # You may use a hard-coded list or dynamically generate one:
    questions_list = create_questions_list(company_name, uuid)
    save_questions = process_questions(questions_list, company_name, uuid, depth=1)
    full_report = generate_full_report(save_questions, company_name, uuid)
    return {"full report": full_report, "subquestions": save_questions}

# Example usage:
#print(enter_company_name("Millies Coffee and Creamery of Pittsburgh, PA", "1234"))
