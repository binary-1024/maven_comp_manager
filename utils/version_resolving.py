import re
from maven_repo import MavenRepo
# from ghsa_info import get_all_versions
from .log import My_logger
logger = My_logger(logger_name="version_resolving").get_logger()

## 这个排序用于比较 预发布版本用, 放在这里比放在全局变量那边好一些
## 因为这个变量只应该在这里使用
pre_release_order = {
    'dev': 10,              # 开发阶段（Development）
    'incubating': 20,       # 试验中的项目
    'pre-alpha': 30,        # 开发初期，尚未进入 Alpha 测试
    'alpha': 40,            # Alpha 阶段，用于内部测试
    'beta': 50,             # 功能完整但不稳定的测试版
    'ea': 60,               # 早期访问版
    'rc': 70,               # 候选版本（Release Candidate）
    'gamma': 80,            # 接近最终发布的小幅调整版
    'preview': 100,          # 预览版
    'pre': 100,              # 准备发布版本（Pre-Release）
    'pr': 100,
    'snapshots': 110,
    'snapshot': 110,         # 快照版（每日构建）
    'nightly': 120,          # 每夜构建版本
    'post': 130,             # 发布后的修订版本（Post-Release）
    'rev': 140,             # 修订版（Revision）
    'milestone': 150,       # 里程碑版本（Milestone）
    'ga': 160,              # 一般可用版（General Availability）
    'final': 990,           # 最终版（Final Release）
    'release': 990,         # 正式发布版本（Release）
    'sp': 9990,              # 安全发布版本（Security Patch）
    'lts': 990,             # 长期支持版本（Long-Term Support）
    'rtm': 990,              # 制造商交付版本（Release to Manufacturing）
    'a': 40,                # Alpha 的简写
    'e': 60,                # 预览版
    'b': 50,                # Beta 的简写
    't': 30,                # 技术功能测试预览版
    'c': 60,                # RC 的简写
    'cr': 60,               # 候选版本的另一种标识
    'r': 140,               # 修订版的简写
    'm': 150,               # 里程碑版本（Milestone）
}

# 可以删掉标识符的版本号
release_keywords = ['final', 'release', 'lts', 'rtm']

# 热补丁版本标识符, 后续如果有别的那么添加
hot_path_keywords = {
    "H":1,
    "h":1
}

strip_character = [
    'v', 
    'i',
    'update',
    'build'
]

## 版本号数位区隔符
VERSION_NUMBER_SEPARATOR = [
    '-', # 1-2-3
    '.', # 1.2.3
    '_', # 1_2_3
    '~', # 1~2~3
    '+', # 1.0.0+build.31
    '/', # 1/2/3
    ':' # 1:2:3
]

def is_hash_string(s: str) -> bool:
    """
    检查字符串是否可能是哈希值（只包含十六进制字符）
    """
    # 去除字符串两端的空白字符
    s = s.strip()
    # 如果字符串为空，返回 False
    if not s:
        return False
    # 检查是否只包含十六进制字符
    try:
        # 尝试将字符串转换为十六进制数
        int(s, 16)
        return True
    except ValueError:
        return False

def compare_version_digits(version1: str, version2: str) -> int:
    """
    比较两个归一化后的版本号
    规则：
    1. 从左到右比较每一位
    2. 前三位正常比较大小
    3. 从第四位开始,如果其中一个是0,则0大于其他数值
    4. 如果第四位都不是0,则正常比较
    Args:
        version1: 第一个版本号（已归一化，用点号分隔）
        version2: 第二个版本号（已归一化，用点号分隔）
    Returns:
        -1: version1 < version2
        0:  version1 == version2
        1:  version1 > version2
    """
    v1_parts = version1.split('.')
    v2_parts = version2.split('.')
    
    # 确保两个版本号长度相同
    max_length = max(len(v1_parts), len(v2_parts))
    v1_parts.extend(['0'] * (max_length - len(v1_parts)))
    v2_parts.extend(['0'] * (max_length - len(v2_parts)))
    
    # 逐位比较
    for i in range(max_length):
        try:
            num1 = int(v1_parts[i])
            num2 = int(v2_parts[i])
        except Exception as e:
            logger.warning(f"bad cases, compare version digits {e}")
            if v1_parts[i] == v2_parts[i]:
                continue
            else:
                raise Exception(f"bad cases, compare version digits {e} {v1_parts[i]}, {v2_parts[i]}")
        
        # 前三位正常比较
        if i < 3 or i > 4:
            if num1 < num2:
                return -1
            if num1 > num2:
                return 1
            continue
            
        # 从第四位开始的特殊比较
        if num1 != num2:
            # 如果其中一个是0
            if num1 == 0:
                return 1  # 0 大于其他数值
            if num2 == 0:
                return -1  # 0 大于其他数值
            # 都不是0则正常比较
            return -1 if num1 < num2 else 1
        
    return 0  # 所有位都相等



# 精确匹配
def exact_match(version_str_, all_tags_):
    '''
    精确匹配, 如果 version_str_ 在 all_tags_ 中, 那么就返回 True, 并且返回 index
    如果 version_str_ 不在 all_tags_ 中, 那么就返回 False, 并且返回 None
    '''
    
    if version_str_ in all_tags_:
        index = all_tags_.index(version_str_)
        logger.info(f"{version_str_} exactly match in original tags {all_tags_[index]}")
        return True, index
    return False, None

# 前缀匹配
def prefix_match(version_str_, all_tags_):
    '''
    前缀匹配, 如果 version_str_ 在 all_tags_ 中存在前缀一致的情况, 那么就返回 True, 并且返回 index列表
    如果 version_str_ 不在 all_tags_ 中, 那么就返回 False, 并且返回 None
    '''
    prefix_match_tag = [ tag for tag in all_tags_ if tag.startswith(version_str_) ]
    if len(prefix_match_tag) == 0:
        logger.warning(f"{version_str_} not matched in all tags")
        return False, None
    else:
        logger.warning(f"{version_str_} found multiple matches in tags with followed order {prefix_match_tag[0]} {prefix_match_tag[-1]}")
        return True, prefix_match_tag

