from openai import OpenAI
client = OpenAI(api_key='KEY')
import time
import json
from IPython.display import HTML
# 在既有的討論串上繼續對談
def input_and_run(input, thread_id, assistant_id, **args):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=input,
        **args
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    return message, run
# 等待產生對話
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run
# 取得回覆的訊息, 也可指定只取得特定識別號碼之後的訊息
def get_response(thread_id, **args):
    return client.beta.threads.messages.list(
        thread_id=thread_id, order="asc", **args)
# 從工具函式表更新 assistant 的工具清單
def update_tools(ass_id, functions_table):
    tools = []
    for function in functions_table:
        tools.append(
            {"type": "function", "function": function['spec']}
        )
    client.beta.assistants.update(
        assistant_id=ass_id,
        tools=tools
    )
# 刪除過去測試過的同名 assistant
def delete_all_assistants(name):
    ids = []
    for assistant in client.beta.assistants.list():
        if assistant.name == name:
            ids.append(assistant.id)
    for id in ids:
        client.beta.assistants.delete(id)
# 根據模型的回覆, 幫你逐一呼叫個別函式
# 並蒐集結果為可以傳回給模型的串列
def call_tools(tool_calls, functions_table):
    outputs = []
    for tool in tool_calls:
        func_name = tool.function.name
        arguments = json.loads(tool.function.arguments)
        print(f'{func_name}({arguments})')
        for function in functions_table:
            if function['spec']['name'] == func_name:
                func = function['function']
                outputs.append({
                    'tool_call_id': tool.id,
                    'output': func(**arguments)
                })
                break
    return outputs
# 找出文件識別碼
def show_html(messages):
    # 找出有文件內容的對話物件
    index = len(messages.data) - 1
    # 找到文件位置
    file_index = messages.data[index].content[0].text.annotations

    if len(file_index) != 0:
        file_ids = file_index[0].file_path.file_id
        content = client.files.content(file_ids)
        # 儲存 HTML
        content.stream_to_file('test.html')
        # 顯示 HTML
        html_content = content.content.decode('utf-8')
        display(HTML(html_content))
