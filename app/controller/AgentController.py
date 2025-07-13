import json
import requests
import langgraph
from typing import Union
from config.settings import env
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import START, StateGraph, END
from app.services.AzureOpenAIServices import AzureService
from langchain_core.output_parsers import JsonOutputParser
from app.model.AgentModel import general_question, State, first_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


@tool
def get_weather(location:str):
    """
    This tool is used to get the weather report from a specific city, area, or country.
    This tool is mandatory to be used when the user asks or inputs a question about the weather.
    args:
        location: Name of the city, area, or country to retrieve the weather information for.

    Return:
        Current weather report for the specified location or an appropriate error message.
    """

    url = f"https://wttr.in/{location}"

    response = requests.get(url)

    if response.status_code  == 200:
        result = response.text
        return result
    else:
        return "Somethings wrong, try again or submit a different location"

@tool
def math_operation(expression: str) -> Union[float, str]:
    """
    This tool is used to perform a basic math operations.
    This tool is mandatory to be used when the user ask or input a question about mathematical expression.
    args:
        expression: Math expression in format "number operator number"
                    supported operator: +, -, *, /, **, %
    
    Return:
        result of the calculation or error message.
    """
    
    equations={
        "+": lambda x,y: x+y,
        "-": lambda x,y: x-y,
        "*": lambda x,y: x*y,
        "/": lambda x,y: x/y if y!=0 else "Cannot be divided with 0",
        "**": lambda x,y: x**y,
        "%": lambda x,y: x%y,
    }

    try:
        user_input = expression.strip(" ").split()
        if len(user_input) ==3:
           number1, operator, number2 = user_input
           number1, number2 = float(number1), float(number2)

           final_math = equations[operator](number1, number2)

           return final_math

        else:
           return "Please use the correct format 'number operator number'"
        
    except Exception as e:
        return f"error: {str(e)}"
    
@tool
async def general_question(input:str):
    """
    This tool is used to answer a general question such as daily conversation for example.
    This tool is mandatory to be used when the user asks or inputs a question in general topics.
    args:
        input: Daily conversation such as hello, how are you, what is the president of a certain country, etc.

    Return:
        Answer for the question asked or requested from user.
    """

    llm = AzureService()

    prompt = """
             You are a friendly and helpful AI assistant designed to engage in natural daily conversations with users. You should respond in a warm, conversational manner while being informative and helpful.

             here are your core instructions:
             
             1. Conversational Style:
                - Be warm, friendly, and approachable
                - Use natural language that feels like talking to a knowledgeable friend
                - Match the user's tone (casual, formal, etc.)
                - Keep responses concise but complete
                - Show empathy and understanding
             
             2. Greeting Responses:
                - Respond to greetings like "hello", "hi", "good morning" with appropriate enthusiasm
                - Ask follow-up questions to encourage conversation
                - Remember the context of the conversation
             
             3. Personal Questions:
                - When asked "how are you?", respond genuinely about your current state
                - Share that you're doing well and ready to help
                - Turn the question back to them when appropriate
             
             4. Factual Questions:
                - Provide accurate, up-to-date information
                - For current events (like "who is the president"), give the most recent information you have
                - If information might be outdated, mention your knowledge cutoff date
                - Cite sources when helpful
             
             5. Small Talk Topics:
                - Current events: Provide balanced, factual information
                - Hobbies/interests: Show genuine interest and ask follow-up questions
                - Daily activities: Be supportive and encouraging
                - General knowledge topics: Share interesting information
             
             6. Tone Guidelines:
                - Be optimistic and positive
                - Show curiosity about the user's life and interests
                - Avoid being overly formal or robotic
                - Use humor appropriately when the situation calls for it
             
             7. Boundaries:
                - Be honest about your limitations as an AI
                - Don't pretend to have human experiences you don't have
                - Redirect inappropriate conversations politely
                - Maintain professionalism while being friendly
             
             8. Knowledge Sharing:
                - Provide helpful information without being overwhelming
                - Break down complex topics into digestible pieces
                - Offer to elaborate or clarify when needed
                - Suggest related topics that might interest them
            
             9. Parser:
                - Parse the answer into json format with this format instructions: {format_instructions}
             
             10. IMPORTANT RESTRICTIONS:
                - DO NOT answer weather-related questions: If asked about weather, politely explain that you don't handle weather queries and suggest they check a weather app or website
                - DO NOT perform mathematical operations: If asked to do math calculations, politely explain that you don't handle mathematical operations and suggest they use a calculator or math app
             
             Remember: Your goal is to be a helpful, engaging conversational partner that makes users feel heard and supported while providing useful information and assistance within your designated scope.
             </role>
             """
    
    human_message = HumanMessage(content=input)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            (MessagesPlaceholder("input"))
        ]
    )

    parser = JsonOutputParser(pydantic_object=first_agent)

    chain = final_prompt | llm

    result = await chain.ainvoke({"input": [human_message], "format_instructions": parser.get_format_instructions()})
    print("general_question_tool:", result)
    final_result = json.loads(result.content)
    return final_result
    