# 补位 padding 0 
def ljust_dot_zero(str_:str, max_dot_count_):
    '''
    按照 max_dot_count_ 来对齐 str_ 的 "." 号数量, 如果 str_ 的 "." 号数量小于 max_dot_count_ 那么就补充 ".0"
    '''
    if str_[-1] == '.':
        # 如果最后一个字符是 "." 那么我们就要去掉最后一个 "." 然后开始补充
        str_ = str_[:-1]
    existing_dot_count = str_.count('.')
    while(existing_dot_count < max_dot_count_):
        str_ += '.0'
        existing_dot_count += 1
    return str_

# 分割版本号和后缀
def split_version_and_suffix(tag: str) -> tuple:
    '''
    分割版本号和后缀
    比如 3.5.6-rc1 那么返回的版本号就是 3.5.6 后缀就是 -rc1
    比如 3.5.6 那么返回的版本号就是 3.5.6 后缀就是 ''
    比如 34_687_123 那么返回的版本号就是 34 后缀就是 _687_123
    '''
    pattern = '0123456789.'
    # 查找第一个非数字和点的位置
    for i, char in enumerate(tag):
        if char not in pattern:
            return tag[:i], tag[i:]
    return tag, ''


def remove_prefix(tag: str):
    '''
    移除 tag 中的 prefix
    '''
    # 如果tag 整个是一个关键字 那么 不移除
    if tag in pre_release_order.keys():
        return tag
    
    # 移除我们确定的那种
    for character in strip_character:
        tag = tag.removeprefix(character)
    return tag

# 切分版本号和预发布版本
def split_version_and_pre_release(tag: str):
    '''
    如果 tag 中存在预发布版本标识, 并且前或或者后面存在连续数字, 那么就在数字和预发布版本号之间加一个点
    '''
    parts = tag.split('.')
    tag = ""
    for part in parts:
        part = remove_prefix(part)
        # 是否是纯数字
        if part.isdigit():
            tag += part+'.'
            continue
        # 如果是空那么久过
        if part == '':
            continue
        # 看看是否是哈希值
        if is_hash_string(part):
            tag += part+'.'
            continue
        # 如果 预发布版本标识存在于 part 则判断 part 的前后是否是数字
        # 但是如果是 简写例如 beta 是 'b', 如果判断 b 是否存在是有着多种字符都存在 b, 先筛掉其他情况将简称放在最后
        # 此外还要判断是不是 只有简称+数字 还是中间还掺杂着其他字符
        tmp_part = part
        flag = False
        for pre_release_identifier in pre_release_order.keys():
            # if part == "preview":
            #     logger.warning(f"[-] preview is not a valid pre-release identifier")
            # 如果发现 pre_release_identifier 存在于 part 中, 那么就进行处理
            if pre_release_identifier in part:
                indentifier_index = part.index(pre_release_identifier)
                # 如果标识在最前面, 那么检查后面剩下的字符是否是数字
                if pre_release_identifier == part:
                    logger.debug(f"[+] part is only pre-release identifier, {part}")
                    flag = True
                    break

                if indentifier_index == 0:
                    if part[len(pre_release_identifier):].isdigit():    
                        tmp_part = f"{pre_release_identifier}.{part[len(pre_release_identifier):]}"
                        logger.debug(f"[+] processed tag: {tag}")
                        flag = True
                        break
                    # 这个是最特殊的情况,有可能开头是个别的东西呢
                    else:
                        left_part = part[len(pre_release_identifier):]
                        split_left_part = split_version_and_pre_release(left_part)
                        tmp_part = pre_release_identifier + '.' + split_left_part
                        if split_left_part == left_part:
                            logger.warning(f"[-] unkown case in split_version_and_pre_release to fix, {part} is not a valid pre-release version")
                        else:
                            flag = True
                            break

                # 如果标识存在于最后面, 那么检查前面剩下的字符是否是数字
                elif indentifier_index == len(part)-len(pre_release_identifier):
                    if part[:-len(pre_release_identifier)].isdigit():
                        tmp_part = f"{part[:-len(pre_release_identifier)]}.{pre_release_identifier}"
                        logger.debug(f"[+] processed tag: {tag}")
                        flag = True
                        break
                # 如果存在于中间, 那么检查前后是否是数字
                else:
                    if part[:indentifier_index].isdigit() and part[indentifier_index+len(pre_release_identifier):].isdigit():
                        tmp_part = f"{part[:indentifier_index]}.{pre_release_identifier}.{part[indentifier_index+len(pre_release_identifier):]}"
                        logger.debug(f"[+] processed tag: {tag}")
                        flag = True
                        break    

        # 循环结束, 可能是找到 keyword 加点之后直接跳出来的, 也可能是自然结束没有进行任何处理
        # 我们需要多加一个逻辑, 
        if not flag:
            logger.warning(f"[-] unkown case in split_version_and_pre_release to fix, {part} is not a valid pre-release version")

        tag += tmp_part+'.'
        logger.debug(f"[+] processed tag: {tag}")
    return tag.removesuffix('.')

def is_pre_identifier_plus_number(input_str: str):
    # 如果 input_str 是纯数字, 那么就返回 True
    if input_str.isdigit():
        return input_str
    # 如果 input_str 是纯 pre release identifier, 那么就返回 True
    if input_str in pre_release_order.keys():
        return input_str
     
    # case1 如果 input_str 是 pre release identifier + 数字, 那么就返回 True
    pattern = rf'({"|".join(pre_release_order.keys())})(\d+)'
    tmp = re.sub(pattern, r'\1.\2', input_str, flags=re.IGNORECASE)
    tmp_list = tmp.split('.')
    if len(tmp_list) > 1:
        return tmp_list[0] + '.' + tmp_list[1] 
    
    # case2 如果是哈希值那也可以过
    if is_hash_string(input_str):
        return input_str
    
    # case3 如果 input_str 是一堆字母+数字, 此外后面不包含任何东西 那么用.来分割这俩
    pattern = r'([a-zA-Z]+)(\d+)'
    tmp = re.sub(pattern, r'\1.\2', input_str, flags=re.IGNORECASE)
    tmp_list = tmp.split('.')
    if len(tmp_list) > 1:
        return tmp_list[0] + '.' + tmp_list[1]

    return False

