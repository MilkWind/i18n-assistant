 #!/usr/bin/env python3
"""
测试国际化键提取功能
"""

import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.pattern_utils import find_i18n_keys_in_text

def test_extraction():
    """测试从复杂的 $t() 调用中提取国际化键"""
    
    # 测试用例
    test_text = """{{ $t('generation.currentAttempt', { 
  current: generationsStore.generationProgress.currentAttempt, 
  max: generationsStore.generationProgress.maxRetries 
}) }}"""
    
    print("测试文本:")
    print(test_text)
    print("\n" + "="*50)
    
    # 调用提取函数
    results = find_i18n_keys_in_text(test_text)
    
    print(f"提取结果数量: {len(results)}")
    print("-" * 30)
    
    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"  键: '{result['key']}'")
        print(f"  行号: {result['line']}")
        print(f"  列号: {result['column']}")
        print(f"  匹配文本: '{result['match_text']}'")
        print(f"  开始位置: {result['start']}")
        print(f"  结束位置: {result['end']}")
        print()
    
    # 验证是否正确提取了目标键
    expected_key = 'generation.currentAttempt'
    found_keys = [result['key'] for result in results]
    
    print("验证结果:")
    if expected_key in found_keys:
        print(f"✅ 成功提取目标键: '{expected_key}'")
    else:
        print(f"❌ 未能提取目标键: '{expected_key}'")
        print(f"实际提取的键: {found_keys}")
    
    return results

def test_additional_cases():
    """测试其他复杂情况"""
    
    test_cases = [
        # 单行简单情况
        "$t('simple.key')",
        
        # 多行复杂参数
        """$t('complex.key', {
    param1: value1,
    param2: value2
})""",
        
        # 嵌套在Vue模板中
        """<div>{{ $t('nested.key', { count: items.length }) }}</div>""",
        
        # 多个键在同一文本中
        """
        $t('first.key')
        $t('second.key', { param: value })
        """,
        
        # 包含变量插值的键（应该被过滤掉）
        "$t(`dynamic.${variable}.key`)",
    ]
    
    print("\n" + "="*60)
    print("额外测试用例:")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"文本: {repr(test_case)}")
        
        results = find_i18n_keys_in_text(test_case)
        extracted_keys = [result['key'] for result in results]
        
        print(f"提取的键: {extracted_keys}")

if __name__ == "__main__":
    print("开始测试国际化键提取功能...")
    print("="*60)
    
    # 主要测试
    results = test_extraction()
    
    # 额外测试
    test_additional_cases()
    
    print("\n" + "="*60)
    print("测试完成!")