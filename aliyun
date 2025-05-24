# 应用ID 
43f10f032fce4a52b8c40e3eb5a01c5d


# 选用模型
qwen-plus-latest

# key
sk-fc310cd28bc74ff5be86913e3816f4d5


您可以通过本文默认的公网终端节点https://dashscope.aliyuncs.com/api/v1/访问百炼平台，也可以通过创建终端节点私网访问百炼平台，以提高数据传输的安全性及传输效率。
方法：将公网终端节点中的域名dashscope.aliyuncs.com替换为已经获取到的默认服务域名或自定义服务域名，
例如：https://ep-2zei6917b47eed******.dashscope.cn-beijing.privatelink.aliyuncs.com/api/v1/

import os
from http import HTTPStatus
from dashscope import Application
# 配置私网终端节点
os.environ['DASHSCOPE_HTTP_BASE_URL'] = 'https://ep-2zei6917b47eed******.dashscope.cn-beijing.privatelink.aliyuncs.com/api/v1/'
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