def strip_prefix_part(part: str):
    '''
    处理一下每一个 part
    '''
    # 是不是标识符开头的那种
    parsed_result = is_pre_identifier_plus_number(part)
    # 如果识别到了 纯(标识符|数字)这种组和我们就直接返回
    if parsed_result:
        if '.' in parsed_result:
            parts_ = parsed_result.split('.')
            return '.'.join([strip_prefix_part(part_) for part_ in parts_ if part_ != '' or part_ != None])
        else:
            return parsed_result
    # 处理那种 数字+标识符的情况
    # pattern = r'\d+(' + '|'.join(pre_release_order.keys()) + ')'
    pattern = rf'(\d+)({"|".join(pre_release_order.keys())})'
    tmp = re.sub(pattern, r'\1.\2', part, flags=re.IGNORECASE)
    tmp_list = tmp.split('.')
    # 如果 tmp_list 长度大于 1 那么就说明有处理过
    if len(tmp_list) > 1:
        return tmp_list[0] + '.' + strip_prefix_part(tmp_list[1])
    
    # 如果还惨杂着其他无法识别的字符那么过滤处理
    for character in strip_character:
        if part.startswith(character):
            tmp = part.removeprefix(character)
            break
    
    # 如果过滤掉了那就返回空
    if tmp == '':
        return ''
    
    # 写一个递归调用, 如果 tmp 和 part 不相等那么就继续递归调用删除前缀
    if tmp != part:
        tmp = strip_prefix_part(tmp)
    return tmp


# 切分版本号和预发布版本
def split_version_and_pre_release_v2(tag: str):
    '''
    如果 tag 中存在预发布版本标识, 并且前或或者后面存在连续数字, 那么就在数字和预发布版本号之间加一个点
    优先级排序: 
        - 纯数字, 纯 pre release identifier, 纯 pre release identifier + 数字 
        - 过滤关键字 + 上述情况, 不优先过滤关键字的原因是 容易将 pre release identifier 破坏掉
    '''
    # 首先用.分割
    parts = tag.split('.')
    # 输出字符串
    out_tag = ""
    # 遍历每个字段处理
    for index, part in enumerate(parts):
        # 处理的开头是特殊字符的情况
        tmp = strip_prefix_part(part)
        # 如果遇到了整段都是可过滤文字那么过
        if tmp is None or tmp == '':
            continue
        out_tag += tmp + '.'
        # 
    return out_tag.removesuffix('.')

    
        

    #     part = remove_prefix(part)
    #     # 是否是纯数字
    #     if part.isdigit():
    #         tag += part+'.'
    #         continue
    #     # 如果是空那么久过
    #     if part == '':
    #         continue
    #     # 看看是否是哈希值
    #     if is_hash_string(part):
    #         tag += part+'.'
    #         continue
    #     # 如果 预发布版本标识存在于 part 则判断 part 的前后是否是数字
    #     # 但是如果是 简写例如 beta 是 'b', 如果判断 b 是否存在是有着多种字符都存在 b, 先筛掉其他情况将简称放在最后
    #     # 此外还要判断是不是 只有简称+数字 还是中间还掺杂着其他字符
    #     tmp_part = part
    #     flag = False
    #     for pre_release_identifier in pre_release_order.keys():
    #         # if part == "preview":
    #         #     logger.warning(f"[-] preview is not a valid pre-release identifier")
    #         # 如果发现 pre_release_identifier 存在于 part 中, 那么就进行处理
    #         if pre_release_identifier in part:
    #             indentifier_index = part.index(pre_release_identifier)
    #             # 如果标识在最前面, 那么检查后面剩下的字符是否是数字
    #             if pre_release_identifier == part:
    #                 logger.debug(f"[+] part is only pre-release identifier, {part}")
    #                 flag = True
    #                 break

    #             if indentifier_index == 0:
    #                 if part[len(pre_release_identifier):].isdigit():    
    #                     tmp_part = f"{pre_release_identifier}.{part[len(pre_release_identifier):]}"
    #                     logger.debug(f"[+] processed tag: {tag}")
    #                     flag = True
    #                     break
    #                 # 这个是最特殊的情况,有可能开头是个别的东西呢
    #                 else:
    #                     left_part = part[len(pre_release_identifier):]
    #                     split_left_part = split_version_and_pre_release(left_part)
    #                     tmp_part = pre_release_identifier + '.' + split_left_part
    #                     if split_left_part == left_part:
    #                         logger.warning(f"[-] unkown case in split_version_and_pre_release to fix, {part} is not a valid pre-release version")
    #                     else:
    #                         flag = True
    #                         break

    #             # 如果标识存在于最后面, 那么检查前面剩下的字符是否是数字
    #             elif indentifier_index == len(part)-len(pre_release_identifier):
    #                 if part[:-len(pre_release_identifier)].isdigit():
    #                     tmp_part = f"{part[:-len(pre_release_identifier)]}.{pre_release_identifier}"
    #                     logger.debug(f"[+] processed tag: {tag}")
    #                     flag = True
    #                     break
    #             # 如果存在于中间, 那么检查前后是否是数字
    #             else:
    #                 if part[:indentifier_index].isdigit() and part[indentifier_index+len(pre_release_identifier):].isdigit():
    #                     tmp_part = f"{part[:indentifier_index]}.{pre_release_identifier}.{part[indentifier_index+len(pre_release_identifier):]}"
    #                     logger.debug(f"[+] processed tag: {tag}")
    #                     flag = True
    #                     break    

    #     # 循环结束, 可能是找到 keyword 加点之后直接跳出来的, 也可能是自然结束没有进行任何处理
    #     # 我们需要多加一个逻辑, 
    #     if not flag:
    #         logger.warning(f"[-] unkown case in split_version_and_pre_release to fix, {part} is not a valid pre-release version")

    #     tag += tmp_part+'.'
    #     logger.debug(f"[+] processed tag: {tag}")
    # return tag.removesuffix('.')

