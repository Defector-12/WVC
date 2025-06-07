# 阿里云百炼API参考

## 凭证信息

```
# 应用ID 
43f10f032fce4a52b8c40e3eb5a01c5d

# 选用模型
qwen-plus-latest

# key
sk-fc310cd28bc74ff5be86913e3816f4d5

# Memory ID
e30ca0abc71549c28bc93586d3630430

# 业务空间ID
llm-crtlndfq40oj579k

# 知识库ID
didtamgrxs
ebnq5okz57
fc2ov71ytv
ihu3fyuhwk
s9gacm0ko0
```

## 接入方式

您可以通过本文默认的公网终端节点`https://dashscope.aliyuncs.com/api/v1/`访问百炼平台，也可以通过创建终端节点私网访问百炼平台，以提高数据传输的安全性及传输效率。

方法：将公网终端节点中的域名`dashscope.aliyuncs.com`替换为已经获取到的默认服务域名或自定义服务域名，
例如：`https://ep-2zei6917b47eed******.dashscope.cn-beijing.privatelink.aliyuncs.com/api/v1/`

## 代码示例

### 基础调用

```python
import os
from http import HTTPStatus
from dashscope import Application

response = Application.call(
    # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    app_id='43f10f032fce4a52b8c40e3eb5a01c5d',
    prompt='你是谁？')

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
    print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
else:
    print(response.output.text)
```

### 多轮对话

```python
import os
from dashscope import Generation
import dashscope

def get_response(messages):
    response = Generation.call(
        # 若没有配置环境变量，请用阿里云百炼API Key
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen-plus",
        messages=messages,
        result_format="message",
    )
    return response

# 初始化一个 messages 数组
messages = [
    {
        "role": "system",
        "content": """你是一名专业的海关术语翻译员，负责翻译海关相关专业术语。""",
    }
]

assistant_output = "欢迎使用海关术语翻译服务，请问您需要翻译什么术语？"
print(f"模型输出：{assistant_output}\n")

user_input = input("请输入：")
# 将用户问题信息添加到messages列表中
messages.append({"role": "user", "content": user_input})
assistant_output = get_response(messages).output.choices[0].message.content
# 将大模型的回复信息添加到messages列表中
messages.append({"role": "assistant", "content": assistant_output})
print(f"模型输出：{assistant_output}")
```

### 流式输出

```python
import os
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"), 
    app_id='43f10f032fce4a52b8c40e3eb5a01c5d',
    prompt='你是谁？',
    stream=True,  # 流式输出
    incremental_output=True)  # 增量输出

for response in responses:
    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
    else:
        print(f'{response.output.text}', end='')  # 处理只输出文本text
```

### 知识库检索

```python
import os
from http import HTTPStatus
from dashscope import Application

response = Application.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"), 
    app_id='43f10f032fce4a52b8c40e3eb5a01c5d',
    prompt='请帮我翻译海关术语',
    rag_options={
        "pipeline_ids": ["didtamgrxs", "ebnq5okz57", "fc2ov71ytv", "ihu3fyuhwk", "s9gacm0ko0"],
    }
)

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
else:
    print(response.output.text)
```

### 长期记忆

使用步骤：
1. 创建长期记忆体，获得唯一的memoryId
2. 保存对话信息，传入memoryId
3. 使用长期记忆进行对话，提供相同的memoryId

```python
from http import HTTPStatus
import os
from dashscope import Application

response = Application.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    app_id='43f10f032fce4a52b8c40e3eb5a01c5d',
    prompt='你好，请记住我是海关检查员',
    memory_id='e30ca0abc71549c28bc93586d3630430'  # 使用已创建的记忆ID
)

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
else:
    print(response.output.text)
```