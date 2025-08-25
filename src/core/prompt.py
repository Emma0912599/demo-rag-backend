"""提示词模板"""

TITLE_GENERATION_PROMPT = """
```\n{compact}\n```\n\n概括上文，只生成一句中文标题，不要标点符号，字数<=10：
"""

QUERY_REWRITE_PROMPT = """
将以下问题重构为更专业或学术化的表述，保留核心含义：\n
问题: {query}\n
请直接提供重构后的表述，不要附加解释。字数<=30。输出：
"""

RAG_ANSWER_PROMPT = """
```\n{context}\n```\n\n根据上下文信息，回答用户问题：
"""