# 对齐主版本号：如果存在三位数字版本，则将其他版本也补齐到三位
def align_major_version(all_tags: list, force_align: bool = False) -> list:
    """
    对齐主版本号：
    - 如果非强制对齐: 至少存在一个 tag 是 三位数字版本并且以.来分割 则返回原来的版本号以及 False 标签, 如果不存在那么强制对齐
    - 如果是强制对齐: 则返回对齐后的版本号以及 True 标签
    Args:
        all_tags: 所有版本号的列表
        force_align: 是否强制对齐, 如果为 True 那么就强制对齐, 如果为 False 那么就只对齐三位数字版本
    Returns:
        处理后的版本号列表
    """
    # 如果 force_align 为 False,
    if not force_align:
        # 检查是否存至少一个在三位数字版本并且是以'.' 分割的
        has_three_parts = any(len(tag.split('.')) >= 3 and 
                              tag.split('.')[0].isdigit() and 
                              tag.split('.')[1].isdigit() and 
                              tag.split('.')[2].isdigit()
                            for tag in all_tags)
        # 如果没有任何一个这种情况, 那么就返回原来的版本号以及 False 标签
        if not has_three_parts:
            return all_tags, False
    
    # 如果 force_align 为 True 或者 all_tags 里面没有三位数字版本 那么就强制对齐
    aligned_tags = []
    for tag in all_tags:
        # 这里应该加一个切分数字和预发布版本的东西
        normal_version = split_version_and_pre_release(tag)
        # 找到 预发布版本号标识符, 然后切分
        version, suffix = split_version_and_suffix(normal_version)
        # 按照.分割 part
        parts = version.split('.')
        parts = [part.strip() for part in parts if part != '']
        
        # 如果 part 小于 3, 即 主版本号不是三位, 那么对主版本就补充 0
        if len(parts) < 3:
            parts.extend(['0'] * (3 - len(parts)))
            
        # 重新组合版本号
        aligned_tag = '.'.join(parts) +'.'+suffix if suffix != '' else '.'.join(parts)
        aligned_tags.append(aligned_tag)
    # 这样起码保证了 主版本号都是 数字.数字.数字+后缀
    return aligned_tags, True

# 版本归一化
def normalize_version(version_str_, all_tags_):
    '''
    归一化, 根据 all_tags 来归一化 version_str_
    - 对齐主版本号为 数字.数字.数字, 
    - 替换预发布版本号为数字, 
    - .数量不一致的情况, 对齐.数量, 补充 0
    '''
    # 找出并替换预发布版本标识
    def replace_word(version_str):
        # 匹配连续的英文字符
        def replace_match(match):
            word = re.match(r'[a-zA-Z]+', match.group(0)).group(0)  # 只取字母部分
            may_numbers = match.group(0)[len(word):]
            # 如果这个单词在pre_release_order中，就替换成对应的值
            # 从 may_numbers 中试图捕获数字, 如果捕获到了 那么在前面加一个点
            match_number = re.match(r'\d+', may_numbers)
            if match_number:
                numbers = match_number.group(0)
                may_numbers = may_numbers[len(numbers):]
                may_numbers = '.' + numbers + may_numbers
            else:
                logger.debug(f"[-] cannot catch number in {may_numbers}")
            return str(pre_release_order.get(word, word)) + may_numbers            
        # 使用正则表达式匹配连续的英文字符
        return re.sub(r'[a-zA-Z]+\d*', replace_match, version_str)

    def get_version_parts(tag: str) -> tuple:
        """获取版本号的数字部分作为排序键"""
        parts = tag.split('.')
        # 转换前三位为数字（如果存在）
        nums = []
        for part in parts[:3]:
            try:
                nums.append(int(part))
            except ValueError:
                nums.append(0)
        # 补充到三位
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums)

    # 先都转换成小写, 并且删除掉以'v'开头的版本号
    normalized_version_str = version_str_.lower().removeprefix('v')
    normalized_all_tags = [tag.lower().removeprefix('v') for tag in all_tags_]
    
    # release_keywords 列表中的预发布版本号如果存在 删掉 因为这个和 没有一样
    for keyword in release_keywords:
        if normalized_version_str.endswith(keyword):
            normalized_version_str = normalized_version_str.removesuffix(keyword)
        normalized_all_tags = [tag.removesuffix(keyword) if tag.endswith(keyword) else tag for tag in normalized_all_tags]

    # 跟我我们统计的区隔符号, 替换成 .
    for separator in VERSION_NUMBER_SEPARATOR:
        normalized_version_str = normalized_version_str.replace(separator, '.')
        normalized_version_str = normalized_version_str.removesuffix('.')
        normalized_all_tags = [tag.replace(separator, '.').removesuffix('.') for tag in normalized_all_tags]

    
    # 对齐主版本号, 如果我确认 alltags 里面有存在前三位是数字, 那么我就要将所有的 tag 都换成前三位是数字
    normalized_all_tags, aligned_flag = align_major_version(normalized_all_tags, force_align=False)
    # 如果 aligned_flag 为 True 那么就说明 all_tags 里面有存在前三位是数字, 那么我就要将 normalized_version_str 也按照前三位数字来排序
    if aligned_flag:
        normalized_version_str, _ = align_major_version([normalized_version_str], force_align=True)
        normalized_version_str = normalized_version_str[0]
        # 如果我确认 alltags 里面有存在前三位是数字, 那么我就要将all_tags 也按照前三位数字来排序
        # normalized_all_tags = sorted(normalized_all_tags, key=get_version_parts, reverse=True)
    
    # 只替换预发布版本标识
    normalized_version_str = replace_word(normalized_version_str)
    normalized_all_tags = [replace_word(tag) for tag in normalized_all_tags]

    # TODO 如果是 有些版本号内容带 哈希 比如 123_6b5a_, 即除了预发布版本以外的字符还会留下

    # 对齐"."号的数量, 首先看 all_tags 中最大的点号数量, 然后再看 version_str_ 和 刚刚的最大点号数量谁最大
    max_dot_in_all_tags = max([len(tag.split('.')) for tag in all_tags_])
    max_dot_in_version_str = len(normalized_version_str.split('.'))
    max_dot_count = max(max_dot_in_all_tags, max_dot_in_version_str)
    
    # 根据 max_dot_count 来对齐 version_str_ 和 all_tags_ 中每个元素的 "." 号数量.
    # 对齐策略就是向右补充"."的时候也要加 0, 比如 1.3.5 -> 1.3.5.0
    normalized_version_str = ljust_dot_zero(normalized_version_str, max_dot_count)
    normalized_all_tags = [ljust_dot_zero(tag, max_dot_count) for tag in normalized_all_tags]
    return normalized_version_str, normalized_all_tags