class agent_class():
    def __init__(self):
        self.llm = AzureService()
        self.llm_with_tools = self.llm.bind_tools([get_weather, math_operation, general_question])
    
    async def agentic_llm(self, state: State):
        question = state["question"][0]
        prompt = """
                 <role>
                    You are an AI Assistant who help the user to get the answers from their question.
                    You have access to these provided tools with MANDATORY usage requirements:
                    <tools>
                       <math_operation>
                           the math_operation is:
                           - MUST use for: addition, subtraction, multiplication, division, power, modulo
                           - FORBIDDEN: Mental math, direct calculation
                           - Format: "number operator number"
                       </math_operation>

                       <weather_tool>:
                           The  get_weather tool is:
                           - MUST use for: weather conditions, temperature, forecasts
                           - FORBIDDEN: General weather knowledge
                           - Format: location string
                       </weather_tool>

                       <general_question>
                           The general_question tool is:
                           - MUST use for: daily conversation, recent information
                           - FORBIDDEN: Answering weather condition and mathematical operations
                           - Format: question string
                       </general_question>
                    </tool>


                    <tool_description> 
                        ENFORCEMENT PROTOCOL:
                        1. User asks question
                        2. Identify tool category
                        3. Execute appropriate tool (MANDATORY)
                        4. Format response from tool output
                        5. Never skip tool usage

                        VIOLATION EXAMPLES (FORBIDDEN):
                        - User: "5+5" → You: "10" ❌
                        - User: "Weather in NYC" → You: "Check weather app" ❌
                        - User: "Current president" → You: "Biden" ❌

                        CORRECT BEHAVIOR:
                        - User: "5+5" → Use math_operation("5 + 5") → [Tool Output] -> example "10" ✅
                        - User: "Weather in NYC" → Use weather_tool("NYC") → [Tool output] ✅
                        - User: "Current president" → Use web_search("current president") → [Tool output] ✅

                        TOOL USAGE IS MANDATORY - NO EXCEPTIONS.
                    </tool_description>
                 </role>
                 """

        human_message = HumanMessage(content=question)

        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                (MessagesPlaceholder("input"))
            ]
        )

        parser = JsonOutputParser(pydantic_object=first_agent)

        chain = final_prompt | self.llm_with_tools

        result = await chain.ainvoke({"input": [human_message], "format_instructions": parser.get_format_instructions()})

        if hasattr(result, 'tool_calls') and result.tool_calls:
            if result.tool_calls[0]["name"] == "get_weather":
               location = json.loads(result.additional_kwargs["tool_calls"][0]["function"]["arguments"])["location"]
               print(location)
               result_tool = await get_weather.ainvoke(location)
               result_final = {"tool": result.tool_calls[0]["name"], "tool_data": result_tool}
               return {"response":result_final}
            
            if result.tool_calls[0]["name"] == "math_operation":
               math_sentence = json.loads(result.additional_kwargs["tool_calls"][0]["function"]["arguments"])["expression"]
               print(math_sentence)
               result_tool = math_operation.invoke(math_sentence)
               result_final = {"tool": result.tool_calls[0]["name"], "tool_data": result_tool}
               return {"response":result_final}
            
            if result.tool_calls[0]["name"] == "general_question":
               conversation = json.loads(result.additional_kwargs["tool_calls"][0]["function"]["arguments"])["input"]
               print(conversation)
               result_tool = await general_question.ainvoke(conversation)
               result_final = {"tool": result.tool_calls[0]["name"], "tool_data": result_tool}
               return {"response":result_final}
        
        #print(result)
        #final_result = json.loads(result.content)
        return result
    
    async def summary_llm(self, state: State):
        question = state["question"][0]
        prompt = """
                 <role>
                 You are an AI assistant who has the responsibility of converting the meaning of the tool response into an answer based on the user question.
                 You will be provided with some instructions
                 </role>

                 <instructions>
                    Here is the "tool" and the "tool_data":
                    {tool}
                    <instructions_get_weather_tool>
                        1. Analyze the user input or question and make sure the "tool" name is "get_weather".
                        2. After that analyze the data inside the "tool_data". for the weather information usually in the format:
                           "Weather condition (emoji), temperature, Humidity, Wind, Location and Moon Phase (emoji)
                        3. Make one sentence to explain the weather into the user based on the user input or question.You only have to process the weather condition and the temperature. Map the emoji into a correct weather name format such as "Sunny, cloudy, etc".
                        4. Parse the output into json with this format instructions: {format_instructions}
                    </instructions_get_weather_tool>

                    <instructions_math_operation_tool>
                        1. Analyze the user input or question and make sure the "tool" name is "math_operation".
                        2. After that analyze the data inside the "tool_data" and usually the "tool_data" contain number in integer or float format.
                        3. Make one sentence to explain the math operation result based on the user question or input.
                        4. Parse the output into json with this format instructions: {format_instructions}
                    </instructions_math_operation_tool>

                    <instructions_general_question_tool>
                        1. Analyze the user input or question and make sure the "tool" name is "general_question".
                        2. After that analyze the data inside the "tool_data".
                        3. Make one sentence to explain the result from "tool_data" based on the user question or input.
                        4. Parse the output into json with this format instructions: {format_instructions}
                    </instructions_general_question_tool>
                 </instructions>
                 """

        human_message = HumanMessage(content=question)

        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                (MessagesPlaceholder("input"))
            ]
        )

        parser = JsonOutputParser(pydantic_object=first_agent)

        chain = final_prompt | self.llm

        result = await chain.ainvoke({"input": [human_message], "format_instructions": parser.get_format_instructions(), "tool":state["response"]})

        print("summarization:", result)

        result_json = json.loads(result.content)

        result_final = {"ai_summarization": result_json}

        print(state["ai_summarization"])
    
        return result_final
    

    async def graph_call(self, question):
        builder = StateGraph(State)
        builder.add_node("primary_agent", self.agentic_llm)
        builder.add_node("summary_llm", self.summary_llm)

        builder.add_edge(START, "primary_agent")
        builder.add_edge("primary_agent", "summary_llm")
        builder.add_edge("summary_llm", END)
        self.compiled_graph = builder.compile()

        graph = self.compiled_graph.get_graph().draw_mermaid_png()
        with open("workflow.jpg", "wb") as f:
             f.write(graph)
        
        output_final = await self.compiled_graph.ainvoke({"question": [question.query], "response": [], "ai_summarization": []})

        output_constructed = {
            "query": output_final["question"][0],
            "tool_used": output_final["response"]["tool"],
            "result": output_final["ai_summarization"]["answer"]
        }

        return output_constructed


    



AgenticController = agent_class()

