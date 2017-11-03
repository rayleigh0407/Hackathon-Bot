import re
RE_langconv = re.compile(r'(-\{|\}-)')

def convert_for_mw(s, locale, update=None):
    ch = []
    nested = 0
    tmp = ''
    for frag in RE_langconv.split(s):
        if frag == '-{':
            tmp += frag
            nested += 1
        elif frag == '}-':
            tmp += frag
            if nested:
                nested -= 1



def convert_for_mw(s, locale, update=None):
    ch = []
    pos = 0
    length = len(s)
    while pos < length:
        index = s.find('-{', pos)
        if index == -1:
            ch.append((s[pos:], 'a'))
            break
        ch.append((s[pos:index], 'a'))
        lookahead = pos = index
        nested = 1
        while nested:
            match = RE_langconv.search(s, lookahead)
            if match is None:
                break
            elif match.group(0) == '-{':
                nested += 1
                print('nested', nested)
                lookahead = match.end(0)
                continue
            else:
                nested -= 1
                print('nested', nested)
                lookahead = match.end(0)
        else:
            pos = lookahead+2
            print('got:', s[index:pos])
            ch.append((s[index:pos], 'b'))
            continue
        print('Got:', s[index:])
        ch.append(convert_for_mw(s[index:] + '}-'*nested))
        break
        ch.append((frag, 'c'))
    return ch







