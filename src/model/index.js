/**
 * @file 官方示例代码 - 模型调用示例集合
 * @description 本文件包含了通义千问API的标准调用示例，来源于官方文档。
 * @important 本文件为官方标准示例代码，请勿随意修改，以确保代码实现的规范性。
 */

// 模型ID为43f10f032fce4a52b8c40e3eb5a01c5d


API密钥为sk-f8dcf20a07ac4b889d74f56b7bf654e7
// 单轮对话示例
export const singleTurnDialog = `
import os
from http import HTTPStatus
from dashscope import Application
response = Application.call(
    # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    app_id='YOUR_APP_ID',# 替换为实际的应用 ID
    prompt='你是谁？')

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
    print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
else:
    print(response.output.text)
`;

// 多轮对话示例
export const multiTurnDialog = `
import os
from http import HTTPStatus
from dashscope import Application
def call_with_session():
    response = Application.call(
        # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        app_id='YOUR_APP_ID',  # 替换为实际的应用 ID
        prompt='你是谁？')

    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
        return response

    responseNext = Application.call(
                # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                app_id='YOUR_APP_ID',  # 替换为实际的应用 ID
                prompt='你有什么技能?',
                session_id=response.output.session_id)  # 上一轮response的session_id

    if responseNext.status_code != HTTPStatus.OK:
        print(f'request_id={responseNext.request_id}')
        print(f'code={responseNext.status_code}')
        print(f'message={responseNext.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
    else:
        print('%s\n session_id=%s\n' % (responseNext.output.text, responseNext.output.session_id))
        # print('%s\n' % (response.usage))

if __name__ == '__main__':
    call_with_session()
`;

// 流式输出示例
export const streamOutput = `
import os
from http import HTTPStatus
from dashscope import Application
responses = Application.call(
            # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
            api_key=os.getenv("DASHSCOPE_API_KEY"), 
            app_id='YOUR_APP_ID',
            prompt='你是谁？',
            stream=True,  # 流式输出
            incremental_output=True)  # 增量输出

for response in responses:
    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
    else:
        print(f'{response.output.text}\n')  # 处理只输出文本text
`;

// 检索知识库示例
export const knowledgeBaseQuery = `
import os
from http import HTTPStatus
# 建议dashscope SDK 的版本 >= 1.20.11
from dashscope import Application
response = Application.call(
    # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
    api_key=os.getenv("DASHSCOPE_API_KEY"), 
    app_id='YOUR_APP_ID',  # 应用ID替换YOUR_APP_ID
    prompt='请帮我推荐一款3000元以下的手机',
    rag_options={
        "pipeline_ids": ["YOUR_PIPELINE_ID1","YOUR_PIPELINE_ID2"],  # 替换为实际的知识库ID,逗号隔开多个
    }
)

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
    print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
else:
    print('%s\n' % (response.output.text))  # 处理只输出文本text
    # print('%s\n' % (response.usage))
`;

// 参数传递示例
export const parameterPassing = `
import os
from http import HTTPStatus
# 建议dashscope SDK 的版本 >= 1.14.0
from dashscope import Application
biz_params = {
    # 智能体应用的自定义插件输入参数传递，自定义的插件ID替换your_plugin_code
    "user_defined_params": {
        "your_plugin_code": {
            "article_index": 2}}}
response = Application.call(
        # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        app_id='YOUR_APP_ID',
        prompt='寝室公约内容',
        biz_params=biz_params)

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
    print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
else:
    print('%s\n' % (response.output.text))  # 处理只输出文本text
    # print('%s\n' % (response.usage))
`;

// 长期记忆示例
export const longTermMemory = `
# DashScope SDK版本不低于1.22.1
from http import HTTPStatus
import os
from dashscope import Application
response = Application.call(
           # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            app_id='YOUR_APP_ID',  # 请输入实际的应用 ID
            prompt='用户饮食偏好：面食',
            memory_id='YOUR_MEMORY_ID')  # 请输入实际的记忆体 ID

if response.status_code != HTTPStatus.OK:
    print(f'request_id={response.request_id}')
    print(f'code={response.status_code}')
    print(f'message={response.message}')
    print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
else:
    print('%s\n' % (response.output.text))  # 处理只输出text
    # print('%s\n' % (response.usage))
`;

// 上传文件示例
export const fileUpload = `
import os
from http import HTTPStatus
# 建议dashscope SDK 的版本 >= 1.20.14
from dashscope import Application
response = Application.call(
    # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
    api_key=os.getenv("DASHSCOPE_API_KEY"), 
    app_id='YOUR_APP_ID',  # 应用ID替换YOUR_APP_ID
    prompt='请根据以下文件帮我推荐一款3000元以下的手机'
);
`;