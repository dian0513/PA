from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'default_username'))
from rich import print as pprint
from db import select_part_v
import time
import json
import gradio as gr
import re

js = """
function createGradioAnimation() {

    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';
    container.style.color = 'blue';  

    var text = 'Part Chat';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 100);
        })(i);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    return 'Animation created';
}
"""

tool_outputs=[]
assistant_id_pa = os.getenv('assistant_id_pa', 'default_username')

def search_capacitor_part(**conditions):
    return str(select_part_v('0',**conditions))

def search_mosfet_part(**conditions):
    return str(select_part_v('1',**conditions))

# assistant = client.beta.assistants.create(
#   name="CP零件 AI助理_V2",
#   instructions="取得料號資訊並分析",
#   model="gpt-4o",
#   tools=tools
# )

tools = []

def history_process(history,fc):
    his_list = []
    for his in history:  # 只處理最新的五筆記錄
        his_list.append({"role": "user", "content": his[0]})
        his_list.append({"role": "assistant", "content": his[1]})
    if fc:
        his_list.append({"role": "user", "content": str(fc)})
    return his_list
def create_thread(message,his,fc):
    message = [{"role": "user", "content": message}]
    message = history_process(his,fc) + message
    thread = client.beta.threads.create(
        messages=message
    )
    return thread


def get_fuction_call(tool_calls):
    tool_outputs = []
    for i in tool_calls:
        print(i.function.name)

        func_args = json.loads(i.function.arguments)
        print(func_args)
        if i.function.name == "search_capacitor_part":
            output = search_capacitor_part(**func_args)
        elif i.function.name == "search_mosfet_part":
            output = search_mosfet_part(**func_args)
        else:
            output = {"status": "error", "message": "Unknown function"}

        tool_outputs.append({
            "tool_call_id": i.id,
            "output": output,
        })
    return tool_outputs

def process_event(event,thread):
    global tool_outputs
    print("function call")
    messages=''
    tool_calls = event.data.required_action.submit_tool_outputs.tool_calls
    run_id = event.data.id
    tool_outputs = get_fuction_call(tool_calls)
    try:
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=thread.id,
                run_id=run_id,
                tool_outputs=tool_outputs
        ) as stream:
            for event in stream:
                if event.event == "thread.message.delta":
                    message_delta = event.data.delta
                    for content_delta in message_delta.content:
                        if content_delta.type == "text" and content_delta.text:
                            content = content_delta.text.value
                            messages += content
                            clean_content = re.sub(r'【[^】]*】', '', messages)
                            yield clean_content
                if event.event == 'thread.run.requires_action':
                    yield from process_event(event, thread)

    except Exception as e:
        # print(e)
        yield f"Error: {str(e)}"


def fuctionCall(user_msg,history,assistant_id):
    global tool_outputs
    print(tool_outputs)
    messages = ''
    thread = create_thread(user_msg, history,tool_outputs)
    try:
        with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant_id,
        ) as stream:
            for event in stream:
                if event.event == "thread.message.delta":
                    message_delta = event.data.delta
                    for content_delta in message_delta.content:
                        if content_delta.type == "text" and content_delta.text:
                            content = content_delta.text.value
                            messages += content
                            clean_content = re.sub(r'【[^】]*】', '', messages)
                            yield clean_content
                if event.event == 'thread.run.requires_action':
                    yield from process_event(event, thread)
    except Exception as e:
        #print(e)
        yield f"Error: {str(e)}"



def wrapper_chat_bot(user_msg, history):
    yield from fuctionCall(user_msg, history, assistant_id)
def rungradio():
    demo = gr.ChatInterface(
        js=js,
        fn=wrapper_chat_bot,
        examples=["電容 330u 160v 有哪些料號?", "mosfet 600v 22a 有哪些料號? "],
        autofocus=True)
    demo.launch(server_name='0.0.0.0',server_port=9001)


rungradio()


