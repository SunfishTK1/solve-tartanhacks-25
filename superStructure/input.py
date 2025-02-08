import boto3
import logging
from enum import Enum

from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
#import utils.tool_use_print_utils as output
#import weather_tool
from webscrap import webscrap

logging.basicConfig(level=logging.INFO, format="%(message)s")

AWS_REGION = "us-east-1"

FINAL_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
# Model used for summarizing each scraped page.
SUMMARIZATION_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"  # Change if you have a dedicated summarization model.

MAX_TOKENS_SUMMARY = 2500

#print(webscrap("Crazy funny stories about peoples lunatic cats"))

def summarize_page(title, link, content, client):
    """
    Uses the Converse API to summarize the provided webpage content.
    The system prompt instructs the model to extract the most important points relevant to company analysis.
    """
    system_prompt = [
        {
            "text": (
                f"Summarize the following webpage content in a concise manner. The page title is '{title}' and its URL is {link}. "
                "Focus on extracting the most important details that would be useful for answering questions about the company."
            )
        }
    ]
    conversation = [
        {
            "role": "user",
            "content": [{"text": f"Content: {content}"}]
        }
    ]
    try:
        response = client.converse(
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
        # Fallback: return a truncated version of the content if summarization fails.
        return content[:500]

def create_critical_investigation_questions(scraped_sources, investigation_question):
    """
    Uses Amazon Bedrock's Converse API with tool calling to generate critical follow-up 
    investigation questions based on scraped webpage sources and an overall investigation question.
    
    The model is instructed to use a tool call (CriticalQuestion_Tool) for each question.
    Each tool call should have an input JSON with a field "question" containing one critical follow-up question.
    
    Parameters:
      - scraped_sources (list of str): List of text results scraped from webpages.
      - investigation_question (str): The overall investigation question previously being examined.
      
    Returns:
      - A list of critical follow-up questions (strings).
    """
    
    # --- Define a custom tool specification for a critical investigation question ---
    def get_critical_question_tool_spec():
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
    
    # --- Dummy tool invocation function for CriticalQuestion_Tool ---
    def invoke_critical_question_tool(payload):
        """
        In a production setting, this function would call an external service.
        For this demo, we simply echo the question provided by the model.
        """
        return {
            "toolUseId": payload.get("toolUseId"),
            "content": {
                "question": payload.get("input", {}).get("question", "")
            }
        }
    
    # --- Build the system prompt ---
    # Combine the scraped sources into a single text block.
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
    
    # --- Build the initial user message ---
    user_message_text = (
        f"Generate separate critical follow-up investigation questions for the overall question: "
        f"'{investigation_question}' using tool calls, based on the provided sources."
    )
    conversation = [{
        "role": "user",
        "content": [{"text": user_message_text}]
    }]
    
    # --- Define the tool configuration ---
    tool_config = {"tools": [get_critical_question_tool_spec()]}
    
    # Create a Bedrock Runtime client.
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    
    collected_questions = []
    MAX_RECURSIONS = 10  # To prevent infinite loops; adjust as needed.
    
    def process_model_response(conversation, recursion):
        # Use your preferred model ID.
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        if recursion <= 0:
            logging.warning("Max recursion reached; stopping further requests.")
            return
        
        try:
            response = client.converse(
                modelId=model_id,
                messages=conversation,
                system=system_prompt,
                toolConfig=tool_config
            )
        except Exception as e:
            logging.error(f"Error during converse call: {e}")
            return
        
        stop_reason = response.get("stopReason", "")
        # Treat the entire assistant response as one turn.
        assistant_message = response.get("output", {}).get("message", {})
        conversation.append(assistant_message)
        
        # Look for toolUse blocks in the assistant message.
        tool_uses = []
        for block in assistant_message.get("content", []):
            if "toolUse" in block:
                tool_uses.append(block["toolUse"])
        
        if tool_uses:
            # Build a single user message with exactly one toolResult block per toolUse block.
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
            user_tool_response = {
                "role": "user",
                "content": tool_result_contents
            }
            conversation.append(user_tool_response)
            process_model_response(conversation, recursion - 1)
        elif stop_reason != "end_turn" and len(collected_questions) < 5:
            # If the model ended its turn without any toolUse blocks but we still need more questions,
            # ask for additional questions.
            followup_message = {
                "role": "user",
                "content": [{"text": "Please provide additional critical investigation questions using tool calls."}]
            }
            conversation.append(followup_message)
            process_model_response(conversation, recursion - 1)
        else:
            return
    
    # Start processing the conversation.
    process_model_response(conversation, MAX_RECURSIONS)
    return collected_questions

def create_questions_list(company_name):
    """
    Uses Amazon Bedrock's Converse API with tool calling to have the model act as a
    financial analyst and generate separate due diligence questions for a given company.
    
    The model is instructed to use a tool call (Question_Tool) for each question. Each tool call
    should provide a JSON input with a field "question" containing one due diligence question.
    
    :param company_name: The name of the company for which to generate questions.
    :return: A list of questions (strings), or an empty list if none were generated.
    """
    
    # --- Define a custom tool specification for registering an individual question ---
    def get_question_tool_spec():
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
    
    # --- Dummy tool invocation: In production, this would call an external service.
    def invoke_question_tool(payload):
        return {
            "toolUseId": payload.get("toolUseId"),
            "content": {
                "question": payload.get("input", {}).get("question", "")
            }
        }
    
    # 1) Build the system prompt.
    system_prompt_text = (
        f"You are a highly experienced financial analyst. For the company '{company_name}', "
        "generate a list of due diligence questions. Do NOT output the questions as one block of text. "
        "Instead, for each question, call the 'Question_Tool' by issuing a tool call. "
        "Each tool call must have an input JSON with a field 'question' containing one due diligence question. "
        "Ensure that the questions cover areas such as financial performance, market position, management, "
        "operational risks, regulatory compliance, competitive landscape, growth strategy, and potential red flags."
    )
    system_prompt = [{"text": system_prompt_text}]
    
    # 2) Build the initial user message.
    user_message_text = f"Generate separate due diligence questions for '{company_name}' using tool calls."
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message_text}]
        }
    ]
    
    # 3) Define the tool configuration.
    tool_config = {"tools": [get_question_tool_spec()]}
    
    # Create a Bedrock Runtime client.
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    
    collected_questions = []
    MAX_RECURSIONS = 10 #was 10  # Maximum recursion depth to prevent infinite loops.
    
    def process_model_response(conversation, recursion):
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        if recursion <= 0:
            logging.warning("Max recursion reached; stopping further requests.")
            return
        
        try:
            response = client.converse(
                modelId=model_id,
                messages=conversation,
                system=system_prompt,
                toolConfig=tool_config
            )
        except Exception as e:
            logging.error(f"Error during converse call: {e}")
            return
        
        stop_reason = response.get("stopReason", "")
        # Treat the entire assistant message as one turn.
        assistant_message = response.get("output", {}).get("message", {})
        conversation.append(assistant_message)
        
        # Look for toolUse blocks in the assistant message.
        tool_uses = []
        for block in assistant_message.get("content", []):
            if "toolUse" in block:
                tool_uses.append(block["toolUse"])
        
        # If toolUse blocks exist, immediately respond with a matching user message.
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
            # IMPORTANT: The user message must contain exactly as many toolResult blocks as toolUse blocks.
            user_tool_response = {
                "role": "user",
                "content": tool_result_contents
            }
            conversation.append(user_tool_response)
            process_model_response(conversation, recursion - 1)
        
        # If no toolUse blocks and we haven't reached end_turn and 10 questions yet, ask for more.
        elif stop_reason != "end_turn" and len(collected_questions) < 10:
            followup_message = {
                "role": "user",
                "content": [{"text": "Please provide additional due diligence questions using tool calls."}]
            }
            conversation.append(followup_message)
            process_model_response(conversation, recursion - 1)
        else:
            # Either stop_turn or we have enough questions.
            return
    
    # Start the conversation processing.
    process_model_response(conversation, MAX_RECURSIONS)
    return collected_questions


