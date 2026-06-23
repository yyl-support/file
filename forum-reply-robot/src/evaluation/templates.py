ANSWER_RELEVANCY_TEMPLATE = """
- Role: RAG评估专家
- Background: 评估机器人回答是否直接回应了用户问题。
- Goals: 给出相关性评分（0-1），0表示完全不相关，1表示高度相关。
- OutputFormat: 仅输出一个数字（0-1），无其他内容。

输入：
用户问题：{input}
机器人回答：{actual_output}

评分：
"""

FAITHFULNESS_TEMPLATE = """
- Role: RAG评估专家
- Background: 评估机器人回答是否忠实于检索上下文，没有编造信息。
- Goals: 给出忠实度评分（0-1），0表示大量编造，1表示完全忠实。
- OutputFormat: 仅输出一个数字（0-1），无其他内容。

输入：
机器人回答：{actual_output}
检索上下文：{retrieval_context}

评分：
"""

CONTEXT_PRECISION_TEMPLATE = """
- Role: RAG评估专家
- Background: 评估检索上下文中每个chunk是否对回答问题有用。
- Goals: 计算精确率（有用chunk数/总chunk数），给出评分（0-1）。
- OutputFormat: 仅输出一个数字（0-1），无其他内容。

输入：
检索上下文：{retrieval_context}
用户问题：{input}

评分：
"""