# 找所有的版本中第一个小于 version_str_ 的版本, 找 top boundary的时候用
# 已经做好开闭区间预处理了
def find_first_lt_eq(normalized_all_tags_, normalized_version_str_, start_inclusive):
    # all_tags_本身就是一个 从高到低排序后的数据
    # 从高到低找到第一个小于 version_str_ 的版本, 如果没找到就默认用最后一个 index 
    try:
        for index, tag in enumerate(normalized_all_tags_):
            if compare_version_digits(tag, normalized_version_str_) == 0:
                return index if start_inclusive else index - 1
            if compare_version_digits(tag, normalized_version_str_) < 0:
                # 由于 开闭区间的问题, 如果闭区间要返回上一个, 开区间要返回本身到时候-1 才会是上一个
                # 更正一下吧, 开闭区间, 对于比较大小的匹配来说不重要, 但是对于 相等的情况确实重要
                # return index-1 if start_inclusive else index
                # 这种情况, 已经在比较值右边了, 不需要在+或者-处理了
                return index - 1
        # 如果没找到, 即全都大于 version_str_ 那么就返回最后一个的 index
        return len(normalized_all_tags_) - 1
    except Exception as e:
        logger.error(f"[-] bad cases in find_first_lt_eq {e}")
        raise e

# 找所有的版本中最后一个大于 version_str_ 的版本, 找 bottom boundary的时候用
# 已经做好开闭区间预处理了
def find_first_gt_eq(normalized_all_tags_, normalized_version_str_, end_inclusive):
    # all_tags_本身就是一个 从高到低排序后的数据
    # 从高到低找到第一个小于等于 version_str_ 的版本
    try:
        for index, tag in enumerate(normalized_all_tags_):
            if compare_version_digits(tag, normalized_version_str_) == 0:
                return index if end_inclusive else index + 1
            if compare_version_digits(tag, normalized_version_str_) < 0:
                # 由于 开闭区间的问题, 闭区间无所谓, 开区间的话要-1 到时候+1 才会返回本身值
                # 这种情况 tag 是在 目标值右边的, 所以要减一到左边
                return index
        # 如果没找到, 即全都大于 version_str_, 那就是有问题了... 报错
        logger.error(f"[-] bad cases in find_first_gt_eq, all tags are greater than {normalized_version_str_}")
        raise Exception(f"[-] bad cases in find_first_gt_eq, all tags are greater than {normalized_version_str_}")
    except Exception as e:
        logger.error(f"[-] bad cases in find_first_gt_eq {e}")
        raise e