def convert_for_mw(s, locale, update=None):
    """
    Recognizes MediaWiki's human conversion format.
    Use locale='zh' for no conversion.

    Reference: (all tests passed)
    https://zh.wikipedia.org/wiki/Help:%E9%AB%98%E7%BA%A7%E5%AD%97%E8%AF%8D%E8%BD%AC%E6%8D%A2%E8%AF%AD%E6%B3%95
    https://www.mediawiki.org/wiki/Writing_systems/Syntax

    >>> print(convert_for_mw('在现代，机械计算-{}-机的应用已经完全被电子计算-{}-机所取代', 'zh-hk'))
    在現代，機械計算機的應用已經完全被電子計算機所取代
    >>> print(convert_for_mw('-{zh-hant:資訊工程;zh-hans:计算机工程学;}-是电子工程的一个分支，主要研究计算机软硬件和二者间的彼此联系。', 'zh-tw'))
    資訊工程是電子工程的一個分支，主要研究計算機軟硬體和二者間的彼此聯繫。
    >>> print(convert_for_mw('張國榮曾在英國-{zh:利兹;zh-hans:利兹;zh-hk:列斯;zh-tw:里茲}-大学學習。', 'zh-hant'))
    張國榮曾在英國里茲大學學習。
    >>> print(convert_for_mw('張國榮曾在英國-{zh:利兹;zh-hans:利兹;zh-hk:列斯;zh-tw:里茲}-大学學習。', 'zh-sg'))
    张国荣曾在英国利兹大学学习。
    >>> print(convert_for_mw('毫米(毫公分)，符號mm，是長度單位和降雨量單位，-{zh-hans:台湾作-{公釐}-或-{公厘}-;zh-hant:港澳和大陸稱為-{毫米}-（台灣亦有使用，但較常使用名稱為毫公分）;zh-mo:台灣作-{公釐}-或-{公厘}-;zh-hk:台灣作-{公釐}-或-{公厘}-;}-。', 'zh-tw'))
    毫米(毫公分)，符號mm，是長度單位和降雨量單位，港澳和大陸稱為毫米（台灣亦有使用，但較常使用名稱為毫公分）。
    >>> print(convert_for_mw('毫米(毫公分)，符號mm，是長度單位和降雨量單位，-{zh-hans:台湾作-{公釐}-或-{公厘}-;zh-hant:港澳和大陸稱為-{毫米}-（台灣亦有使用，但較常使用名稱為毫公分）;zh-mo:台灣作-{公釐}-或-{公厘}-;zh-hk:台灣作-{公釐}-或-{公厘}-;}-。', 'zh-cn'))
    毫米(毫公分)，符号mm，是长度单位和降雨量单位，台湾作公釐或公厘。
    """
    ch = []
    rules = []
    ruledict = update.copy() if update else {}
    nested = 0
    block = ''
    for frag in RE_langconv.split(s):
        if frag == '-{':
            nested += 1
            block += frag
        elif frag == '}-':
            block += frag
            nested -= 1
            if nested:
                continue
            newrules = []
            delim = RE_splitflag.split(block[2:-2].strip(' \t\n\r\f\v;'))
            if len(delim) == 1:
                flag = None
                mapping = RE_splitmap.split(delim[0])
            else:
                flag = RE_splitmap.split(delim[0].strip(' \t\n\r\f\v;'))
                mapping = RE_splitmap.split(delim[1])
            rule = {}
            for m in mapping:
                uni = RE_splituni.split(m)
                if len(uni) == 1:
                    pair = RE_splitpair.split(uni[0])
                else:
                    if rule:
                        newrules.append(rule)
                        rule = {':uni': uni[0]}
                    else:
                        rule[':uni'] = uni[0]
                    pair = RE_splitpair.split(uni[1])
                if len(pair) == 1:
                    rule['zh'] = pair[0]
                else:
                    rule[pair[0]] = pair[1]
            newrules.append(rule)
            if not flag:
                ch.append(fallback(locale, newrules[0]))
            elif any(ch in flag for ch in 'ATRD-HN'):
                for f in flag:
                    # A: add rule for convert code (all text convert)
                    # H: Insert a conversion rule without output
                    if f in ('A', 'H'):
                        for r in newrules:
                            if not r in rules:
                                rules.append(r)
                        if f == 'A':
                            if ':uni' in r:
                                if locale in r:
                                    ch.append(r[locale])
                                else:
                                    ch.append(convert(r[':uni'], locale))
                            else:
                                ch.append(fallback(locale, newrules[0]))
                    # -: remove convert
                    elif f == '-':
                        for r in newrules:
                            try:
                                rules.remove(r)
                            except ValueError:
                                pass
                    # D: convert description (useless)
                    #elif f == 'D':
                        #ch.append('; '.join(': '.join(x) for x in newrules[0].items()))
                    # T: title convert (useless)
                    # R: raw content (implied above)
                    # N: current variant name (useless)
                    #elif f == 'N':
                        #ch.append(locale)
                ruledict = convtable2dict(rules, locale, update)
            else:
                fblimit = frozenset(flag) & frozenset(Locales[locale])
                limitedruledict = update.copy() if update else {}
                for r in rules:
                    if ':uni' in r:
                        if locale in r:
                            limitedruledict[r[':uni']] = r[locale]
                    else:
                        v = None
                        for l in Locales[locale]:
                            if l in r and l in fblimit:
                                v = r[l]
                                break
                        for word in r.values():
                            limitedruledict[word] = v if v else convert(word, locale)
                ch.append(convert(delim[1], locale, limitedruledict))
        elif nested:
            block += frag
        else:
            ch.append(convert(frag, locale, ruledict))
    return ''.join(ch)





s = '毫米(毫公分)，符號mm，是長度單位和降雨量單位，-{zh-hans:台湾作-{公釐}- 或-{公厘}-;zh-hant:港澳和大陸稱為-{毫米}-（台灣亦有使用，但較常使用名稱為毫公分 ）;zh-mo:台灣作-{公釐}-或-{公厘}-;zh-hk:台灣作-{公釐}-或-{公厘}-;}-。'
print(convert_for_mw(s))
print(convert_for_mw('-{zh-hans:台湾作-{公釐}- 或-{公厘}-;zh-hant:港澳和大陸稱為-{毫米}-（台灣亦有使用，但較常使用名稱為毫公分 ）;zh-mo:台灣作-{公釐}-或-{公厘}-;zh-hk:台灣作-{公釐}-或-{公厘'))