def process_questions(questions_list, company_name):
    """
    Process multiple questions concurrently using ThreadPoolExecutor.
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit ask_question for each question in the list
        future_to_question = {executor.submit(ask_question, question, company_name): question 
                              for question in questions_list}
        
        # Process the results as they complete
        for future in as_completed(future_to_question):
            question = future_to_question[future]
            try:
                result = future.result()
                print(f"\nResults for question: '{question}'")
                print(result)
            except Exception as e:
                print(f"Exception for question '{question}': {str(e)}")


def ask_question(input_query, company_name):
    """
    This function prompts the user to enter the company name and asks the model to list out what the company does.
    """

    # Create a Bedrock Runtime client in the AWS Region you want to use.
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Set the model ID, e.g., Claude 3 Haiku.
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    company_name = company_name

    webscrap_result = webscrap(input_query)
    if not webscrap_result:
        logging.error("No webscrap results found.")
        return ""
    
    # Use the Converse API to summarize each scraped page.
    summaries = []
    for title, (link, content) in webscrap_result.items():
        summary = summarize_page(title, link, content, client)
        summaries.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")
    combined_summary = "\n\n".join(summaries)
    #combined_summary = webscrap_result
    
    # Build the final prompt that includes the consolidated summaries.
    user_message = (
        f"Answer the question: {input_query} about the company, {company_name}. "
        f"Use the following summarized web search results to inform your answer:\n\n{combined_summary}"
    )
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    try:
        # Send the message to the model, using a basic inference configuration.
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        print(response_text)
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

def enter_company_name(company_name):
    questions_list = ["Give an overview of the company", "Who are the companies customers", "What technology does the company have?", "Who are the companies competitors?"]
    questions_list = create_questions_list(company_name)
    process_questions(questions_list, company_name)

enter_company_name("Bank of Hawaii")