'''版本比较逻辑
第一优先级: 精确匹配: 当start_version 和 end_version 都是精确匹配的时候, 那么直接返回 这两个 index 之间的版本号
第二优先级: 包含匹配: 当start_version 和 end_version 都是包含匹配的时候, 这意味着肯定不是纯数字的情况, 那么分场景.
    背景: 一般主要用于区分版本号的字符有 ".", "-", "_", 这些字符存在于版本号的话, 那么我们就要分位数和非位数. 
    例如 1.3.3 和 4.5.6. 或者 3.5-rc1 和 4.5-rc2 或者 3.5.9 和 3.5.6-RC1 这种.
    一般来说 前三位数字代表的是 主版本, 副版本 和 修订版本, 从第四位开始则是 里程碑版本, 或者 特殊版本.
    这些里程碑字符优先级排序存放在 pre_release_order 变量中.
    如果 start_version 和 end_version 都是包含匹配, 那么我们就要分位数和非位数.
    例如 3.5.6-RC1 和 3.5.6-RC2 这种, 那么我们就要分位数和非位数.
第三优先级: 数位匹配
'''
def get_all_tags_in_range(start_version, end_version, all_tags_, artifact_id=None):
    if all_tags_ == [] or all_tags_ == None:
        logger.error(f"[-] {artifact_id} all_tags is None or empty")
        return ["error"]
    # 获取 版本字符串和是否包含信息
    start_version_str, start_inclusive = start_version
    end_version_str, end_inclusive = end_version
    # 加一个处理 如果end_version是 (None, _) 就是 表达式为 >, 或者 >= 的情况 我们要报错的
    if end_version_str == "None":
        logger.error(f"[-] {artifact_id} end version is None, please check the affected exp")
        raise Exception(f"[-] {artifact_id} end version is None, please check the affected exp")
    
    # all_tags中元素顺序是 [高版本-> 低版本] 
    affected_versions=[]
    start_exact_flag = False
    end_exact_flag = False
    all_tags = [tag.lower() for tag in all_tags_]
    all_tags = all_tags[::-1]
    all_tags_reverse = all_tags_[::-1]
    start_version_str = start_version_str.lower() if start_version_str != "None" else start_version_str
    end_version_str = end_version_str.lower() if end_version_str != "None" else end_version_str
    
    # ---------------------------------- main body -----------------------------------------------------------
    
    # 不可能存在 受影响范围 >xxx 的情况 只存在 <xxx 这种情况所以提前设置一下
    # 如果 start_version_str 是 "None", 意味着 版本比较 exp 是 "< xxx 或者 <= xxx" 形式的
    if start_version_str == "None":
        start_index = len(all_tags) - 1   # 使用最低版本
        logger.debug(f"[{artifact_id}] start version {start_version_str} not found, Using lowest version {all_tags[-1]} in all tags")
    # 否则 start_version_str 是 版本号, 那么我们就要精确匹配 low boundary
    else:
        start_index = None
        return_start_index = None
        ## 开始匹配 start_index
        try:
            # 精确匹配
            logger.info(f"[{artifact_id}] entry 1 start try exact matching")
            start_exact_flag, return_start_index = exact_match(start_version_str, all_tags)
            # 如果精确匹配没有找到, 那么就使用数位匹配, 比较大小
            if not start_exact_flag:
                # 这个要归一化所有的数位区隔符
                logger.info(f"[{artifact_id}] entry 2 start try normalized exact matching")
                normalized_start_version_str, normalized_all_tags = normalize_version(start_version_str, all_tags)
                # 然后精确匹配一下
                start_exact_flag, return_start_index = exact_match(normalized_start_version_str, normalized_all_tags)
                # 如果精确匹配没有找到, 归一化后的数据不需要前缀匹配了, 那么就使用数位匹配
                # 由于已经归一化过了, 所以数位匹配就是从左到右的比较每一位的大小
                if not start_exact_flag:
                    logger.info(f"[{artifact_id}] entry 3 start try normalzed comparing")
                    try:
                        # 从高到低找到第一个小于 start_version_str 的版本
                        # 如果没找到, 说明全部都大于 start_version_str, 那就用最小的那个大于 start_version_str 的版本
                        return_start_index = find_first_lt_eq(normalized_all_tags, normalized_start_version_str, start_inclusive)
                        # start_exact_flag = True
                    except Exception as e:
                        logger.warning(f"[{artifact_id}] bad cases, find first less than {e}, try prefix match")
                        return_start_index = None
            # # 前缀匹配 有可能不准, 先保守处理
            # if return_start_index is None:
            #     logger.info(f"[{artifact_id}] entry 4 start try normalzed prefix matching")
            #     prefix_match_flag, prefix_match_tag = prefix_match(start_version_str, all_tags)
            #     if prefix_match_flag:
            #         # 作为 bottom 边界, prefix_match_tag如果有多个, 用第一个会准可能会漏, 用最后一个不会漏可能不准
            #         return_start_index = prefix_match_tag[0]
            #         logger.info(f"[{artifact_id}] {start_version_str} match with prefix tags {all_tags[return_start_index]} in multi tags")
            #         start_exact_flag = True
                
            # 各种没有 matching 到
            if return_start_index is None:
                logger.error(f"[{artifact_id}] start version {start_version_str} not found in all tags")
                return ['error']
            
            # 收尾的时候判断一下, 开闭区间, 这里的方法会影响find_first_lt_eq中给的结果, 要注意
            # 如果精确匹配且包含, 那么
            # 不精确比较的情况, 让返回值必须小于一个, 这边才好做
            if not start_exact_flag:
                start_index = return_start_index
            # 精确比较的情况
            elif start_inclusive:
                start_index = return_start_index 
            else:
                start_index = return_start_index - 1 
            
            # 如果找到了还返回 0 就说明 有问题, 他提供的 all_tags 与 漏洞边界匹配 有问题
            if start_index < 0 or start_index >= len(all_tags) or start_index is None:
                logger.error(f"[{artifact_id}] bad cases, start version {start_version_str} found in all tags, but not satisfy the affected exp, need check")
                return ["error"]
        
        except Exception as e:
            logger.error(f"bad cases, start version not found in tags {e}")
            return ["error"]
    # -----------------------------------------------------------#
    ## 开始匹配 end_index
    try:
        # 精确匹配
        end_index = None
        logger.info(f"[{artifact_id}] entry 1 end try exact matching")
        end_exact_flag, return_end_index = exact_match(end_version_str, all_tags)
        # 如果精确匹配没有找到, 那么就使用数位匹配
        if not end_exact_flag:
            # 这个要归一化所有的数位区隔符
            logger.info(f"[{artifact_id}] entry 2 end try normalized exact matching")
            normalized_end_version_str, normalized_all_tags = normalize_version(end_version_str, all_tags)
            # 然后精确匹配一下
            end_exact_flag, return_end_index = exact_match(normalized_end_version_str, normalized_all_tags)
            
            # 如果精确匹配没有找到, 归一化后的数据不需要前缀匹配了, 那么就使用数位匹配
            # 给刚刚匹配到的边界做一个处理, 这个要和精确匹配不同, 这里的return_end_index 是第一个大于 end_version_str 的 index
            if not end_exact_flag:
                logger.info(f"[{artifact_id}] entry 3 end try normalzed comparing")
                try:
                    # 从高到低找到第一个大于 end_version_str 的版本, 如果没找到就默认用第一个 index 
                    return_end_index = find_first_gt_eq(normalized_all_tags, normalized_end_version_str, end_inclusive)
                except Exception as e:
                    logger.warning(f"bad cases, find first greater than {e}, try prefix match")
                    return_end_index = None
        # # 前缀匹配可能不准, 先保守一波.
        # if return_end_index is None:
        #     logger.info(f"[{artifact_id}] entry 4 end try prefix match")
        #     prefix_match_flag, prefix_match_tag = prefix_match(end_version_str, all_tags)
        #     if prefix_match_flag:
        #         # 作为end 的边界, 我尽可能用最后一个保证准确性
        #         return_end_index = prefix_match_tag[-1]
        #         logger.info(f"{end_version_str} match with prefix tags {all_tags_reverse[return_end_index]} in multi tags")
        #         end_exact_flag = True
        
        if return_end_index is None:
            logger.error(f"[{artifact_id}] end version {end_version_str} not found in all tags")
            return ["error"]
        
        # 收尾的时候判断一下, 开闭区间, 这里的方法会影响find_first_gt_eq中给的结果, 要注意
        # 没找到精确的情况, 返回本身 + 1
        if not end_exact_flag:
            end_index = return_end_index
        # 找到精确地, 并且是闭区间, 那么就返回本身
        elif end_inclusive:
            end_index = return_end_index
        # 找到精确地, 但是是开区间, 那么就 + 1
        else:
            end_index = return_end_index + 1
        
        # 最后一层防火墙
        if end_index < 0 or end_index >= len(all_tags) or end_index is None:
            logger.error(f"[{artifact_id}] bad cases, end version {end_version_str} found in all tags, but not satisfy the affected exp, need check")
            return ['error']
        
    except Exception as e:
        logger.error(f"[{artifact_id}] bad cases, end version not found in tags {e}")
        return ['error']
    # 到此为止应该已经解析完版本了, 如果有 end_exact_flag 和 start_exact_flag 为 TRUE 说明找到了边界版本
    # 但是有些边界是包含的, 有些是不包含的, 我们在上面已经区分了这些. 所以我们得到的 index 已经是都该包含的了
    # 所以接下来我们只需要根据 start_index 和 end_index 来获取版本范围
    try:
        if start_index == end_index:
            affected_versions = [all_tags_reverse[start_index]]
        elif end_index > start_index:
            logger.error(f"[{artifact_id}] bad cases, start_index {end_index} is greater than end_index {start_index}")
            return ["error"]
            
        else:
            # 这是最正常的情况
            # affected_versions = all_tags[start_index:end_index+1]
            if start_index <= len(all_tags_reverse)-1:
                affected_versions = all_tags_reverse[end_index:start_index+1]
            else:
                affected_versions = all_tags_reverse[end_index:]
        logger.info(f"[{artifact_id}] finish get affected versions normally")
        return affected_versions
    
    except Exception as e:
        logger.error(f"[{artifact_id}] bad cases, get affected versions {e}, {start_index} {end_index}, affected_versions {affected_versions}")
        return ['error']
# ------------------------------------------------------------------------------------------------
# 解析 版本号
def parse_version(version):
    # 去掉版本号前面的比较符号和空格
    return re.sub(r'^[<>=~^]+\s*', '', version).strip()

# 解析 版本范围的 boundary 用户后续的比较
def parse_affected_versions(affected_versions_exp):
    
    parts = affected_versions_exp.split(',')
    
    start_version = ("None", True)  # (version, is_inclusive)
    end_version = ("None", False)
    
    for part in parts:
        part = part.replace(' ', '')
        if part.startswith('<='):
            end_version = (parse_version(part), True)
        elif part.startswith('<'):
            end_version = (parse_version(part), False)
        elif part.startswith('>='):
            start_version = (parse_version(part), True)
        elif part.startswith('>'):
            start_version = (parse_version(part), False)
        elif part.startswith('='):
            version = parse_version(part)
            start_version = (version, True)
            end_version = (version, True)
        else:
            version = parse_version(part)
            start_version = (version, True)
            end_version = (version, True)
    
    return start_version, end_version



# 通过 ga 和 漏洞边界表达式 来获取受影响的版本
def get_affected_versions_for_test(group_id, artifact_id, vulnerablie_exp):
    # 获取 ga 的所有 maven 版本
    logger.info(f"[+] get_affected_versions start for {group_id}:{artifact_id}:{vulnerablie_exp}")
    mr = MavenRepo(group_id, artifact_id)
    all_tags = mr.get_all_vers_from_ga()
    if all_tags is None or all_tags == []:
        logger.error(f"[-] {group_id}:{artifact_id} versions not found")
        return None
    logger.info(f"[+] all tags: {all_tags}")
    tag_list = []
    # 先都转换成小写, 并且删除掉以'v'开头的版本号
    normalized_all_tags = [tag.lower().removeprefix('v') for tag in all_tags]
    # 跟我我们统计的区隔符号, 替换成 .
    for separator in VERSION_NUMBER_SEPARATOR:
        normalized_all_tags = [tag.replace(separator, '.') for tag in normalized_all_tags]
    logger.info(f"[+] normalized all tags: {normalized_all_tags}")
    # 然后对每个 tag 进行版本预处理标识的处理
    for tag in normalized_all_tags:
        # 分割版本和预发布版本
        processed_tag = split_version_and_pre_release_v2(tag)
        #
        # if processed_tag not in tag_list:
        tag_list.append(processed_tag)
    
    logger.info(f"[+] processed tag list: {tag_list}")
    if len(tag_list) != len(normalized_all_tags):
        logger.error(f"[-] {group_id}:{artifact_id} versions not unique")
        return None
    return tag_list




# def get_all_tags_in_range_v2(start_version, end_version, all_tags_, artifact_id=None):
    # 如果 all_tags_ 是空, 或者 None, 那么就返回 error
#     if all_tags_ == [] or all_tags_ == None:
#         raise Exception(f"[-] {artifact_id} all_tags is None or empty")
#     # 获取 版本字符串和是否包含信息
#     start_version_str, start_inclusive = start_version
#     end_version_str, end_inclusive = end_version
#     # 加一个处理 如果end_version是 (None, _) 就是 表达式为 >, 或者 >= 的情况 我们要报错的
#     if end_version_str == "None":
#         raise Exception(f"[-] {artifact_id} end version is None, please check the affected exp")
#     # all_tags中元素顺序是 [高版本-> 低版本] 
#     affected_versions=[]
#     start_exact_flag = False
#     end_exact_flag = False
#     all_tags = [tag.lower() for tag in all_tags_]
#     all_tags = all_tags[::-1]
#     all_tags_reverse = all_tags_[::-1]
#     start_version_str = start_version_str.lower() if start_version_str != "None" else start_version_str
#     end_version_str = end_version_str.lower() if end_version_str != "None" else end_version_str
#     # 到这边就是基本变量设置结束
#     # ---------------------------------- main body -----------------------------------------------------------
#     # 如果 start_version_str 是 "None", 意味着 版本比较 exp 是 "< xxx 或者 <= xxx" 形式的
#     if start_version_str == "None":
#         start_index = len(all_tags) - 1   # 使用最低版本
#         logger.debug(f"[{artifact_id}] start version {start_version_str} not found, Using lowest version {all_tags[-1]} in all tags")
#     # 否则 start_version_str 是 版本号, 那么我们就要精确匹配 low boundary
#     else:
#         start_index = None
#         ## 开始匹配 start_index
#         try:
#             # 精确匹配
#             logger.info(f"[{artifact_id}] entry 1 start try exact matching")
#             start_exact_flag, return_start_index = exact_match(start_version_str, all_tags)
#             # 如果精确匹配没有找到, 那么就使用数位匹配, 比较大小
#             if not start_exact_flag:
#                 # 这个要归一化所有的数位区隔符
#                 logger.info(f"[{artifact_id}] entry 2 start try normalized exact matching")
#                 normalized_start_version_str, normalized_all_tags = normalize_version(start_version_str, all_tags)
#                 # 然后精确匹配一下
#                 start_exact_flag, return_start_index = exact_match(normalized_start_version_str, normalized_all_tags)
#                 # 如果精确匹配没有找到, 归一化后的数据不需要前缀匹配了, 那么就使用数位匹配
#                 # 由于已经归一化过了, 所以数位匹配就是从左到右的比较每一位的大小
#                 if not start_exact_flag:
#                     logger.info(f"[{artifact_id}] entry 3 start try normalzed comparing")
#                     try:
#                         # 从高到低找到第一个小于 start_version_str 的版本
#                         # 如果没找到, 说明全部都大于 start_version_str, 那就用最小的那个大于 start_version_str 的版本
#                         return_start_index = find_first_lt_eq(normalized_all_tags, normalized_start_version_str, start_inclusive)
#                         start_exact_flag = True
#                     except Exception as e:
#                         logger.warning(f"[{artifact_id}] bad cases, find first less than {e}, try prefix match")

#             # 前缀匹配 有可能不准, 先保守处理
#             if not start_exact_flag:
#                 logger.info(f"[{artifact_id}] entry 4 start try normalzed prefix matching")
#                 prefix_match_flag, prefix_match_tag = prefix_match(start_version_str, all_tags)
#                 if prefix_match_flag:
#                     # 作为 bottom 边界, prefix_match_tag如果有多个, 用第一个会准可能会漏, 用最后一个不会漏可能不准
#                     return_start_index = prefix_match_tag[0]
#                     logger.info(f"[{artifact_id}] {start_version_str} match with prefix tags {all_tags[return_start_index]} in multi tags")
#                     start_exact_flag = True
                
#             # 各种没有 matching 到
#             if not start_exact_flag:
#                 logger.error(f"[{artifact_id}] start version {start_version_str} not found in all tags")
#                 return []
            
#             # 收尾的时候判断一下, 开闭区间, 这里的方法会影响find_first_lt_eq中给的结果, 要注意
#             if start_inclusive:
#                 start_index = return_start_index
#             else:
#                 start_index = return_start_index - 1
            
#             # 如果找到了还返回 0 就说明 有问题, 他提供的 all_tags 与 漏洞边界匹配 有问题
#             if start_index < 0 or start_index >= len(all_tags) or start_index is None:
#                 logger.error(f"[{artifact_id}] bad cases, start version {start_version_str} found in all tags, but not satisfy the affected exp, need check")
#                 return ["error"]
        
#         except Exception as e:
#             logger.error(f"bad cases, start version not found in tags {e}")
#             return ["error"]
#     # -----------------------------------------------------------#
#     ## 开始匹配 end_index
#     try:
#         # 精确匹配
#         end_index = None
#         logger.info(f"[{artifact_id}] entry 1 end try exact matching")
#         end_exact_flag, return_end_index = exact_match(end_version_str, all_tags)
#         # 如果精确匹配没有找到, 那么就使用数位匹配
#         if not end_exact_flag:
#             # 这个要归一化所有的数位区隔符
#             logger.info(f"[{artifact_id}] entry 2 end try normalized exact matching")
#             normalized_end_version_str, normalized_all_tags = normalize_version(end_version_str, all_tags)
#             # 然后精确匹配一下
#             end_exact_flag, return_end_index = exact_match(normalized_end_version_str, normalized_all_tags)
#             # 如果精确匹配没有找到, 归一化后的数据不需要前缀匹配了, 那么就使用数位匹配
#             # 给刚刚匹配到的边界做一个处理, 这个要和精确匹配不同, 这里的return_end_index 是第一个大于 end_version_str 的 index
#             if not end_exact_flag:
#                 logger.info(f"[{artifact_id}] entry 3 end try normalzed comparing")
#                 try:
#                     # 从高到低找到第一个大于 end_version_str 的版本, 如果没找到就默认用第一个 index 
#                     return_end_index = find_first_gt_eq(normalized_all_tags, normalized_end_version_str, end_inclusive)
#                     end_exact_flag = True
#                 except Exception as e:
#                     logger.warning(f"bad cases, find first greater than {e}, try prefix match")

#         # 前缀匹配可能不准, 先保守一波.
#         if not end_exact_flag:
#             logger.info(f"[{artifact_id}] entry 4 end try prefix match")
#             prefix_match_flag, prefix_match_tag = prefix_match(end_version_str, all_tags)
#             if prefix_match_flag:
#                 # 作为end 的边界, 我尽可能用最后一个保证准确性
#                 return_end_index = prefix_match_tag[-1]
#                 logger.info(f"{end_version_str} match with prefix tags {all_tags_reverse[return_end_index]} in multi tags")
#                 end_exact_flag = True
        
#         if not end_exact_flag:
#             logger.error(f"[{artifact_id}] end version {end_version_str} not found in all tags")
#             return ["error"]
        
#         # 收尾的时候判断一下, 开闭区间, 这里的方法会影响find_first_gt_eq中给的结果, 要注意
#         if end_inclusive:
#             end_index = return_end_index
#         else:
#             end_index = return_end_index + 1
        
#         # 最后一层防火墙
#         if end_index < 0 or end_index >= len(all_tags) or end_index is None:
#             logger.error(f"[{artifact_id}] bad cases, end version {end_version_str} found in all tags, but not satisfy the affected exp, need check")
#             return []
        
#     except Exception as e:
#         logger.error(f"[{artifact_id}] bad cases, end version not found in tags {e}")
#         return ['error']
#     # 到此为止应该已经解析完版本了, 如果有 end_exact_flag 和 start_exact_flag 为 TRUE 说明找到了边界版本
#     # 但是有些边界是包含的, 有些是不包含的, 我们在上面已经区分了这些. 所以我们得到的 index 已经是都该包含的了
#     # 所以接下来我们只需要根据 start_index 和 end_index 来获取版本范围
#     try:
#         if start_index == end_index:
#             affected_versions = [all_tags_reverse[start_index]]
#         elif end_index > start_index:
#             logger.error(f"[{artifact_id}] bad cases, start_index {end_index} is greater than end_index {start_index}")
#             return ["error"]
            
#         else:
#             # 这是最正常的情况
#             # affected_versions = all_tags[start_index:end_index+1]
#             affected_versions = all_tags_reverse[end_index:start_index+1] if start_index <= len(all_tags_reverse)-1 else all_tags_reverse[end_index:]
#         logger.info(f"[{artifact_id}] finish get affected versions normally")
#         return affected_versions
    
#     except Exception as e:
#         logger.error(f"[{artifact_id}] bad cases, get affected versions {e}, {start_index} {end_index}, affected_versions {affected_versions}")
#         return []


if __name__ == "__main__":
    print('release' in pre_release_order.keys())
    pass